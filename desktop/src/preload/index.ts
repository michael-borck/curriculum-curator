import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Electron APIs exposed to renderer
const api = {
  // File export: native Save As dialog
  saveFile: (defaultName: string, data: Buffer | string): Promise<string | null> => {
    return ipcRenderer.invoke('save-file', defaultName, data)
  },

  // Ollama info
  getOllamaInfo: (): Promise<{ installed: boolean; binaryPath: string | null }> => {
    return ipcRenderer.invoke('get-ollama-info')
  },

  // Auto-updater
  checkForUpdates: (): Promise<unknown> => {
    return ipcRenderer.invoke('check-for-updates')
  },
  downloadUpdate: (): Promise<unknown> => {
    return ipcRenderer.invoke('download-update')
  },
  installUpdate: (): Promise<void> => {
    return ipcRenderer.invoke('install-update')
  },

  // Update event listeners
  onUpdateAvailable: (callback: (info: unknown) => void): void => {
    ipcRenderer.on('update-available', (_event, info) => callback(info))
  },
  onUpdateDownloadProgress: (callback: (progress: unknown) => void): void => {
    ipcRenderer.on('update-download-progress', (_event, progress) => callback(progress))
  },
  onUpdateDownloaded: (callback: (info: unknown) => void): void => {
    ipcRenderer.on('update-downloaded', (_event, info) => callback(info))
  },
  onUpdateError: (callback: (message: string) => void): void => {
    ipcRenderer.on('update-error', (_event, message) => callback(message))
  }
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error('Failed to expose APIs via contextBridge:', error)
  }
} else {
  // @ts-expect-error -- fallback for non-isolated contexts
  window.electron = electronAPI
  // @ts-expect-error -- fallback for non-isolated contexts
  window.api = api
}
