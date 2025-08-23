import { useState } from 'react';
import {
  ArrowLeft,
  Loader2,
  CheckCircle,
  AlertCircle,
  Mail,
  KeyRound,
} from 'lucide-react';
import api from '../../services/api';

interface PasswordResetFlowProps {
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 'request' | 'verify' | 'reset' | 'complete';

const PasswordResetFlow = ({ onClose, onSuccess }: PasswordResetFlowProps) => {
  const [currentStep, setCurrentStep] = useState<Step>('request');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await api.post('/api/auth/request-password-reset', {
        email,
      });
      if (response.status === 200) {
        setCurrentStep('verify');
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        setError('Email not found');
      } else if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Failed to send reset code. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await api.post('/api/auth/verify-reset-code', {
        email,
        code,
      });
      if (response.status === 200) {
        setCurrentStep('reset');
      }
    } catch (error: any) {
      if (error.response?.status === 400) {
        setError('Invalid or expired code');
      } else if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Verification failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate passwords
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (
      !/(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{}|;:,.<>?])/.test(
        newPassword
      )
    ) {
      setError(
        'Password must contain uppercase, lowercase, number, and special character'
      );
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      const response = await api.post('/api/auth/reset-password', {
        email,
        code,
        new_password: newPassword,
      });
      if (response.status === 200) {
        setCurrentStep('complete');
        window.setTimeout(() => {
          onSuccess();
        }, 2000);
      }
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Password reset failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'request':
        return (
          <>
            <div className='text-center mb-6'>
              <div className='mx-auto w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4'>
                <Mail className='w-6 h-6 text-purple-600' />
              </div>
              <h2 className='text-2xl font-semibold text-gray-900 mb-2'>
                Reset Password
              </h2>
              <p className='text-gray-600'>
                Enter your email address and we&apos;ll send you a code to reset
                your password.
              </p>
            </div>

            <form onSubmit={handleRequestReset} className='space-y-4'>
              {error && (
                <div className='p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
                  <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
                  <p className='text-sm text-red-600'>{error}</p>
                </div>
              )}

              <div>
                <label
                  htmlFor='email'
                  className='block text-sm font-medium text-gray-700 mb-1'
                >
                  Email Address
                </label>
                <input
                  type='email'
                  id='email'
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
                  placeholder='john@example.com'
                  required
                  disabled={isLoading}
                />
              </div>

              <button
                type='submit'
                disabled={isLoading}
                className='w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors disabled:bg-purple-400 disabled:cursor-not-allowed flex items-center justify-center gap-2'
              >
                {isLoading ? (
                  <>
                    <Loader2 className='w-4 h-4 animate-spin' />
                    Sending Code...
                  </>
                ) : (
                  'Send Reset Code'
                )}
              </button>
            </form>
          </>
        );

      case 'verify':
        return (
          <>
            <button
              onClick={() => setCurrentStep('request')}
              className='flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-4 transition-colors'
            >
              <ArrowLeft className='w-4 h-4' />
              Back
            </button>

            <div className='text-center mb-6'>
              <h2 className='text-2xl font-semibold text-gray-900 mb-2'>
                Enter Reset Code
              </h2>
              <p className='text-gray-600'>
                We&apos;ve sent a 6-digit code to {email}
              </p>
            </div>

            <form onSubmit={handleVerifyCode} className='space-y-4'>
              {error && (
                <div className='p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
                  <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
                  <p className='text-sm text-red-600'>{error}</p>
                </div>
              )}

              <div>
                <label
                  htmlFor='code'
                  className='block text-sm font-medium text-gray-700 mb-1'
                >
                  Verification Code
                </label>
                <input
                  type='text'
                  id='code'
                  value={code}
                  onChange={e =>
                    setCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                  }
                  className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 text-center text-lg font-semibold'
                  placeholder='000000'
                  required
                  disabled={isLoading}
                  maxLength={6}
                />
              </div>

              <button
                type='submit'
                disabled={isLoading || code.length !== 6}
                className='w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors disabled:bg-purple-400 disabled:cursor-not-allowed flex items-center justify-center gap-2'
              >
                {isLoading ? (
                  <>
                    <Loader2 className='w-4 h-4 animate-spin' />
                    Verifying...
                  </>
                ) : (
                  'Verify Code'
                )}
              </button>
            </form>
          </>
        );

      case 'reset':
        return (
          <>
            <div className='text-center mb-6'>
              <div className='mx-auto w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4'>
                <KeyRound className='w-6 h-6 text-purple-600' />
              </div>
              <h2 className='text-2xl font-semibold text-gray-900 mb-2'>
                Set New Password
              </h2>
              <p className='text-gray-600'>
                Choose a strong password for your account
              </p>
            </div>

            <form onSubmit={handleResetPassword} className='space-y-4'>
              {error && (
                <div className='p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
                  <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
                  <p className='text-sm text-red-600'>{error}</p>
                </div>
              )}

              <div>
                <label
                  htmlFor='newPassword'
                  className='block text-sm font-medium text-gray-700 mb-1'
                >
                  New Password
                </label>
                <input
                  type='password'
                  id='newPassword'
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
                  placeholder='••••••••'
                  required
                  disabled={isLoading}
                />
                <p className='mt-1 text-xs text-gray-500'>
                  At least 8 characters with uppercase, lowercase, and number
                </p>
              </div>

              <div>
                <label
                  htmlFor='confirmPassword'
                  className='block text-sm font-medium text-gray-700 mb-1'
                >
                  Confirm Password
                </label>
                <input
                  type='password'
                  id='confirmPassword'
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
                  placeholder='••••••••'
                  required
                  disabled={isLoading}
                />
              </div>

              <button
                type='submit'
                disabled={isLoading}
                className='w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors disabled:bg-purple-400 disabled:cursor-not-allowed flex items-center justify-center gap-2'
              >
                {isLoading ? (
                  <>
                    <Loader2 className='w-4 h-4 animate-spin' />
                    Resetting Password...
                  </>
                ) : (
                  'Reset Password'
                )}
              </button>
            </form>
          </>
        );

      case 'complete':
        return (
          <div className='text-center py-8'>
            <div className='mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4'>
              <CheckCircle className='w-8 h-8 text-green-600' />
            </div>
            <h2 className='text-2xl font-semibold text-gray-900 mb-2'>
              Password Reset Complete!
            </h2>
            <p className='text-gray-600'>
              Your password has been successfully reset. You can now log in with
              your new password.
            </p>
          </div>
        );
    }
  };

  return (
    <div className='fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-md w-full mx-4'>
        <div className='flex justify-between items-center p-6 border-b'>
          <h3 className='text-lg font-medium text-gray-900'>Password Reset</h3>
          <button
            onClick={onClose}
            className='text-gray-400 hover:text-gray-500 transition-colors'
          >
            <span className='sr-only'>Close</span>
            <svg
              className='w-6 h-6'
              fill='none'
              viewBox='0 0 24 24'
              stroke='currentColor'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M6 18L18 6M6 6l12 12'
              />
            </svg>
          </button>
        </div>

        <div className='p-6'>{renderStep()}</div>
      </div>
    </div>
  );
};

export default PasswordResetFlow;
