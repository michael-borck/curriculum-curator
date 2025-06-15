// Status Feedback Component for Light Notifications

import React, { useState, useEffect } from 'react';

export interface StatusMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'loading';
  title: string;
  message: string;
  duration?: number; // in milliseconds, 0 = persistent
  action?: {
    label: string;
    onClick: () => void;
  };
  timestamp: Date;
}

interface StatusFeedbackProps {
  messages: StatusMessage[];
  onDismiss: (messageId: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxVisible?: number;
}

export function StatusFeedback({ 
  messages, 
  onDismiss, 
  position = 'top-right',
  maxVisible = 5 
}: StatusFeedbackProps) {
  const [visibleMessages, setVisibleMessages] = useState<StatusMessage[]>([]);

  useEffect(() => {
    // Auto-dismiss messages with duration
    messages.forEach(message => {
      if (message.duration && message.duration > 0) {
        setTimeout(() => {
          onDismiss(message.id);
        }, message.duration);
      }
    });

    // Limit visible messages
    setVisibleMessages(messages.slice(-maxVisible));
  }, [messages, maxVisible, onDismiss]);

  const getPositionStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      position: 'fixed',
      zIndex: 1500,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      padding: '16px',
      pointerEvents: 'none'
    };

    switch (position) {
      case 'top-right':
        return { ...baseStyles, top: 0, right: 0 };
      case 'top-left':
        return { ...baseStyles, top: 0, left: 0 };
      case 'bottom-right':
        return { ...baseStyles, bottom: 0, right: 0 };
      case 'bottom-left':
        return { ...baseStyles, bottom: 0, left: 0 };
      default:
        return { ...baseStyles, top: 0, right: 0 };
    }
  };

  const getMessageStyles = (type: StatusMessage['type']): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      padding: '12px 16px',
      borderRadius: '8px',
      maxWidth: '400px',
      minWidth: '300px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      pointerEvents: 'auto',
      transition: 'all 0.3s ease',
      border: '1px solid',
      position: 'relative'
    };

    switch (type) {
      case 'success':
        return {
          ...baseStyles,
          backgroundColor: '#f0fdf4',
          borderColor: '#bbf7d0',
          color: '#166534'
        };
      case 'error':
        return {
          ...baseStyles,
          backgroundColor: '#fef2f2',
          borderColor: '#fecaca',
          color: '#991b1b'
        };
      case 'warning':
        return {
          ...baseStyles,
          backgroundColor: '#fffbeb',
          borderColor: '#fed7aa',
          color: '#92400e'
        };
      case 'info':
        return {
          ...baseStyles,
          backgroundColor: '#f0f9ff',
          borderColor: '#bae6fd',
          color: '#1e40af'
        };
      case 'loading':
        return {
          ...baseStyles,
          backgroundColor: '#f8fafc',
          borderColor: '#e2e8f0',
          color: '#475569'
        };
      default:
        return baseStyles;
    }
  };

  const getMessageIcon = (type: StatusMessage['type']): string => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      case 'loading': return '⏳';
      default: return 'ℹ️';
    }
  };

  if (visibleMessages.length === 0) return null;

  return (
    <div style={getPositionStyles()}>
      {visibleMessages.map((message, index) => (
        <div
          key={message.id}
          style={{
            ...getMessageStyles(message.type),
            animationDelay: `${index * 100}ms`,
            animation: 'slideIn 0.3s ease-out forwards'
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            <div style={{
              fontSize: '16px',
              marginTop: '2px',
              minWidth: '16px'
            }}>
              {message.type === 'loading' ? (
                <div style={{
                  animation: 'spin 1s linear infinite',
                  fontSize: '14px'
                }}>
                  ⏳
                </div>
              ) : (
                getMessageIcon(message.type)
              )}
            </div>

            <div style={{ flex: 1 }}>
              <div style={{
                fontSize: '14px',
                fontWeight: '600',
                marginBottom: '4px',
                lineHeight: '1.3'
              }}>
                {message.title}
              </div>
              
              <div style={{
                fontSize: '13px',
                lineHeight: '1.4',
                opacity: 0.9
              }}>
                {message.message}
              </div>

              {message.action && (
                <button
                  onClick={message.action.onClick}
                  style={{
                    marginTop: '8px',
                    padding: '4px 8px',
                    border: 'none',
                    backgroundColor: 'rgba(0, 0, 0, 0.1)',
                    color: 'inherit',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '500'
                  }}
                >
                  {message.action.label}
                </button>
              )}
            </div>

            {message.duration !== 0 && (
              <button
                onClick={() => onDismiss(message.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '16px',
                  cursor: 'pointer',
                  color: 'inherit',
                  opacity: 0.7,
                  padding: '0',
                  marginLeft: '4px'
                }}
              >
                ×
              </button>
            )}
          </div>

          {/* Progress bar for timed messages */}
          {message.duration && message.duration > 0 && (
            <div style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: '2px',
              backgroundColor: 'rgba(0, 0, 0, 0.1)',
              borderRadius: '0 0 8px 8px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                backgroundColor: 'currentColor',
                width: '100%',
                animation: `shrink ${message.duration}ms linear forwards`,
                transformOrigin: 'left'
              }} />
            </div>
          )}
        </div>
      ))}

      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }

          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }

          @keyframes shrink {
            from { transform: scaleX(1); }
            to { transform: scaleX(0); }
          }
        `}
      </style>
    </div>
  );
}

// Hook for managing status messages
export function useStatusFeedback() {
  const [messages, setMessages] = useState<StatusMessage[]>([]);

  const addMessage = (message: Omit<StatusMessage, 'id' | 'timestamp'>) => {
    const newMessage: StatusMessage = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date(),
      duration: message.duration ?? 5000 // 5 seconds default
    };
    
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  };

  const dismissMessage = (messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  };

  const clearAll = () => {
    setMessages([]);
  };

  // Convenience methods
  const showSuccess = (title: string, message: string, duration?: number) => 
    addMessage({ type: 'success', title, message, duration });

  const showError = (title: string, message: string, duration?: number) => 
    addMessage({ type: 'error', title, message, duration });

  const showWarning = (title: string, message: string, duration?: number) => 
    addMessage({ type: 'warning', title, message, duration });

  const showInfo = (title: string, message: string, duration?: number) => 
    addMessage({ type: 'info', title, message, duration });

  const showLoading = (title: string, message: string) => 
    addMessage({ type: 'loading', title, message, duration: 0 });

  return {
    messages,
    addMessage,
    dismissMessage,
    clearAll,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading
  };
}