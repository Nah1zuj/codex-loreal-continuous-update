import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'verify_local_vision_browser.mjs'


def run_verifier(*arguments):
    return subprocess.run(
        ['node', str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
    )


def test_local_vision_verifier_rejects_non_loopback_target_before_connecting():
    result = run_verifier('https://example.com', 'http://127.0.0.1:9333')
    assert result.returncode != 0
    assert 'Expected loopback app URL' in result.stderr


def test_local_vision_verifier_rejects_unknown_optional_flag_before_connecting():
    result = run_verifier(
        'http://127.0.0.1:5194',
        'http://127.0.0.1:9333',
        '--medai',
    )
    assert result.returncode != 0
    assert 'Only the optional --media flag is supported' in result.stderr
