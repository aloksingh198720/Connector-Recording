@echo off
echo Starting Connector Recording Desktop Development Environment...

echo Starting Vite development server in background...
start /b npm run dev:renderer > vite.log 2>&1

echo Waiting for Vite server to be ready...
timeout /t 5 /nobreak > nul

echo Starting Electron app in background...
start /b npm run dev:electron > electron.log 2>&1

echo Development environment started!
echo Vite server is running on http://localhost:3000
echo Electron app should open automatically
echo.
echo Logs are being written to vite.log and electron.log
echo.
echo Press any key to close all development processes...
pause > nul

echo Closing development environment...
taskkill /f /im node.exe > nul 2>&1
taskkill /f /im electron.exe > nul 2>&1
del vite.log electron.log > nul 2>&1
echo Done! 