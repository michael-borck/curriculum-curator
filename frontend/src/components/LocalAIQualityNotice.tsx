import React from 'react';
import { Info, Cloud, Shield } from 'lucide-react';

interface LocalAIQualityNoticeProps {
  variant: 'detailed' | 'compact';
}

const LocalAIQualityNotice: React.FC<LocalAIQualityNoticeProps> = ({
  variant,
}) => {
  if (variant === 'compact') {
    return (
      <div className='bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2'>
        <Info className='w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0' />
        <p className='text-sm text-blue-800'>
          Local models are private and free but may produce lower-quality output
          than cloud APIs. Add an API key in Settings for best results.
        </p>
      </div>
    );
  }

  return (
    <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
      <div className='flex items-center gap-2 mb-3'>
        <Info className='w-4 h-4 text-blue-600' />
        <span className='text-sm font-medium text-blue-800'>
          Local AI vs Cloud API
        </span>
      </div>
      <div className='grid grid-cols-2 gap-4'>
        <div className='space-y-1.5'>
          <div className='flex items-center gap-1.5 text-sm font-medium text-gray-800'>
            <Shield className='w-3.5 h-3.5 text-purple-600' />
            Local AI
          </div>
          <ul className='text-xs text-gray-600 space-y-0.5 ml-5 list-disc'>
            <li>Private &mdash; data stays on your machine</li>
            <li>Free to use, no API key needed</li>
            <li>Works offline</li>
            <li>Lower precision with small models</li>
          </ul>
        </div>
        <div className='space-y-1.5'>
          <div className='flex items-center gap-1.5 text-sm font-medium text-gray-800'>
            <Cloud className='w-3.5 h-3.5 text-blue-600' />
            Cloud API
          </div>
          <ul className='text-xs text-gray-600 space-y-0.5 ml-5 list-disc'>
            <li>Highest quality output</li>
            <li>Fastest response times</li>
            <li>Requires API key</li>
            <li>Pay-per-use pricing</li>
          </ul>
        </div>
      </div>
      <p className='text-xs text-blue-700 mt-3'>
        You can add a cloud API key later in Settings for higher-quality
        generation.
      </p>
    </div>
  );
};

export default LocalAIQualityNotice;
