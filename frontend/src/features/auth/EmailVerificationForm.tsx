import { useState, useRef, useEffect } from 'react';
import { setStoredToken } from '../../services/authSession';
import { ArrowLeft, RefreshCw, CheckCircle } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import api from '../../services/api';
import { Alert, Button } from '../../components/ui';

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
    inputRefs.current[0]?.focus();
  }, []);

  useEffect(() => {
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
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    setError('');

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (newCode.every(digit => digit) && index === 5) {
      handleVerify(newCode.join(''));
    }
  };

  const handleKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
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

    const lastIndex = Math.min(digits.length - 1, 5);
    inputRefs.current[lastIndex]?.focus();

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
      const response = await api.post('/auth/verify-email', {
        email,
        code: codeToVerify,
      });

      if (response.status === 200) {
        setSuccessMessage('Email verified successfully!');

        const { access_token, user } = response.data;
        setStoredToken(access_token);
        login(user);

        window.setTimeout(() => {
          onSuccess();
        }, 1500);
      }
    } catch (err: unknown) {
      const error = err as {
        response?: { status?: number; data?: { detail?: string } };
      };
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
      const response = await api.post('/auth/resend-verification', { email });

      if (response.status === 200) {
        setSuccessMessage('Verification code sent! Check your email.');
        setResendCooldown(60);
        setCode(['', '', '', '', '', '']);
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
        <Alert variant='error' onDismiss={() => setError('')} className='mb-4'>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert variant='success' className='mb-4'>
          {successMessage}
        </Alert>
      )}

      <div className='mb-6'>
        <div className='block text-sm font-medium text-gray-700 mb-3'>
          Enter verification code
        </div>
        <div className='flex gap-2 justify-center'>
          {code.map((digit, index) => (
            <input
              key={index}
              ref={el => {
                inputRefs.current[index] = el;
              }}
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

      <Button
        onClick={() => handleVerify()}
        loading={isLoading}
        disabled={!code.every(digit => digit) || !!successMessage}
        className='w-full mb-4'
      >
        {successMessage ? (
          <>
            <CheckCircle className='w-4 h-4 mr-2' />
            Verified!
          </>
        ) : (
          'Verify Email'
        )}
      </Button>

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
            'Sending...'
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
