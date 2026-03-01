/**
 * Floating bottom-right toast that tracks a background task.
 * Designed for exports — shows progress, auto-downloads on complete.
 */

import React from 'react';
import { CheckCircle, Download, X, XCircle } from 'lucide-react';
import type { TaskStatus } from '../../services/taskApi';
import TaskProgressBar from './TaskProgressBar';

interface TaskProgressToastProps {
  status: TaskStatus;
  onDismiss: () => void;
}

const TaskProgressToast: React.FC<TaskProgressToastProps> = ({
  status,
  onDismiss,
}) => {
  const title =
    status.kind === 'export'
      ? `Exporting ${(status.meta.package_type as string | undefined) ?? 'package'}…`
      : `Processing ${status.kind}…`;

  const isDone = status.status === 'completed' || status.status === 'failed';

  return (
    <div className='fixed bottom-4 right-4 z-50 w-80 bg-white rounded-lg shadow-lg border border-gray-200 p-3 space-y-2'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div className='flex items-center gap-2 text-sm font-medium text-gray-700'>
          {status.status === 'completed' ? (
            <CheckCircle className='w-4 h-4 text-green-500' />
          ) : status.status === 'failed' ? (
            <XCircle className='w-4 h-4 text-red-500' />
          ) : (
            <Download className='w-4 h-4 text-purple-500' />
          )}
          <span>
            {status.status === 'completed'
              ? 'Export complete'
              : status.status === 'failed'
                ? 'Export failed'
                : title}
          </span>
        </div>
        {isDone && (
          <button
            onClick={onDismiss}
            className='text-gray-400 hover:text-gray-600'
          >
            <X className='w-4 h-4' />
          </button>
        )}
      </div>

      {/* Progress bar */}
      {!isDone && <TaskProgressBar status={status} />}

      {/* Errors */}
      {status.status === 'failed' && status.errors.length > 0 && (
        <div className='text-xs text-red-600'>
          {status.errors.map((e, i) => (
            <p key={i}>{e}</p>
          ))}
        </div>
      )}
    </div>
  );
};

export default TaskProgressToast;
