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
import Download from './features/downloads/Download';
import AdminDashboard from './features/admin/AdminDashboard';
import DesignCreator from './features/designs/DesignCreator';
import DesignList from './features/designs/DesignList';
import DesignDetail from './features/designs/DesignDetail';
import ImportMaterials from './features/import/ImportMaterials';
import PackageImport from './features/import/PackageImport';
import ResearchPage from './features/research/ResearchPage';
import MaterialDetail from './features/materials/MaterialDetail';
import AIAssistant from './features/ai/AIAssistant';
import Settings from './features/settings/Settings';
import AboutPage from './pages/AboutPage';
import LearningDesignGuide from './pages/LearningDesignGuide';
import AssessmentDesignGuide from './pages/AssessmentDesignGuide';
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
      {...(taskListId ? { designId: taskListId } : {})}
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
            <Route path='/import/package' element={<PackageImport />} />

            {/* Research */}
            <Route path='/research' element={<ResearchPage />} />

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

            {/* Learning Design Routes */}
            <Route path='/units/:unitId/designs' element={<DesignList />} />
            <Route
              path='/units/:unitId/designs/new'
              element={<DesignCreator />}
            />
            <Route
              path='/units/:unitId/designs/:designId'
              element={<DesignDetail />}
            />
            <Route
              path='/units/:unitId/designs/:designId/edit'
              element={<DesignCreator />}
            />

            {/* Guide & About */}
            <Route
              path='/guide/learning-design'
              element={<LearningDesignGuide />}
            />
            <Route
              path='/guide/assessment-design'
              element={<AssessmentDesignGuide />}
            />
            <Route path='/about' element={<AboutPage />} />

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
      <Routes>
        <Route path='/download' element={<Download />} />
        <Route
          path='*'
          element={
            showLogin ? (
              <Login onBackToLanding={() => setShowLogin(false)} />
            ) : (
              <Landing onSignInClick={() => setShowLogin(true)} />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
