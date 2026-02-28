export type SectorId = 'k12' | 'vet' | 'higher_ed' | 'corporate' | 'other';

export interface SectorProfile {
  id: SectorId;
  label: string;
  description: string;
  unitLabel: string;
  topicLabel: string;
  duration: number;
  showCreditPoints: boolean;
  showSemester: boolean;
  showAccreditation: boolean;
  codeLabel: string;
  codePlaceholder: string;
  presets: string[];
  defaultSessionFormats: string[];
}

const SECTOR_PROFILES: Record<SectorId, SectorProfile> = {
  k12: {
    id: 'k12',
    label: 'K-12 Education',
    description: 'Primary and secondary schools',
    unitLabel: 'Subject',
    topicLabel: 'Lesson',
    duration: 10,
    showCreditPoints: false,
    showSemester: false,
    showAccreditation: false,
    codeLabel: 'Subject Code',
    codePlaceholder: 'e.g., MATH-7',
    presets: ['term', 'intensive', 'custom'],
    defaultSessionFormats: [
      'lesson',
      'workshop',
      'excursion',
      'independent',
      'assessment',
    ],
  },
  vet: {
    id: 'vet',
    label: 'Vocational Education (VET)',
    description: 'TAFE, RTOs, and trade training',
    unitLabel: 'Unit',
    topicLabel: 'Week',
    duration: 18,
    showCreditPoints: true,
    showSemester: true,
    showAccreditation: true,
    codeLabel: 'Unit Code',
    codePlaceholder: 'e.g., ICTPRG302',
    presets: ['semester', 'trimester', 'intensive', 'custom'],
    defaultSessionFormats: [
      'practical',
      'tutorial',
      'workshop',
      'simulation',
      'placement',
      'assessment',
    ],
  },
  higher_ed: {
    id: 'higher_ed',
    label: 'Higher Education',
    description: 'Universities and colleges',
    unitLabel: 'Unit',
    topicLabel: 'Week',
    duration: 12,
    showCreditPoints: true,
    showSemester: true,
    showAccreditation: true,
    codeLabel: 'Unit Code',
    codePlaceholder: 'e.g., CS101',
    presets: [
      'semester',
      'trimester',
      'term',
      'intensive',
      'workshop',
      'self-paced',
      'custom',
    ],
    defaultSessionFormats: [
      'lecture',
      'tutorial',
      'lab',
      'workshop',
      'seminar',
      'independent',
    ],
  },
  corporate: {
    id: 'corporate',
    label: 'Corporate Training',
    description: 'Workplace and professional development',
    unitLabel: 'Program',
    topicLabel: 'Session',
    duration: 4,
    showCreditPoints: false,
    showSemester: false,
    showAccreditation: false,
    codeLabel: 'Program Name',
    codePlaceholder: 'e.g., Leadership 101',
    presets: ['workshop', 'intensive', 'self-paced', 'custom'],
    defaultSessionFormats: [
      'presentation',
      'workshop',
      'elearning',
      'simulation',
      'independent',
    ],
  },
  other: {
    id: 'other',
    label: 'Other',
    description: 'Community, non-formal, or custom contexts',
    unitLabel: 'Learning Program',
    topicLabel: 'Module',
    duration: 6,
    showCreditPoints: false,
    showSemester: false,
    showAccreditation: false,
    codeLabel: 'Program Code',
    codePlaceholder: 'e.g., LP-001',
    presets: [
      'semester',
      'trimester',
      'term',
      'intensive',
      'workshop',
      'self-paced',
      'custom',
    ],
    defaultSessionFormats: [
      'workshop',
      'lesson',
      'independent',
      'elearning',
      'assessment',
    ],
  },
};

export function getSectorProfile(
  sectorId: string | null | undefined
): SectorProfile {
  if (sectorId && sectorId in SECTOR_PROFILES) {
    return SECTOR_PROFILES[sectorId as SectorId];
  }
  return SECTOR_PROFILES.higher_ed;
}

export { SECTOR_PROFILES };
