import React, { useState, useEffect } from 'react';
import { useSettings, useUserProfile, useContentDefaults } from './contexts/SettingsContext';
import { SettingsPanel } from './components/SettingsPanel';
import { QuizType } from './types/settings';
import './App.css';

type AppMode = 'wizard' | 'expert';
type ContentType = 'Slides' | 'InstructorNotes' | 'Worksheet' | 'Quiz' | 'ActivityGuide';
type ExpertTab = 'planner' | 'templates' | 'batch' | 'quality';

function App() {
  const { state: settingsState } = useSettings();
  const [profile] = useUserProfile();
  const [defaults] = useContentDefaults();
  const [showSettings, setShowSettings] = useState(false);
  const [currentMode, setCurrentMode] = useState<AppMode>('wizard');
  const [currentStep, setCurrentStep] = useState(1);
  const [expertTab, setExpertTab] = useState<ExpertTab>('planner');
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
    }
  });
  const [aiGenerating, setAiGenerating] = useState(false);
  const [showObjectiveCountModal, setShowObjectiveCountModal] = useState(false);
  const [objectiveCount, setObjectiveCount] = useState(4);
  
  // Progressive disclosure state
  const [formComplexity, setFormComplexity] = useState<'essential' | 'enhanced' | 'advanced'>('essential');
  const [showAdvancedConfig, setShowAdvancedConfig] = useState(false);
  const [showExpertContentOptions, setShowExpertContentOptions] = useState(false);
  const [showAdvancedObjectives, setShowAdvancedObjectives] = useState(false);

  const handleModeSwitch = (mode: AppMode) => {
    setCurrentMode(mode);
    if (mode === 'wizard') {
      setCurrentStep(1);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
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
    if (currentStep < 5 && canProceed()) {
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
      case 3:
        const hasContentTypes = formData.contentTypes.length > 0;
        const hasQuizTypesIfNeeded = !formData.contentTypes.includes('Quiz') || formData.quizTypes.length > 0;
        return hasContentTypes && hasQuizTypesIfNeeded;
      case 4:
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
    } catch (error) {
      console.error('AI generation failed:', error);
      // Fall back gracefully - could show error message
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
              </label>
              <select
                value={formData.duration}
                onChange={(e) => handleInputChange('duration', e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  fontSize: '16px',
                  backgroundColor: 'white'
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
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              {(['Slides', 'InstructorNotes', 'Worksheet', 'Quiz', 'ActivityGuide'] as ContentType[]).map((type) => (
                <div
                  key={type}
                  onClick={() => toggleContentType(type)}
                  style={{
                    padding: '20px',
                    border: `2px solid ${formData.contentTypes.includes(type) ? '#3b82f6' : '#e5e7eb'}`,
                    borderRadius: '12px',
                    cursor: 'pointer',
                    textAlign: 'center',
                    backgroundColor: formData.contentTypes.includes(type) ? '#dbeafe' : 'white',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{
                    width: '48px',
                    height: '48px',
                    margin: '0 auto 12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: formData.contentTypes.includes(type) ? '#3b82f6' : '#f1f5f9',
                    borderRadius: '12px',
                    color: formData.contentTypes.includes(type) ? 'white' : '#64748b',
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
                  </h3>
                  <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
                    {type === 'Slides' && 'Presentation slides with key points'}
                    {type === 'InstructorNotes' && 'Detailed teaching notes'}
                    {type === 'Worksheet' && 'Student practice exercises'}
                    {type === 'Quiz' && 'Assessment questions'}
                    {type === 'ActivityGuide' && 'Interactive learning activities'}
                  </p>
                </div>
              ))}
            </div>
            
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
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
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

      // Continue with cases 4 and 5 from original file...
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
            padding: '32px',
            maxWidth: '400px',
            width: '90%',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)'
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
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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
          
          <div style={{ 
            display: 'flex', 
            gap: '8px', 
            backgroundColor: '#f1f5f9', 
            padding: '4px', 
            borderRadius: '8px' 
          }}>
            <button
              onClick={() => handleModeSwitch('wizard')}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: currentMode === 'wizard' ? 'white' : 'transparent',
                color: currentMode === 'wizard' ? '#3b82f6' : '#64748b',
                cursor: 'pointer'
              }}
            >
              Wizard Mode
            </button>
            <button
              onClick={() => handleModeSwitch('expert')}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: currentMode === 'expert' ? 'white' : 'transparent',
                color: currentMode === 'expert' ? '#3b82f6' : '#64748b',
                cursor: 'pointer'
              }}
            >
              Expert Mode
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ 
        padding: '24px', 
        backgroundColor: '#f8fafc', 
        flex: 1,
        minHeight: 'calc(100vh - 80px)',
        overflow: 'auto'
      }}>
        {currentMode === 'wizard' ? (
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            {/* Progress Indicator */}
            <div style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
                <div style={{ flex: 1, height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ 
                    height: '100%', 
                    backgroundColor: '#3b82f6', 
                    width: `${(currentStep / 5) * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <span style={{ fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
                  Step {currentStep} of 5
                </span>
              </div>
            </div>

            {/* Step Content */}
            <div style={{ 
              backgroundColor: 'white', 
              padding: '32px', 
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              marginBottom: '24px'
            }}>
              {renderWizardStep()}
            </div>

            {/* Navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {currentStep > 1 && currentStep < 5 ? (
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
              
              {currentStep < 4 && (
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
                  Next →
                </button>
              )}
              
              {currentStep === 4 && (
                <button
                  onClick={nextStep}
                  style={{
                    padding: '12px 24px',
                    border: 'none',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                >
                  Review →
                </button>
              )}
            </div>
          </div>
        ) : (
          <div>Expert Mode - Coming Soon</div>
        )}
      </main>
      
      {/* Settings Panel */}
      <SettingsPanel isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
}

export default App;