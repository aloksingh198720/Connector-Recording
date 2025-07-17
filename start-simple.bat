@echo off
echo Starting Connector Recording Desktop...

start /b npm run dev:renderer >nul 2>&1
timeout /t 3 /nobreak >nul
start /b npm run dev:electron >nul 2>&1

echo App started! Press any key to stop...
pause >nul

taskkill /f /im node.exe >nul 2>&1
taskkill /f /im electron.exe >nul 2>&1
echo Stopped. 