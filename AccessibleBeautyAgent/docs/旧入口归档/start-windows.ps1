param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$frontUrl = 'http://127.0.0.1:5174/'
$healthUrl = 'http://127.0.0.1:8002/api/health'
$pythonPath = Join-Path $PSScriptRoot '.venv-windows\Scripts\python.exe'
$vitePath = Join-Path $PSScriptRoot 'frontend\node_modules\vite\bin\vite.js'
$markerPath = Join-Path $PSScriptRoot 'work\windows-install.json'
$backendProcess = $null
$frontendProcess = $null
$voiceProcess = $null
$voicePythonPath = Join-Path $PSScriptRoot '.venv-voice-windows\Scripts\python.exe'
$voiceHealthUrl = 'http://127.0.0.1:8003/voice/health'

function Test-Listener([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}
function Invoke-Checked([string]$Executable, [string[]]$Arguments, [string]$Description) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Description failed (exit $LASTEXITCODE)." }
}

# A second click reuses the three healthy services.
if ((Test-Listener 8002) -or (Test-Listener 5174) -or (Test-Listener 8003)) {
    $existingReady = $false
    try {
        $health = Invoke-RestMethod $healthUrl -TimeoutSec 3
        $page = Invoke-WebRequest $frontUrl -UseBasicParsing -TimeoutSec 3
        $voiceHealth = Invoke-RestMethod $voiceHealthUrl -TimeoutSec 3
        $existingReady = ($voiceHealth.ready -and $health.experience_revision -eq 'harness-v2-20261017' -and $health.status -eq 'ok' -and $health.policy_version -eq 'v5' -and $page.StatusCode -eq 200)
    } catch { $existingReady = $false }
    if ($existingReady) {
        Write-Host "TRACE V5 is already running: $frontUrl"
        if (-not $NoBrowser) { Start-Process $frontUrl }
        exit 0
    }
    throw 'Port 8002, 5174 or 8003 is occupied by an unavailable or different service. No existing process was stopped.'
}

$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $nodeCommand -or -not $npmCommand) { throw 'Install Node.js 22.12+ and reopen this entry.' }
$nodeVersionText = & $nodeCommand.Source --version
if ($LASTEXITCODE -ne 0) { throw 'Could not read Node.js version.' }
$nodeVersion = [version]($nodeVersionText.Trim().TrimStart('v'))
if ($nodeVersion -lt [version]'22.12.0') { throw 'Node.js 22.12+ is required.' }
New-Item -ItemType Directory -Path 'work' -Force | Out-Null

if (-not (Test-Path -LiteralPath $pythonPath)) {
    $pythonLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    $pythonArgs = @('-3')
    if (-not $pythonLauncher) {
        $pythonLauncher = Get-Command python.exe -ErrorAction SilentlyContinue
        $pythonArgs = @()
    }
    if (-not $pythonLauncher) { throw 'Install Python 3.11+ and reopen this entry.' }
    Invoke-Checked -Executable $pythonLauncher.Source -Arguments ($pythonArgs + @('-c','import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)')) -Description 'Python version check (3.11+)'
    Invoke-Checked -Executable $pythonLauncher.Source -Arguments ($pythonArgs + @('-m','venv','.venv-windows')) -Description 'Windows virtual environment creation'
}
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}

$dependencyFiles = @('backend\requirements-windows.txt','backend\requirements-landmarks.txt','frontend\package-lock.json')
$signature = (($dependencyFiles | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash }) -join ':')
$ready = $false
if ((Test-Path -LiteralPath $markerPath) -and (Test-Path -LiteralPath $vitePath)) {
    try {
        $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
        $ready = ($marker.signature -eq $signature -and $marker.platform -eq 'win32')
    } catch { $ready = $false }
}
if (-not $ready) {
    Write-Host 'First Windows setup: installing local dependencies. Internet access is required.'
    Invoke-Checked -Executable $pythonPath -Arguments @('-m','pip','install','--only-binary=:all:','-r','backend\requirements-windows.txt') -Description 'Windows Python dependencies'
    Push-Location -LiteralPath 'frontend'
    try {
        Invoke-Checked -Executable $npmCommand.Source -Arguments @('ci','--cache','..\work\npm-cache','--no-audit','--no-fund') -Description 'Windows frontend dependencies'
        Invoke-Checked -Executable $npmCommand.Source -Arguments @('run','build') -Description 'Frontend build'
    } finally { Pop-Location }
    Invoke-Checked -Executable $pythonPath -Arguments @('scripts\validate_kb.py') -Description 'Knowledge validation'
    @{platform='win32';signature=$signature;completed_at=(Get-Date).ToString('s')} | ConvertTo-Json | Set-Content -LiteralPath $markerPath -Encoding UTF8
}

# Keep speech native bindings separate from the existing backend Python.
if (-not (Test-Path -LiteralPath $voicePythonPath)) {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    $chosen = $null
    if ($launcher) {
        foreach ($version in @('-3.12','-3.13','-3.14')) {
            try { & $launcher.Source $version -c 'import sys; sys.exit(0)' 2>$null; if ($LASTEXITCODE -eq 0) { $chosen=$version; break } } catch { }
        }
    }
    if (-not $chosen) { throw 'Local voice needs Python 3.12 or 3.13 via the Windows Python launcher. Install it and reopen this entry.' }
    Invoke-Checked -Executable $launcher.Source -Arguments @($chosen,'-m','venv','.venv-voice-windows') -Description 'Local voice environment'
}
$voiceReady = $false
try { & $voicePythonPath -c 'import sherpa_onnx,fastapi,uvicorn,websockets,certifi,sentencepiece,pypinyin,numpy' 2>$null; $voiceReady = ($LASTEXITCODE -eq 0) } catch { $voiceReady = $false }
if (-not $voiceReady) { Invoke-Checked -Executable $voicePythonPath -Arguments @('-m','pip','install','-r','voice\requirements.txt') -Description 'Offline voice dependencies' }
$modelsReady = $false
try { & $voicePythonPath -c "import sys;sys.path.insert(0,'voice');from setup_local_voice_models import ready;sys.exit(0 if ready() else 1)"; $modelsReady = ($LASTEXITCODE -eq 0) } catch { }
if (-not $modelsReady) {
    Invoke-Checked -Executable $voicePythonPath -Arguments @('voice\setup_local_voice_models.py') -Description 'Official offline voice models'
}

$env:MPLCONFIGDIR = Join-Path $PSScriptRoot 'work\matplotlib'
New-Item -ItemType Directory -Path $env:MPLCONFIGDIR -Force | Out-Null
try {
    $voiceProcess = Start-Process -FilePath $voicePythonPath -ArgumentList @('-m','uvicorn','server:app','--app-dir','voice','--host','127.0.0.1','--port','8003') -WorkingDirectory $PSScriptRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput 'work\windows-voice.stdout.log' -RedirectStandardError 'work\windows-voice.stderr.log'
    $backendProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8002') -WorkingDirectory $PSScriptRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput 'work\windows-backend.stdout.log' -RedirectStandardError 'work\windows-backend.stderr.log'
    $frontendProcess = Start-Process -FilePath $nodeCommand.Source -ArgumentList @(('"' + $vitePath + '"'),'--config','vite.package.config.ts') -WorkingDirectory (Join-Path $PSScriptRoot 'frontend') -PassThru -WindowStyle Hidden -RedirectStandardOutput 'work\windows-frontend.stdout.log' -RedirectStandardError 'work\windows-frontend.stderr.log'
    $ready = $false
    for ($attempt=0; $attempt -lt 120; $attempt++) {
        if ($backendProcess.HasExited -or $frontendProcess.HasExited -or $voiceProcess.HasExited) { throw 'A service exited. Read work\windows-*.log.' }
        try {
            $health = Invoke-RestMethod $healthUrl -TimeoutSec 1
            $page = Invoke-WebRequest $frontUrl -UseBasicParsing -TimeoutSec 1
            $voiceHealth = Invoke-RestMethod $voiceHealthUrl -TimeoutSec 1
            if ($voiceHealth.ready -and $health.status -eq 'ok' -and $health.policy_version -eq 'v5' -and $page.StatusCode -eq 200) { $ready=$true; break }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'Startup timed out. Read work\windows-*.log.' }
    Write-Host "TRACE V5 correct version: $frontUrl"
    Write-Host 'Keep this terminal open. Control+C stops only the services launched here.'
    if (-not $NoBrowser) { Start-Process $frontUrl }
    while (-not $backendProcess.HasExited -and -not $frontendProcess.HasExited -and -not $voiceProcess.HasExited) { Start-Sleep -Seconds 1 }
    throw 'A development service stopped. Read work\windows-*.log.'
} finally {
    foreach ($ownedProcess in @($backendProcess,$frontendProcess,$voiceProcess)) {
        if ($null -ne $ownedProcess -and -not $ownedProcess.HasExited) {
            Stop-Process -Id $ownedProcess.Id -ErrorAction SilentlyContinue
        }
    }
}
