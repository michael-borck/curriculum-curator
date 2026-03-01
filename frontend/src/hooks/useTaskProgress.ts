/**
 * React hook for subscribing to background task progress via SSE.
 *
 * Usage:
 *   const { status, start } = useTaskProgress({ onComplete, onError });
 *   // kick off: start(taskId)
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  type TaskStatus,
  downloadTaskResult,
  getTaskStatus,
  streamTaskProgress,
} from '../services/taskApi';

interface UseTaskProgressOptions {
  /** Called when task reaches "completed". */
  onComplete?: (status: TaskStatus) => void;
  /** Called when task reaches "failed" or SSE errors out. */
  onError?: (error: string) => void;
  /** Auto-download the result file when complete. Default: false. */
  autoDownload?: boolean | undefined;
}

interface UseTaskProgressReturn {
  /** Current task status (null before start). */
  status: TaskStatus | null;
  /** Begin tracking a task by id. */
  start: (taskId: string) => void;
  /** Stop tracking (cleanup). */
  stop: () => void;
  /** Whether a task is actively being tracked. */
  active: boolean;
}

export function useTaskProgress(
  options: UseTaskProgressOptions = {}
): UseTaskProgressReturn {
  const { onComplete, onError, autoDownload = false } = options;
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [active, setActive] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const pollRef = useRef<number | null>(null);

  // Stable refs for callbacks to avoid re-subscriptions
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;

  const cleanup = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setActive(false);
  }, []);

  const handleUpdate = useCallback(
    (s: TaskStatus) => {
      setStatus(s);
      if (s.status === 'completed') {
        cleanup();
        if (autoDownload) {
          void downloadTaskResult(s.taskId);
        }
        onCompleteRef.current?.(s);
      } else if (s.status === 'failed') {
        cleanup();
        const msg = s.errors.length > 0 ? s.errors.join('; ') : 'Task failed';
        onErrorRef.current?.(msg);
      }
    },
    [cleanup, autoDownload]
  );

  const start = useCallback(
    (taskId: string) => {
      // Clean up any previous subscription
      cleanup();
      setActive(true);
      setStatus(null);

      // Try SSE first
      const controller = streamTaskProgress(
        taskId,
        handleUpdate,
        (_sseError: string) => {
          // SSE failed — fall back to polling
          pollRef.current = window.setInterval(() => {
            void (async () => {
              try {
                const s = await getTaskStatus(taskId);
                handleUpdate(s);
              } catch (err) {
                cleanup();
                onErrorRef.current?.((err as Error).message);
              }
            })();
          }, 1000);
        }
      );
      controllerRef.current = controller;
    },
    [cleanup, handleUpdate]
  );

  const stop = useCallback(() => {
    cleanup();
    setStatus(null);
  }, [cleanup]);

  // Cleanup on unmount
  useEffect(() => cleanup, [cleanup]);

  return { status, start, stop, active };
}
