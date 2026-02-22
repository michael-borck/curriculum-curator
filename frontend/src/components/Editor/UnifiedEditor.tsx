import React from 'react';
import RichTextEditor from './RichTextEditor';

interface UnifiedEditorProps {
  content: string;
  onChange: (content: string) => void;
  contentId?: string | undefined;
  pedagogyHints?: string[] | undefined;
}

const UnifiedEditor: React.FC<UnifiedEditorProps> = ({
  content,
  onChange,
  pedagogyHints,
}) => {
  return (
    <RichTextEditor
      content={content}
      onChange={onChange}
      pedagogyHints={pedagogyHints}
    />
  );
};

export default UnifiedEditor;
