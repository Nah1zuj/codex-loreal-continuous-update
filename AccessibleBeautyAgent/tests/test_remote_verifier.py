import json
from argparse import Namespace

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
