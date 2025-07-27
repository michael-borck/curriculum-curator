import React, { useState, useEffect } from 'react';
import { useMaintenanceService } from '../hooks/useMaintenanceService';
import { useStatusFeedback } from './StatusFeedback';
import type { 
  MaintenanceOperation, 
  MaintenanceIssue, 
  MaintenanceResult,
  MaintenanceOperationInfo,
  MaintenanceRecommendation,
  SystemHealthSummary
} from '../hooks/useMaintenanceService';

interface MaintenanceCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MaintenanceCenter({ isOpen, onClose }: MaintenanceCenterProps) {
  const maintenance = useMaintenanceService();
  const statusFeedback = useStatusFeedback();
  
  const [currentTab, setCurrentTab] = useState<'overview' | 'issues' | 'operations' | 'schedule' | 'reports'>('overview');
  const [selectedOperations, setSelectedOperations] = useState<MaintenanceOperation[]>([]);
  const [isDryRun, setIsDryRun] = useState(true);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [operationInProgress, setOperationInProgress] = useState(false);

  useEffect(() => {
    if (isOpen) {
      maintenance.loadSystemHealth();
      maintenance.loadMaintenanceIssues();
      maintenance.loadAvailableOperations();
      maintenance.loadRecommendations();
    }
  }, [isOpen, maintenance]);

  const handleRunMaintenance = async () => {
    if (selectedOperations.length === 0) {
      statusFeedback.showWarning('No Operations Selected', 'Please select at least one maintenance operation');
      return;
    }

    if (!isDryRun) {
      setShowConfirmDialog(true);
      return;
    }

    await executeMaintenanceOperations();
  };

  const executeMaintenanceOperations = async () => {
    setOperationInProgress(true);
    setShowConfirmDialog(false);

    try {
      const results = await maintenance.performMaintenance(selectedOperations, isDryRun, true);
      
      if (results && results.length > 0) {
        const successCount = results.filter(r => r.success).length;
        const totalSpaceReclaimed = results.reduce((sum, r) => sum + r.space_reclaimed_mb, 0);
        
        if (successCount === results.length) {
          statusFeedback.showSuccess(
            'Maintenance Complete!',
            `Successfully completed ${successCount} operations. ${totalSpaceReclaimed.toFixed(1)} MB reclaimed.`,
            5000
          );
        } else {
          statusFeedback.showWarning(
            'Maintenance Partially Complete',
            `${successCount}/${results.length} operations completed successfully.`
          );
        }
        
        // Refresh data
        maintenance.loadSystemHealth();
        maintenance.loadMaintenanceIssues();
        setSelectedOperations([]);
      }
    } catch (error) {
      statusFeedback.showError(
        'Maintenance Failed',
        `Failed to perform maintenance: ${error}`
      );
    } finally {
      setOperationInProgress(false);
    }
  };

  const handleOperationToggle = (operation: MaintenanceOperation) => {
    setSelectedOperations(prev => 
      prev.includes(operation)
        ? prev.filter(op => op !== operation)
        : [...prev, operation]
    );
  };

  const handleApplyRecommendations = () => {
    const recommendedOperations = maintenance.recommendations
      .filter(r => r.can_auto_execute)
      .map(r => r.operation);
    
    setSelectedOperations(recommendedOperations);
    statusFeedback.showInfo(
      'Recommendations Applied',
      `Selected ${recommendedOperations.length} recommended operations`
    );
  };

  const getHealthScoreColor = (score: number): string => {
    if (score >= 90) return '#10b981'; // green
    if (score >= 70) return '#f59e0b'; // yellow
    if (score >= 50) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const getIssueSeverityColor = (severity: 'Low' | 'Medium' | 'High' | 'Critical'): string => {
    switch (severity) {
      case 'Critical': return '#dc2626';
      case 'High': return '#ea580c';
      case 'Medium': return '#d97706';
      case 'Low': return '#65a30d';
      default: return '#6b7280';
    }
  };

  const getOperationIcon = (operation: MaintenanceOperation): string => {
    switch (operation) {
      case 'DatabaseVacuum': return '🗜️';
      case 'IntegrityCheck': return '🔍';
      case 'OrphanedDataCleanup': return '🧹';
      case 'RetentionPolicyCleanup': return '📅';
      case 'StorageOptimization': return '💾';
      case 'IndexMaintenance': return '⚡';
      case 'ContentDeduplication': return '🔄';
      case 'FileSystemAudit': return '📋';
      default: return '⚙️';
    }
  };

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
        width: '95vw',
        height: '90vh',
        maxWidth: '1200px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#f8fafc'
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '24px', color: '#1e293b' }}>
              🔧 Maintenance Center
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>
              Keep your curriculum data healthy and optimized
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '28px',
              cursor: 'pointer',
              color: '#6b7280'
            }}
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#f8fafc'
        }}>
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'issues', label: 'Issues', icon: '⚠️' },
            { id: 'operations', label: 'Operations', icon: '⚙️' },
            { id: 'schedule', label: 'Schedule', icon: '📅' },
            { id: 'reports', label: 'Reports', icon: '📈' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id as any)}
              style={{
                padding: '12px 20px',
                border: 'none',
                background: currentTab === tab.id ? 'white' : 'transparent',
                borderBottom: currentTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: currentTab === tab.id ? '600' : '400',
                color: currentTab === tab.id ? '#1e293b' : '#64748b',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
          {currentTab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
              {/* System Health Score */}
              <div style={{
                padding: '20px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                backgroundColor: 'white'
              }}>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#1e293b' }}>
                  System Health
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    background: `conic-gradient(${getHealthScoreColor(maintenance.systemHealth?.overall_health_score || 0)} ${(maintenance.systemHealth?.overall_health_score || 0) * 3.6}deg, #e5e7eb 0deg)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative'
                  }}>
                    <div style={{
                      width: '60px',
                      height: '60px',
                      borderRadius: '50%',
                      backgroundColor: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '16px',
                      fontWeight: '600',
                      color: getHealthScoreColor(maintenance.systemHealth?.overall_health_score || 0)
                    }}>
                      {maintenance.systemHealth?.overall_health_score || 0}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '4px' }}>
                      Overall Health Score
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      {maintenance.systemHealth?.total_issues || 0} issues found
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      {maintenance.systemHealth?.estimated_space_reclaimable_mb?.toFixed(1) || 0} MB reclaimable
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div style={{
                padding: '20px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                backgroundColor: 'white'
              }}>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#1e293b' }}>
                  Quick Actions
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <button
                    onClick={handleApplyRecommendations}
                    disabled={!maintenance.recommendations || maintenance.recommendations.length === 0}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      opacity: maintenance.recommendations?.length ? 1 : 0.5
                    }}
                  >
                    ⚡ Apply Recommendations ({maintenance.recommendations?.length || 0})
                  </button>
                  <button
                    onClick={() => maintenance.performMaintenance(['DatabaseVacuum'], true, false)}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: '#10b981',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '14px',
                      cursor: 'pointer'
                    }}
                  >
                    🗜️ Quick Database Vacuum
                  </button>
                  <button
                    onClick={() => maintenance.analyzeMaintenanceIssues()}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: '#6b7280',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '14px',
                      cursor: 'pointer'
                    }}
                  >
                    🔍 Refresh Analysis
                  </button>
                </div>
              </div>

              {/* Critical Issues */}
              {maintenance.issues && maintenance.issues.filter(i => i.severity === 'Critical').length > 0 && (
                <div style={{
                  padding: '20px',
                  border: '2px solid #dc2626',
                  borderRadius: '8px',
                  backgroundColor: '#fef2f2'
                }}>
                  <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#dc2626' }}>
                    ⚠️ Critical Issues
                  </h3>
                  {maintenance.issues.filter(i => i.severity === 'Critical').map((issue, index) => (
                    <div key={index} style={{ marginBottom: '8px' }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#dc2626' }}>
                        {issue.title}
                      </div>
                      <div style={{ fontSize: '12px', color: '#7f1d1d' }}>
                        {issue.description}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {currentTab === 'issues' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
                  Maintenance Issues
                </h3>
                <button
                  onClick={() => maintenance.analyzeMaintenanceIssues()}
                  disabled={maintenance.isAnalyzing}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    opacity: maintenance.isAnalyzing ? 0.7 : 1
                  }}
                >
                  {maintenance.isAnalyzing ? 'Analyzing...' : '🔄 Refresh'}
                </button>
              </div>

              {maintenance.issues && maintenance.issues.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {maintenance.issues.map((issue, index) => (
                    <div key={index} style={{
                      padding: '16px',
                      border: `1px solid ${getIssueSeverityColor(issue.severity)}`,
                      borderRadius: '8px',
                      backgroundColor: 'white'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                        <div>
                          <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', color: '#1e293b' }}>
                            {issue.title}
                          </h4>
                          <span style={{
                            fontSize: '12px',
                            padding: '2px 8px',
                            borderRadius: '10px',
                            backgroundColor: getIssueSeverityColor(issue.severity),
                            color: 'white'
                          }}>
                            {issue.severity}
                          </span>
                        </div>
                        <div style={{ textAlign: 'right', fontSize: '12px', color: '#64748b' }}>
                          {issue.affected_items} items affected
                          {issue.estimated_space_savings_mb && (
                            <div>{issue.estimated_space_savings_mb.toFixed(1)} MB reclaimable</div>
                          )}
                        </div>
                      </div>
                      <p style={{ margin: '8px 0', fontSize: '14px', color: '#64748b' }}>
                        {issue.description}
                      </p>
                      {issue.can_auto_fix && (
                        <button
                          onClick={() => setSelectedOperations(prev => 
                            prev.includes(issue.operation) ? prev : [...prev, issue.operation]
                          )}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#10b981',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '12px',
                            cursor: 'pointer'
                          }}
                        >
                          ✨ Auto-fix Available
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
                  <h3 style={{ margin: '0 0 8px 0' }}>No Issues Found</h3>
                  <p style={{ margin: 0 }}>Your system is in excellent condition!</p>
                </div>
              )}
            </div>
          )}

          {currentTab === 'operations' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
                  Maintenance Operations
                </h3>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
                    <input
                      type="checkbox"
                      checked={isDryRun}
                      onChange={(e) => setIsDryRun(e.target.checked)}
                    />
                    Dry Run (Preview Only)
                  </label>
                  <button
                    onClick={handleRunMaintenance}
                    disabled={selectedOperations.length === 0 || operationInProgress}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: selectedOperations.length > 0 ? '#059669' : '#9ca3af',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: selectedOperations.length > 0 ? 'pointer' : 'not-allowed',
                      fontSize: '14px'
                    }}
                  >
                    {operationInProgress ? 'Running...' : `Run Selected (${selectedOperations.length})`}
                  </button>
                </div>
              </div>

              {maintenance.availableOperations && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '16px' }}>
                  {maintenance.availableOperations.map((opInfo, index) => (
                    <div key={index} style={{
                      padding: '16px',
                      border: selectedOperations.includes(opInfo.operation) ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                      borderRadius: '8px',
                      backgroundColor: 'white',
                      cursor: 'pointer'
                    }}
                      onClick={() => handleOperationToggle(opInfo.operation)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                        <input
                          type="checkbox"
                          checked={selectedOperations.includes(opInfo.operation)}
                          onChange={() => {}} // Handled by parent click
                          style={{ pointerEvents: 'none' }}
                        />
                        <span style={{ fontSize: '20px' }}>
                          {getOperationIcon(opInfo.operation)}
                        </span>
                        <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
                          {opInfo.display_name}
                        </h4>
                      </div>
                      <p style={{ margin: '0 0 12px 32px', fontSize: '14px', color: '#64748b' }}>
                        {opInfo.description}
                      </p>
                      <div style={{ marginLeft: '32px', display: 'flex', gap: '16px', fontSize: '12px', color: '#9ca3af' }}>
                        <span>⏱️ ~{opInfo.estimated_duration_minutes}min</span>
                        {opInfo.requires_backup && <span>💾 Requires backup</span>}
                        {opInfo.destructive && <span>⚠️ Destructive</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {currentTab === 'schedule' && (
            <div>
              <h3 style={{ margin: '0 0 20px 0', fontSize: '20px', color: '#1e293b' }}>
                Automatic Maintenance Schedule
              </h3>
              <div style={{ 
                padding: '20px', 
                backgroundColor: '#f8fafc', 
                borderRadius: '8px',
                textAlign: 'center',
                color: '#64748b'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🚧</div>
                <h4 style={{ margin: '0 0 8px 0' }}>Scheduling Features Coming Soon</h4>
                <p style={{ margin: 0 }}>Automatic maintenance scheduling will be available in a future update.</p>
              </div>
            </div>
          )}

          {currentTab === 'reports' && (
            <div>
              <h3 style={{ margin: '0 0 20px 0', fontSize: '20px', color: '#1e293b' }}>
                Maintenance Reports
              </h3>
              <div style={{ 
                padding: '20px', 
                backgroundColor: '#f8fafc', 
                borderRadius: '8px',
                textAlign: 'center',
                color: '#64748b'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
                <h4 style={{ margin: '0 0 8px 0' }}>Detailed Reports Coming Soon</h4>
                <p style={{ margin: 0 }}>Comprehensive maintenance reports and analytics will be available in a future update.</p>
              </div>
            </div>
          )}
        </div>

        {/* Progress Display */}
        {maintenance.maintenanceProgress && (
          <div style={{
            padding: '16px 24px',
            borderTop: '1px solid #e5e7eb',
            backgroundColor: '#f8fafc'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>
                {maintenance.getOperationDisplayName(maintenance.maintenanceProgress.operation)}
              </span>
              <span style={{ fontSize: '12px', color: '#64748b' }}>
                {maintenance.maintenanceProgress.progress_percentage.toFixed(0)}%
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: '#e5e7eb',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '8px'
            }}>
              <div style={{
                width: `${maintenance.maintenanceProgress.progress_percentage}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              {maintenance.maintenanceProgress.current_step}: {maintenance.maintenanceProgress.current_item}
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
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
          zIndex: 1100
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '400px',
            width: '90vw'
          }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#dc2626' }}>
              ⚠️ Confirm Maintenance Operations
            </h3>
            <p style={{ margin: '0 0 16px 0', color: '#64748b' }}>
              You are about to perform {selectedOperations.length} maintenance operation(s) on your system. 
              This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowConfirmDialog(false)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid #d1d5db',
                  backgroundColor: 'white',
                  color: '#374151',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={executeMaintenanceOperations}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Proceed
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}