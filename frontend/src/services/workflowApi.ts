/**
 * API service for workflow operations
 */

import api from './api';
import {
  WorkflowSession,
  WorkflowQuestion,
  WorkflowStatus,
  WorkflowStageInfo,
  UnitStructureResult,
  PDFAnalysisResult,
  WorkflowStage,
} from '../types/workflow';

class WorkflowAPI {
  /**
   * Create a new workflow session
   */
  async createSession(
    unitId: string,
    sessionName?: string
  ): Promise<{
    status: string;
    session: WorkflowSession;
    next_question: WorkflowQuestion;
  }> {
    const response = await api.post(
      `/api/content/workflow/sessions/create/${unitId}`,
      {
        session_name: sessionName,
      }
    );
    return response.data;
  }

  /**
   * Get workflow session status
   */
  async getSessionStatus(sessionId: string): Promise<WorkflowStatus> {
    const response = await api.get(
      `/api/content/workflow/sessions/${sessionId}/status`
    );
    return response.data;
  }

  /**
   * Get next question in workflow
   */
  async getNextQuestion(sessionId: string): Promise<{
    status: string;
    question?: WorkflowQuestion;
    workflow_status?: string;
    current_stage?: WorkflowStage;
    can_generate?: boolean;
  }> {
    const response = await api.get(
      `/api/content/workflow/sessions/${sessionId}/next-question`
    );
    return response.data;
  }

  /**
   * Submit answer to workflow question
   */
  async submitAnswer(
    sessionId: string,
    questionKey: string,
    answer: any
  ): Promise<{
    status: string;
    next_question?: WorkflowQuestion;
    stage?: WorkflowStage;
    progress?: number;
    message?: string;
    next_steps?: string[];
  }> {
    const response = await api.post(
      `/api/content/workflow/sessions/${sessionId}/answer`,
      {
        question_key: questionKey,
        answer: answer,
      }
    );
    return response.data;
  }

  /**
   * Generate unit structure from workflow decisions
   */
  async generateUnitStructure(sessionId: string): Promise<UnitStructureResult> {
    const response = await api.post(
      `/api/content/workflow/sessions/${sessionId}/generate-structure`
    );
    return response.data;
  }

  /**
   * Get all workflow stages
   */
  async getWorkflowStages(): Promise<{ stages: WorkflowStageInfo[] }> {
    const response = await api.get('/api/content/workflow/stages');
    return response.data;
  }

  /**
   * Get questions for a specific stage
   */
  async getStageQuestions(stage: WorkflowStage): Promise<{
    stage: WorkflowStage;
    questions: any[];
    question_count: number;
  }> {
    const response = await api.get(
      `/api/content/workflow/stages/${stage}/questions`
    );
    return response.data;
  }

  /**
   * List all workflow sessions
   */
  async listSessions(
    includeCompleted = true,
    skip = 0,
    limit = 20
  ): Promise<{
    total: number;
    sessions: WorkflowSession[];
  }> {
    const response = await api.get('/api/content/workflow/sessions', {
      params: { include_completed: includeCompleted, skip, limit },
    });
    return response.data;
  }

  /**
   * Delete a workflow session
   */
  async deleteSession(
    sessionId: string
  ): Promise<{ status: string; message: string }> {
    const response = await api.delete(
      `/api/content/workflow/sessions/${sessionId}`
    );
    return response.data;
  }

  /**
   * Reset a workflow session
   */
  async resetSession(sessionId: string): Promise<{
    status: string;
    message: string;
    next_question: WorkflowQuestion;
  }> {
    const response = await api.post(
      `/api/content/workflow/sessions/${sessionId}/reset`
    );
    return response.data;
  }

  /**
   * Analyze PDF document
   */
  async analyzePDF(
    file: File,
    extractionMethod = 'auto'
  ): Promise<PDFAnalysisResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('extraction_method', extractionMethod);

    const response = await api.post(
      '/api/content/import/pdf/analyze',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Extract text from PDF
   */
  async extractPDFText(
    file: File,
    outputFormat = 'markdown',
    extractionMethod = 'auto'
  ): Promise<{
    status: string;
    filename: string;
    metadata: any;
    text: string;
    structure: any;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('extraction_method', extractionMethod);
    formData.append('output_format', outputFormat);

    const response = await api.post(
      '/api/content/import/pdf/extract-text',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Create unit structure from PDF
   */
  async createUnitStructureFromPDF(
    unitId: string,
    file: File,
    autoCreate = true
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_create', autoCreate.toString());

    const response = await api.post(
      `/api/content/import/pdf/create-course-structure/${unitId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Get import suggestions for a unit
   */
  async getImportSuggestions(unitId: string): Promise<{
    unit: { id: string; name: string };
    current_state: any;
    suggestions: any[];
    next_steps: string[];
  }> {
    const response = await api.get(`/api/content/import/suggestions/${unitId}`);
    return response.data;
  }
}

export default new WorkflowAPI();
