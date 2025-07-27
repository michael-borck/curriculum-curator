import React, { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { useStatusFeedback } from './StatusFeedback';
import type { ImportedContent } from '../hooks/useImport';
import type { AnalysisResult } from './ContentAnalysis';

// Comparison types
export interface ContentComparison {
  original_content: ImportedContent[];
  enhanced_content: ImportedContent[];
  original_analysis: AnalysisResult;
  enhanced_analysis: AnalysisResult;
  improvement_metrics: ImprovementMetrics;
  change_summary: ChangeSummary[];
}

export interface ImprovementMetrics {
  readability_improvement: number;
  structure_improvement: number;
  engagement_improvement: number;
  accessibility_improvement: number;
  completeness_improvement: number;
  overall_improvement: number;
  learning_objectives_added: number;
  content_gaps_filled: number;
}

export interface ChangeSummary {
  section_id: string;
  change_type: ChangeType;
  description: string;
  before_preview: string;
  after_preview: string;
  improvement_percentage: number;
}

export type ChangeType = 'Added' | 'Modified' | 'Removed' | 'Restructured' | 'Enhanced';

interface ContentComparisonProps {
  originalContent: ImportedContent[];
  enhancedContent: ImportedContent[];
  originalAnalysis?: AnalysisResult;
  enhancedAnalysis?: AnalysisResult;
  onAcceptChanges?: () => void;
  onRejectChanges?: () => void;
}

export function ContentComparison({
  originalContent,
  enhancedContent,
  originalAnalysis,
  enhancedAnalysis,
  onAcceptChanges,
  onRejectChanges
}: ContentComparisonProps) {
  const [comparison, setComparison] = useState<ContentComparison | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'side-by-side' | 'inline' | 'metrics'>('side-by-side');
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [showOnlyChanges, setShowOnlyChanges] = useState(true);
  const statusFeedback = useStatusFeedback();

  React.useEffect(() => {
    generateComparison();
  }, [originalContent, enhancedContent]);

  const generateComparison = async () => {
    if (!originalContent.length || !enhancedContent.length) return;
    
    setIsLoading(true);
    try {
      const result = await invoke<ContentComparison>('create_content_comparison', {
        originalContent,
        enhancedContent
      });
      setComparison(result);
    } catch (error) {
      statusFeedback.showError('Comparison Failed', error as string);
    } finally {
      setIsLoading(false);
    }
  };

  const getChangeTypeColor = (type: ChangeType): string => {
    const colors: Record<ChangeType, string> = {
      Added: '#10b981',
      Modified: '#3b82f6',
      Removed: '#ef4444',
      Restructured: '#8b5cf6',
      Enhanced: '#f59e0b'
    };
    return colors[type];
  };

  const getChangeTypeIcon = (type: ChangeType): string => {
    const icons: Record<ChangeType, string> = {
      Added: '+',
      Modified: '✎',
      Removed: '-',
      Restructured: '🔄',
      Enhanced: '✨'
    };
    return icons[type];
  };

  const formatPercentage = (value: number): string => {
    const percentage = Math.round(value * 100);
    return percentage > 0 ? `+${percentage}%` : `${percentage}%`;
  };

  const getImprovementColor = (value: number): string => {
    if (value > 0.1) return '#10b981';
    if (value > 0) return '#3b82f6';
    if (value === 0) return '#6b7280';
    return '#ef4444';
  };

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px',
        minHeight: '400px'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
        <h3 style={{ fontSize: '18px', color: '#1f2937' }}>
          Analyzing Changes...
        </h3>
      </div>
    );
  }

  if (!comparison) return null;

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', margin: 0 }}>
              🔄 Content Comparison
            </h2>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '4px 0 0 0' }}>
              Review changes between original and enhanced content
            </p>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <span style={{
              padding: '8px 16px',
              backgroundColor: '#d1fae5',
              color: '#065f46',
              borderRadius: '20px',
              fontSize: '14px',
              fontWeight: '500'
            }}>
              {formatPercentage(comparison.improvement_metrics.overall_improvement)} Overall
            </span>
          </div>
        </div>
      </div>

      {/* View Mode Selector */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 24px',
        backgroundColor: '#f9fafb',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {(['side-by-side', 'inline', 'metrics'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              style={{
                padding: '6px 16px',
                backgroundColor: viewMode === mode ? '#3b82f6' : 'white',
                color: viewMode === mode ? 'white' : '#6b7280',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {mode === 'side-by-side' ? 'Side by Side' : mode}
            </button>
          ))}
        </div>
        {viewMode !== 'metrics' && (
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#4b5563' }}>
            <input
              type="checkbox"
              checked={showOnlyChanges}
              onChange={(e) => setShowOnlyChanges(e.target.checked)}
              style={{ marginRight: '4px' }}
            />
            Show only changes
          </label>
        )}
      </div>

      {/* Content Area */}
      <div style={{ maxHeight: '600px', overflow: 'auto' }}>
        {viewMode === 'metrics' && (
          <div style={{ padding: '24px' }}>
            {/* Improvement Overview */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '16px',
              marginBottom: '24px'
            }}>
              {[
                { label: 'Readability', value: comparison.improvement_metrics.readability_improvement },
                { label: 'Structure', value: comparison.improvement_metrics.structure_improvement },
                { label: 'Engagement', value: comparison.improvement_metrics.engagement_improvement },
                { label: 'Accessibility', value: comparison.improvement_metrics.accessibility_improvement },
                { label: 'Completeness', value: comparison.improvement_metrics.completeness_improvement },
                { label: 'Overall Quality', value: comparison.improvement_metrics.overall_improvement }
              ].map(({ label, value }) => (
                <div key={label} style={{
                  padding: '16px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb'
                }}>
                  <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>
                    {label}
                  </div>
                  <div style={{
                    fontSize: '24px',
                    fontWeight: '600',
                    color: getImprovementColor(value)
                  }}>
                    {formatPercentage(value)}
                  </div>
                  <div style={{
                    width: '100%',
                    height: '4px',
                    backgroundColor: '#e5e7eb',
                    borderRadius: '2px',
                    marginTop: '8px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${Math.abs(value) * 100}%`,
                      height: '100%',
                      backgroundColor: getImprovementColor(value)
                    }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Additional Metrics */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '16px',
              marginBottom: '24px'
            }}>
              <div style={{
                padding: '16px',
                backgroundColor: '#d1fae5',
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '16px', fontWeight: '600', color: '#065f46' }}>
                  {comparison.improvement_metrics.learning_objectives_added}
                </div>
                <div style={{ fontSize: '14px', color: '#047857' }}>
                  Learning Objectives Added
                </div>
              </div>
              <div style={{
                padding: '16px',
                backgroundColor: '#dbeafe',
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '16px', fontWeight: '600', color: '#1e40af' }}>
                  {comparison.improvement_metrics.content_gaps_filled}
                </div>
                <div style={{ fontSize: '14px', color: '#1d4ed8' }}>
                  Content Gaps Filled
                </div>
              </div>
            </div>

            {/* Change Summary */}
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
              Change Summary
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {comparison.change_summary.map((change, index) => (
                <div key={index} style={{
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <span style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: getChangeTypeColor(change.change_type),
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '16px',
                    fontWeight: '600'
                  }}>
                    {getChangeTypeIcon(change.change_type)}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>
                      {change.description}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                      {formatPercentage(change.improvement_percentage)} improvement
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setViewMode('side-by-side');
                      setSelectedSection(change.section_id);
                    }}
                    style={{
                      padding: '4px 12px',
                      backgroundColor: 'white',
                      color: '#6b7280',
                      border: '1px solid #e5e7eb',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    View
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {viewMode === 'side-by-side' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            height: '100%'
          }}>
            {/* Original Content */}
            <div style={{
              borderRight: '1px solid #e5e7eb',
              overflow: 'auto'
            }}>
              <div style={{
                padding: '12px 16px',
                backgroundColor: '#fee2e2',
                position: 'sticky',
                top: 0,
                zIndex: 10,
                borderBottom: '1px solid #fecaca'
              }}>
                <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#991b1b', margin: 0 }}>
                  Original Content
                </h3>
              </div>
              <div style={{ padding: '16px' }}>
                {comparison.original_content.map((content, index) => {
                  const hasChanges = comparison.change_summary.some(c => c.section_id === content.id);
                  if (showOnlyChanges && !hasChanges) return null;
                  
                  return (
                    <div
                      key={index}
                      style={{
                        marginBottom: '16px',
                        padding: '12px',
                        backgroundColor: selectedSection === content.id ? '#fef3c7' : '#f9fafb',
                        borderRadius: '6px',
                        border: selectedSection === content.id ? '2px solid #f59e0b' : '1px solid #e5e7eb'
                      }}
                    >
                      <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                        {content.title}
                      </h4>
                      <p style={{ fontSize: '13px', color: '#4b5563', lineHeight: '1.6' }}>
                        {content.content}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Enhanced Content */}
            <div style={{ overflow: 'auto' }}>
              <div style={{
                padding: '12px 16px',
                backgroundColor: '#d1fae5',
                position: 'sticky',
                top: 0,
                zIndex: 10,
                borderBottom: '1px solid #a7f3d0'
              }}>
                <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#065f46', margin: 0 }}>
                  Enhanced Content
                </h3>
              </div>
              <div style={{ padding: '16px' }}>
                {comparison.enhanced_content.map((content, index) => {
                  const change = comparison.change_summary.find(c => c.section_id === content.id);
                  if (showOnlyChanges && !change) return null;
                  
                  return (
                    <div
                      key={index}
                      style={{
                        marginBottom: '16px',
                        padding: '12px',
                        backgroundColor: selectedSection === content.id ? '#fef3c7' : '#f9fafb',
                        borderRadius: '6px',
                        border: selectedSection === content.id ? '2px solid #f59e0b' : '1px solid #e5e7eb',
                        position: 'relative'
                      }}
                    >
                      {change && (
                        <div style={{
                          position: 'absolute',
                          top: '8px',
                          right: '8px',
                          padding: '2px 8px',
                          backgroundColor: getChangeTypeColor(change.change_type),
                          color: 'white',
                          borderRadius: '12px',
                          fontSize: '11px',
                          fontWeight: '500'
                        }}>
                          {change.change_type}
                        </div>
                      )}
                      <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                        {content.title}
                      </h4>
                      <p style={{ fontSize: '13px', color: '#4b5563', lineHeight: '1.6' }}>
                        {content.content}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {viewMode === 'inline' && (
          <div style={{ padding: '24px' }}>
            {comparison.change_summary.map((change, index) => (
              <div key={index} style={{
                marginBottom: '24px',
                padding: '16px',
                backgroundColor: '#f9fafb',
                borderRadius: '8px',
                border: '1px solid #e5e7eb'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '12px'
                }}>
                  <span style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: getChangeTypeColor(change.change_type),
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '16px',
                    fontWeight: '600'
                  }}>
                    {getChangeTypeIcon(change.change_type)}
                  </span>
                  <div>
                    <div style={{ fontSize: '15px', fontWeight: '600' }}>
                      {change.description}
                    </div>
                    <div style={{ fontSize: '13px', color: '#6b7280' }}>
                      {formatPercentage(change.improvement_percentage)} improvement
                    </div>
                  </div>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <h5 style={{ fontSize: '13px', fontWeight: '600', color: '#6b7280', marginBottom: '6px' }}>
                      Before:
                    </h5>
                    <div style={{
                      padding: '12px',
                      backgroundColor: '#fee2e2',
                      borderRadius: '6px',
                      fontSize: '13px',
                      lineHeight: '1.5',
                      color: '#7f1d1d'
                    }}>
                      {change.before_preview}
                    </div>
                  </div>
                  <div>
                    <h5 style={{ fontSize: '13px', fontWeight: '600', color: '#065f46', marginBottom: '6px' }}>
                      After:
                    </h5>
                    <div style={{
                      padding: '12px',
                      backgroundColor: '#d1fae5',
                      borderRadius: '6px',
                      fontSize: '13px',
                      lineHeight: '1.5',
                      color: '#064e3b'
                    }}>
                      {change.after_preview}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div style={{
        padding: '16px 24px',
        borderTop: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>
          {comparison.change_summary.length} changes identified
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={onRejectChanges}
            style={{
              padding: '8px 16px',
              backgroundColor: 'white',
              color: '#6b7280',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            ❌ Reject Changes
          </button>
          <button
            onClick={onAcceptChanges}
            style={{
              padding: '8px 16px',
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            ✅ Accept All Changes
          </button>
        </div>
      </div>
    </div>
  );
}
