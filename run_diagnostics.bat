@echo off
setlocal
title ADALM-PLUTO SDR Diagnostics
cd /d "%~dp0"

set "PY_CMD="

:: 1. Check local virtual environment (.venv)
if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else (
    :: 2. Check system python if adi is available
    python -c "import adi" >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=python"
    ) else (
        :: 3. Check py launcher
        py -3 -c "import adi" >nul 2>&1
        if %errorlevel% equ 0 (
            set "PY_CMD=py -3"
        )
    )
)

if not defined PY_CMD (
    echo [!] pyadi-iio not found in local .venv or system Python.
    echo [*] Please run setup.bat to set up the environment automatically.
    echo.
    pause
    exit /b 1
)

%PY_CMD% "scripts\pluto_diagnostics.py"

echo.
pause
