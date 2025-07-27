import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { useStatusFeedback } from './StatusFeedback';
import type { ImportedContent } from '../hooks/useImport';

// Analysis result types
export interface AnalysisResult {
  detected_pedagogy: PedagogicalApproach;
  learning_objectives: LearningObjective[];
  content_structure: ContentStructureAnalysis;
  quality_metrics: QualityMetrics;
  improvement_areas: ImprovementArea[];
  content_gaps: ContentGap[];
}

export type PedagogicalApproach = 'Bloom' | 'Gagne' | 'Constructivist' | 'ProblemBased' | 'Traditional' | 'Mixed';
export type BloomLevel = 'Remember' | 'Understand' | 'Apply' | 'Analyze' | 'Evaluate' | 'Create' | 'Unknown';
export type Priority = 'High' | 'Medium' | 'Low';
export type ImprovementCategory = 'LearningObjectives' | 'ContentStructure' | 'Engagement' | 'Assessment' | 'Accessibility' | 'Clarity';
export type GapType = 'MissingPrerequisites' | 'IncompleteExplanation' | 'LackOfExamples' | 'NoAssessment' | 'MissingVisuals' | 'InsufficientPractice';

export interface LearningObjective {
  text: string;
  bloom_level: BloomLevel;
  action_verb: string;
  content_area: string;
  measurable: boolean;
  confidence: number;
}

export interface ContentStructureAnalysis {
  has_clear_introduction: boolean;
  has_learning_objectives: boolean;
  has_assessments: boolean;
  has_activities: boolean;
  has_summary: boolean;
  logical_flow_score: number;
  sections: SectionAnalysis[];
}

export interface SectionAnalysis {
  title: string;
  content_type: string;
  word_count: number;
  reading_level: number;
  key_concepts: string[];
}

export interface QualityMetrics {
  readability_score: number;
  structure_score: number;
  engagement_score: number;
  accessibility_score: number;
  completeness_score: number;
  overall_quality: number;
}

export interface ImprovementArea {
  category: ImprovementCategory;
  description: string;
  priority: Priority;
  suggested_action: string;
  estimated_impact: number;
}

export interface ContentGap {
  gap_type: GapType;
  description: string;
  suggested_content: string;
  importance: number;
}

interface ContentAnalysisProps {
  importedContent: ImportedContent[];
  onAnalysisComplete?: (analysis: AnalysisResult) => void;
  onRequestEnhancement?: () => void;
}

export function ContentAnalysis({ 
  importedContent, 
  onAnalysisComplete, 
  onRequestEnhancement 
}: ContentAnalysisProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'objectives' | 'quality' | 'gaps'>('overview');
  const statusFeedback = useStatusFeedback();

  useEffect(() => {
    if (importedContent.length > 0) {
      performAnalysis();
    }
  }, [importedContent]);

  const performAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const result = await invoke<AnalysisResult>('analyze_imported_content', {
        importedContent
      });
      setAnalysis(result);
      onAnalysisComplete?.(result);
      statusFeedback.showSuccess('Analysis Complete', 'Content has been analyzed successfully');
    } catch (error) {
      statusFeedback.showError('Analysis Failed', error as string);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getBloomLevelColor = (level: BloomLevel): string => {
    const colors: Record<BloomLevel, string> = {
      Remember: '#ef4444',
      Understand: '#f97316',
      Apply: '#eab308',
      Analyze: '#22c55e',
      Evaluate: '#3b82f6',
      Create: '#8b5cf6',
      Unknown: '#6b7280'
    };
    return colors[level];
  };

  const getPriorityColor = (priority: Priority): string => {
    const colors: Record<Priority, string> = {
      High: '#dc2626',
      Medium: '#f59e0b',
      Low: '#10b981'
    };
    return colors[priority];
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return '#10b981';
    if (score >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  const renderMetricBar = (label: string, score: number) => (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '14px', color: '#4b5563' }}>{label}</span>
        <span style={{ fontSize: '14px', fontWeight: '500', color: getScoreColor(score) }}>
          {Math.round(score * 100)}%
        </span>
      </div>
      <div style={{ 
        width: '100%', 
        height: '8px', 
        backgroundColor: '#e5e7eb', 
        borderRadius: '4px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${score * 100}%`,
          height: '100%',
          backgroundColor: getScoreColor(score),
          transition: 'width 0.3s ease'
        }} />
      </div>
    </div>
  );

  if (isAnalyzing) {
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
        <h3 style={{ fontSize: '18px', color: '#1f2937', marginBottom: '8px' }}>
          Analyzing Content...
        </h3>
        <p style={{ color: '#6b7280', fontSize: '14px' }}>
          Evaluating structure, quality, and learning objectives
        </p>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

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
        <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', margin: 0 }}>
          📊 Content Analysis Results
        </h2>
        <p style={{ color: '#6b7280', fontSize: '14px', margin: '4px 0 0 0' }}>
          Comprehensive analysis of your imported content
        </p>
      </div>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb'
      }}>
        {(['overview', 'objectives', 'quality', 'gaps'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            style={{
              padding: '12px 24px',
              border: 'none',
              backgroundColor: selectedTab === tab ? 'white' : 'transparent',
              borderBottom: selectedTab === tab ? '2px solid #3b82f6' : 'none',
              color: selectedTab === tab ? '#3b82f6' : '#6b7280',
              fontWeight: selectedTab === tab ? '500' : '400',
              fontSize: '14px',
              cursor: 'pointer',
              textTransform: 'capitalize'
            }}
          >
            {tab === 'objectives' ? 'Learning Objectives' : tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ padding: '24px' }}>
        {selectedTab === 'overview' && (
          <div>
            {/* Pedagogical Approach */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                Detected Pedagogical Approach
              </h3>
              <div style={{
                display: 'inline-block',
                padding: '8px 16px',
                backgroundColor: '#dbeafe',
                color: '#1e40af',
                borderRadius: '20px',
                fontSize: '14px',
                fontWeight: '500'
              }}>
                {analysis.detected_pedagogy}
              </div>
            </div>

            {/* Content Structure */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                Content Structure
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                {[
                  { label: 'Clear Introduction', value: analysis.content_structure.has_clear_introduction },
                  { label: 'Learning Objectives', value: analysis.content_structure.has_learning_objectives },
                  { label: 'Assessments', value: analysis.content_structure.has_assessments },
                  { label: 'Activities', value: analysis.content_structure.has_activities },
                  { label: 'Summary', value: analysis.content_structure.has_summary },
                ].map(({ label, value }) => (
                  <div key={label} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    backgroundColor: value ? '#d1fae5' : '#fee2e2',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}>
                    <span>{value ? '✅' : '❌'}</span>
                    <span style={{ color: value ? '#065f46' : '#991b1b' }}>{label}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: '12px' }}>
                {renderMetricBar('Logical Flow Score', analysis.content_structure.logical_flow_score)}
              </div>
            </div>

            {/* Improvement Summary */}
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                Key Improvements Needed
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {analysis.improvement_areas.slice(0, 3).map((improvement, index) => (
                  <div key={index} style={{
                    padding: '12px',
                    backgroundColor: '#f3f4f6',
                    borderRadius: '6px',
                    borderLeft: `4px solid ${getPriorityColor(improvement.priority)}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '14px', fontWeight: '500' }}>{improvement.description}</span>
                      <span style={{
                        fontSize: '12px',
                        padding: '2px 8px',
                        backgroundColor: getPriorityColor(improvement.priority),
                        color: 'white',
                        borderRadius: '12px'
                      }}>
                        {improvement.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'objectives' && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
              Extracted Learning Objectives ({analysis.learning_objectives.length})
            </h3>
            {analysis.learning_objectives.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {analysis.learning_objectives.map((objective, index) => (
                  <div key={index} style={{
                    padding: '16px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb'
                  }}>
                    <div style={{ marginBottom: '8px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 12px',
                        backgroundColor: getBloomLevelColor(objective.bloom_level),
                        color: 'white',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '500',
                        marginRight: '8px'
                      }}>
                        {objective.bloom_level}
                      </span>
                      <span style={{
                        fontSize: '12px',
                        color: objective.measurable ? '#10b981' : '#ef4444'
                      }}>
                        {objective.measurable ? '✓ Measurable' : '✗ Not Measurable'}
                      </span>
                    </div>
                    <p style={{ margin: '8px 0', fontSize: '14px', color: '#1f2937' }}>
                      {objective.text}
                    </p>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>
                      <strong>Action Verb:</strong> {objective.action_verb} | 
                      <strong> Confidence:</strong> {Math.round(objective.confidence * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '40px',
                textAlign: 'center',
                color: '#6b7280',
                backgroundColor: '#f9fafb',
                borderRadius: '8px'
              }}>
                <p>No learning objectives detected in the content.</p>
                <p style={{ fontSize: '14px', marginTop: '8px' }}>
                  Consider adding clear, measurable learning objectives.
                </p>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'quality' && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
              Content Quality Metrics
            </h3>
            <div style={{ marginBottom: '24px' }}>
              {renderMetricBar('Overall Quality', analysis.quality_metrics.overall_quality)}
              {renderMetricBar('Readability', analysis.quality_metrics.readability_score)}
              {renderMetricBar('Structure', analysis.quality_metrics.structure_score)}
              {renderMetricBar('Engagement', analysis.quality_metrics.engagement_score)}
              {renderMetricBar('Accessibility', analysis.quality_metrics.accessibility_score)}
              {renderMetricBar('Completeness', analysis.quality_metrics.completeness_score)}
            </div>

            {/* Section Analysis */}
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
              Section Analysis
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {analysis.content_structure.sections.map((section, index) => (
                <div key={index} style={{
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <strong>{section.title}</strong>
                    <span style={{ color: '#6b7280' }}>{section.word_count} words</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>
                    Reading Level: Grade {section.reading_level.toFixed(1)} | 
                    Type: {section.content_type}
                  </div>
                  {section.key_concepts.length > 0 && (
                    <div style={{ marginTop: '4px' }}>
                      <span style={{ fontSize: '12px', color: '#4b5563' }}>Key concepts: </span>
                      <span style={{ fontSize: '12px', color: '#6b7280' }}>
                        {section.key_concepts.join(', ')}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'gaps' && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
              Identified Content Gaps
            </h3>
            {analysis.content_gaps.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {analysis.content_gaps.map((gap, index) => (
                  <div key={index} style={{
                    padding: '16px',
                    backgroundColor: '#fef3c7',
                    borderRadius: '8px',
                    border: '1px solid #f59e0b'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '20px' }}>
                        {gap.gap_type === 'MissingPrerequisites' && '📚'}
                        {gap.gap_type === 'IncompleteExplanation' && '❓'}
                        {gap.gap_type === 'LackOfExamples' && '💡'}
                        {gap.gap_type === 'NoAssessment' && '📝'}
                        {gap.gap_type === 'MissingVisuals' && '🖼️'}
                        {gap.gap_type === 'InsufficientPractice' && '🎯'}
                      </span>
                      <strong style={{ color: '#92400e' }}>{gap.description}</strong>
                    </div>
                    <p style={{ fontSize: '14px', color: '#78350f', marginBottom: '4px' }}>
                      {gap.suggested_content}
                    </p>
                    <div style={{ fontSize: '12px', color: '#92400e' }}>
                      Importance: {Math.round(gap.importance * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '40px',
                textAlign: 'center',
                color: '#10b981',
                backgroundColor: '#d1fae5',
                borderRadius: '8px'
              }}>
                <p style={{ fontSize: '16px', fontWeight: '500' }}>
                  ✅ No significant content gaps identified!
                </p>
                <p style={{ fontSize: '14px', marginTop: '8px' }}>
                  Your content appears to be comprehensive.
                </p>
              </div>
            )}

            {/* Improvement Areas */}
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginTop: '24px', marginBottom: '12px' }}>
              Recommended Improvements
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {analysis.improvement_areas.map((improvement, index) => (
                <div key={index} style={{
                  padding: '12px',
                  backgroundColor: '#f3f4f6',
                  borderRadius: '6px',
                  borderLeft: `4px solid ${getPriorityColor(improvement.priority)}`
                }}>
                  <div style={{ marginBottom: '4px' }}>
                    <span style={{
                      fontSize: '12px',
                      padding: '2px 8px',
                      backgroundColor: getPriorityColor(improvement.priority),
                      color: 'white',
                      borderRadius: '12px',
                      marginRight: '8px'
                    }}>
                      {improvement.priority}
                    </span>
                    <span style={{ fontSize: '12px', color: '#6b7280' }}>
                      {improvement.category}
                    </span>
                  </div>
                  <p style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
                    {improvement.description}
                  </p>
                  <p style={{ fontSize: '13px', color: '#4b5563' }}>
                    <strong>Action:</strong> {improvement.suggested_action}
                  </p>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                    Estimated Impact: {Math.round(improvement.estimated_impact * 100)}%
                  </div>
                </div>
              ))}
            </div>
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
          Analysis complete. Ready for enhancement?
        </div>
        <button
          onClick={onRequestEnhancement}
          style={{
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          ✨ Enhance Content
        </button>
      </div>
    </div>
  );
}