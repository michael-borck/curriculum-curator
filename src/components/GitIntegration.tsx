import React, { useState, useEffect } from 'react';
import { useGit } from '../hooks/useGit';
import { useStatusFeedback } from './StatusFeedback';
import type { GitConfig, GitInitOptions, CommitOptions, GitHistory } from '../hooks/useGit';

interface GitIntegrationProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GitIntegration({ isOpen, onClose }: GitIntegrationProps) {
  const git = useGit();
  const statusFeedback = useStatusFeedback();
  
  const [activeTab, setActiveTab] = useState<'overview' | 'history' | 'settings'>('overview');
  const [commitMessage, setCommitMessage] = useState('');
  const [showCommitDialog, setShowCommitDialog] = useState(false);
  const [showInitDialog, setShowInitDialog] = useState(false);
  const [initOptions, setInitOptions] = useState<GitInitOptions>({
    repository_path: '',
    initial_commit: true,
    setup_gitignore: true,
    setup_remote: undefined,
  });
  const [history, setHistory] = useState<GitHistory | null>(null);
  const [historyPage, setHistoryPage] = useState(0);

  useEffect(() => {
    if (isOpen) {
      git.loadConfig();
      git.checkInstallation();
      git.detectRepository();
    }
  }, [isOpen, git]);

  const handleEnableGit = async () => {
    if (!git.installationInfo?.is_installed) {
      statusFeedback.showError(
        'Git Not Installed',
        'Git must be installed on your system to use version control features.'
      );
      return;
    }

    if (!git.status?.is_repository) {
      setShowInitDialog(true);
      return;
    }

    // Enable Git integration
    const newConfig: GitConfig = {
      ...git.config!,
      enabled: true,
    };
    
    await git.updateConfig(newConfig);
    statusFeedback.showSuccess(
      'Git Integration Enabled',
      'Version control is now active for this project',
      4000
    );
  };

  const handleDisableGit = async () => {
    const newConfig: GitConfig = {
      ...git.config!,
      enabled: false,
    };
    
    await git.updateConfig(newConfig);
    statusFeedback.showSuccess(
      'Git Integration Disabled',
      'Version control features have been turned off',
      3000
    );
  };

  const handleInitializeRepository = async () => {
    const success = await git.initializeRepository(initOptions);
    if (success) {
      setShowInitDialog(false);
      statusFeedback.showSuccess(
        'Repository Initialized',
        'Git repository has been set up successfully',
        4000
      );
      
      // Enable Git integration
      await handleEnableGit();
    }
  };

  const handleCommit = async () => {
    if (!commitMessage.trim()) {
      statusFeedback.showWarning('Commit Message Required', 'Please enter a commit message');
      return;
    }

    const options: CommitOptions = {
      message: commitMessage.trim(),
      add_all: true,
      specific_files: [],
    };

    const commitHash = await git.commitChanges(options);
    if (commitHash) {
      setShowCommitDialog(false);
      setCommitMessage('');
      statusFeedback.showSuccess(
        'Changes Committed',
        `Commit ${commitHash.substring(0, 8)} created successfully`,
        4000
      );
    }
  };

  const loadHistory = async (page: number = 0) => {
    const result = await git.getHistory(page, 10);
    if (result) {
      setHistory(result);
      setHistoryPage(page);
    }
  };

  useEffect(() => {
    if (activeTab === 'history' && git.config?.enabled) {
      loadHistory(0);
    }
  }, [activeTab, git.config?.enabled]);

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
        height: '85vh',
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
              🔧 Git Integration
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>
              {git.installationInfo?.is_installed 
                ? git.config?.enabled 
                  ? 'Version control is active'
                  : 'Version control is available but disabled'
                : 'Git not installed'
              }
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

        {/* Installation Check */}
        {!git.installationInfo?.is_installed && (
          <div style={{
            margin: '20px 24px',
            padding: '16px',
            backgroundColor: '#fef3c7',
            border: '1px solid #f59e0b',
            borderRadius: '8px'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#92400e', fontSize: '16px' }}>
              ⚠️ Git Not Installed
            </h3>
            <p style={{ margin: '0 0 12px 0', color: '#92400e', fontSize: '14px' }}>
              Git is required for version control features. Please install Git and restart the application.
            </p>
            <a
              href="https://git-scm.com/downloads"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: '#1d4ed8',
                textDecoration: 'underline',
                fontSize: '14px'
              }}
            >
              Download Git →
            </a>
          </div>
        )}

        {git.installationInfo?.is_installed && (
          <>
            {/* Tabs */}
            <div style={{
              display: 'flex',
              gap: '4px',
              backgroundColor: '#f1f5f9',
              padding: '4px',
              margin: '16px 24px 0',
              borderRadius: '8px'
            }}>
              {['overview', 'history', 'settings'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  style={{
                    flex: 1,
                    padding: '8px 16px',
                    border: 'none',
                    borderRadius: '4px',
                    backgroundColor: activeTab === tab ? 'white' : 'transparent',
                    color: activeTab === tab ? '#3b82f6' : '#64748b',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500',
                    textTransform: 'capitalize'
                  }}
                >
                  {tab === 'overview' && '📊'} {tab === 'history' && '📅'} {tab === 'settings' && '⚙️'} {tab}
                </button>
              ))}
            </div>

            {/* Content */}
            <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
              {activeTab === 'overview' && (
                <div>
                  {/* Enable/Disable Git */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '24px',
                    padding: '16px',
                    backgroundColor: '#f8fafc',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0'
                  }}>
                    <div>
                      <h3 style={{ margin: '0 0 4px 0', fontSize: '16px', color: '#1e293b' }}>
                        Version Control Status
                      </h3>
                      <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
                        {git.config?.enabled 
                          ? 'Git integration is active. Changes will be tracked automatically.'
                          : 'Enable Git integration to track changes and maintain version history.'
                        }
                      </p>
                    </div>
                    {git.config?.enabled ? (
                      <button
                        onClick={handleDisableGit}
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
                        Disable Git
                      </button>
                    ) : (
                      <button
                        onClick={handleEnableGit}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#059669',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        Enable Git
                      </button>
                    )}
                  </div>

                  {/* Repository Status */}
                  {git.status && git.config?.enabled && (
                    <div style={{ marginBottom: '24px' }}>
                      <h3 style={{ fontSize: '16px', marginBottom: '12px', color: '#1e293b' }}>
                        Repository Status
                      </h3>
                      
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '16px',
                        marginBottom: '16px'
                      }}>
                        <div style={{
                          padding: '12px',
                          backgroundColor: '#f1f5f9',
                          borderRadius: '6px'
                        }}>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                            Current Branch
                          </div>
                          <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b' }}>
                            {git.status.current_branch || 'No branch'}
                          </div>
                        </div>
                        
                        <div style={{
                          padding: '12px',
                          backgroundColor: '#f1f5f9',
                          borderRadius: '6px'
                        }}>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                            Remote
                          </div>
                          <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b' }}>
                            {git.status.has_remote ? 'Connected' : 'Not connected'}
                          </div>
                        </div>
                      </div>

                      {/* Changes Summary */}
                      <div style={{
                        display: 'flex',
                        gap: '12px',
                        marginBottom: '16px'
                      }}>
                        <div style={{
                          flex: 1,
                          padding: '8px 12px',
                          backgroundColor: git.status.modified_files.length > 0 ? '#fef3c7' : '#f0f9ff',
                          borderRadius: '6px',
                          textAlign: 'center'
                        }}>
                          <div style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
                            {git.status.modified_files.length}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>
                            Modified
                          </div>
                        </div>
                        
                        <div style={{
                          flex: 1,
                          padding: '8px 12px',
                          backgroundColor: git.status.staged_files.length > 0 ? '#dcfce7' : '#f0f9ff',
                          borderRadius: '6px',
                          textAlign: 'center'
                        }}>
                          <div style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
                            {git.status.staged_files.length}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>
                            Staged
                          </div>
                        </div>
                        
                        <div style={{
                          flex: 1,
                          padding: '8px 12px',
                          backgroundColor: git.status.untracked_files.length > 0 ? '#fee2e2' : '#f0f9ff',
                          borderRadius: '6px',
                          textAlign: 'center'
                        }}>
                          <div style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
                            {git.status.untracked_files.length}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>
                            Untracked
                          </div>
                        </div>
                      </div>

                      {/* Commit Button */}
                      {git.status.has_changes() && (
                        <button
                          onClick={() => setShowCommitDialog(true)}
                          style={{
                            width: '100%',
                            padding: '12px',
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}
                        >
                          💾 Commit Changes
                        </button>
                      )}

                      {git.status.is_clean() && (
                        <div style={{
                          padding: '12px',
                          backgroundColor: '#dcfce7',
                          border: '1px solid #16a34a',
                          borderRadius: '6px',
                          textAlign: 'center',
                          color: '#166534'
                        }}>
                          ✅ Working directory is clean
                        </div>
                      )}
                    </div>
                  )}

                  {/* Last Commit */}
                  {git.status?.last_commit && (
                    <div style={{ marginBottom: '24px' }}>
                      <h3 style={{ fontSize: '16px', marginBottom: '12px', color: '#1e293b' }}>
                        Latest Commit
                      </h3>
                      <div style={{
                        padding: '12px',
                        border: '1px solid #e5e7eb',
                        borderRadius: '6px'
                      }}>
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b', marginBottom: '4px' }}>
                          {git.formatCommitMessage(git.status.last_commit, 60)}
                        </div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>
                          {git.status.last_commit.author} • {git.getRelativeTime(git.status.last_commit.timestamp)} • {git.status.last_commit.short_hash}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'history' && git.config?.enabled && (
                <div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '16px'
                  }}>
                    <h3 style={{ fontSize: '16px', color: '#1e293b', margin: 0 }}>
                      Commit History
                    </h3>
                    <button
                      onClick={() => loadHistory(0)}
                      disabled={git.isLoading}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#f3f4f6',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      🔄 Refresh
                    </button>
                  </div>

                  {git.isLoading ? (
                    <div style={{
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      height: '200px',
                      color: '#64748b'
                    }}>
                      Loading history...
                    </div>
                  ) : history && history.commits.length > 0 ? (
                    <div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {history.commits.map((commit) => (
                          <div
                            key={commit.hash}
                            style={{
                              padding: '12px',
                              border: '1px solid #e5e7eb',
                              borderRadius: '6px',
                              backgroundColor: 'white'
                            }}
                          >
                            <div style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              marginBottom: '8px'
                            }}>
                              <div style={{ flex: 1 }}>
                                <div style={{
                                  fontSize: '14px',
                                  fontWeight: '500',
                                  color: '#1e293b',
                                  marginBottom: '4px'
                                }}>
                                  {git.formatCommitMessage(commit, 80)}
                                </div>
                                <div style={{ fontSize: '12px', color: '#64748b' }}>
                                  {commit.author} • {git.getRelativeTime(commit.timestamp)}
                                </div>
                              </div>
                              <div style={{
                                fontSize: '11px',
                                padding: '2px 6px',
                                backgroundColor: '#f1f5f9',
                                borderRadius: '4px',
                                color: '#64748b',
                                fontFamily: 'monospace'
                              }}>
                                {commit.short_hash}
                              </div>
                            </div>
                            
                            {commit.files_changed.length > 0 && (
                              <div style={{ fontSize: '12px', color: '#64748b' }}>
                                📄 {commit.files_changed.length} file{commit.files_changed.length !== 1 ? 's' : ''} changed
                              </div>
                            )}
                          </div>
                        ))}
                      </div>

                      {/* Pagination */}
                      <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        gap: '8px',
                        marginTop: '16px'
                      }}>
                        <button
                          onClick={() => loadHistory(Math.max(0, historyPage - 1))}
                          disabled={historyPage === 0}
                          style={{
                            padding: '6px 12px',
                            border: '1px solid #d1d5db',
                            backgroundColor: 'white',
                            borderRadius: '4px',
                            cursor: historyPage === 0 ? 'not-allowed' : 'pointer',
                            opacity: historyPage === 0 ? 0.5 : 1
                          }}
                        >
                          ← Previous
                        </button>
                        
                        <span style={{
                          padding: '6px 12px',
                          fontSize: '14px',
                          color: '#64748b'
                        }}>
                          Page {historyPage + 1}
                        </span>
                        
                        <button
                          onClick={() => loadHistory(historyPage + 1)}
                          disabled={history.commits.length < 10}
                          style={{
                            padding: '6px 12px',
                            border: '1px solid #d1d5db',
                            backgroundColor: 'white',
                            borderRadius: '4px',
                            cursor: history.commits.length < 10 ? 'not-allowed' : 'pointer',
                            opacity: history.commits.length < 10 ? 0.5 : 1
                          }}
                        >
                          Next →
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      height: '200px',
                      color: '#64748b'
                    }}>
                      <div style={{ fontSize: '48px', marginBottom: '12px' }}>📝</div>
                      <div>No commits yet</div>
                      <div style={{ fontSize: '12px', marginTop: '4px' }}>
                        Make your first commit to see history here
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'settings' && (
                <div>
                  <h3 style={{ fontSize: '16px', marginBottom: '20px', color: '#1e293b' }}>
                    Git Configuration
                  </h3>

                  {git.config && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {/* Auto-commit Settings */}
                      <div>
                        <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>
                          Automatic Commits
                        </h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                            <input
                              type="checkbox"
                              checked={git.config.auto_commit_on_session_save}
                              onChange={(e) => git.updateConfig({
                                ...git.config,
                                auto_commit_on_session_save: e.target.checked
                              })}
                            />
                            <span style={{ fontSize: '14px' }}>Auto-commit when saving sessions</span>
                          </label>
                          
                          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                            <input
                              type="checkbox"
                              checked={git.config.auto_commit_on_content_generation}
                              onChange={(e) => git.updateConfig({
                                ...git.config,
                                auto_commit_on_content_generation: e.target.checked
                              })}
                            />
                            <span style={{ fontSize: '14px' }}>Auto-commit after generating content</span>
                          </label>
                        </div>
                      </div>

                      {/* Commit Message Template */}
                      <div>
                        <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                          Commit Message Template
                        </label>
                        <input
                          type="text"
                          value={git.config.commit_message_template}
                          onChange={(e) => git.updateConfig({
                            ...git.config,
                            commit_message_template: e.target.value
                          })}
                          style={{
                            width: '100%',
                            padding: '8px 12px',
                            border: '1px solid #d1d5db',
                            borderRadius: '6px',
                            fontSize: '14px'
                          }}
                          placeholder="e.g., Update session: {session_name} - {timestamp}"
                        />
                        <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                          Available variables: {'{session_name}'}, {'{timestamp}'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Commit Dialog */}
      {showCommitDialog && (
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
            maxWidth: '500px',
            width: '90%',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
          }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#1e293b' }}>Commit Changes</h3>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                Commit Message
              </label>
              <textarea
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                placeholder="Describe your changes..."
                style={{
                  width: '100%',
                  height: '80px',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCommitDialog(false)}
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
                onClick={handleCommit}
                disabled={!commitMessage.trim() || git.isLoading}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: !commitMessage.trim() ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: !commitMessage.trim() ? 'not-allowed' : 'pointer'
                }}
              >
                {git.isLoading ? 'Committing...' : 'Commit'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Initialize Repository Dialog */}
      {showInitDialog && (
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
            maxWidth: '500px',
            width: '90%',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
          }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#1e293b' }}>Initialize Git Repository</h3>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                Repository Path
              </label>
              <input
                type="text"
                value={initOptions.repository_path}
                onChange={(e) => setInitOptions({
                  ...initOptions,
                  repository_path: e.target.value
                })}
                placeholder="/path/to/your/project"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={initOptions.setup_gitignore}
                  onChange={(e) => setInitOptions({
                    ...initOptions,
                    setup_gitignore: e.target.checked
                  })}
                />
                <span style={{ fontSize: '14px' }}>Create .gitignore file</span>
              </label>
              
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={initOptions.initial_commit}
                  onChange={(e) => setInitOptions({
                    ...initOptions,
                    initial_commit: e.target.checked
                  })}
                />
                <span style={{ fontSize: '14px' }}>Create initial commit</span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowInitDialog(false)}
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
                onClick={handleInitializeRepository}
                disabled={!initOptions.repository_path.trim() || git.isLoading}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: !initOptions.repository_path.trim() ? '#9ca3af' : '#059669',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: !initOptions.repository_path.trim() ? 'not-allowed' : 'pointer'
                }}
              >
                {git.isLoading ? 'Initializing...' : 'Initialize'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}