import React from 'react';

function TestApp() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ color: '#3b82f6' }}>Curriculum Curator - Test</h1>
      <p>If you can see this, React is working!</p>
      <button style={{ 
        padding: '10px 20px', 
        backgroundColor: '#3b82f6', 
        color: 'white', 
        border: 'none', 
        borderRadius: '5px',
        cursor: 'pointer'
      }}>
        Test Button
      </button>
    </div>
  );
}

export default TestApp;