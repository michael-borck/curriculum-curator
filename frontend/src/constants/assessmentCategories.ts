/**
 * Metadata and helpers for assessment category types.
 *
 * Known categories get icons, colors, and labels.
 * Unknown / custom values fall back to a neutral gray pill with a title-cased label.
 */

export interface AssessmentCategoryMeta {
  label: string;
  /** Lucide icon name (consumer maps to JSX) */
  icon: string;
  /** Tailwind pill classes: background + text color */
  color: string;
}

/** Metadata for every known assessment category. */
export const ASSESSMENT_CATEGORY_META: Record<string, AssessmentCategoryMeta> =
  {
    quiz: {
      label: 'Quiz',
      icon: 'ClipboardCheck',
      color: 'bg-blue-100 text-blue-800',
    },
    exam: {
      label: 'Exam',
      icon: 'FileText',
      color: 'bg-red-100 text-red-800',
    },
    assignment: {
      label: 'Assignment',
      icon: 'FileText',
      color: 'bg-indigo-100 text-indigo-800',
    },
    project: {
      label: 'Project',
      icon: 'Users',
      color: 'bg-purple-100 text-purple-800',
    },
    discussion: {
      label: 'Discussion',
      icon: 'MessageSquare',
      color: 'bg-teal-100 text-teal-800',
    },
    paper: {
      label: 'Paper',
      icon: 'FileText',
      color: 'bg-amber-100 text-amber-800',
    },
    presentation: {
      label: 'Presentation',
      icon: 'Presentation',
      color: 'bg-cyan-100 text-cyan-800',
    },
    lab: {
      label: 'Lab',
      icon: 'FlaskConical',
      color: 'bg-violet-100 text-violet-800',
    },
    lab_report: {
      label: 'Lab Report',
      icon: 'FlaskConical',
      color: 'bg-violet-100 text-violet-800',
    },
    portfolio: {
      label: 'Portfolio',
      icon: 'BookOpen',
      color: 'bg-emerald-100 text-emerald-800',
    },
    participation: {
      label: 'Participation',
      icon: 'Users',
      color: 'bg-green-100 text-green-800',
    },
    viva: {
      label: 'Viva',
      icon: 'MessageSquare',
      color: 'bg-pink-100 text-pink-800',
    },
    // Cross-sector
    reflection: {
      label: 'Reflection',
      icon: 'BookOpen',
      color: 'bg-orange-100 text-orange-800',
    },
    journal: {
      label: 'Journal',
      icon: 'BookOpen',
      color: 'bg-orange-100 text-orange-800',
    },
    case_study: {
      label: 'Case Study',
      icon: 'FileText',
      color: 'bg-amber-100 text-amber-800',
    },
    peer_review: {
      label: 'Peer Review',
      icon: 'Users',
      color: 'bg-sky-100 text-sky-800',
    },
    // VET
    practical_assessment: {
      label: 'Practical Assessment',
      icon: 'Wrench',
      color: 'bg-yellow-100 text-yellow-800',
    },
    skills_demonstration: {
      label: 'Skills Demonstration',
      icon: 'Wrench',
      color: 'bg-yellow-100 text-yellow-800',
    },
    // K-12
    test: {
      label: 'Test',
      icon: 'ClipboardCheck',
      color: 'bg-red-100 text-red-800',
    },
    homework: {
      label: 'Homework',
      icon: 'FileText',
      color: 'bg-lime-100 text-lime-800',
    },
    other: {
      label: 'Other',
      icon: 'FileText',
      color: 'bg-gray-100 text-gray-800',
    },
  };

/** All known category keys in display order. */
export const ALL_KNOWN_CATEGORIES = Object.keys(ASSESSMENT_CATEGORY_META);

/**
 * Get category metadata for any category string.
 * Known categories return their configured meta; unknown/custom values get a
 * neutral gray pill with a title-cased label.
 */
export function getCategoryMeta(category: string): AssessmentCategoryMeta {
  if (category in ASSESSMENT_CATEGORY_META) {
    return ASSESSMENT_CATEGORY_META[category];
  }
  const label = category
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
  return { label, icon: 'FileText', color: 'bg-gray-100 text-gray-700' };
}
