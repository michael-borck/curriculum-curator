// Progress Indicator Component for Content Generation

import React, { useState, useEffect } from 'react';
import type { ContentType } from '../types/settings';

export interface GenerationStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  progress: number; // 0-100
  estimatedTime?: number; // in seconds
  startTime?: Date;
  endTime?: Date;
  errorMessage?: string;
  details?: string[];
}

export interface GenerationProgress {
  currentStep: number;
  totalSteps: number;
  overallProgress: number; // 0-100
  steps: GenerationStep[];
  startTime: Date;
  estimatedTotalTime: number; // in seconds
  elapsedTime: number; // in seconds
  remainingTime: number; // in seconds
}

interface ProgressIndicatorProps {
  isVisible: boolean;
  progress: GenerationProgress;
  onCancel?: () => void;
  onRetry?: (stepId: string) => void;
  onClose?: () => void;
}

export function ProgressIndicator({ 
  isVisible, 
  progress, 
  onCancel, 
  onRetry, 
  onClose 
}: ProgressIndicatorProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  // Animate progress changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(progress.overallProgress);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress.overallProgress]);

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getStepIcon = (step: GenerationStep): string => {
    switch (step.status) {
      case 'completed': return '✅';
      case 'in_progress': return '🔄';
      case 'error': return '❌';
      default: return '⏳';
    }
  };

  const getStepColor = (step: GenerationStep): string => {
    switch (step.status) {
      case 'completed': return '#059669';
      case 'in_progress': return '#3b82f6';
      case 'error': return '#dc2626';
      default: return '#9ca3af';
    }
  };

  const isGenerationComplete = progress.steps.every(step => 
    step.status === 'completed' || step.status === 'error'
  );

  const hasErrors = progress.steps.some(step => step.status === 'error');

  if (!isVisible) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        maxWidth: '600px',
        width: '90%',
        maxHeight: '80vh',
        overflow: 'hidden',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#f8fafc'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <h2 style={{
              margin: 0,
              fontSize: '20px',
              fontWeight: '600',
              color: '#1e293b'
            }}>
              {isGenerationComplete 
                ? (hasErrors ? '⚠️ Generation Complete with Errors' : '🎉 Generation Complete!')
                : '🚀 Generating Content...'
              }
            </h2>
            
            {isGenerationComplete && onClose && (
              <button
                onClick={onClose}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '20px',
                  cursor: 'pointer',
                  color: '#64748b',
                  padding: '4px'
                }}
              >
                ×
              </button>
            )}
          </div>

          {/* Overall Progress Bar */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <span style={{ fontSize: '14px', color: '#64748b' }}>
                Overall Progress
              </span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>
                {Math.round(animatedProgress)}%
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
                width: `${animatedProgress}%`,
                height: '100%',
                backgroundColor: hasErrors ? '#f59e0b' : '#3b82f6',
                transition: 'width 0.5s ease-in-out',
                borderRadius: '4px'
              }} />
            </div>
          </div>

          {/* Time Information */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '16px',
            fontSize: '12px'
          }}>
            <div>
              <div style={{ color: '#64748b', marginBottom: '4px' }}>Elapsed</div>
              <div style={{ fontWeight: '600', color: '#1e293b' }}>
                {formatTime(progress.elapsedTime)}
              </div>
            </div>
            <div>
              <div style={{ color: '#64748b', marginBottom: '4px' }}>
                {isGenerationComplete ? 'Total Time' : 'Remaining'}
              </div>
              <div style={{ fontWeight: '600', color: '#1e293b' }}>
                {isGenerationComplete 
                  ? formatTime(progress.elapsedTime)
                  : formatTime(progress.remainingTime)
                }
              </div>
            </div>
            <div>
              <div style={{ color: '#64748b', marginBottom: '4px' }}>Steps</div>
              <div style={{ fontWeight: '600', color: '#1e293b' }}>
                {progress.currentStep} of {progress.totalSteps}
              </div>
            </div>
          </div>
        </div>

        {/* Steps List */}
        <div style={{
          padding: '24px',
          maxHeight: '400px',
          overflow: 'auto'
        }}>
          <div style={{ display: 'grid', gap: '16px' }}>
            {progress.steps.map((step, index) => (
              <div
                key={step.id}
                style={{
                  padding: '16px',
                  backgroundColor: step.status === 'in_progress' ? '#f0f9ff' : '#f8fafc',
                  borderRadius: '8px',
                  border: `1px solid ${step.status === 'in_progress' ? '#bfdbfe' : '#e2e8f0'}`,
                  position: 'relative'
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '8px'
                }}>
                  <div style={{
                    fontSize: '20px',
                    minWidth: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {step.status === 'in_progress' && (
                      <div style={{
                        animation: 'spin 1s linear infinite',
                        fontSize: '16px'
                      }}>
                        ⏳
                      </div>
                    )}
                    {step.status !== 'in_progress' && getStepIcon(step)}
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: '600',
                      color: getStepColor(step),
                      marginBottom: '4px'
                    }}>
                      {step.name}
                    </div>
                    <div style={{
                      fontSize: '14px',
                      color: '#64748b'
                    }}>
                      {step.description}
                    </div>
                  </div>

                  {step.status === 'error' && onRetry && (
                    <button
                      onClick={() => onRetry(step.id)}
                      style={{
                        padding: '6px 12px',
                        border: '1px solid #dc2626',
                        backgroundColor: '#fef2f2',
                        color: '#dc2626',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}
                    >
                      Retry
                    </button>
                  )}
                </div>

                {/* Step Progress Bar */}
                {step.status === 'in_progress' && (
                  <div style={{
                    width: '100%',
                    height: '4px',
                    backgroundColor: '#e5e7eb',
                    borderRadius: '2px',
                    overflow: 'hidden',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      width: `${step.progress}%`,
                      height: '100%',
                      backgroundColor: '#3b82f6',
                      transition: 'width 0.3s ease',
                      borderRadius: '2px'
                    }} />
                  </div>
                )}

                {/* Error Message */}
                {step.status === 'error' && step.errorMessage && (
                  <div style={{
                    padding: '8px 12px',
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '4px',
                    fontSize: '13px',
                    color: '#991b1b',
                    marginTop: '8px'
                  }}>
                    {step.errorMessage}
                  </div>
                )}

                {/* Step Details */}
                {step.details && step.details.length > 0 && (
                  <div style={{ marginTop: '8px' }}>
                    {step.details.map((detail, idx) => (
                      <div
                        key={idx}
                        style={{
                          fontSize: '12px',
                          color: '#64748b',
                          marginBottom: '4px',
                          paddingLeft: '16px',
                          position: 'relative'
                        }}
                      >
                        <span style={{
                          position: 'absolute',
                          left: '0',
                          color: '#3b82f6'
                        }}>
                          •
                        </span>
                        {detail}
                      </div>
                    ))}
                  </div>
                )}

                {/* Timing Info */}
                {(step.startTime || step.estimatedTime) && (
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '8px',
                    fontSize: '11px',
                    color: '#9ca3af'
                  }}>
                    {step.startTime && (
                      <span>
                        Started: {step.startTime.toLocaleTimeString()}
                      </span>
                    )}
                    {step.estimatedTime && step.status !== 'completed' && (
                      <span>
                        Est: {formatTime(step.estimatedTime)}
                      </span>
                    )}
                    {step.endTime && step.startTime && (
                      <span>
                        Duration: {formatTime((step.endTime.getTime() - step.startTime.getTime()) / 1000)}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '24px',
          borderTop: '1px solid #e5e7eb',
          backgroundColor: '#f8fafc',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            {isGenerationComplete 
              ? (hasErrors 
                  ? 'Some steps encountered errors. You can retry failed steps or continue with partial results.'
                  : 'All content has been generated successfully!')
              : 'Content generation is in progress. This may take a few minutes depending on complexity.'
            }
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            {!isGenerationComplete && onCancel && (
              <button
                onClick={onCancel}
                style={{
                  padding: '8px 16px',
                  border: '1px solid #d1d5db',
                  backgroundColor: 'white',
                  color: '#374151',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Cancel
              </button>
            )}
            
            {isGenerationComplete && onClose && (
              <button
                onClick={onClose}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: hasErrors ? '#f59e0b' : '#059669',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                {hasErrors ? 'View Results' : 'Continue'}
              </button>
            )}
          </div>
        </div>
      </div>

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