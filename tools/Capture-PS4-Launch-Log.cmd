@echo off
setlocal
title PS MTP Explorer - Launch Log Collector
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect-PS4LaunchLog.ps1"
echo.
pause
