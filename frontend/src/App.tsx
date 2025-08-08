import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Dashboard from './components/Layout/Dashboard';
import ContentCreator from './features/content/ContentCreator';
import CourseManager from './features/courses/CourseManager';
import CourseView from './features/courses/CourseView';
import Login from './features/auth/Login';
import Landing from './features/landing/Landing';
import { useAuthStore } from './stores/authStore';

function App() {
  const { isAuthenticated, logout } = useAuthStore();
  const [showLogin, setShowLogin] = useState(false);

  // Custom logout that resets to landing page
  const handleLogout = () => {
    logout();
    setShowLogin(false); // Go back to landing page
  };

  // If authenticated, show dashboard
  if (isAuthenticated) {
    return (
      <Router>
        <Toaster position='top-right' />
        <Dashboard onLogout={handleLogout}>
          <Routes>
            <Route path='/' element={<CourseManager />} />
            <Route path='/create/:type' element={<ContentCreator />} />
            <Route path='/courses' element={<CourseManager />} />
            <Route path='/course/:id' element={<CourseView />} />
          </Routes>
        </Dashboard>
      </Router>
    );
  }

  // If not authenticated, show landing or login
  if (showLogin) {
    return <Login onBackToLanding={() => setShowLogin(false)} />;
  }

  return <Landing onSignInClick={() => setShowLogin(true)} />;
}

export default App;
