import { useState, useEffect } from 'react';
import { ArrowLeft, GraduationCap } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
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
        const { access_token, user } = response.data;

        localStorage.setItem('token', access_token);
        login(user);

        if (user.role === 'admin') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
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

          <form className='mt-8 space-y-6' onSubmit={handleSubmit}>
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

            <div>
              <Button
                type='submit'
                loading={isLoading}
                className='w-full bg-purple-600 hover:bg-purple-700 focus:ring-purple-500'
              >
                Sign in
              </Button>
            </div>

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
