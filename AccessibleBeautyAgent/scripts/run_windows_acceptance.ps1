param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9a-f]{40}$')][string]$ExpectedCommit,
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9a-f]{64}$')][string]$PackageSha256,
    [Parameter(Mandatory = $true)][ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })][string]$PackagePath,
    [switch]$DownloadModels
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') {
    throw 'This acceptance entry must run on Windows.'
}
$resolvedPackagePath = (Resolve-Path -LiteralPath $PackagePath).Path
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Get-Command py.exe -ErrorAction SilentlyContinue)) {
    throw 'Install Windows x64 Python 3.12 with the Python Launcher.'
}
$chromeVersion = $null
$registryPaths = @(
    'HKCU:\Software\Google\Chrome\BLBeacon',
    'HKLM:\Software\Google\Chrome\BLBeacon',
    'HKLM:\Software\WOW6432Node\Google\Chrome\BLBeacon'
)
foreach ($path in $registryPaths) {
    try {
        $candidate = (Get-ItemProperty -LiteralPath $path -Name version -ErrorAction Stop).version
        if ($candidate) { $chromeVersion = [string]$candidate; break }
    } catch {}
}
if (-not $chromeVersion) { throw 'Google Chrome version was not found in the Windows registry.' }
$arguments = @(
    'scripts/windows_acceptance.py', 'run',
    '--expected-commit', $ExpectedCommit,
    '--package-sha256', $PackageSha256,
    '--package-path', $resolvedPackagePath,
    '--powershell-version', $PSVersionTable.PSVersion.ToString(),
    '--chrome-version', $chromeVersion
)
if ($DownloadModels) { $arguments += '--download-models' }
& py.exe -3.12 @arguments
exit $LASTEXITCODE
