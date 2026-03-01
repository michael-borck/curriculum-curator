import { useState, useEffect, useCallback } from 'react';
import { Plus, Trash2, Mail, Info } from 'lucide-react';
import api from '../../services/api';
import {
  LoadingState,
  Alert,
  Button,
  EmptyState,
  useConfirmDialog,
} from '../../components/ui';

interface WhitelistEntry {
  id: string;
  pattern: string;
  description?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

const EmailWhitelist = () => {
  const confirm = useConfirmDialog();
  const [entries, setEntries] = useState<WhitelistEntry[]>([]);
  const [newEntry, setNewEntry] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const fetchWhitelist = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/admin/whitelist');
      setEntries(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load whitelist');
      console.error('Error fetching whitelist:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWhitelist();
  }, [fetchWhitelist]);

  const validateEntry = (): boolean => {
    if (!newEntry.trim()) {
      setError('Please enter an email pattern');
      return false;
    }

    const isDuplicate = entries.some(
      entry => entry.pattern.toLowerCase() === newEntry.toLowerCase()
    );

    if (isDuplicate) {
      setError('This entry already exists in the whitelist');
      return false;
    }

    return true;
  };

  const handleAdd = async () => {
    if (!validateEntry()) return;

    setIsAdding(true);
    setError('');

    try {
      const response = await api.post('/admin/whitelist', {
        pattern: newEntry.toLowerCase(),
        description: newDescription || `Email pattern: ${newEntry}`,
        is_active: true,
      });

      setEntries([response.data, ...entries]);
      setNewEntry('');
      setNewDescription('');
      setSuccess('Email pattern added successfully');
      window.setTimeout(() => setSuccess(''), 3000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Failed to add entry');
      }
    } finally {
      setIsAdding(false);
    }
  };

  const handleDelete = async (id: string) => {
    const ok = await confirm({
      title: 'Remove whitelist entry?',
      message: 'Are you sure you want to remove this entry?',
      confirmLabel: 'Remove',
      variant: 'danger',
    });
    if (!ok) return;

    try {
      await api.delete(`/admin/whitelist/${id}`);
      setEntries(entries.filter(entry => entry.id !== id));
      setSuccess('Entry removed successfully');
      window.setTimeout(() => setSuccess(''), 3000);
    } catch {
      setError('Failed to remove entry');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return <LoadingState message='Loading whitelist...' />;
  }

  return (
    <div className='space-y-6'>
      <div>
        <h2 className='text-2xl font-semibold text-gray-900'>
          Email Whitelist
        </h2>
        <p className='mt-1 text-sm text-gray-600'>
          Manage allowed email addresses and domains for user registration
        </p>
      </div>

      {/* Info Box */}
      <Alert variant='info'>
        <div className='flex items-start gap-3'>
          <Info className='w-5 h-5 flex-shrink-0 mt-0.5' />
          <div className='text-sm'>
            <p className='font-medium mb-1'>How it works:</p>
            <ul className='list-disc list-inside space-y-1'>
              <li>Add specific email addresses to allow individual users</li>
              <li>
                Add domains (e.g., company.com) to allow all emails from that
                domain
              </li>
              <li>Only whitelisted emails can register new accounts</li>
            </ul>
          </div>
        </div>
      </Alert>

      {/* Add New Entry */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          Add New Entry
        </h3>

        {error && (
          <Alert
            variant='error'
            onDismiss={() => setError('')}
            className='mb-4'
          >
            {error}
          </Alert>
        )}

        {success && (
          <Alert
            variant='success'
            onDismiss={() => setSuccess('')}
            className='mb-4'
          >
            {success}
          </Alert>
        )}

        <div className='space-y-4'>
          <div className='flex gap-4'>
            <input
              type='text'
              value={newEntry}
              onChange={e => {
                setNewEntry(e.target.value);
                setError('');
              }}
              placeholder='@example.com or user@example.com'
              className='flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
              onKeyPress={e =>
                e.key === 'Enter' && !newDescription && handleAdd()
              }
            />

            <Button
              onClick={handleAdd}
              loading={isAdding}
              disabled={!newEntry.trim()}
            >
              <Plus className='w-4 h-4 mr-2' />
              Add
            </Button>
          </div>

          <input
            type='text'
            value={newDescription}
            onChange={e => setNewDescription(e.target.value)}
            placeholder='Optional description (e.g., "Company employees")'
            className='w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
            onKeyPress={e => e.key === 'Enter' && handleAdd()}
          />
        </div>
      </div>

      {/* Whitelist Entries */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden'>
        <div className='px-6 py-4 border-b border-gray-200'>
          <h3 className='text-lg font-semibold text-gray-900'>
            Current Whitelist
          </h3>
        </div>

        {entries.length === 0 ? (
          <EmptyState
            icon={Mail}
            title='No whitelist entries yet'
            description='Add emails or domains to control who can register'
          />
        ) : (
          <div className='divide-y divide-gray-200'>
            {entries.map(entry => (
              <div
                key={entry.id}
                className='px-6 py-4 flex items-center justify-between hover:bg-gray-50'
              >
                <div className='flex items-center gap-3'>
                  <div className='p-2 rounded-full bg-purple-100'>
                    <Mail className='w-5 h-5 text-purple-600' />
                  </div>
                  <div>
                    <p className='text-sm font-medium text-gray-900'>
                      {entry.pattern}
                    </p>
                    {entry.description && (
                      <p className='text-xs text-gray-600 mb-1'>
                        {entry.description}
                      </p>
                    )}
                    <p className='text-xs text-gray-500'>
                      Added on {formatDate(entry.createdAt)}
                      {!entry.isActive && (
                        <span className='ml-2 text-red-500'>(Inactive)</span>
                      )}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(entry.id)}
                  className='p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors'
                  title='Remove entry'
                >
                  <Trash2 className='w-4 h-4' />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary */}
      <div className='text-sm text-gray-600'>
        Total entries: {entries.length} (
        {entries.filter(e => e.isActive).length} active,{' '}
        {entries.filter(e => !e.isActive).length} inactive)
      </div>
    </div>
  );
};

export default EmailWhitelist;
