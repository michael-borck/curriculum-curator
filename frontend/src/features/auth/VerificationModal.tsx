import { X } from 'lucide-react';
import EmailVerificationForm from './EmailVerificationForm';

interface VerificationModalProps {
  email: string;
  onClose: () => void;
  onSuccess: () => void;
}

const VerificationModal = ({
  email,
  onClose,
  onSuccess,
}: VerificationModalProps) => {
  // Always show the modal, even if email is empty (user might have navigated here directly)
  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
      <div className='bg-white rounded-lg shadow-xl max-w-md w-full relative'>
        {/* Close button */}
        <button
          onClick={onClose}
          className='absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors'
          aria-label='Close'
        >
          <X className='w-5 h-5' />
        </button>

        {/* Modal content */}
        <div className='p-6'>
          <h2 className='text-2xl font-bold text-gray-900 mb-2'>
            Email Verification Required
          </h2>
          <p className='text-gray-600 mb-6'>
            Your email address needs to be verified before you can login.
            {email ? (
              <>
                We&apos;ve sent a verification code to <strong>{email}</strong>
              </>
            ) : (
              <>Please check your registered email for the verification code.</>
            )}
          </p>

          {email ? (
            <EmailVerificationForm
              email={email}
              onSuccess={onSuccess}
              onBack={onClose}
            />
          ) : (
            <div className='text-center py-4'>
              <p className='text-sm text-gray-500 mb-4'>
                Please enter your email address to continue with verification.
              </p>
              <button
                onClick={onClose}
                className='px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700'
              >
                Back to Login
              </button>
            </div>
          )}

          <div className='mt-4 pt-4 border-t border-gray-200'>
            <p className='text-sm text-gray-500 text-center'>
              Can&apos;t find the email? Check your spam folder or click &quot;Resend Code&quot; above.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerificationModal;
