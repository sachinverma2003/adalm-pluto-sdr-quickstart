@echo off
setlocal
title ADALM-PLUTO SDR Setup
cd /d "%~dp0"

echo ================================================================
echo           ADALM-PLUTO SDR 1-Click Setup for Windows
echo ================================================================
echo.
echo Checking Administrator privileges...

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [*] Administrator privileges required for USB driver installation.
    echo [*] Prompting for Windows UAC permission...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd.exe -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

:: Elevated execution starts here
echo [+] Running with Administrator privileges.
echo [+] Launching PowerShell setup script...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows_setup.ps1"

echo.
echo ================================================================
echo Setup finished. Press any key to close this window.
echo ================================================================
pause >nul
