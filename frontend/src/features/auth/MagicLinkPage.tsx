import { useEffect, useRef, useState } from 'react';
import { GraduationCap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { setStoredToken } from '../../services/authSession';
import { useAuthStore } from '../../stores/authStore';
import { Alert, Button } from '../../components/ui';
import type { User } from '../../types/index';

const MagicLinkPage = () => {
  const [status, setStatus] = useState<'verifying' | 'totp' | 'error'>(
    'verifying'
  );
  const [error, setError] = useState('');
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const started = useRef(false);
  const login = useAuthStore(state => state.login);
  const navigate = useNavigate();

  const finish = (data: { access_token: string; user: User }) => {
    setStoredToken(data.access_token);
    login(data.user);
    navigate(data.user.role === 'admin' ? '/admin' : '/dashboard', {
      replace: true,
    });
  };

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const token = hash.get('token');
    if (!token) {
      setStatus('error');
      setError('This sign-in link is missing its token.');
      return;
    }

    api
      .post('/auth/magic-link/verify', { token })
      .then(res => {
        if (res.data?.mfaRequired) {
          setMfaToken(res.data.mfaToken);
          setStatus('totp');
        } else {
          finish(res.data);
        }
      })
      .catch(() => {
        setStatus('error');
        setError('This sign-in link is invalid, expired, or already used.');
      });
    // One-shot: the token must only be consumed once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const verifyCode = async () => {
    if (!mfaToken) return;
    setBusy(true);
    setError('');
    try {
      const res = await api.post('/auth/totp/verify', {
        mfaToken,
        code: code.trim(),
      });
      finish(res.data);
    } catch {
      setError('That code was not accepted.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className='min-h-screen flex items-center justify-center bg-gray-50 px-4'>
      <div className='w-full max-w-md bg-white rounded-2xl shadow-xl p-8 space-y-4'>
        <div className='flex flex-col items-center'>
          <GraduationCap className='w-12 h-12 text-purple-600' />
          <h1 className='mt-4 text-2xl font-bold text-gray-900'>
            Sign in to Curriculum Curator
          </h1>
        </div>

        {status === 'verifying' && (
          <p className='text-center text-sm text-gray-600'>
            Checking your link…
          </p>
        )}

        {status === 'error' && <Alert variant='error'>{error}</Alert>}

        {status === 'totp' && (
          <div className='space-y-3'>
            <p className='text-sm text-gray-600'>
              Enter the 6-digit code from your authenticator, or a recovery
              code.
            </p>
            {error && <Alert variant='error'>{error}</Alert>}
            <input
              value={code}
              onChange={e => setCode(e.target.value)}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg'
              placeholder='123456 or recovery code'
            />
            <Button
              onClick={() => void verifyCode()}
              loading={busy}
              className='w-full'
            >
              Verify and sign in
            </Button>
          </div>
        )}

        {status === 'error' && (
          <Button
            variant='secondary'
            onClick={() => navigate('/')}
            className='w-full'
          >
            Back to sign in
          </Button>
        )}
      </div>
    </div>
  );
};

export default MagicLinkPage;
