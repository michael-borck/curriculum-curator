import React from 'react';
import { Star } from 'lucide-react';

interface StarRatingProps {
  rating: number; // 0-5, supports half stars
  size?: 'sm' | 'md' | 'lg';
  showValue?: boolean;
  tooltipContent?: string;
  onClick?: () => void;
  className?: string;
}

const sizeMap = {
  sm: 'w-3.5 h-3.5',
  md: 'w-5 h-5',
  lg: 'w-7 h-7',
};

const textSizeMap = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
};

const StarRating: React.FC<StarRatingProps> = ({
  rating,
  size = 'md',
  showValue = false,
  tooltipContent,
  onClick,
  className = '',
}) => {
  const stars = [];
  const clampedRating = Math.max(0, Math.min(5, rating));

  for (let i = 1; i <= 5; i++) {
    const filled = clampedRating >= i;
    const halfFilled = !filled && clampedRating >= i - 0.5;

    stars.push(
      <span key={i} className='relative inline-block'>
        {/* Background (empty) star */}
        <Star className={`${sizeMap[size]} text-gray-200`} />
        {/* Filled or half-filled overlay */}
        {(filled || halfFilled) && (
          <span
            className='absolute inset-0 overflow-hidden'
            style={halfFilled ? { width: '50%' } : undefined}
          >
            <Star
              className={`${sizeMap[size]} text-amber-400 fill-amber-400`}
            />
          </span>
        )}
      </span>
    );
  }

  return (
    <div
      className={`inline-flex items-center gap-0.5 ${onClick ? 'cursor-pointer hover:opacity-80' : ''} ${className}`}
      onClick={onClick}
      title={tooltipContent}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e: React.KeyboardEvent) => {
              if (e.key === 'Enter' || e.key === ' ') onClick();
            }
          : undefined
      }
    >
      {stars}
      {showValue && (
        <span className={`ml-1 font-medium text-gray-600 ${textSizeMap[size]}`}>
          {clampedRating.toFixed(1)}
        </span>
      )}
    </div>
  );
};

export default StarRating;
