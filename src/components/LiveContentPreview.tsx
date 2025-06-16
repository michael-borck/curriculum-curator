// Live Content Preview Component

import React, { useState, useEffect } from 'react';
import type { ContentType, QuizType, AnswerKeyOptions, InstructorGuideOptions, AIContentOptions } from '../types/settings';

interface FormData {
  topic: string;
  audience: string;
  subject: string;
  duration: string;
  complexity: string;
  learningObjectives: string[];
  contentTypes: ContentType[];
  quizTypes: QuizType[];
  includeAnswerKeys: boolean;
  includeInstructorGuides: boolean;
  accessibility: boolean;
  rubrics: boolean;
  extensions: boolean;
  answerKeyOptions: AnswerKeyOptions;
  instructorGuideOptions: InstructorGuideOptions;
  aiEnhancements: Record<ContentType, AIContentOptions>;
}

interface LiveContentPreviewProps {
  formData: FormData;
  currentStep: number;
  isVisible: boolean;
  onToggleVisibility: () => void;
  width?: number;
  onWidthChange?: (width: number) => void;
}

const CONTENT_TYPE_ICONS: Record<ContentType, string> = {
  'Slides': '📊',
  'InstructorNotes': '📝',
  'Worksheet': '📄',
  'Quiz': '❓',
  'ActivityGuide': '👥',
  'Custom': '⚙️'
};

const COMPLEXITY_COLORS = {
  'basic': '#22c55e',
  'intermediate': '#f59e0b', 
  'advanced': '#ef4444'
};

export function LiveContentPreview({ 
  formData, 
  currentStep, 
  isVisible, 
  onToggleVisibility, 
  width = 400, 
  onWidthChange 
}: LiveContentPreviewProps) {
  const [previewContent, setPreviewContent] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewWidth, setPreviewWidth] = useState(width);
  const [isResizing, setIsResizing] = useState(false);

  // Generate preview content when form data changes
  useEffect(() => {
    const generatePreview = async () => {
      setIsGenerating(true);
      
      // Simulate content generation delay
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const preview = generateContentPreview(formData, currentStep);
      setPreviewContent(preview);
      setIsGenerating(false);
    };

    generatePreview();
  }, [formData, currentStep]);

  // Handle resize functionality
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = Math.max(300, Math.min(800, window.innerWidth - e.clientX));
      setPreviewWidth(newWidth);
      onWidthChange?.(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const generateContentPreview = (data: FormData, step: number): string => {
    if (step === 1) {
      // Basic Info Preview
      return `# ${data.topic || '[Topic Title]'}

**Target Audience:** ${data.audience || '[Audience Description]'}
**Subject Area:** ${data.subject || '[Subject]'}
**Duration:** ${data.duration}
**Complexity Level:** ${data.complexity}

---
*Preview will expand as you complete more steps...*`;
    }

    if (step === 2) {
      // Learning Objectives Preview
      const objectives = data.learningObjectives.filter(obj => obj.trim());
      return `# ${data.topic}

**Target Audience:** ${data.audience}
**Duration:** ${data.duration} | **Complexity:** ${data.complexity}

## Learning Objectives
By the end of this session, students will be able to:

${objectives.length > 0 
  ? objectives.map((obj, idx) => `${idx + 1}. ${obj}`).join('\n')
  : '*No learning objectives defined yet*'
}

---
*Content structure will appear as you select content types...*`;
    }

    if (step >= 3) {
      // Full Content Structure Preview
      const objectives = data.learningObjectives.filter(obj => obj.trim());
      const hasQuiz = data.contentTypes.includes('Quiz');
      
      let preview = `# ${data.topic}

**Target Audience:** ${data.audience}
**Duration:** ${data.duration} | **Complexity:** ${data.complexity}
**Subject:** ${data.subject}

## Learning Objectives
${objectives.length > 0 
  ? objectives.map((obj, idx) => `${idx + 1}. ${obj}`).join('\n')
  : '*Learning objectives will be generated*'
}

## Content Structure
`;

      // Add content type sections
      data.contentTypes.forEach(contentType => {
        const icon = CONTENT_TYPE_ICONS[contentType];
        preview += `\n### ${icon} ${contentType.replace(/([A-Z])/g, ' $1').trim()}
`;
        
        switch (contentType) {
          case 'Slides':
            preview += `- Introduction slide with objectives
- ${Math.ceil(objectives.length / 2)} main content slides
- Interactive elements and examples
- Summary and next steps slide
`;
            if (data.aiEnhancements[contentType]?.enableInteractionPrompts) {
              preview += `- **AI Enhancement:** Interactive prompts and engagement activities\n`;
            }
            break;
            
          case 'InstructorNotes':
            preview += `- Detailed teaching notes for each section
- Timing guidance (${data.duration} total)
- Key points to emphasize
- Potential student questions and responses
`;
            if (data.includeInstructorGuides && data.instructorGuideOptions.includeTiming) {
              preview += `- **Enhanced:** Section timing breakdown\n`;
            }
            if (data.includeInstructorGuides && data.instructorGuideOptions.includeGradingTips) {
              preview += `- **Enhanced:** Assessment and grading guidance\n`;
            }
            break;
            
          case 'Worksheet':
            preview += `- Practice problems aligned with objectives
- Skill-building exercises
- Real-world application scenarios
`;
            if (data.aiEnhancements[contentType]?.includeBrainstormingActivities) {
              preview += `- **AI Enhancement:** Collaborative brainstorming sections\n`;
            }
            if (data.aiEnhancements[contentType]?.createResistantAlternatives) {
              preview += `- **AI Enhancement:** Process-focused, AI-resistant problems\n`;
            }
            break;
            
          case 'Quiz':
            const quizTypesList = data.quizTypes.length > 0 ? data.quizTypes.join(', ') : 'multiple-choice';
            preview += `- Question types: ${quizTypesList}
- ${Math.max(5, objectives.length * 2)} questions total
- Aligned with learning objectives
`;
            if (data.includeAnswerKeys) {
              preview += `- **Answer Key Included**\n`;
              if (data.answerKeyOptions.includeExplanations) {
                preview += `  - Detailed explanations for each answer\n`;
              }
              if (data.answerKeyOptions.includeDifficulty) {
                preview += `  - Question difficulty levels marked\n`;
              }
              if (data.answerKeyOptions.includePoints) {
                preview += `  - Suggested point values\n`;
              }
            }
            break;
            
          case 'ActivityGuide':
            preview += `- Group activities and exercises
- Individual reflection prompts
- Collaborative learning opportunities
`;
            if (data.aiEnhancements[contentType]?.enableInteractionPrompts) {
              preview += `- **AI Enhancement:** Dynamic interaction prompts\n`;
            }
            if (data.aiEnhancements[contentType]?.addLiteracyComponents) {
              preview += `- **AI Enhancement:** AI literacy integration\n`;
            }
            break;
            
          default:
            preview += `- Custom content structure
- Tailored to specific requirements
`;
        }
      });

      // Add additional features
      if (data.accessibility) {
        preview += `\n## Accessibility Features
- Screen reader compatible formatting
- Alternative text for images
- Clear heading structure
- High contrast color schemes
`;
      }

      if (data.rubrics) {
        preview += `\n## Assessment Rubrics
- Clear evaluation criteria
- Performance level descriptions
- Aligned with learning objectives
`;
      }

      if (data.extensions) {
        preview += `\n## Extension Activities
- Advanced challenges for early finishers
- Additional practice opportunities
- Real-world application projects
`;
      }

      // Add generation status
      preview += `\n---
**Content Generation Status:** Ready to generate
**Estimated Generation Time:** ${getEstimatedTime(data.contentTypes.length)} minutes
**Total Deliverables:** ${getTotalDeliverables(data)} files
`;

      return preview;
    }

    return 'Preview will be available as you complete the wizard steps...';
  };

  const getEstimatedTime = (contentTypeCount: number): number => {
    // Estimate based on content complexity
    const baseTime = 2; // 2 minutes base
    const perContentType = 1.5; // 1.5 minutes per content type
    const complexityMultiplier = formData.complexity === 'advanced' ? 1.5 : 
                                 formData.complexity === 'basic' ? 0.8 : 1.0;
    
    return Math.ceil((baseTime + (contentTypeCount * perContentType)) * complexityMultiplier);
  };

  const getTotalDeliverables = (data: FormData): number => {
    let count = data.contentTypes.length;
    
    if (data.includeAnswerKeys && data.contentTypes.includes('Quiz')) count++;
    if (data.includeInstructorGuides) count++;
    if (data.rubrics) count++;
    
    return count;
  };

  const getCompletionPercentage = (): number => {
    let completed = 0;
    const total = 5; // Total steps
    
    if (formData.topic.trim() && formData.audience.trim()) completed++;
    if (formData.learningObjectives.some(obj => obj.trim())) completed++;
    if (formData.contentTypes.length > 0) completed++;
    if (currentStep >= 4) completed++; // AI enhancements step
    if (currentStep >= 5) completed++; // Review step
    
    return Math.round((completed / total) * 100);
  };

  const getContentTypeColor = (type: ContentType): string => {
    const colors: Record<ContentType, string> = {
      'Slides': '#3b82f6',
      'InstructorNotes': '#059669',
      'Worksheet': '#f59e0b',
      'Quiz': '#dc2626',
      'ActivityGuide': '#8b5cf6',
      'Custom': '#64748b'
    };
    return colors[type] || '#64748b';
  };

  if (!isVisible) {
    return (
      <button
        onClick={onToggleVisibility}
        style={{
          position: 'fixed',
          right: '24px',
          top: '50%',
          transform: 'translateY(-50%)',
          zIndex: 1000,
          padding: '12px',
          backgroundColor: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px 0 0 8px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '500',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          writingMode: 'vertical-rl',
          textOrientation: 'mixed'
        }}
      >
        👁️ Preview
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed',
      right: 0,
      top: 0,
      bottom: 0,
      width: `${previewWidth}px`,
      backgroundColor: 'white',
      borderLeft: '1px solid #e5e7eb',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '-4px 0 6px rgba(0, 0, 0, 0.1)'
    }}>
      {/* Resize Handle */}
      <div
        onMouseDown={() => setIsResizing(true)}
        style={{
          position: 'absolute',
          left: '-4px',
          top: 0,
          bottom: 0,
          width: '8px',
          cursor: 'col-resize',
          backgroundColor: 'transparent',
          zIndex: 1001
        }}
        title="Drag to resize preview panel"
      />
      <div
        style={{
          position: 'absolute',
          left: '-1px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '2px',
          height: '40px',
          backgroundColor: '#3b82f6',
          borderRadius: '1px',
          opacity: isResizing ? 1 : 0.3,
          transition: 'opacity 0.2s ease'
        }}
      />
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#f8fafc'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <h3 style={{
            margin: 0,
            fontSize: '16px',
            fontWeight: '600',
            color: '#1e293b'
          }}>
            👁️ Live Preview
          </h3>
          <button
            onClick={onToggleVisibility}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '18px',
              cursor: 'pointer',
              color: '#64748b',
              padding: '4px'
            }}
          >
            ×
          </button>
        </div>

        {/* Progress Indicator */}
        <div style={{ marginBottom: '12px' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '6px'
          }}>
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              Step {currentStep} of 5
            </span>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#3b82f6' }}>
              {getCompletionPercentage()}% Complete
            </span>
          </div>
          <div style={{
            width: '100%',
            height: '4px',
            backgroundColor: '#e5e7eb',
            borderRadius: '2px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${getCompletionPercentage()}%`,
              height: '100%',
              backgroundColor: '#3b82f6',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* Content Types Summary */}
        {formData.contentTypes.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {formData.contentTypes.map(type => (
              <span
                key={type}
                style={{
                  padding: '2px 6px',
                  backgroundColor: getContentTypeColor(type),
                  color: 'white',
                  borderRadius: '4px',
                  fontSize: '10px',
                  fontWeight: '500'
                }}
              >
                {CONTENT_TYPE_ICONS[type]} {type}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '16px'
      }}>
        {isGenerating ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100px',
            color: '#64748b'
          }}>
            <div style={{
              animation: 'spin 1s linear infinite',
              marginRight: '8px'
            }}>
              ⏳
            </div>
            Updating preview...
          </div>
        ) : (
          <div style={{
            fontSize: '13px',
            lineHeight: '1.5',
            color: '#374151',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap'
          }}>
            {previewContent}
          </div>
        )}
      </div>

      {/* Footer */}
      {currentStep >= 3 && formData.contentTypes.length > 0 && (
        <div style={{
          padding: '16px',
          borderTop: '1px solid #e5e7eb',
          backgroundColor: '#f8fafc'
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '12px',
            fontSize: '12px'
          }}>
            <div>
              <div style={{ fontWeight: '600', color: '#1e293b', marginBottom: '4px' }}>
                Deliverables
              </div>
              <div style={{ color: '#64748b' }}>
                {getTotalDeliverables(formData)} files
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '600', color: '#1e293b', marginBottom: '4px' }}>
                Est. Time
              </div>
              <div style={{ color: '#64748b' }}>
                {getEstimatedTime(formData.contentTypes.length)}m
              </div>
            </div>
          </div>
        </div>
      )}

      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}