$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command py.exe -ErrorAction SilentlyContinue)) {
    throw 'Install Python 3.12 with the Windows Python Launcher.'
}
& py.exe -3.12 install-portable.py @args
exit $LASTEXITCODE
