/**
 * Single source of truth for export format display metadata (story 9.19).
 *
 * Keys are the canonical export format identifiers shared with the backend
 * export registry and format_resolver (persisted in material export_targets
 * and teaching_preferences.export_defaults — do not rename).
 */

export interface ExportFormatMeta {
  /** Short technical name, e.g. "QTI 2.1" */
  label: string;
  /** Plain-language name a non-technical educator understands */
  friendlyLabel: string;
  /** One-sentence explanation shown as a tooltip */
  tooltip: string;
  /** File extension hint, e.g. ".h5p" */
  extension: string;
}

export const EXPORT_FORMAT_META: Record<string, ExportFormatMeta> = {
  imscc: {
    label: 'IMSCC v1.1',
    friendlyLabel: 'LMS Course Package',
    tooltip:
      'Imports a whole unit into Canvas, Moodle, or Blackboard — Common Cartridge standard.',
    extension: '.imscc',
  },
  scorm: {
    label: 'SCORM 1.2',
    friendlyLabel: 'LMS Learning Package',
    tooltip:
      'Self-contained learning package with completion tracking for any SCORM-compliant LMS.',
    extension: '.zip',
  },
  html: {
    label: 'HTML',
    friendlyLabel: 'Web Page',
    tooltip: 'A single web page viewable in any browser, no LMS needed.',
    extension: '.html',
  },
  qti: {
    label: 'QTI 2.1',
    friendlyLabel: 'LMS Native Quiz',
    tooltip:
      'Imports into your LMS quiz bank (Canvas, Moodle, Blackboard) as auto-graded questions.',
    extension: '.zip',
  },
  h5p_question_set: {
    label: 'H5P Question Set',
    friendlyLabel: 'Interactive Quiz',
    tooltip:
      'Rich interactive quiz with immediate feedback — requires the H5P plugin in your LMS.',
    extension: '.h5p',
  },
  h5p_course_presentation: {
    label: 'H5P Course Presentation',
    friendlyLabel: 'Interactive Slides',
    tooltip:
      'Slides students click through in the LMS, with questions embedded between slides.',
    extension: '.h5p',
  },
  h5p_branching: {
    label: 'H5P Branching Scenario',
    friendlyLabel: 'Interactive Scenario',
    tooltip:
      'Choose-your-own-adventure scenario where student decisions lead to different outcomes.',
    extension: '.h5p',
  },
  h5p_interactive_video: {
    label: 'H5P Interactive Video',
    friendlyLabel: 'Interactive Video',
    tooltip: 'Video with questions overlaid at chosen timestamps.',
    extension: '.h5p',
  },
  pdf: {
    label: 'PDF',
    friendlyLabel: 'Printable Document',
    tooltip: 'Fixed-layout document for printing or sharing.',
    extension: '.pdf',
  },
  docx: {
    label: 'DOCX',
    friendlyLabel: 'Word Document',
    tooltip: 'Editable Microsoft Word document.',
    extension: '.docx',
  },
  pptx: {
    label: 'PPTX',
    friendlyLabel: 'PowerPoint Slides',
    tooltip: 'Editable PowerPoint deck, speaker notes included.',
    extension: '.pptx',
  },
};

/** Lookup with a sensible fallback for unknown format keys. */
export function getExportFormatMeta(format: string): ExportFormatMeta {
  const meta = EXPORT_FORMAT_META[format];
  if (meta) return meta;
  const titleized = format
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  return {
    label: titleized,
    friendlyLabel: titleized,
    tooltip: '',
    extension: '',
  };
}
