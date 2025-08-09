import { useState } from 'react';
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
  FileText,
  Activity,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import UserManagement from './UserManagement';
import EmailWhitelist from './EmailWhitelist';
import SystemSettings from './SystemSettings';

type TabType = 'overview' | 'users' | 'whitelist' | 'settings';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    localStorage.removeItem('token');
    navigate('/login');
  };

  const sidebarItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'whitelist', label: 'Email Whitelist', icon: Mail },
    { id: 'settings', label: 'System Settings', icon: Settings },
  ] as const;

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
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
                      124
                    </p>
                  </div>
                  <Users className='w-8 h-8 text-purple-600' />
                </div>
                <p className='text-sm text-green-600 mt-2'>
                  +12% from last month
                </p>
              </div>

              <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                <div className='flex items-center justify-between'>
                  <div>
                    <p className='text-sm text-gray-600'>Active Courses</p>
                    <p className='text-2xl font-semibold text-gray-900 mt-1'>
                      42
                    </p>
                  </div>
                  <FileText className='w-8 h-8 text-purple-600' />
                </div>
                <p className='text-sm text-green-600 mt-2'>
                  +8% from last month
                </p>
              </div>

              <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                <div className='flex items-center justify-between'>
                  <div>
                    <p className='text-sm text-gray-600'>System Health</p>
                    <p className='text-2xl font-semibold text-gray-900 mt-1'>
                      98%
                    </p>
                  </div>
                  <Activity className='w-8 h-8 text-purple-600' />
                </div>
                <p className='text-sm text-gray-600 mt-2'>
                  All systems operational
                </p>
              </div>
            </div>

            {/* Recent Activity */}
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Recent Activity
              </h3>
              <div className='space-y-4'>
                <div className='flex items-center justify-between py-3 border-b border-gray-100'>
                  <div className='flex items-center gap-3'>
                    <div className='w-2 h-2 bg-green-500 rounded-full'></div>
                    <div>
                      <p className='text-sm font-medium text-gray-900'>
                        New user registered
                      </p>
                      <p className='text-xs text-gray-600'>
                        john.doe@example.com
                      </p>
                    </div>
                  </div>
                  <span className='text-xs text-gray-500'>2 hours ago</span>
                </div>
                <div className='flex items-center justify-between py-3 border-b border-gray-100'>
                  <div className='flex items-center gap-3'>
                    <div className='w-2 h-2 bg-blue-500 rounded-full'></div>
                    <div>
                      <p className='text-sm font-medium text-gray-900'>
                        Email whitelist updated
                      </p>
                      <p className='text-xs text-gray-600'>
                        Added 3 new domains
                      </p>
                    </div>
                  </div>
                  <span className='text-xs text-gray-500'>5 hours ago</span>
                </div>
                <div className='flex items-center justify-between py-3'>
                  <div className='flex items-center gap-3'>
                    <div className='w-2 h-2 bg-purple-500 rounded-full'></div>
                    <div>
                      <p className='text-sm font-medium text-gray-900'>
                        System settings changed
                      </p>
                      <p className='text-xs text-gray-600'>
                        AI features enabled
                      </p>
                    </div>
                  </div>
                  <span className='text-xs text-gray-500'>1 day ago</span>
                </div>
              </div>
            </div>
          </div>
        );
      case 'users':
        return <UserManagement />;
      case 'whitelist':
        return <EmailWhitelist />;
      case 'settings':
        return <SystemSettings />;
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
