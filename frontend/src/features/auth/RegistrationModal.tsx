import { useState } from 'react';
import { X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { register } from '../../services/api';
import EmailVerificationForm from './EmailVerificationForm';

interface RegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

interface FormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

const RegistrationModal = ({
  isOpen,
  onClose,
  onSuccess,
}: RegistrationModalProps) => {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRegistered, setIsRegistered] = useState(false);
  const [showVerification, setShowVerification] = useState(false);
  const [isFirstUser, setIsFirstUser] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');

  if (!isOpen) return null;

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[A-Z])(?=.*[a-z])(?=.*\d)/.test(formData.password)) {
      newErrors.password =
        'Password must contain uppercase, lowercase, and number';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    setErrors({});

    try {
      const response = await register(
        formData.email,
        formData.password,
        formData.name
      );

      setIsRegistered(true);
      setRegisteredEmail(formData.email);

      // Check if this was the first user (admin)
      if (
        response.data?.message?.includes('first user') ||
        response.data?.message?.includes('admin privileges')
      ) {
        setIsFirstUser(true);
        // First user doesn't need verification, they can login immediately
        window.setTimeout(() => {
          onSuccess?.();
          onClose();
        }, 2000); // Show success message for 2 seconds
      } else {
        // Regular user needs verification
        window.setTimeout(() => {
          setShowVerification(true);
        }, 2000); // Show success message for 2 seconds before verification
      }
    } catch (error: any) {
      if (error.response?.status === 409) {
        setErrors({ email: 'Email already registered' });
      } else if (error.response?.status === 403) {
        setErrors({
          general:
            'This email domain is not currently authorized for registration. Please contact your system administrator to request access.',
        });
      } else if (error.response?.data?.detail) {
        setErrors({ general: error.response.data.detail });
      } else {
        setErrors({ general: 'Registration failed. Please try again.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleVerificationSuccess = () => {
    onSuccess?.();
    onClose();
  };

  const handleStartOver = () => {
    setFormData({
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    });
    setErrors({});
    setIsRegistered(false);
    setIsFirstUser(false);
    setShowVerification(false);
    setRegisteredEmail('');
  };

  if (showVerification) {
    return (
      <div className='fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50'>
        <div className='bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6'>
          <EmailVerificationForm
            email={registeredEmail}
            onSuccess={handleVerificationSuccess}
            onBack={handleStartOver}
          />
        </div>
      </div>
    );
  }

  return (
    <div className='fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-md w-full mx-4'>
        <div className='flex justify-between items-center p-6 border-b'>
          <h2 className='text-2xl font-semibold text-gray-900'>
            Create Account
          </h2>
          <button
            onClick={onClose}
            className='text-gray-400 hover:text-gray-500 transition-colors'
          >
            <X className='w-6 h-6' />
          </button>
        </div>

        <form onSubmit={handleSubmit} className='p-6 space-y-4'>
          {errors.general && (
            <div className='p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
              <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
              <p className='text-sm text-red-600'>{errors.general}</p>
            </div>
          )}

          {isRegistered && !isFirstUser && (
            <div className='p-3 bg-green-50 border border-green-200 rounded-md flex items-start gap-2'>
              <CheckCircle className='w-5 h-5 text-green-600 flex-shrink-0 mt-0.5' />
              <p className='text-sm text-green-600'>
                Registration successful! Please check your email for the
                verification code.
              </p>
            </div>
          )}

          {isRegistered && isFirstUser && (
            <div className='p-3 bg-blue-50 border border-blue-200 rounded-md flex items-start gap-2'>
              <CheckCircle className='w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5' />
              <div className='text-sm text-blue-600'>
                <p className='font-semibold'>Welcome, Administrator!</p>
                <p>
                  You are the first user and have been granted admin privileges.
                </p>
                <p>You can now login without email verification.</p>
              </div>
            </div>
          )}

          <div>
            <label
              htmlFor='name'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Full Name
            </label>
            <input
              type='text'
              id='name'
              name='name'
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500 ${
                errors.name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder='John Doe'
              disabled={isLoading || isRegistered}
            />
            {errors.name && (
              <p className='mt-1 text-sm text-red-600'>{errors.name}</p>
            )}
          </div>

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
              name='email'
              value={formData.email}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500 ${
                errors.email ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder='john@example.com'
              disabled={isLoading || isRegistered}
            />
            {errors.email && (
              <p className='mt-1 text-sm text-red-600'>{errors.email}</p>
            )}
          </div>

          <div>
            <label
              htmlFor='password'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Password
            </label>
            <input
              type='password'
              id='password'
              name='password'
              value={formData.password}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500 ${
                errors.password ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder='••••••••'
              disabled={isLoading || isRegistered}
            />
            {errors.password && (
              <p className='mt-1 text-sm text-red-600'>{errors.password}</p>
            )}
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
              name='confirmPassword'
              value={formData.confirmPassword}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500 ${
                errors.confirmPassword ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder='••••••••'
              disabled={isLoading || isRegistered}
            />
            {errors.confirmPassword && (
              <p className='mt-1 text-sm text-red-600'>
                {errors.confirmPassword}
              </p>
            )}
          </div>

          <div className='flex gap-3 pt-4'>
            {isRegistered && !isFirstUser ? (
              <>
                <button
                  type='button'
                  onClick={handleStartOver}
                  className='flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors'
                >
                  Start Over
                </button>
                <button
                  type='button'
                  onClick={() => setShowVerification(true)}
                  className='flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors flex items-center justify-center gap-2'
                >
                  <CheckCircle className='w-4 h-4' />
                  Enter Code
                </button>
              </>
            ) : (
              <>
                <button
                  type='button'
                  onClick={onClose}
                  className='flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors'
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  type='submit'
                  className='flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors disabled:bg-purple-400 disabled:cursor-not-allowed flex items-center justify-center gap-2'
                  disabled={isLoading || isRegistered}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className='w-4 h-4 animate-spin' />
                      Creating Account...
                    </>
                  ) : (
                    'Create Account'
                  )}
                </button>
              </>
            )}
          </div>
        </form>

        <div className='px-6 pb-6'>
          <p className='text-sm text-gray-600 text-center'>
            By creating an account, you agree to our{' '}
            <button type='button' className='text-purple-600 hover:underline'>
              Terms of Service
            </button>{' '}
            and{' '}
            <button type='button' className='text-purple-600 hover:underline'>
              Privacy Policy
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegistrationModal;
