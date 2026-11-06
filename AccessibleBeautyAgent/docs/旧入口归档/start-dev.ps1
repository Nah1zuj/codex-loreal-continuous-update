param([switch]$Setup,[switch]$NoBrowser)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if($Setup){& '.\setup.ps1';if(-not $?){throw 'Setup failed'}}
$pythonPath=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$vitePath=Join-Path $PSScriptRoot 'frontend\node_modules\vite\bin\vite.js'
if(-not (Test-Path -LiteralPath $pythonPath) -or -not (Test-Path -LiteralPath $vitePath)){throw 'Run .\setup.ps1 first.'}
if(-not (Test-Path '.env')){Copy-Item -LiteralPath '.env.example' -Destination '.env'}
foreach($portNumber in @(8000,5173)){
    if(Get-NetTCPConnection -LocalPort $portNumber -State Listen -ErrorAction SilentlyContinue){throw "Port $portNumber is already in use. Stop that process or use manual startup with matching proxy ports."}
}
New-Item -ItemType Directory -Path 'work' -Force | Out-Null
$backendProcess=$null
$frontendProcess=$null
try{
    $backendProcess=Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8000') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'work\backend.stdout.log' -RedirectStandardError 'work\backend.stderr.log'
    $nodePath=(Get-Command node).Source
    $frontendProcess=Start-Process -FilePath $nodePath -ArgumentList @('"'+$vitePath+'"','--host','127.0.0.1','--port','5173') -WorkingDirectory (Join-Path $PSScriptRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput 'work\frontend.stdout.log' -RedirectStandardError 'work\frontend.stderr.log'
    $isReady=$false
    for($attempt=0;$attempt -lt 45;$attempt++){
        if($backendProcess.HasExited -or $frontendProcess.HasExited){throw 'A server exited. Read work\*.stderr.log'}
        try{$health=Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 1;$front=Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 1;if($health.status -eq 'ok' -and $front.StatusCode -eq 200){$isReady=$true;break}}catch{}
        Start-Sleep -Milliseconds 500
    }
    if(-not $isReady){throw 'Server readiness timed out; see work logs.'}
    Write-Host 'Frontend: http://127.0.0.1:5173'
    Write-Host 'API docs: http://127.0.0.1:8000/docs'
    Write-Host 'Press Ctrl+C in this window to stop both servers. Logs: work\'
    if(-not $NoBrowser){Start-Process 'http://127.0.0.1:5173'}
    while(-not $backendProcess.HasExited -and -not $frontendProcess.HasExited){Start-Sleep -Seconds 1}
    throw 'A development server stopped unexpectedly. Read work logs.'
}finally{
    foreach($ownedProcess in @($backendProcess,$frontendProcess)){if($null -ne $ownedProcess -and -not $ownedProcess.HasExited){Stop-Process -Id $ownedProcess.Id -ErrorAction SilentlyContinue}}
}
