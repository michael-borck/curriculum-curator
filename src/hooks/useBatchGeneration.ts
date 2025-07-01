import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface BatchItem {
  topic: string;
  learningObjectives: string[];
  duration: string;
  audience: string;
  contentTypes: string[];
  priority?: 'low' | 'normal' | 'high' | 'critical';
  metadata?: Record<string, any>;
}

export interface BatchGenerationOptions {
  parallelGeneration?: boolean;
  maxParallelJobs?: number;
  continueOnError?: boolean;
  savePartialResults?: boolean;
  retryFailedItems?: boolean;
  maxRetries?: number;
}

export interface BatchGenerationResult {
  batchId: string;
  totalItems: number;
  successfulItems: number;
  failedItems: number;
  itemResults: Array<{
    itemId: string;
    success: boolean;
    generatedContent?: any[];
    error?: string;
    elapsedTime: number;
    retryCount: number;
  }>;
  totalElapsedTime: number;
  errors: Array<{
    itemId: string;
    errorMessage: string;
    errorType: string;
    retryable: boolean;
  }>;
}

export interface BatchProgress {
  batchId: string;
  totalItems: number;
  completedItems: number;
  failedItems: number;
  currentItemId?: string;
  currentOperation: string;
  progressPercent: number;
  elapsedTime: number;
  estimatedTimeRemaining?: number;
  errors: any[];
}

export interface BatchState {
  isRunning: boolean;
  currentBatchId: string | null;
  progress: BatchProgress | null;
  result: BatchGenerationResult | null;
  error: string | null;
}

export function useBatchGeneration() {
  const [state, setState] = useState<BatchState>({
    isRunning: false,
    currentBatchId: null,
    progress: null,
    result: null,
    error: null,
  });

  const createBatch = useCallback(async (
    batchName: string,
    items: BatchItem[],
    options?: BatchGenerationOptions
  ): Promise<string> => {
    try {
      const batchId = await invoke<string>('create_batch_generation', {
        request: {
          batchName,
          items: items.map(item => ({
            topic: item.topic,
            learning_objectives: item.learningObjectives,
            duration: item.duration,
            audience: item.audience,
            content_types: item.contentTypes,
            priority: item.priority || 'normal',
            metadata: item.metadata || {},
          })),
          options: options || {
            parallel_generation: true,
            max_parallel_jobs: 3,
            continue_on_error: true,
            save_partial_results: true,
            retry_failed_items: true,
            max_retries: 2,
          },
        },
      });

      setState(prev => ({
        ...prev,
        currentBatchId: batchId,
        error: null,
      }));

      return batchId;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create batch';
      setState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  const executeBatch = useCallback(async (
    batchId: string,
    batchName: string,
    items: BatchItem[],
    options?: BatchGenerationOptions
  ): Promise<BatchGenerationResult> => {
    setState(prev => ({
      ...prev,
      isRunning: true,
      currentBatchId: batchId,
      error: null,
      result: null,
    }));

    try {
      const batchRequest = {
        batch_id: batchId,
        batch_name: batchName,
        items: items.map((item, index) => ({
          id: `item_${index}`,
          content_request: {
            topic: item.topic,
            learning_objectives: item.learningObjectives,
            duration: item.duration,
            audience: item.audience,
            content_types: item.contentTypes.map(ct => `"${ct}"`),
            session_id: null,
          },
          priority: item.priority || 'normal',
          metadata: item.metadata || {},
        })),
        options: options || {
          parallel_generation: true,
          max_parallel_jobs: 3,
          continue_on_error: true,
          save_partial_results: true,
          retry_failed_items: true,
          max_retries: 2,
        },
      };

      const result = await invoke<BatchGenerationResult>('execute_batch_generation', {
        batchId,
        batchRequest,
      });

      setState(prev => ({
        ...prev,
        isRunning: false,
        result,
      }));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Batch execution failed';
      setState(prev => ({
        ...prev,
        isRunning: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  const getBatchStatus = useCallback(async (batchId: string) => {
    try {
      const status = await invoke<BatchProgress>('get_batch_status', { batchId });
      setState(prev => ({
        ...prev,
        progress: status,
      }));
      return status;
    } catch (error) {
      console.error('Failed to get batch status:', error);
      return null;
    }
  }, []);

  const cancelBatch = useCallback(async (batchId: string): Promise<boolean> => {
    try {
      const success = await invoke<boolean>('cancel_batch_generation', { batchId });
      if (success) {
        setState(prev => ({
          ...prev,
          isRunning: false,
          currentBatchId: null,
        }));
      }
      return success;
    } catch (error) {
      console.error('Failed to cancel batch:', error);
      return false;
    }
  }, []);

  const listBatches = useCallback(async () => {
    try {
      return await invoke<any[]>('list_batch_generations');
    } catch (error) {
      console.error('Failed to list batches:', error);
      return [];
    }
  }, []);

  const exportResults = useCallback(async (
    batchId: string,
    format: string,
    outputDirectory: string
  ) => {
    try {
      return await invoke<any>('export_batch_results', {
        batchId,
        format,
        outputDirectory,
      });
    } catch (error) {
      console.error('Failed to export batch results:', error);
      throw error;
    }
  }, []);

  const resetState = useCallback(() => {
    setState({
      isRunning: false,
      currentBatchId: null,
      progress: null,
      result: null,
      error: null,
    });
  }, []);

  return {
    state,
    createBatch,
    executeBatch,
    getBatchStatus,
    cancelBatch,
    listBatches,
    exportResults,
    resetState,
  };
}