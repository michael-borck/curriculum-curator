import React from 'react';
import './Header.css';

type AppMode = 'wizard' | 'expert';

interface HeaderProps {
  currentMode: AppMode;
  onModeSwitch: (mode: AppMode) => void;
  onToggleSidebar: () => void;
  sidebarCollapsed: boolean;
}

export function Header({ currentMode, onModeSwitch, onToggleSidebar, sidebarCollapsed }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="header-left">
        <button 
          className="sidebar-toggle-btn" 
          onClick={onToggleSidebar}
          aria-label={sidebarCollapsed ? "Open sidebar" : "Close sidebar"}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>
        
        <div className="app-title">
          <h1>Curriculum Curator</h1>
          <span className="app-subtitle">Weekly Content Generator</span>
        </div>
      </div>

      <div className="header-center">
        <div className="mode-switcher">
          <button
            className={`mode-btn ${currentMode === 'wizard' ? 'active' : ''}`}
            onClick={() => onModeSwitch('wizard')}
            data-mode="wizard"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Wizard Mode
          </button>
          
          <button
            className={`mode-btn ${currentMode === 'expert' ? 'active' : ''}`}
            onClick={() => onModeSwitch('expert')}
            data-mode="expert"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Expert Mode
          </button>
        </div>
      </div>

      <div className="header-right">
        <div className="header-actions">
          <button className="action-btn" title="Settings">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m10-9a2 2 0 002 2h4a2 2 0 002-2M7 10a2 2 0 002 2h4a2 2 0 002-2" />
            </svg>
          </button>
          
          <button className="action-btn" title="Help">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01" />
              <circle cx="12" cy="12" r="10" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}