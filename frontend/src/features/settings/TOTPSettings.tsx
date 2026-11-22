import { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { CheckCircle, Copy, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../../services/api';

interface TOTPStatus {
  enabled: boolean;
  recoveryCodesRemaining: number;
}

interface TOTPSetup {
  secret: string;
  otpauthUrl: string;
  recoveryCodes: string[];
}

const TOTPSettings = () => {
  const [status, setStatus] = useState<TOTPStatus | null>(null);
  const [setup, setSetup] = useState<TOTPSetup | null>(null);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const loadStatus = async () => {
    try {
      const res = await api.get('/auth/totp/status');
      setStatus(res.data);
    } catch {
      setError('Could not load two-factor status');
    }
  };

  useEffect(() => {
    void loadStatus();
  }, []);

  const copy = async (value: string, label: string) => {
    try {
      await navigator.clipboard.writeText(value);
      toast.success(`${label} copied`);
    } catch {
      toast.error('Clipboard unavailable');
    }
  };

  const startSetup = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await api.post('/auth/totp/setup');
      setSetup(res.data);
    } catch {
      setError('Could not start setup');
    } finally {
      setBusy(false);
    }
  };

  const enable = async () => {
    setBusy(true);
    setError('');
    try {
      await api.post('/auth/totp/enable', { code });
      setSetup(null);
      setCode('');
      await loadStatus();
      toast.success('Two-factor authentication enabled');
    } catch {
      setError(
        'That code was not accepted. Check your authenticator and try again.'
      );
    } finally {
      setBusy(false);
    }
  };

  const disable = async () => {
    setBusy(true);
    setError('');
    try {
      await api.post('/auth/totp/disable', { password, code });
      setPassword('');
      setCode('');
      await loadStatus();
      toast.success('Two-factor authentication disabled');
    } catch {
      setError('Password or code was not accepted');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className='bg-white rounded-lg shadow-md p-6 space-y-4'>
      <div className='flex items-center gap-2'>
        <ShieldCheck className='w-5 h-5 text-purple-600' />
        <h2 className='text-xl font-semibold'>Two-Factor Authentication</h2>
      </div>

      <p className='text-sm text-gray-600'>
        Use an authenticator app (1Password, Bitwarden, Google Authenticator,
        Authy) for a second code at sign-in. You will also get one-time recovery
        codes; store them somewhere safe.
      </p>

      {error && (
        <div className='rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800'>
          {error}
        </div>
      )}

      {status?.enabled && !setup && (
        <div className='space-y-4'>
          <p className='flex items-center gap-2 text-sm text-green-700'>
            <CheckCircle className='w-4 h-4' />
            Enabled — {status.recoveryCodesRemaining} recovery code(s) remaining
          </p>
          <div className='grid gap-3 max-w-md'>
            <input
              type='password'
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder='Current password'
              className='px-3 py-2 border border-gray-300 rounded-lg'
            />
            <input
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder='Current 6-digit or recovery code'
              className='px-3 py-2 border border-gray-300 rounded-lg'
            />
            <button
              type='button'
              onClick={() => void disable()}
              disabled={busy || !password || !code}
              className='px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50'
            >
              Disable two-factor
            </button>
          </div>
        </div>
      )}

      {!status?.enabled && !setup && (
        <button
          type='button'
          onClick={() => void startSetup()}
          disabled={busy}
          className='px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50'
        >
          Set up authenticator
        </button>
      )}

      {setup && (
        <div className='grid gap-6 md:grid-cols-2 max-w-3xl'>
          <div className='space-y-3'>
            <div className='bg-white border border-gray-200 rounded-lg p-3 inline-block'>
              <QRCodeSVG value={setup.otpauthUrl} size={180} />
            </div>
            <p className='text-xs text-gray-500'>
              Scan with your authenticator, or enter the secret manually.
            </p>
            <button
              type='button'
              onClick={() => void copy(setup.secret, 'Secret')}
              className='inline-flex items-center gap-2 text-sm font-mono rounded border border-gray-300 px-3 py-2 hover:bg-gray-50'
            >
              <Copy className='w-4 h-4' />
              {setup.secret}
            </button>
          </div>

          <div className='space-y-3'>
            <input
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder='Enter the 6-digit code'
              className='w-full px-3 py-2 border border-gray-300 rounded-lg'
            />
            <button
              type='button'
              onClick={() => void enable()}
              disabled={busy || code.length < 6}
              className='px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50'
            >
              Enable
            </button>

            <div className='rounded-lg border border-amber-200 bg-amber-50 p-3'>
              <p className='text-sm font-medium text-amber-900'>
                Recovery codes — shown once
              </p>
              <p className='text-xs text-amber-800 mb-2'>
                Each works once if you lose your authenticator.
              </p>
              <button
                type='button'
                onClick={() =>
                  void copy(setup.recoveryCodes.join('\n'), 'Recovery codes')
                }
                className='mb-2 inline-flex items-center gap-2 text-xs font-medium text-amber-900 hover:underline'
              >
                <Copy className='w-3 h-3' /> Copy all
              </button>
              <ul className='grid grid-cols-2 gap-1 font-mono text-xs text-amber-900'>
                {setup.recoveryCodes.map(item => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TOTPSettings;
