import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          🎓 Curriculum Curator
        </h1>
        <p className="text-gray-600 mb-8">
          Your Electron app is working!
        </p>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Test</h2>
          <p className="text-sm text-gray-500">
            This is a simplified version to test the React setup.
          </p>
          <button 
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            onClick={() => alert('Button works!')}
          >
            Test Button
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;