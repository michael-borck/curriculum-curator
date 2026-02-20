import { execSync, spawn, type ChildProcess } from 'child_process'
import http from 'http'

const OLLAMA_HOST = '127.0.0.1'
const OLLAMA_PORT = 11434

let ollamaProcess: ChildProcess | null = null
let ollamaWasRunning = false

/**
 * Detect the Ollama binary on the system.
 * Returns the binary path or null if not found.
 */
export function detectOllama(): string | null {
  // Try `which` (macOS/Linux) or `where` (Windows)
  const whichCmd = process.platform === 'win32' ? 'where ollama' : 'which ollama'
  try {
    const result = execSync(whichCmd, { encoding: 'utf-8', timeout: 5000 }).trim()
    if (result) return result.split('\n')[0].trim()
  } catch {
    // Not found via PATH, try known locations
  }

  const fallbackPaths =
    process.platform === 'win32'
      ? [
          `${process.env.LOCALAPPDATA}\\Programs\\Ollama\\ollama.exe`,
          `${process.env.PROGRAMFILES}\\Ollama\\ollama.exe`,
        ]
      : ['/usr/local/bin/ollama', '/opt/homebrew/bin/ollama', '/usr/bin/ollama']

  const fs = require('fs') as typeof import('fs')
  for (const p of fallbackPaths) {
    try {
      if (fs.existsSync(p)) return p
    } catch {
      // skip
    }
  }

  return null
}

function ollamaHealthCheck(): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(`http://${OLLAMA_HOST}:${OLLAMA_PORT}/api/tags`, (res) => {
      resolve(res.statusCode === 200)
    })
    req.on('error', () => resolve(false))
    req.setTimeout(2000, () => {
      req.destroy()
      resolve(false)
    })
  })
}

/**
 * Start Ollama if it's not already running.
 * Returns true if Ollama is available, false otherwise.
 */
export async function startOllama(): Promise<boolean> {
  // Check if already running
  const alreadyRunning = await ollamaHealthCheck()
  if (alreadyRunning) {
    ollamaWasRunning = true
    console.log('[ollama] already running (external instance)')
    return true
  }

  // Detect binary
  const binaryPath = detectOllama()
  if (!binaryPath) {
    console.warn('[ollama] binary not found on system')
    return false
  }

  console.log(`[ollama] starting from ${binaryPath}`)

  ollamaProcess = spawn(binaryPath, ['serve'], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env } as Record<string, string>,
  })

  ollamaProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`[ollama] ${data.toString().trim()}`)
  })

  ollamaProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`[ollama] ${data.toString().trim()}`)
  })

  ollamaProcess.on('exit', (code) => {
    console.log(`[ollama] process exited with code ${code}`)
    ollamaProcess = null
  })

  // Wait up to 15s for Ollama to become healthy
  for (let i = 0; i < 15; i++) {
    const healthy = await ollamaHealthCheck()
    if (healthy) {
      console.log(`[ollama] healthy after ${i + 1}s`)
      return true
    }
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }

  console.error('[ollama] failed to become healthy within 15s')
  return false
}

/**
 * Stop Ollama gracefully. Skips if it was already running before we started.
 */
export async function stopOllama(): Promise<void> {
  if (ollamaWasRunning) {
    console.log('[ollama] skipping shutdown (was already running)')
    return
  }

  if (!ollamaProcess) return

  return new Promise((resolve) => {
    const proc = ollamaProcess!

    const killTimer = setTimeout(() => {
      console.warn('[ollama] SIGTERM timeout, sending SIGKILL')
      proc.kill('SIGKILL')
    }, 3000)

    proc.on('exit', () => {
      clearTimeout(killTimer)
      ollamaProcess = null
      resolve()
    })

    proc.kill('SIGTERM')
  })
}
