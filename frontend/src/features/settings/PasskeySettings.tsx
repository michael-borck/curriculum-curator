import { useEffect, useState } from 'react';
import { KeyRound, Plus, Trash2 } from 'lucide-react';
import { startRegistration } from '@simplewebauthn/browser';
import toast from 'react-hot-toast';
import api from '../../services/api';

interface Passkey {
  id: string;
  name: string;
  createdAt: string;
  lastUsedAt?: string | null;
}

const PasskeySettings = () => {
  const [passkeys, setPasskeys] = useState<Passkey[]>([]);
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const res = await api.get('/auth/passkeys');
      setPasskeys(res.data.passkeys);
    } catch {
      setError('Could not load passkeys');
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const addPasskey = async () => {
    setBusy(true);
    setError('');
    try {
      const optionsRes = await api.post('/auth/passkeys/register/options');
      const credential = await startRegistration({
        optionsJSON: optionsRes.data.options,
      });
      await api.post('/auth/passkeys/register/verify', {
        credential,
        challengeToken: optionsRes.data.challengeToken,
        name: name.trim() || 'Passkey',
      });
      setName('');
      await load();
      toast.success('Passkey added');
    } catch {
      setError('Passkey registration was cancelled or failed');
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    try {
      await api.delete(`/auth/passkeys/${id}`);
      await load();
      toast.success('Passkey removed');
    } catch {
      toast.error('Could not remove passkey');
    }
  };

  const supported =
    typeof window !== 'undefined' && Boolean(window.PublicKeyCredential);

  return (
    <div className='bg-white rounded-lg shadow-md p-6 space-y-4'>
      <div className='flex items-center gap-2'>
        <KeyRound className='w-5 h-5 text-purple-600' />
        <h2 className='text-xl font-semibold'>Passkeys</h2>
      </div>

      <p className='text-sm text-gray-600'>
        Sign in with your device unlock (Touch ID, Windows Hello, a security
        key) instead of a password. Passkeys are phishing-resistant.
      </p>

      {!supported && (
        <div className='rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900'>
          This browser or desktop app does not support passkeys.
        </div>
      )}

      {error && (
        <div className='rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800'>
          {error}
        </div>
      )}

      {supported && (
        <div className='flex flex-wrap gap-2 items-center'>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder='Name (e.g. MacBook Touch ID)'
            className='px-3 py-2 border border-gray-300 rounded-lg'
          />
          <button
            type='button'
            onClick={() => void addPasskey()}
            disabled={busy}
            className='inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50'
          >
            <Plus className='w-4 h-4' /> Add passkey
          </button>
        </div>
      )}

      {passkeys.length === 0 ? (
        <p className='text-sm text-gray-500'>No passkeys registered yet.</p>
      ) : (
        <ul className='divide-y divide-gray-100'>
          {passkeys.map(passkey => (
            <li
              key={passkey.id}
              className='flex items-center justify-between py-3'
            >
              <div>
                <p className='text-sm font-medium text-gray-900'>
                  {passkey.name}
                </p>
                <p className='text-xs text-gray-500'>
                  Added {new Date(passkey.createdAt).toLocaleString()}
                </p>
              </div>
              <button
                type='button'
                onClick={() => void remove(passkey.id)}
                className='inline-flex items-center gap-1 text-sm text-red-600 hover:text-red-700'
              >
                <Trash2 className='w-4 h-4' /> Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PasskeySettings;
