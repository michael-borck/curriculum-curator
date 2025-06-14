const { app, BrowserWindow, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const kill = require('tree-kill');

const isDev = process.env.ELECTRON_IS_DEV === '1';
const API_PORT = 8000;
const API_URL = `http://127.0.0.1:${API_PORT}`;

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    show: false, // Don't show until Python server is ready
  });

  // Start Python server
  startPythonServer()
    .then(() => {
      // Load the React app
      if (isDev) {
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
      } else {
        mainWindow.loadFile(path.join(__dirname, '../web/build/index.html'));
      }
      
      mainWindow.show();
    })
    .catch((error) => {
      console.error('Failed to start Python server:', error);
      dialog.showErrorBox('Startup Error', 
        'Failed to start the Curriculum Curator server. Please check the logs for more details.');
      app.quit();
    });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

async function startPythonServer() {
  return new Promise((resolve, reject) => {
    try {
      let pythonExecutable = 'python3';
      let serverScript;
      let cwd;

      if (isDev) {
        // Development mode - use local Python installation
        serverScript = path.join(__dirname, '../curriculum_curator/web/api.py');
        cwd = path.join(__dirname, '..');
      } else {
        // Production mode - use bundled Python environment
        const resourcesPath = process.resourcesPath;
        serverScript = path.join(resourcesPath, 'python-server/curriculum_curator/web/api.py');
        cwd = path.join(resourcesPath, 'python-server');
        
        // Try to find bundled Python executable
        if (process.platform === 'win32') {
          pythonExecutable = path.join(resourcesPath, 'python-server/python.exe');
        } else {
          pythonExecutable = path.join(resourcesPath, 'python-server/bin/python');
        }
        
        // Fallback to system Python if bundled doesn't exist
        if (!fs.existsSync(pythonExecutable)) {
          pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
        }
      }

      console.log('Starting Python server:', pythonExecutable, serverScript);
      console.log('Working directory:', cwd);

      pythonProcess = spawn(pythonExecutable, ['-m', 'uvicorn', 'curriculum_curator.web.api:app', '--host', '127.0.0.1', '--port', API_PORT.toString()], {
        cwd: cwd,
        stdio: ['ignore', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHONPATH: cwd,
        }
      });

      pythonProcess.stdout.on('data', (data) => {
        console.log('Python server stdout:', data.toString());
      });

      pythonProcess.stderr.on('data', (data) => {
        console.log('Python server stderr:', data.toString());
      });

      pythonProcess.on('error', (error) => {
        console.error('Python server error:', error);
        reject(error);
      });

      pythonProcess.on('exit', (code) => {
        console.log('Python server exited with code:', code);
        if (code !== 0 && code !== null) {
          reject(new Error(`Python server exited with code ${code}`));
        }
      });

      // Wait for server to be ready
      waitForServer(resolve, reject);

    } catch (error) {
      reject(error);
    }
  });
}

async function waitForServer(resolve, reject, attempts = 0) {
  const maxAttempts = 30; // 30 seconds max wait time
  
  if (attempts >= maxAttempts) {
    reject(new Error('Python server failed to start within timeout'));
    return;
  }

  try {
    const response = await axios.get(`${API_URL}/health`, { timeout: 1000 });
    if (response.data.status === 'healthy') {
      console.log('Python server is ready');
      resolve();
      return;
    }
  } catch (error) {
    // Server not ready yet, continue waiting
  }

  setTimeout(() => waitForServer(resolve, reject, attempts + 1), 1000);
}

function stopPythonServer() {
  if (pythonProcess) {
    console.log('Stopping Python server...');
    kill(pythonProcess.pid, 'SIGTERM', (error) => {
      if (error) {
        console.error('Error stopping Python server:', error);
      } else {
        console.log('Python server stopped');
      }
    });
    pythonProcess = null;
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  stopPythonServer();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopPythonServer();
});

// Handle app updates and other electron events
app.on('ready', () => {
  // Additional setup can go here
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, url) => {
    event.preventDefault();
    shell.openExternal(url);
  });
});