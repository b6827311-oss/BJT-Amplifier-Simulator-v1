# run.ps1 -- Start the Flask server for Lab 04
# Run .\setup.ps1 once before using this script.
# ASCII-only on purpose (Windows PowerShell 5.1 code-page safety).

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$PythonExe = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $PythonExe)) {
    throw '.venv not found. Run .\setup.ps1 first.'
}

$NgspiceExe = Join-Path $env:LOCALAPPDATA 'ngspice\Spice64\bin\ngspice_con.exe'
if (Test-Path $NgspiceExe) {
    $env:NGSPICE_BIN = $NgspiceExe
} else {
    Write-Host 'ngspice not in the usual location; spice_engine.py will search PATH / tools\ngspice.' -ForegroundColor Yellow
}

Write-Host 'Lab 03 : http://127.0.0.1:5000/' -ForegroundColor Cyan
Write-Host 'Lab 04 : http://127.0.0.1:5000/simulator' -ForegroundColor Cyan
& $PythonExe (Join-Path $Root 'run_app.py')
