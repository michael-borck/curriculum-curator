import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Dashboard from './components/Layout/Dashboard';
import ContentCreator from './features/content/ContentCreator';
import CourseManager from './features/courses/CourseManager';
import CourseView from './features/courses/CourseView';
import Login from './features/auth/Login';
import { useAuthStore } from './stores/authStore';

function App() {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Router>
      <Toaster position="top-right" />
      <Dashboard>
        <Routes>
          <Route path="/" element={<CourseManager />} />
          <Route path="/create/:type" element={<ContentCreator />} />
          <Route path="/courses" element={<CourseManager />} />
          <Route path="/course/:id" element={<CourseView />} />
        </Routes>
      </Dashboard>
    </Router>
  );
}

export default App;