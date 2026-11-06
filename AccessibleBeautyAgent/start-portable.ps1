$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if((-not (Test-Path .venv-portable/Scripts/python.exe)) -or (-not (Test-Path work/install-root-windows.txt)) -or ((Get-Content work/install-root-windows.txt -Raw) -ne $PSScriptRoot) -or (-not (Test-Path frontend/node_modules/vite/bin/vite.js))){ & ./install-portable.ps1 }
& ./.venv-portable/Scripts/python.exe launch-portable.py
exit $LASTEXITCODE
