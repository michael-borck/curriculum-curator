// AI Integration Preference Configuration Wizard

import React, { useState, useEffect } from 'react';
import { useUserProfile, useSettings } from '../contexts/SettingsContext';
import type { 
  AIIntegrationPreference, 
  AICustomizationSettings, 
  AIContentOptions, 
  AIPromptSettings, 
  AIResistanceStrategy,
  ContentType 
} from '../types/settings';

interface AIIntegrationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (preferences: AICustomizationSettings) => void;
}

interface AIPreferenceProfile {
  preference: AIIntegrationPreference;
  title: string;
  description: string;
  icon: string;
  benefits: string[];
  concerns: string[];
  recommendedFor: string[];
}

const AI_PREFERENCE_PROFILES: AIPreferenceProfile[] = [
  {
    preference: 'ai-enhanced',
    title: 'AI-Enhanced Teaching',
    description: 'Leverage AI to create more engaging and personalized learning experiences',
    icon: '🚀',
    benefits: [
      'Personalized content adaptation',
      'Interactive learning activities',
      'Automated differentiation',
      'Time-saving content generation'
    ],
    concerns: [
      'Student dependency on AI tools',
      'Need for digital literacy skills',
      'Authenticity of student work'
    ],
    recommendedFor: [
      'Tech-savvy educators',
      'Large class sizes',
      'Differentiated instruction needs',
      'Time-constrained environments'
    ]
  },
  {
    preference: 'ai-resistant',
    title: 'AI-Resistant Focus',
    description: 'Emphasize traditional teaching methods and critical thinking without AI dependency',
    icon: '🛡️',
    benefits: [
      'Authentic human interaction',
      'Deep critical thinking skills',
      'Traditional pedagogical methods',
      'Reduced technology dependency'
    ],
    concerns: [
      'Students may still encounter AI elsewhere',
      'Missing efficiency opportunities',
      'Potential disconnect with modern tools'
    ],
    recommendedFor: [
      'Humanities educators',
      'Philosophy and ethics courses',
      'Writing-intensive subjects',
      'Traditional academic settings'
    ]
  },
  {
    preference: 'ai-literate',
    title: 'AI Literacy Education',
    description: 'Teach students about AI while using it as a learning tool',
    icon: '🎓',
    benefits: [
      'Digital citizenship skills',
      'Understanding AI capabilities/limitations',
      'Ethical AI use education',
      'Future-ready skill development'
    ],
    concerns: [
      'Complex curriculum integration',
      'Need for educator AI knowledge',
      'Rapid technology changes'
    ],
    recommendedFor: [
      'Computer science educators',
      'STEM subjects',
      'Professional development',
      'College-level courses'
    ]
  },
  {
    preference: 'mixed-approach',
    title: 'Balanced Integration',
    description: 'Strategic combination of AI-enhanced and traditional teaching methods',
    icon: '⚖️',
    benefits: [
      'Flexibility in teaching methods',
      'Best of both approaches',
      'Adaptable to different topics',
      'Reduced polarization'
    ],
    concerns: [
      'Complexity in implementation',
      'Need for clear guidelines',
      'Potential inconsistency'
    ],
    recommendedFor: [
      'Experienced educators',
      'Diverse subject areas',
      'Mixed student populations',
      'Experimental teaching'
    ]
  },
  {
    preference: 'context-dependent',
    title: 'Context-Dependent Use',
    description: 'AI integration varies based on specific learning objectives and contexts',
    icon: '🎯',
    benefits: [
      'Highly targeted AI use',
      'Context-appropriate tools',
      'Flexible implementation',
      'Learning objective alignment'
    ],
    concerns: [
      'Complex decision-making',
      'Requires deep AI understanding',
      'Inconsistent student experience'
    ],
    recommendedFor: [
      'Advanced practitioners',
      'Research-based teaching',
      'Graduate-level instruction',
      'Professional training'
    ]
  }
];

const CONTENT_TYPE_DESCRIPTIONS: Record<ContentType, {name: string; aiUseCase: string}> = {
  'Slides': {
    name: 'Presentation Slides',
    aiUseCase: 'Visual design, content summarization, interactive elements'
  },
  'InstructorNotes': {
    name: 'Instructor Notes',
    aiUseCase: 'Teaching tips, timing guidance, discussion prompts'
  },
  'Worksheet': {
    name: 'Student Worksheets',
    aiUseCase: 'Problem generation, scaffolding, differentiation'
  },
  'Quiz': {
    name: 'Assessments & Quizzes',
    aiUseCase: 'Question generation, answer keys, rubrics'
  },
  'ActivityGuide': {
    name: 'Activity Guides',
    aiUseCase: 'Collaborative tasks, engagement strategies, facilitation'
  },
  'Custom': {
    name: 'Custom Content',
    aiUseCase: 'Flexible AI integration based on content type'
  }
};

export function AIIntegrationWizard({ isOpen, onClose, onComplete }: AIIntegrationWizardProps) {
  const [, updateProfile] = useUserProfile();
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedPreference, setSelectedPreference] = useState<AIIntegrationPreference | null>(null);
  const [contentOptions, setContentOptions] = useState<Record<ContentType, AIContentOptions>>({
    'Slides': {
      enableInteractionPrompts: true,
      includeBrainstormingActivities: false,
      suggestAITools: true,
      createResistantAlternatives: false,
      addLiteracyComponents: false
    },
    'InstructorNotes': {
      enableInteractionPrompts: false,
      includeBrainstormingActivities: false,
      suggestAITools: false,
      createResistantAlternatives: false,
      addLiteracyComponents: false
    },
    'Worksheet': {
      enableInteractionPrompts: false,
      includeBrainstormingActivities: true,
      suggestAITools: false,
      createResistantAlternatives: true,
      addLiteracyComponents: false
    },
    'Quiz': {
      enableInteractionPrompts: false,
      includeBrainstormingActivities: false,
      suggestAITools: false,
      createResistantAlternatives: true,
      addLiteracyComponents: true
    },
    'ActivityGuide': {
      enableInteractionPrompts: true,
      includeBrainstormingActivities: true,
      suggestAITools: true,
      createResistantAlternatives: false,
      addLiteracyComponents: true
    },
    'Custom': {
      enableInteractionPrompts: false,
      includeBrainstormingActivities: false,
      suggestAITools: false,
      createResistantAlternatives: false,
      addLiteracyComponents: false
    }
  });
  const [promptSettings, setPromptSettings] = useState<AIPromptSettings>({
    customPrompts: {},
    promptStyle: 'detailed',
    includeExamples: true,
    adaptToAudience: true
  });
  const [resistanceStrategies, setResistanceStrategies] = useState<AIResistanceStrategy[]>([]);

  useEffect(() => {
    if (selectedPreference) {
      // Auto-configure based on preference
      applyPreferenceDefaults(selectedPreference);
    }
  }, [selectedPreference]);

  const applyPreferenceDefaults = (preference: AIIntegrationPreference) => {
    switch (preference) {
      case 'ai-enhanced':
        setContentOptions(prev => ({
          ...prev,
          'Slides': { ...prev['Slides'], enableInteractionPrompts: true, suggestAITools: true },
          'Worksheet': { ...prev['Worksheet'], includeBrainstormingActivities: true },
          'ActivityGuide': { ...prev['ActivityGuide'], enableInteractionPrompts: true, suggestAITools: true }
        }));
        setPromptSettings(prev => ({ ...prev, promptStyle: 'creative', includeExamples: true }));
        setResistanceStrategies([]);
        break;

      case 'ai-resistant':
        setContentOptions(prev => Object.fromEntries(
          Object.entries(prev).map(([key, value]) => [
            key,
            { ...value, createResistantAlternatives: true, suggestAITools: false, enableInteractionPrompts: false }
          ])
        ) as Record<ContentType, AIContentOptions>);
        setPromptSettings(prev => ({ ...prev, promptStyle: 'academic', includeExamples: false }));
        setResistanceStrategies(['process-focused', 'authentic-context', 'collaborative-elements']);
        break;

      case 'ai-literate':
        setContentOptions(prev => Object.fromEntries(
          Object.entries(prev).map(([key, value]) => [
            key,
            { ...value, addLiteracyComponents: true, suggestAITools: true }
          ])
        ) as Record<ContentType, AIContentOptions>);
        setPromptSettings(prev => ({ ...prev, promptStyle: 'detailed', adaptToAudience: true }));
        setResistanceStrategies(['meta-cognitive']);
        break;

      case 'mixed-approach':
        // Keep defaults but enable flexibility
        setPromptSettings(prev => ({ ...prev, promptStyle: 'detailed', adaptToAudience: true }));
        setResistanceStrategies(['collaborative-elements']);
        break;

      case 'context-dependent':
        setPromptSettings(prev => ({ ...prev, promptStyle: 'academic', adaptToAudience: true }));
        setResistanceStrategies(['meta-cognitive', 'process-focused']);
        break;
    }
  };

  const updateContentOption = (contentType: ContentType, option: keyof AIContentOptions, value: boolean) => {
    setContentOptions(prev => ({
      ...prev,
      [contentType]: {
        ...prev[contentType],
        [option]: value
      }
    }));
  };

  const toggleResistanceStrategy = (strategy: AIResistanceStrategy) => {
    setResistanceStrategies(prev => 
      prev.includes(strategy) 
        ? prev.filter(s => s !== strategy)
        : [...prev, strategy]
    );
  };

  const handleComplete = () => {
    if (!selectedPreference) return;

    const aiCustomization: AICustomizationSettings = {
      contentSpecificOptions: contentOptions,
      promptCustomization: promptSettings,
      resistanceStrategies
    };

    // Update user profile
    updateProfile({ aiPreference: selectedPreference });
    
    onComplete(aiCustomization);
    onClose();
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return selectedPreference !== null;
      case 2:
      case 3:
        return true;
      default:
        return false;
    }
  };

  if (!isOpen) return null;

  return (
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
        maxWidth: '800px',
        width: '90%',
        maxHeight: '90%',
        overflow: 'hidden',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1e293b' }}>
            🤖 AI Integration Preferences
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#64748b'
            }}
          >
            ×
          </button>
        </div>

        {/* Progress */}
        <div style={{ padding: '16px 24px', backgroundColor: '#f8fafc' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <div style={{ flex: 1, height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                backgroundColor: '#3b82f6',
                width: `${(currentStep / 3) * 100}%`,
                transition: 'width 0.3s ease'
              }} />
            </div>
            <span style={{ fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
              Step {currentStep} of 3
            </span>
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '24px', overflow: 'auto', maxHeight: '60vh' }}>
          {currentStep === 1 && (
            <div>
              <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                Choose Your AI Integration Approach
              </h3>
              <p style={{ color: '#64748b', marginBottom: '24px', fontSize: '16px' }}>
                Select the approach that best aligns with your teaching philosophy and goals.
              </p>

              <div style={{ display: 'grid', gap: '16px' }}>
                {AI_PREFERENCE_PROFILES.map((preferenceProfile) => (
                  <div
                    key={preferenceProfile.preference}
                    onClick={() => setSelectedPreference(preferenceProfile.preference)}
                    style={{
                      padding: '20px',
                      border: `2px solid ${selectedPreference === preferenceProfile.preference ? '#3b82f6' : '#e5e7eb'}`,
                      borderRadius: '12px',
                      cursor: 'pointer',
                      backgroundColor: selectedPreference === preferenceProfile.preference ? '#dbeafe' : 'white',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                      <div style={{ fontSize: '32px' }}>{preferenceProfile.icon}</div>
                      <div style={{ flex: 1 }}>
                        <h4 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', margin: '0 0 8px 0' }}>
                          {preferenceProfile.title}
                        </h4>
                        <p style={{ fontSize: '14px', color: '#64748b', margin: '0 0 16px 0' }}>
                          {preferenceProfile.description}
                        </p>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '13px' }}>
                          <div>
                            <h5 style={{ color: '#059669', fontWeight: '600', margin: '0 0 8px 0' }}>✓ Benefits:</h5>
                            <ul style={{ margin: 0, paddingLeft: '16px', color: '#64748b' }}>
                              {preferenceProfile.benefits.map((benefit, index) => (
                                <li key={index}>{benefit}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h5 style={{ color: '#dc2626', fontWeight: '600', margin: '0 0 8px 0' }}>⚠ Considerations:</h5>
                            <ul style={{ margin: 0, paddingLeft: '16px', color: '#64748b' }}>
                              {preferenceProfile.concerns.map((concern, index) => (
                                <li key={index}>{concern}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentStep === 2 && selectedPreference && (
            <div>
              <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                Content-Specific AI Settings
              </h3>
              <p style={{ color: '#64748b', marginBottom: '24px', fontSize: '16px' }}>
                Configure how AI is used for different types of content you create.
              </p>

              <div style={{ display: 'grid', gap: '20px' }}>
                {Object.entries(CONTENT_TYPE_DESCRIPTIONS).map(([contentType, info]) => (
                  <div
                    key={contentType}
                    style={{
                      padding: '20px',
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px'
                    }}
                  >
                    <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', margin: '0 0 8px 0' }}>
                      {info.name}
                    </h4>
                    <p style={{ fontSize: '14px', color: '#64748b', margin: '0 0 16px 0' }}>
                      AI Use Case: {info.aiUseCase}
                    </p>

                    <div style={{ display: 'grid', gap: '12px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={contentOptions[contentType as ContentType]?.enableInteractionPrompts ?? false}
                          onChange={(e) => updateContentOption(contentType as ContentType, 'enableInteractionPrompts', e.target.checked)}
                          style={{ width: '16px', height: '16px' }}
                        />
                        <span style={{ fontSize: '14px', color: '#374151' }}>
                          💬 Enable interaction prompts and discussion starters
                        </span>
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={contentOptions[contentType as ContentType]?.includeBrainstormingActivities ?? false}
                          onChange={(e) => updateContentOption(contentType as ContentType, 'includeBrainstormingActivities', e.target.checked)}
                          style={{ width: '16px', height: '16px' }}
                        />
                        <span style={{ fontSize: '14px', color: '#374151' }}>
                          💡 Include brainstorming and ideation activities
                        </span>
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={contentOptions[contentType as ContentType]?.suggestAITools ?? false}
                          onChange={(e) => updateContentOption(contentType as ContentType, 'suggestAITools', e.target.checked)}
                          style={{ width: '16px', height: '16px' }}
                        />
                        <span style={{ fontSize: '14px', color: '#374151' }}>
                          🔧 Suggest relevant AI tools for students
                        </span>
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={contentOptions[contentType as ContentType]?.createResistantAlternatives ?? false}
                          onChange={(e) => updateContentOption(contentType as ContentType, 'createResistantAlternatives', e.target.checked)}
                          style={{ width: '16px', height: '16px' }}
                        />
                        <span style={{ fontSize: '14px', color: '#374151' }}>
                          🛡️ Create AI-resistant alternative activities
                        </span>
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={contentOptions[contentType as ContentType]?.addLiteracyComponents ?? false}
                          onChange={(e) => updateContentOption(contentType as ContentType, 'addLiteracyComponents', e.target.checked)}
                          style={{ width: '16px', height: '16px' }}
                        />
                        <span style={{ fontSize: '14px', color: '#374151' }}>
                          📚 Add AI literacy and ethics components
                        </span>
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div>
              <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                Prompt Style & Resistance Strategies
              </h3>
              <p style={{ color: '#64748b', marginBottom: '24px', fontSize: '16px' }}>
                Fine-tune how AI generates content and handles potential misuse.
              </p>

              <div style={{ display: 'grid', gap: '24px' }}>
                {/* Prompt Settings */}
                <div style={{
                  padding: '20px',
                  backgroundColor: '#f0f9ff',
                  border: '1px solid #bfdbfe',
                  borderRadius: '12px'
                }}>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1e40af', margin: '0 0 16px 0' }}>
                    📝 Content Generation Style
                  </h4>

                  <div style={{ display: 'grid', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#1e40af' }}>
                        Writing Style
                      </label>
                      <select
                        value={promptSettings.promptStyle}
                        onChange={(e) => setPromptSettings(prev => ({ ...prev, promptStyle: e.target.value as 'direct' | 'guided' | 'exploratory' }))}
                        style={{
                          width: '100%',
                          padding: '12px',
                          border: '1px solid #bfdbfe',
                          borderRadius: '8px',
                          fontSize: '14px',
                          backgroundColor: 'white'
                        }}
                      >
                        <option value="concise">Concise - Brief, direct content</option>
                        <option value="detailed">Detailed - Comprehensive explanations</option>
                        <option value="creative">Creative - Engaging, imaginative content</option>
                        <option value="academic">Academic - Formal, scholarly tone</option>
                      </select>
                    </div>

                    <div style={{ display: 'grid', gap: '8px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={promptSettings.includeExamples}
                          onChange={(e) => setPromptSettings(prev => ({ ...prev, includeExamples: e.target.checked }))}
                          style={{ width: '16px', height: '16px' }}
                        />
                        <span style={{ fontSize: '14px', color: '#1e40af' }}>
                          Include concrete examples and illustrations
                        </span>
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={promptSettings.adaptToAudience}
                          onChange={(e) => setPromptSettings(prev => ({ ...prev, adaptToAudience: e.target.checked }))}
                          style={{ width: '16px', height: '16px' }}
                        />
                        <span style={{ fontSize: '14px', color: '#1e40af' }}>
                          Adapt language and complexity to target audience
                        </span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Resistance Strategies */}
                <div style={{
                  padding: '20px',
                  backgroundColor: '#fef3c7',
                  border: '1px solid #fbbf24',
                  borderRadius: '12px'
                }}>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#92400e', margin: '0 0 16px 0' }}>
                    🛡️ AI Resistance Strategies
                  </h4>
                  <p style={{ fontSize: '14px', color: '#92400e', marginBottom: '16px' }}>
                    Techniques to encourage original thinking and prevent over-reliance on AI.
                  </p>

                  <div style={{ display: 'grid', gap: '8px' }}>
                    {[
                      { strategy: 'process-focused', label: 'Process-Focused', desc: 'Emphasize thinking process over final answers' },
                      { strategy: 'authentic-context', label: 'Authentic Context', desc: 'Use real-world, personal experiences' },
                      { strategy: 'collaborative-elements', label: 'Collaborative Elements', desc: 'Require group discussion and consensus' },
                      { strategy: 'real-time-components', label: 'Real-Time Components', desc: 'Include live demonstration or presentation' },
                      { strategy: 'meta-cognitive', label: 'Meta-Cognitive', desc: 'Require reflection on thinking process' },
                      { strategy: 'hands-on-physical', label: 'Hands-On Physical', desc: 'Include physical manipulation or creation' }
                    ].map(({ strategy, label, desc }) => (
                      <label key={strategy} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={resistanceStrategies.includes(strategy as AIResistanceStrategy)}
                          onChange={() => toggleResistanceStrategy(strategy as AIResistanceStrategy)}
                          style={{ width: '16px', height: '16px', marginTop: '2px' }}
                        />
                        <div>
                          <span style={{ fontSize: '14px', color: '#92400e', fontWeight: '500' }}>
                            {label}
                          </span>
                          <div style={{ fontSize: '12px', color: '#b45309' }}>
                            {desc}
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '24px',
          borderTop: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <button
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              backgroundColor: currentStep === 1 ? '#f3f4f6' : 'white',
              color: currentStep === 1 ? '#9ca3af' : '#374151',
              borderRadius: '6px',
              cursor: currentStep === 1 ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            ← Previous
          </button>

          <div style={{ display: 'flex', gap: '12px' }}>
            {currentStep < 3 && (
              <button
                onClick={() => setCurrentStep(currentStep + 1)}
                disabled={!canProceed()}
                style={{
                  padding: '12px 24px',
                  border: 'none',
                  backgroundColor: canProceed() ? '#3b82f6' : '#9ca3af',
                  color: 'white',
                  borderRadius: '8px',
                  cursor: canProceed() ? 'pointer' : 'not-allowed',
                  fontSize: '16px',
                  fontWeight: '500'
                }}
              >
                Next →
              </button>
            )}
            
            {currentStep === 3 && (
              <button
                onClick={handleComplete}
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
                ✅ Apply Settings
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}