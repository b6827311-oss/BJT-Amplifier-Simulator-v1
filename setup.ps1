# setup.ps1 -- Fresh-PC setup for ENG29 2121 Lab 04
# Creates the venv, installs Flask, and installs ngspice 47 into
# %LOCALAPPDATA%\ngspice (no administrator rights required).
# Run:  powershell -ExecutionPolicy Bypass -File .\setup.ps1
# NOTE: this file is intentionally ASCII-only so Windows PowerShell 5.1
#       parses it correctly regardless of the machine's ANSI code page.

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Step([string] $Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

$PythonExe = Join-Path $Root '.venv\Scripts\python.exe'
$NgspiceExe = Join-Path $env:LOCALAPPDATA 'ngspice\Spice64\bin\ngspice_con.exe'
$ArchiveHash = '59225971BD68CDD1199443649AA4615A9E6D684933F205AB49006A3942518F5A'
$NgspiceUrl = 'https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/ngspice-47_64.7z/download'
$SevenZipUrl = 'https://www.7-zip.org/a/7zr.exe'

# ---------------------------------------------------------------------------
Step '1/4  Python venv'
# ---------------------------------------------------------------------------
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m venv .venv
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python -m venv .venv
} else {
    throw 'Python 3.10+ not found. Install Python, reopen the terminal, then run setup.ps1 again.'
}
if (-not (Test-Path $PythonExe)) {
    throw ('Failed to create venv. Expected: ' + $PythonExe)
}

# ---------------------------------------------------------------------------
Step '2/4  Python dependencies'
# ---------------------------------------------------------------------------
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r (Join-Path $Root 'requirements.txt')

# ---------------------------------------------------------------------------
Step '3/4  ngspice 47'
# ---------------------------------------------------------------------------
if (Test-Path $NgspiceExe) {
    Write-Host ('ngspice already present: ' + $NgspiceExe)
} else {
    $Work = Join-Path $env:TEMP 'bjt-lab04-ngspice'
    New-Item -ItemType Directory -Force -Path $Work | Out-Null

    $Archive = Join-Path $Work 'ngspice-47_64.7z'
    $SevenZip = Join-Path $Work '7zr.exe'

    if (-not (Test-Path $SevenZip)) {
        Write-Host ('Downloading 7zr.exe from ' + $SevenZipUrl)
        & curl.exe -L --fail --retry 3 -o $SevenZip $SevenZipUrl
        if ($LASTEXITCODE -ne 0) { throw 'Failed to download 7zr.exe' }
    }

    $HashOk = (Test-Path $Archive) -and
              ((Get-FileHash $Archive -Algorithm SHA256).Hash -eq $ArchiveHash)
    if (-not $HashOk) {
        Write-Host ('Downloading ngspice 47 from ' + $NgspiceUrl + ' (13.8 MB)')
        & curl.exe -L --fail --retry 3 -o $Archive $NgspiceUrl
        if ($LASTEXITCODE -ne 0) { throw 'Failed to download ngspice' }
        $HashOk = ((Get-FileHash $Archive -Algorithm SHA256).Hash -eq $ArchiveHash)
        if (-not $HashOk) {
            throw 'SHA-256 mismatch for downloaded ngspice archive. Do NOT extract it.'
        }
    }

    New-Item -ItemType Directory -Force -Path (Split-Path $NgspiceExe) | Out-Null
    Write-Host ('Extracting ngspice to ' + $env:LOCALAPPDATA + '\ngspice')
    & $SevenZip x $Archive ("-o" + $env:LOCALAPPDATA + '\ngspice') -y | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Failed to extract ngspice' }
}

if (-not (Test-Path $NgspiceExe)) {
    throw ('ngspice still not found at ' + $NgspiceExe)
}
& $NgspiceExe -v

# ---------------------------------------------------------------------------
Step '4/4  Verify with unittest'
# ---------------------------------------------------------------------------
& $PythonExe -m unittest discover -s tests

Write-Host "`nDone." -ForegroundColor Green
Write-Host 'Start the server with:  .\run.ps1'
Write-Host 'Then open http://127.0.0.1:5000/simulator'
