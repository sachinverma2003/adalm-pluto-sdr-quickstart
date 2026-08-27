@echo off
setlocal
title ADALM-PLUTO SDR Diagnostics
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" "scripts\pluto_diagnostics.py"

echo.
pause
