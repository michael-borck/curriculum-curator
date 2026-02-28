import React from 'react';
import type { MaterialExportPreview } from '../../services/exportApi';

// ─── Display labels and colours ──────────────────────────────────────

const CONTENT_TYPE_BADGES: Record<string, { label: string; color: string }> = {
  quiz: { label: 'Quiz', color: 'bg-purple-100 text-purple-700' },
  slides: { label: 'Slides', color: 'bg-orange-100 text-orange-700' },
  branching: { label: 'Branching', color: 'bg-green-100 text-green-700' },
  interactive_video: {
    label: 'Interactive Video',
    color: 'bg-indigo-100 text-indigo-700',
  },
  rich_text: { label: 'Text', color: 'bg-gray-100 text-gray-600' },
};

const TARGET_LABELS: Record<string, string> = {
  qti: 'QTI',
  h5p_question_set: 'H5P Quiz',
  h5p_course_presentation: 'H5P Slides',
  h5p_branching: 'H5P Branching',
  h5p_interactive_video: 'H5P Interactive Video',
  html: 'HTML',
};

// ─── Component ───────────────────────────────────────────────────────

interface MaterialExportRowProps {
  material: MaterialExportPreview;
  overrides: Record<string, string[]>;
  onOverrideChange: (
    materialId: string,
    targets: Record<string, string[]>
  ) => void;
}

const MaterialExportRow: React.FC<MaterialExportRowProps> = ({
  material,
  overrides,
  onOverrideChange,
}) => {
  const toggleTarget = (contentType: string, target: string) => {
    const current =
      overrides[contentType] ?? material.resolvedTargets[contentType] ?? [];
    const isActive = current.includes(target);
    const next = isActive
      ? current.filter(t => t !== target)
      : [...current, target];
    // Don't allow empty — if user deselects last, keep it
    if (next.length === 0) return;
    onOverrideChange(material.materialId, {
      ...overrides,
      [contentType]: next,
    });
  };

  return (
    <div className='flex items-start gap-3 py-2.5 px-3 rounded-lg hover:bg-gray-50'>
      {/* Title */}
      <div className='min-w-0 flex-1'>
        <p className='text-sm font-medium text-gray-800 truncate'>
          {material.title}
        </p>
        <div className='flex items-center gap-1.5 mt-1'>
          {material.contentTypes.map(ct => {
            const badge = CONTENT_TYPE_BADGES[ct] ?? {
              label: ct,
              color: 'bg-gray-100 text-gray-600',
            };
            return (
              <span
                key={ct}
                className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${badge.color}`}
              >
                {badge.label}
              </span>
            );
          })}
        </div>
      </div>

      {/* Target chips per content type */}
      <div className='flex flex-col gap-1.5 shrink-0'>
        {material.contentTypes.map(ct => {
          const available = material.availableTargets[ct] ?? [];
          if (available.length <= 1) return null; // No choice to make
          const active = overrides[ct] ?? material.resolvedTargets[ct] ?? [];
          return (
            <div key={ct} className='flex items-center gap-1'>
              {available.map(target => {
                const isOn = active.includes(target);
                return (
                  <button
                    key={target}
                    onClick={() => toggleTarget(ct, target)}
                    className={`text-[11px] px-2 py-0.5 rounded-full border transition ${
                      isOn
                        ? 'bg-purple-100 border-purple-300 text-purple-700 font-medium'
                        : 'bg-white border-gray-200 text-gray-500 hover:border-gray-300'
                    }`}
                  >
                    {TARGET_LABELS[target] ?? target}
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MaterialExportRow;
