import React, { useState } from 'react';
import { ImportWizard } from './ImportWizardSimple';
import { ContentAnalysis } from './ContentAnalysis';
import { EnhancementSuggestions } from './EnhancementSuggestions';
import { ContentComparison } from './ContentComparison';
import { useStatusFeedback } from './StatusFeedback';
import type { ImportedContent } from '../hooks/useImport';
import type { AnalysisResult } from './ContentAnalysis';
import type { EnhancementSuggestions as EnhancementSuggestionsType, ContentEnhancement } from './EnhancementSuggestions';

type WorkflowStep = 'import' | 'analysis' | 'enhancement' | 'comparison' | 'complete';

interface ImportAnalysisWorkflowProps {
  onWorkflowComplete?: (finalContent: ImportedContent[]) => void;
}

export function ImportAnalysisWorkflow({ onWorkflowComplete }: ImportAnalysisWorkflowProps) {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('import');
  const [importedContent, setImportedContent] = useState<ImportedContent[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [enhancementSuggestions, setEnhancementSuggestions] = useState<EnhancementSuggestionsType | null>(null);
  const [enhancedContent, setEnhancedContent] = useState<ImportedContent[]>([]);
  const [workflowHistory, setWorkflowHistory] = useState<string[]>([]);
  const statusFeedback = useStatusFeedback();

  const addToHistory = (action: string) => {
    setWorkflowHistory(prev => [...prev, `${new Date().toLocaleTimeString()}: ${action}`]);
  };

  const handleImportComplete = (content: ImportedContent[]) => {
    setImportedContent(content);
    addToHistory(`Imported ${content.length} content items`);
    setCurrentStep('analysis');
    statusFeedback.showSuccess('Import Complete', `Successfully imported ${content.length} items`);
  };

  const handleAnalysisComplete = (analysis: AnalysisResult) => {
    setAnalysisResult(analysis);
    addToHistory('Content analysis completed');
    statusFeedback.showSuccess('Analysis Complete', 'Content has been analyzed');
  };

  const handleRequestEnhancement = () => {
    setCurrentStep('enhancement');
    addToHistory('User requested enhancement suggestions');
  };

  const handleEnhancementsGenerated = (suggestions: EnhancementSuggestionsType) => {
    setEnhancementSuggestions(suggestions);
    addToHistory(`Generated ${suggestions.content_enhancements.length} enhancement suggestions`);
  };

  const handleApplyEnhancement = (enhancement: ContentEnhancement) => {
    // In a real implementation, this would apply the enhancement to the content
    // For now, we'll simulate by creating enhanced content
    const enhanced = importedContent.map(content => {
      if (content.id === enhancement.section_id) {
        return {
          ...content,
          content: enhancement.suggested_content,
          metadata: {
            ...content.metadata,
            enhanced: true,
            enhancement_type: enhancement.enhancement_type
          }
        };
      }
      return content;
    });
    setEnhancedContent(enhanced);
    addToHistory(`Applied ${enhancement.enhancement_type} enhancement to section`);
  };

  const handleProceedToComparison = () => {
    // If no enhancements were applied, use the original content
    if (enhancedContent.length === 0) {
      setEnhancedContent(importedContent);
    }
    setCurrentStep('comparison');
    addToHistory('Proceeding to content comparison');
  };

  const handleAcceptChanges = () => {
    addToHistory('User accepted all changes');
    setCurrentStep('complete');
    statusFeedback.showSuccess('Changes Accepted', 'All enhancements have been applied');
    onWorkflowComplete?.(enhancedContent);
  };

  const handleRejectChanges = () => {
    addToHistory('User rejected changes');
    setEnhancedContent(importedContent);
    statusFeedback.showInfo('Changes Rejected', 'Reverted to original content');
  };

  const getStepNumber = (step: WorkflowStep): number => {
    const steps: WorkflowStep[] = ['import', 'analysis', 'enhancement', 'comparison', 'complete'];
    return steps.indexOf(step) + 1;
  };

  const isStepComplete = (step: WorkflowStep): boolean => {
    const currentStepNumber = getStepNumber(currentStep);
    const stepNumber = getStepNumber(step);
    return stepNumber < currentStepNumber;
  };

  const isStepActive = (step: WorkflowStep): boolean => {
    return step === currentStep;
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Progress Indicator */}
      <div style={{
        marginBottom: '32px',
        padding: '20px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          Import & Analysis Workflow
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {(['import', 'analysis', 'enhancement', 'comparison', 'complete'] as WorkflowStep[]).map((step, index) => (
            <React.Fragment key={step}>
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                flex: 1
              }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: isStepComplete(step) ? '#10b981' : isStepActive(step) ? '#3b82f6' : '#e5e7eb',
                  color: isStepComplete(step) || isStepActive(step) ? 'white' : '#6b7280',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '600',
                  fontSize: '16px',
                  marginBottom: '8px'
                }}>
                  {isStepComplete(step) ? '✓' : index + 1}
                </div>
                <span style={{
                  fontSize: '12px',
                  color: isStepActive(step) ? '#1f2937' : '#6b7280',
                  fontWeight: isStepActive(step) ? '600' : '400',
                  textTransform: 'capitalize'
                }}>
                  {step}
                </span>
              </div>
              {index < 4 && (
                <div style={{
                  flex: 1,
                  height: '2px',
                  backgroundColor: isStepComplete(step) ? '#10b981' : '#e5e7eb',
                  margin: '0 8px',
                  marginBottom: '24px'
                }} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ marginBottom: '24px' }}>
        {currentStep === 'import' && (
          <ImportWizard onImportComplete={handleImportComplete} />
        )}

        {currentStep === 'analysis' && importedContent.length > 0 && (
          <ContentAnalysis
            importedContent={importedContent}
            onAnalysisComplete={handleAnalysisComplete}
            onRequestEnhancement={handleRequestEnhancement}
          />
        )}

        {currentStep === 'enhancement' && importedContent.length > 0 && analysisResult && (
          <div>
            <EnhancementSuggestions
              importedContent={importedContent}
              analysisResult={analysisResult}
              onEnhancementsGenerated={handleEnhancementsGenerated}
              onApplyEnhancement={handleApplyEnhancement}
            />
            <div style={{
              marginTop: '16px',
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button
                onClick={handleProceedToComparison}
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
                Proceed to Comparison →
              </button>
            </div>
          </div>
        )}

        {currentStep === 'comparison' && importedContent.length > 0 && enhancedContent.length > 0 && (
          <ContentComparison
            originalContent={importedContent}
            enhancedContent={enhancedContent}
            originalAnalysis={analysisResult || undefined}
            onAcceptChanges={handleAcceptChanges}
            onRejectChanges={handleRejectChanges}
          />
        )}

        {currentStep === 'complete' && (
          <div style={{
            padding: '40px',
            backgroundColor: '#d1fae5',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
            <h3 style={{ fontSize: '20px', fontWeight: '600', color: '#065f46', marginBottom: '8px' }}>
              Workflow Complete!
            </h3>
            <p style={{ fontSize: '14px', color: '#047857', marginBottom: '24px' }}>
              Your content has been successfully imported, analyzed, and enhanced.
            </p>
            <button
              onClick={() => {
                setCurrentStep('import');
                setImportedContent([]);
                setAnalysisResult(null);
                setEnhancementSuggestions(null);
                setEnhancedContent([]);
                addToHistory('Started new workflow');
              }}
              style={{
                padding: '12px 24px',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Start New Import
            </button>
          </div>
        )}
      </div>

      {/* Workflow History */}
      <div style={{
        padding: '16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}>
        <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
          Workflow History
        </h3>
        <div style={{
          maxHeight: '120px',
          overflow: 'auto',
          fontSize: '12px',
          color: '#6b7280'
        }}>
          {workflowHistory.length === 0 ? (
            <p>No actions yet. Start by importing content.</p>
          ) : (
            workflowHistory.map((entry, index) => (
              <div key={index} style={{ marginBottom: '4px' }}>
                {entry}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
