import React, { useState, useEffect, useMemo } from 'react';
import { useSessionManagement, type SessionListItem } from '../hooks/useSessionManagement';
import { useStatusFeedback } from './StatusFeedback';

interface SessionHistoryProps {
  isOpen: boolean;
  onClose: () => void;
  onSessionSelect?: (sessionId: string) => void;
}

interface TimelineGroup {
  date: string;
  displayDate: string;
  sessions: SessionListItem[];
}

export function SessionHistory({ isOpen, onClose, onSessionSelect }: SessionHistoryProps) {
  const sessionMgmt = useSessionManagement();
  const statusFeedback = useStatusFeedback();
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year' | 'all'>('month');
  const [groupBy, setGroupBy] = useState<'day' | 'week' | 'month'>('day');

  useEffect(() => {
    if (isOpen) {
      sessionMgmt.loadSessions({
        sort_by: 'updated_at',
        sort_order: 'desc',
        limit: 100
      });
    }
  }, [isOpen, sessionMgmt]);

  const filteredSessions = useMemo(() => {
    const now = new Date();
    let cutoffDate: Date;

    switch (timeRange) {
      case 'week':
        cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'month':
        cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'year':
        cutoffDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        break;
      default:
        return sessionMgmt.sessions;
    }

    return sessionMgmt.sessions.filter(session => 
      new Date(session.updated_at) >= cutoffDate
    );
  }, [sessionMgmt.sessions, timeRange]);

  const timelineGroups = useMemo(() => {
    const groups: TimelineGroup[] = [];
    const groupMap = new Map<string, SessionListItem[]>();

    filteredSessions.forEach(session => {
      const date = new Date(session.updated_at);
      let groupKey: string;
      let displayDate: string;

      switch (groupBy) {
        case 'day':
          groupKey = date.toISOString().split('T')[0];
          displayDate = date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          });
          break;
        case 'week':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          groupKey = weekStart.toISOString().split('T')[0];
          const weekEnd = new Date(weekStart);
          weekEnd.setDate(weekStart.getDate() + 6);
          displayDate = `Week of ${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}`;
          break;
        case 'month':
          groupKey = `${date.getFullYear()}-${date.getMonth()}`;
          displayDate = date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long' 
          });
          break;
        default:
          groupKey = date.toISOString().split('T')[0];
          displayDate = date.toLocaleDateString();
      }

      if (!groupMap.has(groupKey)) {
        groupMap.set(groupKey, []);
      }
      groupMap.get(groupKey)!.push(session);
    });

    // Convert to array and sort by date (newest first)
    Array.from(groupMap.entries())
      .sort(([a], [b]) => b.localeCompare(a))
      .forEach(([date, sessions]) => {
        const displayDate = groupMap.get(date) ? 
          // Find display date from first session in group
          getDisplayDateForGroup(date, groupBy) : date;
        
        groups.push({
          date,
          displayDate,
          sessions: sessions.sort((a, b) => 
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
          )
        });
      });

    return groups;
  }, [filteredSessions, groupBy]);

  const getDisplayDateForGroup = (dateKey: string, groupBy: string): string => {
    const date = new Date(dateKey);
    
    switch (groupBy) {
      case 'day':
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        
        if (dateKey === today.toISOString().split('T')[0]) return 'Today';
        if (dateKey === yesterday.toISOString().split('T')[0]) return 'Yesterday';
        
        return date.toLocaleDateString('en-US', { 
          weekday: 'long', 
          month: 'long', 
          day: 'numeric' 
        });
      case 'week':
        const weekEnd = new Date(date);
        weekEnd.setDate(date.getDate() + 6);
        return `Week of ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
      case 'month':
        return date.toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'long' 
        });
      default:
        return date.toLocaleDateString();
    }
  };

  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getActivityIcon = (session: SessionListItem) => {
    if (session.content_count === 0) return '📝'; // Planning
    if (session.content_types.includes('Quiz')) return '❓';
    if (session.content_types.includes('Slides')) return '📊';
    return '📄';
  };

  const getActivityDescription = (session: SessionListItem) => {
    if (session.content_count === 0) {
      return 'Started planning session';
    }
    if (session.content_count === 1) {
      return `Created ${session.content_types[0]}`;
    }
    return `Generated ${session.content_count} content items`;
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
        maxWidth: '800px',
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
              Session History
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>
              Track your session activity and progress over time
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
          alignItems: 'center'
        }}>
          <div>
            <label style={{ fontSize: '14px', fontWeight: '500', marginRight: '8px' }}>
              Time Range:
            </label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
              style={{
                padding: '6px 10px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            >
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
              <option value="year">Past Year</option>
              <option value="all">All Time</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '14px', fontWeight: '500', marginRight: '8px' }}>
              Group By:
            </label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as typeof groupBy)}
              style={{
                padding: '6px 10px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            >
              <option value="day">Day</option>
              <option value="week">Week</option>
              <option value="month">Month</option>
            </select>
          </div>

          {sessionMgmt.statistics && (
            <div style={{
              marginLeft: 'auto',
              fontSize: '14px',
              color: '#64748b'
            }}>
              {filteredSessions.length} sessions in timeframe
            </div>
          )}
        </div>

        {/* Timeline Content */}
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
              Loading history...
            </div>
          ) : timelineGroups.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '200px',
              fontSize: '16px',
              color: '#64748b'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📅</div>
              <div>No activity in this time period</div>
              <div style={{ fontSize: '14px', marginTop: '8px' }}>
                Try selecting a longer time range
              </div>
            </div>
          ) : (
            <div style={{ position: 'relative' }}>
              {/* Timeline line */}
              <div style={{
                position: 'absolute',
                left: '15px',
                top: '20px',
                bottom: '20px',
                width: '2px',
                backgroundColor: '#e5e7eb'
              }} />

              {timelineGroups.map((group, groupIndex) => (
                <div key={group.date} style={{ marginBottom: '32px' }}>
                  {/* Date Header */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '16px'
                  }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      marginRight: '16px',
                      position: 'relative',
                      zIndex: 1
                    }}>
                      {group.sessions.length}
                    </div>
                    <h3 style={{
                      margin: 0,
                      fontSize: '16px',
                      fontWeight: '600',
                      color: '#1e293b'
                    }}>
                      {group.displayDate}
                    </h3>
                  </div>

                  {/* Sessions in this group */}
                  <div style={{ marginLeft: '48px' }}>
                    {group.sessions.map((session, sessionIndex) => (
                      <div
                        key={session.id}
                        onClick={() => onSessionSelect?.(session.id)}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '12px',
                          padding: '12px',
                          borderRadius: '8px',
                          cursor: onSessionSelect ? 'pointer' : 'default',
                          transition: 'background-color 0.2s',
                          marginBottom: '8px'
                        }}
                        onMouseEnter={(e) => {
                          if (onSessionSelect) {
                            e.currentTarget.style.backgroundColor = '#f8fafc';
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        {/* Activity Icon */}
                        <div style={{
                          fontSize: '20px',
                          marginTop: '2px'
                        }}>
                          {getActivityIcon(session)}
                        </div>

                        {/* Session Info */}
                        <div style={{ flex: 1 }}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'flex-start',
                            marginBottom: '4px'
                          }}>
                            <h4 style={{
                              margin: 0,
                              fontSize: '14px',
                              fontWeight: '600',
                              color: '#1e293b'
                            }}>
                              {session.name}
                            </h4>
                            <span style={{
                              fontSize: '12px',
                              color: '#64748b',
                              whiteSpace: 'nowrap',
                              marginLeft: '12px'
                            }}>
                              {getRelativeTime(session.updated_at)}
                            </span>
                          </div>

                          <p style={{
                            margin: '0 0 8px 0',
                            fontSize: '13px',
                            color: '#64748b',
                            lineHeight: '1.4'
                          }}>
                            {getActivityDescription(session)} • {session.topic}
                          </p>

                          {/* Content Types */}
                          {session.content_types.length > 0 && (
                            <div style={{
                              display: 'flex',
                              gap: '4px',
                              flexWrap: 'wrap'
                            }}>
                              {session.content_types.slice(0, 3).map(type => (
                                <span
                                  key={type}
                                  style={{
                                    fontSize: '10px',
                                    padding: '2px 6px',
                                    backgroundColor: '#f1f5f9',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: '8px',
                                    color: '#475569'
                                  }}
                                >
                                  {type}
                                </span>
                              ))}
                              {session.content_types.length > 3 && (
                                <span style={{
                                  fontSize: '10px',
                                  color: '#64748b'
                                }}>
                                  +{session.content_types.length - 3} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Favorite indicator */}
                        {session.is_favorite && (
                          <div style={{
                            fontSize: '14px',
                            color: '#f59e0b',
                            marginTop: '2px'
                          }}>
                            ⭐
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer with Stats */}
        {sessionMgmt.statistics && (
          <div style={{
            padding: '16px 24px',
            borderTop: '1px solid #e5e7eb',
            backgroundColor: '#f8fafc',
            fontSize: '14px',
            color: '#64748b'
          }}>
            <div style={{ display: 'flex', gap: '24px', justifyContent: 'center' }}>
              <div>
                <strong style={{ color: '#1e293b' }}>{sessionMgmt.statistics.total_sessions}</strong> total sessions
              </div>
              <div>
                <strong style={{ color: '#1e293b' }}>{sessionMgmt.statistics.sessions_this_week}</strong> this week
              </div>
              <div>
                <strong style={{ color: '#1e293b' }}>{sessionMgmt.statistics.sessions_this_month}</strong> this month
              </div>
              <div>
                <strong style={{ color: '#1e293b' }}>{sessionMgmt.statistics.favorite_count}</strong> favorites
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}