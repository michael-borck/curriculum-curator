import { useState } from 'react';
import { ArrowLeft, GraduationCap, Loader2, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import RegistrationModal from './RegistrationModal';
import PasswordResetFlow from './PasswordResetFlow';
import VerificationModal from './VerificationModal';
import type { LoginProps, HandleSubmitFunction } from '../../types/index';

const Login = ({ onBackToLanding }: LoginProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRegistration, setShowRegistration] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [showVerification, setShowVerification] = useState(false);
  const [verificationEmail, setVerificationEmail] = useState('');

  const login = useAuthStore(state => state.login);
  const navigate = useNavigate();

  const handleSubmit: HandleSubmitFunction = async e => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // OAuth2PasswordRequestForm expects form data
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (response.status === 200) {
        const { access_token, user } = response.data;

        // Store token
        localStorage.setItem('token', access_token);

        // Update auth store
        login(user);

        // Navigate based on role
        if (user.role === 'admin') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
      }
    } catch (error: any) {
      if (error.response?.status === 401) {
        setError('Invalid email or password');
      } else if (error.response?.status === 403) {
        // Check if it's specifically email not verified
        const detail = error.response?.data?.detail;
        if (
          detail &&
          typeof detail === 'object' &&
          detail.error === 'email_not_verified'
        ) {
          // Open verification modal with the email
          setVerificationEmail(detail.email || email);
          setShowVerification(true);
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
    setShowRegistration(false);
    // User is already logged in after verification, navigate to dashboard
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
              Access your personalized content creation platform
            </p>
          </div>

          {error && (
            <div className='p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
              <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
              <p className='text-sm text-red-600'>{error}</p>
            </div>
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
                  onClick={() => setShowPasswordReset(true)}
                  className='font-medium text-purple-600 hover:text-purple-500'
                >
                  Forgot your password?
                </button>
              </div>
            </div>

            <div>
              <button
                type='submit'
                disabled={isLoading}
                className='group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:bg-purple-400 disabled:cursor-not-allowed'
              >
                {isLoading ? (
                  <>
                    <Loader2 className='w-4 h-4 mr-2 animate-spin' />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </button>
            </div>

            <div className='text-center'>
              <span className='text-sm text-gray-600'>
                Don&apos;t have an account?{' '}
                <button
                  type='button'
                  onClick={() => setShowRegistration(true)}
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
        isOpen={showRegistration}
        onClose={() => setShowRegistration(false)}
        onSuccess={handleRegistrationSuccess}
      />

      {/* Password Reset Flow */}
      {showPasswordReset && (
        <PasswordResetFlow
          onClose={() => setShowPasswordReset(false)}
          onSuccess={() => {
            setShowPasswordReset(false);
            setError('');
          }}
        />
      )}

      {/* Verification Modal */}
      {showVerification && (
        <VerificationModal
          email={verificationEmail}
          onClose={() => setShowVerification(false)}
          onSuccess={() => {
            setShowVerification(false);
            // Try to login again after verification
            handleSubmit({ preventDefault: () => {} } as any);
          }}
        />
      )}
    </>
  );
};

export default Login;
