import { useState, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useParams,
} from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Layout
import AppLayout from './components/Layout/AppLayout';

// Pages
import DashboardPage from './pages/DashboardPage';
import UnitPage from './pages/UnitPage';

// Features
import ContentCreator from './features/content/ContentCreator';
import ContentView from './features/content/ContentView';
import Login from './features/auth/Login';
import Landing from './features/landing/Landing';
import AdminDashboard from './features/admin/AdminDashboard';
import LRDCreator from './features/lrd/LRDCreator';
import LRDList from './features/lrd/LRDList';
import LRDDetail from './features/lrd/LRDDetail';
import ImportMaterials from './features/import/ImportMaterials';
import MaterialDetail from './features/materials/MaterialDetail';
import AIAssistant from './features/ai/AIAssistant';
import Settings from './features/settings/Settings';
import TaskBoard from './features/tasks/TaskBoard';

// Onboarding
import TeachingStyleOnboarding from './components/onboarding/TeachingStyleOnboarding';

// Store
import { useAuthStore } from './stores/authStore';
import { useTeachingStyleStore } from './stores/teachingStyleStore';

// Redirect helper for routes with params
const UnitDashboardRedirect = () => {
  const { unitId } = useParams();
  return <Navigate to={`/units/${unitId}`} replace />;
};

const UnitStructureRedirect = () => {
  const { unitId } = useParams();
  return <Navigate to={`/units/${unitId}?tab=structure`} replace />;
};

const TaskBoardWrapper = () => {
  const { unitId, taskListId } = useParams();
  return (
    <TaskBoard
      {...(unitId ? { unitId } : {})}
      {...(taskListId ? { lrdId: taskListId } : {})}
    />
  );
};

function App() {
  const { isAuthenticated, user, logout, isLoading, initializeAuth } =
    useAuthStore();
  const { isSet: teachingStyleIsSet } = useTeachingStyleStore();

  // Initialize auth on app load
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  const [showLogin, setShowLogin] = useState(false);
  const [showTeachingStyleOnboarding, setShowTeachingStyleOnboarding] =
    useState(false);
  const [onboardingDismissed, setOnboardingDismissed] = useState(false);

  // Check if we should show teaching style onboarding
  useEffect(() => {
    if (
      isAuthenticated &&
      user &&
      !user.teachingPhilosophy &&
      !teachingStyleIsSet &&
      !onboardingDismissed
    ) {
      // Small delay to let the app load first
      const timer = window.setTimeout(() => {
        setShowTeachingStyleOnboarding(true);
      }, 500);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [isAuthenticated, user, teachingStyleIsSet, onboardingDismissed]);

  // Custom logout that resets to landing page
  const handleLogout = () => {
    logout();
    setShowLogin(false); // Go back to landing page
  };

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className='min-h-screen flex items-center justify-center bg-gray-50'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto'></div>
          <p className='mt-4 text-gray-600'>Loading...</p>
        </div>
      </div>
    );
  }

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

    // Regular users get the new app layout
    return (
      <Router>
        <Toaster position='top-right' />
        {showTeachingStyleOnboarding && (
          <TeachingStyleOnboarding
            onComplete={() => setShowTeachingStyleOnboarding(false)}
            onSkip={() => {
              setShowTeachingStyleOnboarding(false);
              setOnboardingDismissed(true);
            }}
          />
        )}
        <Routes>
          {/* App Layout wrapper with nested routes */}
          <Route element={<AppLayout onLogout={handleLogout} />}>
            {/* Dashboard / Home */}
            <Route path='/' element={<DashboardPage />} />
            <Route path='/dashboard' element={<DashboardPage />} />

            {/* Unit routes */}
            <Route path='/units' element={<DashboardPage />} />
            <Route path='/units/:unitId' element={<UnitPage />} />
            <Route path='/units/:unitId/edit' element={<UnitPage />} />

            {/* Legacy redirects */}
            <Route path='/courses' element={<Navigate to='/units' replace />} />
            <Route
              path='/units/:unitId/dashboard'
              element={<UnitDashboardRedirect />}
            />
            <Route
              path='/units/:unitId/structure'
              element={<UnitStructureRedirect />}
            />

            {/* Content Creation and Viewing */}
            <Route path='/content/new' element={<ContentCreator />} />
            <Route path='/create/:type' element={<ContentCreator />} />
            <Route
              path='/units/:unitId/content/:contentId'
              element={<ContentView />}
            />
            <Route
              path='/units/:unitId/content/:contentId/edit'
              element={<ContentCreator />}
            />

            {/* Import */}
            <Route path='/import' element={<ImportMaterials />} />

            {/* Materials — legacy route kept for backward compat */}
            <Route
              path='/units/:unitId/materials/:contentId'
              element={<MaterialDetail />}
            />

            {/* Teaching Style - redirect to settings */}
            <Route
              path='/teaching-style'
              element={<Navigate to='/settings?tab=teaching-style' replace />}
            />

            {/* AI Assistant */}
            <Route path='/ai-assistant' element={<AIAssistant />} />

            {/* Settings */}
            <Route path='/settings' element={<Settings />} />

            {/* Task Routes */}
            <Route
              path='/units/:unitId/tasks/:taskListId'
              element={<TaskBoardWrapper />}
            />

            {/* LRD Routes */}
            <Route path='/units/:unitId/lrds' element={<LRDList />} />
            <Route path='/units/:unitId/lrds/new' element={<LRDCreator />} />
            <Route path='/units/:unitId/lrds/:lrdId' element={<LRDDetail />} />
            <Route
              path='/units/:unitId/lrds/:lrdId/edit'
              element={<LRDCreator />}
            />

            {/* Catch-all redirect */}
            <Route path='*' element={<Navigate to='/dashboard' replace />} />
          </Route>
        </Routes>
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
