<#
PlutoSDR Quickstart Automated Setup for Windows
------------------------------------------------
1. Downloads & installs official ADI USB drivers (PlutoSDR-M2k-USB-Drivers)
2. Downloads & installs official ADI libiio Windows runtime
3. Detects/installs a clean Python environment (Python 3.10 - 3.12)
4. Configures a self-contained virtual environment (.venv)
5. Installs pyadi-iio, numpy, and matplotlib
6. Guarantees libiio.dll availability inside the venv
7. Self-tests imports (iio, adi) and tests Pluto hardware connectivity
#>

$ErrorActionPreference = "Stop"
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvDir  = Join-Path $RepoRoot ".venv"
$VenvPy   = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip  = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         ADALM-PLUTO SDR Windows 1-Click Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# Step 1: Install ADI PlutoSDR USB / RNDIS Drivers
# ------------------------------------------------------------
Write-Host "[1/7] Checking official ADI USB / RNDIS driver..." -ForegroundColor Yellow
$driverInstalled = Test-Path "C:\Program Files\Analog Devices\PlutoSDR-M2K"
if ($driverInstalled) {
    Write-Host "      [+] ADI USB driver package is already installed." -ForegroundColor Green
} else {
    Write-Host "      [*] Downloading ADI USB driver installer..." -ForegroundColor Gray
    $driverUrl = "https://github.com/analogdevicesinc/plutosdr-m2k-drivers-win/releases/latest/download/PlutoSDR-M2k-USB-Drivers.exe"
    $driverExe = Join-Path $env:TEMP "PlutoSDR-M2k-USB-Drivers.exe"
    try {
        Invoke-WebRequest -Uri $driverUrl -OutFile $driverExe -UseBasicParsing
        Write-Host "      [*] Installing ADI USB driver silently..." -ForegroundColor Gray
        Start-Process -FilePath $driverExe -ArgumentList "/S" -Wait
        Write-Host "      [+] ADI USB driver installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Host "      [!] Warning: Could not auto-download USB driver: $_" -ForegroundColor DarkYellow
    }
}

# ------------------------------------------------------------
# Step 2: Install Official ADI libiio Windows Runtime
# ------------------------------------------------------------
Write-Host ""
Write-Host "[2/7] Checking official libiio Windows runtime..." -ForegroundColor Yellow
$hasLibiioSystem = (Test-Path "C:\Windows\System32\libiio.dll") -or (Test-Path "C:\Program Files\libiio\libiio.dll")

if ($hasLibiioSystem) {
    Write-Host "      [+] libiio native runtime is present on this system." -ForegroundColor Green
} else {
    Write-Host "      [*] Downloading official ADI libiio installer from GitHub..." -ForegroundColor Gray
    try {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/analogdevicesinc/libiio/releases/latest" -UseBasicParsing
        $setupAsset = $release.assets | Where-Object { $_.name -like "*setup.exe" } | Select-Object -First 1

        if ($setupAsset) {
            $libiioUrl = $setupAsset.browser_download_url
        } else {
            $libiioUrl = "https://github.com/analogdevicesinc/libiio/releases/download/v0.26/libiio-0.26.ga0eca0d2-setup.exe"
        }

        $libiioExe = Join-Path $env:TEMP "libiio-setup.exe"
        Invoke-WebRequest -Uri $libiioUrl -OutFile $libiioExe -UseBasicParsing
        Write-Host "      [*] Installing libiio runtime silently..." -ForegroundColor Gray
        Start-Process -FilePath $libiioExe -ArgumentList "/S" -Wait
        Write-Host "      [+] libiio runtime installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Host "      [!] Warning: Could not auto-install libiio installer: $_" -ForegroundColor DarkYellow
    }
}

# ------------------------------------------------------------
# Step 3: Locate or Install Python (Standard CPython)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[3/7] Locating suitable Python runtime..." -ForegroundColor Yellow

$pythonCmd = $null

# 1. Try py launcher with explicit 3.12 or 3.11
foreach ($v in @("-3.12", "-3.11", "-3.10", "-3")) {
    try {
        $ver = (& py $v --version 2>&1)
        if ($ver -match "Python 3\.(10|11|12)") {
            $pythonCmd = @("py", $v)
            Write-Host "      [+] Found Python via launcher: $ver (using py $v)" -ForegroundColor Green
            break
        }
    }
    catch {}
}

# 2. Try standard python.exe (ignore Microsoft Store dummy stub)
if (-not $pythonCmd) {
    try {
        $pyPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        if ($pyPath -and $pyPath -notmatch "WindowsApps") {
            $ver = (& python --version 2>&1)
            if ($ver -match "Python 3\.") {
                $pythonCmd = @("python")
                Write-Host "      [+] Found standard Python: $ver ($pyPath)" -ForegroundColor Green
            }
        }
    }
    catch {}
}

# 3. If Python not found or only store stub present, install via winget
if (-not $pythonCmd) {
    Write-Host "      [*] Compatible Python 3.12 not found. Installing via winget..." -ForegroundColor Gray
    try {
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        Write-Host "      [+] Python 3.12 installed." -ForegroundColor Green
        $pythonCmd = @("py", "-3.12")
    }
    catch {
        Write-Host "      [!] winget install failed. Please install Python 3.11 or 3.12 from python.org." -ForegroundColor Red
        exit 1
    }
}

# ------------------------------------------------------------
# Step 4: Create or Verify Virtual Environment (.venv)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[4/7] Setting up Python virtual environment (.venv)..." -ForegroundColor Yellow

$needNewVenv = $true
if (Test-Path $VenvPy) {
    try {
        $existingVer = (& $VenvPy --version 2>&1)
        # Python 3.10, 3.11, 3.12 are fully verified for pyadi-iio
        if ($existingVer -match "Python 3\.(10|11|12)") {
            Write-Host "      [+] Existing .venv is healthy: $existingVer" -ForegroundColor Green
            $needNewVenv = $false
        } else {
            Write-Host "      [*] Existing .venv uses incompatible $existingVer. Rebuilding..." -ForegroundColor DarkYellow
        }
    }
    catch {
        $needNewVenv = $true
    }
}

if ($needNewVenv) {
    if (Test-Path $VenvDir) {
        Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
    }
    Write-Host "      [*] Creating virtual environment in $VenvDir..." -ForegroundColor Gray
    & $pythonCmd[0] $pythonCmd[1..($pythonCmd.Length-1)] -m venv $VenvDir
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPy)) {
        Write-Host "      [!] Error: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "      [+] Virtual environment created successfully." -ForegroundColor Green
}

# ------------------------------------------------------------
# Step 5: Install Python Dependencies & Bundle libiio.dll
# ------------------------------------------------------------
Write-Host ""
Write-Host "[5/7] Installing Python dependencies (pyadi-iio, numpy, matplotlib)..." -ForegroundColor Yellow
& $VenvPy -m pip install --upgrade pip --quiet
& $VenvPy -m pip install -r "$RepoRoot\requirements.txt" --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "      [!] Error: pip install failed. Please check your internet connection." -ForegroundColor Red
    exit 1
}
Write-Host "      [+] Python packages installed." -ForegroundColor Green

# Locate and bundle libiio.dll into .venv so it's 100% self-contained
Write-Host "      [*] Bundling libiio.dll into .venv for guaranteed DLL discovery..." -ForegroundColor Gray
$dllSources = @(
    "C:\Windows\System32\libiio.dll",
    "C:\Program Files\libiio\libiio.dll",
    "C:\Program Files (x86)\libiio\libiio.dll",
    "C:\Program Files\PothosSDR\bin\libiio.dll"
)
$foundDll = $null
foreach ($src in $dllSources) {
    if (Test-Path $src) {
        $foundDll = $src
        break
    }
}

if ($foundDll) {
    $venvScripts = Join-Path $VenvDir "Scripts"
    $venvSitePackages = Join-Path $VenvDir "Lib\site-packages"
    Copy-Item $foundDll -Destination (Join-Path $venvScripts "libiio.dll") -Force -ErrorAction SilentlyContinue
    if (Test-Path $venvSitePackages) {
        Copy-Item $foundDll -Destination (Join-Path $venvSitePackages "libiio.dll") -Force -ErrorAction SilentlyContinue
    }
    Write-Host "      [+] libiio.dll configured inside virtual environment." -ForegroundColor Green
} else {
    Write-Host "      [!] Note: libiio.dll not found in standard system locations." -ForegroundColor DarkYellow
}

# ------------------------------------------------------------
# Step 6: Automated Self-Test (Verify iio and adi imports)
# ------------------------------------------------------------
Write-Host ""
Write-Host "[6/7] Verifying Python bindings (import iio, import adi)..." -ForegroundColor Yellow

$testScript = "import iio, adi; print('OK')"
$testResult = try { (& $VenvPy -c $testScript 2>&1) } catch { $_ }

if ($LASTEXITCODE -ne 0 -or $testResult -notmatch "OK") {
    Write-Host "      [!] ERROR: Python failed to load libiio library." -ForegroundColor Red
    Write-Host "      Details: $testResult" -ForegroundColor Red
    Write-Host ""
    Write-Host "      Remediation:" -ForegroundColor Yellow
    Write-Host "      1. Download and run libiio Windows installer from:" -ForegroundColor Yellow
    Write-Host "         https://github.com/analogdevicesinc/libiio/releases/latest" -ForegroundColor Yellow
    Write-Host "      2. Then re-run setup.bat" -ForegroundColor Yellow
    exit 1
}

Write-Host "      [+] Python environment verified: libiio and pyadi-iio loaded successfully!" -ForegroundColor Green

# ------------------------------------------------------------
# Step 7: Pluto Hardware Check & First Run
# ------------------------------------------------------------
Write-Host ""
Write-Host "[7/7] Checking ADALM-PLUTO Hardware Connection..." -ForegroundColor Yellow
Write-Host ""
Write-Host "      -------------------------------------------------------" -ForegroundColor Cyan
Write-Host "      Connect your ADALM-PLUTO now:" -ForegroundColor Cyan
Write-Host "        * Middle port labeled 'USB' (Carries Data + Power)" -ForegroundColor Cyan
Write-Host "        * Do NOT use the outer 'POWER' port for PC connection" -ForegroundColor Cyan
Write-Host "      -------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""

$plutoIp = "192.168.2.1"
$plutoOnline = $false

Write-Host "      Scanning for Pluto at $plutoIp (waiting up to 15 seconds for boot)..." -ForegroundColor Gray

for ($i = 1; $i -le 8; $i++) {
    $pingOk = Test-Connection -ComputerName $plutoIp -Count 1 -Quiet -ErrorAction SilentlyContinue
    if ($pingOk) {
        $plutoOnline = $true
        break
    }
    Start-Sleep -Seconds 2
}

if ($plutoOnline) {
    Write-Host "      [+] Pluto detected at $plutoIp! Running hello_pluto.py..." -ForegroundColor Green
    Write-Host ""
    & $VenvPy "$RepoRoot\examples\hello_pluto.py"
} else {
    Write-Host "      [*] Pluto not detected at $plutoIp yet (Device may still be booting or unplugged)." -ForegroundColor DarkYellow
    Write-Host "      Once the Pluto LED is steady, test connection with:" -ForegroundColor White
    Write-Host "        .venv\Scripts\python.exe examples\hello_pluto.py" -ForegroundColor Cyan
    Write-Host "      Or run diagnostics with:" -ForegroundColor White
    Write-Host "        run_diagnostics.bat" -ForegroundColor Cyan
}

Write-Host ""
exit 0
