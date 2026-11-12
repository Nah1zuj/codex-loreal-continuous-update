import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != 'nt', reason='PowerShell-specific startup guard')
@pytest.mark.parametrize('name', [
    'install-portable.ps1', 'start-portable.ps1', 'scripts/run_windows_acceptance.ps1',
])
def test_portable_powershell_parses(name):
    root = Path(__file__).resolve().parents[2]
    path = str(root / name).replace("'", "''")
    script = (
        "$tokens=$null; $parseErrors=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{path}',"
        "[ref]$tokens,[ref]$parseErrors) | Out-Null; "
        "if($parseErrors.Count){$parseErrors | Out-String | Write-Output; exit 1}"
    )
    result = subprocess.run(['powershell', '-NoProfile', '-Command', script],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
