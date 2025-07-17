#!/usr/bin/env python3
"""
Startup script for Connector Recording Desktop
Runs Python Flask backend first, then Electron app
"""

import subprocess
import sys
import time
import os
import signal
import threading
import requests
from pathlib import Path

def wait_for_backend(url="http://127.0.0.1:5000", max_attempts=30, delay=2):
    """Wait for the Flask backend to be ready"""
    print(f"Waiting for backend at {url}...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{url}/api/command", 
                                 json={"type": "health_check", "data": {}},
                                 timeout=5)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Attempt {attempt + 1}/{max_attempts}: Backend not ready yet...")
        time.sleep(delay)
    
    print("❌ Backend failed to start within expected time")
    return False

def start_python_backend():
    """Start the Python Flask backend"""
    print("🚀 Starting Python Flask backend...")
    backend_path = Path("python_backend/desktop_app.py")
    
    if not backend_path.exists():
        print(f"❌ Error: Backend file not found at {backend_path}")
        return None
    
    try:
        # Start the Flask backend
        process = subprocess.Popen([
            sys.executable, str(backend_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Python backend process started")
        return process
    except Exception as e:
        print(f"❌ Error starting Python backend: {e}")
        return None

def start_electron_app():
    """Start the Electron app"""
    print("🚀 Starting Electron app...")
    
    try:
        # Build React app first
        print("📦 Building React app...")
        build_process = subprocess.run(["npm", "run", "build"], 
                                      capture_output=True, text=True)
        
        if build_process.returncode != 0:
            print("❌ Error building React app:")
            print(build_process.stderr)
            return None
        
        print("✅ React app built successfully")
        
        # Start Electron in production mode
        print("⚡ Starting Electron...")
        electron_process = subprocess.Popen([
            "npm", "run", "electron"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Electron app started successfully")
        return electron_process
    except Exception as e:
        print(f"❌ Error starting Electron app: {e}")
        return None

def main():
    """Main startup function"""
    print("🎬 Connector Recording Desktop")
    print("=" * 50)
    
    # Start Python backend
    python_process = start_python_backend()
    if not python_process:
        print("❌ Failed to start Python backend. Exiting.")
        return
    
    # Wait for backend to be ready
    if not wait_for_backend():
        print("❌ Backend failed to start. Exiting.")
        python_process.terminate()
        return
    
    # Wait additional time for backend to fully initialize
    print("⏳ Waiting for backend to fully initialize...")
    time.sleep(3)
    
    # Start Electron app
    electron_process = start_electron_app()
    if not electron_process:
        print("❌ Failed to start Electron app. Exiting.")
        python_process.terminate()
        return
    
    print("\n🎉 Both services started successfully!")
    print("📱 Electron app should open automatically")
    print("🔧 Python backend running on http://127.0.0.1:5000")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Wait for either process to finish
        while True:
            if python_process.poll() is not None:
                print("❌ Python backend stopped")
                break
            if electron_process.poll() is not None:
                print("❌ Electron app stopped")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
    
    # Cleanup
    if python_process:
        python_process.terminate()
        python_process.wait()
    if electron_process:
        electron_process.terminate()
        electron_process.wait()
    
    print("✅ All services stopped")

if __name__ == "__main__":
    main() 