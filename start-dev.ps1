Write-Host "Starting Connector Recording Desktop Development Environment..."

# Start Vite dev server
Write-Host "Starting Vite development server..."
Start-Process powershell -ArgumentList "npm run dev:renderer"

# Wait for Vite to be ready
Start-Sleep -Seconds 4

# Start Electron app
Write-Host "Starting Electron app..."
Start-Process powershell -ArgumentList "npm run dev:electron"

Write-Host "Development environment started!"
Write-Host "Vite server is running on http://localhost:3000"
Write-Host "Electron app should open automatically"
Write-Host "Press Ctrl+C to stop all processes..." 