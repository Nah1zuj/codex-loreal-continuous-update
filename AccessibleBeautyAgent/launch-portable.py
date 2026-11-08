"""Run the local services and stop the child processes owned by this instance."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener
import webbrowser

from runtime import (DEFAULTS, ROOT, VITE, WORK, instance_lock, isolated_environment,
                     node_executable, require_python)

HOST = '127.0.0.1'
OPENER = build_opener(ProxyHandler({}))


def port_in_use(port):
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((HOST, port)) == 0


def get_json(url):
    with OPENER.open(url, timeout=2) as response:
        return json.load(response)


def health(url):
    return {
        'frontend': get_json(url + 'release.json'),
        'backend': get_json(url + 'api/health'),
        'voice': get_json(url + 'local-voice/health'),
    }


def close_children(children):
    for child in children:
        if child.poll() is None:
            child.terminate()
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def run(args):
    ports = {name: getattr(args, name + '_port') for name in ('frontend', 'backend', 'voice')}
    if len(set(ports.values())) != len(ports):
        raise RuntimeError('网页、后端和语音必须使用不同的端口。')
    url = f"http://{HOST}:{ports['frontend']}/"
    if args.doctor:
        return diagnose(url)
    require_python()
    node = node_executable()
    if not VITE.is_file():
        raise RuntimeError('前端依赖缺失，请运行“首次安装”入口。')
    directory = (args.isolated or WORK).resolve()
    if not directory.is_relative_to(WORK.resolve()):
        raise RuntimeError('隔离工作目录必须位于项目的 work 目录。')
    directory.mkdir(parents=True, exist_ok=True)
    with instance_lock(directory / 'launcher.lock') as acquired:
        if not acquired:
            print('同一工作目录的 TRACE 已在启动或运行。请使用原启动窗口停止服务。', flush=True)
            return 0
        busy = [str(port) for port in ports.values() if port_in_use(port)]
        if busy:
            raise RuntimeError('本机端口已占用：' + '、'.join(busy) + '。请在原应用关闭占用或更换端口。')
        env = os.environ.copy()
        env.update({f'TRACE_{name.upper()}_PORT': str(port) for name, port in ports.items()})
        env['TRACE_WORK_DIR'] = str(directory)
        env['MPLCONFIGDIR'] = str(directory / 'matplotlib')
        if args.isolated:
            env.update(isolated_environment(directory))
        commands = {
            'backend': uvicorn('app.main:app', 'backend', ports['backend']),
            'voice': uvicorn('server:app', 'voice', ports['voice']),
            'frontend': [node, str(VITE), 'frontend'],
        }
        with ExitStack() as stack:
            logs = {name: stack.enter_context((directory / f'portable-{name}.log').open('wb'))
                    for name in commands}
            children = []
            stack.callback(close_children, children)
            for name, command in commands.items():
                children.append(subprocess.Popen(command, cwd=ROOT, env=env, stdout=logs[name],
                                                 stderr=subprocess.STDOUT))
            print('正在启动 TRACE，请稍候…', flush=True)
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if any(child.poll() is not None for child in children):
                    raise RuntimeError(f'有服务退出。请查看 {directory}/portable-*.log。')
                try:
                    state = health(url)
                except (URLError, OSError, ValueError):
                    time.sleep(0.3)
                    continue
                release = json.loads((ROOT / 'frontend/public/release.json').read_text(encoding='utf-8'))
                if state['frontend'].get('release') != release['release']:
                    raise RuntimeError('网页版本不匹配。请检查正在使用的端口。')
                if state['backend'].get('status') != 'ok' or not state['backend'].get('memory'):
                    raise RuntimeError('后端或数据库不可用。请查看后端日志。')
                break
            else:
                raise RuntimeError(f'启动超时。请查看 {directory}/portable-*.log。')
            print(f'TRACE 已就绪：{url}\n保留此窗口。Control+C 停止本次启动的服务。', flush=True)
            if not state['voice'].get('ready'):
                print('本地语音不可用，文字仍可使用。请运行 voice/setup_local_voice_models.py 检查模型。', flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            while all(child.poll() is None for child in children):
                time.sleep(0.4)
            raise RuntimeError(f'有服务停止。请查看 {directory}/portable-*.log。')


def uvicorn(app, directory, port):
    return [sys.executable, '-m', 'uvicorn', app, '--app-dir', directory,
            '--host', HOST, '--port', str(port), '--timeout-graceful-shutdown', '3']


def diagnose(url):
    diagnostics = {'python': sys.version.split()[0], 'vite_installed': VITE.is_file(), 'url': url}
    try:
        require_python()
        node_executable()
        diagnostics['runtime_version_ok'] = True
    except (OSError, RuntimeError, subprocess.SubprocessError):
        diagnostics['runtime_version_ok'] = False
    try:
        diagnostics['services'] = health(url)
    except (URLError, OSError, ValueError):
        diagnostics['services'] = None
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))
    return 0 if diagnostics['services'] and diagnostics['runtime_version_ok'] else 1


def port_number(value):
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError('端口必须介于 1 与 65535。')
    return port


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--doctor', action='store_true')
    parser.add_argument('--isolated', type=Path, help='自测目录，须位于应用 work 内')
    for name in ('frontend', 'backend', 'voice'):
        parser.add_argument('--' + name + '-port', type=port_number, default=DEFAULTS[name])
    return run(parser.parse_args())


if __name__ == '__main__':
    def shutdown(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, shutdown)
    if os.name == 'nt':
        signal.signal(signal.SIGBREAK, shutdown)
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\nTRACE 已停止。')
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
