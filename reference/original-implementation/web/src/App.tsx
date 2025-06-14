import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Workflows from './pages/Workflows';
import Sessions from './pages/Sessions';
import Prompts from './pages/Prompts';
import Validators from './pages/Validators';
import Remediators from './pages/Remediators';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/sessions" element={<Sessions />} />
          <Route path="/prompts" element={<Prompts />} />
          <Route path="/validators" element={<Validators />} />
          <Route path="/remediators" element={<Remediators />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;