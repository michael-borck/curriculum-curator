// Teaching Style Detection Component

import React, { useState, useEffect } from 'react';
import { useUserProfile } from '../contexts/SettingsContext';
import { 
  TeachingStyle, 
  TeachingStyleIndicators, 
  TeachingStyleDetectionResult 
} from '../types/settings';

interface TeachingStyleDetectorProps {
  isOpen: boolean;
  onClose: () => void;
  onStyleDetected: (result: TeachingStyleDetectionResult) => void;
}

interface Question {
  id: string;
  text: string;
  options: {
    value: string;
    label: string;
    indicators: Partial<TeachingStyleIndicators>;
  }[];
}

const DETECTION_QUESTIONS: Question[] = [
  {
    id: 'classroom_structure',
    text: 'How do you prefer to structure your classroom sessions?',
    options: [
      {
        value: 'highly_structured',
        label: 'Highly structured with clear timeline and agenda',
        indicators: { structurePreference: 9, interactionLevel: 4 }
      },
      {
        value: 'flexible_framework',
        label: 'Flexible framework that adapts to student needs',
        indicators: { structurePreference: 6, studentCenteredApproach: 8 }
      },
      {
        value: 'student_driven',
        label: 'Student-driven with minimal predetermined structure',
        indicators: { structurePreference: 2, studentCenteredApproach: 9 }
      },
      {
        value: 'mixed_approach',
        label: 'Mix of structured and flexible elements',
        indicators: { structurePreference: 5, studentCenteredApproach: 6 }
      }
    ]
  },
  {
    id: 'student_interaction',
    text: 'How much do you encourage student interaction during lessons?',
    options: [
      {
        value: 'constant_interaction',
        label: 'Constant interaction and discussion throughout',
        indicators: { interactionLevel: 10, collaborationEmphasis: 9 }
      },
      {
        value: 'regular_interaction',
        label: 'Regular planned interaction points',
        indicators: { interactionLevel: 7, collaborationEmphasis: 6 }
      },
      {
        value: 'minimal_interaction',
        label: 'Minimal interaction, mostly lecture-based',
        indicators: { interactionLevel: 3, structurePreference: 8 }
      },
      {
        value: 'end_interaction',
        label: 'Interaction mainly at the end for Q&A',
        indicators: { interactionLevel: 4, structurePreference: 7 }
      }
    ]
  },
  {
    id: 'technology_use',
    text: 'How do you typically integrate technology in your teaching?',
    options: [
      {
        value: 'heavy_tech',
        label: 'Heavy use of digital tools and platforms',
        indicators: { technologyIntegration: 9, interactionLevel: 6 }
      },
      {
        value: 'balanced_tech',
        label: 'Balanced mix of digital and traditional methods',
        indicators: { technologyIntegration: 6, structurePreference: 5 }
      },
      {
        value: 'minimal_tech',
        label: 'Minimal technology, prefer traditional methods',
        indicators: { technologyIntegration: 2, structurePreference: 7 }
      },
      {
        value: 'student_tech',
        label: 'Students use technology for research and projects',
        indicators: { technologyIntegration: 7, studentCenteredApproach: 8 }
      }
    ]
  },
  {
    id: 'assessment_style',
    text: 'How do you prefer to assess student learning?',
    options: [
      {
        value: 'frequent_informal',
        label: 'Frequent informal checks and discussions',
        indicators: { assessmentFrequency: 'high', interactionLevel: 8 }
      },
      {
        value: 'project_based',
        label: 'Project-based and portfolio assessments',
        indicators: { assessmentFrequency: 'medium', studentCenteredApproach: 9 }
      },
      {
        value: 'traditional_tests',
        label: 'Traditional tests and quizzes',
        indicators: { assessmentFrequency: 'medium', structurePreference: 8 }
      },
      {
        value: 'peer_self',
        label: 'Peer and self-assessment opportunities',
        indicators: { assessmentFrequency: 'high', collaborationEmphasis: 9 }
      }
    ]
  },
  {
    id: 'learning_approach',
    text: 'What learning approach do you emphasize most?',
    options: [
      {
        value: 'constructivist',
        label: 'Students build knowledge through exploration',
        indicators: { studentCenteredApproach: 9, collaborationEmphasis: 7 }
      },
      {
        value: 'direct_instruction',
        label: 'Clear, step-by-step instruction and demonstration',
        indicators: { structurePreference: 9, interactionLevel: 4 }
      },
      {
        value: 'inquiry_based',
        label: 'Question-driven investigation and discovery',
        indicators: { studentCenteredApproach: 8, interactionLevel: 7 }
      },
      {
        value: 'collaborative',
        label: 'Group work and peer learning',
        indicators: { collaborationEmphasis: 10, interactionLevel: 9 }
      }
    ]
  }
];

const STYLE_MAPPINGS: Record<TeachingStyle, TeachingStyleIndicators> = {
  'traditional-lecture': {
    interactionLevel: 3,
    structurePreference: 9,
    studentCenteredApproach: 2,
    technologyIntegration: 3,
    assessmentFrequency: 'medium',
    collaborationEmphasis: 2
  },
  'constructivist': {
    interactionLevel: 8,
    structurePreference: 4,
    studentCenteredApproach: 9,
    technologyIntegration: 6,
    assessmentFrequency: 'high',
    collaborationEmphasis: 7
  },
  'direct-instruction': {
    interactionLevel: 4,
    structurePreference: 9,
    studentCenteredApproach: 3,
    technologyIntegration: 5,
    assessmentFrequency: 'medium',
    collaborationEmphasis: 3
  },
  'inquiry-based': {
    interactionLevel: 7,
    structurePreference: 3,
    studentCenteredApproach: 8,
    technologyIntegration: 7,
    assessmentFrequency: 'high',
    collaborationEmphasis: 6
  },
  'flipped-classroom': {
    interactionLevel: 8,
    structurePreference: 6,
    studentCenteredApproach: 7,
    technologyIntegration: 9,
    assessmentFrequency: 'high',
    collaborationEmphasis: 7
  },
  'project-based': {
    interactionLevel: 6,
    structurePreference: 4,
    studentCenteredApproach: 9,
    technologyIntegration: 7,
    assessmentFrequency: 'medium',
    collaborationEmphasis: 8
  },
  'competency-based': {
    interactionLevel: 6,
    structurePreference: 7,
    studentCenteredApproach: 7,
    technologyIntegration: 6,
    assessmentFrequency: 'high',
    collaborationEmphasis: 5
  },
  'culturally-responsive': {
    interactionLevel: 8,
    structurePreference: 5,
    studentCenteredApproach: 8,
    technologyIntegration: 6,
    assessmentFrequency: 'high',
    collaborationEmphasis: 8
  },
  'mixed-approach': {
    interactionLevel: 6,
    structurePreference: 6,
    studentCenteredApproach: 6,
    technologyIntegration: 6,
    assessmentFrequency: 'medium',
    collaborationEmphasis: 6
  }
};

export function TeachingStyleDetector({ isOpen, onClose, onStyleDetected }: TeachingStyleDetectorProps) {
  const [profile, updateProfile] = useUserProfile();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnswer = (questionId: string, optionValue: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionValue }));
  };

  const calculateStyleIndicators = (): TeachingStyleIndicators => {
    const indicators: TeachingStyleIndicators = {
      interactionLevel: 0,
      structurePreference: 0,
      studentCenteredApproach: 0,
      technologyIntegration: 0,
      assessmentFrequency: 'medium',
      collaborationEmphasis: 0
    };

    let assessmentCount = { low: 0, medium: 0, high: 0 };
    let totalQuestions = 0;

    Object.entries(answers).forEach(([questionId, answer]) => {
      const question = DETECTION_QUESTIONS.find(q => q.id === questionId);
      if (!question) return;

      const option = question.options.find(opt => opt.value === answer);
      if (!option) return;

      totalQuestions++;
      Object.entries(option.indicators).forEach(([key, value]) => {
        if (key === 'assessmentFrequency') {
          assessmentCount[value as keyof typeof assessmentCount]++;
        } else {
          (indicators as any)[key] += value as number;
        }
      });
    });

    // Average the numerical indicators
    if (totalQuestions > 0) {
      indicators.interactionLevel = Math.round(indicators.interactionLevel / totalQuestions);
      indicators.structurePreference = Math.round(indicators.structurePreference / totalQuestions);
      indicators.studentCenteredApproach = Math.round(indicators.studentCenteredApproach / totalQuestions);
      indicators.technologyIntegration = Math.round(indicators.technologyIntegration / totalQuestions);
      indicators.collaborationEmphasis = Math.round(indicators.collaborationEmphasis / totalQuestions);
    }

    // Determine assessment frequency
    const maxAssessment = Math.max(assessmentCount.low, assessmentCount.medium, assessmentCount.high);
    if (assessmentCount.high === maxAssessment) indicators.assessmentFrequency = 'high';
    else if (assessmentCount.low === maxAssessment) indicators.assessmentFrequency = 'low';
    else indicators.assessmentFrequency = 'medium';

    return indicators;
  };

  const findBestMatchingStyle = (userIndicators: TeachingStyleIndicators): TeachingStyleDetectionResult => {
    const scores: Record<TeachingStyle, number> = {} as any;

    Object.entries(STYLE_MAPPINGS).forEach(([style, styleIndicators]) => {
      let score = 0;
      let totalWeight = 0;

      // Compare numerical indicators (weighted)
      const weights = {
        interactionLevel: 2,
        structurePreference: 2,
        studentCenteredApproach: 3,
        technologyIntegration: 1.5,
        collaborationEmphasis: 2
      };

      Object.entries(weights).forEach(([indicator, weight]) => {
        const userValue = (userIndicators as any)[indicator];
        const styleValue = (styleIndicators as any)[indicator];
        const difference = Math.abs(userValue - styleValue);
        const maxDifference = 10; // max possible difference
        const similarity = (maxDifference - difference) / maxDifference;
        score += similarity * weight;
        totalWeight += weight;
      });

      // Assessment frequency comparison
      if (userIndicators.assessmentFrequency === styleIndicators.assessmentFrequency) {
        score += 1;
      }
      totalWeight += 1;

      scores[style as TeachingStyle] = (score / totalWeight) * 100;
    });

    // Find best and second-best matches
    const sortedStyles = Object.entries(scores).sort(([,a], [,b]) => b - a);
    const primaryStyle = sortedStyles[0][0] as TeachingStyle;
    const secondaryStyle = sortedStyles[1] && sortedStyles[1][1] > 60 ? sortedStyles[1][0] as TeachingStyle : undefined;
    const confidence = Math.round(sortedStyles[0][1]);

    return {
      primaryStyle,
      secondaryStyle,
      confidence,
      indicators: userIndicators,
      recommendations: generateRecommendations(primaryStyle, userIndicators)
    };
  };

  const generateRecommendations = (style: TeachingStyle, indicators: TeachingStyleIndicators): string[] => {
    const recommendations: string[] = [];

    // Base recommendations by style
    switch (style) {
      case 'constructivist':
        recommendations.push('Focus on open-ended activities and discovery learning');
        recommendations.push('Include reflection prompts and knowledge-building exercises');
        break;
      case 'direct-instruction':
        recommendations.push('Use clear, step-by-step instructional sequences');
        recommendations.push('Include guided practice and immediate feedback');
        break;
      case 'inquiry-based':
        recommendations.push('Start lessons with compelling questions');
        recommendations.push('Design investigation and exploration activities');
        break;
      case 'project-based':
        recommendations.push('Create authentic, real-world project scenarios');
        recommendations.push('Include collaboration and presentation components');
        break;
      case 'flipped-classroom':
        recommendations.push('Provide pre-class content for home study');
        recommendations.push('Design in-class activities for application and discussion');
        break;
    }

    // Additional recommendations based on indicators
    if (indicators.technologyIntegration >= 7) {
      recommendations.push('Include digital tools and online resources');
    }
    if (indicators.collaborationEmphasis >= 7) {
      recommendations.push('Design group activities and peer learning opportunities');
    }
    if (indicators.assessmentFrequency === 'high') {
      recommendations.push('Include frequent formative assessment checkpoints');
    }

    return recommendations;
  };

  const analyzeAndDetect = async () => {
    setIsAnalyzing(true);
    
    // Simulate analysis time
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const indicators = calculateStyleIndicators();
    const result = findBestMatchingStyle(indicators);
    
    // Update user profile with detected style
    if (profile) {
      updateProfile({ teachingStyle: result.primaryStyle });
    }
    
    setIsAnalyzing(false);
    onStyleDetected(result);
  };

  const isComplete = Object.keys(answers).length === DETECTION_QUESTIONS.length;
  const currentQ = DETECTION_QUESTIONS[currentQuestion];

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
        maxWidth: '600px',
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
            🎯 Teaching Style Detection
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
                width: `${(Object.keys(answers).length / DETECTION_QUESTIONS.length) * 100}%`,
                transition: 'width 0.3s ease'
              }} />
            </div>
            <span style={{ fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
              {Object.keys(answers).length} of {DETECTION_QUESTIONS.length}
            </span>
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '24px', overflow: 'auto', maxHeight: '60vh' }}>
          {!isAnalyzing && !isComplete && (
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', color: '#1e293b' }}>
                Question {currentQuestion + 1} of {DETECTION_QUESTIONS.length}
              </h3>
              
              <p style={{ fontSize: '16px', marginBottom: '24px', color: '#374151' }}>
                {currentQ.text}
              </p>
              
              <div style={{ display: 'grid', gap: '12px' }}>
                {currentQ.options.map((option) => (
                  <label
                    key={option.value}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '16px',
                      border: `2px solid ${answers[currentQ.id] === option.value ? '#3b82f6' : '#e5e7eb'}`,
                      borderRadius: '8px',
                      cursor: 'pointer',
                      backgroundColor: answers[currentQ.id] === option.value ? '#dbeafe' : 'white',
                      transition: 'all 0.2s'
                    }}
                  >
                    <input
                      type="radio"
                      name={currentQ.id}
                      value={option.value}
                      checked={answers[currentQ.id] === option.value}
                      onChange={() => handleAnswer(currentQ.id, option.value)}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <span style={{ fontSize: '14px', color: '#374151' }}>
                      {option.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {isAnalyzing && (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                margin: '0 auto 16px',
                border: '4px solid #f3f4f6',
                borderTop: '4px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <h3 style={{ fontSize: '18px', color: '#1e293b', marginBottom: '8px' }}>
                Analyzing Your Teaching Style...
              </h3>
              <p style={{ color: '#64748b', fontSize: '14px' }}>
                Evaluating your responses and matching them to educational methodologies
              </p>
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
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
            disabled={currentQuestion === 0}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              backgroundColor: currentQuestion === 0 ? '#f3f4f6' : 'white',
              color: currentQuestion === 0 ? '#9ca3af' : '#374151',
              borderRadius: '6px',
              cursor: currentQuestion === 0 ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            ← Previous
          </button>

          <div style={{ display: 'flex', gap: '12px' }}>
            {!isComplete && currentQuestion < DETECTION_QUESTIONS.length - 1 && answers[currentQ.id] && (
              <button
                onClick={() => setCurrentQuestion(currentQuestion + 1)}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Next →
              </button>
            )}
            
            {isComplete && !isAnalyzing && (
              <button
                onClick={analyzeAndDetect}
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
                🎯 Analyze Teaching Style
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}