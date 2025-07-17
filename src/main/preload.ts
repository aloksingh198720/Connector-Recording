import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  sendPythonCommand: (command: any) => ipcRenderer.invoke('python-command', command),
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  restoreWindow: () => ipcRenderer.invoke('restore-window'),
});

declare global {
  interface Window {
    electronAPI: {
      sendPythonCommand: (command: any) => Promise<any>;
      minimizeWindow: () => Promise<void>;
      restoreWindow: () => Promise<void>;
    };
  }
} 