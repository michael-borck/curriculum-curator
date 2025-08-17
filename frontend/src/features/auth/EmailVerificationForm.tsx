import { useState, useRef, useEffect } from 'react';
import {
  ArrowLeft,
  Loader2,
  CheckCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import api from '../../services/api';

interface EmailVerificationFormProps {
  email: string;
  onSuccess: () => void;
  onBack?: () => void;
}

const EmailVerificationForm = ({
  email,
  onSuccess,
  onBack,
}: EmailVerificationFormProps) => {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const login = useAuthStore(state => state.login);

  useEffect(() => {
    // Focus first input on mount
    inputRefs.current[0]?.focus();
  }, []);

  useEffect(() => {
    // Resend cooldown timer
    if (resendCooldown > 0) {
      const timer = window.setTimeout(
        () => setResendCooldown(resendCooldown - 1),
        1000
      );
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [resendCooldown]);

  const handleCodeChange = (index: number, value: string) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    setError(''); // Clear error when typing

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all digits entered
    if (newCode.every(digit => digit) && index === 5) {
      handleVerify(newCode.join(''));
    }
  };

  const handleKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    // Handle backspace
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }

    // Handle arrow keys
    if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text');
    const digits = pastedData.replace(/\D/g, '').slice(0, 6).split('');

    const newCode = [...code];
    digits.forEach((digit, index) => {
      if (index < 6) {
        newCode[index] = digit;
      }
    });
    setCode(newCode);

    // Focus last filled input or last input
    const lastIndex = Math.min(digits.length - 1, 5);
    inputRefs.current[lastIndex]?.focus();

    // Auto-submit if 6 digits pasted
    if (digits.length === 6) {
      handleVerify(digits.join(''));
    }
  };

  const handleVerify = async (verificationCode?: string) => {
    const codeToVerify = verificationCode || code.join('');

    if (codeToVerify.length !== 6) {
      setError('Please enter all 6 digits');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await api.post('/api/auth/verify-email', {
        email,
        code: codeToVerify,
      });

      if (response.status === 200) {
        setSuccessMessage('Email verified successfully!');

        // Store token and user data
        const { access_token, user } = response.data;
        localStorage.setItem('token', access_token);
        login(user);

        // Call success callback after a short delay
        window.setTimeout(() => {
          onSuccess();
        }, 1500);
      }
    } catch (error: any) {
      if (error.response?.status === 400) {
        setError('Invalid or expired verification code');
      } else if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Verification failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsResending(true);
    setError('');
    setSuccessMessage('');

    try {
      const response = await api.post('/api/auth/resend-verification', {
        email,
      });

      if (response.status === 200) {
        setSuccessMessage('Verification code sent! Check your email.');
        setResendCooldown(60); // 60 second cooldown
        setCode(['', '', '', '', '', '']); // Clear code
        inputRefs.current[0]?.focus();
      }
    } catch {
      setError('Failed to resend code. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className='w-full'>
      {onBack && (
        <button
          onClick={onBack}
          className='flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-4 transition-colors'
        >
          <ArrowLeft className='w-4 h-4' />
          Back to registration
        </button>
      )}

      <div className='text-center mb-6'>
        <h2 className='text-2xl font-semibold text-gray-900 mb-2'>
          Verify Your Email
        </h2>
        <p className='text-gray-600'>
          We&apos;ve sent a 6-digit code to
          <br />
          <span className='font-medium text-gray-900'>{email}</span>
        </p>
      </div>

      {error && (
        <div className='mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
          <p className='text-sm text-red-600'>{error}</p>
        </div>
      )}

      {successMessage && (
        <div className='mb-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-start gap-2'>
          <CheckCircle className='w-5 h-5 text-green-600 flex-shrink-0 mt-0.5' />
          <p className='text-sm text-green-600'>{successMessage}</p>
        </div>
      )}

      <div className='mb-6'>
        <div className='block text-sm font-medium text-gray-700 mb-3'>
          Enter verification code
        </div>
        <div className='flex gap-2 justify-center'>
          {code.map((digit, index) => (
            <input
              key={index}
              ref={el => (inputRefs.current[index] = el)}
              type='text'
              inputMode='numeric'
              pattern='\d*'
              maxLength={1}
              value={digit}
              onChange={e => handleCodeChange(index, e.target.value)}
              onKeyDown={e => handleKeyDown(index, e)}
              onPaste={handlePaste}
              className={`w-12 h-12 text-center text-lg font-semibold border-2 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors ${
                error ? 'border-red-300' : 'border-gray-300'
              }`}
              disabled={isLoading || !!successMessage}
            />
          ))}
        </div>
      </div>

      <button
        onClick={() => handleVerify()}
        disabled={isLoading || !code.every(digit => digit) || !!successMessage}
        className='w-full mb-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors disabled:bg-purple-400 disabled:cursor-not-allowed flex items-center justify-center gap-2'
      >
        {isLoading ? (
          <>
            <Loader2 className='w-4 h-4 animate-spin' />
            Verifying...
          </>
        ) : successMessage ? (
          <>
            <CheckCircle className='w-4 h-4' />
            Verified!
          </>
        ) : (
          'Verify Email'
        )}
      </button>

      <div className='text-center'>
        <p className='text-sm text-gray-600 mb-2'>
          Didn&apos;t receive the code?
        </p>
        <button
          onClick={handleResend}
          disabled={isResending || resendCooldown > 0}
          className='text-purple-600 hover:text-purple-700 font-medium text-sm inline-flex items-center gap-1 transition-colors disabled:text-gray-400 disabled:cursor-not-allowed'
        >
          {isResending ? (
            <>
              <Loader2 className='w-4 h-4 animate-spin' />
              Sending...
            </>
          ) : resendCooldown > 0 ? (
            `Resend in ${resendCooldown}s`
          ) : (
            <>
              <RefreshCw className='w-4 h-4' />
              Resend code
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default EmailVerificationForm;
