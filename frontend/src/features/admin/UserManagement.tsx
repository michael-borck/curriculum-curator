import { useState, useEffect } from 'react';
import {
  Search,
  MoreVertical,
  UserPlus,
  Lock,
  Unlock,
  Trash2,
  Edit,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import api from '../../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'USER' | 'ADMIN';
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  last_login?: string;
}

const UserManagement = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState<'all' | 'USER' | 'ADMIN'>('all');
  const [filterStatus, setFilterStatus] = useState<
    'all' | 'active' | 'inactive'
  >('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDropdown, setShowDropdown] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    filterUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [users, searchQuery, filterRole, filterStatus]);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/admin/users');
      setUsers(response.data);
      setError('');
    } catch (error: any) {
      setError('Failed to load users');
      console.error('Error fetching users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterUsers = () => {
    let filtered = [...users];

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        user =>
          user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          user.email.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Role filter
    if (filterRole !== 'all') {
      filtered = filtered.filter(user => user.role === filterRole);
    }

    // Status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(user =>
        filterStatus === 'active' ? user.is_active : !user.is_active
      );
    }

    setFilteredUsers(filtered);
  };

  const handleToggleStatus = async (userId: string, currentStatus: boolean) => {
    try {
      await api.patch(`/api/admin/users/${userId}/status`, {
        is_active: !currentStatus,
      });

      setUsers(
        users.map(user =>
          user.id === userId ? { ...user, is_active: !currentStatus } : user
        )
      );

      setShowDropdown(null);
    } catch (error) {
      console.error('Error updating user status:', error);
    }
  };

  const handleChangeRole = async (
    userId: string,
    newRole: 'USER' | 'ADMIN'
  ) => {
    try {
      await api.patch(`/api/admin/users/${userId}/role`, { role: newRole });

      setUsers(
        users.map(user =>
          user.id === userId ? { ...user, role: newRole } : user
        )
      );

      setShowDropdown(null);
    } catch (error) {
      console.error('Error updating user role:', error);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return;
    }

    try {
      await api.delete(`/api/admin/users/${userId}`);
      setUsers(users.filter(user => user.id !== userId));
      setShowDropdown(null);
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='w-8 h-8 animate-spin text-purple-600' />
      </div>
    );
  }

  if (error) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-center'>
          <AlertCircle className='w-12 h-12 text-red-500 mx-auto mb-4' />
          <p className='text-gray-600'>{error}</p>
          <button
            onClick={fetchUsers}
            className='mt-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700'
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      <div className='flex justify-between items-center'>
        <h2 className='text-2xl font-semibold text-gray-900'>
          User Management
        </h2>
        <button className='flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors'>
          <UserPlus className='w-4 h-4' />
          Add User
        </button>
      </div>

      {/* Filters */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
        <div className='flex flex-wrap gap-4'>
          {/* Search */}
          <div className='flex-1 min-w-[200px]'>
            <div className='relative'>
              <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5' />
              <input
                type='text'
                placeholder='Search users...'
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
              />
            </div>
          </div>

          {/* Role Filter */}
          <select
            value={filterRole}
            onChange={e => setFilterRole(e.target.value as typeof filterRole)}
            className='px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
          >
            <option value='all'>All Roles</option>
            <option value='USER'>Users</option>
            <option value='ADMIN'>Admins</option>
          </select>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={e =>
              setFilterStatus(e.target.value as typeof filterStatus)
            }
            className='px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
          >
            <option value='all'>All Status</option>
            <option value='active'>Active</option>
            <option value='inactive'>Inactive</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden'>
        <div className='overflow-x-auto'>
          <table className='w-full'>
            <thead className='bg-gray-50 border-b border-gray-200'>
              <tr>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  User
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Role
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Status
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Verified
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Created
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Last Login
                </th>
                <th className='relative px-6 py-3'>
                  <span className='sr-only'>Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className='bg-white divide-y divide-gray-200'>
              {filteredUsers.map(user => (
                <tr key={user.id} className='hover:bg-gray-50'>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div>
                      <div className='text-sm font-medium text-gray-900'>
                        {user.name}
                      </div>
                      <div className='text-sm text-gray-500'>{user.email}</div>
                    </div>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.role === 'ADMIN'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-full ${
                        user.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.is_active ? (
                        <>
                          <CheckCircle className='w-3 h-3' />
                          Active
                        </>
                      ) : (
                        <>
                          <XCircle className='w-3 h-3' />
                          Inactive
                        </>
                      )}
                    </span>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    {user.email_verified ? (
                      <CheckCircle className='w-5 h-5 text-green-600' />
                    ) : (
                      <XCircle className='w-5 h-5 text-gray-400' />
                    )}
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                    {formatDate(user.created_at)}
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                    {user.last_login ? formatDate(user.last_login) : 'Never'}
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-right text-sm font-medium'>
                    <div className='relative'>
                      <button
                        onClick={() =>
                          setShowDropdown(
                            showDropdown === user.id ? null : user.id
                          )
                        }
                        className='text-gray-400 hover:text-gray-500'
                      >
                        <MoreVertical className='w-5 h-5' />
                      </button>

                      {showDropdown === user.id && (
                        <div className='absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200'>
                          <div className='py-1'>
                            <button
                              onClick={() =>
                                handleToggleStatus(user.id, user.is_active)
                              }
                              className='flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left'
                            >
                              {user.is_active ? (
                                <>
                                  <Lock className='w-4 h-4' />
                                  Deactivate
                                </>
                              ) : (
                                <>
                                  <Unlock className='w-4 h-4' />
                                  Activate
                                </>
                              )}
                            </button>
                            <button
                              onClick={() =>
                                handleChangeRole(
                                  user.id,
                                  user.role === 'ADMIN' ? 'USER' : 'ADMIN'
                                )
                              }
                              className='flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left'
                            >
                              <Edit className='w-4 h-4' />
                              Make {user.role === 'ADMIN' ? 'User' : 'Admin'}
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              className='flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left'
                            >
                              <Trash2 className='w-4 h-4' />
                              Delete
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredUsers.length === 0 && (
          <div className='text-center py-12'>
            <p className='text-gray-500'>No users found</p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className='text-sm text-gray-600'>
        Showing {filteredUsers.length} of {users.length} users
      </div>
    </div>
  );
};

export default UserManagement;
