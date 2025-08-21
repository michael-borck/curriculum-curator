import { useState, useEffect } from 'react';
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
  Loader2,
  Brain,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import UserManagement from './UserManagement';
import EmailWhitelist from './EmailWhitelist';
import SystemSettings from './SystemSettings';
import { AdminLLMSettings } from './AdminLLMSettings';
import api from '../../services/api';

type TabType = 'overview' | 'users' | 'whitelist' | 'settings' | 'llm';

interface DashboardStats {
  total_users: number;
  verified_users: number;
  active_users: number;
  admin_users: number;
  users_by_role: Record<string, number>;
  recent_registrations: number;
}

interface RecentActivity {
  id: string;
  action: string;
  description: string;
  timestamp: string;
  type: 'user' | 'whitelist' | 'settings';
}

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(
    null
  );
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState('');
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchDashboardStats();
    }
  }, [activeTab]);

  useEffect(() => {
    // Listen for navigation events from SystemSettings
    const handleNavigateToTab = (event: CustomEvent) => {
      if (event.detail === 'llm') {
        setActiveTab('llm');
      }
    };
    
    window.addEventListener('navigate-to-tab', handleNavigateToTab as EventListener);
    return () => {
      window.removeEventListener('navigate-to-tab', handleNavigateToTab as EventListener);
    };
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setIsLoadingStats(true);
      setStatsError('');

      const [statsResponse] = await Promise.all([
        api.get('/api/admin/users/stats'),
        // Could add more endpoints here for unit stats, etc.
      ]);

      setDashboardStats(statsResponse.data);

      // Generate some mock recent activity for now
      // In a real app, this would come from an audit log API
      setRecentActivity([
        {
          id: '1',
          action: 'New user registered',
          description: `john.doe@example.com`,
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          type: 'user',
        },
        {
          id: '2',
          action: 'Email whitelist updated',
          description: 'Added 3 new domains',
          timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          type: 'whitelist',
        },
        {
          id: '3',
          action: 'System settings changed',
          description: 'AI features enabled',
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          type: 'settings',
        },
      ]);
    } catch (error: any) {
      console.error('Error fetching dashboard stats:', error);
      setStatsError('Failed to load dashboard statistics');
    } finally {
      setIsLoadingStats(false);
    }
  };

  const handleLogout = () => {
    logout();
    localStorage.removeItem('token');
    navigate('/login');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return 'Just now';
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays === 1) return '1 day ago';
    return `${diffDays} days ago`;
  };

  const getActivityIcon = (type: RecentActivity['type']) => {
    switch (type) {
      case 'user':
        return 'bg-green-500';
      case 'whitelist':
        return 'bg-blue-500';
      case 'settings':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const sidebarItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'whitelist', label: 'Email Whitelist', icon: Mail },
    { id: 'settings', label: 'System Settings', icon: Settings },
    { id: 'llm', label: 'LLM Configuration', icon: Brain },
  ] as const;

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        if (isLoadingStats) {
          return (
            <div className='flex items-center justify-center h-64'>
              <Loader2 className='w-8 h-8 animate-spin text-purple-600' />
            </div>
          );
        }

        if (statsError) {
          return (
            <div className='bg-red-50 border border-red-200 rounded-lg p-6'>
              <p className='text-red-600'>{statsError}</p>
              <button
                onClick={fetchDashboardStats}
                className='mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700'
              >
                Retry
              </button>
            </div>
          );
        }

        return (
          <div className='space-y-6'>
            <h2 className='text-2xl font-semibold text-gray-900'>
              Dashboard Overview
            </h2>

            {/* Stats Cards */}
            <div className='grid grid-cols-1 md:grid-cols-3 gap-6'>
              <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                <div className='flex items-center justify-between'>
                  <div>
                    <p className='text-sm text-gray-600'>Total Users</p>
                    <p className='text-2xl font-semibold text-gray-900 mt-1'>
                      {dashboardStats?.total_users || 0}
                    </p>
                  </div>
                  <Users className='w-8 h-8 text-purple-600' />
                </div>
                <p className='text-sm text-green-600 mt-2'>
                  +{dashboardStats?.recent_registrations || 0} this week
                </p>
              </div>

              <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                <div className='flex items-center justify-between'>
                  <div>
                    <p className='text-sm text-gray-600'>Active Users</p>
                    <p className='text-2xl font-semibold text-gray-900 mt-1'>
                      {dashboardStats?.active_users || 0}
                    </p>
                  </div>
                  <Activity className='w-8 h-8 text-purple-600' />
                </div>
                <p className='text-sm text-blue-600 mt-2'>
                  {dashboardStats?.verified_users || 0} verified
                </p>
              </div>

              <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                <div className='flex items-center justify-between'>
                  <div>
                    <p className='text-sm text-gray-600'>Admin Users</p>
                    <p className='text-2xl font-semibold text-gray-900 mt-1'>
                      {dashboardStats?.admin_users || 0}
                    </p>
                  </div>
                  <Shield className='w-8 h-8 text-purple-600' />
                </div>
                <p className='text-sm text-gray-600 mt-2'>
                  System administrators
                </p>
              </div>
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

            {/* Recent Activity */}
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Recent Activity
              </h3>
              {recentActivity.length > 0 ? (
                <div className='space-y-4'>
                  {recentActivity.map((activity, index) => (
                    <div
                      key={activity.id}
                      className={`flex items-center justify-between py-3 ${
                        index < recentActivity.length - 1
                          ? 'border-b border-gray-100'
                          : ''
                      }`}
                    >
                      <div className='flex items-center gap-3'>
                        <div
                          className={`w-2 h-2 ${getActivityIcon(activity.type)} rounded-full`}
                        ></div>
                        <div>
                          <p className='text-sm font-medium text-gray-900'>
                            {activity.action}
                          </p>
                          <p className='text-xs text-gray-600'>
                            {activity.description}
                          </p>
                        </div>
                      </div>
                      <span className='text-xs text-gray-500'>
                        {formatDate(activity.timestamp)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className='text-gray-500 text-center py-8'>
                  No recent activity
                </p>
              )}
            </div>
          </div>
        );
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

export default AdminDashboard;
