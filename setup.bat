@echo off
setlocal EnableDelayedExpansion
title ADALM-PLUTO SDR Setup
cd /d "%~dp0"

echo ================================================================
echo           ADALM-PLUTO SDR 1-Click Setup for Windows
echo ================================================================
echo.

:: Check Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Administrator privileges required for USB driver and libiio setup.
    echo [*] Requesting Windows UAC permission...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd.exe -ArgumentList '/c cd /d \"\"%~dp0\"\" && \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

:: Elevated execution
echo [+] Running with Administrator privileges.
echo [+] Launching PowerShell setup engine...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows_setup.ps1"
set SETUP_EXIT_CODE=%errorlevel%

echo.
echo ================================================================
if %SETUP_EXIT_CODE% equ 0 (
    echo [SUCCESS] Setup completed successfully!
    echo.
    echo Next steps:
    echo   1. In VS Code: Open this folder
    echo   2. Press Ctrl+Shift+P -^> 'Python: Select Interpreter'
    echo   3. Choose: %~dp0.venv\Scripts\python.exe
    echo   4. Run 'run_diagnostics.bat' or 'examples\hello_pluto.py'
) else (
    echo [ERROR] Setup encountered an issue (Exit Code: %SETUP_EXIT_CODE%).
    echo Please review the messages above for details.
)
echo ================================================================
echo.
pause
exit /b %SETUP_EXIT_CODE%
