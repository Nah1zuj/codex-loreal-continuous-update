"""Smoke-test the real local launcher without touching daily settings or ports."""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == 'nt'


def new_socket():
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    return listener


def port_is_open(port):
    with socket.socket() as client:
        client.settimeout(0.3)
        return client.connect_ex(('127.0.0.1', port)) == 0


def check(client, path):
    response = client.get(path)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--missing-voice', action='store_true')
    args = parser.parse_args()
    work = ROOT / 'work'
    work.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='runtime-test-', dir=work) as temporary:
        directory = Path(temporary)
        sockets = [new_socket() for _ in range(3)]
        ports = [listener.getsockname()[1] for listener in sockets]
        command = [sys.executable, 'launch-portable.py', '--no-browser', '--isolated', str(directory)]
        for name, port in zip(('frontend', 'backend', 'voice'), ports):
            command.extend((f'--{name}-port', str(port)))
        options = {'cwd': ROOT, 'encoding': 'utf-8', 'env': {**os.environ, 'PYTHONUTF8': '1'}}
        try:
            sockets[1].listen(16)
            conflict = subprocess.run(command, capture_output=True, timeout=10, **options)
            assert conflict.returncode == 1 and str(ports[1]) in conflict.stderr, conflict.stderr
            assert port_is_open(ports[1])
            print('PASS occupied port preserved')
        finally:
            for listener in sockets:
                listener.close()
        creation = subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0
        with (directory / 'launcher.log').open('wb') as output:
            owner = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                     creationflags=creation, **options)
            try:
                with httpx.Client(base_url=f'http://127.0.0.1:{ports[0]}', trust_env=False) as client:
                    for _ in range(120):
                        assert owner.poll() is None, (directory / 'launcher.log').read_text(encoding='utf-8')
                        try:
                            voice = check(client, '/local-voice/health')
                            check(client, '/api/health')
                            if 'TRACE 已就绪' in (directory / 'launcher.log').read_text(encoding='utf-8'):
                                break
                            time.sleep(0.5)
                        except (httpx.RequestError, httpx.HTTPStatusError):
                            time.sleep(0.5)
                    else:
                        for log in sorted(directory.glob('*.log')):
                            print(f'{log.name}: {log.read_text(encoding="utf-8")[-3000:]}', file=sys.stderr)
                        raise AssertionError('Launcher health timed out')
                    assert voice['ready'] is not args.missing_voice, voice
                    assert client.get('/').status_code == 200
                    assert check(client, '/release.json')['release']
                    backend = client.get('/api/health')
                    assert backend.json()['readiness']['sqlite_ready'] is True
                    assert backend.json()['provider_mode'] == 'mock'
                    assert 'set-cookie' not in backend.headers
                    origin = str(client.base_url).rstrip('/')
                    reply = client.post('/api/chat', json={'message': '你好', 'locale': 'zh-CN'},
                                        headers={'Origin': origin})
                    reply.raise_for_status()
                    session = reply.json()['session']['session_id']
                    assert check(client, '/api/session/' + session)['camera_consent'] is False
                    assert (directory / 'beauty.sqlite').is_file()
                    print(f'PASS frontend, isolated SQLite, text turn, session restore; speech={voice["model_status"]}')
                duplicate = subprocess.run(command, capture_output=True, timeout=10, **options)
                assert duplicate.returncode == 0 and '已在启动或运行' in duplicate.stdout, duplicate.stdout
                assert owner.poll() is None
                print('PASS duplicate preserves owner')
                doctor = subprocess.run(command + ['--doctor'], capture_output=True, timeout=10, **options)
                assert doctor.returncode == 0 and json.loads(doctor.stdout)['runtime_version_ok']
                print('PASS runtime diagnostics')
            finally:
                if owner.poll() is None:
                    owner.send_signal(signal.CTRL_BREAK_EVENT if WINDOWS else signal.SIGTERM)
                    owner.wait(timeout=25)
        assert not any(port_is_open(port) for port in ports)
        print('PASS owned ports released')


if __name__ == '__main__':
    main()
