# make-portable.ps1 -- Build an offline USB bundle for Lab 04
# Result: portable\BJT-Amplifier-Simulator-v1\  and  dist\*.zip
# The build machine needs internet for `pip download`; the USB bundle does not.
# ASCII-only on purpose (Windows PowerShell 5.1 code-page safety).

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Dest = Join-Path $Root 'portable\BJT-Amplifier-Simulator-v1'
$Zip = Join-Path $Root 'dist\BJT-Amplifier-Simulator-v1-portable.zip'
$PythonExe = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path $PythonExe)) {
    throw 'Run .\setup.ps1 first to create the venv and install Flask.'
}

Write-Host ('Building portable bundle at ' + $Dest) -ForegroundColor Cyan
if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

foreach ($name in @(
    'app.py', 'dc_bias.py', 'spice_engine.py', 'plots.py', 'run_app.py',
    'requirements.txt', 'README.md', 'AGENTS.md'
)) {
    Copy-Item (Join-Path $Root $name) (Join-Path $Dest $name)
}
foreach ($name in @('templates', 'static', 'tests', 'docs')) {
    Copy-Item (Join-Path $Root $name) (Join-Path $Dest $name) -Recurse
}

# Offline wheels so the target PC never needs the internet on first run.
# MarkupSafe ships version-specific Windows wheels, so fetch Python 3.10-3.13.
$Wheels = Join-Path $Dest 'wheels'
New-Item -ItemType Directory -Force -Path $Wheels | Out-Null
foreach ($Version in @('3.10', '3.11', '3.12', '3.13')) {
    $Abi = 'cp' + $Version.Replace('.', '')
    & $PythonExe -m pip download --only-binary=:all: `
        --platform win_amd64 --python-version $Version `
        --implementation cp --abi $Abi `
        -r (Join-Path $Dest 'requirements.txt') -d $Wheels
    if ($LASTEXITCODE -ne 0) {
        throw ('pip download failed for Python ' + $Version + ' - check internet on the build machine.')
    }
}

# Bundle the ngspice installation made by setup.ps1.
$NgSrc = Join-Path $env:LOCALAPPDATA 'ngspice\Spice64'
if (Test-Path $NgSrc) {
    $NgDst = Join-Path $Dest 'tools\ngspice\Spice64'
    New-Item -ItemType Directory -Force -Path $NgDst | Out-Null
    Copy-Item (Join-Path $NgSrc '*') $NgDst -Recurse -Force
} else {
    Write-Host 'WARNING: ngspice not found in %LOCALAPPDATA%. The target PC will need its own copy.' -ForegroundColor Yellow
}

# Launcher: creates .venv from the bundled wheels on first run, then starts Flask.
$Launcher = @'
@echo off
setlocal
cd /d "%~dp0"
set "NGSPICE_BIN=%~dp0tools\ngspice\Spice64\bin\ngspice_con.exe"
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (python -m venv .venv) else (py -3 -m venv .venv)
    call ".venv\Scripts\python.exe" -m pip install --upgrade pip
    call ".venv\Scripts\python.exe" -m pip install --no-index --find-links="%~dp0wheels" -r requirements.txt
)
start "" http://127.0.0.1:5000/simulator
call ".venv\Scripts\python.exe" run_app.py
pause
'@
$Launcher | Set-Content (Join-Path $Dest 'run.bat') -Encoding ASCII

$Readme = @'
# Portable bundle - Lab 04 BJT Amplifier Simulator

1. Copy this folder OUT of the USB stick to the target PC first (e.g. Desktop).
2. The target PC needs Python 3.10+ (`py -3` or `python` on PATH).
3. Double-click run.bat. On first run it creates .venv and installs Flask from
   the bundled `wheels` folder (offline), then opens
   http://127.0.0.1:5000/simulator for you. Later runs are faster.
4. If ngspice does not start, set environment variable NGSPICE_BIN to the
   full path of ngspice_con.exe before running run.bat.

No internet is needed on the target PC. See docs\validation.md and README.md
for the real browser/ngspice evidence.
'@
$Readme | Set-Content (Join-Path $Dest 'PORTABLE-README.md') -Encoding ASCII

New-Item -ItemType Directory -Force -Path (Split-Path $Zip) | Out-Null
Compress-Archive -Path (Join-Path $Dest '*') -DestinationPath $Zip -CompressionLevel Optimal -Force

Write-Host "`nDone." -ForegroundColor Green
Write-Host ('Folder: ' + $Dest)
Write-Host ('ZIP   : ' + $Zip)
