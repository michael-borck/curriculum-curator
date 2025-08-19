import { useState } from 'react';
import { AlertCircle, Key, Shield, Clock, Info } from 'lucide-react';

interface AlternativeVerificationProps {
  email: string;
  onClose?: () => void;
}

const AlternativeVerification = ({
  email,
  onClose,
}: AlternativeVerificationProps) => {
  const [showCodes, setShowCodes] = useState(false);

  // Generate codes client-side for display (not secure, just for UX)
  const generateDisplayCode = () => {
    const today = new Date().toISOString().split('T')[0];
    const hash = email.toLowerCase() + today;
    return hash
      .split('')
      .reduce((acc, char) => ((acc << 5) - acc + char.charCodeAt(0)) | 0, 0)
      .toString(16)
      .toUpperCase()
      .slice(-8);
  };

  const isUniversityEmail = email.toLowerCase().includes('curtin.edu.au');

  return (
    <div className='bg-white rounded-lg p-6 max-w-2xl mx-auto'>
      <div className='flex items-center gap-3 mb-4'>
        <Shield className='h-6 w-6 text-purple-600' />
        <h2 className='text-xl font-semibold text-gray-900'>
          Verification Options
        </h2>
      </div>

      {isUniversityEmail ? (
        <div className='bg-green-50 border border-green-200 rounded-lg p-4 mb-4'>
          <div className='flex items-start gap-2'>
            <Info className='h-5 w-5 text-green-600 mt-0.5' />
            <div>
              <p className='text-green-800 font-medium'>
                University Email Detected
              </p>
              <p className='text-green-700 text-sm mt-1'>
                Your @curtin.edu.au email is automatically verified! You can log
                in immediately without a verification code.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className='mb-6'>
            <p className='text-gray-600 mb-4'>
              Due to email restrictions, we offer alternative verification
              methods:
            </p>

            <div className='space-y-3'>
              {/* Method 1: Development Code */}
              <div className='border border-gray-200 rounded-lg p-4'>
                <div className='flex items-start gap-3'>
                  <div className='bg-blue-100 rounded-full p-2'>
                    <Key className='h-4 w-4 text-blue-600' />
                  </div>
                  <div className='flex-1'>
                    <h3 className='font-medium text-gray-900'>
                      Quick Verification
                    </h3>
                    <p className='text-sm text-gray-600 mt-1'>
                      For .edu.au emails, use this code:
                    </p>
                    <div className='mt-2 bg-gray-100 rounded px-3 py-2 font-mono text-lg text-center'>
                      DEV123
                    </div>
                  </div>
                </div>
              </div>

              {/* Method 2: Admin Code */}
              <div className='border border-gray-200 rounded-lg p-4'>
                <div className='flex items-start gap-3'>
                  <div className='bg-purple-100 rounded-full p-2'>
                    <Shield className='h-4 w-4 text-purple-600' />
                  </div>
                  <div className='flex-1'>
                    <h3 className='font-medium text-gray-900'>
                      Admin Verification
                    </h3>
                    <p className='text-sm text-gray-600 mt-1'>
                      Contact your administrator for a verification code
                    </p>
                    <button
                      onClick={() => setShowCodes(!showCodes)}
                      className='mt-2 text-sm text-purple-600 hover:text-purple-700 font-medium'
                    >
                      {showCodes ? 'Hide' : 'Show'} admin instructions
                    </button>

                    {showCodes && (
                      <div className='mt-3 p-3 bg-purple-50 rounded-lg text-sm'>
                        <p className='font-medium text-purple-900 mb-2'>
                          For Administrators:
                        </p>
                        <ol className='list-decimal list-inside space-y-1 text-purple-800'>
                          <li>
                            Run:{' '}
                            <code className='bg-white px-1 rounded'>
                              ./generate_verification_codes.py {email}
                            </code>
                          </li>
                          <li>Share the generated code with the user</li>
                          <li>Code is valid for 24 hours</li>
                        </ol>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Method 3: Manual Approval */}
              <div className='border border-gray-200 rounded-lg p-4'>
                <div className='flex items-start gap-3'>
                  <div className='bg-orange-100 rounded-full p-2'>
                    <Clock className='h-4 w-4 text-orange-600' />
                  </div>
                  <div className='flex-1'>
                    <h3 className='font-medium text-gray-900'>
                      Manual Approval
                    </h3>
                    <p className='text-sm text-gray-600 mt-1'>
                      Email your administrator with your registration details:
                    </p>
                    <div className='mt-2 p-2 bg-gray-50 rounded text-sm'>
                      <p className='text-gray-700'>
                        Email: <span className='font-mono'>{email}</span>
                      </p>
                      <p className='text-gray-700'>
                        Registration Date: {new Date().toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
            <div className='flex items-start gap-2'>
              <AlertCircle className='h-5 w-5 text-amber-600 mt-0.5' />
              <div>
                <p className='text-amber-800 font-medium'>
                  Email Delivery Issues
                </p>
                <p className='text-amber-700 text-sm mt-1'>
                  University email systems may block verification emails from
                  external services. Please use one of the alternative methods
                  above.
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {onClose && (
        <div className='mt-6 flex justify-end'>
          <button
            onClick={onClose}
            className='px-4 py-2 text-gray-700 hover:text-gray-900 font-medium'
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
};

export default AlternativeVerification;
