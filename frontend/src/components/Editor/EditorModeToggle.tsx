import React from 'react';
import { FileText, Code } from 'lucide-react';

export type EditorMode = 'simple' | 'advanced';

interface EditorModeToggleProps {
  mode: EditorMode;
  onChange: (mode: EditorMode) => void;
}

const EditorModeToggle: React.FC<EditorModeToggleProps> = ({
  mode,
  onChange,
}) => (
  <div className='inline-flex rounded-lg border border-gray-200 p-0.5 bg-gray-50'>
    <button
      onClick={() => onChange('simple')}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
        mode === 'simple'
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      <FileText className='h-3.5 w-3.5' />
      Simple
    </button>
    <button
      onClick={() => onChange('advanced')}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
        mode === 'advanced'
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      <Code className='h-3.5 w-3.5' />
      Advanced
    </button>
  </div>
);

export default EditorModeToggle;
