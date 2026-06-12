import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Save, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import type { Editor } from '@tiptap/core';
import UnifiedEditor from '../components/Editor/UnifiedEditor';
import SpeakerNotesGenerateDialog from '../components/Editor/SpeakerNotesGenerateDialog';
import { materialsApi } from '../services/materialsApi';
import type { SpeakerNotesDraft } from '../services/aiApi';
import type { MaterialResponse } from '../types/unitStructure';
import { getFormatMeta } from '../constants/sessionFormats';
import { applySpeakerNotesDrafts } from '../utils/speakerNotes';
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
  const [hasSlides, setHasSlides] = useState(false);
  const editorRef = useRef<Editor | null>(null);
  const { isAIDisabled } = useAILevel();

  const updateHasSlides = useCallback((json: Record<string, unknown>) => {
    const content = json.content;
    setHasSlides(
      Array.isArray(content) &&
        content.some(node => (node as { type?: string }).type === 'slideBreak')
    );
  }, []);

  useEffect(() => {
    if (!materialId) return;
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const data = await materialsApi.getMaterial(materialId);
        if (!cancelled) {
          setMaterial(data);
          setEditedHtml(data.description ?? '');
          if (data.contentJson) updateHasSlides(data.contentJson);
        }
      } catch {
        if (!cancelled) setLoadError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [materialId, updateHasSlides]);

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

      <UnifiedEditor
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
    </div>
  );
};

export default MaterialEditorPage;
