import { useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Dashboard from './components/Layout/Dashboard';
import ContentCreator from './features/content/ContentCreator';
import CourseManager from './features/courses/CourseManager';
import CourseView from './features/courses/CourseView';
import Login from './features/auth/Login';
import Landing from './features/landing/Landing';
import AdminDashboard from './features/admin/AdminDashboard';
import { useAuthStore } from './stores/authStore';

function App() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const [showLogin, setShowLogin] = useState(false);

  // Custom logout that resets to landing page
  const handleLogout = () => {
    logout();
    setShowLogin(false); // Go back to landing page
  };

  // If authenticated, show appropriate dashboard based on role
  if (isAuthenticated && user) {
    // Admin users get admin dashboard
    if (user.role === 'ADMIN') {
      return (
        <Router>
          <Toaster position='top-right' />
          <Routes>
            <Route path='/admin' element={<AdminDashboard />} />
            <Route path='*' element={<Navigate to='/admin' replace />} />
          </Routes>
        </Router>
      );
    }

    // Regular users get normal dashboard
    return (
      <Router>
        <Toaster position='top-right' />
        <Dashboard onLogout={handleLogout}>
          <Routes>
            <Route path='/' element={<CourseManager />} />
            <Route path='/dashboard' element={<CourseManager />} />
            <Route path='/create/:type' element={<ContentCreator />} />
            <Route path='/courses' element={<CourseManager />} />
            <Route path='/course/:id' element={<CourseView />} />
            <Route path='*' element={<Navigate to='/dashboard' replace />} />
          </Routes>
        </Dashboard>
      </Router>
    );
  }

  // If not authenticated, show landing or login
  if (showLogin) {
    return (
      <Router>
        <Routes>
          <Route
            path='/login'
            element={<Login onBackToLanding={() => setShowLogin(false)} />}
          />
          <Route
            path='*'
            element={<Login onBackToLanding={() => setShowLogin(false)} />}
          />
        </Routes>
      </Router>
    );
  }

  return <Landing onSignInClick={() => setShowLogin(true)} />;
}

export default App;
