import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  Plus,
  Upload,
  Target,
  Brain,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Search,
  Bell,
  GraduationCap,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import type { DashboardProps } from '../../types/index';

const Dashboard = ({ children, onLogout }: DashboardProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout: authStoreLogout } = useAuthStore();
  const logout = onLogout || authStoreLogout;
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: BookOpen, label: 'My Courses', path: '/courses' },
    { icon: Plus, label: 'Create Content', path: '/content/new' },
    { icon: Upload, label: 'Import Materials', path: '/import' },
    { icon: Target, label: 'Teaching Style', path: '/teaching-style' },
    { icon: Brain, label: 'AI Assistant', path: '/ai-assistant' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  const isActive = (path: string): boolean => location.pathname === path;

  return (
    <div className='h-screen flex overflow-hidden bg-gray-50'>
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className='md:hidden fixed inset-0 bg-black bg-opacity-50 z-40'
          role='button'
          tabIndex={0}
          onClick={() => setSidebarOpen(false)}
          onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ' ') {
              setSidebarOpen(false);
            }
          }}
        />
      )}

      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 transition-transform duration-300 fixed md:static inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white flex flex-col`}
      >
        <div className='p-4 border-b border-gray-800'>
          <div className='flex items-center justify-between'>
            <div className='flex items-center gap-2'>
              <GraduationCap className='w-8 h-8 text-purple-400' />
              <span className='text-xl font-bold'>Curriculum Curator</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className='md:hidden text-gray-400 hover:text-white'
            >
              <X className='w-6 h-6' />
            </button>
          </div>
        </div>

        <nav className='flex-1 overflow-y-auto py-4'>
          {menuItems.map(item => {
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => {
                  navigate(item.path);
                  setSidebarOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition ${
                  isActive(item.path)
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon className='w-5 h-5' />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className='p-4 border-t border-gray-800'>
          <button
            onClick={logout}
            className='w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white rounded-lg transition'
          >
            <LogOut className='w-5 h-5' />
            Sign Out
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className='flex-1 flex flex-col overflow-hidden'>
        {/* Top header */}
        <header className='bg-white shadow-sm border-b border-gray-200'>
          <div className='px-4 sm:px-6 lg:px-8 py-4'>
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-4'>
                <button
                  onClick={() => setSidebarOpen(true)}
                  className='md:hidden text-gray-600 hover:text-gray-900'
                >
                  <Menu className='w-6 h-6' />
                </button>
                <div className='relative'>
                  <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5' />
                  <input
                    type='text'
                    placeholder='Search courses, content...'
                    className='pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 w-64'
                  />
                </div>
              </div>

              <div className='flex items-center gap-4'>
                <button className='relative p-2 text-gray-600 hover:text-gray-900'>
                  <Bell className='w-6 h-6' />
                  <span className='absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full'></span>
                </button>

                <div className='relative'>
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className='flex items-center gap-2 text-gray-700 hover:text-gray-900'
                  >
                    <div className='w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white'>
                      {user?.name?.charAt(0) || 'U'}
                    </div>
                    <span className='hidden sm:block font-medium'>
                      {user?.name || 'User'}
                    </span>
                    <ChevronDown className='w-4 h-4' />
                  </button>

                  {userMenuOpen && (
                    <div className='absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50'>
                      <a
                        href='/profile'
                        className='block px-4 py-2 text-gray-700 hover:bg-gray-100'
                      >
                        Profile
                      </a>
                      <a
                        href='/settings'
                        className='block px-4 py-2 text-gray-700 hover:bg-gray-100'
                      >
                        Settings
                      </a>
                      <hr className='my-2' />
                      <button
                        onClick={logout}
                        className='block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100'
                      >
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className='flex-1 overflow-y-auto bg-gray-50'>{children}</main>
      </div>
    </div>
  );
};

export default Dashboard;
