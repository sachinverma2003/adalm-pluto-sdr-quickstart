@echo off
setlocal EnableDelayedExpansion
title ADALM-PLUTO SDR Quick Runner
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

:: If user passed a script path via CLI (e.g. run.bat examples\my_script.py), execute directly
if "%~1" neq "" (
    ".venv\Scripts\python.exe" %*
    exit /b %errorlevel%
)

:: Interactive Quick Menu if double-clicked without arguments
:menu
cls
echo ================================================================
echo               ADALM-PLUTO SDR Quick Launcher
echo ================================================================
echo.
echo   [1] Hello Pluto (Connectivity and Basic Info)
echo   [2] TX/RX Loopback Tone (FFT Spectrum Plot)
echo   [3] Hardware Diagnostics ^& Benchmark (Temp, Speed, AD9364 Probe)
echo   [4] Launch Interactive Python Shell (with pyadi-iio)
echo   [5] Exit
echo.
echo ================================================================
set /p "CHOICE=Select an option [1-5]: "

if "%CHOICE%"=="1" (
    cls
    echo Running examples\hello_pluto.py ...
    echo.
    ".venv\Scripts\python.exe" "examples\hello_pluto.py"
    echo.
    pause
    goto menu
)

if "%CHOICE%"=="2" (
    cls
    echo Running examples\tx_rx_loopback.py ...
    echo.
    ".venv\Scripts\python.exe" "examples\tx_rx_loopback.py"
    echo.
    pause
    goto menu
)

if "%CHOICE%"=="3" (
    cls
    echo Running scripts\pluto_diagnostics.py ...
    echo.
    ".venv\Scripts\python.exe" "scripts\pluto_diagnostics.py"
    echo.
    pause
    goto menu
)

if "%CHOICE%"=="4" (
    cls
    echo Starting Python interactive session with pyadi-iio...
    echo Tip: 'import adi, iio; sdr = adi.Pluto(uri=\"ip:192.168.2.1\")'
    echo.
    ".venv\Scripts\python.exe"
    goto menu
)

if "%CHOICE%"=="5" exit /b 0

goto menu
