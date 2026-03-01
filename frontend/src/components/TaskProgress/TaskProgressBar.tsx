/**
 * Reusable progress bar for background tasks.
 * Shows a bar + label + error list.
 */

import React from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import type { TaskStatus } from '../../services/taskApi';

interface TaskProgressBarProps {
  status: TaskStatus;
  /** Hide the label text. Default: false. */
  compact?: boolean | undefined;
}

const TaskProgressBar: React.FC<TaskProgressBarProps> = ({
  status,
  compact = false,
}) => {
  const pct =
    status.total > 0
      ? Math.round((status.progress / status.total) * 100)
      : null;
  const indeterminate = pct === null && status.status === 'processing';

  return (
    <div className='w-full space-y-1'>
      {/* Label */}
      {!compact && status.label && (
        <div className='flex items-center gap-2 text-xs text-gray-500'>
          {status.status === 'processing' && (
            <Loader2 className='w-3 h-3 animate-spin' />
          )}
          <span className='truncate'>{status.label}</span>
          {pct !== null && <span className='ml-auto tabular-nums'>{pct}%</span>}
        </div>
      )}

      {/* Bar */}
      <div className='w-full bg-gray-200 rounded-full h-1.5 overflow-hidden'>
        {indeterminate ? (
          <div className='h-full bg-purple-500 rounded-full animate-pulse w-full' />
        ) : (
          <div
            className='h-full bg-purple-600 rounded-full transition-all duration-300'
            style={{ width: `${pct ?? 0}%` }}
          />
        )}
      </div>

      {/* Errors */}
      {status.errors.length > 0 && (
        <div className='space-y-0.5'>
          {status.errors.map((err, i) => (
            <div
              key={i}
              className='flex items-start gap-1 text-xs text-red-600'
            >
              <AlertCircle className='w-3 h-3 mt-0.5 flex-shrink-0' />
              <span>{err}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TaskProgressBar;
