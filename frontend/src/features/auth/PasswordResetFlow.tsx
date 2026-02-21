import { useState } from 'react';
import { ArrowLeft, Mail, KeyRound, CheckCircle } from 'lucide-react';
import api from '../../services/api';
import { Modal, Alert, Button, FormInput } from '../../components/ui';

interface PasswordResetFlowProps {
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 'request' | 'reset' | 'complete';

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
      const response = await api.post('/auth/forgot-password', {
        email,
      });
      if (response.status === 200) {
        setCurrentStep('reset');
      }
    } catch (err: unknown) {
      const error = err as {
        response?: { status?: number; data?: { detail?: string } };
      };
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
      const response = await api.post('/auth/reset-password', {
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
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
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
                <Alert variant='error' onDismiss={() => setError('')}>
                  {error}
                </Alert>
              )}

              <FormInput
                label='Email Address'
                type='email'
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder='john@example.com'
                required
                disabled={isLoading}
              />

              <Button type='submit' loading={isLoading} className='w-full'>
                Send Reset Code
              </Button>
            </form>
          </>
        );

      case 'reset':
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
              <div className='mx-auto w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4'>
                <KeyRound className='w-6 h-6 text-purple-600' />
              </div>
              <h2 className='text-2xl font-semibold text-gray-900 mb-2'>
                Set New Password
              </h2>
              <p className='text-gray-600'>
                Enter the 6-digit code sent to {email} and choose a new
                password.
              </p>
            </div>

            <form onSubmit={handleResetPassword} className='space-y-4'>
              {error && (
                <Alert variant='error' onDismiss={() => setError('')}>
                  {error}
                </Alert>
              )}

              <FormInput
                label='Reset Code'
                type='text'
                value={code}
                onChange={e =>
                  setCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                }
                className='text-center text-lg font-semibold'
                placeholder='000000'
                required
                disabled={isLoading}
                maxLength={6}
              />

              <FormInput
                label='New Password'
                type='password'
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                placeholder='••••••••'
                hint='At least 8 characters with uppercase, lowercase, and number'
                required
                disabled={isLoading}
              />

              <FormInput
                label='Confirm Password'
                type='password'
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder='••••••••'
                required
                disabled={isLoading}
              />

              <Button
                type='submit'
                loading={isLoading}
                disabled={code.length !== 6}
                className='w-full'
              >
                Reset Password
              </Button>
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
    <Modal isOpen={true} onClose={onClose} title='Password Reset'>
      {renderStep()}
    </Modal>
  );
};

export default PasswordResetFlow;
