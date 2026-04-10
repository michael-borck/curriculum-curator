import { useState } from 'react';
import { useEditor, EditorContent, Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import Image from '@tiptap/extension-image';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
import { VideoNode } from './VideoNode';
import { YoutubeNode } from './YoutubeNode';
import { MermaidNode } from './MermaidNode';
import { QuizQuestionNode } from './QuizQuestionNode';
import { SlideBreakNode } from './SlideBreakNode';
import { SpeakerNotesNode } from './SpeakerNotesNode';
import { BranchingCardNode } from './BranchingCardNode';
import { InteractiveVideoEmbedNode } from './InteractiveVideoEmbedNode';
import { TranscriptSegmentNode } from './TranscriptSegmentNode';
import { VideoInteractionNode } from './VideoInteractionNode';
import ImageInsertDialog from './ImageInsertDialog';
import BranchingMapDialog from './BranchingMapDialog';
import VisualPromptPanel from './VisualPromptPanel';
import { createLowlight } from 'lowlight';
import js from 'highlight.js/lib/languages/javascript';
import python from 'highlight.js/lib/languages/python';
import html from 'highlight.js/lib/languages/xml';
import css from 'highlight.js/lib/languages/css';
import type { RichTextEditorProps } from '../../types/index';
import { useAILevel } from '../../hooks/useAILevel';
import {
  useTeachingStyleStore,
  getPedagogyStaticGuidance,
} from '../../stores/teachingStyleStore';

// Create lowlight instance and register languages
const lowlight = createLowlight();
lowlight.register('javascript', js);
lowlight.register('python', python);
lowlight.register('html', html);
lowlight.register('css', css);
import {
  Bold,
  Italic,
  Code,
  List,
  ListOrdered,
  Heading1,
  Heading2,
  Table as TableIcon,
  ImagePlus,
  Youtube,
  Video,
  GitMerge,
  HelpCircle,
  PanelTopDashed,
  GitFork,
  Map,
  Wand2,
  Undo,
  Redo,
  Info,
} from 'lucide-react';

const MenuBar = ({
  editor,
  onImageClick,
  onVisualPromptClick,
  onMapClick,
  isAIDisabled,
}: {
  editor: Editor | null;
  onImageClick: () => void;
  onVisualPromptClick: () => void;
  onMapClick: () => void;
  isAIDisabled: boolean;
}) => {
  if (!editor) return null;

  return (
    <div className='border-b border-gray-200 p-2 flex gap-2 flex-wrap'>
      <button
        onClick={() => editor.chain().focus().toggleBold().run()}
        className={`p-2 rounded hover:bg-gray-100 ${
          editor.isActive('bold') ? 'bg-gray-200' : ''
        }`}
      >
        <Bold size={18} />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleItalic().run()}
        className={`p-2 rounded hover:bg-gray-100 ${
          editor.isActive('italic') ? 'bg-gray-200' : ''
        }`}
      >
        <Italic size={18} />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleCode().run()}
        className={`p-2 rounded hover:bg-gray-100 ${
          editor.isActive('code') ? 'bg-gray-200' : ''
        }`}
      >
        <Code size={18} />
      </button>

      <div className='w-px bg-gray-300 mx-1' />

      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        className={`p-2 rounded hover:bg-gray-100 ${
          editor.isActive('heading', { level: 1 }) ? 'bg-gray-200' : ''
        }`}
      >
        <Heading1 size={18} />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        className={`p-2 rounded hover:bg-gray-100 ${
          editor.isActive('heading', { level: 2 }) ? 'bg-gray-200' : ''
        }`}
      >
        <Heading2 size={18} />
      </button>

      <div className='w-px bg-gray-300 mx-1' />

      <button
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={`p-2 rounded hover:bg-gray-100 ${
          editor.isActive('bulletList') ? 'bg-gray-200' : ''
        }`}
      >
        <List size={18} />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={`p-2 rounded hover:bg-gray-100 ${
          editor.isActive('orderedList') ? 'bg-gray-200' : ''
        }`}
      >
        <ListOrdered size={18} />
      </button>

      <div className='w-px bg-gray-300 mx-1' />

      <button
        onClick={() =>
          editor.chain().focus().insertTable({ rows: 3, cols: 3 }).run()
        }
        className='p-2 rounded hover:bg-gray-100'
      >
        <TableIcon size={18} />
      </button>
      <button
        onClick={onImageClick}
        className='p-2 rounded hover:bg-gray-100'
        title='Insert image'
      >
        <ImagePlus size={18} />
      </button>
      <button
        onClick={() => {
          const url = window.prompt('Enter YouTube URL:');
          if (url) {
            editor.commands.setYoutubeVideo({ src: url });
          }
        }}
        className='p-2 rounded hover:bg-gray-100'
        title='Embed YouTube video'
      >
        <Youtube size={18} />
      </button>
      <button
        onClick={() => {
          const url = window.prompt('Enter video URL (MP4, WebM):');
          if (url) {
            editor.commands.setVideo({ src: url });
          }
        }}
        className='p-2 rounded hover:bg-gray-100'
        title='Embed video from URL'
      >
        <Video size={18} />
      </button>
      <button
        onClick={() => editor.commands.insertMermaid()}
        className='p-2 rounded hover:bg-gray-100'
        title='Insert Mermaid diagram'
      >
        <GitMerge size={18} />
      </button>
      <button
        onClick={() => editor.commands.insertQuizQuestion()}
        className='p-2 rounded hover:bg-gray-100'
        title='Insert quiz question'
      >
        <HelpCircle size={18} />
      </button>
      <button
        onClick={() => editor.commands.insertSlideBreak()}
        className='p-2 rounded hover:bg-gray-100'
        title='Insert slide break'
      >
        <PanelTopDashed size={18} />
      </button>
      <button
        onClick={() => editor.commands.insertBranchingCard()}
        className='p-2 rounded hover:bg-gray-100'
        title='Insert branching card'
      >
        <GitFork size={18} />
      </button>
      <button
        onClick={onMapClick}
        className='p-2 rounded hover:bg-gray-100'
        title='View branching map'
      >
        <Map size={18} />
      </button>
      <button
        onClick={isAIDisabled ? undefined : onVisualPromptClick}
        className={`p-2 rounded ${
          isAIDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'
        }`}
        title={
          isAIDisabled
            ? 'Enable AI to generate image prompts'
            : 'Generate image prompt'
        }
      >
        <Wand2 size={18} />
      </button>

      <div className='w-px bg-gray-300 mx-1' />

      <button
        onClick={() => editor.chain().focus().undo().run()}
        className='p-2 rounded hover:bg-gray-100'
      >
        <Undo size={18} />
      </button>
      <button
        onClick={() => editor.chain().focus().redo().run()}
        className='p-2 rounded hover:bg-gray-100'
      >
        <Redo size={18} />
      </button>
    </div>
  );
};

const RichTextEditor = ({
  content,
  onChange,
  onJsonChange,
  pedagogyHints = [],
  unitId,
  materialId,
}: RichTextEditorProps) => {
  const { isAIDisabled } = useAILevel();
  const globalStyle = useTeachingStyleStore(state => state.globalStyle);
  const [showImageDialog, setShowImageDialog] = useState(false);
  const [showBranchingMap, setShowBranchingMap] = useState(false);
  const [showVisualPrompt, setShowVisualPrompt] = useState(false);
  const [visualPromptText, setVisualPromptText] = useState('');

  const editor = useEditor({
    extensions: [
      StarterKit,
      Image.configure({ inline: false, allowBase64: false }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      CodeBlockLowlight.configure({ lowlight }),
      VideoNode,
      YoutubeNode,
      MermaidNode,
      QuizQuestionNode,
      SlideBreakNode,
      SpeakerNotesNode,
      BranchingCardNode,
      InteractiveVideoEmbedNode,
      TranscriptSegmentNode,
      VideoInteractionNode,
    ],
    content,
    onUpdate: ({ editor }: { editor: Editor }) => {
      onChange(editor.getHTML());
      onJsonChange?.(editor.getJSON());
    },
  });

  const staticGuidance = isAIDisabled
    ? getPedagogyStaticGuidance(globalStyle)
    : [];

  const handleImageInsert = (src: string, alt: string) => {
    editor?.chain().focus().setImage({ src, alt }).run();
  };

  return (
    <div className='border border-gray-300 rounded-lg overflow-hidden'>
      <MenuBar
        editor={editor}
        onImageClick={() => setShowImageDialog(true)}
        onMapClick={() => setShowBranchingMap(true)}
        onVisualPromptClick={() => {
          const { from, to } = editor?.state.selection ?? { from: 0, to: 0 };
          const text =
            from !== to
              ? (editor?.state.doc.textBetween(from, to, ' ') ?? '')
              : '';
          setVisualPromptText(text);
          setShowVisualPrompt(true);
        }}
        isAIDisabled={isAIDisabled}
      />
      <ImageInsertDialog
        isOpen={showImageDialog}
        onClose={() => setShowImageDialog(false)}
        onInsert={handleImageInsert}
        unitId={unitId}
        materialId={materialId}
      />
      {editor && (
        <BranchingMapDialog
          isOpen={showBranchingMap}
          onClose={() => setShowBranchingMap(false)}
          editor={editor}
        />
      )}
      <VisualPromptPanel
        isOpen={showVisualPrompt}
        onClose={() => setShowVisualPrompt(false)}
        selectedText={visualPromptText}
      />
      <EditorContent
        editor={editor}
        className='prose max-w-none p-4 min-h-[400px] focus:outline-none'
      />
      {isAIDisabled && staticGuidance.length > 0 ? (
        <div className='bg-blue-50 border-t border-blue-200 p-3'>
          <div className='flex items-start gap-2'>
            <Info className='w-4 h-4 text-blue-600 mt-0.5 shrink-0' />
            <div>
              <p className='text-sm font-medium text-blue-800 mb-1'>
                Pedagogy Guidance
              </p>
              <ul className='space-y-1'>
                {staticGuidance.map((tip, i) => (
                  <li key={i} className='text-sm text-blue-700'>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ) : (
        pedagogyHints &&
        pedagogyHints.length > 0 && (
          <div className='bg-blue-50 border-t border-blue-200 p-3'>
            <p className='text-sm text-blue-700'>
              <strong>Pedagogy Tip:</strong> {pedagogyHints}
            </p>
          </div>
        )
      )}
    </div>
  );
};

export default RichTextEditor;
