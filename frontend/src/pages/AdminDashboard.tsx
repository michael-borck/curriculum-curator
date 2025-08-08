import { useState } from 'react';
import {
  Users,
  Shield,
  Database,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Filter,
  Download,
  Mail,
} from 'lucide-react';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('all');

  const users = [
    {
      id: 1,
      name: 'Dr. Jane Smith',
      email: 'j.smith@university.edu',
      role: 'Lecturer',
      courses: 4,
      status: 'active',
      lastActive: '2 hours ago',
    },
    {
      id: 2,
      name: 'Prof. John Doe',
      email: 'j.doe@university.edu',
      role: 'Lecturer',
      courses: 6,
      status: 'active',
      lastActive: '1 day ago',
    },
    {
      id: 3,
      name: 'Dr. Emily Chen',
      email: 'e.chen@university.edu',
      role: 'Lecturer',
      courses: 0,
      status: 'pending',
      lastActive: 'Never',
    },
    {
      id: 4,
      name: 'Dr. Michael Brown',
      email: 'm.brown@university.edu',
      role: 'Lecturer',
      courses: 3,
      status: 'active',
      lastActive: '5 hours ago',
    },
    {
      id: 5,
      name: 'Sarah Johnson',
      email: 's.johnson@university.edu',
      role: 'Admin',
      courses: 0,
      status: 'active',
      lastActive: 'Now',
    },
  ];

  const systemStats = [
    { label: 'Total Users', value: 47, change: '+12%' },
    { label: 'Active Sessions', value: 23, change: '+5%' },
    { label: 'Content Items', value: 1243, change: '+18%' },
    { label: 'Storage Used', value: '8.2GB', change: '+3%' },
  ];

  return (
    <div className='p-6'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          Admin Dashboard
        </h1>
        <p className='text-gray-600'>
          Manage users, system settings, and platform configuration
        </p>
      </div>

      {/* System Stats */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-6 mb-8'>
        {systemStats.map((stat, index) => (
          <div
            key={index}
            className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'
          >
            <div className='flex items-center justify-between mb-2'>
              <p className='text-gray-600 text-sm'>{stat.label}</p>
              <span className='text-green-600 text-sm font-medium'>
                {stat.change}
              </span>
            </div>
            <p className='text-2xl font-bold text-gray-900'>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* User Management */}
      <div className='bg-white rounded-xl shadow-sm border border-gray-200'>
        <div className='p-6 border-b border-gray-200'>
          <div className='flex items-center justify-between mb-4'>
            <h2 className='text-xl font-semibold text-gray-900'>
              User Management
            </h2>
            <div className='flex gap-2'>
              <button className='px-4 py-2 text-purple-600 border border-purple-600 rounded-lg hover:bg-purple-50 transition'>
                <Mail className='w-4 h-4 inline mr-2' />
                Invite User
              </button>
              <button className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition'>
                <Users className='w-4 h-4 inline mr-2' />
                Add User
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className='flex gap-6 border-b border-gray-200'>
            {['all', 'lecturers', 'pending', 'blocked'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 px-1 font-medium transition ${
                  activeTab === tab
                    ? 'text-purple-600 border-b-2 border-purple-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Search and Filter */}
        <div className='p-4 border-b border-gray-200'>
          <div className='flex gap-4'>
            <div className='relative flex-1'>
              <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5' />
              <input
                type='text'
                placeholder='Search users...'
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>
            <button className='px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2'>
              <Filter className='w-4 h-4' />
              Filter
            </button>
            <button className='px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2'>
              <Download className='w-4 h-4' />
              Export
            </button>
          </div>
        </div>

        {/* User Table */}
        <div className='overflow-x-auto'>
          <table className='w-full'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Name
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Email
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Role
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Courses
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Status
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Last Active
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className='bg-white divide-y divide-gray-200'>
              {users.map(user => (
                <tr key={user.id} className='hover:bg-gray-50'>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div className='text-sm font-medium text-gray-900'>
                      {user.name}
                    </div>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div className='text-sm text-gray-600'>{user.email}</div>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div className='text-sm text-gray-900'>{user.role}</div>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div className='text-sm text-gray-900'>{user.courses}</div>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : user.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.status === 'active' && (
                        <CheckCircle className='w-3 h-3 mr-1' />
                      )}
                      {user.status === 'pending' && (
                        <Clock className='w-3 h-3 mr-1' />
                      )}
                      {user.status === 'blocked' && (
                        <XCircle className='w-3 h-3 mr-1' />
                      )}
                      {user.status}
                    </span>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-600'>
                    {user.lastActive}
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm'>
                    <div className='flex gap-2'>
                      {user.status === 'pending' ? (
                        <>
                          <button className='text-green-600 hover:text-green-900'>
                            Approve
                          </button>
                          <button className='text-red-600 hover:text-red-900'>
                            Reject
                          </button>
                        </>
                      ) : (
                        <>
                          <button className='text-blue-600 hover:text-blue-900'>
                            Edit
                          </button>
                          <button className='text-gray-600 hover:text-gray-900'>
                            View
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Settings */}
      <div className='grid md:grid-cols-3 gap-6 mt-8'>
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <Shield className='w-8 h-8 text-purple-600 mb-3' />
          <h3 className='font-semibold text-gray-900 mb-2'>Access Control</h3>
          <p className='text-sm text-gray-600 mb-4'>
            Manage permissions and roles
          </p>
          <button className='text-purple-600 hover:text-purple-700 font-medium text-sm'>
            Configure →
          </button>
        </div>
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <Database className='w-8 h-8 text-purple-600 mb-3' />
          <h3 className='font-semibold text-gray-900 mb-2'>System Settings</h3>
          <p className='text-sm text-gray-600 mb-4'>
            Configure platform settings
          </p>
          <button className='text-purple-600 hover:text-purple-700 font-medium text-sm'>
            Manage →
          </button>
        </div>
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <Activity className='w-8 h-8 text-purple-600 mb-3' />
          <h3 className='font-semibold text-gray-900 mb-2'>Audit Logs</h3>
          <p className='text-sm text-gray-600 mb-4'>
            View system activity logs
          </p>
          <button className='text-purple-600 hover:text-purple-700 font-medium text-sm'>
            View Logs →
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
