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
Invoke-WebRequest -Uri $driverUrl -OutFile $driverExe

Write-Host "==> Installing driver silently (this may prompt for admin consent)"
Start-Process -FilePath $driverExe -ArgumentList "/S" -Wait

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "==> Python not found. Installing via winget..."
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    Write-Host "Python installed. Please re-open your terminal so PATH updates, then re-run this script."
    exit 0
}

Write-Host "==> Creating Python virtual environment"
python -m venv "$RepoRoot\.venv"
& "$RepoRoot\.venv\Scripts\pip.exe" install --upgrade pip
& "$RepoRoot\.venv\Scripts\pip.exe" install pyadi-iio numpy matplotlib

Write-Host ""
Write-Host "==> Plug in your PlutoSDR now if you haven't already."
Write-Host "    Windows should install the driver automatically and it will show up"
Write-Host "    as a network adapter (check Device Manager > Network adapters, or"
Write-Host "    Ports (COM & LPT) for the console)."
Read-Host "Press Enter once the device shows up in Device Manager"

Write-Host "==> Running hello_pluto.py"
try {
    & "$RepoRoot\.venv\Scripts\python.exe" "$RepoRoot\examples\hello_pluto.py"
} catch {
    Write-Host "Could not reach Pluto at ip:192.168.2.1 yet. Wait a few seconds and re-run:"
    Write-Host "  .venv\Scripts\python.exe examples\hello_pluto.py"
}

Write-Host ""
Write-Host "==> Done. In VS Code: open this folder, run 'Python: Select Interpreter',"
Write-Host "    choose: $RepoRoot\.venv\Scripts\python.exe"
