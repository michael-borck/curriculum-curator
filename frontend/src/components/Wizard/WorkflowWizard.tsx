import React, { useState, useEffect } from 'react';
import {
  ChevronRight,
  CheckCircle,
  Circle,
  AlertCircle,
  RefreshCw,
  X,
  FileText,
  Loader2,
} from 'lucide-react';
import workflowApi from '../../services/workflowApi';
import {
  WorkflowSession,
  WorkflowQuestion,
  WorkflowStage,
  SessionStatus,
} from '../../types/workflow';

interface WorkflowWizardProps {
  unitId: string;
  unitName: string;
  onComplete?: (outlineId: string) => void;
  onCancel?: () => void;
}

const STAGE_LABELS: Record<WorkflowStage, string> = {
  [WorkflowStage.INITIAL]: 'Getting Started',
  [WorkflowStage.COURSE_OVERVIEW]: 'Unit Overview',
  [WorkflowStage.LEARNING_OUTCOMES]: 'Learning Outcomes',
  [WorkflowStage.UNIT_BREAKDOWN]: 'Unit Breakdown',
  [WorkflowStage.WEEKLY_PLANNING]: 'Weekly Planning',
  [WorkflowStage.CONTENT_GENERATION]: 'Content Generation',
  [WorkflowStage.QUALITY_REVIEW]: 'Quality Review',
  [WorkflowStage.COMPLETED]: 'Completed',
};

const WorkflowWizard: React.FC<WorkflowWizardProps> = ({
  unitId,
  unitName,
  onComplete,
  onCancel,
}) => {
  const [session, setSession] = useState<WorkflowSession | null>(null);
  const [currentQuestion, setCurrentQuestion] =
    useState<WorkflowQuestion | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [completionMessage, setCompletionMessage] = useState<string | null>(
    null
  );
  const [nextSteps, setNextSteps] = useState<string[]>([]);

  // Initialize workflow session
  useEffect(() => {
    initializeSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unitId]);

  const initializeSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await workflowApi.createSession(
        unitId,
        `Content Creation for ${unitName}`
      );
      setSession(response.session);
      setCurrentQuestion(response.next_question);
      setProgress(response.next_question?.progress || 0);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start workflow');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!session || !currentQuestion || selectedAnswer === null) return;

    setLoading(true);
    setError(null);
    try {
      const response = await workflowApi.submitAnswer(
        session.id,
        currentQuestion.question_key,
        selectedAnswer
      );

      if (response.status === 'completed' || response.status === 'ready_to_generate') {
        setCompletionMessage(
          response.message || 'Workflow completed successfully!'
        );
        setNextSteps(response.next_steps || []);
        setCurrentQuestion(null);
        setProgress(response.status === 'completed' ? 100 : response.progress || progress);
      } else {
        setCurrentQuestion(response.next_question || null);
        setProgress(response.progress || progress);
        if (response.stage) {
          setSession({ ...session, currentStage: response.stage });
        }
      }
      setSelectedAnswer(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit answer');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateStructure = async (useAI: boolean = true) => {
    if (!session) return;

    setLoading(true);
    setError(null);
    try {
      const result = await workflowApi.generateUnitStructure(session.id, useAI);
      if (result.status === 'success') {
        const structureType = useAI ? 'AI-assisted' : 'empty';
        setCompletionMessage(
          `${structureType} unit structure generated successfully! 
          ${result.structure?.learning_outcomes?.length || 0} learning outcomes, 
          ${result.structure?.weekly_topics?.length || 0} weekly topics, and 
          ${result.structure?.assessments?.length || 0} assessments created.`
        );
        if (onComplete) {
          onComplete(result.outline_id);
        }
      } else if (result.status === 'exists') {
        setError(result.message);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Failed to generate unit structure'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResetSession = async () => {
    if (!session) return;

    setLoading(true);
    setError(null);
    try {
      const response = await workflowApi.resetSession(session.id);
      setCurrentQuestion(response.next_question);
      setProgress(0);
      setCompletionMessage(null);
      setNextSteps([]);
      setSession({ ...session, currentStage: WorkflowStage.COURSE_OVERVIEW });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset session');
    } finally {
      setLoading(false);
    }
  };

  const renderQuestion = () => {
    if (!currentQuestion) return null;

    switch (currentQuestion.input_type) {
      case 'select':
        return (
          <div className='space-y-2'>
            {currentQuestion.options?.map(option => (
              <label
                key={option}
                className='flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors'
              >
                <input
                  type='radio'
                  name='answer'
                  value={option}
                  checked={selectedAnswer === option}
                  onChange={e => setSelectedAnswer(e.target.value)}
                  className='mr-3'
                />
                <span className='text-gray-700'>{option}</span>
              </label>
            ))}
          </div>
        );

      case 'multiselect':
        return (
          <div className='space-y-2'>
            {currentQuestion.options?.map(option => (
              <label
                key={option}
                className='flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors'
              >
                <input
                  type='checkbox'
                  value={option}
                  checked={selectedAnswer?.includes(option) || false}
                  onChange={e => {
                    const current = selectedAnswer || [];
                    if (e.target.checked) {
                      setSelectedAnswer([...current, option]);
                    } else {
                      setSelectedAnswer(
                        current.filter((v: string) => v !== option)
                      );
                    }
                  }}
                  className='mr-3'
                />
                <span className='text-gray-700'>{option}</span>
              </label>
            ))}
          </div>
        );

      case 'number':
        return (
          <input
            type='number'
            value={selectedAnswer || ''}
            onChange={e => setSelectedAnswer(parseInt(e.target.value))}
            className='w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            placeholder='Enter a number...'
          />
        );

      case 'text':
        return (
          <textarea
            value={selectedAnswer || ''}
            onChange={e => setSelectedAnswer(e.target.value)}
            className='w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            rows={4}
            placeholder='Enter your answer...'
          />
        );

      default:
        return null;
    }
  };

  const renderProgressBar = () => {
    const stages = [
      WorkflowStage.COURSE_OVERVIEW,
      WorkflowStage.LEARNING_OUTCOMES,
      WorkflowStage.UNIT_BREAKDOWN,
      WorkflowStage.WEEKLY_PLANNING,
      WorkflowStage.CONTENT_GENERATION,
      WorkflowStage.QUALITY_REVIEW,
    ];

    const currentStageIndex = session
      ? stages.indexOf(session.currentStage)
      : -1;

    return (
      <div className='mb-8'>
        <div className='flex justify-between items-center mb-4'>
          {stages.map((stage, index) => (
            <div
              key={stage}
              className={`flex flex-col items-center ${
                index < stages.length - 1 ? 'flex-1' : ''
              }`}
            >
              <div className='flex items-center w-full'>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-sm ${
                    index < currentStageIndex
                      ? 'bg-green-500'
                      : index === currentStageIndex
                        ? 'bg-blue-500'
                        : 'bg-gray-300'
                  }`}
                >
                  {index < currentStageIndex ? (
                    <CheckCircle className='w-5 h-5' />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < stages.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      index < currentStageIndex ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
              <span className='text-xs mt-1 text-center max-w-[100px]'>
                {STAGE_LABELS[stage]}
              </span>
            </div>
          ))}
        </div>
        <div className='bg-gray-200 rounded-full h-2'>
          <div
            className='bg-blue-500 h-2 rounded-full transition-all duration-300'
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    );
  };

  if (loading && !session) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='w-8 h-8 animate-spin text-blue-500' />
      </div>
    );
  }

  return (
    <div className='max-w-4xl mx-auto p-6'>
      <div className='bg-white rounded-lg shadow-lg'>
        {/* Header */}
        <div className='px-6 py-4 border-b flex justify-between items-center'>
          <div>
            <h2 className='text-2xl font-bold text-gray-900'>
              Guided Content Creation
            </h2>
            <p className='text-gray-600 mt-1'>
              {unitName} -{' '}
              {session ? STAGE_LABELS[session.currentStage] : 'Initializing...'}
            </p>
          </div>
          {onCancel && (
            <button
              onClick={onCancel}
              className='text-gray-500 hover:text-gray-700'
            >
              <X className='w-6 h-6' />
            </button>
          )}
        </div>

        {/* Progress Bar */}
        <div className='px-6 py-4'>{renderProgressBar()}</div>

        {/* Content */}
        <div className='px-6 py-4 min-h-[300px]'>
          {error && (
            <div className='mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start'>
              <AlertCircle className='w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5' />
              <span className='text-red-700'>{error}</span>
            </div>
          )}

          {completionMessage ? (
            <div className='space-y-4'>
              <div className='p-4 bg-green-50 border border-green-200 rounded-lg'>
                <div className='flex items-start'>
                  <CheckCircle className='w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5' />
                  <div>
                    <p className='text-green-700 font-semibold'>
                      {completionMessage}
                    </p>
                    {nextSteps.length > 0 && (
                      <div className='mt-4'>
                        <p className='text-green-700 font-semibold mb-2'>
                          Next Steps:
                        </p>
                        <ul className='list-disc list-inside text-green-600 space-y-1'>
                          {nextSteps.map((step, index) => (
                            <li key={index}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {session?.status !== SessionStatus.COMPLETED && (
                <div className='space-y-3'>
                  <button
                    onClick={() => handleGenerateStructure(true)}
                    className='w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center'
                  >
                    <FileText className='w-5 h-5 mr-2' />
                    Generate with AI Assistance
                  </button>
                  <button
                    onClick={() => handleGenerateStructure(false)}
                    className='w-full px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center justify-center'
                  >
                    <FileText className='w-5 h-5 mr-2' />
                    Create Empty Structure
                  </button>
                </div>
              )}
            </div>
          ) : currentQuestion ? (
            <div className='space-y-4'>
              <div className='text-lg font-semibold text-gray-900'>
                {currentQuestion.question_text}
              </div>
              {renderQuestion()}
            </div>
          ) : (
            <div className='text-center py-8'>
              <Circle className='w-12 h-12 text-gray-400 mx-auto mb-4' />
              <p className='text-gray-600'>No more questions in this stage</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className='px-6 py-4 border-t flex justify-between items-center'>
          <button
            onClick={handleResetSession}
            disabled={loading || !session}
            className='px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors flex items-center disabled:opacity-50'
          >
            <RefreshCw className='w-4 h-4 mr-2' />
            Reset
          </button>

          <div className='flex space-x-3'>
            {currentQuestion && (
              <button
                onClick={handleSubmitAnswer}
                disabled={loading || selectedAnswer === null}
                className='px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center disabled:opacity-50'
              >
                {loading ? (
                  <Loader2 className='w-4 h-4 mr-2 animate-spin' />
                ) : (
                  <ChevronRight className='w-4 h-4 mr-2' />
                )}
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowWizard;
