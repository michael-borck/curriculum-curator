/**
 * AILevelBadge — small presentational component showing the current
 * AI assist level and whether a Learning Design is active.
 */

import { BookOpen } from 'lucide-react';
import { useAILevel } from '../../hooks/useAILevel';

interface AILevelBadgeProps {
  hasDesign?: boolean;
  className?: string;
}

const levelColors: Record<string, string> = {
  none: 'bg-gray-100 text-gray-600',
  refine: 'bg-yellow-100 text-yellow-700',
  create: 'bg-blue-100 text-blue-700',
};

const AILevelBadge: React.FC<AILevelBadgeProps> = ({
  hasDesign = false,
  className = '',
}) => {
  const { level } = useAILevel();

  const colorClass = levelColors[level] ?? levelColors.none;

  return (
    <div className={`flex items-center gap-1.5 ${className}`}>
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}
      >
        AI: {level}
      </span>
      {hasDesign && (
        <span className='inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700'>
          <BookOpen className='w-3 h-3' />
          Design
        </span>
      )}
    </div>
  );
};

export default AILevelBadge;
