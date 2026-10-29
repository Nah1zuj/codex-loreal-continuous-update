import os
import subprocess
from pathlib import Path
import pytest

@pytest.mark.skipif(os.name!='nt',reason='PowerShell-specific startup guard')
def test_setup_script_parses():
    root=Path(__file__).resolve().parents[2]
    # Parse without installing dependencies or starting services.
    script="$tokens=$null; $parseErrors=$null; [System.Management.Automation.Language.Parser]::ParseFile('"+str(root/'setup.ps1')+"',[ref]$tokens,[ref]$parseErrors) | Out-Null; if($parseErrors.Count -gt 0){$parseErrors | Out-String | Write-Output; exit 1}"
    r=subprocess.run(['powershell','-NoProfile','-Command',script],capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
