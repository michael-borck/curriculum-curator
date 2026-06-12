import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import UnifiedEditor from '../components/Editor/UnifiedEditor';
import { materialsApi } from '../services/materialsApi';
import type { MaterialResponse } from '../types/unitStructure';
import { getFormatMeta } from '../constants/sessionFormats';

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
  }, [materialId]);

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
        }}
        unitId={unitId}
        materialId={materialId}
      />
    </div>
  );
};

export default MaterialEditorPage;
