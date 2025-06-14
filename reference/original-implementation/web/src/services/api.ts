import axios from 'axios';
import {
  WorkflowSession,
  WorkflowRunRequest,
  WorkflowRunResponse,
  WorkflowListResponse,
  ValidatorInfo,
  RemediatorInfo,
  PromptListResponse,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const workflowApi = {
  // List all workflows
  listWorkflows: (): Promise<WorkflowListResponse> =>
    api.get('/api/workflows').then(response => response.data),

  // Run a workflow
  runWorkflow: (request: WorkflowRunRequest): Promise<WorkflowRunResponse> =>
    api.post('/api/workflows/run', request).then(response => response.data),

  // Get workflow session
  getWorkflowSession: (sessionId: string): Promise<WorkflowSession> =>
    api.get(`/api/workflows/sessions/${sessionId}`).then(response => response.data),

  // List all workflow sessions
  listWorkflowSessions: (): Promise<WorkflowSession[]> =>
    api.get('/api/workflows/sessions').then(response => response.data),
};

export const promptApi = {
  // List prompts
  listPrompts: (tag?: string): Promise<PromptListResponse> => {
    const params = tag ? { tag } : {};
    return api.get('/api/prompts', { params }).then(response => response.data);
  },
};

export const validatorApi = {
  // List validators
  listValidators: (): Promise<Record<string, ValidatorInfo[]>> =>
    api.get('/api/validators').then(response => response.data),
};

export const remediatorApi = {
  // List remediators
  listRemediators: (): Promise<Record<string, RemediatorInfo[]>> =>
    api.get('/api/remediators').then(response => response.data),
};

export const healthApi = {
  // Health check
  checkHealth: (): Promise<{ status: string; message: string }> =>
    api.get('/health').then(response => response.data),
};