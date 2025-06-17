import React, { useState, useEffect } from 'react';
import { useBackup, BackupListItem, BackupFilter } from '../hooks/useBackup';
import { useStatusFeedback } from './StatusFeedback';
import { useDesktopLayout } from '../utils/desktopLayout';

interface BackupRecoveryProps {
  isOpen: boolean;
  onClose: () => void;
  onSessionRestore?: (sessionId: string) => void;
  currentSessionId?: string;
}

export function BackupRecovery({ 
  isOpen, 
  onClose, 
  onSessionRestore,
  currentSessionId 
}: BackupRecoveryProps) {
  const backup = useBackup();
  const statusFeedback = useStatusFeedback();
  const layout = useDesktopLayout();
  
  const [activeTab, setActiveTab] = useState<'list' | 'config'>('list');
  const [filterSessionId, setFilterSessionId] = useState<string>('');
  const [showAutoBackupsOnly, setShowAutoBackupsOnly] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showRestoreConfirm, setShowRestoreConfirm] = useState<string | null>(null);
  const [selectedBackups, setSelectedBackups] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isOpen) {
      backup.loadBackups();
      backup.loadStatistics();
      backup.loadConfig();
    }
  }, [isOpen, backup]);

  const handleFilter = async () => {
    const filter: BackupFilter = {};
    
    if (filterSessionId) {
      filter.session_id = filterSessionId;
    }
    
    if (showAutoBackupsOnly) {
      filter.auto_generated_only = true;
    }
    
    filter.limit = 50;
    
    await backup.loadBackups(filter);
  };

  const handleCreateBackup = async () => {
    if (!currentSessionId) {
      statusFeedback.showWarning('No Active Session', 'Please select a session to backup');
      return;
    }

    try {
      const backupId = await backup.createManualBackup(currentSessionId);
      statusFeedback.showSuccess(
        'Backup Created',
        `Manual backup created successfully`,
        3000
      );
    } catch (error) {
      statusFeedback.showError(
        'Backup Failed',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const handleRestore = async (backupId: string) => {
    try {
      const newSessionId = await backup.restoreFromBackup(backupId);
      setShowRestoreConfirm(null);
      
      statusFeedback.showSuccess(
        'Backup Restored',
        `Session restored successfully`,
        4000
      );
      
      if (onSessionRestore) {
        onSessionRestore(newSessionId);
      }
      
      onClose();
    } catch (error) {
      statusFeedback.showError(
        'Restore Failed',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const handleDelete = async (backupId: string) => {
    try {
      await backup.deleteBackup(backupId);
      setShowDeleteConfirm(null);
      statusFeedback.showSuccess('Backup Deleted', '', 2000);
    } catch (error) {
      statusFeedback.showError(
        'Delete Failed',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const handleBulkDelete = async () => {
    if (selectedBackups.size === 0) return;
    
    try {
      for (const backupId of selectedBackups) {
        await backup.deleteBackup(backupId);
      }
      setSelectedBackups(new Set());
      statusFeedback.showSuccess(
        'Backups Deleted',
        `${selectedBackups.size} backups deleted successfully`,
        3000
      );
    } catch (error) {
      statusFeedback.showError(
        'Bulk Delete Failed',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const handleCleanup = async () => {
    try {
      const cleanedCount = await backup.cleanupOldBackups();
      statusFeedback.showSuccess(
        'Cleanup Complete',
        cleanedCount > 0 ? `Cleaned up ${cleanedCount} old backups` : 'No old backups to clean',
        3000
      );
    } catch (error) {
      statusFeedback.showError(
        'Cleanup Failed',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const toggleBackupSelection = (backupId: string) => {
    const newSelection = new Set(selectedBackups);
    if (newSelection.has(backupId)) {
      newSelection.delete(backupId);
    } else {
      newSelection.add(backupId);
    }
    setSelectedBackups(newSelection);
  };

  const selectAllBackups = () => {
    if (selectedBackups.size === backup.backups.length) {
      setSelectedBackups(new Set());
    } else {
      setSelectedBackups(new Set(backup.backups.map(b => b.id)));
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
        width: '90vw',
        height: '80vh',
        maxWidth: '1000px',
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
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
              Backup & Recovery
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>
              {backup.statistics && (
                `${backup.statistics.total_backups} backups • ${backup.formatBackupSize(backup.statistics.total_size)} total`
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
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
          gap: '4px',
          backgroundColor: '#f1f5f9',
          padding: '4px',
          margin: '16px 24px 0',
          borderRadius: '8px'
        }}>
          <button
            onClick={() => setActiveTab('list')}
            style={{
              flex: 1,
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: activeTab === 'list' ? 'white' : 'transparent',
              color: activeTab === 'list' ? '#3b82f6' : '#64748b',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            📋 Backup List
          </button>
          <button
            onClick={() => setActiveTab('config')}
            style={{
              flex: 1,
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: activeTab === 'config' ? 'white' : 'transparent',
              color: activeTab === 'config' ? '#3b82f6' : '#64748b',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            ⚙️ Settings
          </button>
        </div>

        {activeTab === 'list' && (
          <>
            {/* Controls */}
            <div style={{
              padding: '16px 24px',
              borderBottom: '1px solid #e5e7eb',
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
              flexWrap: 'wrap'
            }}>
              <input
                type="text"
                placeholder="Filter by session ID..."
                value={filterSessionId}
                onChange={(e) => setFilterSessionId(e.target.value)}
                style={{
                  flex: 1,
                  minWidth: '200px',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
              
              <button
                onClick={handleFilter}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Filter
              </button>

              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={showAutoBackupsOnly}
                  onChange={(e) => setShowAutoBackupsOnly(e.target.checked)}
                />
                <span style={{ fontSize: '14px' }}>Auto backups only</span>
              </label>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={handleCreateBackup}
                  disabled={!currentSessionId}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: !currentSessionId ? '#9ca3af' : '#059669',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: !currentSessionId ? 'not-allowed' : 'pointer',
                    fontSize: '14px'
                  }}
                >
                  💾 Create Backup
                </button>

                {selectedBackups.size > 0 && (
                  <button
                    onClick={handleBulkDelete}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#dc2626',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    🗑️ Delete ({selectedBackups.size})
                  </button>
                )}

                <button
                  onClick={handleCleanup}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  🧹 Cleanup
                </button>
              </div>
            </div>

            {/* Backup List */}
            <div style={{ flex: 1, overflow: 'auto', padding: '16px 24px' }}>
              {backup.isLoading ? (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '200px',
                  fontSize: '16px',
                  color: '#64748b'
                }}>
                  Loading backups...
                </div>
              ) : backup.error ? (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '200px',
                  fontSize: '16px',
                  color: '#dc2626'
                }}>
                  Error: {backup.error}
                </div>
              ) : backup.backups.length === 0 ? (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '200px',
                  fontSize: '16px',
                  color: '#64748b'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>💾</div>
                  <div>No backups found</div>
                  <div style={{ fontSize: '14px', marginTop: '8px' }}>
                    Create your first backup to get started
                  </div>
                </div>
              ) : (
                <>
                  {/* Select All */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '12px',
                    backgroundColor: '#f8fafc',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    border: '1px solid #e2e8f0'
                  }}>
                    <input
                      type="checkbox"
                      checked={selectedBackups.size === backup.backups.length && backup.backups.length > 0}
                      onChange={selectAllBackups}
                    />
                    <span style={{ fontSize: '14px', fontWeight: '500' }}>
                      Select All ({backup.backups.length} backups)
                    </span>
                  </div>

                  {/* Backup Items */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {backup.backups.map((backupItem) => (
                      <div
                        key={backupItem.id}
                        style={{
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          padding: '16px',
                          backgroundColor: selectedBackups.has(backupItem.id) ? '#f0f9ff' : 'white',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '16px'
                        }}
                      >
                        {/* Selection Checkbox */}
                        <input
                          type="checkbox"
                          checked={selectedBackups.has(backupItem.id)}
                          onChange={() => toggleBackupSelection(backupItem.id)}
                        />

                        {/* Backup Icon */}
                        <div style={{ fontSize: '24px' }}>
                          {backup.getBackupTypeIcon(backupItem.backup_type)}
                        </div>

                        {/* Backup Info */}
                        <div style={{ flex: 1 }}>
                          <h3 style={{
                            margin: '0 0 4px 0',
                            fontSize: '16px',
                            fontWeight: '600',
                            color: '#1e293b'
                          }}>
                            {backupItem.session_name}
                          </h3>
                          <div style={{
                            fontSize: '12px',
                            color: '#64748b',
                            marginBottom: '8px'
                          }}>
                            {backup.getBackupTypeName(backupItem.backup_type)} • 
                            {backup.formatRelativeTime(backupItem.created_at)} • 
                            {backup.formatBackupSize(backupItem.file_size)} • 
                            {backupItem.content_count} items
                          </div>
                          
                          {/* Status Indicator */}
                          <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '12px',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            backgroundColor: backupItem.is_recoverable ? '#dcfce7' : '#fee2e2',
                            color: backupItem.is_recoverable ? '#166534' : '#dc2626'
                          }}>
                            {backupItem.is_recoverable ? '✓ Recoverable' : '⚠ Corrupted'}
                          </div>
                        </div>

                        {/* Actions */}
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => setShowRestoreConfirm(backupItem.id)}
                            disabled={!backupItem.is_recoverable}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: !backupItem.is_recoverable ? '#9ca3af' : '#059669',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: !backupItem.is_recoverable ? 'not-allowed' : 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            🔄 Restore
                          </button>
                          <button
                            onClick={() => setShowDeleteConfirm(backupItem.id)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#dc2626',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </>
        )}

        {activeTab === 'config' && (
          <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
            <div style={{ maxWidth: '600px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', marginBottom: '16px' }}>
                Backup Configuration
              </h3>
              
              {backup.config ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {/* Enable Backups */}
                  <label style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      checked={backup.config.enabled}
                      onChange={(e) => backup.updateConfig({
                        ...backup.config!,
                        enabled: e.target.checked
                      })}
                      style={{ width: '18px', height: '18px' }}
                    />
                    <div>
                      <span style={{ fontSize: '16px', fontWeight: '500' }}>Enable Automatic Backups</span>
                      <div style={{ fontSize: '14px', color: '#64748b' }}>
                        Automatically create backups based on your schedule
                      </div>
                    </div>
                  </label>

                  {/* Backup Interval */}
                  <div>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                      Backup Frequency
                    </label>
                    <select
                      value={backup.getIntervalDisplayName(backup.config.auto_backup_interval)}
                      onChange={(e) => {
                        // Convert display name back to interval object
                        const intervalMap: Record<string, any> = {
                          'Never': { Never: null },
                          'Every Session': { EverySession: null },
                          'Every 5 Minutes': { Every5Minutes: null },
                          'Every 15 Minutes': { Every15Minutes: null },
                          'Every 30 Minutes': { Every30Minutes: null },
                          'Hourly': { Hourly: null },
                          'Daily': { Daily: null }
                        };
                        backup.updateConfig({
                          ...backup.config!,
                          auto_backup_interval: intervalMap[e.target.value]
                        });
                      }}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '14px'
                      }}
                    >
                      <option value="Never">Never</option>
                      <option value="Every Session">Every Session</option>
                      <option value="Every 5 Minutes">Every 5 Minutes</option>
                      <option value="Every 15 Minutes">Every 15 Minutes</option>
                      <option value="Every 30 Minutes">Every 30 Minutes</option>
                      <option value="Hourly">Hourly</option>
                      <option value="Daily">Daily</option>
                    </select>
                  </div>

                  {/* Trigger Options */}
                  <div>
                    <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '12px' }}>
                      Automatic Backup Triggers
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={backup.config.backup_on_session_close}
                          onChange={(e) => backup.updateConfig({
                            ...backup.config!,
                            backup_on_session_close: e.target.checked
                          })}
                        />
                        <span style={{ fontSize: '14px' }}>Backup when closing sessions</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={backup.config.backup_on_content_generation}
                          onChange={(e) => backup.updateConfig({
                            ...backup.config!,
                            backup_on_content_generation: e.target.checked
                          })}
                        />
                        <span style={{ fontSize: '14px' }}>Backup after generating content</span>
                      </label>
                    </div>
                  </div>

                  {/* Backup Limits */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                        Max Backups per Session
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={backup.config.max_backups_per_session}
                        onChange={(e) => backup.updateConfig({
                          ...backup.config!,
                          max_backups_per_session: parseInt(e.target.value)
                        })}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #d1d5db',
                          borderRadius: '6px',
                          fontSize: '14px'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                        Max Total Backups
                      </label>
                      <input
                        type="number"
                        min="10"
                        max="1000"
                        value={backup.config.max_total_backups}
                        onChange={(e) => backup.updateConfig({
                          ...backup.config!,
                          max_total_backups: parseInt(e.target.value)
                        })}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #d1d5db',
                          borderRadius: '6px',
                          fontSize: '14px'
                        }}
                      />
                    </div>
                  </div>

                  {/* Compression */}
                  <label style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      checked={backup.config.compress_backups}
                      onChange={(e) => backup.updateConfig({
                        ...backup.config!,
                        compress_backups: e.target.checked
                      })}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <div>
                      <span style={{ fontSize: '14px', fontWeight: '500' }}>Compress backup files</span>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>
                        Reduces file size but may take longer to create
                      </div>
                    </div>
                  </label>
                </div>
              ) : (
                <div>Loading configuration...</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '400px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
          }}>
            <h3 style={{ margin: '0 0 12px 0', color: '#1e293b' }}>Delete Backup</h3>
            <p style={{ margin: '0 0 20px 0', color: '#64748b' }}>
              Are you sure you want to delete this backup? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowDeleteConfirm(null)}
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
                onClick={() => handleDelete(showDeleteConfirm)}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: '#dc2626',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Restore Confirmation */}
      {showRestoreConfirm && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '400px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
          }}>
            <h3 style={{ margin: '0 0 12px 0', color: '#1e293b' }}>Restore Backup</h3>
            <p style={{ margin: '0 0 20px 0', color: '#64748b' }}>
              This will create a new session from the backup. Your current work will not be affected.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowRestoreConfirm(null)}
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
                onClick={() => handleRestore(showRestoreConfirm)}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: '#059669',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Restore
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}