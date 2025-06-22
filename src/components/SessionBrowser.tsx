import React, { useState, useEffect } from 'react';
import { useSessionManagement, type SessionListItem } from '../hooks/useSessionManagement';
import { useStatusFeedback } from './StatusFeedback';
import { useDesktopLayout } from '../utils/desktopLayout';

interface SessionBrowserProps {
  isOpen: boolean;
  onClose: () => void;
  onSessionSelect?: (sessionId: string) => void;
  mode?: 'browse' | 'select';
}

export function SessionBrowser({ 
  isOpen, 
  onClose, 
  onSessionSelect,
  mode = 'browse' 
}: SessionBrowserProps) {
  const sessionMgmt = useSessionManagement();
  const statusFeedback = useStatusFeedback();
  const layout = useDesktopLayout();
  
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string>('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'updated_at' | 'created_at' | 'name'>('updated_at');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      sessionMgmt.loadSessions();
      sessionMgmt.loadStatistics();
    }
  }, [isOpen, sessionMgmt]);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    await sessionMgmt.searchSessions(query);
  };

  const handleTagFilter = async (tag: string) => {
    setSelectedTag(tag);
    if (tag) {
      await sessionMgmt.filterByTags([tag]);
    } else {
      await sessionMgmt.loadSessions();
    }
  };

  const handleSortChange = async (newSortBy: typeof sortBy) => {
    setSortBy(newSortBy);
    await sessionMgmt.loadSessions({
      sort_by: newSortBy,
      sort_order: 'desc'
    });
  };

  const handleFavoriteToggle = async (sessionId: string, isFavorite: boolean) => {
    try {
      await sessionMgmt.toggleFavorite(sessionId, isFavorite);
      statusFeedback.showSuccess(
        isFavorite ? 'Added to Favorites' : 'Removed from Favorites',
        '',
        2000
      );
    } catch (error) {
      statusFeedback.showError(
        'Failed to Update',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const handleDuplicate = async (session: SessionListItem) => {
    try {
      const newSessionId = await sessionMgmt.duplicateSession(
        session.id, 
        `${session.name} (Copy)`
      );
      statusFeedback.showSuccess(
        'Session Duplicated',
        `Created copy: ${session.name} (Copy)`,
        3000
      );
    } catch (error) {
      statusFeedback.showError(
        'Duplication Failed',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const handleDelete = async (sessionId: string) => {
    try {
      await sessionMgmt.deleteSession(sessionId);
      setShowDeleteConfirm(null);
      statusFeedback.showSuccess('Session Deleted', '', 2000);
    } catch (error) {
      statusFeedback.showError(
        'Delete Failed',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  };

  const handleSessionClick = (sessionId: string) => {
    if (mode === 'select' && onSessionSelect) {
      onSessionSelect(sessionId);
      onClose();
    } else {
      // In browse mode, open the session for editing
      if (onSessionSelect) {
        onSessionSelect(sessionId);
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return date.toLocaleDateString();
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'Slides': return '📊';
      case 'InstructorNotes': return '📝';
      case 'Worksheet': return '📄';
      case 'Quiz': return '❓';
      case 'ActivityGuide': return '👥';
      default: return '📎';
    }
  };

  const filteredSessions = showFavoritesOnly 
    ? sessionMgmt.getFavoriteSessions()
    : sessionMgmt.sessions;

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
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
              {mode === 'select' ? 'Select Session' : 'Session Browser'}
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>
              {sessionMgmt.statistics && (
                `${sessionMgmt.statistics.total_sessions} sessions, ${sessionMgmt.statistics.total_content_items} content items`
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

        {/* Controls */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          {/* Search */}
          <div style={{ flex: 1, minWidth: '200px' }}>
            <input
              type="text"
              placeholder="Search sessions..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>

          {/* Tag Filter */}
          <select
            value={selectedTag}
            onChange={(e) => handleTagFilter(e.target.value)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          >
            <option value="">All Tags</option>
            {sessionMgmt.getAllTags().map(tag => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value as typeof sortBy)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          >
            <option value="updated_at">Recently Updated</option>
            <option value="created_at">Recently Created</option>
            <option value="name">Name</option>
          </select>

          {/* View Controls */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
              style={{
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                backgroundColor: showFavoritesOnly ? '#fef3c7' : 'white',
                color: showFavoritesOnly ? '#92400e' : '#64748b',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              ⭐ Favorites
            </button>
            <button
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              style={{
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                backgroundColor: 'white',
                color: '#64748b',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              {viewMode === 'grid' ? '📋' : '⊞'}
            </button>
          </div>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '16px 24px' }}>
          {sessionMgmt.isLoading ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '200px',
              fontSize: '16px',
              color: '#64748b'
            }}>
              Loading sessions...
            </div>
          ) : sessionMgmt.error ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '200px',
              fontSize: '16px',
              color: '#dc2626'
            }}>
              Error: {sessionMgmt.error}
            </div>
          ) : filteredSessions.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '200px',
              fontSize: '16px',
              color: '#64748b'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
              <div>No sessions found</div>
              <div style={{ fontSize: '14px', marginTop: '8px' }}>
                {searchQuery || selectedTag || showFavoritesOnly 
                  ? 'Try adjusting your filters' 
                  : 'Create your first session to get started'}
              </div>
            </div>
          ) : (
            <div style={{
              display: viewMode === 'grid' ? 'grid' : 'flex',
              flexDirection: viewMode === 'list' ? 'column' : undefined,
              gridTemplateColumns: viewMode === 'grid' ? 'repeat(auto-fill, minmax(300px, 1fr))' : undefined,
              gap: '16px'
            }}>
              {filteredSessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => handleSessionClick(session.id)}
                  style={{
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '16px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    backgroundColor: 'white',
                    ...(viewMode === 'list' && {
                      display: 'flex',
                      alignItems: 'center',
                      gap: '16px'
                    })
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#3b82f6';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  {/* Session Header */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: viewMode === 'grid' ? '12px' : '0',
                    ...(viewMode === 'list' && { flex: 1 })
                  }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{
                        margin: '0 0 4px 0',
                        fontSize: '16px',
                        fontWeight: '600',
                        color: '#1e293b',
                        lineHeight: '1.3'
                      }}>
                        {session.name}
                      </h3>
                      <div style={{
                        fontSize: '12px',
                        color: '#64748b',
                        marginBottom: '8px'
                      }}>
                        {session.topic} • {session.duration} • {formatDate(session.updated_at)}
                      </div>
                      
                      {viewMode === 'grid' && (
                        <div style={{
                          fontSize: '14px',
                          color: '#374151',
                          marginBottom: '12px',
                          lineHeight: '1.4',
                          maxHeight: '40px',
                          overflow: 'hidden'
                        }}>
                          {session.preview}
                        </div>
                      )}

                      {/* Content Types */}
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                        {session.content_types.map(type => (
                          <span
                            key={type}
                            style={{
                              fontSize: '11px',
                              padding: '2px 6px',
                              backgroundColor: '#f1f5f9',
                              border: '1px solid #e2e8f0',
                              borderRadius: '12px',
                              color: '#475569',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '2px'
                            }}
                          >
                            {getContentTypeIcon(type)} {type}
                          </span>
                        ))}
                      </div>

                      {/* Tags */}
                      {session.tags.length > 0 && (
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {session.tags.map(tag => (
                            <span
                              key={tag}
                              style={{
                                fontSize: '11px',
                                padding: '2px 6px',
                                backgroundColor: '#dbeafe',
                                border: '1px solid #bfdbfe',
                                borderRadius: '12px',
                                color: '#1e40af'
                              }}
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div style={{
                      display: 'flex',
                      gap: '4px',
                      marginLeft: '8px'
                    }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFavoriteToggle(session.id, !session.is_favorite);
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: '16px',
                          padding: '4px',
                          borderRadius: '4px',
                          color: session.is_favorite ? '#f59e0b' : '#9ca3af'
                        }}
                        title={session.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                      >
                        ⭐
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDuplicate(session);
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: '14px',
                          padding: '4px',
                          borderRadius: '4px',
                          color: '#6b7280'
                        }}
                        title="Duplicate session"
                      >
                        📋
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteConfirm(session.id);
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: '14px',
                          padding: '4px',
                          borderRadius: '4px',
                          color: '#dc2626'
                        }}
                        title="Delete session"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
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
            <h3 style={{ margin: '0 0 12px 0', color: '#1e293b' }}>Delete Session</h3>
            <p style={{ margin: '0 0 20px 0', color: '#64748b' }}>
              Are you sure you want to delete this session? This action cannot be undone.
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
    </div>
  );
}