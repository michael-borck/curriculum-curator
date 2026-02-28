/**
 * Metadata and helpers for session format types.
 *
 * Known formats get icons, colors, and labels.
 * Unknown / custom values fall back to a neutral gray pill with a title-cased label.
 */

export interface SessionFormatMeta {
  label: string;
  /** Lucide icon name (consumer maps to JSX) */
  icon: string;
  /** Tailwind pill classes: background + text color */
  color: string;
}

/** Metadata for every known session format. */
export const SESSION_FORMAT_META: Record<string, SessionFormatMeta> = {
  lecture: {
    label: 'Lecture',
    icon: 'Presentation',
    color: 'bg-blue-100 text-blue-800',
  },
  tutorial: {
    label: 'Tutorial',
    icon: 'Users',
    color: 'bg-green-100 text-green-800',
  },
  lab: {
    label: 'Lab',
    icon: 'FlaskConical',
    color: 'bg-purple-100 text-purple-800',
  },
  workshop: {
    label: 'Workshop',
    icon: 'Users',
    color: 'bg-yellow-100 text-yellow-800',
  },
  seminar: {
    label: 'Seminar',
    icon: 'MessageSquare',
    color: 'bg-teal-100 text-teal-800',
  },
  independent: {
    label: 'Independent',
    icon: 'BookOpen',
    color: 'bg-orange-100 text-orange-800',
  },
  // K-12
  lesson: {
    label: 'Lesson',
    icon: 'BookOpen',
    color: 'bg-sky-100 text-sky-800',
  },
  excursion: {
    label: 'Excursion',
    icon: 'Map',
    color: 'bg-emerald-100 text-emerald-800',
  },
  // VET
  practical: {
    label: 'Practical',
    icon: 'Wrench',
    color: 'bg-amber-100 text-amber-800',
  },
  placement: {
    label: 'Placement',
    icon: 'Building',
    color: 'bg-indigo-100 text-indigo-800',
  },
  simulation: {
    label: 'Simulation',
    icon: 'Monitor',
    color: 'bg-violet-100 text-violet-800',
  },
  // Corporate
  presentation: {
    label: 'Presentation',
    icon: 'Presentation',
    color: 'bg-cyan-100 text-cyan-800',
  },
  elearning: {
    label: 'E-Learning',
    icon: 'Monitor',
    color: 'bg-lime-100 text-lime-800',
  },
  // Cross-sector
  assessment: {
    label: 'Assessment',
    icon: 'ClipboardCheck',
    color: 'bg-red-100 text-red-800',
  },
  // Free text
  custom: {
    label: 'Custom',
    icon: 'FileText',
    color: 'bg-gray-100 text-gray-800',
  },
};

/** All known format keys in display order. */
export const ALL_KNOWN_FORMATS = Object.keys(SESSION_FORMAT_META);

/**
 * Get format metadata for any type string.
 * Known formats return their configured meta; unknown/custom values get a
 * neutral gray pill with a title-cased label.
 */
export function getFormatMeta(type: string): SessionFormatMeta {
  if (type in SESSION_FORMAT_META) {
    return SESSION_FORMAT_META[type];
  }
  // Generate sensible defaults for custom / unknown values
  const label = type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  return { label, icon: 'FileText', color: 'bg-gray-100 text-gray-700' };
}
