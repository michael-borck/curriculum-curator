import React, { useState, useEffect } from 'react';
import { useUserProfile, useContentDefaults } from '../contexts/SettingsContext';
import { useLLM } from '../hooks/useLLM';
import { useExport } from '../hooks/useExport';
import { useFileOperations } from '../hooks/useFileOperations';
import { useWorkflow } from '../hooks/useWorkflow';
import { useBatchGeneration } from '../hooks/useBatchGeneration';
import { generationManager } from '../utils/generationManager';
import { useStatusFeedback } from './StatusFeedback';
import { useDesktopLayout } from '../utils/desktopLayout';
import type { ContentType, QuizType, AIContentOptions, GenerationConfig } from '../types/settings';

interface ExpertModeProps {
  onModeSwitch: (mode: 'wizard' | 'expert') => void;
}

export function ExpertMode({ onModeSwitch }: ExpertModeProps) {
  const [profile] = useUserProfile();
  const [defaults] = useContentDefaults();
  const llm = useLLM();
  const exportHook = useExport();
  const fileOps = useFileOperations();
  const workflow = useWorkflow();
  const batchGeneration = useBatchGeneration();
  const statusFeedback = useStatusFeedback();
  const layout = useDesktopLayout();
  const [activeTab, setActiveTab] = useState<'planner' | 'workflow' | 'batch' | 'quality'>('planner');
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedExportFormat, setSelectedExportFormat] = useState('Markdown');
  const [selectedTemplate, setSelectedTemplate] = useState('default');
  const [batchFormData, setBatchFormData] = useState({
    courseName: '',
    numberOfLessons: 5,
    selectedContentTypes: [] as ContentType[],
    lessons: [] as Array<{
      topic: string;
      learningObjectives: string[];
      duration: string;
      audience: string;
    }>,
  });
  
  const [formData, setFormData] = useState({
    topic: defaults?.topic || '',
    learningObjectives: [''],
    duration: defaults?.duration || '50 minutes',
    audience: '',
    subject: profile?.subject || '',
    complexity: defaults?.complexity || 'intermediate',
    contentTypes: [...(defaults?.contentTypes || [])] as ContentType[],
    quizTypes: [...(defaults?.quizTypes || [])] as QuizType[],
    includeAnswerKeys: defaults?.includeAnswerKeys ?? true,
    includeInstructorGuides: defaults?.includeInstructorGuides ?? true,
    accessibility: defaults?.includeAccessibilityFeatures ?? false,
    rubrics: defaults?.includeRubrics ?? false,
    extensions: false,
    aiEnhancements: {} as Record<ContentType, AIContentOptions>,
    customPrompts: {},
    batchGeneration: false,
  });

  // Load export formats on component mount
  useEffect(() => {
    fileOps.getSupportedFormats().then(formats => {
      if (formats.length > 0) {
        setSelectedExportFormat(formats[0]);
      }
    });
  }, [fileOps]);

  const handleInputChange = (field: string, value: string | boolean | string[] | Record<string, unknown>) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const addLearningObjective = () => {
    setFormData(prev => ({
      ...prev,
      learningObjectives: [...prev.learningObjectives, ''],
    }));
  };

  const updateLearningObjective = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      learningObjectives: prev.learningObjectives.map((obj, i) => i === index ? value : obj),
    }));
  };

  const removeLearningObjective = (index: number) => {
    if (formData.learningObjectives.length > 1) {
      setFormData(prev => ({
        ...prev,
        learningObjectives: prev.learningObjectives.filter((_, i) => i !== index),
      }));
    }
  };

  const toggleContentType = (contentType: ContentType) => {
    setFormData(prev => ({
      ...prev,
      contentTypes: prev.contentTypes.includes(contentType)
        ? prev.contentTypes.filter(t => t !== contentType)
        : [...prev.contentTypes, contentType],
    }));
  };

  const toggleQuizType = (quizType: QuizType) => {
    setFormData(prev => ({
      ...prev,
      quizTypes: prev.quizTypes.includes(quizType)
        ? prev.quizTypes.filter(t => t !== quizType)
        : [...prev.quizTypes, quizType],
    }));
  };

  const generateSelectedContent = async (selectedTypes?: ContentType[]) => {
    // Check if LLM provider is available
    if (!llm.hasAvailableProvider) {
      statusFeedback.showWarning(
        'LLM Provider Required',
        'Please configure an LLM provider in settings to generate content.',
        5000
      );
      return;
    }

    const typesToGenerate = selectedTypes || formData.contentTypes;
    if (typesToGenerate.length === 0) {
      statusFeedback.showWarning(
        'No Content Selected',
        'Please select at least one content type to generate.',
        3000
      );
      return;
    }

    const config: GenerationConfig = {
      topic: formData.topic,
      audience: formData.audience,
      subject: formData.subject,
      duration: formData.duration,
      complexity: formData.complexity,
      learningObjectives: formData.learningObjectives.filter(obj => obj.trim()),
      contentTypes: typesToGenerate,
      quizTypes: formData.quizTypes,
      additionalOptions: {
        includeAnswerKeys: formData.includeAnswerKeys,
        includeInstructorGuides: formData.includeInstructorGuides,
        accessibility: formData.accessibility,
        rubrics: formData.rubrics,
        extensions: formData.extensions,
      },
    };

    try {
      statusFeedback.showInfo(
        'Generation Started',
        `Generating ${typesToGenerate.length} content type${typesToGenerate.length > 1 ? 's' : ''}...`
      );

      await generationManager.startGeneration(
        config,
        (progress) => {
          // Progress tracking handled by generation manager
        },
        (error) => {
          statusFeedback.showError(
            'Generation Error',
            `Error in ${error.stepId}: ${error.message}`,
            6000
          );
        }
      );

      statusFeedback.showSuccess(
        'Content Generated',
        `Successfully generated content for ${typesToGenerate.join(', ')}.`,
        4000
      );
    } catch (error) {
      statusFeedback.showError(
        'Generation Failed',
        error instanceof Error ? error.message : 'An unexpected error occurred.',
        6000
      );
    }
  };

  const handleExport = async (format?: string, template?: string) => {
    // For now, we'll use a mock session ID - in a real implementation,
    // this would come from the current active session
    const mockSessionId = "mock-session-id";
    const exportFormat = format || selectedExportFormat;
    const templateName = template || selectedTemplate;
    
    try {
      const result = await fileOps.exportContent(mockSessionId, {
        format: exportFormat,
        include_metadata: true,
        template_name: templateName !== 'default' ? templateName : undefined,
      });

      if (result.success) {
        statusFeedback.showSuccess(
          'Export Complete',
          `Content exported to ${result.output_path}`,
          5000
        );
      } else {
        throw new Error(result.error || 'Export failed');
      }
    } catch (error) {
      statusFeedback.showError(
        'Export Failed',
        error instanceof Error ? error.message : 'An unexpected error occurred.',
        6000
      );
    }
  };

  const handleSaveSession = async () => {
    const mockSessionId = "mock-session-id";
    
    try {
      const result = await fileOps.saveSession(mockSessionId, {
        include_content: true,
        include_metadata: true
      });

      if (result.success) {
        statusFeedback.showSuccess(
          'Session Saved',
          `Session saved to ${result.output_path}`,
          4000
        );
      } else {
        throw new Error(result.error || 'Save failed');
      }
    } catch (error) {
      statusFeedback.showError(
        'Save Failed',
        error instanceof Error ? error.message : 'An unexpected error occurred.',
        6000
      );
    }
  };

  const handleLoadSession = async () => {
    try {
      const result = await fileOps.loadSession();

      if (result.success) {
        statusFeedback.showSuccess(
          'Session Loaded',
          `Loaded session ${result.sessionId}`,
          3000
        );
        // TODO: Update form data with loaded session
      } else {
        throw new Error(result.error || 'Load failed');
      }
    } catch (error) {
      statusFeedback.showError(
        'Load Failed',
        error instanceof Error ? error.message : 'An unexpected error occurred.',
        6000
      );
    }
  };

  const getStepDescription = (stepName: string): string => {
    switch (stepName) {
      case 'Content Planning':
        return 'Generate learning objectives and content outline';
      case 'Material Generation':
        return 'Create slides, worksheets, and instructor materials';
      case 'Assessment Creation':
        return 'Build quizzes, rubrics, and answer keys';
      case 'Quality Review':
        return 'Validate content alignment and quality standards';
      default:
        return '';
    }
  };

  const handleBatchFormChange = (field: string, value: any) => {
    setBatchFormData(prev => ({ ...prev, [field]: value }));
  };

  const generateBatchLessons = () => {
    const lessons = [];
    for (let i = 0; i < batchFormData.numberOfLessons; i++) {
      lessons.push({
        topic: `${batchFormData.courseName} - Lesson ${i + 1}`,
        learningObjectives: [''],
        duration: '50 minutes',
        audience: formData.audience || 'Students',
      });
    }
    setBatchFormData(prev => ({ ...prev, lessons }));
  };

  const updateBatchLesson = (index: number, field: string, value: string | string[]) => {
    setBatchFormData(prev => ({
      ...prev,
      lessons: prev.lessons.map((lesson, i) => 
        i === index ? { ...lesson, [field]: value } : lesson
      ),
    }));
  };

  const startBatchGeneration = async () => {
    if (!llm.hasAvailableProvider) {
      statusFeedback.showWarning(
        'LLM Provider Required',
        'Please configure an LLM provider in settings to generate content.',
        5000
      );
      return;
    }

    if (batchFormData.lessons.length === 0) {
      statusFeedback.showWarning(
        'No Lessons Configured',
        'Please configure lessons before starting batch generation.',
        3000
      );
      return;
    }

    if (batchFormData.selectedContentTypes.length === 0) {
      statusFeedback.showWarning(
        'No Content Types Selected',
        'Please select at least one content type for batch generation.',
        3000
      );
      return;
    }

    try {
      statusFeedback.showInfo(
        'Starting Batch Generation',
        `Generating content for ${batchFormData.lessons.length} lessons...`
      );

      const batchId = await batchGeneration.createBatch(
        batchFormData.courseName || 'Unnamed Course',
        batchFormData.lessons.map(lesson => ({
          topic: lesson.topic,
          learningObjectives: lesson.learningObjectives.filter(obj => obj.trim()),
          duration: lesson.duration,
          audience: lesson.audience,
          contentTypes: batchFormData.selectedContentTypes,
          priority: 'normal' as const,
        })),
        {
          parallelGeneration: true,
          maxParallelJobs: 3,
          continueOnError: true,
          savePartialResults: true,
          retryFailedItems: true,
          maxRetries: 2,
        }
      );

      const result = await batchGeneration.executeBatch(
        batchId,
        batchFormData.courseName || 'Unnamed Course',
        batchFormData.lessons.map(lesson => ({
          topic: lesson.topic,
          learningObjectives: lesson.learningObjectives.filter(obj => obj.trim()),
          duration: lesson.duration,
          audience: lesson.audience,
          contentTypes: batchFormData.selectedContentTypes,
          priority: 'normal' as const,
        }))
      );

      statusFeedback.showSuccess(
        'Batch Generation Complete',
        `Generated content for ${result.successfulItems}/${result.totalItems} lessons.`,
        5000
      );
    } catch (error) {
      statusFeedback.showError(
        'Batch Generation Failed',
        error instanceof Error ? error.message : 'An unexpected error occurred.',
        6000
      );
    }
  };

  const toggleBatchContentType = (contentType: ContentType) => {
    setBatchFormData(prev => ({
      ...prev,
      selectedContentTypes: prev.selectedContentTypes.includes(contentType)
        ? prev.selectedContentTypes.filter(t => t !== contentType)
        : [...prev.selectedContentTypes, contentType],
    }));
  };

  const getStepOptions = (stepName: string): React.ReactNode => {
    switch (stepName) {
      case 'Content Planning':
        return (
          <>
            <label><input type="checkbox" defaultChecked /> Use AI suggestions</label>
            <label><input type="checkbox" /> Include assessment mapping</label>
          </>
        );
      case 'Material Generation':
        return (
          <>
            <label><input type="checkbox" defaultChecked /> Generate slides first</label>
            <label><input type="checkbox" /> Parallel generation</label>
          </>
        );
      case 'Assessment Creation':
        return (
          <>
            <label><input type="checkbox" /> Include difficulty progression</label>
            <label><input type="checkbox" defaultChecked /> Auto-generate explanations</label>
          </>
        );
      case 'Quality Review':
        return (
          <>
            <label><input type="checkbox" defaultChecked /> Objective alignment check</label>
            <label><input type="checkbox" /> Readability analysis</label>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ 
      maxWidth: `${layout.contentMaxWidth}px`, 
      margin: '0 auto',
      fontSize: `${layout.fontSize.base}px`
    }}>
      {/* Expert Mode Header */}
      <div style={{
        backgroundColor: 'white',
        padding: `${layout.spacing.lg}px`,
        borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        marginBottom: `${layout.spacing.lg}px`
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h1 style={{ margin: 0, fontSize: '24px', color: '#1e293b', fontWeight: '600' }}>
            🎯 Expert Mode
          </h1>
          <button
            onClick={() => onModeSwitch('wizard')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f1f5f9',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              color: '#475569'
            }}
          >
            ← Switch to Wizard
          </button>
        </div>
        <p style={{ margin: 0, color: '#64748b', fontSize: '16px' }}>
          Direct workflow control for power users. Generate specific content types, skip steps, or batch create materials.
        </p>

        {/* Mode Tabs */}
        <div style={{ 
          display: 'flex', 
          gap: '8px', 
          backgroundColor: '#f1f5f9', 
          padding: '4px', 
          borderRadius: '8px',
          marginTop: '20px'
        }}>
          {[
            { id: 'planner', label: '📋 Content Planner', desc: 'Quick content generation' },
            { id: 'workflow', label: '⚡ Workflow Control', desc: 'Direct step control' },
            { id: 'batch', label: '🚀 Batch Generator', desc: 'Multiple lessons' },
            { id: 'quality', label: '✨ Quality Control', desc: 'Validation settings' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              style={{
                flex: 1,
                padding: '12px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: activeTab === tab.id ? 'white' : 'transparent',
                color: activeTab === tab.id ? '#3b82f6' : '#64748b',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                textAlign: 'center'
              }}
              title={tab.desc}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="expert-content">
        {activeTab === 'planner' && (
          <div className="planner-tab">
            <div className="planner-grid">
              <div className="planner-section">
                <h2>Course Information</h2>
                <div className="form-group">
                  <label htmlFor="expert-topic">Topic/Subject</label>
                  <input
                    id="expert-topic"
                    type="text"
                    value={formData.topic}
                    onChange={(e) => handleInputChange('topic', e.target.value)}
                    placeholder="Enter the lesson topic"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="expert-audience">Target Audience</label>
                  <input
                    id="expert-audience"
                    type="text"
                    value={formData.audience}
                    onChange={(e) => handleInputChange('audience', e.target.value)}
                    placeholder="Describe your students"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="expert-duration">Session Duration</label>
                  <select
                    id="expert-duration"
                    value={formData.duration}
                    onChange={(e) => handleInputChange('duration', e.target.value)}
                    className="form-select"
                  >
                    <option value="30 minutes">30 minutes</option>
                    <option value="50 minutes">50 minutes</option>
                    <option value="75 minutes">75 minutes</option>
                    <option value="90 minutes">90 minutes</option>
                    <option value="2 hours">2 hours</option>
                    <option value="3 hours">3 hours</option>
                    <option value="Custom">Custom duration</option>
                  </select>
                </div>
              </div>

              <div className="planner-section">
                <h2>Learning Objectives</h2>
                <div className="objectives-editor">
                  {formData.learningObjectives.map((objective, index) => (
                    <div key={index} className="objective-row">
                      <input
                        type="text"
                        value={objective}
                        onChange={(e) => updateLearningObjective(index, e.target.value)}
                        placeholder={`Learning objective ${index + 1}`}
                        className="form-input"
                      />
                      <div className="objective-controls">
                        {formData.learningObjectives.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeLearningObjective(index)}
                            className="btn-icon danger"
                            title="Remove objective"
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addLearningObjective}
                    className="add-btn"
                  >
                    + Add Objective
                  </button>
                </div>
              </div>

              <div className="planner-section full-width">
                <h2>Content Types</h2>
                <div className="content-selection">
                  {(['Slides', 'InstructorNotes', 'Worksheet', 'Quiz', 'ActivityGuide'] as ContentType[]).map((type) => (
                    <div
                      key={type}
                      className={`content-card ${formData.contentTypes.includes(type) ? 'selected' : ''}`}
                      onClick={() => toggleContentType(type)}
                    >
                      <div className="content-header">
                        <input
                          type="checkbox"
                          checked={formData.contentTypes.includes(type)}
                          onChange={() => toggleContentType(type)}
                        />
                        <h3>{type.replace(/([A-Z])/g, ' $1').trim()}</h3>
                      </div>
                      <div className="content-options">
                        <label>
                          <input type="checkbox" /> Advanced formatting
                        </label>
                        <label>
                          <input type="checkbox" /> Include media placeholders
                        </label>
                        <label>
                          <input type="checkbox" /> Auto-generate assessment
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="planner-actions">
              <div style={{ display: 'flex', gap: '12px' }}>
                <button 
                  className="btn secondary"
                  onClick={handleSaveSession}
                  disabled={fileOps.isOperating}
                >
                  {fileOps.isOperating && fileOps.lastOperation === 'save' ? '💾 Saving...' : '💾 Save Session'}
                </button>
                <button 
                  className="btn secondary"
                  onClick={handleLoadSession}
                  disabled={fileOps.isOperating}
                >
                  {fileOps.isOperating && fileOps.lastOperation === 'load' ? '📁 Loading...' : '📁 Load Session'}
                </button>
                <div style={{ position: 'relative' }}>
                  <button 
                    className="btn secondary"
                    onClick={() => setShowExportModal(!showExportModal)}
                    disabled={fileOps.isOperating}
                    title="Export content in various formats"
                  >
                    {fileOps.isOperating && fileOps.lastOperation === 'export' ? '📤 Exporting...' : '📤 Export ▼'}
                  </button>
                  {showExportModal && (
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      background: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                      padding: '16px',
                      minWidth: '280px',
                      zIndex: 1000
                    }}>
                      <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600' }}>Export Options</h4>
                      
                      <div style={{ marginBottom: '12px' }}>
                        <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>Format:</label>
                        <select 
                          value={selectedExportFormat}
                          onChange={(e) => setSelectedExportFormat(e.target.value)}
                          style={{ width: '100%', padding: '6px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                        >
                          {['Markdown', 'HTML', 'PDF', 'PowerPoint', 'Word'].map(format => (
                            <option key={format} value={format}>
                              {format}
                            </option>
                          ))}
                        </select>
                      </div>

                      {selectedExportFormat === 'Html' && (
                        <div style={{ marginBottom: '12px' }}>
                          <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>Template:</label>
                          <select 
                            value={selectedTemplate}
                            onChange={(e) => setSelectedTemplate(e.target.value)}
                            style={{ width: '100%', padding: '6px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                          >
                            <option value="default">Default</option>
                            <option value="professional">Professional</option>
                            <option value="academic">Academic</option>
                            <option value="minimal">Minimal</option>
                            <option value="presentation">Presentation</option>
                          </select>
                        </div>
                      )}

                      <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                        <button 
                          className="btn primary"
                          onClick={() => {
                            handleExport();
                            setShowExportModal(false);
                          }}
                          disabled={fileOps.isOperating}
                          style={{ flex: 1, fontSize: '12px' }}
                        >
                          Export
                        </button>
                        <button 
                          className="btn secondary"
                          onClick={() => setShowExportModal(false)}
                          style={{ fontSize: '12px' }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <button 
                className="btn primary"
                onClick={() => generateSelectedContent()}
                disabled={!formData.topic || formData.contentTypes.length === 0}
              >
                Generate Content
              </button>
            </div>
          </div>
        )}

        {activeTab === 'workflow' && (
          <div className="workflow-tab">
            <div className="workflow-header">
              <h2>Workflow Control</h2>
              <p>Execute specific generation steps or skip phases</p>
            </div>

            <div className="workflow-content">
              <div className="workflow-steps">
                <h3>Generation Pipeline</h3>
                {workflow.state.error && (
                  <div className="error-message">{workflow.state.error}</div>
                )}
                <div className="step-list">
                  {workflow.state.steps.map((step, index) => (
                    <div key={index} className={`step-item ${step.status}`}>
                      <div className="step-header">
                        <span className="step-number">{index + 1}</span>
                        <h4>{step.name}</h4>
                        {step.status === 'pending' && (
                          <button 
                            className="btn-small primary"
                            onClick={async () => {
                              if (!workflow.state.workflowId) {
                                const contentRequest = {
                                  topic: formData.topic,
                                  learningObjectives: formData.learningObjectives.filter(obj => obj.trim()),
                                  duration: formData.duration,
                                  audience: formData.audience,
                                  contentTypes: formData.contentTypes,
                                };
                                await workflow.createWorkflow(contentRequest);
                              }
                              await workflow.executeStep(index);
                            }}
                            disabled={workflow.state.isRunning}
                          >
                            Run Step
                          </button>
                        )}
                        {step.status === 'running' && (
                          <span className="status-badge">Running...</span>
                        )}
                        {step.status === 'completed' && (
                          <span className="status-badge success">✓ Complete</span>
                        )}
                        {step.status === 'failed' && (
                          <span className="status-badge error">✗ Failed</span>
                        )}
                        {step.status === 'pending' && index < 3 && (
                          <button 
                            className="btn-small secondary"
                            onClick={() => workflow.skipStep(index)}
                          >
                            Skip
                          </button>
                        )}
                      </div>
                      <p>{getStepDescription(step.name)}</p>
                      {step.error && (
                        <div className="step-error">{step.error}</div>
                      )}
                      <div className="step-options">
                        {getStepOptions(step.name)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="workflow-controls">
                <h3>Quick Actions</h3>
                <div className="action-grid">
                  <button 
                    className="action-btn"
                    onClick={async () => {
                      const result = await workflow.executeQuickAction('slides_only', {
                        topic: formData.topic,
                        learningObjectives: formData.learningObjectives.filter(obj => obj.trim()),
                        duration: formData.duration,
                        audience: formData.audience,
                        contentTypes: ['Slides'],
                      });
                      statusFeedback.showSuccess('Slides generated successfully!');
                    }}
                    disabled={workflow.state.isRunning}
                  >
                    <span className="action-icon">⚡</span>
                    <span>Generate Slides Only</span>
                  </button>
                  <button 
                    className="action-btn"
                    onClick={async () => {
                      const result = await workflow.executeQuickAction('assessment_suite', {
                        topic: formData.topic,
                        learningObjectives: formData.learningObjectives.filter(obj => obj.trim()),
                        duration: formData.duration,
                        audience: formData.audience,
                        contentTypes: ['Quiz', 'ActivityGuide'],
                      });
                      statusFeedback.showSuccess('Assessment suite created!');
                    }}
                    disabled={workflow.state.isRunning}
                  >
                    <span className="action-icon">📝</span>
                    <span>Create Assessment Suite</span>
                  </button>
                  <button 
                    className="action-btn"
                    onClick={async () => {
                      const result = await workflow.executeQuickAction('learning_objectives', {
                        topic: formData.topic,
                        learningObjectives: [],
                        duration: formData.duration,
                        audience: formData.audience,
                        contentTypes: [],
                      });
                      statusFeedback.showSuccess('Learning objectives generated!');
                    }}
                    disabled={workflow.state.isRunning}
                  >
                    <span className="action-icon">🎯</span>
                    <span>Learning Objectives Only</span>
                  </button>
                  <button 
                    className="action-btn"
                    onClick={async () => {
                      const result = await workflow.executeQuickAction('complete_package', {
                        topic: formData.topic,
                        learningObjectives: formData.learningObjectives.filter(obj => obj.trim()),
                        duration: formData.duration,
                        audience: formData.audience,
                        contentTypes: formData.contentTypes,
                      });
                      statusFeedback.showSuccess('Complete lesson package generated!');
                    }}
                    disabled={workflow.state.isRunning}
                  >
                    <span className="action-icon">📚</span>
                    <span>Complete Lesson Package</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'batch' && (
          <div className="batch-tab">
            <div className="batch-header">
              <h2>Batch Content Generator</h2>
              <p>Generate content for multiple lessons at once</p>
            </div>

            {batchGeneration.state.isRunning && (
              <div style={{
                backgroundColor: '#eff6ff',
                border: '1px solid #3b82f6',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '20px',
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#1e40af' }}>Batch Generation in Progress</h4>
                <p style={{ margin: '0', color: '#3730a3' }}>
                  Generating content for {batchFormData.lessons.length} lessons...
                </p>
                {batchGeneration.state.progress && (
                  <div style={{ marginTop: '12px' }}>
                    <div style={{
                      backgroundColor: '#dbeafe',
                      borderRadius: '4px',
                      height: '8px',
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        backgroundColor: '#3b82f6',
                        height: '100%',
                        width: `${batchGeneration.state.progress.progressPercent}%`,
                        transition: 'width 0.3s ease',
                      }} />
                    </div>
                    <p style={{ fontSize: '12px', margin: '4px 0 0 0', color: '#6b7280' }}>
                      {batchGeneration.state.progress.completedItems}/{batchGeneration.state.progress.totalItems} completed
                    </p>
                  </div>
                )}
              </div>
            )}

            <div className="batch-content">
              <div className="batch-setup">
                <h3>Batch Configuration</h3>
                <div className="form-group">
                  <label>Course Name</label>
                  <input 
                    type="text" 
                    placeholder="e.g., Introduction to Psychology" 
                    className="form-input"
                    value={batchFormData.courseName}
                    onChange={(e) => handleBatchFormChange('courseName', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Number of Lessons</label>
                  <input 
                    type="number" 
                    placeholder="12" 
                    min="1" 
                    max="50" 
                    className="form-input"
                    value={batchFormData.numberOfLessons}
                    onChange={(e) => handleBatchFormChange('numberOfLessons', parseInt(e.target.value) || 1)}
                  />
                </div>
                <div className="form-group">
                  <label>Content Types (for all lessons)</label>
                  <div className="checkbox-group">
                    {(['Slides', 'InstructorNotes', 'Worksheet', 'Quiz'] as ContentType[]).map((type) => (
                      <label key={type}>
                        <input 
                          type="checkbox" 
                          checked={batchFormData.selectedContentTypes.includes(type)}
                          onChange={() => toggleBatchContentType(type)}
                        />
                        {type.replace(/([A-Z])/g, ' $1').trim()}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <button 
                    type="button" 
                    className="btn secondary"
                    onClick={generateBatchLessons}
                    disabled={!batchFormData.courseName || batchFormData.numberOfLessons < 1}
                  >
                    Generate Lesson Structure
                  </button>
                </div>
              </div>

              <div className="batch-preview">
                <h3>Lesson Preview ({batchFormData.lessons.length} lessons)</h3>
                {batchFormData.lessons.length > 0 ? (
                  <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    {batchFormData.lessons.map((lesson, index) => (
                      <div key={index} style={{
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        padding: '12px',
                        marginBottom: '8px',
                        backgroundColor: '#fafafa',
                      }}>
                        <div className="form-group" style={{ marginBottom: '8px' }}>
                          <label style={{ fontSize: '12px', fontWeight: '500' }}>Lesson {index + 1} Topic:</label>
                          <input
                            type="text"
                            value={lesson.topic}
                            onChange={(e) => updateBatchLesson(index, 'topic', e.target.value)}
                            className="form-input"
                            style={{ fontSize: '14px', padding: '6px 8px' }}
                          />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                          <div className="form-group">
                            <label style={{ fontSize: '12px', fontWeight: '500' }}>Duration:</label>
                            <select
                              value={lesson.duration}
                              onChange={(e) => updateBatchLesson(index, 'duration', e.target.value)}
                              className="form-select"
                              style={{ fontSize: '14px', padding: '6px 8px' }}
                            >
                              <option value="30 minutes">30 minutes</option>
                              <option value="50 minutes">50 minutes</option>
                              <option value="75 minutes">75 minutes</option>
                              <option value="90 minutes">90 minutes</option>
                            </select>
                          </div>
                          <div className="form-group">
                            <label style={{ fontSize: '12px', fontWeight: '500' }}>Audience:</label>
                            <input
                              type="text"
                              value={lesson.audience}
                              onChange={(e) => updateBatchLesson(index, 'audience', e.target.value)}
                              className="form-input"
                              style={{ fontSize: '14px', padding: '6px 8px' }}
                              placeholder="e.g., High school students"
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="batch-placeholder">
                    <p>Configure your batch settings and click "Generate Lesson Structure" to see a preview</p>
                  </div>
                )}
              </div>
            </div>

            <div className="batch-actions">
              <button className="btn secondary" disabled>Import CSV (Coming Soon)</button>
              <button className="btn secondary" disabled>Save Configuration (Coming Soon)</button>
              <button 
                className="btn primary"
                onClick={startBatchGeneration}
                disabled={
                  batchGeneration.state.isRunning || 
                  batchFormData.lessons.length === 0 ||
                  batchFormData.selectedContentTypes.length === 0 ||
                  !llm.hasAvailableProvider
                }
              >
                {batchGeneration.state.isRunning ? 'Generating...' : 'Start Batch Generation'}
              </button>
            </div>

            {batchGeneration.state.result && (
              <div style={{
                backgroundColor: '#f0fdf4',
                border: '1px solid #16a34a',
                borderRadius: '8px',
                padding: '16px',
                marginTop: '20px',
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#15803d' }}>Batch Generation Complete</h4>
                <p style={{ margin: '0', color: '#166534' }}>
                  Successfully generated content for {batchGeneration.state.result.successfulItems} out of {batchGeneration.state.result.totalItems} lessons
                  ({Math.round((batchGeneration.state.result.totalElapsedTime / 1000) * 100) / 100}s total time)
                </p>
                {batchGeneration.state.result.failedItems > 0 && (
                  <p style={{ margin: '8px 0 0 0', color: '#dc2626' }}>
                    {batchGeneration.state.result.failedItems} lesson(s) failed to generate
                  </p>
                )}
              </div>
            )}

            {batchGeneration.state.error && (
              <div style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #dc2626',
                borderRadius: '8px',
                padding: '16px',
                marginTop: '20px',
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#dc2626' }}>Batch Generation Error</h4>
                <p style={{ margin: '0', color: '#991b1b' }}>{batchGeneration.state.error}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'quality' && (
          <div className="quality-tab">
            <div className="quality-header">
              <h2>Quality Control</h2>
              <p>Configure validation rules and quality standards</p>
            </div>

            <div className="quality-content">
              <div className="quality-section">
                <h3>Content Validation</h3>
                <div className="validation-rules">
                  <label className="rule-item">
                    <input type="checkbox" defaultChecked />
                    <div className="rule-info">
                      <strong>Readability Check</strong>
                      <p>Ensure content matches target reading level</p>
                    </div>
                  </label>
                  <label className="rule-item">
                    <input type="checkbox" defaultChecked />
                    <div className="rule-info">
                      <strong>Learning Objective Alignment</strong>
                      <p>Verify content supports stated objectives</p>
                    </div>
                  </label>
                  <label className="rule-item">
                    <input type="checkbox" />
                    <div className="rule-info">
                      <strong>Accessibility Standards</strong>
                      <p>Check for accessibility compliance</p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="quality-section">
                <h3>Generation Settings</h3>
                <div className="form-group">
                  <label>Content Complexity</label>
                  <select className="form-select">
                    <option>Beginner</option>
                    <option>Intermediate</option>
                    <option>Advanced</option>
                    <option>Mixed</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Quality Threshold</label>
                  <input type="range" min="1" max="10" defaultValue="7" />
                  <span>7/10</span>
                </div>
              </div>

              <div className="quality-section">
                <h3>Review Process</h3>
                <div className="checkbox-group">
                  <label>
                    <input type="checkbox" defaultChecked />
                    <span>Require manual review before export</span>
                  </label>
                  <label>
                    <input type="checkbox" />
                    <span>Auto-fix common issues</span>
                  </label>
                  <label>
                    <input type="checkbox" />
                    <span>Generate quality report</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}