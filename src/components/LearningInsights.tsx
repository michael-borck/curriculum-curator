// Learning Insights Component

import React, { useState, useEffect } from 'react';
import type { LearningInsights, CrossSessionLearningData, BehaviorPattern } from '../types/settings';
import { crossSessionLearning } from '../utils/crossSessionLearning';

interface LearningInsightsProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LearningInsights({ isOpen, onClose }: LearningInsightsProps) {
  const [insights, setInsights] = useState<LearningInsights | null>(null);
  const [statistics, setStatistics] = useState<CrossSessionLearningData | null>(null);
  const [activeTab, setActiveTab] = useState<'insights' | 'patterns' | 'suggestions'>('insights');

  useEffect(() => {
    if (isOpen) {
      setInsights(crossSessionLearning.getLearningInsights());
      setStatistics(crossSessionLearning.getLearningStatistics());
    }
  }, [isOpen]);

  if (!isOpen || !insights) return null;

  const handleExportData = () => {
    const data = crossSessionLearning.exportLearningData();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'curriculum-curator-learning-data.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClearData = () => {
    if (confirm('Are you sure you want to clear all learning data? This action cannot be undone.')) {
      crossSessionLearning.clearLearningData();
      setInsights(crossSessionLearning.getLearningInsights());
      setStatistics(null);
    }
  };

  const formatDuration = (minutes: number): string => {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const getSuccessRate = (): number => {
    if (!statistics || statistics.totalSessions === 0) return 0;
    return Math.round((statistics.successfulSessions / statistics.totalSessions) * 100);
  };

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
        maxWidth: '900px',
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
            📊 Learning Insights
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

        {/* Statistics Banner */}
        {statistics && (
          <div style={{
            padding: '16px 24px',
            backgroundColor: '#f8fafc',
            borderBottom: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#3b82f6' }}>
                  {statistics.totalSessions}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Total Sessions</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#059669' }}>
                  {getSuccessRate()}%
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Success Rate</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#f59e0b' }}>
                  {formatDuration(insights.averageSessionDuration)}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Avg Duration</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#8b5cf6' }}>
                  {insights.preferredContentTypes.length}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Preferred Types</div>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#f8fafc'
        }}>
          {[
            { id: 'insights', label: '📈 Usage Patterns', icon: '📈' },
            { id: 'patterns', label: '🔍 Behavior Patterns', icon: '🔍' },
            { id: 'suggestions', label: '💡 Recommendations', icon: '💡' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                flex: 1,
                padding: '16px 24px',
                border: 'none',
                backgroundColor: activeTab === tab.id ? 'white' : 'transparent',
                color: activeTab === tab.id ? '#3b82f6' : '#64748b',
                borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '500'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ padding: '24px', overflow: 'auto', maxHeight: '60vh' }}>
          {activeTab === 'insights' && (
            <div style={{ display: 'grid', gap: '24px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                  Content Type Preferences
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                  {insights.preferredContentTypes.map((type, index) => (
                    <div key={type} style={{
                      padding: '16px',
                      backgroundColor: '#f1f5f9',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '20px' }}>#{index + 1}</span>
                        <span style={{ fontWeight: '500' }}>{type.replace(/([A-Z])/g, ' $1').trim()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                  Common Subjects
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {insights.commonSubjects.map(subject => (
                    <span key={subject} style={{
                      padding: '6px 12px',
                      backgroundColor: '#dbeafe',
                      color: '#1e40af',
                      borderRadius: '20px',
                      fontSize: '14px',
                      fontWeight: '500'
                    }}>
                      {subject}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                  Optimized Defaults
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
                  <div style={{
                    padding: '16px',
                    backgroundColor: '#ecfdf5',
                    borderRadius: '8px',
                    border: '1px solid #d1fae5'
                  }}>
                    <div style={{ fontWeight: '500', color: '#065f46', marginBottom: '8px' }}>Complexity</div>
                    <div style={{ fontSize: '18px', color: '#047857' }}>
                      {insights.adaptedDefaults.complexity || 'Intermediate'}
                    </div>
                  </div>
                  <div style={{
                    padding: '16px',
                    backgroundColor: '#fef3c7',
                    borderRadius: '8px',
                    border: '1px solid #fde68a'
                  }}>
                    <div style={{ fontWeight: '500', color: '#92400e', marginBottom: '8px' }}>Duration</div>
                    <div style={{ fontSize: '18px', color: '#d97706' }}>
                      {insights.adaptedDefaults.duration || '50 minutes'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'patterns' && (
            <div style={{ display: 'grid', gap: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                Detected Behavior Patterns
              </h3>
              {statistics?.behaviorPatterns && statistics.behaviorPatterns.length > 0 ? (
                <div style={{ display: 'grid', gap: '16px' }}>
                  {statistics.behaviorPatterns.map((pattern, index) => (
                    <div key={index} style={{
                      padding: '20px',
                      backgroundColor: '#f8fafc',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                        <div style={{ fontWeight: '600', color: '#1e293b' }}>
                          {pattern.pattern.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <div style={{
                          padding: '4px 8px',
                          backgroundColor: pattern.confidence > 0.7 ? '#dcfce7' : '#fef3c7',
                          color: pattern.confidence > 0.7 ? '#166534' : '#92400e',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}>
                          {Math.round(pattern.confidence * 100)}% confidence
                        </div>
                      </div>
                      <div style={{ color: '#64748b', marginBottom: '8px' }}>
                        Frequency: {pattern.frequency} sessions
                      </div>
                      <div style={{ color: '#374151' }}>
                        {pattern.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{
                  textAlign: 'center',
                  padding: '40px',
                  color: '#64748b'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                  <div style={{ fontSize: '18px', marginBottom: '8px' }}>No patterns detected yet</div>
                  <div>Use the app more to see personalized behavior insights</div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'suggestions' && (
            <div style={{ display: 'grid', gap: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
                Personalized Recommendations
              </h3>
              <div style={{ display: 'grid', gap: '16px' }}>
                {insights.improvementSuggestions.map((suggestion, index) => (
                  <div key={index} style={{
                    padding: '16px',
                    backgroundColor: '#dbeafe',
                    borderRadius: '8px',
                    border: '1px solid #bfdbfe',
                    display: 'flex',
                    alignItems: 'start',
                    gap: '12px'
                  }}>
                    <div style={{ fontSize: '20px', marginTop: '2px' }}>💡</div>
                    <div style={{ color: '#1e40af', lineHeight: '1.5' }}>{suggestion}</div>
                  </div>
                ))}
              </div>

              {insights.errorPatterns.length > 0 && (
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#dc2626' }}>
                    Common Issues to Avoid
                  </h4>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {insights.errorPatterns.map((error, index) => (
                      <div key={index} style={{
                        padding: '12px',
                        backgroundColor: '#fef2f2',
                        borderRadius: '6px',
                        border: '1px solid #fecaca',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <span style={{ fontSize: '16px' }}>⚠️</span>
                        <span style={{ color: '#991b1b' }}>{error.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
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
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={handleExportData}
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
              📤 Export Data
            </button>
            <button
              onClick={handleClearData}
              style={{
                padding: '8px 16px',
                border: '1px solid #ef4444',
                backgroundColor: '#fef2f2',
                color: '#dc2626',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              🗑️ Clear Data
            </button>
          </div>

          <button
            onClick={onClose}
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
            Close
          </button>
        </div>
      </div>
    </div>
  );
}