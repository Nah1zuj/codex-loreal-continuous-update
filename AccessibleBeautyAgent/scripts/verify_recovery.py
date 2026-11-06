"""Use isolated services to check bounded conversation, process loss, and recovery."""
import argparse
import base64
import json
import os
import re
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import cv2
import httpx
import numpy as np
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from verify_runtime import ROOT, new_socket, port_is_open


def wait_until(predicate, description, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.1)
    raise AssertionError(f'Timed out waiting for {description}')


def get(client, path):
    response = client.get(path)
    response.raise_for_status()
    return response.json()


def post(client, path, body):
    response = client.post(path, json=body)
    response.raise_for_status()
    return response.json()


@contextmanager
def launcher(directory, ports, client):
    command = [sys.executable, 'launch-portable.py', '--no-browser', '--isolated', str(directory)]
    for name, port in zip(('frontend', 'backend', 'voice'), ports):
        command.extend((f'--{name}-port', str(port)))
    log = directory / 'verify-launcher.log'
    with log.open('wb') as output:
        process = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        try:
            def ready():
                assert process.poll() is None, log.read_text()
                if 'TRACE 已就绪' not in log.read_text():
                    return False
                try:
                    return get(client, '/api/health')['readiness']['sqlite_ready'] is True
                except (httpx.RequestError, httpx.HTTPStatusError):
                    return False

            wait_until(ready, 'launcher health')
            yield process
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=25)
    wait_until(lambda: not any(port_is_open(port) for port in ports), 'owned listener release')


def verify_chat(client, turns):
    started = post(client, '/api/experience/reflect', {'locale': 'zh-CN'})['session']
    sid = started['session_id']
    plan = started['makeup_plan']
    command = {'session_id': sid, 'event_id': str(uuid4()), 'action': 'advance',
               'expected_plan_id': plan['id'], 'expected_revision': plan['revision'],
               'expected_step_id': plan['steps'][plan['active_index']]['id']}
    progress = post(client, '/api/makeup/command', command)['session']['makeup_plan']
    assert progress['revision'] == plan['revision'] + 1

    for index in range(turns):
        response = client.post('/api/chat/stream', json={'session_id': sid, 'message': f'今天感觉还好。测试回合 {index+1}'})
        response.raise_for_status()
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert events and events[-1]['type'] == 'final', (index, events)
        current = events[-1]['reply']['session']['makeup_plan']
        assert (current['id'], current['revision'], current['active_index']) == (
            progress['id'], progress['revision'], progress['active_index'],
        )
    transcript = get(client, '/api/transcripts/' + sid)
    assert not transcript['persisted'] and 1 <= len(transcript['messages']) <= 30
    assert sum(len(turn['text']) for turn in transcript['messages']) <= 16000
    print(f'PASS {turns} live SSE turns, no implicit advancement, rolling transcript={len(transcript["messages"])}', flush=True)
    return command, progress


def grant_camera(client, sid):
    permit = post(client, '/api/vision/local/permits', {'session_id': sid, 'scope': 'camera'})
    encoded = cv2.imencode('.png', np.full((160, 160, 3), 127, np.uint8))[1]
    frame = {'session_id': sid, 'permit_id': permit['permit_id'], 'frame_id': str(uuid4()),
             'image': base64.b64encode(encoded.tobytes()).decode(), 'captured_at': time.time(),
             'explicit_consent': True}
    observed = post(client, '/api/vision/local', frame)
    assert not observed['frame_saved'] and observed['observation']['frame_id'] == frame['frame_id']
    return frame


def voice_connection(origin):
    endpoint = origin.replace('http://', 'ws://', 1) + '/local-voice/stream'
    return connect(endpoint, origin=origin, open_timeout=10, close_timeout=3, proxy=None)


def exercise_voice(client, origin):
    assert get(client, '/local-voice/health')['ready'], 'Install local speech models for connection tests'
    for _ in range(3):
        with voice_connection(origin) as socket:
            assert json.loads(socket.recv(timeout=5))['type'] == 'ready'
            socket.send(json.dumps({'type': 'mode', 'mode': 'bounded', 'epoch': 1}))
            assert json.loads(socket.recv(timeout=5))['type'] == 'mode'
            socket.send(b'\0' * 640)
            assert get(client, '/local-voice/health')['connections'] == 1
        wait_until(lambda: get(client, '/local-voice/health')['connections'] == 0, 'voice socket release')
    print('PASS three actual local voice WebSocket connect/close cycles returned to zero connections', flush=True)


def crash_backend(process, directory):
    log = (directory / 'portable-backend.log').read_text()
    match = re.search(r'Started server process \[(\d+)\]', log)
    assert match, 'Cannot identify owned backend process'
    pid = int(match.group(1))
    parent = int(subprocess.check_output(['ps', '-o', 'ppid=', '-p', str(pid)], text=True).strip())
    assert parent == process.pid, 'Backend log PID is not a child of the isolated launcher'
    os.kill(pid, signal.SIGKILL)
    assert process.wait(timeout=25) != 0, 'The launcher should report an abnormal child exit'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--turns', type=int, default=120)
    args = parser.parse_args()
    if os.name == 'nt':
        parser.error('The crash injection uses Unix ps and SIGKILL. Run on Mac or Linux.')
    if args.turns < 16:
        parser.error('At least 16 turns are needed to exercise the rolling history.')
    work = ROOT / 'work'
    work.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='verify-recovery-', dir=work) as temp:
        directory = Path(temp)
        sockets = [new_socket() for _ in range(3)]
        ports = [listener.getsockname()[1] for listener in sockets]
        for listener in sockets:
            listener.close()
        origin = f'http://127.0.0.1:{ports[0]}'
        with httpx.Client(base_url=origin, trust_env=False, timeout=20) as client:
            with launcher(directory, ports, client) as process:
                command, progress = verify_chat(client, args.turns)
                sid = command['session_id']
                frame = grant_camera(client, sid)
                exercise_voice(client, origin)
                with voice_connection(origin) as socket:
                    assert json.loads(socket.recv(timeout=5))['type'] == 'ready'
                    crash_backend(process, directory)
                    try:
                        socket.recv(timeout=5)
                    except ConnectionClosed:
                        pass
                    else:
                        raise AssertionError('Owned voice socket remained active after backend crash')
            print('PASS killed the owned backend, launcher reported failure, all owned ports released', flush=True)
            with launcher(directory, ports, client):
                restored = post(client, '/api/session/'+sid+'/restore', {})
                assert restored['makeup_plan']['revision'] == progress['revision']
                assert restored['makeup_plan']['active_index'] == progress['active_index']
                assert not restored['camera_consent'] and restored['visual_state'] is None
                assert get(client, '/api/transcripts/' + sid)['messages'] == []
                stale = client.post('/api/vision/local', json={**frame, 'captured_at': time.time()})
                assert stale.status_code == 403
                receipt = get(client, '/api/makeup/events/'+sid+'/'+command['event_id'])
                assert receipt['event']['status'] == 'committed'
                replay = post(client, '/api/makeup/command', command)
                assert replay['duplicate'] and replay['session']['makeup_plan']['revision'] == progress['revision']
                assert get(client, '/local-voice/health')['connections'] == 0
            print('PASS same isolated SQLite restores committed event once; no transcript, visual permit, or voice connection restored')


if __name__ == '__main__':
    main()
