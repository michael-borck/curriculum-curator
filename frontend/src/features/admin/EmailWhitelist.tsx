import { useState, useEffect } from 'react';
import {
  Plus,
  Trash2,
  Mail,
  Globe,
  AlertCircle,
  CheckCircle,
  Loader2,
  Info,
} from 'lucide-react';
import api from '../../services/api';

interface WhitelistEntry {
  id: string;
  pattern: string;
  type: 'EMAIL' | 'DOMAIN';
  created_at: string;
  created_by: string;
}

const EmailWhitelist = () => {
  const [entries, setEntries] = useState<WhitelistEntry[]>([]);
  const [newEntry, setNewEntry] = useState('');
  const [entryType, setEntryType] = useState<'EMAIL' | 'DOMAIN'>('EMAIL');
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchWhitelist();
  }, []);

  const fetchWhitelist = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/admin/whitelist');
      setEntries(response.data);
      setError('');
    } catch (error: any) {
      setError('Failed to load whitelist');
      console.error('Error fetching whitelist:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const validateEntry = (): boolean => {
    if (!newEntry.trim()) {
      setError('Please enter an email or domain');
      return false;
    }

    if (entryType === 'EMAIL') {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(newEntry)) {
        setError('Please enter a valid email address');
        return false;
      }
    } else {
      const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-_.]*\.[a-zA-Z]{2,}$/;
      if (!domainRegex.test(newEntry)) {
        setError('Please enter a valid domain (e.g., example.com)');
        return false;
      }
    }

    // Check for duplicates
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
      const response = await api.post('/api/admin/whitelist', {
        pattern: newEntry.toLowerCase(),
        type: entryType,
      });

      setEntries([response.data, ...entries]);
      setNewEntry('');
      setSuccess(
        `${entryType === 'EMAIL' ? 'Email' : 'Domain'} added successfully`
      );

      window.setTimeout(() => setSuccess(''), 3000);
    } catch {
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
    if (!window.confirm('Are you sure you want to remove this entry?')) {
      return;
    }

    try {
      await api.delete(`/api/admin/whitelist/${id}`);
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
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='w-8 h-8 animate-spin text-purple-600' />
      </div>
    );
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
      <div className='bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3'>
        <Info className='w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5' />
        <div className='text-sm text-blue-800'>
          <p className='font-medium mb-1'>How it works:</p>
          <ul className='list-disc list-inside space-y-1 text-blue-700'>
            <li>Add specific email addresses to allow individual users</li>
            <li>
              Add domains (e.g., company.com) to allow all emails from that
              domain
            </li>
            <li>Only whitelisted emails can register new accounts</li>
          </ul>
        </div>
      </div>

      {/* Add New Entry */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          Add New Entry
        </h3>

        {error && (
          <div className='mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
            <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
            <p className='text-sm text-red-600'>{error}</p>
          </div>
        )}

        {success && (
          <div className='mb-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-start gap-2'>
            <CheckCircle className='w-5 h-5 text-green-600 flex-shrink-0 mt-0.5' />
            <p className='text-sm text-green-600'>{success}</p>
          </div>
        )}

        <div className='flex gap-4'>
          <select
            value={entryType}
            onChange={e => setEntryType(e.target.value as 'EMAIL' | 'DOMAIN')}
            className='px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
          >
            <option value='EMAIL'>Email Address</option>
            <option value='DOMAIN'>Domain</option>
          </select>

          <input
            type='text'
            value={newEntry}
            onChange={e => {
              setNewEntry(e.target.value);
              setError('');
            }}
            placeholder={
              entryType === 'EMAIL' ? 'user@example.com' : 'example.com'
            }
            className='flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
            onKeyPress={e => e.key === 'Enter' && handleAdd()}
          />

          <button
            onClick={handleAdd}
            disabled={isAdding || !newEntry.trim()}
            className='px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:bg-purple-400 disabled:cursor-not-allowed flex items-center gap-2'
          >
            {isAdding ? (
              <>
                <Loader2 className='w-4 h-4 animate-spin' />
                Adding...
              </>
            ) : (
              <>
                <Plus className='w-4 h-4' />
                Add
              </>
            )}
          </button>
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
          <div className='text-center py-12'>
            <Mail className='w-12 h-12 text-gray-400 mx-auto mb-4' />
            <p className='text-gray-500'>No whitelist entries yet</p>
            <p className='text-sm text-gray-400 mt-1'>
              Add emails or domains to control who can register
            </p>
          </div>
        ) : (
          <div className='divide-y divide-gray-200'>
            {entries.map(entry => (
              <div
                key={entry.id}
                className='px-6 py-4 flex items-center justify-between hover:bg-gray-50'
              >
                <div className='flex items-center gap-3'>
                  <div
                    className={`p-2 rounded-full ${
                      entry.type === 'EMAIL' ? 'bg-purple-100' : 'bg-blue-100'
                    }`}
                  >
                    {entry.type === 'EMAIL' ? (
                      <Mail
                        className={`w-5 h-5 ${
                          entry.type === 'EMAIL'
                            ? 'text-purple-600'
                            : 'text-blue-600'
                        }`}
                      />
                    ) : (
                      <Globe className='w-5 h-5 text-blue-600' />
                    )}
                  </div>
                  <div>
                    <p className='text-sm font-medium text-gray-900'>
                      {entry.pattern}
                    </p>
                    <p className='text-xs text-gray-500'>
                      Added on {formatDate(entry.created_at)} by{' '}
                      {entry.created_by}
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
        {entries.filter(e => e.type === 'EMAIL').length} emails,{' '}
        {entries.filter(e => e.type === 'DOMAIN').length} domains)
      </div>
    </div>
  );
};

export default EmailWhitelist;
