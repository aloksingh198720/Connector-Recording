# 🎬 Connector Recording Desktop

A beautiful desktop automation application with an elegant Electron-based UI and intelligent Python backend for automating login processes via image-based UI element detection and screenshot capture.

## 🚀 Features

- **Modern Glassmorphism UI**: Beautiful React-based interface with Tailwind CSS
- **Application Management**: View and manage running applications
- **Screenshot Capture**: Take screenshots of specific applications or entire screen
- **Recording System**: Record application interactions with automatic screenshot capture
- **UI Element Detection**: Intelligent detection of buttons, input fields, and other UI elements
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Real-time Status**: Live status updates and error handling

## 🏗️ Architecture

- **Frontend**: Electron + React + TypeScript
- **Backend**: Python Flask API
- **Communication**: HTTP API between Electron and Python
- **UI Framework**: Tailwind CSS with custom glassmorphism design
- **Automation**: PyAutoGUI, OpenCV, and MSS for screenshot capture

## 📋 Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd connector-recording-desktop
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Option 1: Use the startup script (Recommended)
```bash
python start_app.py
```

This script will:
- Start the Python Flask backend
- Build the React app
- Launch the Electron application

### Option 2: Manual startup

1. **Start the Python backend**:
   ```bash
   python python_backend/desktop_app.py
   ```

2. **Build the React app**:
   ```bash
   npm run build
   ```

3. **Start Electron**:
   ```bash
   npm run electron
   ```

## 📁 Project Structure

```
connector-recording-desktop/
├── src/
│   ├── main/                 # Electron main process
│   │   ├── main.ts          # Main process entry point
│   │   └── preload.ts       # Preload script for IPC
│   └── renderer/            # React renderer process
│       ├── App.tsx          # Main React component
│       ├── main.tsx         # React entry point
│       └── index.css        # Styles
├── python_backend/
│   └── desktop_app.py       # Python Flask backend
├── dist/                    # Built React app
├── screenshots/             # Captured screenshots
├── package.json
├── requirements.txt
└── start_app.py            # Startup script
```

## 🔧 Development

### Development Mode
```bash
# Terminal 1: Start Python backend
python python_backend/desktop_app.py

# Terminal 2: Start React dev server
npm run dev

# Terminal 3: Start Electron in dev mode
npm run electron:dev
```

### Building for Production
```bash
npm run build
npm run electron
```

## 🎯 Usage

1. **Launch the application** using the startup script
2. **Select an application** from the running applications list
3. **Take screenshots** or **start recording** to capture application interactions
4. **View captured screenshots** in the history panel
5. **Monitor status** through the real-time status bar

## 📄 JSON Session Files

The application creates JSON session files to organize screenshots by application:

- **File Naming**: JSON files are named after the application (e.g., `SSMS.json`, `Chrome.json`)
- **Location**: Files are stored in `screenshots/[ApplicationName]/[ApplicationName].json`
- **Structure**: Each JSON file contains:
  - Application name and path
  - Session timestamp
  - List of screenshots with metadata (name, path, description, timestamp)

Example JSON structure:
```json
{
  "application_name": "SSMS.exe",
  "application_path": "C:\\Program Files\\Microsoft SQL Server Management Studio\\SSMS.exe",
  "session_timestamp": "2025-01-13T10:00:00.000Z",
  "screenshots": [
    {
      "image_name": "Login Screen",
      "image_path": "C:\\Connector Recording\\screenshots\\SSMS\\Login_Screen_20250113_100000.png",
      "description": "Initial login screen",
      "timestamp": "2025-01-13T10:00:00.000Z"
    }
  ]
}
```

## 🔌 API Endpoints

The Python backend provides the following API endpoints:

- `POST /api/command` - Main command endpoint
  - `get_running_apps` - List running applications
  - `capture_screenshot` - Take a screenshot
  - `start_recording` - Start recording session
  - `stop_recording` - Stop recording session
  - `get_screenshots` - List captured screenshots

## 🎨 UI Components

- **Application Selector**: Browse and select running applications
- **Screenshot Viewer**: Display current and historical screenshots
- **Recording Controls**: Start/stop recording with visual feedback
- **Status Bar**: Real-time status and error reporting
- **Error Boundaries**: Graceful error handling and recovery

## 🐛 Troubleshooting

### Common Issues

1. **Python backend not starting**:
   - Ensure Python dependencies are installed: `pip install -r requirements.txt`
   - Check if port 5000 is available

2. **Electron app not loading**:
   - Build React app first: `npm run build`
   - Check console for error messages

3. **Screenshot capture issues**:
   - Ensure the application has proper permissions
   - Check if the target application is visible

4. **UI disappearing**:
   - Check browser console for JavaScript errors
   - Verify asset paths in built files

### Debug Mode

Enable debug mode by setting environment variables:
```bash
# Windows
set DEBUG=true
set NODE_ENV=development

# macOS/Linux
export DEBUG=true
export NODE_ENV=development
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions, please check the troubleshooting section or create an issue in the repository. 