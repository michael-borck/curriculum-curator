import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { useStatusFeedback } from './StatusFeedback';
import type { ImportedContent } from '../hooks/useImport';
import type { AnalysisResult } from './ContentAnalysis';

// Enhancement types
export interface EnhancementSuggestions {
  overall_approach: string;
  content_enhancements: ContentEnhancement[];
  structural_improvements: StructuralImprovement[];
  pedagogical_enhancements: PedagogicalEnhancement[];
  estimated_improvement_score: number;
  implementation_priority: ImplementationPriority[];
}

export interface ContentEnhancement {
  section_id: string;
  enhancement_type: EnhancementType;
  original_content: string;
  suggested_content: string;
  rationale: string;
  impact_score: number;
}

export interface StructuralImprovement {
  improvement_type: StructuralImprovementType;
  description: string;
  implementation_guide: string;
  expected_impact: string;
  effort_level: EffortLevel;
}

export interface PedagogicalEnhancement {
  enhancement_type: PedagogicalEnhancementType;
  current_state: string;
  desired_state: string;
  implementation_steps: string[];
  learning_impact: string;
}

export interface ImplementationPriority {
  priority_level: number;
  enhancement_ref: string;
  quick_win: boolean;
  dependencies: string[];
}

export type EnhancementType = 'Clarity' | 'Engagement' | 'Examples' | 'Visuals' | 'Activities' | 'Assessment';
export type StructuralImprovementType = 'Organization' | 'Flow' | 'Transitions' | 'Consistency' | 'Completeness';
export type PedagogicalEnhancementType = 'LearningObjectives' | 'Scaffolding' | 'Differentiation' | 'ActiveLearning' | 'Feedback';
export type EffortLevel = 'Low' | 'Medium' | 'High';

interface EnhancementSuggestionsProps {
  importedContent: ImportedContent[];
  analysisResult: AnalysisResult;
  onEnhancementsGenerated?: (suggestions: EnhancementSuggestions) => void;
  onApplyEnhancement?: (enhancement: ContentEnhancement) => void;
}

export function EnhancementSuggestions({ 
  importedContent, 
  analysisResult,
  onEnhancementsGenerated,
  onApplyEnhancement
}: EnhancementSuggestionsProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [suggestions, setSuggestions] = useState<EnhancementSuggestions | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'content' | 'structure' | 'pedagogy'>('overview');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [appliedEnhancements, setAppliedEnhancements] = useState<Set<string>>(new Set());
  const statusFeedback = useStatusFeedback();

  const generateEnhancements = async () => {
    setIsGenerating(true);
    try {
      // For now, using a mock provider - will be replaced with actual LLM selection
      const result = await invoke<EnhancementSuggestions>('generate_enhancement_suggestions', {
        importedContent,
        analysisResult,
        llmProviderId: 'mock'
      });
      setSuggestions(result);
      onEnhancementsGenerated?.(result);
      statusFeedback.showSuccess('Enhancement Suggestions Generated', 'AI-powered suggestions are ready for review');
    } catch (error) {
      statusFeedback.showError('Generation Failed', error as string);
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const applyEnhancement = (enhancement: ContentEnhancement) => {
    setAppliedEnhancements(prev => new Set(prev).add(enhancement.section_id));
    onApplyEnhancement?.(enhancement);
    statusFeedback.showSuccess('Enhancement Applied', `Applied ${enhancement.enhancement_type} enhancement`);
  };

  const getEnhancementTypeIcon = (type: EnhancementType): string => {
    const icons: Record<EnhancementType, string> = {
      Clarity: '💡',
      Engagement: '🎯',
      Examples: '📖',
      Visuals: '🖼️',
      Activities: '🎮',
      Assessment: '📊'
    };
    return icons[type];
  };

  const getEffortLevelColor = (level: EffortLevel): string => {
    const colors: Record<EffortLevel, string> = {
      Low: '#10b981',
      Medium: '#f59e0b',
      High: '#ef4444'
    };
    return colors[level];
  };

  const getImpactScoreColor = (score: number): string => {
    if (score >= 0.8) return '#10b981';
    if (score >= 0.6) return '#3b82f6';
    if (score >= 0.4) return '#f59e0b';
    return '#6b7280';
  };

  if (!suggestions && !isGenerating) {
    return (
      <div style={{ 
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        padding: '40px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>✨</div>
        <h3 style={{ fontSize: '18px', color: '#1f2937', marginBottom: '8px' }}>
          Ready to Enhance Your Content
        </h3>
        <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '24px' }}>
          Generate AI-powered suggestions to improve your educational content
        </p>
        <button
          onClick={generateEnhancements}
          style={{
            padding: '12px 24px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          Generate Enhancement Suggestions
        </button>
      </div>
    );
  }

  if (isGenerating) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        padding: '40px',
        minHeight: '400px',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
        <h3 style={{ fontSize: '18px', color: '#1f2937', marginBottom: '8px' }}>
          Generating Enhancement Suggestions...
        </h3>
        <p style={{ color: '#6b7280', fontSize: '14px' }}>
          Analyzing content and creating personalized improvements
        </p>
      </div>
    );
  }

  if (!suggestions) return null;

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
              ✨ Enhancement Suggestions
            </h2>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '4px 0 0 0' }}>
              AI-powered recommendations to improve your content
            </p>
          </div>
          <div style={{
            padding: '8px 16px',
            backgroundColor: '#dbeafe',
            color: '#1e40af',
            borderRadius: '20px',
            fontSize: '14px',
            fontWeight: '500'
          }}>
            {Math.round(suggestions.estimated_improvement_score * 100)}% Potential Improvement
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb'
      }}>
        {(['overview', 'content', 'structure', 'pedagogy'] as const).map((tab) => (
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
            {tab === 'content' ? 'Content Improvements' : tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ padding: '24px' }}>
        {selectedTab === 'overview' && (
          <div>
            {/* Overall Approach */}
            <div style={{
              padding: '16px',
              backgroundColor: '#f0f9ff',
              borderRadius: '8px',
              marginBottom: '24px'
            }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0369a1', marginBottom: '8px' }}>
                Recommended Approach
              </h3>
              <p style={{ fontSize: '14px', color: '#0c4a6e', lineHeight: '1.6' }}>
                {suggestions.overall_approach}
              </p>
            </div>

            {/* Quick Wins */}
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
              🎯 Quick Wins
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
              {suggestions.implementation_priority
                .filter(p => p.quick_win)
                .slice(0, 3)
                .map((priority, index) => {
                  const enhancement = suggestions.content_enhancements.find(e => e.section_id === priority.enhancement_ref);
                  if (!enhancement) return null;
                  return (
                    <div key={index} style={{
                      padding: '12px',
                      backgroundColor: '#f3f4f6',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px'
                    }}>
                      <span style={{ fontSize: '24px' }}>{getEnhancementTypeIcon(enhancement.enhancement_type)}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '14px', fontWeight: '500' }}>{enhancement.enhancement_type}</div>
                        <div style={{ fontSize: '12px', color: '#6b7280' }}>{enhancement.rationale}</div>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedTab('content');
                          setExpandedItems(new Set([enhancement.section_id]));
                        }}
                        style={{
                          padding: '4px 12px',
                          backgroundColor: '#3b82f6',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer'
                        }}
                      >
                        View
                      </button>
                    </div>
                  );
                })}
            </div>

            {/* Implementation Timeline */}
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
              📅 Implementation Priority
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {suggestions.implementation_priority
                .sort((a, b) => a.priority_level - b.priority_level)
                .slice(0, 5)
                .map((priority, index) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px',
                    backgroundColor: index === 0 ? '#fee2e2' : '#f9fafb',
                    borderRadius: '4px'
                  }}>
                    <span style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      backgroundColor: index === 0 ? '#dc2626' : '#6b7280',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}>
                      {priority.priority_level}
                    </span>
                    <span style={{ fontSize: '14px', flex: 1 }}>{priority.enhancement_ref}</span>
                    {priority.quick_win && (
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 6px',
                        backgroundColor: '#10b981',
                        color: 'white',
                        borderRadius: '3px'
                      }}>
                        Quick Win
                      </span>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}

        {selectedTab === 'content' && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
              Content Enhancement Suggestions ({suggestions.content_enhancements.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {suggestions.content_enhancements.map((enhancement) => (
                <div key={enhancement.section_id} style={{
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  overflow: 'hidden'
                }}>
                  <div
                    onClick={() => toggleExpanded(enhancement.section_id)}
                    style={{
                      padding: '16px',
                      backgroundColor: appliedEnhancements.has(enhancement.section_id) ? '#d1fae5' : '#f9fafb',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px'
                    }}
                  >
                    <span style={{ fontSize: '24px' }}>{getEnhancementTypeIcon(enhancement.enhancement_type)}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '14px', fontWeight: '500' }}>
                          {enhancement.enhancement_type} Enhancement
                        </span>
                        <span style={{
                          fontSize: '12px',
                          padding: '2px 8px',
                          backgroundColor: getImpactScoreColor(enhancement.impact_score),
                          color: 'white',
                          borderRadius: '12px'
                        }}>
                          {Math.round(enhancement.impact_score * 100)}% Impact
                        </span>
                        {appliedEnhancements.has(enhancement.section_id) && (
                          <span style={{ color: '#10b981', fontSize: '14px' }}>✓ Applied</span>
                        )}
                      </div>
                      <p style={{ fontSize: '13px', color: '#6b7280', margin: '4px 0 0 0' }}>
                        {enhancement.rationale}
                      </p>
                    </div>
                    <span style={{
                      transform: expandedItems.has(enhancement.section_id) ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s'
                    }}>
                      ▼
                    </span>
                  </div>
                  
                  {expandedItems.has(enhancement.section_id) && (
                    <div style={{ padding: '16px', borderTop: '1px solid #e5e7eb' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div>
                          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#6b7280' }}>
                            Original Content
                          </h4>
                          <div style={{
                            padding: '12px',
                            backgroundColor: '#f9fafb',
                            borderRadius: '6px',
                            fontSize: '13px',
                            lineHeight: '1.6',
                            border: '1px solid #e5e7eb'
                          }}>
                            {enhancement.original_content}
                          </div>
                        </div>
                        <div>
                          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#059669' }}>
                            Suggested Enhancement
                          </h4>
                          <div style={{
                            padding: '12px',
                            backgroundColor: '#d1fae5',
                            borderRadius: '6px',
                            fontSize: '13px',
                            lineHeight: '1.6',
                            border: '1px solid #10b981'
                          }}>
                            {enhancement.suggested_content}
                          </div>
                        </div>
                      </div>
                      {!appliedEnhancements.has(enhancement.section_id) && (
                        <button
                          onClick={() => applyEnhancement(enhancement)}
                          style={{
                            marginTop: '12px',
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
                          Apply This Enhancement
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'structure' && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
              Structural Improvements ({suggestions.structural_improvements.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {suggestions.structural_improvements.map((improvement, index) => (
                <div key={index} style={{
                  padding: '16px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <h4 style={{ fontSize: '15px', fontWeight: '600', color: '#1f2937' }}>
                      {improvement.improvement_type}
                    </h4>
                    <span style={{
                      fontSize: '12px',
                      padding: '4px 12px',
                      backgroundColor: getEffortLevelColor(improvement.effort_level),
                      color: 'white',
                      borderRadius: '12px'
                    }}>
                      {improvement.effort_level} Effort
                    </span>
                  </div>
                  <p style={{ fontSize: '14px', color: '#4b5563', marginBottom: '8px' }}>
                    {improvement.description}
                  </p>
                  <div style={{
                    padding: '12px',
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    marginBottom: '8px'
                  }}>
                    <h5 style={{ fontSize: '13px', fontWeight: '600', color: '#6b7280', marginBottom: '4px' }}>
                      Implementation Guide:
                    </h5>
                    <p style={{ fontSize: '13px', color: '#4b5563', lineHeight: '1.5' }}>
                      {improvement.implementation_guide}
                    </p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>📈</span>
                    <span style={{ fontSize: '13px', color: '#059669' }}>
                      <strong>Expected Impact:</strong> {improvement.expected_impact}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'pedagogy' && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
              Pedagogical Enhancements ({suggestions.pedagogical_enhancements.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {suggestions.pedagogical_enhancements.map((enhancement, index) => (
                <div key={index} style={{
                  padding: '16px',
                  backgroundColor: '#fef3c7',
                  borderRadius: '8px',
                  border: '1px solid #f59e0b'
                }}>
                  <h4 style={{ fontSize: '15px', fontWeight: '600', color: '#92400e', marginBottom: '8px' }}>
                    {enhancement.enhancement_type}
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                    <div>
                      <h5 style={{ fontSize: '13px', fontWeight: '600', color: '#6b7280', marginBottom: '4px' }}>
                        Current State:
                      </h5>
                      <p style={{ fontSize: '13px', color: '#4b5563' }}>
                        {enhancement.current_state}
                      </p>
                    </div>
                    <div>
                      <h5 style={{ fontSize: '13px', fontWeight: '600', color: '#059669', marginBottom: '4px' }}>
                        Desired State:
                      </h5>
                      <p style={{ fontSize: '13px', color: '#047857' }}>
                        {enhancement.desired_state}
                      </p>
                    </div>
                  </div>
                  <div style={{
                    padding: '12px',
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    marginBottom: '8px'
                  }}>
                    <h5 style={{ fontSize: '13px', fontWeight: '600', color: '#6b7280', marginBottom: '8px' }}>
                      Implementation Steps:
                    </h5>
                    <ol style={{ margin: 0, paddingLeft: '20px' }}>
                      {enhancement.implementation_steps.map((step, stepIndex) => (
                        <li key={stepIndex} style={{ fontSize: '13px', color: '#4b5563', marginBottom: '4px' }}>
                          {step}
                        </li>
                      ))}
                    </ol>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>🎓</span>
                    <span style={{ fontSize: '13px', color: '#7c3aed' }}>
                      <strong>Learning Impact:</strong> {enhancement.learning_impact}
                    </span>
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
          {appliedEnhancements.size} of {suggestions.content_enhancements.length} enhancements applied
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => {
              // Export suggestions functionality
              statusFeedback.showInfo('Export', 'Export functionality coming soon');
            }}
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
            📄 Export Report
          </button>
          <button
            onClick={() => {
              // Apply all quick wins
              const quickWins = suggestions.implementation_priority
                .filter(p => p.quick_win)
                .map(p => suggestions.content_enhancements.find(e => e.section_id === p.enhancement_ref))
                .filter(Boolean) as ContentEnhancement[];
              
              quickWins.forEach(enhancement => applyEnhancement(enhancement));
            }}
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
            ⚡ Apply All Quick Wins
          </button>
        </div>
      </div>
    </div>
  );
}
