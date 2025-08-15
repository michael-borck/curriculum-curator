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
import CourseDashboard from './features/courses/CourseDashboard';
import CourseView from './features/courses/CourseView';
import Login from './features/auth/Login';
import Landing from './features/landing/Landing';
import AdminDashboard from './features/admin/AdminDashboard';
import LRDCreator from './features/lrd/LRDCreator';
import LRDList from './features/lrd/LRDList';
import LRDDetail from './features/lrd/LRDDetail';
import ImportMaterials from './features/import/ImportMaterials';
import MaterialDetail from './features/materials/MaterialDetail';
import TeachingStyle from './features/teaching/TeachingStyle';
import AIAssistant from './features/ai/AIAssistant';
import Settings from './features/settings/Settings';
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
    if (user.role === 'admin') {
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
            <Route path='/courses' element={<CourseManager />} />
            <Route
              path='/courses/:courseId/dashboard'
              element={<CourseDashboard />}
            />
            <Route path='/course/:id' element={<CourseView />} />

            {/* Content Creation */}
            <Route path='/content/new' element={<ContentCreator />} />
            <Route path='/create/:type' element={<ContentCreator />} />

            {/* Import */}
            <Route path='/import' element={<ImportMaterials />} />

            {/* Materials */}
            <Route path='/materials/:materialId' element={<MaterialDetail />} />

            {/* Teaching Style */}
            <Route path='/teaching-style' element={<TeachingStyle />} />

            {/* AI Assistant */}
            <Route path='/ai-assistant' element={<AIAssistant />} />

            {/* Settings */}
            <Route path='/settings' element={<Settings />} />

            {/* LRD Routes */}
            <Route path='/courses/:courseId/lrds' element={<LRDList />} />
            <Route
              path='/courses/:courseId/lrds/new'
              element={<LRDCreator />}
            />
            <Route
              path='/courses/:courseId/lrds/:lrdId'
              element={<LRDDetail />}
            />
            <Route
              path='/courses/:courseId/lrds/:lrdId/edit'
              element={<LRDCreator />}
            />

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
            path='/verify'
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
