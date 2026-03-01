/**
 * API client for the generic background-task system.
 *
 * Provides SSE streaming, polling fallback, and download helpers.
 */

// ─── Types ───────────────────────────────────────────────────────────

export interface TaskStatus {
  taskId: string;
  kind: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  total: number;
  label: string;
  errors: string[];
  meta: Record<string, unknown>;
  result: Record<string, unknown> | null;
  createdAt: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ─── Poll ────────────────────────────────────────────────────────────

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const resp = await window.fetch(`/api/bg-tasks/${taskId}`, {
    headers: getAuthHeaders(),
  });
  if (!resp.ok) throw new Error(`Task not found (${resp.status})`);
  return (await resp.json()) as TaskStatus;
}

// ─── SSE stream ──────────────────────────────────────────────────────

export function streamTaskProgress(
  taskId: string,
  onUpdate: (status: TaskStatus) => void,
  onError: (error: string) => void
): AbortController {
  const controller = new AbortController();

  void (async () => {
    try {
      const resp = await window.fetch(`/api/bg-tasks/${taskId}/events`, {
        headers: getAuthHeaders(),
        signal: controller.signal,
      });
      if (!resp.ok) {
        onError(`SSE connection failed (${resp.status})`);
        return;
      }

      const reader = resp.body?.getReader();
      if (!reader) {
        onError('No response body');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      let done = false;
      while (!done) {
        const result = await reader.read();
        done = result.done;
        const value = result.value;
        if (done || !value) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as TaskStatus;
              onUpdate(data);
            } catch {
              // skip malformed lines
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        onError((err as Error).message);
      }
    }
  })();

  return controller;
}

// ─── Download ────────────────────────────────────────────────────────

export async function downloadTaskResult(taskId: string): Promise<string> {
  const resp = await window.fetch(`/api/bg-tasks/${taskId}/download`, {
    headers: getAuthHeaders(),
  });
  if (!resp.ok) throw new Error(`Download failed (${resp.status})`);

  const disposition = resp.headers.get('content-disposition');
  const match = disposition?.match(/filename="?([^"]+)"?/);
  const filename = match?.[1] ?? 'download';

  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(url);
  a.remove();

  return filename;
}
