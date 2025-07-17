import React, { useState, useEffect, useRef } from 'react';
import './index.css';

interface Application {
  name: string;
  pid: number;
  windowTitle: string;
  path?: string;
}

interface Screenshot {
  id?: string;
  timestamp?: string;
  path: string;
  application?: string;
  name?: string;
  description?: string;
}

const App: React.FC = () => {
  const [hasError, setHasError] = useState(false);
  const [screenshots, setScreenshots] = useState<Screenshot[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState<string>('Ready');
  const [currentScreenshot, setCurrentScreenshot] = useState<string>('');
  const [currentScreenshotSaved, setCurrentScreenshotSaved] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [appPath, setAppPath] = useState<string>('');
  const [region, setRegion] = useState<{x: number, y: number, width: number, height: number} | null>(null);
  const [isSelectingRegion, setIsSelectingRegion] = useState(false);
  const [selectionStart, setSelectionStart] = useState<{x: number, y: number} | null>(null);
  const [selectionEnd, setSelectionEnd] = useState<{x: number, y: number} | null>(null);
  const [showScreenshotDialog, setShowScreenshotDialog] = useState(false);
  const [screenshotName, setScreenshotName] = useState('');
  const [screenshotDescription, setScreenshotDescription] = useState('');
  const [launchedApp, setLaunchedApp] = useState<Application | null>(null);
  const [isWindowMinimized, setIsWindowMinimized] = useState(false);
  const [sessionScreenshots, setSessionScreenshots] = useState<Screenshot[]>([]);
  const [showJsonDialog, setShowJsonDialog] = useState(false);
  const [jsonData, setJsonData] = useState<string>('');
  const [currentJsonFile, setCurrentJsonFile] = useState<string>('');
  const [currentScreenshotConvertedPath, setCurrentScreenshotConvertedPath] = useState<string>('');
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Clear screenshots history from UI display only (keep files in folder)
    setScreenshots([]);
    setSessionScreenshots([]);
    setCurrentScreenshot('');
    setCurrentScreenshotSaved(false);
    setCurrentJsonFile('');
    setStatus('Ready - History cleared from display');
  }, []);

  // Handle ESC key to close dialogs
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (showScreenshotDialog) {
          setShowScreenshotDialog(false);
        }
        if (showJsonDialog) {
          setShowJsonDialog(false);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showScreenshotDialog, showJsonDialog]);

  const startRegionSelection = async () => {
    if (!launchedApp) {
      setError('Please launch an application first');
      return;
    }
    
    setStatus('Focusing target application and starting region selection...');
    
    // First minimize the Electron window
    await window.electronAPI.minimizeWindow();
    setIsWindowMinimized(true);
    
    // Wait a bit for the window to minimize
    setTimeout(async () => {
      // Start region selection (this will focus the target app)
      const response = await window.electronAPI.sendPythonCommand({
        type: 'start_region_selection',
        data: { application: launchedApp.name }
      });
      
      if (response.success) {
        setStatus('Target application focused. Ready for region selection...');
        
        // Now start the visual region selection
        const visualResponse = await window.electronAPI.sendPythonCommand({
          type: 'start_visual_region_selection',
          data: { application: launchedApp.name }
        });
        
        if (visualResponse.success) {
          setStatus('Visual region selection active. Click and drag on the target application to select a region...');
          
          // Poll for the capture result
          let pollCount = 0;
          const maxPolls = 60; // 30 seconds max (60 * 500ms)
          
          const pollForResult = async () => {
            try {
              pollCount++;
              
              if (pollCount > maxPolls) {
                console.log('Polling timeout reached, restoring window');
                setStatus('Timeout: No capture detected. Restoring window...');
                await window.electronAPI.restoreWindow();
                setIsWindowMinimized(false);
                setError('No screenshot was captured. Please try again.');
                return;
              }
              
              const resultResponse = await window.electronAPI.sendPythonCommand({
                type: 'get_last_capture_result',
                data: {}
              });
              
              if (resultResponse.success && resultResponse.filepath) {
                console.log('Capture result received:', resultResponse);
                console.log('Setting current screenshot to:', resultResponse.filepath);
                setCurrentScreenshot(resultResponse.filepath);
                setCurrentScreenshotSaved(false); // Not saved yet
                setStatus('Region captured successfully! Restoring window...');
                
                // Test if the file exists
                const fileExists = await checkImageExists(resultResponse.filepath);
                console.log('File exists check:', fileExists);
                
                // Restore the Electron window
                await window.electronAPI.restoreWindow();
                setIsWindowMinimized(false);
                
                // Show the save dialog (don't display image until saved)
                setShowScreenshotDialog(true);
                loadScreenshots();
              } else {
                // Continue polling
                console.log(`No capture result yet, continuing to poll... (${pollCount}/${maxPolls})`);
                setTimeout(pollForResult, 500);
              }
            } catch (error) {
              console.error('Error polling for capture result:', error);
              // Continue polling even on error
              setTimeout(pollForResult, 1000);
            }
          };
          
          // Start polling after a delay
          setTimeout(pollForResult, 1000);
        } else {
          setError(visualResponse.error || 'Failed to start visual region selection');
          setStatus('Failed to start visual region selection');
          // Restore window on error
          await window.electronAPI.restoreWindow();
          setIsWindowMinimized(false);
        }
      } else {
        setError(response.error || 'Failed to focus target application');
        setStatus('Failed to focus target application');
        // Restore window on error
        await window.electronAPI.restoreWindow();
        setIsWindowMinimized(false);
      }
    }, 500);
  };

  const launchApplication = async () => {
    if (!appPath) {
      setError('Please enter an application path');
      return;
    }
    setStatus('Launching application...');
    const response = await window.electronAPI.sendPythonCommand({
      type: 'launch_app',
      data: { exe_path: appPath }
    });
    if (response.success) {
      setLaunchedApp({
        name: appPath.split('\\').pop() || 'Unknown',
        pid: response.pid || 0,
        windowTitle: appPath.split('\\').pop() || 'Unknown',
        path: appPath
      });
      setStatus('Application launched successfully');
      setError('');
    } else {
      setError(response.error || 'Failed to launch application');
      setStatus('Failed to launch application');
    }
  };

  const focusLaunchedApp = async () => {
    if (!launchedApp) {
      setError('Please launch an application first');
      return;
    }
    setStatus('Focusing application...');
    const response = await window.electronAPI.sendPythonCommand({
      type: 'focus_window',
      data: { title_keywords: [launchedApp.name] }
    });
    if (response.success) {
      setStatus('Application focused');
    } else {
      setError(response.error || 'Failed to focus application');
      setStatus('Failed to focus application');
    }
  };

  const takeRegionScreenshot = async (regionData?: {x: number, y: number, width: number, height: number}) => {
    const targetRegion = regionData || region;
    if (!targetRegion) {
      setError('Please select a region first');
      return;
    }
    
    setStatus('Capturing region screenshot...');
    const response = await window.electronAPI.sendPythonCommand({
      type: 'capture_region_screenshot',
      data: { region: targetRegion }
    });
    
    if (response.success) {
      setCurrentScreenshot(response.filepath);
      setCurrentScreenshotSaved(false); // Not saved yet
      setStatus('Region screenshot captured successfully');
      setShowScreenshotDialog(true);
      loadScreenshots();
    } else {
      setStatus('Failed to capture region screenshot');
      setError(response.error || 'Failed to capture region screenshot');
    }
  };

  const saveScreenshotWithDetails = async () => {
    if (!screenshotName.trim()) {
      setError('Please provide a name for the screenshot');
      return;
    }
    
    if (!currentScreenshot) {
      setError('No screenshot to save');
      return;
    }
    
    setStatus('Saving screenshot to folder...');
    
    try {
      // Save screenshot to folder immediately
      const response = await window.electronAPI.sendPythonCommand({
        type: 'save_screenshot_with_metadata',
        data: {
          filepath: currentScreenshot,
          name: screenshotName,
          description: screenshotDescription,
          application_name: launchedApp?.name || 'Unknown'
        }
      });
      
      if (response.success) {
        // Add to session screenshots for display
        const newScreenshot: Screenshot = {
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          path: response.filepath, // Use the saved file path
          application: launchedApp?.name || 'Unknown',
          name: screenshotName,
          description: screenshotDescription
        };
        
        setSessionScreenshots(prev => [...prev, newScreenshot]);
        
        // Also add to main screenshots list for history
        setScreenshots(prev => [...prev, newScreenshot]);
        
        setShowScreenshotDialog(false);
        setScreenshotName('');
        setScreenshotDescription('');
        setCurrentScreenshot('');
        setCurrentScreenshotSaved(false);
        
        setStatus(`Screenshot saved: ${screenshotName} (${sessionScreenshots.length + 1} in session)`);
      } else {
        setError(response.error || 'Failed to save screenshot');
        setStatus('Failed to save screenshot');
      }
    } catch (error) {
      setError('Error saving screenshot');
      setStatus('Error saving screenshot');
    }
  };

  const manualCaptureScreenshot = async () => {
    setStatus('Taking screenshot of focused application...');
    const response = await window.electronAPI.sendPythonCommand({
      type: 'capture_screenshot',
      data: { application: launchedApp?.name }
    });
    
    if (response.success) {
      console.log('Manual capture result:', response);
      console.log('Setting current screenshot to:', response.filepath);
      setCurrentScreenshot(response.filepath);
      setCurrentScreenshotSaved(false); // Not saved yet
      
      // Test if the file exists
      const fileExists = await checkImageExists(response.filepath);
      console.log('File exists check:', fileExists);
      
      setStatus('Screenshot captured! Restoring window...');
      
      // Restore the Electron window
      await window.electronAPI.restoreWindow();
      setIsWindowMinimized(false);
      
      // Show the save dialog (don't display image until saved)
      setShowScreenshotDialog(true);
      loadScreenshots();
    } else {
      setError(response.error || 'Failed to capture screenshot');
      setStatus('Failed to capture screenshot');
    }
  };

  const loadScreenshots = async () => {
    const response = await window.electronAPI.sendPythonCommand({
      type: 'get_screenshots',
      data: {}
    });
    if (response.success) {
      console.log('Loaded screenshots:', response.screenshots);
      setScreenshots(response.screenshots || []);
    } else {
      console.error('Failed to load screenshots:', response.error);
    }
  };

  const clearSession = async () => {
    // Clear all screenshots from display (but keep files in folder)
    setSessionScreenshots([]);
    setScreenshots([]);
    setCurrentScreenshot('');
    setCurrentScreenshotSaved(false);
    setLaunchedApp(null);
    setAppPath('');
    setScreenshotName('');
    setScreenshotDescription('');
    setCurrentJsonFile('');
    setError('');
    setStatus('Session cleared. Ready for new session.');
  };

  const createJsonData = async () => {
    if (sessionScreenshots.length === 0) {
      setError('No screenshots in current session to create JSON');
      return;
    }

    setStatus('Cleaning up duplicates and creating JSON file...');

    try {
      // First, clean up any duplicate screenshots
      const cleanupResponse = await window.electronAPI.sendPythonCommand({
        type: 'cleanup_duplicate_screenshots',
        data: {
          application_name: launchedApp?.name || 'Unknown'
        }
      });

      if (!cleanupResponse.success) {
        console.warn('Warning: Could not cleanup duplicate screenshots:', cleanupResponse.error);
      }

      // Prepare screenshots data for JSON creation
      const screenshotsForJson = sessionScreenshots.map(screenshot => ({
        name: screenshot.name || screenshot.id || 'unnamed',
        path: screenshot.path,
        description: screenshot.description || '',
        timestamp: screenshot.timestamp || new Date().toISOString()
      }));

      // Create JSON file with screenshots
      const response = await window.electronAPI.sendPythonCommand({
        type: 'create_session_json',
        data: {
          application_name: launchedApp?.name || 'Unknown',
          application_path: launchedApp?.path || '',
          screenshots: screenshotsForJson
        }
      });

      if (response.success) {
        setStatus(`JSON created successfully! ${response.screenshots_count} screenshots organized.`);
        // Store the JSON file path for later viewing
        setCurrentJsonFile(response.json_file);
      } else {
        setError(response.error || 'Failed to create session JSON');
        setStatus('Failed to create session JSON');
      }
    } catch (error) {
      setError('Error creating session JSON');
      setStatus('Error creating session JSON');
    }
  };

  const viewJsonData = async () => {
    if (!currentJsonFile) {
      setError('No JSON file available. Please create JSON first.');
      return;
    }

    setStatus('Loading JSON data...');

    try {
      const response = await window.electronAPI.sendPythonCommand({
        type: 'read_json_file',
        data: { filepath: currentJsonFile }
      });

      if (response.success) {
        setJsonData(response.json_content);
        setShowJsonDialog(true);
        setStatus('JSON data loaded successfully');
      } else {
        setError(response.error || 'Failed to read JSON file');
        setStatus('Failed to read JSON file');
      }
    } catch (error) {
      setError('Error reading JSON file');
      setStatus('Error reading JSON file');
    }
  };

  const removeScreenshot = async (screenshotPath: string, isSessionScreenshot: boolean = false) => {
    try {
      setStatus('Removing screenshot...');
      
      const response = await window.electronAPI.sendPythonCommand({
        type: 'remove_screenshot',
        data: { filepath: screenshotPath }
      });

      if (response.success) {
        if (isSessionScreenshot) {
          // Remove from session screenshots
          setSessionScreenshots(prev => prev.filter(s => s.path !== screenshotPath));
        } else {
          // Refresh all screenshots
          loadScreenshots();
        }
        
        setStatus('Screenshot removed successfully');
      } else {
        setError(response.error || 'Failed to remove screenshot');
        setStatus('Failed to remove screenshot');
      }
    } catch (error) {
      setError('Error removing screenshot');
      setStatus('Error removing screenshot');
    }
  };

  const getSelectionStyle = () => {
    if (!selectionStart || !selectionEnd) return {};
    
    const x = Math.min(selectionStart.x, selectionEnd.x);
    const y = Math.min(selectionStart.y, selectionEnd.y);
    const width = Math.abs(selectionEnd.x - selectionStart.x);
    const height = Math.abs(selectionEnd.y - selectionStart.y);
    
    return {
      position: 'fixed' as const,
      left: x,
      top: y,
      width,
      height,
      border: '2px dashed #ff5722',
      backgroundColor: 'rgba(255, 87, 34, 0.1)',
      pointerEvents: 'none' as const,
      zIndex: 1000000,
    };
  };

  // Helper to normalize file path for Electron image src
  const getImageSrc = (filePath: string) => {
    if (!filePath) return '';
    console.log('getImageSrc called with:', filePath);
    // For Electron renderer, just prepend file:// and normalize slashes
    let normalized = filePath.replace(/\\/g, '/');
    if (!normalized.startsWith('/')) normalized = '/' + normalized;
    const result = 'file://' + normalized;
    console.log('getImageSrc result:', result);
    return result;
  };

  // Helper to force image reload
  const forceImageReload = (imgElement: HTMLImageElement) => {
    const originalSrc = imgElement.src;
    imgElement.src = '';
    setTimeout(() => {
      imgElement.src = originalSrc;
    }, 100);
  };

  // Helper to check if image exists and is accessible
  const checkImageExists = async (filePath: string) => {
    try {
      const response = await window.electronAPI.sendPythonCommand({
        type: 'check_file_exists',
        data: { filepath: filePath }
      });
      return response.success;
    } catch (error) {
      console.error('Error checking file existence:', error);
      return false;
    }
  };

  return (
    <div className="app">
      {showScreenshotDialog && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            zIndex: 10001,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
          onClick={() => setShowScreenshotDialog(false)}
        >
          <div 
            style={{
              background: 'white',
              padding: '20px',
              borderRadius: '8px',
              minWidth: '400px',
              maxWidth: '600px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Add Screenshot to Session</h3>
            <div style={{ marginBottom: '15px' }}>
              <label>Name:</label>
              <input
                type="text"
                value={screenshotName}
                onChange={(e) => setScreenshotName(e.target.value)}
                placeholder="Enter screenshot name"
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label>Description:</label>
              <textarea
                value={screenshotDescription}
                onChange={(e) => setScreenshotDescription(e.target.value)}
                placeholder="Enter description (optional)"
                style={{ width: '100%', padding: '8px', marginTop: '5px', height: '80px' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setShowScreenshotDialog(false)}
                style={{ padding: '8px 16px', border: '1px solid #ccc', borderRadius: '4px' }}
              >
                Cancel
              </button>
              <button 
                onClick={saveScreenshotWithDetails}
                style={{ padding: '8px 16px', background: '#667eea', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Add to Session
              </button>
            </div>
          </div>
        </div>
      )}

      {showJsonDialog && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            zIndex: 10002,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
          onClick={() => setShowJsonDialog(false)}
        >
          <div 
            style={{
              background: 'white',
              padding: '20px',
              borderRadius: '8px',
              minWidth: '600px',
              maxWidth: '800px',
              maxHeight: '80vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Session JSON Data</h3>
            <div style={{ marginBottom: '15px' }}>
              <textarea
                value={jsonData}
                readOnly
                style={{ 
                  width: '100%', 
                  height: '400px', 
                  padding: '8px', 
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  border: '1px solid #ccc',
                  borderRadius: '4px'
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setShowJsonDialog(false)}
                style={{ padding: '8px 16px', border: '1px solid #ccc', borderRadius: '4px' }}
              >
                Close
              </button>
              <button 
                onClick={() => {
                  navigator.clipboard.writeText(jsonData);
                  setStatus('JSON data copied to clipboard');
                }}
                style={{ padding: '8px 16px', background: '#4caf50', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="header">
        <h1>🎬 Connector Recording Desktop</h1>
        <div className="status-bar">
          <span className={`status ${isRecording ? 'recording' : 'ready'}`}>
            {isRecording ? '🔴 Recording' : '🟢 Ready'}
          </span>
          <span className="status-text">{status}</span>
        </div>
      </div>
      
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError('')}>✕</button>
        </div>
      )}
      
      <div className="main-content">
        <div className="left-panel">
          <div className="section">
            <h2>🚀 Launch Application</h2>
            <input
              type="text"
              placeholder="Enter application path (e.g. C:\Program Files\App\app.exe)"
              value={appPath}
              onChange={e => setAppPath(e.target.value)}
              style={{ width: '100%', marginBottom: 8, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
            />
            <button className="refresh-btn" onClick={launchApplication} style={{ width: '100%', marginBottom: 8 }}>
              🚀 Launch Application
            </button>
            {launchedApp && (
              <div style={{ 
                background: '#f0f8ff', 
                padding: '12px', 
                borderRadius: '6px', 
                marginTop: '8px',
                border: '1px solid #667eea'
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#667eea' }}>✅ Launched Application</h4>
                <div style={{ fontSize: '14px', color: '#333' }}>
                  <div><strong>Name:</strong> {launchedApp.name}</div>
                  <div><strong>Path:</strong> {launchedApp.path}</div>
                </div>
                <button 
                  className="refresh-btn" 
                  onClick={focusLaunchedApp} 
                  style={{ width: '100%', marginTop: '8px', background: '#4caf50' }}
                >
                  👁️ Focus Application
                </button>
              </div>
            )}
          </div>
          
          <div className="section">
            <h2>🎯 Region Screenshot</h2>
            <div className="action-buttons">
              <button 
                className="action-btn" 
                onClick={startRegionSelection}
                disabled={!launchedApp}
                style={{ 
                  background: launchedApp ? 'linear-gradient(135deg, #ff5722 0%, #e64a19 100%)' : '#ccc',
                  color: 'white',
                  width: '100%',
                  padding: '12px 20px'
                }}
              >
                🖱️ Select Region & Capture
              </button>
              
              {isWindowMinimized && (
                <button 
                  className="action-btn" 
                  onClick={manualCaptureScreenshot}
                  style={{ 
                    background: 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)',
                    color: 'white',
                    width: '100%',
                    padding: '12px 20px',
                    marginTop: '8px'
                  }}
                >
                  📸 Manual Capture
                </button>
              )}
            </div>
            
            {isWindowMinimized && (
              <div style={{ 
                background: '#fff3cd', 
                padding: '12px', 
                borderRadius: '6px', 
                marginTop: '12px',
                fontSize: '14px',
                color: '#856404',
                border: '1px solid #ffeaa7'
              }}>
                <h4 style={{ margin: '0 0 8px 0' }}>📋 Instructions:</h4>
                <ul style={{ margin: '0', paddingLeft: '20px' }}>
                  <li>Electron window is minimized</li>
                  <li>Visual region selector is active</li>
                  <li>Click and drag to select a region</li>
                  <li>You'll see dashed lines while selecting</li>
                  <li>Release mouse to capture the region</li>
                  <li>Window will restore automatically with the screenshot</li>
                </ul>
              </div>
            )}
            
            {!launchedApp && (
              <div style={{ 
                background: '#fff3cd', 
                padding: '8px', 
                borderRadius: '4px', 
                marginTop: '8px',
                fontSize: '12px',
                color: '#856404'
              }}>
                ℹ️ Launch an application first to use region selection
              </div>
            )}
          </div>

          <div className="section">
            <h2>📋 Session Management</h2>
            <div className="action-buttons">
              <button 
                className="action-btn" 
                onClick={clearSession}
                style={{ 
                  background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                  color: 'white',
                  width: '100%',
                  padding: '12px 20px',
                  marginBottom: '8px'
                }}
              >
                🗑️ Clear Session
              </button>
              
              <button 
                className="action-btn" 
                onClick={createJsonData}
                disabled={sessionScreenshots.length === 0}
                style={{ 
                  background: sessionScreenshots.length > 0 ? 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)' : '#ccc',
                  color: 'white',
                  width: '100%',
                  padding: '12px 20px',
                  marginBottom: '8px'
                }}
              >
                💾 Save All & Create JSON
              </button>
              
              <button 
                className="action-btn" 
                onClick={viewJsonData}
                disabled={!currentJsonFile}
                style={{ 
                  background: currentJsonFile ? 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)' : '#ccc',
                  color: 'white',
                  width: '100%',
                  padding: '12px 20px'
                }}
              >
                👁️ View JSON
              </button>
            </div>
            
            <div style={{ 
              background: '#e3f2fd', 
              padding: '12px', 
              borderRadius: '6px', 
              marginTop: '12px',
              fontSize: '14px',
              color: '#1565c0',
              border: '1px solid #bbdefb'
            }}>
              <h4 style={{ margin: '0 0 8px 0' }}>📊 Session Info:</h4>
              <div style={{ fontSize: '12px' }}>
                <div><strong>Application:</strong> {launchedApp?.name || 'None'}</div>
                <div><strong>Screenshots:</strong> {sessionScreenshots.length}</div>
                <div><strong>JSON File:</strong> {currentJsonFile ? '✅ Created' : '❌ Not Created'}</div>
                <div><strong>Status:</strong> {sessionScreenshots.length > 0 ? 'Active Session' : 'No Screenshots'}</div>
              </div>
            </div>
          </div>
        </div>
        <div className="right-panel">
          <div className="section">
            <h2>🖼️ Current Screenshot</h2>
            {currentScreenshot && currentScreenshotSaved ? (
              <div className="screenshot-viewer">
                <div style={{ marginBottom: '8px', fontSize: '12px', color: '#666' }}>
                  <button 
                    onClick={() => {
                      console.log('Current screenshot path:', currentScreenshot);
                      console.log('Converted path:', getImageSrc(currentScreenshot));
                      checkImageExists(currentScreenshot).then(exists => {
                        console.log('File exists:', exists);
                      });
                    }}
                    style={{ 
                      fontSize: '10px', 
                      padding: '4px 8px', 
                      background: '#f0f0f0',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      marginRight: '8px'
                    }}
                  >
                    Debug Image
                  </button>
                  <span>Path: {currentScreenshot}</span>
                </div>
                <img
                  src={getImageSrc(currentScreenshot)}
                  alt="Current Screenshot"
                  className="screenshot-image"
                  onLoad={() => {
                    console.log('Image loaded successfully');
                    setStatus('Screenshot displayed successfully');
                    setError(''); // Clear any previous errors
                  }}
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    console.error('Image failed to load:', {
                      src: target.src,
                      originalPath: currentScreenshot,
                      convertedPath: getImageSrc(currentScreenshot)
                    });
                    
                    // Check if file exists first
                    checkImageExists(currentScreenshot).then(exists => {
                      console.log('File exists check result:', exists);
                      if (!exists) {
                        setError(`Screenshot file not found: ${currentScreenshot}`);
                      } else {
                        setError('Failed to load screenshot image. Check console for details.');
                        // Try to reload the image after a delay
                        setTimeout(() => {
                          if (target) {
                            console.log('Retrying image load...');
                            forceImageReload(target);
                          }
                        }, 1000);
                      }
                    });
                  }}
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '300px',
                    border: '1px solid #ccc',
                    borderRadius: '8px'
                  }}
                />
              </div>
            ) : currentScreenshot && !currentScreenshotSaved ? (
              <div className="no-screenshot" style={{ 
                padding: '20px', 
                textAlign: 'center', 
                color: '#666',
                fontStyle: 'italic',
                background: '#f9f9f9',
                borderRadius: '8px',
                border: '1px solid #e0e0e0'
              }}>
                📸 Screenshot captured! Please save it using the dialog above.
              </div>
            ) : (
              <div className="no-screenshot">No screenshot taken yet</div>
            )}
          </div>
          <div className="section">
            <h2>📁 Screenshots History</h2>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <button className="refresh-btn" onClick={loadScreenshots}>
                🔄 Refresh
              </button>
              <button 
                className="refresh-btn" 
                onClick={() => setScreenshots([])}
                style={{ background: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)' }}
              >
                🗑️ Clear History
              </button>
            </div>
            <div className="screenshots-list">
              {screenshots.map((screenshot, index) => (
                <div key={index} className="screenshot-item">
                  <div className="screenshot-info">
                    <div className="screenshot-app">{screenshot.application}</div>
                    <div className="screenshot-time">{screenshot.timestamp}</div>
                    {screenshot.name && <div className="screenshot-name">{screenshot.name}</div>}
                  </div>
                  <div style={{ position: 'relative' }}>
                    <img
                      src={getImageSrc(screenshot.path)}
                      alt="Screenshot"
                      className="screenshot-thumbnail"
                      onLoad={() => console.log('History image loaded:', screenshot.path)}
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        console.error('History image failed to load:', {
                          path: screenshot.path,
                          src: target.src,
                          convertedPath: getImageSrc(screenshot.path)
                        });
                        
                        // Check if file exists
                        checkImageExists(screenshot.path).then(exists => {
                          console.log('History file exists check:', exists);
                          if (!exists) {
                            console.log('History file does not exist, showing placeholder');
                          }
                        });
                        
                        // Show a placeholder for broken images
                        target.style.display = 'none';
                        const placeholder = document.createElement('div');
                        placeholder.style.cssText = `
                          width: 60px;
                          height: 40px;
                          background: #f0f0f0;
                          border: 1px solid #ccc;
                          border-radius: 4px;
                          display: flex;
                          align-items: center;
                          justify-content: center;
                          font-size: 10px;
                          color: #666;
                        `;
                        placeholder.textContent = 'No Image';
                        target.parentNode?.appendChild(placeholder);
                      }}
                      style={{
                        width: '60px',
                        height: '40px',
                        objectFit: 'cover',
                        borderRadius: '4px',
                        border: '1px solid #e0e0e0'
                      }}
                    />
                    <button
                      onClick={() => removeScreenshot(screenshot.path, false)}
                      style={{
                        position: 'absolute',
                        top: '5px',
                        right: '5px',
                        background: 'rgba(244, 67, 54, 0.9)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '50%',
                        width: '24px',
                        height: '24px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      title="Remove screenshot"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="section">
            <h2>📸 Current Session Screenshots</h2>
            <div className="screenshots-list">
              {sessionScreenshots.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '20px', 
                  color: '#666',
                  fontStyle: 'italic'
                }}>
                  No screenshots in current session
                </div>
              ) : (
                sessionScreenshots.map((screenshot, index) => (
                  <div key={index} className="screenshot-item">
                    <div className="screenshot-info">
                      <div className="screenshot-app">{screenshot.application}</div>
                      <div className="screenshot-time">{screenshot.timestamp}</div>
                      {screenshot.name && <div className="screenshot-name">{screenshot.name}</div>}
                      {screenshot.description && <div className="screenshot-description">{screenshot.description}</div>}
                    </div>
                    <div style={{ position: 'relative' }}>
                      <img
                        src={getImageSrc(screenshot.path)}
                        alt="Screenshot"
                        className="screenshot-thumbnail"
                        onLoad={() => console.log('Session image loaded:', screenshot.path)}
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          console.error('Session image failed to load:', {
                            path: screenshot.path,
                            src: target.src,
                            convertedPath: getImageSrc(screenshot.path)
                          });
                          
                          // Check if file exists
                          checkImageExists(screenshot.path).then(exists => {
                            console.log('Session file exists check:', exists);
                            if (!exists) {
                              console.log('Session file does not exist, showing placeholder');
                            }
                          });
                          
                          // Show a placeholder for broken images
                          target.style.display = 'none';
                          const placeholder = document.createElement('div');
                          placeholder.style.cssText = `
                            width: 60px;
                            height: 40px;
                            background: #f0f0f0;
                            border: 1px solid #ccc;
                            border-radius: 4px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 10px;
                            color: #666;
                          `;
                          placeholder.textContent = 'No Image';
                          target.parentNode?.appendChild(placeholder);
                        }}
                        style={{
                          width: '60px',
                          height: '40px',
                          objectFit: 'cover',
                          borderRadius: '4px',
                          border: '1px solid #e0e0e0'
                        }}
                      />
                      <button
                        onClick={() => removeScreenshot(screenshot.path, true)}
                        style={{
                          position: 'absolute',
                          top: '5px',
                          right: '5px',
                          background: 'rgba(244, 67, 54, 0.9)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '50%',
                          width: '24px',
                          height: '24px',
                          fontSize: '12px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                        title="Remove screenshot"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App; 