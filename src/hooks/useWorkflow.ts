// Workflow management hook for Expert Mode
import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface WorkflowStep {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress: number;
  error?: string;
}

export interface WorkflowState {
  workflowId: string | null;
  currentStep: number;
  totalSteps: number;
  steps: WorkflowStep[];
  isRunning: boolean;
  error: string | null;
}

export interface ContentRequest {
  topic: string;
  learningObjectives: string[];
  duration: string;
  audience: string;
  contentTypes: string[];
}

export function useWorkflow() {
  const [state, setState] = useState<WorkflowState>({
    workflowId: null,
    currentStep: 0,
    totalSteps: 4,
    steps: [
      { name: 'Content Planning', status: 'pending', progress: 0 },
      { name: 'Material Generation', status: 'pending', progress: 0 },
      { name: 'Assessment Creation', status: 'pending', progress: 0 },
      { name: 'Quality Review', status: 'pending', progress: 0 },
    ],
    isRunning: false,
    error: null,
  });

  const createWorkflow = useCallback(async (contentRequest: ContentRequest) => {
    try {
      const workflowId = await invoke<string>('create_workflow', {
        name: `Workflow for ${contentRequest.topic}`,
        contentRequest,
      });
      
      setState(prev => ({
        ...prev,
        workflowId,
        error: null,
      }));
      
      return workflowId;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to create workflow',
      }));
      throw error;
    }
  }, []);

  const executeStep = useCallback(async (stepIndex: number) => {
    if (!state.workflowId) {
      throw new Error('No workflow created');
    }

    setState(prev => ({
      ...prev,
      isRunning: true,
      steps: prev.steps.map((step, index) => 
        index === stepIndex 
          ? { ...step, status: 'running' as const, progress: 0 }
          : step
      ),
      error: null,
    }));

    try {
      const result = await invoke<{
        status: string;
        output?: any;
        error?: string;
        progress?: number;
        message?: string;
      }>('execute_workflow_step', {
        workflowId: state.workflowId,
        stepIndex,
      });

      setState(prev => ({
        ...prev,
        isRunning: false,
        currentStep: stepIndex + 1,
        steps: prev.steps.map((step, index) => 
          index === stepIndex 
            ? { 
                ...step, 
                status: result.error ? 'failed' : 'completed' as const,
                progress: 100,
                error: result.error,
              }
            : step
        ),
      }));

      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isRunning: false,
        steps: prev.steps.map((step, index) => 
          index === stepIndex 
            ? { 
                ...step, 
                status: 'failed' as const,
                error: error instanceof Error ? error.message : 'Step execution failed',
              }
            : step
        ),
        error: error instanceof Error ? error.message : 'Step execution failed',
      }));
      throw error;
    }
  }, [state.workflowId]);

  const executeQuickAction = useCallback(async (
    action: 'slides_only' | 'assessment_suite' | 'learning_objectives' | 'complete_package',
    contentRequest: ContentRequest
  ) => {
    setState(prev => ({
      ...prev,
      isRunning: true,
      error: null,
    }));

    try {
      const result = await invoke<{
        action: string;
        status: string;
        content?: any[];
        output?: any;
        message?: string;
      }>('execute_quick_action', {
        action,
        contentRequest,
      });

      setState(prev => ({
        ...prev,
        isRunning: false,
      }));

      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isRunning: false,
        error: error instanceof Error ? error.message : 'Quick action failed',
      }));
      throw error;
    }
  }, []);

  const skipStep = useCallback((stepIndex: number) => {
    setState(prev => ({
      ...prev,
      steps: prev.steps.map((step, index) => 
        index === stepIndex 
          ? { ...step, status: 'skipped' as const }
          : step
      ),
      currentStep: Math.max(prev.currentStep, stepIndex + 1),
    }));
  }, []);

  const resetWorkflow = useCallback(() => {
    setState({
      workflowId: null,
      currentStep: 0,
      totalSteps: 4,
      steps: [
        { name: 'Content Planning', status: 'pending', progress: 0 },
        { name: 'Material Generation', status: 'pending', progress: 0 },
        { name: 'Assessment Creation', status: 'pending', progress: 0 },
        { name: 'Quality Review', status: 'pending', progress: 0 },
      ],
      isRunning: false,
      error: null,
    });
  }, []);

  return {
    state,
    createWorkflow,
    executeStep,
    executeQuickAction,
    skipStep,
    resetWorkflow,
  };
}