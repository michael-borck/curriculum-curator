import { spawn, type ChildProcess } from 'child_process'
import { join } from 'path'
import { existsSync, readFileSync, writeFileSync } from 'fs'
import { randomBytes } from 'crypto'
import { app } from 'electron'
import { is } from '@electron-toolkit/utils'
import http from 'http'

const PORT = 8000
const HOST = '127.0.0.1'

let backendProcess: ChildProcess | null = null

/** Per-install signing key, generated once and kept in userData (0600). */
function getOrCreateSecretKey(): string {
  const path = join(app.getPath('userData'), 'secret_key')
  if (existsSync(path)) {
    const existing = readFileSync(path, 'utf8').trim()
    if (existing.length >= 32) return existing
  }
  const generated = randomBytes(48).toString('hex')
  writeFileSync(path, generated + '\n', { mode: 0o600 })
  return generated
}

export function getBackendPort(): number {
  return PORT
}

export function startBackend(): void {
  const env: Record<string, string> = {
    ...process.env as Record<string, string>,
    LOCAL_MODE: 'true',
    DEBUG: 'false',
    SECRET_KEY: getOrCreateSecretKey(),
    DATABASE_URL: `sqlite:///${join(app.getPath('userData'), 'curriculum_curator.db')}`
  }

  if (is.dev) {
    // Dev mode: run uvicorn via uv from the backend directory
    const backendDir = join(app.getAppPath(), '..', 'backend')
    backendProcess = spawn('uv', [
      'run', 'uvicorn', 'app.main:app',
      '--port', String(PORT),
      '--host', HOST
    ], {
      cwd: backendDir,
      env,
      stdio: ['ignore', 'pipe', 'pipe']
    })
  } else {
    // Prod mode: run PyInstaller binary from extraResources
    const backendBin = join(process.resourcesPath, 'backend', 'curriculum-curator-api')
    const pandocPath = join(process.resourcesPath, 'pandoc')
    const typstPath = join(process.resourcesPath, 'typst')

    env.PANDOC_PATH = pandocPath
    env.TYPST_PATH = typstPath

    backendProcess = spawn(backendBin, [
      '--port', String(PORT),
      '--host', HOST
    ], {
      env,
      stdio: ['ignore', 'pipe', 'pipe']
    })
  }

  backendProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`[backend] ${data.toString().trim()}`)
  })

  backendProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`[backend] ${data.toString().trim()}`)
  })

  backendProcess.on('exit', (code) => {
    console.log(`[backend] process exited with code ${code}`)
    backendProcess = null
  })
}

function healthCheck(): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(`http://${HOST}:${PORT}/health`, (res) => {
      resolve(res.statusCode === 200)
    })
    req.on('error', () => resolve(false))
    req.setTimeout(1000, () => {
      req.destroy()
      resolve(false)
    })
  })
}

export async function waitForBackend(): Promise<boolean> {
  const maxRetries = is.dev ? 30 : 120
  const retryInterval = 1000

  for (let i = 0; i < maxRetries; i++) {
    const healthy = await healthCheck()
    if (healthy) {
      console.log(`[backend] healthy after ${i + 1} attempts`)
      return true
    }
    await new Promise((resolve) => setTimeout(resolve, retryInterval))
  }

  console.error('[backend] failed to become healthy within timeout')
  return false
}

export async function stopBackend(): Promise<void> {
  if (!backendProcess) return

  return new Promise((resolve) => {
    const proc = backendProcess!

    const killTimer = setTimeout(() => {
      console.warn('[backend] SIGTERM timeout, sending SIGKILL')
      proc.kill('SIGKILL')
    }, 3000)

    proc.on('exit', () => {
      clearTimeout(killTimer)
      backendProcess = null
      resolve()
    })

    proc.kill('SIGTERM')
  })
}
