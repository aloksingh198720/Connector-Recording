#!/usr/bin/env python3
"""
Connector Recording - Simple Launcher
"""

import sys
import os
from pathlib import Path

def main():
    """Main launcher function"""
    print("🎯 Connector Recording - Desktop Automation")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("python_backend/desktop_app.py").exists():
        print("❌ Error: desktop_app.py not found!")
        print("   Please run this script from the project root directory.")
        return 1
    
    # Check if requirements are installed
    try:
        import pyautogui
        import cv2
        import mss
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install dependencies with: pip install -r requirements.txt")
        return 1
    
    # Create screenshots directory if it doesn't exist
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting desktop automation application...")
    print("💡 Press Ctrl+C to stop the application")
    print()
    
    try:
        # Import and run the desktop app
        sys.path.append(str(Path("python_backend")))
        from desktop_app import main as desktop_main
        desktop_main()
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 