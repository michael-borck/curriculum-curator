import React, { useState } from 'react';
import { useUserProfile, useContentDefaults } from '../contexts/SettingsContext';
import { useLLM } from '../hooks/useLLM';
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
  const statusFeedback = useStatusFeedback();
  const layout = useDesktopLayout();
  const [activeTab, setActiveTab] = useState<'planner' | 'workflow' | 'batch' | 'quality'>('planner');
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
              <button className="btn secondary">Save Draft</button>
              <button className="btn secondary">Load Template</button>
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
                <div className="step-list">
                  <div className="step-item">
                    <div className="step-header">
                      <span className="step-number">1</span>
                      <h4>Content Planning</h4>
                      <button className="btn-small primary">Run Step</button>
                    </div>
                    <p>Generate learning objectives and content outline</p>
                    <div className="step-options">
                      <label><input type="checkbox" defaultChecked /> Use AI suggestions</label>
                      <label><input type="checkbox" /> Include assessment mapping</label>
                    </div>
                  </div>

                  <div className="step-item">
                    <div className="step-header">
                      <span className="step-number">2</span>
                      <h4>Material Generation</h4>
                      <button className="btn-small secondary">Skip</button>
                    </div>
                    <p>Create slides, worksheets, and instructor materials</p>
                    <div className="step-options">
                      <label><input type="checkbox" defaultChecked /> Generate slides first</label>
                      <label><input type="checkbox" /> Parallel generation</label>
                    </div>
                  </div>

                  <div className="step-item">
                    <div className="step-header">
                      <span className="step-number">3</span>
                      <h4>Assessment Creation</h4>
                      <button className="btn-small primary">Run Step</button>
                    </div>
                    <p>Build quizzes, rubrics, and answer keys</p>
                    <div className="step-options">
                      <label><input type="checkbox" /> Include difficulty progression</label>
                      <label><input type="checkbox" defaultChecked /> Auto-generate explanations</label>
                    </div>
                  </div>

                  <div className="step-item">
                    <div className="step-header">
                      <span className="step-number">4</span>
                      <h4>Quality Review</h4>
                      <button className="btn-small secondary">Auto</button>
                    </div>
                    <p>Validate content alignment and quality standards</p>
                    <div className="step-options">
                      <label><input type="checkbox" defaultChecked /> Objective alignment check</label>
                      <label><input type="checkbox" /> Readability analysis</label>
                    </div>
                  </div>
                </div>
              </div>

              <div className="workflow-controls">
                <h3>Quick Actions</h3>
                <div className="action-grid">
                  <button className="action-btn">
                    <span className="action-icon">⚡</span>
                    <span>Generate Slides Only</span>
                  </button>
                  <button className="action-btn">
                    <span className="action-icon">📝</span>
                    <span>Create Assessment Suite</span>
                  </button>
                  <button className="action-btn">
                    <span className="action-icon">🎯</span>
                    <span>Learning Objectives Only</span>
                  </button>
                  <button className="action-btn">
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

            <div className="batch-content">
              <div className="batch-setup">
                <h3>Batch Configuration</h3>
                <div className="form-group">
                  <label>Course Name</label>
                  <input type="text" placeholder="e.g., Introduction to Psychology" className="form-input" />
                </div>
                <div className="form-group">
                  <label>Number of Lessons</label>
                  <input type="number" placeholder="12" min="1" max="50" className="form-input" />
                </div>
                <div className="form-group">
                  <label>Content Types (for all lessons)</label>
                  <div className="checkbox-group">
                    <label><input type="checkbox" /> Slides</label>
                    <label><input type="checkbox" /> Instructor Notes</label>
                    <label><input type="checkbox" /> Worksheets</label>
                    <label><input type="checkbox" /> Quizzes</label>
                  </div>
                </div>
              </div>

              <div className="batch-preview">
                <h3>Batch Preview</h3>
                <div className="batch-placeholder">
                  <p>Configure your batch settings to see a preview</p>
                </div>
              </div>
            </div>

            <div className="batch-actions">
              <button className="btn secondary">Import CSV</button>
              <button className="btn secondary">Save Configuration</button>
              <button className="btn primary">Start Batch Generation</button>
            </div>
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