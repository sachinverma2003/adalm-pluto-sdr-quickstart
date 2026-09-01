@echo off
setlocal
title ADALM-PLUTO - Hello Pluto Example
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
echo             ADALM-PLUTO SDR - Hello Pluto
echo ================================================================
echo.

".venv\Scripts\python.exe" "examples\hello_pluto.py" %*

echo.
echo ================================================================
pause
