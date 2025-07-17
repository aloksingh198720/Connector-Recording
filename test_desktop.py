#!/usr/bin/env python3
"""
Test script for Connector Recording Desktop Application
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing Python imports...")
    
    try:
        import pyautogui
        print("✅ pyautogui imported successfully")
    except ImportError as e:
        print(f"❌ pyautogui import failed: {e}")
        return False
    
    try:
        import cv2
        print("✅ opencv-python imported successfully")
    except ImportError as e:
        print(f"❌ opencv-python import failed: {e}")
        return False
    
    try:
        import mss
        print("✅ mss imported successfully")
    except ImportError as e:
        print(f"❌ mss import failed: {e}")
        return False
    
    try:
        import psutil
        print("✅ psutil imported successfully")
    except ImportError as e:
        print(f"❌ psutil import failed: {e}")
        return False
    
    try:
        import PIL
        print("✅ pillow imported successfully")
    except ImportError as e:
        print(f"❌ pillow import failed: {e}")
        return False
    
    try:
        import numpy
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    return True

def test_directories():
    """Test if required directories exist"""
    print("\n📁 Testing directories...")
    
    # Check if screenshots directory exists
    screenshots_dir = Path("screenshots")
    if screenshots_dir.exists():
        print("✅ screenshots directory exists")
    else:
        print("📁 Creating screenshots directory...")
        screenshots_dir.mkdir(exist_ok=True)
        print("✅ screenshots directory created")
    
    # Check if python_backend directory exists
    backend_dir = Path("python_backend")
    if backend_dir.exists():
        print("✅ python_backend directory exists")
    else:
        print("❌ python_backend directory not found")
        return False
    
    # Check if desktop_app.py exists
    desktop_app = backend_dir / "desktop_app.py"
    if desktop_app.exists():
        print("✅ desktop_app.py exists")
    else:
        print("❌ desktop_app.py not found")
        return False
    
    return True

def test_desktop_app():
    """Test if the desktop app can be imported"""
    print("\n🎯 Testing desktop application...")
    
    try:
        sys.path.append(str(Path("python_backend")))
        from desktop_app import DesktopAutomationApp
        print("✅ DesktopAutomationApp imported successfully")
        
        # Test creating an instance
        app = DesktopAutomationApp()
        print("✅ DesktopAutomationApp instance created successfully")
        
        # Test health check
        health = app.health_check()
        print(f"✅ Health check: {health}")
        
        return True
    except Exception as e:
        print(f"❌ Desktop app test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎯 Connector Recording - Desktop Application Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        return 1
    
    # Test directories
    if not test_directories():
        print("\n❌ Directory tests failed.")
        return 1
    
    # Test desktop app
    if not test_desktop_app():
        print("\n❌ Desktop app tests failed.")
        return 1
    
    print("\n🎉 All tests passed! Desktop application is ready to run.")
    print("\n🚀 To start the application:")
    print("   npm run dev")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 