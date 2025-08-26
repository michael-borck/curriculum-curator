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
import UnitManager from './features/units/UnitManager';
// import UnitDashboard from './features/units/UnitDashboard'; // TODO: Re-enable when ready
import UnitView from './features/units/UnitView';
import UnitWorkflow from './features/units/UnitWorkflow';
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
import UnitStructure from './features/units/UnitStructure';

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
            <Route path='/' element={<UnitManager />} />
            <Route path='/dashboard' element={<UnitManager />} />
            <Route path='/units' element={<UnitManager />} />
            <Route path='/courses' element={<Navigate to='/units' replace />} />
            <Route path='/units/:unitId/dashboard' element={<UnitWorkflow />} />
            <Route
              path='/units/:unitId/structure'
              element={<UnitStructure />}
            />
            <Route path='/units/:id' element={<UnitView />} />

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
            <Route path='/units/:unitId/lrds' element={<LRDList />} />
            <Route path='/units/:unitId/lrds/new' element={<LRDCreator />} />
            <Route path='/units/:unitId/lrds/:lrdId' element={<LRDDetail />} />
            <Route
              path='/units/:unitId/lrds/:lrdId/edit'
              element={<LRDCreator />}
            />

            <Route path='*' element={<Navigate to='/dashboard' replace />} />
          </Routes>
        </Dashboard>
      </Router>
    );
  }

  // If not authenticated, wrap everything in Router for navigation context
  return (
    <Router>
      <Toaster position='top-right' />
      {showLogin ? (
        <Login onBackToLanding={() => setShowLogin(false)} />
      ) : (
        <Landing onSignInClick={() => setShowLogin(true)} />
      )}
    </Router>
  );
}

export default App;
