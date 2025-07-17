import { app, BrowserWindow, ipcMain, screen } from 'electron';
import * as path from 'path';

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  console.log('Creating window...');
  
  // Get primary display work area
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  
  // Calculate window size (80% of screen size)
  const windowWidth = Math.min(1200, Math.floor(width * 0.8));
  const windowHeight = Math.min(800, Math.floor(height * 0.8));
  
  // Center the window
  const x = Math.floor((width - windowWidth) / 2);
  const y = Math.floor((height - windowHeight) / 2);
  
  mainWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    x: x,
    y: y,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    titleBarStyle: 'default',
    frame: true,
    transparent: false,
    show: false, // Don't show until ready
    alwaysOnTop: false,
    skipTaskbar: false,
    resizable: true,
    maximizable: true,
    minimizable: true,
    closable: true,
  });

  console.log('Window created, loading content...');
  
  // Check if we're in development mode
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  
  if (isDev) {
    console.log('Loading development URL...');
    mainWindow.loadURL('http://localhost:3000');
    // Removed developer tools
  } else {
    console.log('Loading production file...');
    const filePath = path.join(__dirname, '../renderer/index.html');
    console.log('File path:', filePath);
    mainWindow.loadFile(filePath);
  }

  mainWindow.once('ready-to-show', () => {
    console.log('Window ready to show');
    mainWindow?.show();
    mainWindow?.focus();
    console.log('Window should be visible now');
  });

  mainWindow.on('closed', () => {
    console.log('Window closed');
    mainWindow = null;
  });

  // Allow window to be closed normally
  mainWindow.on('close', (event) => {
    console.log('Window close event triggered');
    // Allow closing - remove the prevention logic
  });

  mainWindow.on('show', () => {
    console.log('Window show event fired');
  });

  mainWindow.on('hide', () => {
    console.log('Window hide event fired');
  });

  mainWindow.on('minimize', () => {
    console.log('Window minimize event fired');
  });

  mainWindow.on('restore', () => {
    console.log('Window restore event fired');
  });

  mainWindow.on('maximize', () => {
    console.log('Window maximize event fired');
  });

  mainWindow.on('unmaximize', () => {
    console.log('Window unmaximize event fired');
  });

  mainWindow.on('resize', () => {
    if (mainWindow) {
      const bounds = mainWindow.getBounds();
      console.log('Window resized to:', bounds);
    }
  });

  mainWindow.on('move', () => {
    if (mainWindow) {
      const bounds = mainWindow.getBounds();
      console.log('Window moved to:', bounds);
    }
  });
}

async function sendCommandToPython(command: any): Promise<any> {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/command', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(command),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error communicating with Python backend:', error);
    return { success: false, error: `Backend communication error: ${error}` };
  }
}

app.whenReady().then(() => {
  createWindow();

  ipcMain.handle('python-command', async (_event, command) => {
    return await sendCommandToPython(command);
  });

  ipcMain.handle('minimize-window', async () => {
    if (mainWindow) {
      mainWindow.minimize();
    }
  });

  ipcMain.handle('restore-window', async () => {
    if (mainWindow) {
      mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
}); 