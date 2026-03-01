import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  MoreVertical,
  Lock,
  Unlock,
  Trash2,
  CheckCircle,
  XCircle,
  UserX,
} from 'lucide-react';
import api from '../../services/api';
import {
  LoadingState,
  Alert,
  Button,
  EmptyState,
  useConfirmDialog,
} from '../../components/ui';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'lecturer' | 'admin' | 'student' | 'assistant';
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
  lastLogin?: string;
}

type RoleFilter = 'all' | 'lecturer' | 'admin' | 'student' | 'assistant';
type StatusFilter = 'all' | 'active' | 'inactive';

const roleOptions = [
  { value: 'all', label: 'All Roles' },
  { value: 'lecturer', label: 'Lecturers' },
  { value: 'admin', label: 'Admins' },
  { value: 'student', label: 'Students' },
  { value: 'assistant', label: 'Assistants' },
];

const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
];

const UserManagement = () => {
  const confirm = useConfirmDialog();
  const [users, setUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState<RoleFilter>('all');
  const [filterStatus, setFilterStatus] = useState<StatusFilter>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDropdown, setShowDropdown] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/admin/users');
      setUsers(response.data.users || response.data);
      setError('');
    } catch (err) {
      setError('Failed to load users');
      console.error('Error fetching users:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Filter users based on search, role, and status
  const filteredUsers = users.filter(user => {
    const matchesSearch =
      !searchQuery ||
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRole = filterRole === 'all' || user.role === filterRole;

    const matchesStatus =
      filterStatus === 'all' ||
      (filterStatus === 'active' ? user.isActive : !user.isActive);

    return matchesSearch && matchesRole && matchesStatus;
  });

  const handleToggleStatus = async (userId: string, currentStatus: boolean) => {
    try {
      await api.post(`/admin/users/${userId}/toggle-status`);
      setUsers(prev =>
        prev.map(user =>
          user.id === userId ? { ...user, isActive: !currentStatus } : user
        )
      );
      setShowDropdown(null);
    } catch (err) {
      console.error('Error updating user status:', err);
    }
  };

  const handleVerifyUser = async (userId: string) => {
    try {
      await api.post(`/admin/users/${userId}/verify`);
      setUsers(prev =>
        prev.map(user =>
          user.id === userId ? { ...user, isVerified: true } : user
        )
      );
      setShowDropdown(null);
    } catch (err) {
      console.error('Error verifying user:', err);
    }
  };

  const handleDeleteUser = async (
    userId: string,
    permanent: boolean = false
  ) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;

    const action = permanent ? 'permanently delete' : 'deactivate';
    const warning = permanent
      ? 'This will permanently remove the user and all their data. This action cannot be undone!'
      : 'This will deactivate the user account. They will not be able to login.';

    const ok = await confirm({
      title: `${action.charAt(0).toUpperCase() + action.slice(1)} ${user.email}?`,
      message: warning,
      confirmLabel: action.charAt(0).toUpperCase() + action.slice(1),
      variant: 'danger',
    });
    if (!ok) return;

    try {
      const response = await api.delete(
        `/admin/users/${userId}${permanent ? '?permanent=true' : ''}`
      );

      if (permanent) {
        setUsers(prev => prev.filter(u => u.id !== userId));
      } else {
        setUsers(prev =>
          prev.map(u => (u.id === userId ? { ...u, isActive: false } : u))
        );
      }

      const message = response.data?.message || `User ${action}d successfully`;
      window.alert(message);
      setShowDropdown(null);
    } catch (err) {
      console.error('Error deleting user:', err);
      window.alert(`Failed to ${action} user. Please try again.`);
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
    return <LoadingState message='Loading users...' />;
  }

  if (error) {
    return (
      <div className='space-y-4'>
        <Alert variant='error'>{error}</Alert>
        <Button onClick={fetchUsers}>Retry</Button>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      <h2 className='text-2xl font-semibold text-gray-900'>User Management</h2>

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
            onChange={e => setFilterRole(e.target.value as RoleFilter)}
            className='px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
          >
            {roleOptions.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value as StatusFilter)}
            className='px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
          >
            {statusOptions.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
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
                <UserRow
                  key={user.id}
                  user={user}
                  showDropdown={showDropdown === user.id}
                  onToggleDropdown={() =>
                    setShowDropdown(showDropdown === user.id ? null : user.id)
                  }
                  onToggleStatus={() =>
                    handleToggleStatus(user.id, user.isActive)
                  }
                  onVerify={() => handleVerifyUser(user.id)}
                  onDeactivate={() => handleDeleteUser(user.id, false)}
                  onDelete={() => handleDeleteUser(user.id, true)}
                  formatDate={formatDate}
                />
              ))}
            </tbody>
          </table>
        </div>

        {filteredUsers.length === 0 && (
          <EmptyState
            title='No users found'
            description='Try adjusting your search or filter criteria'
          />
        )}
      </div>

      {/* Summary */}
      <div className='text-sm text-gray-600'>
        Showing {filteredUsers.length} of {users.length} users
      </div>
    </div>
  );
};

// Extracted UserRow component for cleaner code
interface UserRowProps {
  user: User;
  showDropdown: boolean;
  onToggleDropdown: () => void;
  onToggleStatus: () => void;
  onVerify: () => void;
  onDeactivate: () => void;
  onDelete: () => void;
  formatDate: (date: string) => string;
}

const UserRow = ({
  user,
  showDropdown,
  onToggleDropdown,
  onToggleStatus,
  onVerify,
  onDeactivate,
  onDelete,
  formatDate,
}: UserRowProps) => {
  const roleColors: Record<User['role'], string> = {
    admin: 'bg-purple-100 text-purple-800',
    lecturer: 'bg-blue-100 text-blue-800',
    student: 'bg-green-100 text-green-800',
    assistant: 'bg-gray-100 text-gray-800',
  };

  return (
    <tr
      className={`hover:bg-gray-50 ${!user.isActive ? 'opacity-60 bg-gray-50' : ''}`}
    >
      <td className='px-6 py-4 whitespace-nowrap'>
        <div>
          <div className='text-sm font-medium text-gray-900'>{user.name}</div>
          <div className='text-sm text-gray-500'>{user.email}</div>
        </div>
      </td>
      <td className='px-6 py-4 whitespace-nowrap'>
        <span
          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${roleColors[user.role]}`}
        >
          {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
        </span>
      </td>
      <td className='px-6 py-4 whitespace-nowrap'>
        <span
          className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-full ${
            user.isActive
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {user.isActive ? (
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
        {user.isVerified ? (
          <CheckCircle className='w-5 h-5 text-green-600' />
        ) : (
          <XCircle className='w-5 h-5 text-gray-400' />
        )}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
        {formatDate(user.createdAt)}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
        {user.lastLogin ? formatDate(user.lastLogin) : 'Never'}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-right text-sm font-medium'>
        <div className='relative'>
          <button
            onClick={onToggleDropdown}
            className='text-gray-400 hover:text-gray-500'
          >
            <MoreVertical className='w-5 h-5' />
          </button>

          {showDropdown && (
            <UserActionsDropdown
              user={user}
              onToggleStatus={onToggleStatus}
              onVerify={onVerify}
              onDeactivate={onDeactivate}
              onDelete={onDelete}
            />
          )}
        </div>
      </td>
    </tr>
  );
};

// Extracted dropdown menu component
interface UserActionsDropdownProps {
  user: User;
  onToggleStatus: () => void;
  onVerify: () => void;
  onDeactivate: () => void;
  onDelete: () => void;
}

const UserActionsDropdown = ({
  user,
  onToggleStatus,
  onVerify,
  onDeactivate,
  onDelete,
}: UserActionsDropdownProps) => (
  <div className='absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200'>
    <div className='py-1'>
      {!user.isVerified && (
        <button
          onClick={onVerify}
          className='flex items-center gap-2 px-4 py-2 text-sm text-green-700 hover:bg-green-50 w-full text-left'
        >
          <CheckCircle className='w-4 h-4' />
          Verify User
        </button>
      )}
      <button
        onClick={onToggleStatus}
        className='flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left'
      >
        {user.isActive ? (
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
      {user.isActive && (
        <button
          onClick={onDeactivate}
          className='flex items-center gap-2 px-4 py-2 text-sm text-orange-600 hover:bg-orange-50 w-full text-left'
        >
          <UserX className='w-4 h-4' />
          Deactivate User
        </button>
      )}
      <button
        onClick={onDelete}
        className='flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left border-t border-gray-100'
      >
        <Trash2 className='w-4 h-4' />
        Permanently Delete
      </button>
    </div>
  </div>
);

export default UserManagement;
