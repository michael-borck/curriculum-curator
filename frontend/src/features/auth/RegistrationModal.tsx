import { useState } from 'react';
import { CheckCircle } from 'lucide-react';
import api, { register } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import EmailVerificationForm from './EmailVerificationForm';
import { Modal, Alert, Button, FormInput } from '../../components/ui';

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

const initialFormData: FormData = {
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
};

const RegistrationModal = ({
  isOpen,
  onClose,
  onSuccess,
}: RegistrationModalProps) => {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRegistered, setIsRegistered] = useState(false);
  const [showVerification, setShowVerification] = useState(false);
  const [isFirstUser, setIsFirstUser] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');
  const login = useAuthStore(state => state.login);

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
    } else if (
      !/(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{}|;:,.<>?])/.test(
        formData.password
      )
    ) {
      newErrors.password =
        'Password must contain uppercase, lowercase, number, and special character';
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
        // Auto-login the first user after a brief delay
        window.setTimeout(async () => {
          try {
            const loginResponse = await api.post('/auth/login', {
              email: formData.email,
              password: formData.password,
            });
            if (loginResponse.status === 200) {
              const { access_token, user } = loginResponse.data;
              localStorage.setItem('token', access_token);
              login(user);
            }
          } catch {
            // Login failed — user can log in manually
          }
          onSuccess?.();
          onClose();
        }, 2000);
      } else {
        window.setTimeout(() => {
          setShowVerification(true);
        }, 2000);
      }
    } catch (err: unknown) {
      const error = err as {
        response?: { status?: number; data?: { detail?: string } };
      };

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
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleVerificationSuccess = () => {
    onSuccess?.();
    onClose();
  };

  const handleStartOver = () => {
    setFormData(initialFormData);
    setErrors({});
    setIsRegistered(false);
    setIsFirstUser(false);
    setShowVerification(false);
    setRegisteredEmail('');
  };

  // Show verification form if registered
  if (showVerification) {
    return (
      <Modal isOpen={true} onClose={onClose} title='Verify Your Email'>
        <EmailVerificationForm
          email={registeredEmail}
          onSuccess={handleVerificationSuccess}
          onBack={handleStartOver}
        />
      </Modal>
    );
  }

  const isDisabled = isLoading || isRegistered;

  return (
    <Modal isOpen={true} onClose={onClose} title='Create Account' size='lg'>
      <form onSubmit={handleSubmit} className='space-y-4'>
        {errors.general && (
          <Alert
            variant='error'
            onDismiss={() => {
              // eslint-disable-next-line @typescript-eslint/no-unused-vars
              const { general: _unused, ...rest } = errors;
              setErrors(rest);
            }}
          >
            {errors.general}
          </Alert>
        )}

        {isRegistered && !isFirstUser && (
          <Alert variant='success'>
            Registration successful! Please check your email for the
            verification code.
          </Alert>
        )}

        {isRegistered && isFirstUser && (
          <Alert variant='info'>
            <div>
              <p className='font-semibold'>Welcome, Administrator!</p>
              <p>
                You are the first user and have been granted admin privileges.
              </p>
              <p>You can now login without email verification.</p>
            </div>
          </Alert>
        )}

        <FormInput
          label='Full Name'
          name='name'
          value={formData.name}
          onChange={handleChange}
          error={errors.name || ''}
          placeholder='John Doe'
          disabled={isDisabled}
          required
        />

        <FormInput
          label='Email Address'
          name='email'
          type='email'
          value={formData.email}
          onChange={handleChange}
          error={errors.email || ''}
          placeholder='john@example.com'
          disabled={isDisabled}
          required
        />

        <FormInput
          label='Password'
          name='password'
          type='password'
          value={formData.password}
          onChange={handleChange}
          error={errors.password || ''}
          placeholder='••••••••'
          hint='At least 8 characters with uppercase, lowercase, number, and special character'
          disabled={isDisabled}
          required
        />

        <FormInput
          label='Confirm Password'
          name='confirmPassword'
          type='password'
          value={formData.confirmPassword}
          onChange={handleChange}
          error={errors.confirmPassword || ''}
          placeholder='••••••••'
          disabled={isDisabled}
          required
        />

        <div className='flex gap-3 pt-4'>
          {isRegistered && !isFirstUser ? (
            <>
              <Button
                variant='secondary'
                onClick={handleStartOver}
                className='flex-1'
              >
                Start Over
              </Button>
              <Button
                onClick={() => setShowVerification(true)}
                className='flex-1'
              >
                <CheckCircle className='w-4 h-4 mr-2' />
                Enter Code
              </Button>
            </>
          ) : (
            <>
              <Button
                variant='secondary'
                onClick={onClose}
                disabled={isLoading}
                className='flex-1'
              >
                Cancel
              </Button>
              <Button
                type='submit'
                loading={isLoading}
                disabled={isRegistered}
                className='flex-1'
              >
                Create Account
              </Button>
            </>
          )}
        </div>
      </form>

      <div className='mt-6'>
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
    </Modal>
  );
};

export default RegistrationModal;
