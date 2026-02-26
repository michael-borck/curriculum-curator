import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Settings,
  Mail,
  Shield,
  LogOut,
  Menu,
  X,
  Home,
  Activity,
  Brain,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import UserManagement from './UserManagement';
import EmailWhitelist from './EmailWhitelist';
import SystemSettings from './SystemSettings';
import { AdminLLMSettings } from './AdminLLMSettings';
import api from '../../services/api';
import { LoadingState, Alert, Button } from '../../components/ui';

type TabType = 'overview' | 'users' | 'whitelist' | 'settings' | 'llm';

interface DashboardStats {
  total_users: number;
  verified_users: number;
  active_users: number;
  admin_users: number;
  users_by_role: Record<string, number>;
  recent_registrations: number;
}

const sidebarItems = [
  { id: 'overview', label: 'Overview', icon: Home },
  { id: 'users', label: 'User Management', icon: Users },
  { id: 'whitelist', label: 'Email Whitelist', icon: Mail },
  { id: 'settings', label: 'System Settings', icon: Settings },
  { id: 'llm', label: 'LLM Configuration', icon: Brain },
] as const;

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(
    null
  );
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState('');
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const fetchDashboardStats = useCallback(async () => {
    try {
      setIsLoadingStats(true);
      setStatsError('');

      const [statsResponse] = await Promise.all([
        api.get('/admin/users/stats'),
      ]);

      setDashboardStats(statsResponse.data);
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
      setStatsError('Failed to load dashboard statistics');
    } finally {
      setIsLoadingStats(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchDashboardStats();
    }
  }, [activeTab, fetchDashboardStats]);

  useEffect(() => {
    const handleNavigateToTab = (event: CustomEvent) => {
      if (event.detail === 'llm') {
        setActiveTab('llm');
      }
    };

    window.addEventListener(
      'navigate-to-tab',
      handleNavigateToTab as EventListener
    );
    return () => {
      window.removeEventListener(
        'navigate-to-tab',
        handleNavigateToTab as EventListener
      );
    };
  }, []);

  const handleLogout = () => {
    logout();
    localStorage.removeItem('token');
    navigate('/login');
  };

  const renderOverview = () => {
    if (isLoadingStats) {
      return <LoadingState message='Loading dashboard...' />;
    }

    if (statsError) {
      return (
        <Alert variant='error'>
          <div className='flex items-center justify-between'>
            <span>{statsError}</span>
            <Button variant='danger' size='sm' onClick={fetchDashboardStats}>
              Retry
            </Button>
          </div>
        </Alert>
      );
    }

    return (
      <div className='space-y-6'>
        <h2 className='text-2xl font-semibold text-gray-900'>
          Dashboard Overview
        </h2>

        {/* Stats Cards */}
        <div className='grid grid-cols-1 md:grid-cols-3 gap-6'>
          <StatCard
            title='Total Users'
            value={dashboardStats?.total_users || 0}
            subtitle={`+${dashboardStats?.recent_registrations || 0} this week`}
            subtitleColor='text-green-600'
            icon={Users}
          />
          <StatCard
            title='Active Users'
            value={dashboardStats?.active_users || 0}
            subtitle={`${dashboardStats?.verified_users || 0} verified`}
            subtitleColor='text-blue-600'
            icon={Activity}
          />
          <StatCard
            title='Admin Users'
            value={dashboardStats?.admin_users || 0}
            subtitle='System administrators'
            subtitleColor='text-gray-600'
            icon={Shield}
          />
        </div>

        {/* User Breakdown */}
        {dashboardStats?.users_by_role && (
          <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4'>
              User Breakdown by Role
            </h3>
            <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
              {Object.entries(dashboardStats.users_by_role).map(
                ([role, count]) => (
                  <div key={role} className='text-center'>
                    <div className='text-2xl font-semibold text-gray-900'>
                      {count}
                    </div>
                    <div className='text-sm text-gray-600 capitalize'>
                      {role.toLowerCase()}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'users':
        return <UserManagement />;
      case 'whitelist':
        return <EmailWhitelist />;
      case 'settings':
        return <SystemSettings />;
      case 'llm':
        return <AdminLLMSettings />;
      default:
        return null;
    }
  };

  return (
    <div className='min-h-screen bg-gray-50 flex'>
      {/* Sidebar */}
      <div
        className={`${isSidebarOpen ? 'w-64' : 'w-16'} transition-all duration-300 bg-white shadow-lg`}
      >
        <div className='h-full flex flex-col'>
          {/* Logo and Toggle */}
          <div className='p-4 border-b border-gray-200 flex items-center justify-between'>
            {isSidebarOpen && (
              <div className='flex items-center gap-2'>
                <Shield className='w-8 h-8 text-purple-600' />
                <span className='font-semibold text-gray-900'>Admin Panel</span>
              </div>
            )}
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className='p-1 hover:bg-gray-100 rounded-md transition-colors'
            >
              {isSidebarOpen ? (
                <X className='w-5 h-5' />
              ) : (
                <Menu className='w-5 h-5' />
              )}
            </button>
          </div>

          {/* Navigation */}
          <nav className='flex-1 p-4'>
            <ul className='space-y-2'>
              {sidebarItems.map(item => (
                <li key={item.id}>
                  <button
                    onClick={() => setActiveTab(item.id as TabType)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                      activeTab === item.id
                        ? 'bg-purple-100 text-purple-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className='w-5 h-5' />
                    {isSidebarOpen && (
                      <span className='text-sm font-medium'>{item.label}</span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          {/* User Info and Logout */}
          <div className='p-4 border-t border-gray-200'>
            {isSidebarOpen && (
              <div className='mb-3'>
                <p className='text-sm font-medium text-gray-900'>
                  {user?.name}
                </p>
                <p className='text-xs text-gray-600'>{user?.email}</p>
              </div>
            )}
            <button
              onClick={handleLogout}
              className='w-full flex items-center gap-3 px-3 py-2 text-red-600 hover:bg-red-50 rounded-md transition-colors'
            >
              <LogOut className='w-5 h-5' />
              {isSidebarOpen && (
                <span className='text-sm font-medium'>Logout</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className='flex-1 overflow-auto'>
        <div className='p-8'>{renderContent()}</div>
      </div>
    </div>
  );
};

// Extracted StatCard component for reuse
interface StatCardProps {
  title: string;
  value: number;
  subtitle: string;
  subtitleColor: string;
  icon: React.ElementType;
}

const StatCard = ({
  title,
  value,
  subtitle,
  subtitleColor,
  icon: Icon,
}: StatCardProps) => (
  <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
    <div className='flex items-center justify-between'>
      <div>
        <p className='text-sm text-gray-600'>{title}</p>
        <p className='text-2xl font-semibold text-gray-900 mt-1'>{value}</p>
      </div>
      <Icon className='w-8 h-8 text-purple-600' />
    </div>
    <p className={`text-sm ${subtitleColor} mt-2`}>{subtitle}</p>
  </div>
);

export default AdminDashboard;
