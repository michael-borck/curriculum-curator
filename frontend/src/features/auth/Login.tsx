import { useState, useEffect } from 'react';
import { isDesktopClient, setStoredToken } from '../../services/authSession';
import { ArrowLeft, GraduationCap } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { startAuthentication } from '@simplewebauthn/browser';
import RegistrationModal from './RegistrationModal';
import PasswordResetFlow from './PasswordResetFlow';
import VerificationModal from './VerificationModal';
import { Alert, Button } from '../../components/ui';
import { useModal } from '../../hooks';
import type { LoginProps, HandleSubmitFunction } from '../../types/index';

const Login = ({ onBackToLanding }: LoginProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [verificationEmail, setVerificationEmail] = useState('');
  const [isFirstUserSetup, setIsFirstUserSetup] = useState(false);
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [magicMessage, setMagicMessage] = useState('');

  const registrationModal = useModal();
  const passwordResetModal = useModal();
  const verificationModal = useModal();

  const login = useAuthStore(state => state.login);
  const navigate = useNavigate();

  // Check if this is a fresh install (no users yet)
  useEffect(() => {
    api
      .get('/auth/config')
      .then(res => {
        if (res.data?.hasUsers === false) {
          setIsFirstUserSetup(true);
          registrationModal.open();
        }
      })
      .catch(() => {
        // Config endpoint unavailable — proceed with normal login
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const completeLogin = (data: {
    access_token: string;
    user: { role: string };
  }) => {
    setStoredToken(data.access_token);
    login(data.user as Parameters<typeof login>[0]);
    if (data.user.role === 'admin') {
      navigate('/admin');
    } else {
      navigate('/dashboard');
    }
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaToken) return;
    setError('');
    setIsLoading(true);
    try {
      const res = await api.post('/auth/totp/verify', {
        mfaToken,
        code: mfaCode.trim(),
      });
      completeLogin(res.data);
    } catch {
      setError(
        'That code was not accepted. Try the next code or a recovery code.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithPasskey = async () => {
    setError('');
    setIsLoading(true);
    try {
      const optionsRes = await api.post('/auth/passkeys/login/options');
      const credential = await startAuthentication({
        optionsJSON: optionsRes.data.options,
      });
      const res = await api.post('/auth/passkeys/login/verify', {
        credential,
        challengeToken: optionsRes.data.challengeToken,
      });
      completeLogin(res.data);
    } catch {
      setError('Passkey sign-in was cancelled or failed');
    } finally {
      setIsLoading(false);
    }
  };

  const requestMagicLink = async () => {
    if (!email.trim()) {
      setError('Enter your email address first');
      return;
    }
    setError('');
    setMagicMessage('');
    try {
      await api.post('/auth/magic-link', { email: email.trim() });
      setMagicMessage(
        'If that email can sign in, a one-time link has been sent. Open it on the device where you want to sign in.'
      );
    } catch {
      setMagicMessage(
        'If that email can sign in, a one-time link has been sent.'
      );
    }
  };

  const handleSubmit: HandleSubmitFunction = async e => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await api.post('/auth/login', {
        email,
        password,
      });

      if (response.status === 200) {
        if (response.data?.mfaRequired) {
          setMfaToken(response.data.mfaToken);
          setMfaCode('');
          setError('');
          return;
        }
        completeLogin(response.data);
      }
    } catch (err: unknown) {
      const error = err as {
        response?: {
          status?: number;
          data?: {
            detail?:
              | string
              | { error?: string; email?: string; message?: string };
          };
        };
      };

      if (error.response?.status === 401) {
        setError('Invalid email or password');
      } else if (error.response?.status === 403) {
        const detail = error.response?.data?.detail;
        if (
          detail &&
          typeof detail === 'object' &&
          detail.error === 'email_not_verified'
        ) {
          setVerificationEmail(detail.email || email);
          verificationModal.open();
          setError('');
        } else {
          setError('Please verify your email before logging in');
        }
      } else if (error.response?.status === 423) {
        setError(
          'Account is locked due to too many failed attempts. Please try again later.'
        );
      } else if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        setError(
          typeof detail === 'string' ? detail : detail.message || 'Login failed'
        );
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegistrationSuccess = () => {
    registrationModal.close();
    setIsFirstUserSetup(false);
    navigate('/dashboard');
  };

  return (
    <>
      <div className='min-h-screen flex items-center justify-center bg-gray-50'>
        <div className='max-w-md w-full space-y-8'>
          {onBackToLanding && (
            <button
              onClick={onBackToLanding}
              className='flex items-center gap-2 text-purple-600 hover:text-purple-700 font-medium'
            >
              <ArrowLeft className='w-4 h-4' />
              Back to Home
            </button>
          )}
          <div>
            <div className='flex justify-center mb-4'>
              <GraduationCap className='w-12 h-12 text-purple-600' />
            </div>
            <h2 className='mt-6 text-center text-3xl font-extrabold text-gray-900'>
              Sign in to Curriculum Curator
            </h2>
            <p className='mt-2 text-center text-sm text-gray-600'>
              Access your personalised content creation platform
            </p>
            <p className='mt-1 text-center text-xs text-gray-400'>
              v{__APP_VERSION__}
            </p>
          </div>

          {error && (
            <Alert variant='error' onDismiss={() => setError('')}>
              {error}
            </Alert>
          )}

          <form
            className='mt-8 space-y-6'
            onSubmit={mfaToken ? handleMfaSubmit : handleSubmit}
          >
            {mfaToken ? (
              <div className='space-y-2'>
                <p className='text-sm text-gray-600'>
                  Enter the 6-digit code from your authenticator, or one of your
                  recovery codes.
                </p>
                <input
                  value={mfaCode}
                  onChange={e => setMfaCode(e.target.value)}
                  required
                  className='appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm'
                  placeholder='123456 or recovery code'
                  disabled={isLoading}
                />
                <button
                  type='button'
                  onClick={() => {
                    setMfaToken(null);
                    setMfaCode('');
                    setError('');
                  }}
                  className='text-sm text-purple-600 hover:text-purple-500'
                >
                  Back to sign in
                </button>
              </div>
            ) : (
              <div className='rounded-md shadow-sm -space-y-px'>
                <div>
                  <input
                    type='email'
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    className='appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 focus:z-10 sm:text-sm'
                    placeholder='Email address'
                    disabled={isLoading}
                  />
                </div>
                <div>
                  <input
                    type='password'
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    className='appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 focus:z-10 sm:text-sm'
                    placeholder='Password'
                    disabled={isLoading}
                  />
                </div>
              </div>
            )}

            {!mfaToken && (
              <div className='flex items-center justify-between'>
                <div className='text-sm'>
                  <button
                    type='button'
                    onClick={passwordResetModal.open}
                    className='font-medium text-purple-600 hover:text-purple-500'
                  >
                    Forgot your password?
                  </button>
                </div>
              </div>
            )}

            <div>
              <Button
                type='submit'
                loading={isLoading}
                className='w-full bg-purple-600 hover:bg-purple-700 focus:ring-purple-500'
              >
                {mfaToken ? 'Verify code' : 'Sign in'}
              </Button>
            </div>

            {!mfaToken && !isDesktopClient() && (
              <div className='text-center -mt-2 space-y-2'>
                {typeof window !== 'undefined' &&
                  window.PublicKeyCredential && (
                    <button
                      type='button'
                      onClick={() => void signInWithPasskey()}
                      className='text-sm font-medium text-purple-600 hover:text-purple-500'
                    >
                      Sign in with a passkey
                    </button>
                  )}
                <div>
                  <button
                    type='button'
                    onClick={() => void requestMagicLink()}
                    className='text-sm text-purple-600 hover:text-purple-500'
                  >
                    Email me a one-time sign-in link instead
                  </button>
                  {magicMessage && (
                    <p className='mt-2 text-xs text-gray-600'>{magicMessage}</p>
                  )}
                </div>
              </div>
            )}

            {!mfaToken && (
              <div className='text-center'>
                <span className='text-sm text-gray-600'>
                  Don&apos;t have an account?{' '}
                  <button
                    type='button'
                    onClick={registrationModal.open}
                    className='font-medium text-purple-600 hover:text-purple-500'
                  >
                    Sign up
                  </button>
                </span>
              </div>
            )}

            <p className='text-sm text-gray-600 bg-white border border-gray-200 rounded-lg p-4'>
              You&apos;re signing in to a shared copy of Curriculum Curator. The
              people who run this server can access the work stored here. Prefer
              to draft in private first?{' '}
              <button
                type='button'
                onClick={() => navigate('/download')}
                className='font-medium text-purple-600 hover:text-purple-500'
              >
                Install the desktop app
              </button>{' '}
              on your own computer — no account needed — and share your work
              when you&apos;re ready.
            </p>
          </form>
        </div>
      </div>

      {/* Registration Modal */}
      <RegistrationModal
        isOpen={registrationModal.isOpen}
        onClose={() => {
          registrationModal.close();
          setIsFirstUserSetup(false);
        }}
        onSuccess={handleRegistrationSuccess}
        isFirstUserSetup={isFirstUserSetup}
      />

      {/* Password Reset Flow */}
      {passwordResetModal.isOpen && (
        <PasswordResetFlow
          onClose={passwordResetModal.close}
          onSuccess={() => {
            passwordResetModal.close();
            setError('');
          }}
        />
      )}

      {/* Verification Modal */}
      {verificationModal.isOpen && (
        <VerificationModal
          email={verificationEmail}
          onClose={verificationModal.close}
          onSuccess={() => {
            verificationModal.close();
            handleSubmit({
              preventDefault: () => {
                /* noop */
              },
            } as React.FormEvent<HTMLFormElement>);
          }}
        />
      )}
    </>
  );
};

export default Login;
