import React from 'react';
import RichTextEditor from './RichTextEditor';

interface UnifiedEditorProps {
  content: string | Record<string, unknown>;
  onChange: (content: string) => void;
  onJsonChange?: ((json: Record<string, unknown>) => void) | undefined;
  contentId?: string | undefined;
  pedagogyHints?: string[] | undefined;
  unitId?: string | undefined;
  materialId?: string | undefined;
}

const UnifiedEditor: React.FC<UnifiedEditorProps> = ({
  content,
  onChange,
  onJsonChange,
  pedagogyHints,
  unitId,
  materialId,
}) => {
  return (
    <RichTextEditor
      content={content}
      onChange={onChange}
      onJsonChange={onJsonChange}
      pedagogyHints={pedagogyHints}
      unitId={unitId}
      materialId={materialId}
    />
  );
};

export default UnifiedEditor;
