#Requires -RunAsAdministrator
<#
PlutoSDR quickstart setup for Windows.
- Downloads + silently installs ADI's official USB driver package
- Creates a Python venv with pyadi-iio and runs a hello-world test
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "==> Downloading official ADI Windows USB driver (PlutoSDR-M2k-USB-Drivers)"
$driverUrl = "https://github.com/analogdevicesinc/plutosdr-m2k-drivers-win/releases/latest/download/PlutoSDR-M2k-USB-Drivers.exe"
$driverExe = Join-Path $env:TEMP "PlutoSDR-M2k-USB-Drivers.exe"
Invoke-WebRequest -Uri $driverUrl -OutFile $driverExe -UseBasicParsing

Write-Host "==> Installing driver silently (this may prompt for admin consent)"
Start-Process -FilePath $driverExe -ArgumentList "/S" -Wait

# Locate a working Python interpreter (handle Windows Store stub vs real Python)
$pythonExe = $null
$testPy = try { (& python --version 2>&1) } catch { $null }
if ($testPy -match "Python 3") {
    $pythonExe = "python"
} else {
    $testPyLauncher = try { (& py -3 --version 2>&1) } catch { $null }
    if ($testPyLauncher -match "Python 3") {
        $pythonExe = "py -3"
    }
}

if (-not $pythonExe) {
    Write-Host "==> Working Python 3 not found. Installing via winget..."
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    Write-Host "Python installed. Please re-open your terminal so PATH updates, then re-run this script."
    exit 0
}

Write-Host "==> Creating Python virtual environment in .venv"
if ($pythonExe -eq "py -3") {
    py -3 -m venv "$RepoRoot\.venv"
} else {
    python -m venv "$RepoRoot\.venv"
}

$venvPip = Join-Path $RepoRoot ".venv\Scripts\pip.exe"
$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"

& $venvPip install --upgrade pip
& $venvPip install -r "$RepoRoot\requirements.txt"

Write-Host ""
Write-Host "==> Plug in your PlutoSDR now if you haven't already."
Write-Host "    IMPORTANT: Plug into the middle port labeled 'USB' (not 'POWER')."
Write-Host "    Windows will enumerate it as a network adapter at 192.168.2.1."
Read-Host "Press Enter once the device is plugged in and ready"

Write-Host "==> Running hello_pluto.py..."
& $venvPy "$RepoRoot\examples\hello_pluto.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Note: Could not reach Pluto at ip:192.168.2.1 immediately."
    Write-Host "Pluto takes 15-20 seconds to boot up. Once LED is steady, re-run:"
    Write-Host "  .venv\Scripts\python.exe examples\hello_pluto.py"
}

Write-Host ""
Write-Host "==> Done. In VS Code: open this folder, run 'Python: Select Interpreter',"
Write-Host "    choose: $RepoRoot\.venv\Scripts\python.exe"
