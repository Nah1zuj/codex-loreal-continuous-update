$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
function RunChecked([string]$Exe,[string[]]$ArgsList){ & $Exe @ArgsList; if($LASTEXITCODE -ne 0){throw "Command failed: $Exe"} }
if(-not (Get-Command node.exe -ErrorAction SilentlyContinue) -or -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)){throw 'Install Node.js 22.12+ first.'}
RunChecked node.exe @('-e','let [a,b]=process.versions.node.split(".").map(Number);if(a<22||(a===22&&b<12))process.exit(1)')
$py=Get-Command py.exe -ErrorAction SilentlyContinue
if(-not $py){throw 'Install Python 3.12 with the Python launcher first.'}
RunChecked $py.Source @('-3.12','-c','import sys; assert sys.version_info[:2]==(3,12)')
New-Item -ItemType Directory -Force work | Out-Null
$marker='work/install-root-windows.txt'
if((Test-Path .venv-portable) -and ((-not (Test-Path $marker)) -or ((Get-Content $marker -Raw) -ne $PSScriptRoot))){Rename-Item .venv-portable ('.venv-portable.previous-'+[DateTimeOffset]::Now.ToUnixTimeSeconds())}
if(-not (Test-Path .venv-portable/Scripts/python.exe)){RunChecked $py.Source @('-3.12','-m','venv','.venv-portable')}
RunChecked '.venv-portable/Scripts/python.exe' @('-m','pip','install','-r','backend/requirements-windows.txt','-r','voice/requirements.txt')
RunChecked '.venv-portable/Scripts/python.exe' @('voice/setup_local_voice_models.py')
Push-Location frontend
try {RunChecked npm.cmd @('ci');RunChecked npm.cmd @('run','build')} finally {Pop-Location}
RunChecked '.venv-portable/Scripts/python.exe' @('-c',"import sys;sys.path.insert(0,'voice');from setup_local_voice_models import ready;assert ready(),'Missing voice models'")
[IO.File]::WriteAllText((Join-Path $PSScriptRoot $marker),$PSScriptRoot)
Write-Host 'Install complete.'
