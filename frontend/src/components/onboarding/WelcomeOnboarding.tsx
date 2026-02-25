import { useState } from 'react';
import {
  Lightbulb,
  ArrowRight,
  Sparkles,
  X,
  Target,
  BookOpen,
  Users,
  Brain,
  Rocket,
  Puzzle,
  FlaskRoundIcon as Flask,
  CheckCircle,
  School,
  Wrench,
  GraduationCap,
  Building2,
  MoreHorizontal,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useTeachingStyleStore } from '../../stores/teachingStyleStore';
import api from '../../services/api';
import toast from 'react-hot-toast';
import type { PedagogyType } from '../../types';
import {
  SECTOR_PROFILES,
  getSectorProfile,
} from '../../constants/sectorProfiles';
import type { SectorId } from '../../constants/sectorProfiles';
import type { LucideIcon } from 'lucide-react';

const sectorCards: { id: SectorId; icon: LucideIcon }[] = [
  { id: 'k12', icon: School },
  { id: 'vet', icon: Wrench },
  { id: 'higher_ed', icon: GraduationCap },
  { id: 'corporate', icon: Building2 },
  { id: 'other', icon: MoreHorizontal },
];

const teachingStyles = [
  {
    id: 'traditional',
    name: 'Traditional',
    icon: BookOpen,
    color: 'bg-blue-500',
    description: 'Structured lectures and direct instruction',
  },
  {
    id: 'inquiry-based',
    name: 'Inquiry-Based',
    icon: Lightbulb,
    color: 'bg-yellow-500',
    description: 'Question-driven exploration and discovery',
  },
  {
    id: 'project-based',
    name: 'Project-Based',
    icon: Target,
    color: 'bg-orange-500',
    description: 'Real-world projects and hands-on work',
  },
  {
    id: 'collaborative',
    name: 'Collaborative',
    icon: Users,
    color: 'bg-indigo-500',
    description: 'Group work and peer learning',
  },
  {
    id: 'constructivist',
    name: 'Constructivist',
    icon: Puzzle,
    color: 'bg-green-500',
    description: 'Building knowledge through experience',
  },
  {
    id: 'experiential',
    name: 'Experiential',
    icon: Flask,
    color: 'bg-red-500',
    description: 'Learning through direct experience',
  },
  {
    id: 'problem-based',
    name: 'Problem-Based',
    icon: Brain,
    color: 'bg-pink-500',
    description: 'Solving complex real-world problems',
  },
  {
    id: 'game-based',
    name: 'Game-Based',
    icon: Rocket,
    color: 'bg-purple-500',
    description: 'Games, challenges, and interactive elements',
  },
  {
    id: 'competency-based',
    name: 'Competency-Based',
    icon: CheckCircle,
    color: 'bg-teal-500',
    description: 'Mastering specific skills',
  },
];

const questions = [
  {
    id: 0,
    question: 'How do you prefer to introduce new concepts?',
    options: [
      { value: 'traditional', label: 'Structured lectures and presentations' },
      { value: 'constructivist', label: 'Let students explore and discover' },
      { value: 'inquiry-based', label: 'Start with questions' },
      { value: 'project-based', label: 'Through project contexts' },
    ],
  },
  {
    id: 1,
    question: "What's your ideal classroom dynamic?",
    options: [
      { value: 'collaborative', label: 'Students in groups and teams' },
      { value: 'traditional', label: 'Teacher-led instruction' },
      { value: 'project-based', label: 'Long-term project work' },
      { value: 'experiential', label: 'Hands-on activities' },
    ],
  },
  {
    id: 2,
    question: 'How do you assess student learning?',
    options: [
      { value: 'traditional', label: 'Tests and exams' },
      { value: 'project-based', label: 'Portfolios and presentations' },
      { value: 'problem-based', label: 'Problem-solving demonstrations' },
      { value: 'competency-based', label: 'Skill demonstrations' },
    ],
  },
  {
    id: 3,
    question: 'What role do you prefer in the classroom?',
    options: [
      { value: 'traditional', label: 'Expert and knowledge source' },
      { value: 'constructivist', label: 'Facilitator and guide' },
      { value: 'collaborative', label: 'Collaborator and co-learner' },
      { value: 'inquiry-based', label: 'Question prompter' },
    ],
  },
  {
    id: 4,
    question: 'How do you structure learning time?',
    options: [
      { value: 'game-based', label: 'Games and interactive activities' },
      { value: 'traditional', label: 'Lecture then practice' },
      { value: 'experiential', label: 'Experience then reflect' },
      { value: 'problem-based', label: 'Problem then learn' },
    ],
  },
];

type Step = 'SECTOR' | 'STYLE_CHOICE' | 'QUIZ' | 'SELECT';

interface WelcomeOnboardingProps {
  onComplete: () => void;
  onSkip: () => void;
}

const WelcomeOnboarding = ({ onComplete, onSkip }: WelcomeOnboardingProps) => {
  const { user } = useAuthStore();
  const { setGlobalStyle } = useTeachingStyleStore();
  const [step, setStep] = useState<Step>('SECTOR');
  const [selectedSector, setSelectedSector] = useState<SectorId>('higher_ed');
  const [selectedStyle, setSelectedStyle] =
    useState<PedagogyType>('inquiry-based');
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);

  const handleQuizAnswer = (answer: string) => {
    const newAnswers = { ...answers, [currentQuestion]: answer };
    setAnswers(newAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      const styleCounts: Record<string, number> = {};
      Object.values(newAnswers).forEach(style => {
        styleCounts[style] = (styleCounts[style] || 0) + 1;
      });
      const maxCount = Math.max(...Object.values(styleCounts));
      const recommended = Object.entries(styleCounts).find(
        ([, count]) => count === maxCount
      )?.[0] as PedagogyType;

      saveProfile(recommended || 'inquiry-based');
    }
  };

  const saveProfile = async (style: PedagogyType) => {
    try {
      setSaving(true);
      await api.patch('/auth/profile', {
        educationSector: selectedSector,
        teachingPhilosophy: style,
      });
      setGlobalStyle(style);
      if (user) {
        useAuthStore.setState({
          user: {
            ...user,
            educationSector: selectedSector,
            teachingPhilosophy: style,
          },
        });
      }
      const sectorProfile = getSectorProfile(selectedSector);
      toast.success(
        `Welcome! Set up as ${sectorProfile.label} with ${teachingStyles.find(s => s.id === style)?.name} style.`
      );
      onComplete();
    } catch (error) {
      console.error('Error saving profile:', error);
      toast.error('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  // Step 1: Sector selection
  if (step === 'SECTOR') {
    return (
      <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm'>
        <div className='bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8 relative animate-in fade-in zoom-in duration-300'>
          <button
            onClick={onSkip}
            className='absolute top-4 right-4 text-gray-400 hover:text-gray-600'
          >
            <X className='w-5 h-5' />
          </button>

          <div className='text-center mb-8'>
            <div className='inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 mb-4'>
              <Sparkles className='w-8 h-8 text-purple-600' />
            </div>
            <h2 className='text-2xl font-bold text-gray-900 mb-2'>
              Welcome to Curriculum Curator!
            </h2>
            <p className='text-gray-600'>
              What education sector do you work in? This helps us set sensible
              defaults for labels, structure, and features.
            </p>
          </div>

          <div className='grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mb-6'>
            {sectorCards.map(({ id, icon: Icon }) => {
              const profile = SECTOR_PROFILES[id];
              const isSelected = selectedSector === id;
              return (
                <button
                  key={id}
                  onClick={() => setSelectedSector(id)}
                  className={`text-left p-4 border-2 rounded-xl transition-all ${
                    isSelected
                      ? 'ring-2 ring-purple-500 border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                >
                  <div className='flex items-center gap-3 mb-1'>
                    <div
                      className={`p-2 rounded-lg ${isSelected ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-600'}`}
                    >
                      <Icon className='h-5 w-5' />
                    </div>
                    <span className='font-medium text-gray-900 text-sm'>
                      {profile.label}
                    </span>
                    {isSelected && (
                      <CheckCircle className='h-4 w-4 text-purple-500 ml-auto' />
                    )}
                  </div>
                  <p className='text-xs text-gray-500 ml-12'>
                    {profile.description}
                  </p>
                </button>
              );
            })}
          </div>

          <div className='flex justify-between items-center'>
            <button
              onClick={onSkip}
              className='text-sm text-gray-400 hover:text-gray-600'
            >
              Skip for now
            </button>
            <button
              onClick={() => setStep('STYLE_CHOICE')}
              className='px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2'
            >
              Continue
              <ArrowRight className='w-4 h-4' />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Step 2a: Teaching style choice (quiz or select)
  if (step === 'STYLE_CHOICE') {
    return (
      <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm'>
        <div className='bg-white rounded-2xl shadow-2xl max-w-xl w-full p-8 relative animate-in fade-in zoom-in duration-300'>
          <button
            onClick={onSkip}
            className='absolute top-4 right-4 text-gray-400 hover:text-gray-600'
          >
            <X className='w-5 h-5' />
          </button>

          <div className='text-center mb-8'>
            <div className='inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 mb-4'>
              <Sparkles className='w-8 h-8 text-purple-600' />
            </div>
            <h2 className='text-2xl font-bold text-gray-900 mb-2'>
              Your Teaching Style
            </h2>
            <p className='text-gray-600'>
              Your teaching style helps our AI generate content that matches
              your pedagogical approach.
            </p>
          </div>

          <div className='space-y-4'>
            <button
              onClick={() => setStep('QUIZ')}
              className='w-full p-5 text-left border-2 border-purple-200 rounded-xl hover:border-purple-400 hover:bg-purple-50 transition-all group'
            >
              <div className='flex items-center gap-4'>
                <div className='p-3 rounded-lg bg-purple-100 text-purple-600 group-hover:bg-purple-200'>
                  <Lightbulb className='w-6 h-6' />
                </div>
                <div>
                  <h3 className='font-semibold text-gray-900'>
                    Take a Quick Quiz
                  </h3>
                  <p className='text-sm text-gray-500'>
                    5 questions to discover your teaching style
                  </p>
                </div>
                <ArrowRight className='w-5 h-5 text-gray-400 ml-auto group-hover:text-purple-600' />
              </div>
            </button>

            <button
              onClick={() => setStep('SELECT')}
              className='w-full p-5 text-left border-2 border-gray-200 rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all group'
            >
              <div className='flex items-center gap-4'>
                <div className='p-3 rounded-lg bg-gray-100 text-gray-600 group-hover:bg-gray-200'>
                  <Target className='w-6 h-6' />
                </div>
                <div>
                  <h3 className='font-semibold text-gray-900'>
                    I Know My Style
                  </h3>
                  <p className='text-sm text-gray-500'>
                    Select from common teaching philosophies
                  </p>
                </div>
                <ArrowRight className='w-5 h-5 text-gray-400 ml-auto group-hover:text-gray-600' />
              </div>
            </button>
          </div>

          <div className='flex justify-between items-center mt-6'>
            <button
              onClick={() => setStep('SECTOR')}
              className='text-sm text-gray-500 hover:text-gray-700'
            >
              Back
            </button>
            <button
              onClick={onSkip}
              className='text-sm text-gray-400 hover:text-gray-600'
            >
              Skip for now
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Step 2b: Quiz mode
  if (step === 'QUIZ') {
    const question = questions[currentQuestion];

    return (
      <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm'>
        <div className='bg-white rounded-2xl shadow-2xl max-w-xl w-full p-8 relative animate-in fade-in duration-200'>
          <div className='mb-6'>
            <div className='flex justify-between items-center mb-4'>
              <span className='text-sm font-medium text-purple-600'>
                Question {currentQuestion + 1} of {questions.length}
              </span>
              <button
                onClick={() => {
                  setStep('STYLE_CHOICE');
                  setCurrentQuestion(0);
                  setAnswers({});
                }}
                className='text-sm text-gray-400 hover:text-gray-600'
              >
                Cancel
              </button>
            </div>
            <div className='w-full bg-gray-200 rounded-full h-2'>
              <div
                className='bg-purple-600 h-2 rounded-full transition-all duration-300'
                style={{
                  width: `${((currentQuestion + 1) / questions.length) * 100}%`,
                }}
              />
            </div>
          </div>

          <h3 className='text-xl font-semibold text-gray-900 mb-6'>
            {question.question}
          </h3>

          <div className='space-y-3'>
            {question.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleQuizAnswer(option.value)}
                disabled={saving}
                className='w-full flex items-center p-4 border border-gray-200 rounded-xl hover:bg-purple-50 hover:border-purple-300 transition-colors text-left group disabled:opacity-50'
              >
                <div className='flex-shrink-0 w-5 h-5 rounded-full border border-gray-300 group-hover:border-purple-500 mr-3 flex items-center justify-center'>
                  <div className='w-2.5 h-2.5 rounded-full bg-purple-500 opacity-0 group-hover:opacity-100 transition-opacity' />
                </div>
                <span className='text-gray-700 group-hover:text-gray-900'>
                  {option.label}
                </span>
              </button>
            ))}
          </div>

          {currentQuestion > 0 && (
            <button
              onClick={() => setCurrentQuestion(currentQuestion - 1)}
              className='mt-4 text-sm text-gray-500 hover:text-gray-700'
            >
              Go back
            </button>
          )}
        </div>
      </div>
    );
  }

  // Step 2c: Manual selection mode
  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm overflow-y-auto'>
      <div className='bg-white rounded-2xl shadow-2xl max-w-3xl w-full p-8 relative my-8 animate-in fade-in duration-200'>
        <div className='flex justify-between items-center mb-6'>
          <h2 className='text-xl font-semibold text-gray-900'>
            Select Your Teaching Style
          </h2>
          <button
            onClick={() => setStep('STYLE_CHOICE')}
            className='text-sm text-gray-400 hover:text-gray-600'
          >
            Back
          </button>
        </div>

        <div className='grid gap-3 md:grid-cols-3 mb-6 max-h-[50vh] overflow-y-auto'>
          {teachingStyles.map(style => {
            const Icon = style.icon;
            const isSelected = selectedStyle === style.id;

            return (
              <button
                key={style.id}
                onClick={() => setSelectedStyle(style.id as PedagogyType)}
                className={`text-left p-4 border rounded-xl transition-all ${
                  isSelected
                    ? 'ring-2 ring-purple-500 border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                <div className='flex items-center gap-3 mb-2'>
                  <div className={`p-2 rounded-lg ${style.color} text-white`}>
                    <Icon className='h-4 w-4' />
                  </div>
                  <span className='font-medium text-gray-900 text-sm'>
                    {style.name}
                  </span>
                  {isSelected && (
                    <CheckCircle className='h-4 w-4 text-purple-500 ml-auto' />
                  )}
                </div>
                <p className='text-xs text-gray-500'>{style.description}</p>
              </button>
            );
          })}
        </div>

        <div className='flex justify-end gap-3'>
          <button
            onClick={onSkip}
            className='px-4 py-2 text-gray-600 hover:text-gray-800'
          >
            Skip for now
          </button>
          <button
            onClick={() => saveProfile(selectedStyle)}
            disabled={saving}
            className='px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50'
          >
            {saving ? 'Saving...' : 'Continue'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default WelcomeOnboarding;
