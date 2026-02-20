import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { PedagogyType, AIAssistLevel } from '../types/index';

interface TeachingStyleState {
  globalStyle: PedagogyType;
  isSet: boolean;
  aiAssistLevel: AIAssistLevel;
  setGlobalStyle: (style: PedagogyType) => void;
  setAIAssistLevel: (level: AIAssistLevel) => void;
  initFromUser: (
    teachingPhilosophy: string | undefined,
    aiAssistLevel?: AIAssistLevel
  ) => void;
}

export const useTeachingStyleStore = create<TeachingStyleState>()(
  persist(
    set => ({
      globalStyle: 'inquiry-based',
      isSet: false,
      aiAssistLevel: 'create',
      setGlobalStyle: (style: PedagogyType) =>
        set({ globalStyle: style, isSet: true }),
      setAIAssistLevel: (level: AIAssistLevel) => set({ aiAssistLevel: level }),
      initFromUser: (
        teachingPhilosophy: string | undefined,
        aiAssistLevel?: AIAssistLevel
      ) => {
        const updates: Partial<TeachingStyleState> = {};
        if (teachingPhilosophy) {
          updates.globalStyle = teachingPhilosophy as PedagogyType;
          updates.isSet = true;
        }
        if (aiAssistLevel) {
          updates.aiAssistLevel = aiAssistLevel;
        }
        if (Object.keys(updates).length > 0) {
          set(updates);
        }
      },
    }),
    {
      name: 'teaching-style-storage',
    }
  )
);

// Pedagogy options for use across the app
export const pedagogyOptions: Array<{
  id: PedagogyType;
  name: string;
  shortName: string;
  description: string;
}> = [
  {
    id: 'inquiry-based',
    name: 'Inquiry-Based',
    shortName: 'Inquiry',
    description: 'Students learn through questioning and exploration',
  },
  {
    id: 'project-based',
    name: 'Project-Based',
    shortName: 'Project',
    description: 'Learning through real-world projects and applications',
  },
  {
    id: 'collaborative',
    name: 'Collaborative',
    shortName: 'Collab',
    description: 'Group work and peer-to-peer learning',
  },
  {
    id: 'game-based',
    name: 'Game-Based',
    shortName: 'Game',
    description: 'Learning through games and interactive challenges',
  },
  {
    id: 'traditional',
    name: 'Traditional',
    shortName: 'Traditional',
    description: 'Structured lecture-based teaching approach',
  },
  {
    id: 'constructivist',
    name: 'Constructivist',
    shortName: 'Construct',
    description: 'Students build knowledge through experience',
  },
  {
    id: 'problem-based',
    name: 'Problem-Based',
    shortName: 'Problem',
    description: 'Learning through solving real problems',
  },
  {
    id: 'experiential',
    name: 'Experiential',
    shortName: 'Experience',
    description: 'Learning through direct experience and reflection',
  },
  {
    id: 'competency-based',
    name: 'Competency-Based',
    shortName: 'Competency',
    description: 'Focus on mastering specific skills and competencies',
  },
];

export const getPedagogyHint = (style: PedagogyType): string => {
  const hints: Record<PedagogyType, string> = {
    'inquiry-based':
      'Start with thought-provoking questions to encourage exploration.',
    'project-based': 'Include real-world applications and hands-on activities.',
    traditional: 'Focus on clear explanations and structured examples.',
    collaborative: 'Add group activities and discussion prompts.',
    'game-based': 'Incorporate challenges, points, or competitive elements.',
    constructivist: 'Help students build knowledge through guided discovery.',
    'problem-based': 'Present real-world problems that require investigation.',
    experiential: 'Include hands-on experiences and reflective activities.',
    'competency-based':
      'Focus on measurable skills and clear learning outcomes.',
  };
  return hints[style] || '';
};

export const getPedagogyStaticGuidance = (style: PedagogyType): string[] => {
  const guidance: Record<PedagogyType, string[]> = {
    'inquiry-based': [
      'Open each topic with a driving question that students cannot answer without investigation.',
      'Design activities where students gather evidence before receiving explanations.',
      'Include reflection prompts that ask students to evaluate their own reasoning process.',
      'Sequence content so that each discovery builds toward the next question.',
    ],
    'project-based': [
      'Frame each unit around a tangible deliverable students produce by the end.',
      'Break large projects into milestones with clear checkpoints and feedback loops.',
      'Connect project requirements directly to learning outcomes so students see the purpose.',
      'Include authentic constraints (budget, timeline, stakeholders) to mirror real-world practice.',
    ],
    collaborative: [
      'Design tasks that require genuine interdependence — not just dividing work.',
      'Include structured roles (facilitator, recorder, challenger) to keep groups productive.',
      "Build in peer feedback stages where students evaluate each other's contributions.",
      'Vary group composition across activities to expose students to diverse perspectives.',
    ],
    'game-based': [
      'Define clear win conditions and rules before introducing game mechanics.',
      'Use points or levels to mark progress, not just final achievement.',
      'Include an element of choice so students feel agency within the game structure.',
      'Debrief after each game activity to connect the experience to learning objectives.',
    ],
    traditional: [
      'Structure each session with a clear introduction, body, and summary.',
      'Provide worked examples before asking students to practice independently.',
      'Use formative checks (quick polls, exit tickets) to gauge understanding during lectures.',
      'Supplement lectures with curated readings that reinforce key concepts.',
    ],
    constructivist: [
      "Start with students' prior knowledge and build new concepts on top of it.",
      'Use scaffolded tasks that gradually remove support as competence grows.',
      'Encourage students to explain concepts in their own words rather than memorise definitions.',
      'Design activities where students encounter and resolve cognitive conflict.',
    ],
    'problem-based': [
      "Present ill-structured problems that don't have a single correct answer.",
      'Let students identify what they need to learn before providing resources.',
      'Facilitate rather than lecture — guide students toward resources instead of giving answers.',
      'Include a reflection stage where students evaluate their problem-solving process.',
    ],
    experiential: [
      'Follow the cycle: concrete experience, reflective observation, abstract conceptualisation, active experimentation.',
      'Include field work, simulations, or lab activities that create direct experience.',
      'Build structured reflection journals or debrief sessions after each experience.',
      'Connect each experience explicitly to theoretical frameworks in the unit.',
    ],
    'competency-based': [
      'Define observable, measurable competencies for each topic or module.',
      'Allow flexible pacing so students who demonstrate mastery can advance.',
      'Use rubrics that describe specific performance levels for each competency.',
      'Provide multiple assessment pathways so students can demonstrate competency in different ways.',
    ],
  };
  return guidance[style] || [];
};
