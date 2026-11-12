"""Check the opt-in TRACE text or label route on a loopback test instance."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

import httpx


class VerificationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def verify_text(client, args):
    health = client.get('/api/health').raise_for_status().json()
    require(health['provider_mode'] == args.provider
            and health.get('provider_models', {}).get('language') == args.model
            and health['readiness']['remote_text_configured'],
            'The expected text provider and model are not configured and enabled.')
    if not args.execute:
        print('READY: text configuration only. No message sent.')
        return

    with client.stream('POST', '/api/chat/stream', json={
        'locale': 'zh-CN',
        'message': '在一个虚构的工作坊里，如何用一句友善的话介绍自然妆这个主题？请只给一句介绍。',
    }) as response:
        response.raise_for_status()
        terminal = None
        committed = False
        for line in response.iter_lines():
            if line.startswith('data: '):
                event = json.loads(line[6:])
                if event['type'] == 'committed':
                    committed = True
                if event['type'] in ('final', 'error'):
                    terminal = event
    require(terminal and terminal['type'] == 'final' and terminal['reply'].get('message', '').strip(),
            'The text request did not finish with a nonempty reply.')
    require(not committed, 'The fixed verification message unexpectedly committed course progress.')
    turns = client.get('/api/diagnostics').raise_for_status().json()['turns']
    require(turns and turns[-1]['outcome'] == 'complete' and turns[-1].get('provider') == args.provider
            and turns[-1].get('remote_response_verified') is True,
            'The completed reply lacks evidence of a response from the expected remote provider.')
    print(f'PASS: completed text stream from {args.provider}; reply and cookies omitted.')


def verify_label(client, args):
    service = client.get('/api/reading/availability').raise_for_status().json()
    require(service['status'] == 'configured' and service['provider'] == args.provider
            and service.get('model') == args.model
            and service['destination_host'] == args.destination_host,
            'The expected label provider, model, and destination are not configured and enabled.')
    if not args.execute:
        print(f'READY: label configuration for {args.destination_host} only. No image sent.')
        return

    require(args.image and (args.expect_text or args.expect_uncertain),
            'To send one approved test label, provide --image and its expected outcome.')
    require(args.image.stat().st_size <= 2_000_000, 'Use a synthetic JPEG or PNG under 2 MB.')
    raw = args.image.read_bytes()
    require(raw.startswith(b'\x89PNG\r\n\x1a\n') or raw.startswith(b'\xff\xd8\xff'),
            'The approved label must be a PNG or JPEG file.')
    require(args.expect_sha256 and len(args.expect_sha256) == 64
            and all(character in '0123456789abcdef' for character in args.expect_sha256),
            'Provide the approved image SHA-256 as 64 lowercase hexadecimal characters.')
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == args.expect_sha256,
            'The selected image does not match the explicitly approved SHA-256.')
    image = base64.b64encode(raw).decode('ascii')
    result = client.post('/api/reading/read', json={
        'image': image, 'label_kind': args.label_kind,
        'explicit_consent': True, 'remote_upload_consent': True, 'authorized_provider': args.provider,
        'authorized_destination_host': args.destination_host,
    }).raise_for_status().json()
    require(result['service'] == args.provider and result['simulated'] is False,
            'The returned result was not attributed to the expected remote provider.')
    verification = client.get('/api/reading/availability').raise_for_status().json()
    require(verification['remote_verified'] is True and verification['provider'] == args.provider
            and verification['destination_host'] == args.destination_host,
            'The active provider configuration has no verified result.')
    if args.expect_uncertain:
        require(result['status'] == 'UNCERTAIN'
                and all(result[field] is None for field in ('shade', 'composition', 'instructions')),
                'The unreadable sample did not preserve uncertainty.')
    else:
        require(result['status'] == 'READ' and args.expect_text in (result['full_text'] or ''),
                'The clear sample did not contain the expected transcription.')
    print(f'PASS: {result["status"]} label result from {args.provider} at {args.destination_host}; '
          f'image SHA-256 {digest}; image and text omitted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, required=True, help='Port of a disposable loopback TRACE backend')
    modes = parser.add_subparsers(dest='mode', required=True)
    text = modes.add_parser('text', help='Check a text provider with one fixed fictional message')
    text.add_argument('--provider', required=True, choices=('deepseek', 'qwen', 'openai_compatible'))
    text.add_argument('--model', required=True, help='Exact configured text model name')
    text.add_argument('--execute', action='store_true', help='Authorize sending the fixed fictional message')
    label = modes.add_parser('label', help='Check one approved synthetic label')
    label.add_argument('--provider', required=True, choices=('deepseek', 'qwen'))
    label.add_argument('--model', required=True, help='Exact configured image-reading model name')
    label.add_argument('--destination-host', required=True)
    label.add_argument('--label-kind', choices=('product', 'garment'), default='product')
    label.add_argument('--image', type=Path, help='One approved JPEG or PNG with no personal content')
    expectations = label.add_mutually_exclusive_group()
    expectations.add_argument('--expect-text', help='Known text to find in the clear sample')
    expectations.add_argument('--expect-uncertain', action='store_true', help='Expect an unreadable result without inferred fields')
    label.add_argument('--expect-sha256', help='Approved lowercase SHA-256 of the one image to send')
    label.add_argument('--execute', action='store_true', help='Authorize sending this image once to the named host')
    args = parser.parse_args()

    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{args.port}', timeout=120, trust_env=False) as client:
            (verify_text if args.mode == 'text' else verify_label)(client, args)
    except VerificationError as error:
        parser.exit(1, f'INCOMPLETE: {error}\n')
    except httpx.HTTPStatusError as error:
        parser.exit(1, f'INCOMPLETE: local API returned HTTP {error.response.status_code}.\n')
    except (httpx.RequestError, OSError, ValueError, KeyError, TypeError):
        parser.exit(1, 'INCOMPLETE: local request, file, or response validation failed.\n')


if __name__ == '__main__':
    main()
