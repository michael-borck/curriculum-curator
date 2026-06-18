import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Save, Sparkles, Wand2 } from 'lucide-react';
import toast from 'react-hot-toast';
import type { Editor } from '@tiptap/core';
import UnifiedEditor from '../components/Editor/UnifiedEditor';
import SpeakerNotesGenerateDialog from '../components/Editor/SpeakerNotesGenerateDialog';
import RestructureDialog from '../components/Editor/RestructureDialog';
import SourceFilesPanel from '../components/Editor/SourceFilesPanel';
import { materialsApi } from '../services/materialsApi';
import type { SpeakerNotesDraft } from '../services/aiApi';
import type { AttachedSourceFile } from '../services/materialImportApi';
import type { MaterialResponse } from '../types/unitStructure';
import { getFormatMeta } from '../constants/sessionFormats';
import { applySpeakerNotesDrafts } from '../utils/speakerNotes';
import {
  isPlainParagraphContent,
  estimateTokens,
} from '../utils/contentStructure';
import { useAILevel } from '../hooks/useAILevel';

/**
 * Full-page content editor for a single weekly material.
 *
 * Hosts the TipTap editor (UnifiedEditor) on its own route so structured
 * content (quiz questions, slide breaks, speaker notes, branching cards)
 * can be authored. The metadata form in WeeklyMaterialsManager still owns
 * title/type/status edits; this page owns the material body.
 */
const MaterialEditorPage: React.FC = () => {
  const { unitId, materialId } = useParams<{
    unitId: string;
    materialId: string;
  }>();
  const navigate = useNavigate();

  const [material, setMaterial] = useState<MaterialResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [editedHtml, setEditedHtml] = useState('');
  const [editedJson, setEditedJson] = useState<
    Record<string, unknown> | undefined
  >(undefined);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notesDialogOpen, setNotesDialogOpen] = useState(false);
  const [restructureOpen, setRestructureOpen] = useState(false);
  const [hasSlides, setHasSlides] = useState(false);
  const [tipDismissed, setTipDismissed] = useState(
    () => localStorage.getItem('speaker-notes-tip-dismissed') === 'true'
  );
  const [editorKey, setEditorKey] = useState(0);
  const editorRef = useRef<Editor | null>(null);
  const { isAIDisabled } = useAILevel();

  const dismissTip = () => {
    localStorage.setItem('speaker-notes-tip-dismissed', 'true');
    setTipDismissed(true);
  };

  const updateHasSlides = useCallback((json: Record<string, unknown>) => {
    const content = json.content;
    setHasSlides(
      Array.isArray(content) &&
        content.some(node => (node as { type?: string }).type === 'slideBreak')
    );
  }, []);

  const loadMaterial = useCallback(
    async (showSpinner = true) => {
      if (!materialId) return;
      try {
        if (showSpinner) setLoading(true);
        const data = await materialsApi.getMaterial(materialId);
        setMaterial(data);
        setEditedHtml(data.description ?? '');
        setEditedJson(data.contentJson);
        if (data.contentJson) updateHasSlides(data.contentJson);
        // Bump the key so the editor remounts with freshly loaded content
        setEditorKey(k => k + 1);
        setDirty(false);
      } catch {
        setLoadError(true);
      } finally {
        if (showSpinner) setLoading(false);
      }
    },
    [materialId, updateHasSlides]
  );

  useEffect(() => {
    void loadMaterial();
  }, [loadMaterial]);

  const handleSave = useCallback(async () => {
    if (!material) return;
    try {
      setSaving(true);
      const updated = await materialsApi.updateMaterial(material.id, {
        description: editedHtml,
        ...(editedJson && { contentJson: editedJson }),
      });
      setMaterial(updated);
      setDirty(false);
      toast.success('Material saved');
    } catch {
      toast.error('Failed to save material');
    } finally {
      setSaving(false);
    }
  }, [material, editedHtml, editedJson]);

  // Warn before the browser unloads with unsaved changes
  useEffect(() => {
    if (!dirty) return;
    const beforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, [dirty]);

  const handleBack = () => {
    if (
      dirty &&
      !window.confirm('You have unsaved changes. Leave without saving?')
    ) {
      return;
    }
    navigate(`/units/${unitId}?tab=structure`);
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='w-6 h-6 animate-spin text-gray-400' />
      </div>
    );
  }

  if (loadError || !material) {
    return (
      <div className='max-w-3xl mx-auto py-12 text-center'>
        <p className='text-gray-600 mb-4'>Material not found.</p>
        <button
          onClick={() => navigate(`/units/${unitId}?tab=structure`)}
          className='text-blue-600 hover:underline'
        >
          Back to unit
        </button>
      </div>
    );
  }

  const formatMeta = getFormatMeta(material.type);
  // Prefer the structured document when present; description is the
  // HTML fallback for materials created before structured authoring.
  const initialContent =
    material.contentJson ?? material.description ?? '<p></p>';
  // Source files attached by a Mode B multi-format import (story 6.15),
  // stored untransformed in material_metadata.
  const sourceFiles = (material.materialMetadata?.attached_source_files ??
    []) as AttachedSourceFile[];
  // Structure recovery (6.16) is offered for flat plain-paragraph content,
  // the shape a PDF import produces.
  const liveJson = editedJson ?? material.contentJson;
  const canRestructure = isPlainParagraphContent(liveJson);

  return (
    <div className='max-w-5xl mx-auto px-4 py-6'>
      <div className='flex items-center justify-between mb-4'>
        <div className='flex items-center gap-3 min-w-0'>
          <button
            onClick={handleBack}
            className='p-2 rounded-lg hover:bg-gray-100 text-gray-600'
            title='Back to unit'
          >
            <ArrowLeft className='w-5 h-5' />
          </button>
          <div className='min-w-0'>
            <h1 className='text-xl font-semibold text-gray-900 truncate'>
              {material.title}
            </h1>
            <p className='text-sm text-gray-500'>
              Week {material.weekNumber} · {formatMeta.label}
            </p>
          </div>
        </div>
        <div className='flex items-center gap-3'>
          {dirty && (
            <span className='text-sm text-amber-600'>Unsaved changes</span>
          )}
          {hasSlides && !isAIDisabled && (
            <button
              onClick={() => setNotesDialogOpen(true)}
              className='flex items-center gap-2 px-4 py-2 text-sm text-purple-700 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100'
              title='Draft speaker notes for your slides with AI, reviewed before saving'
            >
              <Sparkles className='w-4 h-4' />
              Notes with AI
            </button>
          )}
          {canRestructure && !isAIDisabled && (
            <button
              onClick={() => setRestructureOpen(true)}
              className='flex items-center gap-2 px-4 py-2 text-sm text-purple-700 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100'
              title='Recover headings and lists from this plain-text import, reviewed before applying'
            >
              <Wand2 className='w-4 h-4' />
              Improve structure
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving || !dirty}
            className='flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed'
          >
            {saving ? (
              <Loader2 className='w-4 h-4 animate-spin' />
            ) : (
              <Save className='w-4 h-4' />
            )}
            Save
          </button>
        </div>
      </div>

      {hasSlides && !tipDismissed && (
        <div className='mb-4 flex items-start justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800'>
          <p>
            <span className='font-medium'>
              Speaker notes carry your teaching
            </span>{' '}
            — what you say, not what students see on screen. Each slide has a
            notes block that exports to PowerPoint&apos;s speaker notes pane.
          </p>
          <button
            onClick={dismissTip}
            className='shrink-0 text-amber-600 hover:text-amber-800 text-xs font-medium'
          >
            Got it
          </button>
        </div>
      )}

      <UnifiedEditor
        key={editorKey}
        content={initialContent}
        onChange={html => {
          setEditedHtml(html);
          setDirty(true);
        }}
        onJsonChange={json => {
          setEditedJson(json);
          updateHasSlides(json);
        }}
        onEditorReady={editor => {
          editorRef.current = editor;
        }}
        unitId={unitId}
        materialId={materialId}
      />

      {materialId && sourceFiles.length > 0 && (
        <SourceFilesPanel
          materialId={materialId}
          sourceFiles={sourceFiles}
          onPromoted={() => void loadMaterial(false)}
        />
      )}

      {notesDialogOpen && materialId && editorRef.current && (
        <SpeakerNotesGenerateDialog
          materialId={materialId}
          contentJson={editorRef.current.getJSON()}
          onApply={(drafts: SpeakerNotesDraft[]) => {
            const editor = editorRef.current;
            if (!editor) return;
            const updated = applySpeakerNotesDrafts(editor.getJSON(), drafts);
            editor.commands.setContent(updated, true);
            toast.success(
              `Applied notes to ${drafts.length} slide${drafts.length === 1 ? '' : 's'} — remember to save`
            );
          }}
          onClose={() => setNotesDialogOpen(false)}
        />
      )}

      {restructureOpen && materialId && (
        <RestructureDialog
          materialId={materialId}
          estimatedTokens={estimateTokens(
            editorRef.current?.getJSON() ?? liveJson
          )}
          onApply={contentJson => {
            editorRef.current?.commands.setContent(contentJson, true);
            toast.success('Structure applied — remember to save');
          }}
          onClose={() => setRestructureOpen(false)}
        />
      )}
    </div>
  );
};

export default MaterialEditorPage;
