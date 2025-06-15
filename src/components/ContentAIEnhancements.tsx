// Content-Specific AI Enhancement Options Component

import React, { useState, useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import type { ContentType, AIContentOptions, CustomContentType } from '../types/settings';

interface ContentAIEnhancementsProps {
  selectedContentTypes: ContentType[];
  customContentTypes?: CustomContentType[];
  onEnhancementsChange: (enhancements: Record<ContentType, AIContentOptions>) => void;
  disabled?: boolean;
}

interface ContentTypeInfo {
  name: string;
  description: string;
  icon: string;
  aiCapabilities: {
    interaction: string;
    brainstorming: string;
    tools: string;
    resistance: string;
    literacy: string;
  };
}

const CONTENT_TYPE_INFO: Record<ContentType, ContentTypeInfo> = {
  'Slides': {
    name: 'Presentation Slides',
    description: 'Interactive lecture materials with visual aids',
    icon: '📽️',
    aiCapabilities: {
      interaction: 'Add discussion prompts and audience engagement cues',
      brainstorming: 'Include collaborative thinking exercises',
      tools: 'Suggest presentation tools and interactive platforms',
      resistance: 'Create alternative non-digital activities',
      literacy: 'Add AI awareness and digital citizenship content'
    }
  },
  'InstructorNotes': {
    name: 'Instructor Notes',
    description: 'Teaching guides and lesson planning materials',
    icon: '📋',
    aiCapabilities: {
      interaction: 'Include facilitation prompts and timing cues',
      brainstorming: 'Add ideation activities for instructor preparation',
      tools: 'Recommend teaching tools and classroom management apps',
      resistance: 'Emphasize human-centered teaching approaches',
      literacy: 'Include AI pedagogy and ethical considerations'
    }
  },
  'Worksheet': {
    name: 'Student Worksheets',
    description: 'Practice exercises and problem-solving activities',
    icon: '📝',
    aiCapabilities: {
      interaction: 'Add peer collaboration and discussion prompts',
      brainstorming: 'Include creative problem-solving exercises',
      tools: 'Suggest student-friendly AI tools for research',
      resistance: 'Create process-focused, hands-on alternatives',
      literacy: 'Teach responsible AI use and fact-checking'
    }
  },
  'Quiz': {
    name: 'Assessments & Quizzes',
    description: 'Evaluation tools and knowledge checks',
    icon: '✅',
    aiCapabilities: {
      interaction: 'Add reflection questions and peer review',
      brainstorming: 'Include open-ended creative responses',
      tools: 'Recommend assessment and feedback platforms',
      resistance: 'Design AI-resistant question types',
      literacy: 'Assess AI literacy and ethical understanding'
    }
  },
  'ActivityGuide': {
    name: 'Activity Guides',
    description: 'Structured learning experiences and group work',
    icon: '🎯',
    aiCapabilities: {
      interaction: 'Design collaborative and discussion-based activities',
      brainstorming: 'Include ideation and creative thinking exercises',
      tools: 'Suggest collaboration tools and platforms',
      resistance: 'Focus on human interaction and teamwork',
      literacy: 'Integrate AI ethics discussions and scenarios'
    }
  },
  'Custom': {
    name: 'Custom Content',
    description: 'Flexible content tailored to specific needs',
    icon: '🔧',
    aiCapabilities: {
      interaction: 'Customizable interaction patterns',
      brainstorming: 'Flexible ideation approaches',
      tools: 'Context-appropriate tool suggestions',
      resistance: 'Adaptable resistance strategies',
      literacy: 'Targeted AI literacy components'
    }
  }
};

export function ContentAIEnhancements({ selectedContentTypes, customContentTypes = [], onEnhancementsChange, disabled = false }: ContentAIEnhancementsProps) {
  const { state } = useSettings();
  const [enhancements, setEnhancements] = useState<Record<ContentType, AIContentOptions>>({} as Record<ContentType, AIContentOptions>);
  const [expandedTypes, setExpandedTypes] = useState<Set<ContentType>>(new Set());

  // Initialize with existing AI customization settings or defaults
  useEffect(() => {
    const initialEnhancements: Record<ContentType, AIContentOptions> = {} as Record<ContentType, AIContentOptions>;
    
    selectedContentTypes.forEach(contentType => {
      const existingOptions = state.settings?.advanced.aiCustomization?.contentSpecificOptions?.[contentType];
      initialEnhancements[contentType] = existingOptions || {
        enableInteractionPrompts: false,
        includeBrainstormingActivities: false,
        suggestAITools: false,
        createResistantAlternatives: false,
        addLiteracyComponents: false
      };
    });
    
    setEnhancements(initialEnhancements);
    onEnhancementsChange(initialEnhancements);
  }, [selectedContentTypes, state.settings]);

  const updateEnhancement = (contentType: ContentType, option: keyof AIContentOptions, value: boolean) => {
    const newEnhancements = {
      ...enhancements,
      [contentType]: {
        ...enhancements[contentType],
        [option]: value
      }
    };
    setEnhancements(newEnhancements);
    onEnhancementsChange(newEnhancements);
  };

  const toggleExpanded = (contentType: ContentType) => {
    const newExpanded = new Set(expandedTypes);
    if (newExpanded.has(contentType)) {
      newExpanded.delete(contentType);
    } else {
      newExpanded.add(contentType);
    }
    setExpandedTypes(newExpanded);
  };

  const getEnhancementCount = (contentType: ContentType): number => {
    const options = enhancements[contentType];
    if (!options) return 0;
    return Object.values(options).filter(Boolean).length;
  };

  const getContentTypeInfo = (contentType: ContentType): ContentTypeInfo => {
    // Check if it's a standard content type
    if (CONTENT_TYPE_INFO[contentType]) {
      return CONTENT_TYPE_INFO[contentType];
    }
    
    // Check if it's a custom content type
    const customType = customContentTypes.find(ct => ct.name === contentType);
    if (customType) {
      return {
        name: customType.name,
        description: customType.description,
        icon: customType.icon,
        aiCapabilities: {
          interaction: 'Add discussion prompts and interaction elements',
          brainstorming: 'Include creative thinking exercises',
          tools: 'Suggest relevant tools and resources',
          resistance: 'Create non-AI dependent alternatives',
          literacy: 'Add AI awareness and ethics components'
        }
      };
    }
    
    // Fallback for unknown content types
    return {
      name: contentType,
      description: 'Custom content type',
      icon: '📄',
      aiCapabilities: {
        interaction: 'Add interaction and engagement elements',
        brainstorming: 'Include ideation activities',
        tools: 'Suggest helpful tools',
        resistance: 'Create traditional alternatives',
        literacy: 'Add AI literacy components'
      }
    };
  };

  if (selectedContentTypes.length === 0) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        color: '#64748b',
        backgroundColor: '#f8fafc',
        borderRadius: '12px',
        border: '2px dashed #cbd5e1'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
        <h3 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>AI Enhancement Options</h3>
        <p style={{ margin: 0, fontSize: '14px' }}>
          Select content types in the previous step to configure AI enhancements
        </p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', margin: '0 0 8px 0', color: '#1e293b' }}>
          🤖 AI Enhancement Options
        </h3>
        <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
          Configure how AI will enhance each type of content you're creating. These options are based on your AI integration preferences.
        </p>
      </div>

      <div style={{ display: 'grid', gap: '16px' }}>
        {selectedContentTypes.map(contentType => {
          const info = getContentTypeInfo(contentType);
          const isExpanded = expandedTypes.has(contentType);
          const enhancementCount = getEnhancementCount(contentType);
          
          return (
            <div
              key={contentType}
              style={{
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                overflow: 'hidden',
                backgroundColor: 'white'
              }}
            >
              {/* Header */}
              <div
                onClick={() => !disabled && toggleExpanded(contentType)}
                style={{
                  padding: '16px 20px',
                  backgroundColor: isExpanded ? '#f0f9ff' : '#f8fafc',
                  borderBottom: isExpanded ? '1px solid #e2e8f0' : 'none',
                  cursor: disabled ? 'default' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '24px' }}>{info.icon}</span>
                  <div>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
                      {info.name}
                    </h4>
                    <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
                      {info.description}
                    </p>
                  </div>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {enhancementCount > 0 && (
                    <span style={{
                      backgroundColor: '#dbeafe',
                      color: '#1e40af',
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500'
                    }}>
                      {enhancementCount} enhancement{enhancementCount !== 1 ? 's' : ''}
                    </span>
                  )}
                  <span style={{
                    fontSize: '18px',
                    color: '#64748b',
                    transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.2s'
                  }}>
                    ▼
                  </span>
                </div>
              </div>

              {/* Options */}
              {isExpanded && (
                <div style={{ padding: '20px' }}>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: disabled ? 'default' : 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={enhancements[contentType]?.enableInteractionPrompts ?? false}
                        onChange={(e) => !disabled && updateEnhancement(contentType, 'enableInteractionPrompts', e.target.checked)}
                        disabled={disabled}
                        style={{ marginTop: '4px', width: '16px', height: '16px' }}
                      />
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>
                          💬 Enable Interaction Prompts
                        </div>
                        <div style={{ fontSize: '13px', color: '#6b7280' }}>
                          {info.aiCapabilities.interaction}
                        </div>
                      </div>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: disabled ? 'default' : 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={enhancements[contentType]?.includeBrainstormingActivities ?? false}
                        onChange={(e) => !disabled && updateEnhancement(contentType, 'includeBrainstormingActivities', e.target.checked)}
                        disabled={disabled}
                        style={{ marginTop: '4px', width: '16px', height: '16px' }}
                      />
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>
                          💡 Include Brainstorming Activities
                        </div>
                        <div style={{ fontSize: '13px', color: '#6b7280' }}>
                          {info.aiCapabilities.brainstorming}
                        </div>
                      </div>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: disabled ? 'default' : 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={enhancements[contentType]?.suggestAITools ?? false}
                        onChange={(e) => !disabled && updateEnhancement(contentType, 'suggestAITools', e.target.checked)}
                        disabled={disabled}
                        style={{ marginTop: '4px', width: '16px', height: '16px' }}
                      />
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>
                          🔧 Suggest AI Tools
                        </div>
                        <div style={{ fontSize: '13px', color: '#6b7280' }}>
                          {info.aiCapabilities.tools}
                        </div>
                      </div>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: disabled ? 'default' : 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={enhancements[contentType]?.createResistantAlternatives ?? false}
                        onChange={(e) => !disabled && updateEnhancement(contentType, 'createResistantAlternatives', e.target.checked)}
                        disabled={disabled}
                        style={{ marginTop: '4px', width: '16px', height: '16px' }}
                      />
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>
                          🛡️ Create AI-Resistant Alternatives
                        </div>
                        <div style={{ fontSize: '13px', color: '#6b7280' }}>
                          {info.aiCapabilities.resistance}
                        </div>
                      </div>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: disabled ? 'default' : 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={enhancements[contentType]?.addLiteracyComponents ?? false}
                        onChange={(e) => !disabled && updateEnhancement(contentType, 'addLiteracyComponents', e.target.checked)}
                        disabled={disabled}
                        style={{ marginTop: '4px', width: '16px', height: '16px' }}
                      />
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>
                          📚 Add AI Literacy Components
                        </div>
                        <div style={{ fontSize: '13px', color: '#6b7280' }}>
                          {info.aiCapabilities.literacy}
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {selectedContentTypes.length > 0 && (
        <div style={{
          marginTop: '20px',
          padding: '16px',
          backgroundColor: '#f0f9ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span style={{ color: '#1e40af', fontSize: '16px' }}>💡</span>
            <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#1e40af' }}>
              AI Enhancement Tips
            </h4>
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#1e40af' }}>
            <li>Enable options that align with your teaching philosophy and AI integration preference</li>
            <li>Consider your students' digital literacy levels when choosing AI tool suggestions</li>
            <li>AI-resistant alternatives help maintain academic integrity while teaching critical thinking</li>
            <li>Literacy components prepare students for an AI-integrated future</li>
          </ul>
        </div>
      )}
    </div>
  );
}