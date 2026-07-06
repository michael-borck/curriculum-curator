import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, KeyRound, Copy, Check, Info } from 'lucide-react';
import api from '../../services/api';
import { LoadingState, Alert, Button, EmptyState } from '../../components/ui';

interface PendingVerification {
  userId: string;
  email: string;
  name: string;
  code: string;
  expiresAt: string;
  createdAt: string;
}

const formatWhen = (iso: string): string => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
};

const PendingVerifications = () => {
  const [items, setItems] = useState<PendingVerification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchPending = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/admin/pending-verifications');
      setItems(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load pending sign-ups.');
      console.error('Error fetching pending verifications:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  const copyCode = async (code: string, userId: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedId(userId);
      setTimeout(() => setCopiedId(null), 1500);
    } catch (err) {
      console.error('Clipboard unavailable:', err);
    }
  };

  if (isLoading) {
    return <LoadingState message='Loading pending sign-ups…' />;
  }

  return (
    <div className='space-y-4'>
      <div className='flex items-start justify-between gap-4'>
        <div>
          <h2 className='text-xl font-semibold text-gray-900'>
            Pending Sign-ups
          </h2>
          <p className='text-sm text-gray-600 mt-1'>
            Users who registered but haven&apos;t verified their email yet.
          </p>
        </div>
        <Button variant='secondary' onClick={fetchPending}>
          <RefreshCw className='w-4 h-4 mr-2' />
          Refresh
        </Button>
      </div>

      <div className='flex items-start gap-2 rounded-md bg-blue-50 border border-blue-200 p-3 text-sm text-blue-800'>
        <Info className='w-4 h-4 mt-0.5 flex-shrink-0' />
        <p>
          Verification codes are normally emailed. When email isn&apos;t
          configured, read the code here and pass it to the user so they can
          finish signing in. You can also verify a user directly from{' '}
          <span className='font-medium'>User Management</span>.
        </p>
      </div>

      {error && <Alert variant='error'>{error}</Alert>}

      {items.length === 0 ? (
        <EmptyState
          icon={KeyRound}
          title='No pending sign-ups'
          description='Everyone who registered has verified their email (or their codes have expired — they can request a new one).'
        />
      ) : (
        <div className='overflow-x-auto border border-gray-200 rounded-lg'>
          <table className='min-w-full divide-y divide-gray-200'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  User
                </th>
                <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Code
                </th>
                <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Registered
                </th>
                <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Code expires
                </th>
              </tr>
            </thead>
            <tbody className='bg-white divide-y divide-gray-200'>
              {items.map(item => (
                <tr key={item.userId}>
                  <td className='px-4 py-3'>
                    <div className='text-sm font-medium text-gray-900'>
                      {item.name}
                    </div>
                    <div className='text-sm text-gray-500'>{item.email}</div>
                  </td>
                  <td className='px-4 py-3'>
                    <button
                      type='button'
                      onClick={() => copyCode(item.code, item.userId)}
                      title='Copy code'
                      className='inline-flex items-center gap-2 font-mono text-base tracking-widest text-gray-900 hover:text-purple-700'
                    >
                      {item.code}
                      {copiedId === item.userId ? (
                        <Check className='w-4 h-4 text-green-600' />
                      ) : (
                        <Copy className='w-4 h-4 text-gray-400' />
                      )}
                    </button>
                  </td>
                  <td className='px-4 py-3 text-sm text-gray-500'>
                    {formatWhen(item.createdAt)}
                  </td>
                  <td className='px-4 py-3 text-sm text-gray-500'>
                    {formatWhen(item.expiresAt)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PendingVerifications;
