@echo off
setlocal
title ADALM-PLUTO - TX/RX Loopback Example
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment (.venv) not found.
    echo [*] Running setup.bat first to configure the environment...
    echo.
    call setup.bat
    if not exist ".venv\Scripts\python.exe" (
        echo [!] Setup was not completed.
        pause
        exit /b 1
    )
)

echo ================================================================
echo         ADALM-PLUTO SDR - TX/RX Loopback Spectrum Plot
echo ================================================================
echo.

".venv\Scripts\python.exe" "examples\tx_rx_loopback.py" %*

echo.
echo ================================================================
pause
