// Teaching Style Detection Results Component

import React from 'react';
import { TeachingStyleDetectionResult, TeachingStyle } from '../types/settings';

interface TeachingStyleResultsProps {
  isOpen: boolean;
  onClose: () => void;
  result: TeachingStyleDetectionResult | null;
  onAccept: () => void;
  onRetake: () => void;
}

const STYLE_DESCRIPTIONS: Record<TeachingStyle, { name: string; description: string; icon: string }> = {
  'traditional-lecture': {
    name: 'Traditional Lecture',
    description: 'Teacher-centered approach with structured presentation of information',
    icon: '🎓'
  },
  'constructivist': {
    name: 'Constructivist',
    description: 'Students actively build knowledge through exploration and discovery',
    icon: '🔨'
  },
  'direct-instruction': {
    name: 'Direct Instruction',
    description: 'Systematic, explicit teaching with clear steps and modeling',
    icon: '📋'
  },
  'inquiry-based': {
    name: 'Inquiry-Based',
    description: 'Learning driven by questions, investigation, and student curiosity',
    icon: '🔍'
  },
  'flipped-classroom': {
    name: 'Flipped Classroom',
    description: 'Content at home, application and discussion in class',
    icon: '🔄'
  },
  'project-based': {
    name: 'Project-Based',
    description: 'Learning through authentic, real-world projects and challenges',
    icon: '🚀'
  },
  'competency-based': {
    name: 'Competency-Based',
    description: 'Progress based on mastery of specific skills and knowledge',
    icon: '🎯'
  },
  'culturally-responsive': {
    name: 'Culturally Responsive',
    description: 'Teaching that acknowledges and builds on students\' cultural backgrounds',
    icon: '🌍'
  },
  'mixed-approach': {
    name: 'Mixed Approach',
    description: 'Flexible combination of multiple teaching methodologies',
    icon: '🔀'
  }
};

export function TeachingStyleResults({ isOpen, onClose, result, onAccept, onRetake }: TeachingStyleResultsProps) {
  if (!isOpen || !result) return null;

  const primaryStyle = STYLE_DESCRIPTIONS[result.primaryStyle];
  const secondaryStyle = result.secondaryStyle ? STYLE_DESCRIPTIONS[result.secondaryStyle] : null;

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return '#059669'; // green
    if (confidence >= 60) return '#d97706'; // orange
    return '#dc2626'; // red
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 80) return 'High Confidence';
    if (confidence >= 60) return 'Moderate Confidence';
    return 'Low Confidence';
  };

  const renderIndicatorBar = (label: string, value: number, maxValue: number = 10) => (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '14px', color: '#374151' }}>{label}</span>
        <span style={{ fontSize: '12px', color: '#6b7280' }}>{value}/{maxValue}</span>
      </div>
      <div style={{ 
        width: '100%', 
        height: '8px', 
        backgroundColor: '#e5e7eb', 
        borderRadius: '4px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${(value / maxValue) * 100}%`,
          height: '100%',
          backgroundColor: value >= 7 ? '#059669' : value >= 4 ? '#d97706' : '#dc2626',
          transition: 'width 0.3s ease'
        }} />
      </div>
    </div>
  );

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
        maxWidth: '700px',
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
            🎉 Your Teaching Style
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

        {/* Content */}
        <div style={{ padding: '24px', overflow: 'auto', maxHeight: '70vh' }}>
          {/* Primary Style */}
          <div style={{
            padding: '20px',
            backgroundColor: '#f0f9ff',
            border: '2px solid #3b82f6',
            borderRadius: '12px',
            marginBottom: '24px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>
              {primaryStyle.icon}
            </div>
            <h3 style={{ fontSize: '24px', fontWeight: '600', color: '#1e40af', marginBottom: '8px' }}>
              {primaryStyle.name}
            </h3>
            <p style={{ fontSize: '16px', color: '#1e40af', marginBottom: '16px' }}>
              {primaryStyle.description}
            </p>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              backgroundColor: 'white',
              borderRadius: '20px',
              border: '1px solid #bfdbfe'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: getConfidenceColor(result.confidence)
              }} />
              <span style={{ fontSize: '14px', color: '#374151', fontWeight: '500' }}>
                {getConfidenceLabel(result.confidence)} ({result.confidence}%)
              </span>
            </div>
          </div>

          {/* Secondary Style */}
          {secondaryStyle && (
            <div style={{
              padding: '16px',
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              marginBottom: '24px'
            }}>
              <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
                {secondaryStyle.icon} Secondary Style: {secondaryStyle.name}
              </h4>
              <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
                {secondaryStyle.description}
              </p>
            </div>
          )}

          {/* Style Indicators */}
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            marginBottom: '24px'
          }}>
            <h4 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', marginBottom: '20px' }}>
              📊 Your Teaching Profile
            </h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                {renderIndicatorBar('Student Interaction', result.indicators.interactionLevel)}
                {renderIndicatorBar('Structure Preference', result.indicators.structurePreference)}
                {renderIndicatorBar('Student-Centered Approach', result.indicators.studentCenteredApproach)}
              </div>
              <div>
                {renderIndicatorBar('Technology Integration', result.indicators.technologyIntegration)}
                {renderIndicatorBar('Collaboration Emphasis', result.indicators.collaborationEmphasis)}
                <div style={{ marginBottom: '12px' }}>
                  <span style={{ fontSize: '14px', color: '#374151' }}>Assessment Frequency</span>
                  <div style={{ 
                    marginTop: '4px',
                    padding: '8px 12px',
                    backgroundColor: result.indicators.assessmentFrequency === 'high' ? '#dcfce7' : 
                                   result.indicators.assessmentFrequency === 'medium' ? '#fef3c7' : '#fee2e2',
                    color: result.indicators.assessmentFrequency === 'high' ? '#166534' : 
                           result.indicators.assessmentFrequency === 'medium' ? '#92400e' : '#dc2626',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '500',
                    textTransform: 'capitalize'
                  }}>
                    {result.indicators.assessmentFrequency}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div style={{
            padding: '20px',
            backgroundColor: '#ecfdf5',
            border: '1px solid #bbf7d0',
            borderRadius: '12px'
          }}>
            <h4 style={{ fontSize: '18px', fontWeight: '600', color: '#166534', marginBottom: '16px' }}>
              💡 Personalized Recommendations
            </h4>
            <div style={{ display: 'grid', gap: '8px' }}>
              {result.recommendations.map((recommendation, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  <span style={{ color: '#16a34a', fontSize: '16px' }}>✓</span>
                  <span style={{ fontSize: '14px', color: '#166534' }}>
                    {recommendation}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '24px',
          borderTop: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px'
        }}>
          <button
            onClick={onRetake}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              backgroundColor: '#f3f4f6',
              color: '#374151',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            🔄 Retake Assessment
          </button>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={onClose}
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
              Close
            </button>
            <button
              onClick={onAccept}
              style={{
                padding: '12px 24px',
                border: 'none',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '500'
              }}
            >
              ✓ Apply to Profile
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}