import React, { useState, useEffect } from 'react';
import RichTextEditor from './RichTextEditor';
import QuartoEditor from './QuartoEditor';
import EditorModeToggle, { type EditorMode } from './EditorModeToggle';

const STORAGE_KEY = 'editor-mode-preference';

interface UnifiedEditorProps {
  content: string;
  onChange: (content: string) => void;
  contentId?: string | undefined;
  pedagogyHints?: string[] | undefined;
}

const UnifiedEditor: React.FC<UnifiedEditorProps> = ({
  content,
  onChange,
  contentId,
  pedagogyHints,
}) => {
  const [mode, setMode] = useState<EditorMode>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === 'advanced' ? 'advanced' : 'simple';
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  return (
    <div>
      <div className='flex items-center justify-between mb-3'>
        <EditorModeToggle mode={mode} onChange={setMode} />
        {mode === 'advanced' && (
          <span className='text-xs text-gray-500'>
            Quarto / YAML front matter enabled
          </span>
        )}
      </div>

      {mode === 'simple' ? (
        <RichTextEditor
          content={content}
          onChange={onChange}
          pedagogyHints={pedagogyHints}
        />
      ) : (
        <QuartoEditor
          contentId={contentId}
          content={content}
          onChange={onChange}
        />
      )}
    </div>
  );
};

export default UnifiedEditor;
