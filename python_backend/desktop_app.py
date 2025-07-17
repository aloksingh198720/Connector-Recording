from flask import Flask, request, jsonify
from flask_cors import CORS
import psutil
import os
import time
from datetime import datetime
import threading
import pyautogui
import cv2
import mss
from PIL import Image
import numpy as np
from pathlib import Path
import uuid
import json
import subprocess
import re

app = Flask(__name__)
CORS(app)

# Global variables
recording = False
screenshots_dir = Path("screenshots")  # Point to main screenshots folder
current_app = None

# Ensure screenshots directory exists
screenshots_dir.mkdir(exist_ok=True)

# Configure pyautogui for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

@app.route('/api/command', methods=['POST'])
def handle_command():
    try:
        command = request.json
        command_type = command.get('type')
        data = command.get('data', {})
        
        if command_type == 'get_running_apps':
            return get_running_apps()
        elif command_type == 'launch_app':
            return launch_app(data.get('exe_path'))
        elif command_type == 'focus_window':
            return focus_window(data.get('title_keywords', []))
        elif command_type == 'capture_screenshot':
            return capture_screenshot(data.get('application'), data.get('region'))
        elif command_type == 'start_region_selection':
            return start_region_selection(data.get('application'))
        elif command_type == 'capture_region_screenshot':
            return capture_region_screenshot(data.get('region'))
        elif command_type == 'save_screenshot_with_metadata':
            return save_screenshot_with_metadata(data.get('filepath'), data.get('name'), data.get('description'), data.get('application_name'))
        elif command_type == 'start_system_region_selection':
            return start_system_region_selection(data.get('application'))
        elif command_type == 'get_last_capture_result':
            return get_last_capture_result()
        elif command_type == 'create_session_json':
            return create_session_json(data.get('application_name'), data.get('application_path'), data.get('screenshots'))
        elif command_type == 'organize_screenshots_by_app':
            return organize_screenshots_by_app(data.get('application_name'))
        elif command_type == 'remove_screenshot':
            return remove_screenshot(data.get('filepath'))
        elif command_type == 'start_visual_region_selection':
            return start_visual_region_selection(data.get('application'))
        elif command_type == 'start_recording':
            return start_recording(data.get('application'))
        elif command_type == 'stop_recording':
            return stop_recording()
        elif command_type == 'get_screenshots':
            return get_screenshots()
        elif command_type == 'get_windows':
            return get_windows()
        elif command_type == 'health_check':
            return health_check()
        elif command_type == 'clear_all_screenshots':
            return clear_all_screenshots()
        elif command_type == 'read_json_file':
            return read_json_file(data.get('filepath'))
        elif command_type == 'check_file_exists':
            return check_file_exists(data.get('filepath'))
        elif command_type == 'cleanup_old_json_files':
            return cleanup_old_json_files(data.get('application_name'))
        elif command_type == 'cleanup_duplicate_screenshots':
            return cleanup_duplicate_screenshots(data.get('application_name'))
        else:
            return jsonify({'success': False, 'error': f'Unknown command: {command_type}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def launch_app(exe_path):
    """Launch an application by path"""
    try:
        # Clean and normalize the path - remove quotes and extra spaces
        exe_path = exe_path.strip().strip('"').strip("'")
        exe_path = os.path.normpath(exe_path)
        
        print(f"Attempting to launch: {exe_path}")
        print(f"File exists: {os.path.exists(exe_path)}")
        
        if not exe_path:
            return jsonify({'success': False, 'error': 'No application path provided'})
        
        if not os.path.exists(exe_path):
            return jsonify({'success': False, 'error': f'Application not found: {exe_path}'})
        
        # Launch the application with proper shell handling for paths with spaces
        if os.name == 'nt':  # Windows
            process = subprocess.Popen([exe_path], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     shell=True)
        else:  # Unix/Linux
            process = subprocess.Popen([exe_path], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
        
        # Wait a bit for the app to start
        time.sleep(2)
        
        return jsonify({
            'success': True,
            'message': f'Application launched: {os.path.basename(exe_path)}',
            'pid': process.pid
        })
        
    except Exception as e:
        error_msg = f'Error launching application: {str(e)}'
        print(error_msg)
        return jsonify({'success': False, 'error': error_msg})

def focus_window(title_keywords):
    """Focus a window by title keywords"""
    try:
        import win32gui
        import win32con
        import win32api
        import time
        
        found_windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_title and any(keyword.lower() in window_title.lower() for keyword in title_keywords):
                    windows.append((hwnd, window_title))
            return True  # Continue enumeration
        
        win32gui.EnumWindows(enum_windows_callback, found_windows)
        
        if found_windows:
            # Focus the first matching window
            hwnd, title = found_windows[0]
            
            # More aggressive window focusing
            try:
                # 1. Restore the window if it's minimized
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)
                
                # 2. Set the window as foreground
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                
                # 3. Bring window to top
                win32gui.BringWindowToTop(hwnd)
                time.sleep(0.1)
                
                # 4. Set focus to the window
                win32gui.SetFocus(hwnd)
                time.sleep(0.1)
                
                # 5. Force the window to be active
                win32api.SendMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
                
                # 6. Additional attempt to bring to front
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                time.sleep(0.1)
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                
            except Exception as focus_error:
                print(f"Focus error: {focus_error}")
            
            return jsonify({
                'success': True, 
                'window_focused': True,
                'message': f'Window focused: {title}',
                'window_title': title
            })
        else:
            return jsonify({
                'success': False, 
                'window_focused': False,
                'message': f'No windows found matching keywords: {title_keywords}'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def health_check():
    """Health check for the backend"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'Backend is running'
    })

def get_running_apps():
    """Get list of running applications"""
    try:
        apps = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                # Get process info
                pinfo = proc.info
                if pinfo['name'] and pinfo['name'] != 'System Idle Process':
                    apps.append({
                        'name': pinfo['name'],
                        'pid': pinfo['pid'],
                        'windowTitle': pinfo['name'],  # Simplified - you might want to get actual window titles
                        'path': pinfo.get('exe', '')
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Remove duplicates and sort
        unique_apps = []
        seen_names = set()
        for app in apps:
            if app['name'] not in seen_names:
                seen_names.add(app['name'])
                unique_apps.append(app)
        
        unique_apps.sort(key=lambda x: x['name'])
        
        return jsonify({
            'success': True,
            'apps': unique_apps[:50]  # Limit to 50 apps
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_windows():
    """Get list of all visible windows for debugging"""
    try:
        import win32gui
        
        windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_title:  # Only include windows with titles
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_title,
                        'class_name': win32gui.GetClassName(hwnd)
                    })
            return True
        
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        # Sort by title
        windows.sort(key=lambda x: x['title'].lower())
        
        return jsonify({
            'success': True,
            'windows': windows[:50]  # Limit to 50 windows
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def capture_screenshot(application=None, region=None):
    """Capture screenshot for specific application or region"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if region:
            # Capture specific region
            filename = f"screenshot_region_{timestamp}.png"
            filepath = screenshots_dir / filename
            
            with mss.mss() as sct:
                monitor = {
                    "top": region["y"],
                    "left": region["x"],
                    "width": region["width"],
                    "height": region["height"]
                }
                screenshot = sct.grab(monitor)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
        else:
            # Capture entire screen
            filename = f"screenshot_{application or 'screen'}_{timestamp}.png"
            filepath = screenshots_dir / filename
            
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
        
        return jsonify({
            'success': True,
            'filepath': str(filepath.absolute()),
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def start_region_selection(application):
    """Start region selection process - focus the application first"""
    try:
        if application:
            print(f"Attempting to focus application: {application}")
            
            # Extract different possible window names
            exe_name = os.path.basename(application).replace('.exe', '')
            app_name = exe_name.replace('.exe', '')
            
            # Try multiple strategies to find and focus the window
            focus_strategies = [
                [application],  # Full path
                [exe_name],     # Just executable name
                [app_name],     # Without .exe
                [exe_name.lower()],  # Lowercase
                [app_name.lower()],  # Lowercase without .exe
            ]
            
            # Add specific patterns for known applications
            if 'SSMS' in application or 'sql' in application.lower():
                focus_strategies.extend([
                    ['Microsoft SQL Server Management Studio'],
                    ['SQL Server Management Studio'],
                    ['SSMS'],
                    ['Management Studio']
                ])
            elif 'chrome' in application.lower():
                focus_strategies.extend([
                    ['Chrome'],
                    ['Google Chrome'],
                    ['chrome.exe']
                ])
            elif 'firefox' in application.lower():
                focus_strategies.extend([
                    ['Firefox'],
                    ['Mozilla Firefox'],
                    ['firefox.exe']
                ])
            
            window_focused = False
            focused_window = None
            
            for strategy in focus_strategies:
                print(f"Trying focus strategy: {strategy}")
                focus_result = focus_window(strategy)
                
                if focus_result.json.get('window_focused', False):
                    window_focused = True
                    focused_window = focus_result.json.get('window_title', 'Unknown')
                    print(f"Successfully focused window: {focused_window}")
                    break
                else:
                    print(f"Strategy failed: {focus_result.json.get('message', 'Unknown error')}")
            
            if not window_focused:
                # Last resort: try to get all windows and find the best match
                print("Trying to get all windows for manual matching...")
                windows_response = get_windows()
                if windows_response.json.get('success'):
                    windows = windows_response.json.get('windows', [])
                    print(f"Found {len(windows)} windows")
                    
                    # Look for windows that might match our application
                    for window in windows:
                        window_title = window.get('title', '').lower()
                        if any(keyword.lower() in window_title for keyword in [exe_name, app_name]):
                            print(f"Found potential match: {window.get('title')}")
                            focus_result = focus_window([window.get('title')])
                            if focus_result.json.get('window_focused', False):
                                window_focused = True
                                focused_window = window.get('title')
                                break
        
        # Return success to indicate ready for region selection
        return jsonify({
            'success': True,
            'message': 'Ready for region selection',
            'application': application,
            'window_focused': window_focused,
            'focused_window': focused_window
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def capture_region_screenshot(region):
    """Capture screenshot of specific region"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"region_screenshot_{timestamp}.png"
        
        # Save to main screenshots directory (not python_backend/screenshots)
        filepath = screenshots_dir / filename
        
        with mss.mss() as sct:
            monitor = {
                "top": region["y"],
                "left": region["x"],
                "width": region["width"],
                "height": region["height"]
            }
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
        
        result = {
            'success': True,
            'filepath': str(filepath.absolute()),
            'filename': filename,
            'region': region
        }
        
        print(f"Region screenshot captured: {result}")
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Error capturing region screenshot: {str(e)}"
        print(error_msg)
        return jsonify({'success': False, 'error': error_msg})

def check_duplicate_screenshot(app_folder, clean_name):
    """Check if a screenshot with the same name already exists and return the existing file if found"""
    try:
        if not app_folder.exists():
            return None
        
        # Look for existing files with the same base name
        for file in app_folder.glob(f"{clean_name}_*.png"):
            return file
        
        return None
    except Exception as e:
        print(f"Error checking for duplicates: {e}")
        return None

def save_screenshot_with_metadata(filepath, name, description, application_name=None):
    """Save screenshot with metadata (name and description) and move to app folder"""
    try:
        import shutil
        # Clean application name for folder creation - remove invalid characters
        app_folder = screenshots_dir
        if application_name:
            clean_app_name = re.sub(r'[<>:"/\\|?*]', '_', application_name)
            clean_app_name = clean_app_name.replace('.exe', '').replace(' ', '_').strip('_')
            app_folder = screenshots_dir / clean_app_name
            app_folder.mkdir(exist_ok=True)
        
        # Move the screenshot to the app folder
        original_path = Path(filepath)
        if not original_path.exists():
            return jsonify({'success': False, 'error': 'Screenshot file not found'})
        
        # Create clean filename
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        
        # Check for existing screenshot with the same name
        existing_file = check_duplicate_screenshot(app_folder, clean_name)
        
        if existing_file:
            # If duplicate exists, remove the new file and return the existing one
            original_path.unlink()  # Remove the new screenshot
            return jsonify({
                'success': True,
                'message': 'Screenshot already exists, using existing file',
                'filepath': str(existing_file.absolute()),
                'is_duplicate': True
            })
        
        # Create new filename with timestamp
        new_filename = f"{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        new_path = app_folder / new_filename
        
        # Move file to app folder
        shutil.move(str(original_path), str(new_path))
        
        return jsonify({
            'success': True,
            'message': 'Screenshot saved successfully',
            'filepath': str(new_path.absolute()),
            'filename': new_filename,
            'is_duplicate': False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def start_system_region_selection(application):
    """Start system-wide region selection using Python overlay"""
    try:
        import tkinter as tk
        from tkinter import Canvas
        import threading
        
        if application:
            # Focus the application first
            focus_result = focus_window([application])
            if not focus_result.json.get('window_focused', False):
                # Try alternative approaches
                exe_name = os.path.basename(application).replace('.exe', '')
                focus_result = focus_window([exe_name])
        
        # Create a system-wide overlay window
        def create_overlay():
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.attributes('-alpha', 0.3)
            root.attributes('-topmost', True)
            root.configure(bg='black')
            
            canvas = Canvas(root, bg='black', highlightthickness=0)
            canvas.pack(fill='both', expand=True)
            
            start_x, start_y = 0, 0
            selection_rect = None
            
            def on_mouse_down(event):
                nonlocal start_x, start_y, selection_rect
                start_x, start_y = event.x, event.y
                if selection_rect:
                    canvas.delete(selection_rect)
                selection_rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, 
                                                      outline='#ff5722', width=2, dash=(5,5))
            
            def on_mouse_move(event):
                nonlocal selection_rect
                if selection_rect:
                    canvas.coords(selection_rect, start_x, start_y, event.x, event.y)
            
            def on_mouse_up(event):
                nonlocal selection_rect
                if selection_rect:
                    x1, y1, x2, y2 = canvas.coords(selection_rect)
                    x = min(x1, x2)
                    y = min(y1, y2)
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    
                    if width > 10 and height > 10:
                        # Capture the region
                        region = {'x': int(x), 'y': int(y), 'width': int(width), 'height': int(height)}
                        capture_result = capture_region_screenshot(region)
                        
                        # Store the result for the frontend to retrieve
                        global last_capture_result
                        last_capture_result = capture_result.json
                    
                root.destroy()
            
            def on_escape(event):
                root.destroy()
            
            canvas.bind('<Button-1>', on_mouse_down)
            canvas.bind('<B1-Motion>', on_mouse_move)
            canvas.bind('<ButtonRelease-1>', on_mouse_up)
            root.bind('<Escape>', on_escape)
            
            # Instructions
            instruction = canvas.create_text(root.winfo_screenwidth()//2, 50, 
                                          text="Click and drag to select a region. Press ESC to cancel.", 
                                          fill='white', font=('Arial', 16))
            
            root.mainloop()
        
        # Run the overlay in a separate thread
        overlay_thread = threading.Thread(target=create_overlay)
        overlay_thread.daemon = True
        overlay_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'System region selection started',
            'application': application
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Global variable to store last capture result
last_capture_result = None

def get_last_capture_result():
    """Get the result of the last system region capture"""
    global last_capture_result
    if last_capture_result:
        result = last_capture_result
        last_capture_result = None  # Clear after retrieving
        return jsonify(result)
    else:
        return jsonify({'success': False, 'error': 'No capture result available'})

def create_session_json(application_name, application_path, screenshots_data):
    """Create JSON file for session with organized structure"""
    try:
        # Clean application name for folder creation - remove invalid characters
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '_', application_name)
        clean_app_name = clean_app_name.replace('.exe', '').replace(' ', '_').strip('_')
        
        # Create application-specific folder
        app_folder = screenshots_dir / clean_app_name
        app_folder.mkdir(exist_ok=True)
        
        # Remove any existing JSON file for this application to ensure only one JSON
        existing_json = app_folder / f"{clean_app_name}.json"
        if existing_json.exists():
            existing_json.unlink()
            print(f"Removed existing JSON file: {existing_json}")
        
        # Create JSON structure
        json_structure = {
            "application_name": application_name,
            "application_path": application_path,
            "session_timestamp": datetime.now().isoformat(),
            "screenshots": []
        }
        
        # Process screenshots and move them to app folder
        processed_count = 0
        for screenshot_info in screenshots_data:
            original_path = Path(screenshot_info['path'])
            
            # Check if file exists in main screenshots directory
            if not original_path.exists():
                # Look for the file in the main screenshots directory
                filename = original_path.name
                potential_path = screenshots_dir / filename
                if potential_path.exists():
                    original_path = potential_path
                    print(f"Found file at: {original_path}")
                else:
                    print(f"File not found: {original_path}")
                    continue
            
            if original_path.exists():
                # Create clean filename based on screenshot name
                clean_name = re.sub(r'[<>:"/\\|?*]', '_', screenshot_info['name'])
                new_filename = f"{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                new_path = app_folder / new_filename
                
                # Move file to app folder
                import shutil
                shutil.move(str(original_path), str(new_path))
                
                # Add to JSON structure
                json_structure["screenshots"].append({
                    "image_name": screenshot_info['name'],
                    "image_path": str(new_path.absolute()),
                    "description": screenshot_info.get('description', ''),
                    "timestamp": screenshot_info.get('timestamp', datetime.now().isoformat())
                })
                processed_count += 1
                print(f"Moved screenshot to app folder: {new_path}")
            else:
                print(f"Skipping file that doesn't exist: {original_path}")
        
        # Save JSON file with application name
        json_file = app_folder / f"{clean_app_name}.json"
        with open(json_file, 'w') as f:
            json.dump(json_structure, f, indent=2)
        
        print(f"Created JSON file: {json_file} with {processed_count} screenshots")
        
        return jsonify({
            'success': True,
            'message': f'Session JSON created successfully with {processed_count} screenshots',
            'json_file': str(json_file.absolute()),
            'app_folder': str(app_folder.absolute()),
            'screenshots_count': len(json_structure["screenshots"])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def organize_screenshots_by_app(application_name):
    """Organize existing screenshots by application name"""
    try:
        # Clean application name for folder creation - remove invalid characters
        import re
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '_', application_name)
        clean_app_name = clean_app_name.replace('.exe', '').replace(' ', '_').strip('_')
        
        # Create application-specific folder
        app_folder = screenshots_dir / clean_app_name
        app_folder.mkdir(exist_ok=True)
        
        # Find and move screenshots for this application
        moved_count = 0
        for file in screenshots_dir.glob("*.png"):
            # Check if file is related to this application
            if application_name.lower() in file.name.lower():
                new_path = app_folder / file.name
                import shutil
                shutil.move(str(file), str(new_path))
                moved_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Organized {moved_count} screenshots for {application_name}',
            'app_folder': str(app_folder.absolute()),
            'moved_count': moved_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def remove_screenshot(filepath):
    """Remove a screenshot file and its metadata"""
    try:
        file_path = Path(filepath)
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'Screenshot file not found'})
        
        # Remove the screenshot file
        file_path.unlink()
        
        # Also remove metadata file if it exists
        metadata_file = file_path.with_suffix('.json')
        if metadata_file.exists():
            metadata_file.unlink()
        
        return jsonify({
            'success': True,
            'message': f'Screenshot removed successfully: {file_path.name}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def start_visual_region_selection(application):
    """Start visual region selection with proper overlay and dashed selection rectangle"""
    try:
        import tkinter as tk
        from tkinter import Canvas
        import threading
        
        if application:
            # Focus the application first
            focus_result = focus_window([application])
            if not focus_result.json.get('window_focused', False):
                # Try alternative approaches
                exe_name = os.path.basename(application).replace('.exe', '')
                focus_result = focus_window([exe_name])
        
        # Create a system-wide overlay window with visual feedback
        def create_visual_overlay():
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.attributes('-alpha', 0.2)  # More transparent
            root.attributes('-topmost', True)
            root.configure(bg='black')
            
            canvas = Canvas(root, bg='black', highlightthickness=0)
            canvas.pack(fill='both', expand=True)
            
            start_x, start_y = 0, 0
            selection_rect = None
            selection_text = None
            
            def on_mouse_down(event):
                nonlocal start_x, start_y, selection_rect, selection_text
                start_x, start_y = event.x, event.y
                if selection_rect:
                    canvas.delete(selection_rect)
                if selection_text:
                    canvas.delete(selection_text)
                selection_rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, 
                                                      outline='#ff5722', width=3, dash=(10,5))
                selection_text = canvas.create_text(start_x + 10, start_y - 10, 
                                                 text="Drag to select region", 
                                                 fill='#ff5722', font=('Arial', 12, 'bold'))
            
            def on_mouse_move(event):
                nonlocal selection_rect, selection_text
                if selection_rect:
                    x1, y1, x2, y2 = canvas.coords(selection_rect)
                    width = abs(event.x - start_x)
                    height = abs(event.y - start_y)
                    
                    # Update rectangle
                    canvas.coords(selection_rect, start_x, start_y, event.x, event.y)
                    
                    # Update text with dimensions
                    if selection_text:
                        canvas.delete(selection_text)
                        selection_text = canvas.create_text(start_x + 10, start_y - 10, 
                                                         text=f"Region: {width} x {height} pixels", 
                                                         fill='#ff5722', font=('Arial', 12, 'bold'))
            
            def on_mouse_up(event):
                nonlocal selection_rect, selection_text
                if selection_rect:
                    x1, y1, x2, y2 = canvas.coords(selection_rect)
                    x = min(x1, x2)
                    y = min(y1, y2)
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    
                    if width > 10 and height > 10:
                        # Show capture feedback
                        canvas.delete(selection_rect)
                        canvas.delete(selection_text)
                        
                        # Show "Capturing..." message
                        capture_text = canvas.create_text(root.winfo_screenwidth()//2, root.winfo_screenheight()//2, 
                                                       text="Capturing region...", 
                                                       fill='#4caf50', font=('Arial', 24, 'bold'))
                        root.update()
                        
                        try:
                            # Capture the region using simple approach
                            region = {'x': int(x), 'y': int(y), 'width': int(width), 'height': int(height)}
                            
                            # Simple capture without Flask context
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"region_screenshot_{timestamp}.png"
                            filepath = screenshots_dir / filename
                            
                            with mss.mss() as sct:
                                monitor = {
                                    "top": region["y"],
                                    "left": region["x"],
                                    "width": region["width"],
                                    "height": region["height"]
                                }
                                screenshot = sct.grab(monitor)
                                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
                            
                            # Store the result for the frontend to retrieve
                            global last_capture_result
                            last_capture_result = {
                                'success': True,
                                'filepath': str(filepath.absolute()),
                                'filename': filename,
                                'region': region
                            }
                            
                            print(f"Region captured successfully: {last_capture_result}")
                            
                            # Show success message briefly
                            canvas.delete(capture_text)
                            success_text = canvas.create_text(root.winfo_screenwidth()//2, root.winfo_screenheight()//2, 
                                                           text="✓ Region captured successfully!", 
                                                           fill='#4caf50', font=('Arial', 20, 'bold'))
                            root.after(1000, root.destroy)  # Close after 1 second
                        except Exception as e:
                            print(f"Error capturing region: {e}")
                            canvas.delete(capture_text)
                            error_text = canvas.create_text(root.winfo_screenwidth()//2, root.winfo_screenheight()//2, 
                                                         text=f"Error capturing region: {str(e)}", 
                                                         fill='#f44336', font=('Arial', 16, 'bold'))
                            root.after(2000, root.destroy)
                    else:
                        # Selection too small
                        canvas.delete(selection_rect)
                        canvas.delete(selection_text)
                        error_text = canvas.create_text(root.winfo_screenwidth()//2, root.winfo_screenheight()//2, 
                                                     text="Selection too small. Try again.", 
                                                     fill='#f44336', font=('Arial', 16, 'bold'))
                        root.after(2000, root.destroy)
            
            def on_escape(event):
                root.destroy()
            
            canvas.bind('<Button-1>', on_mouse_down)
            canvas.bind('<B1-Motion>', on_mouse_move)
            canvas.bind('<ButtonRelease-1>', on_mouse_up)
            root.bind('<Escape>', on_escape)
            
            # Instructions
            instruction = canvas.create_text(root.winfo_screenwidth()//2, 50, 
                                          text="Click and drag to select a region. Press ESC to cancel.", 
                                          fill='white', font=('Arial', 16, 'bold'))
            
            root.mainloop()
        
        # Run the overlay in a separate thread
        overlay_thread = threading.Thread(target=create_visual_overlay)
        overlay_thread.daemon = True
        overlay_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Visual region selection started',
            'application': application
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def start_recording(application):
    """Start recording for specific application"""
    global recording, current_app
    
    try:
        if recording:
            return jsonify({'success': False, 'error': 'Already recording'})
        
        current_app = application
        recording = True
        
        # Start recording thread
        recording_thread = threading.Thread(target=recording_loop)
        recording_thread.daemon = True
        recording_thread.start()
        
        return jsonify({'success': True, 'message': 'Recording started'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def stop_recording():
    """Stop recording"""
    global recording
    
    try:
        recording = False
        return jsonify({'success': True, 'message': 'Recording stopped'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def recording_loop():
    """Recording loop that runs in background"""
    global recording, current_app
    
    while recording:
        try:
            # Take screenshot every 2 seconds
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"recording_{current_app}_{timestamp}.png"
            filepath = screenshots_dir / filename
            
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))
            
            time.sleep(2)  # Wait 2 seconds
            
        except Exception as e:
            print(f"Error in recording loop: {e}")
            recording = False
            break

def get_screenshots():
    """Get list of all screenshots with metadata"""
    try:
        screenshots = []
        
        if screenshots_dir.exists():
            for file in screenshots_dir.glob("*.png"):
                # Check for metadata file
                metadata_file = file.with_suffix('.json')
                metadata = {}
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                    except:
                        metadata = {}
                
                # Extract application name from filename or metadata
                parts = file.name.split('_')
                app_name = metadata.get('name', parts[1] if len(parts) > 1 else 'Unknown')
                
                # Get file modification time
                mtime = file.stat().st_mtime
                timestamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                screenshots.append({
                    'id': file.name,
                    'application': app_name,
                    'timestamp': timestamp,
                    'path': str(file.absolute()),
                    'name': metadata.get('name', ''),
                    'description': metadata.get('description', ''),
                    'created_at': metadata.get('created_at', timestamp)
                })
        
        # Sort by timestamp (newest first)
        screenshots.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'screenshots': screenshots
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def clear_all_screenshots():
    """Clear all screenshots and metadata files"""
    try:
        cleared_count = 0
        
        if screenshots_dir.exists():
            # Remove all PNG files
            for file in screenshots_dir.glob("*.png"):
                try:
                    file.unlink()
                    cleared_count += 1
                except Exception as e:
                    print(f"Error removing {file}: {e}")
            
            # Remove all JSON metadata files
            for file in screenshots_dir.glob("*.json"):
                try:
                    file.unlink()
                    cleared_count += 1
                except Exception as e:
                    print(f"Error removing {file}: {e}")
            
            # Remove all subdirectories
            for subdir in screenshots_dir.iterdir():
                if subdir.is_dir():
                    try:
                        import shutil
                        shutil.rmtree(subdir)
                        cleared_count += 1
                    except Exception as e:
                        print(f"Error removing directory {subdir}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {cleared_count} files/directories',
            'cleared_count': cleared_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def read_json_file(filepath):
    """Read and return the contents of a JSON file"""
    try:
        file_path = Path(filepath)
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'JSON file not found'})
        
        with open(file_path, 'r') as f:
            json_content = f.read()
        
        return jsonify({
            'success': True,
            'json_content': json_content,
            'filepath': str(file_path.absolute())
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def check_file_exists(filepath):
    """Check if a file exists and is accessible"""
    try:
        file_path = Path(filepath)
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return jsonify({'success': False, 'error': 'File not readable'})
        
        return jsonify({
            'success': True,
            'exists': True,
            'filepath': str(file_path.absolute()),
            'size': file_path.stat().st_size
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def cleanup_duplicate_screenshots(application_name):
    """Clean up duplicate screenshots in the application folder"""
    try:
        # Clean application name for folder creation
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '_', application_name)
        clean_app_name = clean_app_name.replace('.exe', '').replace(' ', '_').strip('_')
        
        # Get application folder
        app_folder = screenshots_dir / clean_app_name
        if not app_folder.exists():
            return jsonify({'success': True, 'message': 'No application folder found to clean'})
        
        # Find and remove duplicates
        removed_count = 0
        seen_files = {}
        
        for file_path in app_folder.glob("*.png"):
            # Extract base name without timestamp
            filename = file_path.stem
            # Remove timestamp pattern from filename
            base_name = re.sub(r'_\d{8}_\d{6}$', '', filename)
            
            if base_name in seen_files:
                # This is a duplicate, remove it
                file_path.unlink()
                removed_count += 1
                print(f"Removed duplicate: {file_path.name}")
            else:
                seen_files[base_name] = file_path
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {removed_count} duplicate screenshots',
            'removed_count': removed_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def cleanup_old_json_files(application_name):
    """Remove old JSON files for the application and create fresh ones"""
    try:
        # Clean application name for folder creation
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '_', application_name)
        clean_app_name = clean_app_name.replace('.exe', '').replace(' ', '_').strip('_')
        
        # Create application-specific folder
        app_folder = screenshots_dir / clean_app_name
        app_folder.mkdir(exist_ok=True)
        
        # Remove all existing JSON files in the app folder
        removed_count = 0
        for json_file in app_folder.glob("*.json"):
            try:
                json_file.unlink()
                removed_count += 1
                print(f"Removed old JSON file: {json_file}")
            except Exception as e:
                print(f"Error removing {json_file}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {removed_count} old JSON files for {application_name}',
            'removed_count': removed_count,
            'app_folder': str(app_folder.absolute())
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Starting Python backend server...")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False) 