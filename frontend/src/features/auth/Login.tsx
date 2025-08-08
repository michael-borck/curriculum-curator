import { useState } from 'react';
import { ArrowLeft, GraduationCap } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import type { LoginProps, HandleSubmitFunction } from '../../types/index';

const Login = ({ onBackToLanding }: LoginProps) => {
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('test');
  const login = useAuthStore(state => state.login);

  const handleSubmit: HandleSubmitFunction = e => {
    e.preventDefault();
    // Mock login - replace with real API call
    login({ email, name: 'Test User', role: 'lecturer' });
  };

  return (
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
              />
            </div>
          </div>
          <div>
            <button
              type='submit'
              className='group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500'
            >
              Sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
