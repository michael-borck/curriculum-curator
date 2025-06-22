import { useState } from 'react';
import type { AppMode } from './types';
import './App.css';

function SimpleApp() {
  const [currentMode, setCurrentMode] = useState<AppMode>('wizard');

  const handleModeSwitch = (mode: AppMode) => {
    setCurrentMode(mode);
  };

  return (
    <div className="app">
      {/* Simple Header */}
      <header style={{ 
        padding: '16px 24px', 
        backgroundColor: 'white', 
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
          Curriculum Curator
        </h1>
        
        <div style={{ 
          display: 'flex', 
          gap: '8px', 
          backgroundColor: '#f1f5f9', 
          padding: '4px', 
          borderRadius: '8px' 
        }}>
          <button
            onClick={() => handleModeSwitch('wizard')}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: currentMode === 'wizard' ? 'white' : 'transparent',
              color: currentMode === 'wizard' ? '#3b82f6' : '#64748b',
              cursor: 'pointer'
            }}
          >
            Wizard Mode
          </button>
          <button
            onClick={() => handleModeSwitch('expert')}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: currentMode === 'expert' ? 'white' : 'transparent',
              color: currentMode === 'expert' ? '#3b82f6' : '#64748b',
              cursor: 'pointer'
            }}
          >
            Expert Mode
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ 
        padding: '24px', 
        backgroundColor: '#f8fafc', 
        flex: 1,
        minHeight: 'calc(100vh - 80px)'
      }}>
        <div style={{ 
          maxWidth: '800px', 
          margin: '0 auto', 
          backgroundColor: 'white', 
          padding: '32px', 
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{ marginBottom: '16px', color: '#1e293b' }}>
            {currentMode === 'wizard' ? 'Wizard Mode - Step by Step Content Creation' : 'Expert Mode - Advanced Content Tools'}
          </h2>
          
          <p style={{ color: '#64748b', marginBottom: '24px' }}>
            {currentMode === 'wizard' 
              ? 'Let us guide you through creating educational content step by step.'
              : 'Access advanced tools and direct control over content generation.'
            }
          </p>

          {currentMode === 'wizard' ? (
            <div>
              <div style={{ 
                backgroundColor: '#dbeafe', 
                padding: '16px', 
                borderRadius: '8px', 
                marginBottom: '16px',
                border: '1px solid #3b82f6'
              }}>
                <strong>Step 1: Topic & Objectives</strong>
                <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                  Define what you want to teach and your learning objectives.
                </p>
              </div>
              
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                  What topic will you be teaching?
                </label>
                <input 
                  type="text" 
                  placeholder="e.g., Introduction to Calculus, World War I, Cell Biology"
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '16px'
                  }}
                />
              </div>
              
              <button style={{
                padding: '12px 24px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px'
              }}>
                Next Step →
              </button>
            </div>
          ) : (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                <div>
                  <h3 style={{ marginBottom: '12px' }}>Content Planner</h3>
                  <p style={{ fontSize: '14px', color: '#64748b' }}>
                    Plan and organize your educational content with advanced controls.
                  </p>
                </div>
                <div>
                  <h3 style={{ marginBottom: '12px' }}>Batch Generator</h3>
                  <p style={{ fontSize: '14px', color: '#64748b' }}>
                    Generate multiple lessons and content types at once.
                  </p>
                </div>
              </div>
              
              <button style={{
                padding: '12px 24px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                marginTop: '24px'
              }}>
                Start Content Generation
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default SimpleApp;