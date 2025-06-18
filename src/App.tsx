import React, { useState, useEffect } from 'react';
import { useSettings, useUserProfile, useContentDefaults, useUIPreferences } from './contexts/SettingsContext';
import { SettingsPanel } from './components/SettingsPanel';
import { ContentAIEnhancements } from './components/ContentAIEnhancements';
import { CustomContentTypeManager } from './components/CustomContentTypeManager';
import { ExpertMode } from './components/ExpertMode';
import { LiveContentPreview } from './components/LiveContentPreview';
import { ProgressIndicator } from './components/ProgressIndicator';
import { StatusFeedback, useStatusFeedback } from './components/StatusFeedback';
import { LLMProviderSetup } from './components/LLMProviderSetup';
import { FileOperations } from './components/FileOperations';
import { SessionBrowser } from './components/SessionBrowser';
import { SessionHistory } from './components/SessionHistory';
import { BackupRecovery } from './components/BackupRecovery';
import { ImportWizard } from './components/ImportWizard';
import { GitIntegration } from './components/GitIntegration';
import { DataExportWizard } from './components/DataExportWizard';
import { useLLM } from './hooks/useLLM';
import { crossSessionLearning } from './utils/crossSessionLearning';
import { generationManager } from './utils/generationManager';
import type { GenerationProgress, GenerationConfig } from './utils/generationManager';
import { useDesktopLayout, shouldShowPreviewByDefault, getOptimalWizardLayout } from './utils/desktopLayout';
import type { QuizType, ContentType, AIContentOptions, CustomContentType } from './types/settings';
import './App.css';

type AppMode = 'wizard' | 'expert';

function App() {
  const [profile] = useUserProfile();
  const [defaults] = useContentDefaults();
  const [preferences] = useUIPreferences();
  const statusFeedback = useStatusFeedback();
  const layout = useDesktopLayout();
  const llm = useLLM();
  const [showSettings, setShowSettings] = useState(false);
  const [currentMode, setCurrentMode] = useState<AppMode>('wizard');
  const [currentStep, setCurrentStep] = useState(1);
  const [usingDefaults, setUsingDefaults] = useState(false);
  const [formData, setFormData] = useState({
    topic: '',
    audience: '',
    duration: '50 minutes',
    learningObjectives: [''],
    contentTypes: [] as ContentType[],
    quizTypes: [] as QuizType[],
    complexity: 'intermediate',
    style: 'interactive',
    accessibility: false,
    rubrics: false,
    extensions: false,
    includeAnswerKeys: true,
    includeInstructorGuides: true,
    answerKeyOptions: {
      includeExplanations: true,
      includeDifficulty: true,
      includePoints: false
    },
    instructorGuideOptions: {
      includeTiming: true,
      includeGradingTips: true,
      includeDiscussionPrompts: false,
      includeExtensions: false
    },
    aiEnhancements: {} as Record<ContentType, AIContentOptions>
  });
  const [aiGenerating, setAiGenerating] = useState(false);
  const [showObjectiveCountModal, setShowObjectiveCountModal] = useState(false);
  const [objectiveCount, setObjectiveCount] = useState(4);
  const [showCustomContentManager, setShowCustomContentManager] = useState(false);
  const [customContentTypes, setCustomContentTypes] = useState<CustomContentType[]>([]);
  const [showPreview, setShowPreview] = useState(() => shouldShowPreviewByDefault(window.innerWidth));
  const [previewWidth, setPreviewWidth] = useState(() => layout.previewPanelWidth);
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress | null>(null);
  const [showProgress, setShowProgress] = useState(false);
  const [showLLMSetup, setShowLLMSetup] = useState(false);
  const [showFileOperations, setShowFileOperations] = useState(false);
  const [showSessionBrowser, setShowSessionBrowser] = useState(false);
  const [showSessionHistory, setShowSessionHistory] = useState(false);
  const [showBackupRecovery, setShowBackupRecovery] = useState(false);
  const [showImportWizard, setShowImportWizard] = useState(false);
  const [showGitIntegration, setShowGitIntegration] = useState(false);
  const [showDataExportWizard, setShowDataExportWizard] = useState(false);
  const [showSessionsMenu, setShowSessionsMenu] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Initialize session tracking on component mount
  useEffect(() => {
    const sessionId = crossSessionLearning.startSession({
      contentTypes: formData.contentTypes,
      subject: profile?.subject || 'General',
      complexity: formData.complexity,
      aiEnhancements: formData.aiEnhancements
    });

    // Cleanup on unmount
    return () => {
      if (sessionId) {
        crossSessionLearning.endSession({
          completed: false,
          contentGenerated: false,
          errorsEncountered: []
        });
      }
    };
  }, [formData.contentTypes, profile?.subject, formData.complexity, formData.aiEnhancements]);

  // Auto-apply settings on load if user preference is set
  useEffect(() => {
    if (defaults && preferences?.useSettingsByDefault && !usingDefaults) {
      setFormData(prev => ({
        ...prev,
        duration: defaults.duration,
        complexity: defaults.complexity,
        contentTypes: [...defaults.contentTypes],
        quizTypes: [...defaults.quizTypes],
        includeAnswerKeys: defaults.includeAnswerKeys,
        includeInstructorGuides: defaults.includeInstructorGuides,
        rubrics: defaults.includeRubrics,
        accessibility: defaults.includeAccessibilityFeatures,
        answerKeyOptions: defaults.answerKeyOptions ? {
          includeExplanations: defaults.answerKeyOptions.includeExplanations,
          includeDifficulty: defaults.answerKeyOptions.includeDifficulty,
          includePoints: defaults.answerKeyOptions.includePoints
        } : prev.answerKeyOptions,
        instructorGuideOptions: defaults.instructorGuideOptions ? {
          includeTiming: defaults.instructorGuideOptions.includeTiming,
          includeGradingTips: defaults.instructorGuideOptions.includeGradingTips,
          includeDiscussionPrompts: defaults.instructorGuideOptions.includeDiscussionPrompts,
          includeExtensions: defaults.instructorGuideOptions.includeExtensions
        } : prev.instructorGuideOptions
      }));
      setUsingDefaults(true);
      
      // Track settings application
      crossSessionLearning.trackInteraction({
        type: 'setting_changed',
        data: { source: 'auto_apply_defaults' }
      });

      // Show status feedback
      statusFeedback.showSuccess(
        'Settings Applied',
        `Your default preferences have been automatically applied for ${defaults.contentTypes.length} content types.`
      );
    }
  }, [defaults, preferences, usingDefaults, statusFeedback]);

  // Load custom content types from settings
  const { state } = useSettings();
  useEffect(() => {
    if (state.settings?.advanced?.customContentTypes) {
      setCustomContentTypes(state.settings.advanced.customContentTypes);
    }
  }, [state.settings]);

  const handleModeSwitch = (mode: AppMode) => {
    setCurrentMode(mode);
    if (mode === 'wizard') {
      setCurrentStep(1);
    }
  };

  const handleInputChange = (field: string, value: string | boolean | Record<string, unknown>) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAIEnhancementsChange = (enhancements: Record<ContentType, AIContentOptions>) => {
    setFormData(prev => ({ ...prev, aiEnhancements: enhancements }));
  };

  const handleCustomContentTypesUpdated = (types: CustomContentType[]) => {
    setCustomContentTypes(types);
  };

  const addLearningObjective = () => {
    setFormData(prev => ({
      ...prev,
      learningObjectives: [...prev.learningObjectives, '']
    }));
  };

  const updateLearningObjective = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      learningObjectives: prev.learningObjectives.map((obj, i) => i === index ? value : obj)
    }));
  };

  const removeLearningObjective = (index: number) => {
    if (formData.learningObjectives.length > 1) {
      setFormData(prev => ({
        ...prev,
        learningObjectives: prev.learningObjectives.filter((_, i) => i !== index)
      }));
    }
  };

  const toggleContentType = (contentType: ContentType) => {
    setFormData(prev => ({
      ...prev,
      contentTypes: prev.contentTypes.includes(contentType)
        ? prev.contentTypes.filter(t => t !== contentType)
        : [...prev.contentTypes, contentType]
    }));
  };

  const toggleQuizType = (quizType: QuizType) => {
    setFormData(prev => ({
      ...prev,
      quizTypes: prev.quizTypes.includes(quizType)
        ? prev.quizTypes.filter(t => t !== quizType)
        : [...prev.quizTypes, quizType]
    }));
  };

  const nextStep = () => {
    if (currentStep < 6 && canProceed()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.topic.trim() !== '' && formData.audience.trim() !== '';
      case 2:
        return formData.learningObjectives.some(obj => obj.trim() !== '');
      case 3: {
        const hasContentTypes = formData.contentTypes.length > 0;
        const hasQuizTypesIfNeeded = !formData.contentTypes.includes('Quiz') || formData.quizTypes.length > 0;
        return hasContentTypes && hasQuizTypesIfNeeded;
      }
      case 4:
        return true; // AI enhancements are optional
      case 5:
        return true;
      default:
        return false;
    }
  };

  const hasManualObjectives = () => {
    return formData.learningObjectives.some(obj => obj.trim() !== '');
  };

  const getRecommendedObjectiveCount = () => {
    const duration = formData.duration;
    if (duration.includes('30')) return 3;
    if (duration.includes('50') || duration.includes('75')) return 4;
    if (duration.includes('90') || duration.includes('2 hour')) return 5;
    if (duration.includes('3 hour')) return 6;
    return 4;
  };

  const generateAIObjectives = async (count: number, existingObjectives: string[] = []) => {
    setAiGenerating(true);
    setShowObjectiveCountModal(false);
    
    // Show loading feedback
    const loadingId = statusFeedback.showLoading(
      'Generating Learning Objectives',
      `Creating ${count} objectives for ${formData.topic}...`
    );
    
    try {
      // Simulate AI generation (in real implementation, this would call the Rust backend)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const sampleObjectives = [
        `Students will be able to explain the fundamental concepts of ${formData.topic}`,
        `Students will demonstrate understanding by solving problems related to ${formData.topic}`,
        `Students will analyze real-world applications of ${formData.topic}`,
        `Students will evaluate different approaches to ${formData.topic}`,
        `Students will create examples that illustrate key principles of ${formData.topic}`,
        `Students will compare and contrast different aspects of ${formData.topic}`,
        `Students will apply ${formData.topic} concepts to new situations`,
        `Students will synthesize information about ${formData.topic} from multiple sources`
      ];
      
      // Filter out objectives similar to existing ones
      const availableObjectives = sampleObjectives.filter(obj => 
        !existingObjectives.some(existing => 
          existing.toLowerCase().includes(obj.split(' ').slice(-3).join(' ').toLowerCase())
        )
      );
      
      const newObjectives = availableObjectives.slice(0, count);
      
      if (existingObjectives.length > 0) {
        // Add to existing objectives
        setFormData(prev => ({
          ...prev,
          learningObjectives: [...prev.learningObjectives.filter(obj => obj.trim()), ...newObjectives]
        }));
      } else {
        // Replace empty objectives
        setFormData(prev => ({
          ...prev,
          learningObjectives: newObjectives
        }));
      }

      // Dismiss loading and show success
      statusFeedback.dismissMessage(loadingId);
      statusFeedback.showSuccess(
        'Objectives Generated',
        `Successfully created ${newObjectives.length} learning objectives for ${formData.topic}.`,
        4000
      );

    } catch (error) {
      console.error('AI generation failed:', error);
      
      // Dismiss loading and show error
      statusFeedback.dismissMessage(loadingId);
      statusFeedback.showError(
        'Generation Failed',
        'Unable to generate learning objectives. Please try again or create them manually.',
        6000
      );
    } finally {
      setAiGenerating(false);
    }
  };

  const handleGenerateObjectives = () => {
    const recommended = getRecommendedObjectiveCount();
    setObjectiveCount(recommended);
    setShowObjectiveCountModal(true);
  };

  const handleSuggestMore = () => {
    const existingObjectives = formData.learningObjectives.filter(obj => obj.trim());
    const recommended = Math.min(3, 8 - existingObjectives.length);
    setObjectiveCount(recommended);
    setShowObjectiveCountModal(true);
  };

  const applyDefaultSettings = () => {
    if (!defaults) return;

    setFormData(prev => ({
      ...prev,
      duration: defaults.duration,
      complexity: defaults.complexity,
      contentTypes: [...defaults.contentTypes],
      quizTypes: [...defaults.quizTypes],
      includeAnswerKeys: defaults.includeAnswerKeys,
      includeInstructorGuides: defaults.includeInstructorGuides,
      rubrics: defaults.includeRubrics,
      accessibility: defaults.includeAccessibilityFeatures,
      answerKeyOptions: defaults.answerKeyOptions ? {
        includeExplanations: defaults.answerKeyOptions.includeExplanations,
        includeDifficulty: defaults.answerKeyOptions.includeDifficulty,
        includePoints: defaults.answerKeyOptions.includePoints
      } : prev.answerKeyOptions,
      instructorGuideOptions: defaults.instructorGuideOptions ? {
        includeTiming: defaults.instructorGuideOptions.includeTiming,
        includeGradingTips: defaults.instructorGuideOptions.includeGradingTips,
        includeDiscussionPrompts: defaults.instructorGuideOptions.includeDiscussionPrompts,
        includeExtensions: defaults.instructorGuideOptions.includeExtensions
      } : prev.instructorGuideOptions
    }));
    
    setUsingDefaults(true);
    
    // Track settings application
    crossSessionLearning.trackInteraction({
      type: 'setting_changed',
      data: { source: 'manual_apply_defaults', contentTypes: defaults.contentTypes }
    });

    // Show status feedback
    statusFeedback.showSuccess(
      'Settings Applied',
      `Applied your saved preferences: ${defaults.contentTypes.join(', ')} for ${defaults.duration}.`,
      3000
    );
  };

  const clearDefaults = () => {
    setFormData(prev => ({
      ...prev,
      duration: '50 minutes',
      complexity: 'intermediate',
      contentTypes: [],
      quizTypes: [],
      includeAnswerKeys: true,
      includeInstructorGuides: true,
      rubrics: false,
      accessibility: false,
      answerKeyOptions: {
        includeExplanations: true,
        includeDifficulty: true,
        includePoints: false
      },
      instructorGuideOptions: {
        includeTiming: true,
        includeGradingTips: true,
        includeDiscussionPrompts: false,
        includeExtensions: false
      }
    }));
    
    setUsingDefaults(false);
  };

  // Rest of the component continues...
  // [I'll continue with the render methods from the original file]

  const renderWizardStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div>
            <h2 style={{ marginBottom: '8px', color: '#1e293b' }}>Topic & Audience</h2>
            <p style={{ color: '#64748b', marginBottom: '32px' }}>
              Let's start by defining what you want to teach and who your students are.
            </p>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                What topic will you be teaching?
              </label>
              <input
                type="text"
                value={formData.topic}
                onChange={(e) => handleInputChange('topic', e.target.value)}
                placeholder="e.g., Introduction to Calculus, World War I, Cell Biology"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  fontSize: '16px'
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Who is your audience?
              </label>
              <input
                type="text"
                value={formData.audience}
                onChange={(e) => handleInputChange('audience', e.target.value)}
                placeholder="e.g., High school seniors, College freshmen, Adult learners"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  fontSize: '16px'
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                How long is your class session?
                {usingDefaults && defaults?.duration === formData.duration && (
                  <span style={{ 
                    fontSize: '12px', 
                    color: '#16a34a', 
                    fontWeight: '400',
                    marginLeft: '8px',
                    padding: '2px 6px',
                    backgroundColor: '#dcfce7',
                    borderRadius: '4px'
                  }}>
                    ⚙️ From Settings
                  </span>
                )}
              </label>
              <select
                value={formData.duration}
                onChange={(e) => handleInputChange('duration', e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: `1px solid ${usingDefaults && defaults?.duration === formData.duration ? '#16a34a' : '#d1d5db'}`,
                  borderRadius: '8px',
                  fontSize: '16px',
                  backgroundColor: usingDefaults && defaults?.duration === formData.duration ? '#f0fdf4' : 'white'
                }}
              >
                <option value="30 minutes">30 minutes</option>
                <option value="50 minutes">50 minutes</option>
                <option value="75 minutes">75 minutes</option>
                <option value="90 minutes">90 minutes</option>
                <option value="2 hours">2 hours</option>
                <option value="3 hours">3 hours</option>
              </select>
            </div>
          </div>
        );

      case 2:
        return (
          <div>
            <h2 style={{ marginBottom: '8px', color: '#1e293b' }}>Learning Objectives</h2>
            <p style={{ color: '#64748b', marginBottom: '32px' }}>
              What should students be able to do after this lesson?
            </p>
            
            {/* AI Generation Section */}
            {!hasManualObjectives() && !aiGenerating && (
              <div style={{ 
                backgroundColor: '#f0f9ff', 
                border: '1px solid #bfdbfe', 
                borderRadius: '12px', 
                padding: '20px', 
                marginBottom: '24px', 
                textAlign: 'center' 
              }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#1e40af', fontSize: '16px' }}>
                  ✨ Let AI Help You Get Started
                </h3>
                <p style={{ margin: '0 0 16px 0', color: '#1e40af', fontSize: '14px' }}>
                  Generate learning objectives for: <strong>{formData.topic || 'your topic'}</strong>
                  {formData.audience && ` (${formData.audience})`} • {formData.duration}
                </p>
                <button
                  onClick={handleGenerateObjectives}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '16px',
                    fontWeight: '500'
                  }}
                >
                  ✨ Generate AI Objectives
                </button>
              </div>
            )}

            {/* Loading State */}
            {aiGenerating && (
              <div style={{ 
                backgroundColor: '#f9fafb', 
                border: '1px solid #e5e7eb', 
                borderRadius: '12px', 
                padding: '40px', 
                marginBottom: '24px', 
                textAlign: 'center' 
              }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  margin: '0 auto 16px',
                  border: '4px solid #f3f4f6',
                  borderTop: '4px solid #3b82f6',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
                <p style={{ color: '#64748b', fontSize: '16px', margin: '0 0 8px 0' }}>
                  AI is generating learning objectives...
                </p>
                <p style={{ color: '#9ca3af', fontSize: '14px', margin: 0 }}>
                  This may take a few seconds
                </p>
              </div>
            )}

            {/* Learning Objectives Input */}
            <div style={{ marginBottom: '16px' }}>
              {formData.learningObjectives.map((objective, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                  <input
                    type="text"
                    value={objective}
                    onChange={(e) => updateLearningObjective(index, e.target.value)}
                    placeholder={`Learning objective ${index + 1}`}
                    style={{
                      flex: 1,
                      padding: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '16px'
                    }}
                  />
                  {formData.learningObjectives.length > 1 && (
                    <button
                      onClick={() => removeLearningObjective(index)}
                      style={{
                        width: '32px',
                        height: '32px',
                        border: 'none',
                        backgroundColor: '#fee2e2',
                        color: '#dc2626',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '18px'
                      }}
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={addLearningObjective}
                  style={{
                    flex: 1,
                    padding: '12px 16px',
                    border: '2px dashed #d1d5db',
                    background: 'none',
                    borderRadius: '8px',
                    color: '#6b7280',
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                >
                  + Add Another Objective
                </button>
                
                {hasManualObjectives() && (
                  <button
                    onClick={handleSuggestMore}
                    style={{
                      padding: '12px 16px',
                      border: '1px solid #3b82f6',
                      backgroundColor: '#dbeafe',
                      color: '#1e40af',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontSize: '16px',
                      fontWeight: '500'
                    }}
                  >
                    ✨ Suggest More
                  </button>
                )}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div>
            <h2 style={{ marginBottom: '8px', color: '#1e293b' }}>Content Selection</h2>
            <p style={{ color: '#64748b', marginBottom: '32px' }}>
              What types of content would you like to generate?
            </p>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: `repeat(${Math.min(layout.gridColumns, 3)}, 1fr)`, 
              gap: `${layout.spacing.md}px`
            }}>
              {(['Slides', 'InstructorNotes', 'Worksheet', 'Quiz', 'ActivityGuide'] as ContentType[]).map((type) => {
                const isSelected = formData.contentTypes.includes(type);
                const isFromDefaults = usingDefaults && defaults?.contentTypes.includes(type);
                const borderColor = isSelected ? (isFromDefaults ? '#16a34a' : '#3b82f6') : '#e5e7eb';
                const bgColor = isSelected ? (isFromDefaults ? '#dcfce7' : '#dbeafe') : 'white';
                
                return (
                  <div
                    key={type}
                    onClick={() => toggleContentType(type)}
                    style={{
                      padding: `${layout.spacing.md}px`,
                      border: `2px solid ${borderColor}`,
                      borderRadius: '12px',
                      cursor: 'pointer',
                      textAlign: 'center',
                      backgroundColor: bgColor,
                      transition: 'all 0.2s',
                      position: 'relative'
                    }}
                  >
                    {/* Settings indicator badge */}
                    {isFromDefaults && (
                      <div style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        backgroundColor: '#16a34a',
                        color: 'white',
                        borderRadius: '50%',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        fontWeight: 'bold'
                      }}>
                        ⚙
                      </div>
                    )}
                    
                    <div style={{
                      width: '48px',
                      height: '48px',
                      margin: '0 auto 12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: isSelected ? (isFromDefaults ? '#16a34a' : '#3b82f6') : '#f1f5f9',
                      borderRadius: '12px',
                      color: isSelected ? 'white' : '#64748b',
                      fontSize: '24px'
                    }}>
                      {type === 'Slides' && '📊'}
                      {type === 'InstructorNotes' && '📝'}
                      {type === 'Worksheet' && '📄'}
                      {type === 'Quiz' && '❓'}
                      {type === 'ActivityGuide' && '👥'}
                    </div>
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '8px' }}>
                      {type.replace(/([A-Z])/g, ' $1').trim()}
                      {isFromDefaults && (
                        <span style={{ 
                          fontSize: '11px', 
                          color: '#16a34a', 
                          fontWeight: '400',
                          marginLeft: '4px'
                        }}>
                          ⚙️
                        </span>
                      )}
                    </h3>
                    <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
                      {type === 'Slides' && 'Presentation slides with key points'}
                      {type === 'InstructorNotes' && 'Detailed teaching notes'}
                      {type === 'Worksheet' && 'Student practice exercises'}
                      {type === 'Quiz' && 'Assessment questions'}
                      {type === 'ActivityGuide' && 'Interactive learning activities'}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Custom Content Types Section */}
            {customContentTypes.length > 0 && (
              <div style={{ marginTop: '32px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                    🎨 Custom Content Types
                  </h3>
                  <button
                    onClick={() => setShowCustomContentManager(true)}
                    style={{
                      padding: '8px 16px',
                      border: '1px solid #3b82f6',
                      backgroundColor: '#dbeafe',
                      color: '#1e40af',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: '500'
                    }}
                  >
                    ⚙️ Manage Custom Types
                  </button>
                </div>
                
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: `repeat(${layout.gridColumns}, 1fr)`, 
                  gap: `${layout.spacing.md}px`
                }}>
                  {customContentTypes.map((customType) => {
                    const isSelected = formData.contentTypes.includes(customType.name as ContentType);
                    const borderColor = isSelected ? '#3b82f6' : '#e5e7eb';
                    const bgColor = isSelected ? '#dbeafe' : 'white';
                    
                    return (
                      <div
                        key={customType.id}
                        onClick={() => toggleContentType(customType.name as ContentType)}
                        style={{
                          padding: `${layout.spacing.md}px`,
                          border: `2px solid ${borderColor}`,
                          borderRadius: '12px',
                          cursor: 'pointer',
                          textAlign: 'center',
                          backgroundColor: bgColor,
                          transition: 'all 0.2s',
                          position: 'relative'
                        }}
                      >
                        <div style={{
                          width: '48px',
                          height: '48px',
                          margin: '0 auto 12px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: isSelected ? '#3b82f6' : '#f1f5f9',
                          borderRadius: '12px',
                          color: isSelected ? 'white' : '#64748b',
                          fontSize: '24px'
                        }}>
                          {customType.icon}
                        </div>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '8px' }}>
                          {customType.name}
                        </h3>
                        <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
                          {customType.description}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Add Custom Content Type Button - Shows when no custom types exist */}
            {customContentTypes.length === 0 && (
              <div style={{ 
                marginTop: '32px',
                padding: '24px',
                backgroundColor: '#f8fafc',
                borderRadius: '12px',
                border: '2px dashed #cbd5e1',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>🎨</div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '8px' }}>
                  Need something different?
                </h3>
                <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '16px' }}>
                  Create custom content types for specialized materials like lab reports, case studies, or project proposals.
                </p>
                <button
                  onClick={() => setShowCustomContentManager(true)}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  ➕ Create Custom Content Type
                </button>
              </div>
            )}
            
            {/* Quiz Types Selection - Shows when Quiz is selected */}
            {formData.contentTypes.includes('Quiz') && (
              <div style={{ 
                marginTop: '32px',
                padding: '20px',
                backgroundColor: '#f0f9ff',
                border: '1px solid #bfdbfe',
                borderRadius: '12px'
              }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1e40af', marginBottom: '16px' }}>
                  📊 Quiz Types
                </h3>
                <p style={{ fontSize: '14px', color: '#1e40af', marginBottom: '20px' }}>
                  Select which types of assessment questions to include:
                </p>
                
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: `repeat(${Math.min(layout.gridColumns, 2)}, 1fr)`, 
                  gap: `${layout.spacing.sm}px`
                }}>
                  {[
                    { type: 'multiple-choice', label: 'Multiple Choice', icon: '🔘', desc: 'A, B, C, D options' },
                    { type: 'true-false', label: 'True/False', icon: '✓✗', desc: 'Simple binary questions' },
                    { type: 'short-answer', label: 'Short Answer', icon: '📝', desc: 'Brief written responses' },
                    { type: 'essay', label: 'Essay Questions', icon: '📄', desc: 'Long-form responses' },
                    { type: 'fill-in-blank', label: 'Fill in the Blank', icon: '📝', desc: 'Complete the sentence' },
                    { type: 'matching', label: 'Matching', icon: '🔗', desc: 'Connect related items' }
                  ].map((quiz) => (
                    <div
                      key={quiz.type}
                      onClick={() => toggleQuizType(quiz.type as QuizType)}
                      style={{
                        padding: '16px',
                        border: `2px solid ${formData.quizTypes.includes(quiz.type as QuizType) ? '#3b82f6' : '#e5e7eb'}`,
                        borderRadius: '8px',
                        cursor: 'pointer',
                        backgroundColor: formData.quizTypes.includes(quiz.type as QuizType) ? '#dbeafe' : 'white',
                        transition: 'all 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                        <span style={{ fontSize: '18px' }}>{quiz.icon}</span>
                        <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                          {quiz.label}
                        </h4>
                      </div>
                      <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
                        {quiz.desc}
                      </p>
                    </div>
                  ))}
                </div>
                
                {/* Answer Key & Instructor Guide Options */}
                <div style={{ 
                  marginTop: '20px',
                  padding: '16px',
                  backgroundColor: 'white',
                  borderRadius: '12px',
                  border: '1px solid #e5e7eb'
                }}>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>📋</span>
                    Automatic Generation Options
                  </h4>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.includeAnswerKeys}
                        onChange={(e) => handleInputChange('includeAnswerKeys', e.target.checked)}
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span style={{ fontSize: '14px', color: '#374151' }}>
                        🔑 Generate Answer Keys
                      </span>
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.includeInstructorGuides}
                        onChange={(e) => handleInputChange('includeInstructorGuides', e.target.checked)}
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span style={{ fontSize: '14px', color: '#374151' }}>
                        📖 Generate Instructor Guides
                      </span>
                    </label>
                  </div>

                  {/* Answer Key Options */}
                  {formData.includeAnswerKeys && (
                    <div style={{ 
                      marginBottom: '16px',
                      padding: '12px',
                      backgroundColor: '#f8fafc',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0'
                    }}>
                      <h5 style={{ fontSize: '14px', fontWeight: '600', color: '#475569', marginBottom: '12px' }}>
                        🔑 Answer Key Options
                      </h5>
                      <div style={{ display: 'grid', gap: '8px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formData.answerKeyOptions?.includeExplanations ?? true}
                            onChange={(e) => handleInputChange('answerKeyOptions', { 
                              ...formData.answerKeyOptions, 
                              includeExplanations: e.target.checked 
                            })}
                            style={{ width: '14px', height: '14px' }}
                          />
                          <span style={{ fontSize: '13px', color: '#64748b' }}>
                            Include detailed explanations for answers
                          </span>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formData.answerKeyOptions?.includeDifficulty ?? true}
                            onChange={(e) => handleInputChange('answerKeyOptions', { 
                              ...formData.answerKeyOptions, 
                              includeDifficulty: e.target.checked 
                            })}
                            style={{ width: '14px', height: '14px' }}
                          />
                          <span style={{ fontSize: '13px', color: '#64748b' }}>
                            Mark question difficulty levels
                          </span>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formData.answerKeyOptions?.includePoints ?? false}
                            onChange={(e) => handleInputChange('answerKeyOptions', { 
                              ...formData.answerKeyOptions, 
                              includePoints: e.target.checked 
                            })}
                            style={{ width: '14px', height: '14px' }}
                          />
                          <span style={{ fontSize: '13px', color: '#64748b' }}>
                            Suggest point values for each question
                          </span>
                        </label>
                      </div>
                    </div>
                  )}

                  {/* Instructor Guide Options */}
                  {formData.includeInstructorGuides && (
                    <div style={{ 
                      padding: '12px',
                      backgroundColor: '#f0f9ff',
                      borderRadius: '8px',
                      border: '1px solid #bfdbfe'
                    }}>
                      <h5 style={{ fontSize: '14px', fontWeight: '600', color: '#1e40af', marginBottom: '12px' }}>
                        📖 Instructor Guide Content
                      </h5>
                      <div style={{ display: 'grid', gap: '8px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formData.instructorGuideOptions?.includeTiming ?? true}
                            onChange={(e) => handleInputChange('instructorGuideOptions', { 
                              ...formData.instructorGuideOptions, 
                              includeTiming: e.target.checked 
                            })}
                            style={{ width: '14px', height: '14px' }}
                          />
                          <span style={{ fontSize: '13px', color: '#1e40af' }}>
                            Suggested timing for each section
                          </span>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formData.instructorGuideOptions?.includeGradingTips ?? true}
                            onChange={(e) => handleInputChange('instructorGuideOptions', { 
                              ...formData.instructorGuideOptions, 
                              includeGradingTips: e.target.checked 
                            })}
                            style={{ width: '14px', height: '14px' }}
                          />
                          <span style={{ fontSize: '13px', color: '#1e40af' }}>
                            Grading tips and common mistakes
                          </span>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formData.instructorGuideOptions?.includeDiscussionPrompts ?? false}
                            onChange={(e) => handleInputChange('instructorGuideOptions', { 
                              ...formData.instructorGuideOptions, 
                              includeDiscussionPrompts: e.target.checked 
                            })}
                            style={{ width: '14px', height: '14px' }}
                          />
                          <span style={{ fontSize: '13px', color: '#1e40af' }}>
                            Discussion prompts for reviewing answers
                          </span>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formData.instructorGuideOptions?.includeExtensions ?? false}
                            onChange={(e) => handleInputChange('instructorGuideOptions', { 
                              ...formData.instructorGuideOptions, 
                              includeExtensions: e.target.checked 
                            })}
                            style={{ width: '14px', height: '14px' }}
                          />
                          <span style={{ fontSize: '13px', color: '#1e40af' }}>
                            Extension activities for advanced students
                          </span>
                        </label>
                      </div>
                    </div>
                  )}

                  {/* Preview Summary */}
                  <div style={{ 
                    marginTop: '16px',
                    padding: '12px',
                    backgroundColor: '#ecfdf5',
                    borderRadius: '8px',
                    fontSize: '13px',
                    color: '#166534'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span>✨</span>
                      <strong>Will Generate:</strong>
                    </div>
                    <div style={{ paddingLeft: '24px' }}>
                      {formData.quizTypes.length > 0 && (
                        <div>• Quiz with {formData.quizTypes.length} question type{formData.quizTypes.length > 1 ? 's' : ''}</div>
                      )}
                      {formData.includeAnswerKeys && (
                        <div>• Complete answer key{formData.answerKeyOptions?.includeExplanations ? ' with explanations' : ''}</div>
                      )}
                      {formData.includeInstructorGuides && (
                        <div>• Instructor guide{formData.instructorGuideOptions?.includeGradingTips ? ' with grading tips' : ''}</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case 4:
        return (
          <div>
            <h2 style={{ marginBottom: '8px', color: '#1e293b' }}>AI Enhancement Options</h2>
            <p style={{ color: '#64748b', marginBottom: '32px' }}>
              Configure how AI will enhance each type of content based on your teaching preferences.
            </p>
            
            <ContentAIEnhancements
              selectedContentTypes={formData.contentTypes}
              customContentTypes={customContentTypes}
              onEnhancementsChange={handleAIEnhancementsChange}
            />
          </div>
        );

      case 5:
        return (
          <div>
            <h2 style={{ marginBottom: '8px', color: '#1e293b' }}>Final Settings</h2>
            <p style={{ color: '#64748b', marginBottom: '32px' }}>
              Review your settings and configure any final options before generating your curriculum content.
            </p>
            
            <div style={{ display: 'grid', gap: '24px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                  Content Complexity
                  {usingDefaults && defaults?.complexity === formData.complexity && (
                    <span style={{ 
                      fontSize: '12px', 
                      color: '#16a34a', 
                      fontWeight: '400',
                      marginLeft: '8px',
                      padding: '2px 6px',
                      backgroundColor: '#dcfce7',
                      borderRadius: '4px'
                    }}>
                      ⚙️ From Settings
                    </span>
                  )}
                </label>
                <select
                  value={formData.complexity}
                  onChange={(e) => handleInputChange('complexity', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: `1px solid ${usingDefaults && defaults?.complexity === formData.complexity ? '#16a34a' : '#d1d5db'}`,
                    borderRadius: '8px',
                    fontSize: '16px',
                    backgroundColor: usingDefaults && defaults?.complexity === formData.complexity ? '#f0fdf4' : 'white'
                  }}
                >
                  <option value="basic">Basic - Introductory level concepts</option>
                  <option value="intermediate">Intermediate - Standard course depth</option>
                  <option value="advanced">Advanced - In-depth analysis and application</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                  Teaching Style
                </label>
                <select
                  value={formData.style}
                  onChange={(e) => handleInputChange('style', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '16px'
                  }}
                >
                  <option value="interactive">Interactive - Engaging activities and discussions</option>
                  <option value="traditional">Traditional - Lecture-based approach</option>
                  <option value="hands-on">Hands-on - Practical exercises and labs</option>
                  <option value="collaborative">Collaborative - Group work and peer learning</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '12px', fontWeight: '500' }}>
                  Additional Features
                </label>
                <div style={{ display: 'grid', gap: '12px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formData.accessibility}
                      onChange={(e) => handleInputChange('accessibility', e.target.checked)}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <span style={{ fontSize: '14px', color: '#374151' }}>
                      ♿ Include accessibility features
                    </span>
                  </label>
                  
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formData.rubrics}
                      onChange={(e) => handleInputChange('rubrics', e.target.checked)}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <span style={{ fontSize: '14px', color: '#374151' }}>
                      📊 Generate assessment rubrics
                    </span>
                  </label>
                  
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formData.extensions}
                      onChange={(e) => handleInputChange('extensions', e.target.checked)}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <span style={{ fontSize: '14px', color: '#374151' }}>
                      🚀 Include extension activities
                    </span>
                  </label>
                </div>
              </div>

              {/* Summary */}
              <div style={{
                padding: '20px',
                backgroundColor: '#f8fafc',
                borderRadius: '12px',
                border: '1px solid #e2e8f0'
              }}>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
                  📋 Generation Summary
                </h3>
                <div style={{ display: 'grid', gap: '8px', fontSize: '14px', color: '#475569' }}>
                  <div><strong>Topic:</strong> {formData.topic}</div>
                  <div><strong>Audience:</strong> {formData.audience}</div>
                  <div><strong>Duration:</strong> {formData.duration}</div>
                  <div><strong>Learning Objectives:</strong> {formData.learningObjectives.filter(obj => obj.trim()).length}</div>
                  <div><strong>Content Types:</strong> {formData.contentTypes.join(', ')}</div>
                  {formData.contentTypes.includes('Quiz') && (
                    <div><strong>Quiz Types:</strong> {formData.quizTypes.join(', ')}</div>
                  )}
                  <div><strong>Complexity:</strong> {formData.complexity}</div>
                  <div><strong>AI Enhancements:</strong> {Object.values(formData.aiEnhancements).reduce((total, options) => total + Object.values(options).filter(Boolean).length, 0)} features enabled</div>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return <div>Step not implemented</div>;
    }
  };

  return (
    <div className="app">
      {/* Objective Count Modal */}
      {showObjectiveCountModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: `${layout.spacing.xl}px`,
            maxWidth: layout.isSmallDesktop ? '350px' : '400px',
            width: '90%',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
            fontSize: `${layout.fontSize.base}px`
          }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#1e293b', fontSize: '20px' }}>
              How many learning objectives?
            </h3>
            <p style={{ margin: '0 0 20px 0', color: '#64748b', fontSize: '14px' }}>
              Recommended: {getRecommendedObjectiveCount()} objectives for {formData.duration}
            </p>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <input
                type="number"
                min="1"
                max="8"
                value={objectiveCount}
                onChange={(e) => setObjectiveCount(Number(e.target.value))}
                style={{
                  width: '80px',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '16px',
                  textAlign: 'center'
                }}
              />
              <span style={{ color: '#64748b', fontSize: '14px' }}>objectives</span>
            </div>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowObjectiveCountModal(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  backgroundColor: '#f3f4f6',
                  color: '#374151',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const existingObjectives = formData.learningObjectives.filter(obj => obj.trim());
                  generateAIObjectives(objectiveCount, existingObjectives);
                }}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                ✨ Generate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header style={{ 
        padding: '16px 24px', 
        backgroundColor: 'white', 
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h1 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
            Curriculum Curator
          </h1>
          {profile && (
            <span style={{ fontSize: '14px', color: '#64748b' }}>
              Welcome, {profile.name} ({profile.subject})
            </span>
          )}
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Mode Switcher - Make it first and prominent */}
          <div style={{ 
            display: 'flex', 
            gap: '4px', 
            backgroundColor: '#f1f5f9', 
            padding: '6px', 
            borderRadius: '8px',
            border: '2px solid #3b82f6',
            minWidth: '240px'
          }}>
            <button
              onClick={() => handleModeSwitch('wizard')}
              style={{
                padding: '10px 16px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: currentMode === 'wizard' ? 'white' : 'transparent',
                color: currentMode === 'wizard' ? '#3b82f6' : '#64748b',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                flex: 1,
                boxShadow: currentMode === 'wizard' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
              }}
            >
              🧙‍♂️ Wizard
            </button>
            <button
              onClick={() => handleModeSwitch('expert')}
              style={{
                padding: '10px 16px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: currentMode === 'expert' ? 'white' : 'transparent',
                color: currentMode === 'expert' ? '#3b82f6' : '#64748b',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                flex: 1,
                boxShadow: currentMode === 'expert' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
              }}
            >
              🎯 Expert
            </button>
          </div>

          <button
            onClick={() => {
              setShowPreview(!showPreview);
              // Track preview toggle
              crossSessionLearning.trackInteraction({
                type: 'setting_changed',
                data: { action: 'toggle_preview', enabled: !showPreview }
              });
            }}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              backgroundColor: showPreview ? '#3b82f6' : 'white',
              color: showPreview ? 'white' : '#64748b',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            👁️ Preview
          </button>
          <button
            onClick={() => setShowLLMSetup(true)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              backgroundColor: llm.hasAvailableProvider ? '#dcfce7' : '#fef3c7',
              color: llm.hasAvailableProvider ? '#166534' : '#92400e',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            {llm.hasAvailableProvider ? '🤖 LLM Ready' : '⚠️ Setup LLM'}
          </button>
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowSessionsMenu(!showSessionsMenu)}
              style={{
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                backgroundColor: 'white',
                color: '#64748b',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              📁 Sessions ▼
            </button>
            {showSessionsMenu && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                background: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                padding: '8px 0',
                minWidth: '160px',
                zIndex: 1000
              }}>
                <button
                  onClick={() => {
                    setShowSessionBrowser(true);
                    setShowSessionsMenu(false);
                  }}
                  style={{
                    width: '100%',
                    padding: '8px 16px',
                    border: 'none',
                    background: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '14px',
                    color: '#374151'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  📁 Browse Sessions
                </button>
                <button
                  onClick={() => {
                    setShowSessionHistory(true);
                    setShowSessionsMenu(false);
                  }}
                  style={{
                    width: '100%',
                    padding: '8px 16px',
                    border: 'none',
                    background: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '14px',
                    color: '#374151'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  📅 Session History
                </button>
                <button
                  onClick={() => {
                    setShowBackupRecovery(true);
                    setShowSessionsMenu(false);
                  }}
                  style={{
                    width: '100%',
                    padding: '8px 16px',
                    border: 'none',
                    background: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '14px',
                    color: '#374151'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  💾 Backup & Recovery
                </button>
              </div>
            )}
          </div>
          <button
            onClick={() => setShowImportWizard(true)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              color: '#64748b',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            📁 Import
          </button>
          <button
            onClick={() => setShowFileOperations(true)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              color: '#64748b',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            💾 File
          </button>
          <button
            onClick={() => setShowGitIntegration(true)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              color: '#64748b',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            🔧 Git
          </button>
          <button
            onClick={() => setShowDataExportWizard(true)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              color: '#64748b',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            📤 Export
          </button>
          <button
            onClick={() => setShowSettings(true)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              color: '#64748b',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            ⚙️ Settings
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ 
        padding: `${layout.spacing.md}px`, 
        backgroundColor: '#f8fafc', 
        flex: 1,
        minHeight: 'calc(100vh - 80px)',
        overflow: 'auto',
        marginRight: showPreview ? `${previewWidth}px` : '0',
        transition: 'margin-right 0.3s ease',
        fontSize: `${layout.fontSize.base}px`
      }}>
        {currentMode === 'wizard' ? (
          <div style={{ 
            maxWidth: `${layout.contentMaxWidth}px`, 
            margin: '0 auto',
            ...getOptimalWizardLayout(layout.windowWidth).containerMaxWidth && {
              maxWidth: getOptimalWizardLayout(layout.windowWidth).containerMaxWidth
            }
          }}>
            {/* Progress Indicator */}
            <div style={{ marginBottom: `${layout.spacing.xl}px` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
                <div style={{ flex: 1, height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ 
                    height: '100%', 
                    backgroundColor: '#3b82f6', 
                    width: `${(currentStep / 6) * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <span style={{ fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
                  Step {currentStep} of 6
                </span>
              </div>
            </div>

            {/* Use Settings Banner */}
            {defaults && profile && (
              <div style={{
                backgroundColor: usingDefaults ? '#dcfce7' : '#f0f9ff',
                border: `2px solid ${usingDefaults ? '#16a34a' : '#3b82f6'}`,
                borderRadius: '12px',
                padding: `${layout.spacing.md}px`,
                marginBottom: `${layout.spacing.lg}px`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '16px'
              }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ 
                    fontSize: '16px', 
                    fontWeight: '600', 
                    color: usingDefaults ? '#166534' : '#1e40af', 
                    margin: '0 0 8px 0' 
                  }}>
                    {usingDefaults ? '✅ Using Your Settings' : '⚙️ Use Your Saved Settings'}
                  </h3>
                  <p style={{ 
                    fontSize: '14px', 
                    color: usingDefaults ? '#166534' : '#1e40af', 
                    margin: '0 0 12px 0' 
                  }}>
                    {usingDefaults 
                      ? `Applied ${profile.name}'s default preferences for ${defaults.contentTypes.length} content types and ${defaults.duration} sessions.`
                      : `Quickly populate form with your saved preferences: ${defaults.contentTypes.length} content types, ${defaults.duration} duration, and ${defaults.complexity} complexity.`
                    }
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                    {defaults.contentTypes.length > 0 && (
                      <span style={{ 
                        padding: '4px 8px', 
                        backgroundColor: 'white', 
                        borderRadius: '12px', 
                        color: usingDefaults ? '#166534' : '#1e40af',
                        border: `1px solid ${usingDefaults ? '#16a34a' : '#3b82f6'}`
                      }}>
                        📝 {defaults.contentTypes.join(', ')}
                      </span>
                    )}
                    <span style={{ 
                      padding: '4px 8px', 
                      backgroundColor: 'white', 
                      borderRadius: '12px', 
                      color: usingDefaults ? '#166534' : '#1e40af',
                      border: `1px solid ${usingDefaults ? '#16a34a' : '#3b82f6'}`
                    }}>
                      ⏱️ {defaults.duration}
                    </span>
                    <span style={{ 
                      padding: '4px 8px', 
                      backgroundColor: 'white', 
                      borderRadius: '12px', 
                      color: usingDefaults ? '#166534' : '#1e40af',
                      border: `1px solid ${usingDefaults ? '#16a34a' : '#3b82f6'}`
                    }}>
                      📊 {defaults.complexity}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  {!usingDefaults ? (
                    <button
                      onClick={applyDefaultSettings}
                      style={{
                        padding: '12px 20px',
                        border: 'none',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      ⚙️ Use Settings
                    </button>
                  ) : (
                    <button
                      onClick={clearDefaults}
                      style={{
                        padding: '12px 20px',
                        border: '1px solid #16a34a',
                        backgroundColor: 'white',
                        color: '#166534',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      🔄 Clear Settings
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Step Content */}
            <div style={{ 
              backgroundColor: 'white', 
              padding: `${layout.spacing.xl}px`, 
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              marginBottom: '24px'
            }}>
              {renderWizardStep()}
            </div>

            {/* Navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {currentStep > 1 ? (
                <button
                  onClick={prevStep}
                  style={{
                    padding: '12px 24px',
                    border: '1px solid #d1d5db',
                    backgroundColor: '#f3f4f6',
                    color: '#374151',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                >
                  ← Previous
                </button>
              ) : <div />}
              
              {currentStep < 5 && (
                <button
                  onClick={nextStep}
                  disabled={!canProceed()}
                  style={{
                    padding: '12px 24px',
                    border: 'none',
                    backgroundColor: canProceed() ? '#3b82f6' : '#9ca3af',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: canProceed() ? 'pointer' : 'not-allowed',
                    fontSize: '16px'
                  }}
                >
                  {currentStep === 4 ? 'Review →' : 'Next →'}
                </button>
              )}
              
              {currentStep === 5 && (
                <button
                  onClick={async () => {
                    // Check if LLM provider is available before starting generation
                    if (!llm.hasAvailableProvider) {
                      setShowLLMSetup(true);
                      statusFeedback.showWarning(
                        'LLM Provider Required',
                        'Please configure an LLM provider to generate content.',
                        5000
                      );
                      return;
                    }

                    // Track content generation attempt
                    crossSessionLearning.trackInteraction({
                      type: 'content_generated',
                      data: {
                        contentTypes: formData.contentTypes,
                        complexity: formData.complexity,
                        duration: formData.duration,
                        subject: formData.subject
                      }
                    });
                    
                    // Update session with completion
                    crossSessionLearning.updateSession({
                      contentTypes: formData.contentTypes,
                      complexity: formData.complexity,
                      aiEnhancements: formData.aiEnhancements
                    });

                    // Prepare generation config
                    const config: GenerationConfig = {
                      topic: formData.topic,
                      audience: formData.audience,
                      subject: formData.subject,
                      duration: formData.duration,
                      complexity: formData.complexity,
                      learningObjectives: formData.learningObjectives.filter(obj => obj.trim()),
                      contentTypes: formData.contentTypes,
                      quizTypes: formData.quizTypes,
                      additionalOptions: {
                        includeAnswerKeys: formData.includeAnswerKeys,
                        includeInstructorGuides: formData.includeInstructorGuides,
                        accessibility: formData.accessibility,
                        rubrics: formData.rubrics,
                        extensions: formData.extensions
                      }
                    };

                    // Start generation with progress tracking
                    setShowProgress(true);
                    
                    try {
                      const result = await generationManager.startGeneration(
                        config,
                        (progress) => {
                          setGenerationProgress(progress);
                        },
                        (error) => {
                          console.error('Generation error:', error);
                          statusFeedback.showError(
                            'Generation Error',
                            `Error in ${error.stepId}: ${error.message}`,
                            8000
                          );
                        }
                      );

                      // End session as successful
                      crossSessionLearning.endSession({
                        completed: true,
                        contentGenerated: result.success,
                        errorsEncountered: result.errors.map(e => e.message)
                      });

                      // Show completion feedback
                      if (result.success) {
                        statusFeedback.showSuccess(
                          'Content Generated Successfully!',
                          `Generated ${result.contentFiles.length} content files. You can now download or export your materials.`,
                          0 // Persistent message
                        );
                      } else {
                        statusFeedback.showWarning(
                          'Generation Completed with Issues',
                          `${result.contentFiles.length} files generated, but ${result.errors.length} errors occurred. Review the results.`,
                          0 // Persistent message
                        );
                      }

                    } catch (error) {
                      console.error('Generation failed:', error);
                      crossSessionLearning.endSession({
                        completed: false,
                        contentGenerated: false,
                        errorsEncountered: [error instanceof Error ? error.message : 'Unknown error']
                      });

                      // Show failure feedback
                      statusFeedback.showError(
                        'Generation Failed',
                        error instanceof Error ? error.message : 'An unexpected error occurred during content generation.',
                        0 // Persistent message
                      );
                    }
                  }}
                  style={{
                    padding: '12px 24px',
                    border: 'none',
                    backgroundColor: '#059669',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '16px',
                    fontWeight: '500'
                  }}
                >
                  🚀 Generate Content
                </button>
              )}
            </div>
          </div>
        ) : (
          <ExpertMode 
            onModeSwitch={(mode) => setCurrentMode(mode)}
          />
        )}
      </main>
      
      {/* Settings Panel */}
      <SettingsPanel isOpen={showSettings} onClose={() => setShowSettings(false)} />
      
      {/* Custom Content Type Manager */}
      <CustomContentTypeManager 
        isOpen={showCustomContentManager} 
        onClose={() => setShowCustomContentManager(false)}
        onContentTypesUpdated={handleCustomContentTypesUpdated}
      />

      {/* Live Content Preview */}
      <LiveContentPreview
        formData={formData}
        currentStep={currentStep}
        isVisible={showPreview}
        onToggleVisibility={() => setShowPreview(!showPreview)}
        width={previewWidth}
        onWidthChange={setPreviewWidth}
      />

      {/* Progress Indicator */}
      {generationProgress && (
        <ProgressIndicator
          isVisible={showProgress}
          progress={generationProgress}
          onCancel={() => {
            generationManager.cancelGeneration();
            setShowProgress(false);
            setGenerationProgress(null);
          }}
          onRetry={(stepId) => {
            generationManager.retryStep(stepId);
          }}
          onClose={() => {
            setShowProgress(false);
            setGenerationProgress(null);
          }}
        />
      )}

      {/* LLM Provider Setup */}
      <LLMProviderSetup
        isOpen={showLLMSetup}
        onClose={() => setShowLLMSetup(false)}
        onProviderReady={(providerId) => {
          statusFeedback.showSuccess(
            'LLM Provider Ready',
            `${providerId} is now configured and ready for content generation.`,
            4000
          );
          setShowLLMSetup(false);
        }}
      />

      {/* File Operations */}
      <FileOperations
        isOpen={showFileOperations}
        onClose={() => setShowFileOperations(false)}
        sessionId={currentSessionId}
      />

      {/* Session Browser */}
      <SessionBrowser
        isOpen={showSessionBrowser}
        onClose={() => setShowSessionBrowser(false)}
        onSessionSelect={(sessionId) => {
          setCurrentSessionId(sessionId);
          setShowSessionBrowser(false);
          statusFeedback.showSuccess('Session Loaded', `Switched to session ${sessionId}`, 3000);
        }}
      />

      {/* Session History */}
      <SessionHistory
        isOpen={showSessionHistory}
        onClose={() => setShowSessionHistory(false)}
        onSessionSelect={(sessionId) => {
          setCurrentSessionId(sessionId);
          setShowSessionHistory(false);
          statusFeedback.showSuccess('Session Loaded', `Switched to session ${sessionId}`, 3000);
        }}
      />

      {/* Backup & Recovery */}
      <BackupRecovery
        isOpen={showBackupRecovery}
        onClose={() => setShowBackupRecovery(false)}
        onSessionRestore={(sessionId) => {
          setCurrentSessionId(sessionId);
          statusFeedback.showSuccess('Session Restored', `Session restored and loaded`, 4000);
        }}
        currentSessionId={currentSessionId}
      />

      {/* Import Wizard */}
      <ImportWizard
        isOpen={showImportWizard}
        onClose={() => setShowImportWizard(false)}
        onImportComplete={(sessionId, sessionName) => {
          setCurrentSessionId(sessionId);
          statusFeedback.showSuccess(
            'Import Complete!',
            `Successfully imported content as "${sessionName}". Session is now active.`,
            5000
          );
        }}
      />

      {/* Git Integration */}
      <GitIntegration
        isOpen={showGitIntegration}
        onClose={() => setShowGitIntegration(false)}
      />

      {/* Data Export Wizard */}
      <DataExportWizard
        isOpen={showDataExportWizard}
        onClose={() => setShowDataExportWizard(false)}
        onExportComplete={(result) => {
          statusFeedback.showSuccess(
            'Export Complete!',
            `Successfully exported ${result.sessions_exported} sessions. File saved to ${result.output_path}`,
            5000
          );
        }}
      />

      {/* Status Feedback */}
      <StatusFeedback
        messages={statusFeedback.messages}
        onDismiss={statusFeedback.dismissMessage}
        position="top-right"
        maxVisible={3}
      />
    </div>
  );
}

export default App;