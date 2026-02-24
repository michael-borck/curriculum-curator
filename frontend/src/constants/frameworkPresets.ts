/**
 * Preset templates for custom alignment frameworks.
 * Frontend-only constants — not stored in DB.
 */

import type {
  FrameworkItemCreate,
  FrameworkPresetType,
} from '../types/unitStructure';

export interface FrameworkPreset {
  id: string;
  type: FrameworkPresetType | null;
  name: string;
  description: string;
  icon: string;
  color: string;
  items: FrameworkItemCreate[];
  hint: string;
}

export const FRAMEWORK_PRESETS: FrameworkPreset[] = [
  {
    id: 'plo',
    type: 'plo',
    name: 'Program Learning Outcomes',
    description: 'Map ULOs to your degree program outcomes',
    icon: '\uD83C\uDF93',
    color: 'indigo',
    items: [],
    hint: 'Enter PLOs from your program accreditation document',
  },
  {
    id: 'grit',
    type: 'grit',
    name: 'GRIT Mindset',
    description: 'Global, Responsible, Innovative, Technology-savvy',
    icon: '\uD83D\uDCAA',
    color: 'amber',
    items: [
      { code: 'G', description: 'Global perspectives and cultural awareness' },
      { code: 'R', description: 'Responsible and ethical decision-making' },
      { code: 'I', description: 'Innovative and creative problem-solving' },
      { code: 'T', description: 'Technology-savvy and digitally fluent' },
    ],
    hint: 'Pre-filled with standard GRIT framework items',
  },
  {
    id: 'ethics',
    type: 'ethics',
    name: 'Professional Ethics',
    description: 'Professional body ethical standards',
    icon: '\u2696\uFE0F',
    color: 'emerald',
    items: [],
    hint: 'Add from CPA/Engineers Australia/ACS or your professional body',
  },
  {
    id: 'indigenous',
    type: 'indigenous',
    name: 'Indigenous Perspectives',
    description: 'Indigenous knowledge and reconciliation alignment',
    icon: '\uD83C\uDF3F',
    color: 'orange',
    items: [],
    hint: "Add from your university's Reconciliation Action Plan (RAP)",
  },
  {
    id: 'vision',
    type: 'vision',
    name: 'Organisation Vision',
    description: 'Faculty, school, or university strategic priorities',
    icon: '\uD83C\uDFDB\uFE0F',
    color: 'purple',
    items: [],
    hint: 'Faculty/school/university strategic priorities',
  },
  {
    id: 'other',
    type: null,
    name: 'Other',
    description: 'Create a fully custom alignment framework',
    icon: '\uD83D\uDCCB',
    color: 'gray',
    items: [],
    hint: 'Define your own items',
  },
];
