export interface WorkflowSession {
  session_id: string;
  workflow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  variables?: Record<string, any>;
  result?: any;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRunRequest {
  workflow: string;
  variables?: Record<string, any>;
  session_id?: string;
}

export interface WorkflowRunResponse {
  session_id: string;
  status: string;
  message: string;
}

export interface WorkflowInfo {
  name: string;
  description: string;
  steps?: any[];
}

export interface WorkflowListResponse {
  config_workflows: Record<string, WorkflowInfo>;
  predefined_workflows: Record<string, WorkflowInfo>;
}

export interface ValidatorInfo {
  name: string;
  implemented: boolean;
  category: string;
}

export interface RemediatorInfo {
  name: string;
  implemented: boolean;
  category: string;
}

export interface PromptListResponse {
  prompts: string[];
}