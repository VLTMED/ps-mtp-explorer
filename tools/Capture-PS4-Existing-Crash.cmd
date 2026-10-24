@echo off
setlocal
title PS MTP Explorer - Existing Crash Log
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect-PS4LaunchLog.ps1" -ExistingCrash -Seconds 30
echo.
pause
