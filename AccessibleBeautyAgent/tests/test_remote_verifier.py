import base64
import json
from argparse import Namespace
import hashlib

import httpx
import pytest

from scripts.verify_remote_services import VerificationError, verify_label, verify_text


def test_label_preflight_never_reads_or_sends_an_image(tmp_path, capsys):
    requests = []

    def handle(request):
        requests.append((request.method, request.url.path))
        return httpx.Response(200, json={
            'status': 'configured', 'provider': 'qwen', 'destination_host': 'approved.example',
        })

    args = Namespace(provider='qwen', destination_host='approved.example', execute=False,
                     image=tmp_path / 'missing.png')
    with httpx.Client(base_url='http://127.0.0.1', transport=httpx.MockTransport(handle)) as client:
        verify_label(client, args)
        args.execute = True
        args.destination_host = 'different.example'
        with pytest.raises(VerificationError, match='destination'):
            verify_label(client, args)
    assert requests == [('GET', '/api/reading/availability')] * 2
    assert 'No image sent' in capsys.readouterr().out


@pytest.mark.parametrize('verified', [False, True])
def test_text_verifier_requires_provider_proof_beyond_a_final_event(verified, capsys):
    def handle(request):
        if request.url.path == '/api/health':
            return httpx.Response(200, json={
                'provider_mode': 'qwen', 'readiness': {'remote_text_configured': True},
            })
        if request.url.path == '/api/chat/stream':
            assert '虚构' in json.loads(request.content)['message']
            return httpx.Response(200, text='data: {"type":"final","reply":{"message":"Example"}}\n\n',
                                  headers={'set-cookie': 'trace_identity=test; Path=/api'})
        assert request.url.path == '/api/diagnostics'
        assert request.headers['cookie'] == 'trace_identity=test'
        return httpx.Response(200, json={'turns': [{
            'provider': 'qwen', 'outcome': 'complete', 'remote_response_verified': verified,
        }]})

    args = Namespace(provider='qwen', execute=True)
    with httpx.Client(base_url='http://127.0.0.1', transport=httpx.MockTransport(handle)) as client:
        if verified:
            verify_text(client, args)
            assert 'PASS: completed text stream from qwen' in capsys.readouterr().out
        else:
            with pytest.raises(VerificationError, match='lacks evidence'):
                verify_text(client, args)


def test_text_verifier_rejects_course_progress_commit():
    def handle(request):
        if request.url.path == '/api/health':
            return httpx.Response(200, json={
                'provider_mode': 'qwen', 'readiness': {'remote_text_configured': True},
            })
        if request.url.path == '/api/chat/stream':
            return httpx.Response(200, text=(
                'data: {"type":"committed","event":{"kind":"advance"}}\n\n'
                'data: {"type":"final","reply":{"message":"Example"}}\n\n'
            ))
        raise AssertionError('diagnostics must not be accepted after a course commit')

    args = Namespace(provider='qwen', execute=True)
    with httpx.Client(base_url='http://127.0.0.1', transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(VerificationError, match='course progress'):
            verify_text(client, args)


def test_label_execute_rejects_unapproved_image_hash_before_post(tmp_path):
    requests = []
    png = (b'\x89PNG\r\n\x1a\n' + b'synthetic test bytes')
    image = tmp_path / 'label.png'
    image.write_bytes(png)

    def handle(request):
        requests.append((request.method, request.url.path))
        return httpx.Response(200, json={
            'status': 'configured', 'provider': 'qwen', 'destination_host': 'approved.example',
        })

    args = Namespace(
        provider='qwen', destination_host='approved.example', execute=True,
        image=image, expect_text='TRACE', expect_uncertain=False,
        expect_sha256=hashlib.sha256(png + b'changed').hexdigest(), label_kind='product',
    )
    with httpx.Client(base_url='http://127.0.0.1', transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(VerificationError, match='approved SHA-256'):
            verify_label(client, args)
    assert requests == [('GET', '/api/reading/availability')]


def test_label_execute_posts_only_the_hash_approved_image(tmp_path, capsys):
    requests = []
    png = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
    )
    image = tmp_path / 'label.png'
    image.write_bytes(png)

    def handle(request):
        requests.append((request.method, request.url.path))
        if request.method == 'POST':
            assert base64.b64decode(json.loads(request.content)['image']) == png
            return httpx.Response(200, json={
                'service': 'qwen', 'simulated': False, 'status': 'READ',
                'full_text': 'TRACE TEST LABEL', 'shade': None,
                'composition': None, 'instructions': None,
            })
        verified = len(requests) > 2
        return httpx.Response(200, json={
            'status': 'configured', 'provider': 'qwen', 'destination_host': 'approved.example',
            'remote_verified': verified,
        })

    digest = hashlib.sha256(png).hexdigest()
    args = Namespace(
        provider='qwen', destination_host='approved.example', execute=True,
        image=image, expect_text='TRACE TEST LABEL', expect_uncertain=False,
        expect_sha256=digest, label_kind='product',
    )
    with httpx.Client(base_url='http://127.0.0.1', transport=httpx.MockTransport(handle)) as client:
        verify_label(client, args)
    assert requests == [
        ('GET', '/api/reading/availability'),
        ('POST', '/api/reading/read'),
        ('GET', '/api/reading/availability'),
    ]
    output = capsys.readouterr().out
    assert digest in output and 'image and text omitted' in output
