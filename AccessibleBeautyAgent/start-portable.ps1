$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
# Run the installer as a child so its exit code is available to this wrapper.
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install-portable.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& ./.venv-portable/Scripts/python.exe launch-portable.py @args
exit $LASTEXITCODE
