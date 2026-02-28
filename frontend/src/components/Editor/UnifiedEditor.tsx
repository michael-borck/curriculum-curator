import React from 'react';
import RichTextEditor from './RichTextEditor';

interface UnifiedEditorProps {
  content: string;
  onChange: (content: string) => void;
  onJsonChange?: ((json: Record<string, unknown>) => void) | undefined;
  contentId?: string | undefined;
  pedagogyHints?: string[] | undefined;
}

const UnifiedEditor: React.FC<UnifiedEditorProps> = ({
  content,
  onChange,
  onJsonChange,
  pedagogyHints,
}) => {
  return (
    <RichTextEditor
      content={content}
      onChange={onChange}
      onJsonChange={onJsonChange}
      pedagogyHints={pedagogyHints}
    />
  );
};

export default UnifiedEditor;
