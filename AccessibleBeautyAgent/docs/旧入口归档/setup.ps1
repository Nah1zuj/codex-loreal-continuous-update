param([switch]$SkipTests)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
foreach($setupPort in @(8000,5173)){
    if(Get-NetTCPConnection -LocalPort $setupPort -State Listen -ErrorAction SilentlyContinue){throw 'Stop development servers before setup; running Windows binaries cannot be replaced safely.'}
}
foreach($toolName in @('python','node','npm.cmd')){if(-not (Get-Command $toolName -ErrorAction SilentlyContinue)){throw "Missing required software: $toolName"}}
if(-not (Test-Path '.venv\Scripts\python.exe')){python -m venv .venv;if($LASTEXITCODE -ne 0){throw 'venv creation failed'}}
New-Item -ItemType Directory -Path 'work' -Force | Out-Null
& '.\.venv\Scripts\python.exe' -m pip install --no-cache-dir -r 'backend\requirements-lock.txt'
if($LASTEXITCODE -ne 0){throw 'Python dependencies failed'}
if(-not (Test-Path '.env')){Copy-Item -LiteralPath '.env.example' -Destination '.env'}
Push-Location 'frontend'
try{npm.cmd ci --cache '..\work\npm-cache';if($LASTEXITCODE -ne 0){throw 'npm ci failed'};npm.cmd run build;if($LASTEXITCODE -ne 0){throw 'Frontend build failed'}}finally{Pop-Location}
& '.\.venv\Scripts\python.exe' 'scripts\validate_kb.py'
if($LASTEXITCODE -ne 0){throw 'KB validation failed'}
if(-not $SkipTests){& '.\.venv\Scripts\python.exe' -m pytest;if($LASTEXITCODE -ne 0){throw 'Backend tests failed'}}
Write-Host 'Setup complete. Run: .\start-dev.ps1'
