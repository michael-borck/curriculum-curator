import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import type { IpcMainInvokeEvent } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { autoUpdater } from 'electron-updater'
import {
  getBackendInfo,
  startBackend,
  stopBackend,
  waitForBackend
} from './backend'
import { startOllama, stopOllama, detectOllama } from './ollama'

let mainWindow: BrowserWindow | null = null

const ALLOWED_EXTERNAL_PROTOCOLS = new Set(['https:', 'http:', 'mailto:'])

function openExternalSafely(url: string): void {
  try {
    if (ALLOWED_EXTERNAL_PROTOCOLS.has(new URL(url).protocol)) {
      shell.openExternal(url)
    }
  } catch {
    // Ignore malformed URLs
  }
}

/** IPC handlers only accept messages from our own renderer. */
function isTrustedSender(event: IpcMainInvokeEvent): boolean {
  return mainWindow !== null && event.sender === mainWindow.webContents
}

const hasSingleInstanceLock = app.requestSingleInstanceLock()
if (!hasSingleInstanceLock) {
  app.quit()
}

app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.focus()
  }
})

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      webviewTag: true
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  // Security: sanitize webview preferences to prevent node access in guest content
  mainWindow.webContents.on('will-attach-webview', (_event, webPreferences) => {
    delete webPreferences.preload
    webPreferences.nodeIntegration = false
    webPreferences.contextIsolation = true
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    openExternalSafely(details.url)
    return { action: 'deny' }
  })

  // Keep the main frame on the app itself; send anything else to the browser.
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const allowed =
      url.startsWith('file://') ||
      (is.dev && process.env['ELECTRON_RENDERER_URL']
        ? url.startsWith(process.env['ELECTRON_RENDERER_URL'])
        : false)
    if (!allowed) {
      event.preventDefault()
      openExternalSafely(url)
    }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    const info = getBackendInfo()
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'), {
      query: {
        backendPort: String(info.port),
        ...(info.token ? { desktopToken: info.token } : {})
      }
    })
  }
}

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.curriculum-curator.desktop')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Start Ollama before backend (backend's Ollama service needs it)
  await startOllama()

  // Start backend before creating the window
  await startBackend()
  const healthy = await waitForBackend()
  if (!healthy) {
    dialog.showErrorBox(
      'Curriculum Curator could not start',
      'The local backend failed to start. Please restart the app. If the ' +
        'problem continues, reinstall it or check the application logs.'
    )
    app.quit()
    return
  }

  createWindow()

  // Auto-updater: check 3s after window is shown (skip in dev)
  if (!is.dev) {
    autoUpdater.autoDownload = false
    setTimeout(() => {
      autoUpdater.checkForUpdates()
    }, 3000)
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', async () => {
  await stopBackend()
  await stopOllama()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// --- IPC Handlers ---

// Ollama info for renderer
ipcMain.handle('get-ollama-info', (event) => {
  if (!isTrustedSender(event)) return { installed: false, binaryPath: null }
  const binaryPath = detectOllama()
  return { installed: binaryPath !== null, binaryPath }
})

// File export: native Save As dialog
ipcMain.handle('save-file', async (event, defaultName: string, data: Buffer | string) => {
  if (!isTrustedSender(event)) return null
  const result = await dialog.showSaveDialog({
    defaultPath: defaultName,
    filters: [
      { name: 'PDF', extensions: ['pdf'] },
      { name: 'Word', extensions: ['docx'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })

  if (result.canceled || !result.filePath) {
    return null
  }

  const fs = await import('fs/promises')
  await fs.writeFile(result.filePath, data)
  return result.filePath
})

// Auto-updater IPC
ipcMain.handle('check-for-updates', (event) => {
  if (!isTrustedSender(event)) return null
  return autoUpdater.checkForUpdates()
})

ipcMain.handle('download-update', (event) => {
  if (!isTrustedSender(event)) return null
  return autoUpdater.downloadUpdate()
})

ipcMain.handle('install-update', (event) => {
  if (!isTrustedSender(event)) return
  autoUpdater.quitAndInstall()
})

autoUpdater.on('update-available', (info) => {
  mainWindow?.webContents.send('update-available', info)
})

autoUpdater.on('download-progress', (progress) => {
  mainWindow?.webContents.send('update-download-progress', progress)
})

autoUpdater.on('update-downloaded', (info) => {
  mainWindow?.webContents.send('update-downloaded', info)
})

autoUpdater.on('error', (error) => {
  mainWindow?.webContents.send('update-error', error.message)
})
