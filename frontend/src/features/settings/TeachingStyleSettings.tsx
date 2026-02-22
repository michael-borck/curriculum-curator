import { useState, useEffect } from 'react';
import {
  Target,
  BookOpen,
  Users,
  Lightbulb,
  Brain,
  Rocket,
  Puzzle,
  FlaskRoundIcon as Flask,
  CheckCircle,
  ArrowRight,
  Sparkles,
  Ban,
  Pencil,
  Wand2,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useTeachingStyleStore } from '../../stores/teachingStyleStore';
import api from '../../services/api';
import toast from 'react-hot-toast';
import type { PedagogyType, AIAssistLevel } from '../../types';

const teachingStyles = [
  {
    id: 'traditional',
    name: 'Traditional',
    icon: BookOpen,
    color: 'bg-blue-500',
    description:
      'Teacher-centered approach with lectures and structured content delivery',
    characteristics: [
      'Direct instruction',
      'Structured lessons',
      'Clear objectives',
      'Assessment-focused',
    ],
  },
  {
    id: 'inquiry-based',
    name: 'Inquiry-Based',
    icon: Lightbulb,
    color: 'bg-yellow-500',
    description: 'Students learn by asking questions and investigating',
    characteristics: [
      'Question-driven',
      'Research skills',
      'Investigation',
      'Self-directed learning',
    ],
  },
  {
    id: 'project-based',
    name: 'Project-Based',
    icon: Target,
    color: 'bg-orange-500',
    description: 'Learning through engaging in real-world projects',
    characteristics: [
      'Hands-on projects',
      'Real-world problems',
      'Collaborative work',
      'Product creation',
    ],
  },
  {
    id: 'collaborative',
    name: 'Collaborative',
    icon: Users,
    color: 'bg-indigo-500',
    description: 'Learning through group work and peer interaction',
    characteristics: [
      'Group projects',
      'Peer teaching',
      'Discussion-based',
      'Shared responsibility',
    ],
  },
  {
    id: 'constructivist',
    name: 'Constructivist',
    icon: Puzzle,
    color: 'bg-green-500',
    description:
      'Students construct knowledge through experience and reflection',
    characteristics: [
      'Discovery learning',
      'Student-centered',
      'Real-world connections',
      'Critical thinking',
    ],
  },
  {
    id: 'experiential',
    name: 'Experiential',
    icon: Flask,
    color: 'bg-red-500',
    description: 'Learning through direct experience and reflection',
    characteristics: [
      'Hands-on experience',
      'Field work',
      'Simulations',
      'Reflective practice',
    ],
  },
  {
    id: 'problem-based',
    name: 'Problem-Based',
    icon: Brain,
    color: 'bg-pink-500',
    description: 'Learning centered around solving complex problems',
    characteristics: [
      'Problem scenarios',
      'Critical analysis',
      'Solution development',
      'Applied learning',
    ],
  },
  {
    id: 'game-based',
    name: 'Game-Based',
    icon: Rocket,
    color: 'bg-purple-500',
    description: 'Learning through games, challenges, and interactive elements',
    characteristics: [
      'Gamification',
      'Challenges & rewards',
      'Interactive engagement',
      'Competition & fun',
    ],
  },
  {
    id: 'competency-based',
    name: 'Competency-Based',
    icon: CheckCircle,
    color: 'bg-teal-500',
    description: 'Focus on mastering specific skills and competencies',
    characteristics: [
      'Skill mastery',
      'Self-paced learning',
      'Clear benchmarks',
      'Practical application',
    ],
  },
];

const questions = [
  {
    id: 0,
    question: 'How do you prefer to introduce new concepts?',
    options: [
      {
        value: 'traditional',
        label: 'Through structured lectures and presentations',
      },
      {
        value: 'constructivist',
        label: 'By letting students explore and discover',
      },
      {
        value: 'inquiry-based',
        label: 'Start with questions and investigations',
      },
      {
        value: 'project-based',
        label: 'Through real-world project contexts',
      },
    ],
  },
  {
    id: 1,
    question: "What's your ideal classroom dynamic?",
    options: [
      {
        value: 'collaborative',
        label: 'Students working in groups and teams',
      },
      {
        value: 'traditional',
        label: 'Teacher leading, students listening and taking notes',
      },
      {
        value: 'project-based',
        label: 'Students working on long-term projects',
      },
      {
        value: 'experiential',
        label: 'Students learning through hands-on activities',
      },
    ],
  },
  {
    id: 2,
    question: 'How do you assess student learning?',
    options: [
      { value: 'traditional', label: 'Tests, quizzes, and exams' },
      {
        value: 'project-based',
        label: 'Project presentations and portfolios',
      },
      { value: 'problem-based', label: 'Problem-solving demonstrations' },
      {
        value: 'competency-based',
        label: 'Skill demonstrations and competency checks',
      },
    ],
  },
  {
    id: 3,
    question: 'What role do you prefer in the classroom?',
    options: [
      {
        value: 'traditional',
        label: 'Expert and primary source of knowledge',
      },
      { value: 'constructivist', label: 'Facilitator and guide' },
      { value: 'collaborative', label: 'Collaborator and co-learner' },
      {
        value: 'inquiry-based',
        label: 'Question prompter and research advisor',
      },
    ],
  },
  {
    id: 4,
    question: 'How do you prefer to structure learning time?',
    options: [
      {
        value: 'game-based',
        label: 'Through challenges, games, and interactive activities',
      },
      { value: 'traditional', label: 'Lecture first, then practice' },
      {
        value: 'experiential',
        label: 'Experience first, then reflect and theorise',
      },
      {
        value: 'problem-based',
        label: 'Present problem, then learn as needed',
      },
    ],
  },
];

type Mode = 'VIEW' | 'QUIZ' | 'SELECT';

const aiLevelOptions: Array<{
  level: AIAssistLevel;
  label: string;
  icon: typeof Ban;
  description: string;
}> = [
  {
    level: 'none',
    label: 'No AI',
    icon: Ban,
    description: 'Manual curriculum builder. Pedagogy tips guide your work.',
  },
  {
    level: 'refine',
    label: 'Correct & Refine',
    icon: Pencil,
    description: 'AI improves and refines your existing text.',
  },
  {
    level: 'create',
    label: 'Create & Generate',
    icon: Wand2,
    description: 'AI creates content guided by your pedagogy.',
  },
];

const TeachingStyleSettings = () => {
  const { user } = useAuthStore();
  const { globalStyle, setGlobalStyle, aiAssistLevel, setAIAssistLevel } =
    useTeachingStyleStore();
  const [mode, setMode] = useState<Mode>('VIEW');
  const [selectedStyle, setSelectedStyle] = useState<PedagogyType>(
    (user?.teachingPhilosophy as PedagogyType) || globalStyle || 'inquiry-based'
  );
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);

  // Sync with user profile on mount
  useEffect(() => {
    if (user?.teachingPhilosophy) {
      setSelectedStyle(user.teachingPhilosophy as PedagogyType);
      setGlobalStyle(user.teachingPhilosophy as PedagogyType);
    }
  }, [user?.teachingPhilosophy, setGlobalStyle]);

  const calculateRecommendedStyle = (): PedagogyType => {
    const styleCounts: Record<string, number> = {};
    Object.values(answers).forEach(style => {
      styleCounts[style] = (styleCounts[style] || 0) + 1;
    });

    const maxCount = Math.max(...Object.values(styleCounts));
    const recommended = Object.entries(styleCounts).find(
      ([, count]) => count === maxCount
    )?.[0];
    return (recommended as PedagogyType) || 'inquiry-based';
  };

  const handleQuizAnswer = (answer: string) => {
    const newAnswers = { ...answers, [currentQuestion]: answer };
    setAnswers(newAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Quiz complete - calculate result
      const recommended = calculateRecommendedStyle();
      setSelectedStyle(recommended);
      setMode('VIEW');
      setCurrentQuestion(0);
      setAnswers({});
      // Auto-save after quiz
      saveTeachingStyle(recommended);
    }
  };

  const saveTeachingStyle = async (style?: PedagogyType) => {
    const styleToSave = style || selectedStyle;
    try {
      setSaving(true);
      await api.patch('/auth/profile', {
        teachingPhilosophy: styleToSave,
      });
      // Update both stores
      setGlobalStyle(styleToSave);
      if (user) {
        useAuthStore.setState({
          user: { ...user, teachingPhilosophy: styleToSave },
        });
      }
      toast.success('Teaching style saved successfully!');
    } catch (error) {
      console.error('Error saving teaching style:', error);
      toast.error('Failed to save teaching style');
    } finally {
      setSaving(false);
    }
  };

  const handleAILevelChange = async (level: AIAssistLevel) => {
    try {
      setSaving(true);
      await api.patch('/auth/profile', {
        teachingPreferences: { aiAssistLevel: level },
      });
      setAIAssistLevel(level);
      if (user) {
        useAuthStore.setState({
          user: {
            ...user,
            teachingPreferences: {
              ...user.teachingPreferences,
              aiAssistLevel: level,
            },
          },
        });
      }
      toast.success(
        level === 'none'
          ? 'AI features disabled'
          : level === 'refine'
            ? 'AI set to refine mode'
            : 'Full AI features enabled'
      );
    } catch (error) {
      console.error('Error saving AI level:', error);
      toast.error('Failed to save AI level');
    } finally {
      setSaving(false);
    }
  };

  const currentStyle = teachingStyles.find(s => s.id === selectedStyle);
  const CurrentIcon = currentStyle?.icon || Sparkles;

  // Quiz Mode
  if (mode === 'QUIZ') {
    const question = questions[currentQuestion];

    return (
      <div className='bg-white rounded-lg shadow-md p-6'>
        <div className='mb-6'>
          <div className='flex justify-between items-center mb-4'>
            <h2 className='text-xl font-semibold'>Teaching Style Quiz</h2>
            <div className='flex items-center gap-4'>
              <span className='text-sm text-gray-600'>
                Question {currentQuestion + 1} of {questions.length}
              </span>
              <button
                onClick={() => {
                  setMode('VIEW');
                  setCurrentQuestion(0);
                  setAnswers({});
                }}
                className='text-sm text-gray-500 hover:text-gray-700'
              >
                Cancel
              </button>
            </div>
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

        <div className='mb-8'>
          <h3 className='text-lg font-medium mb-6'>{question.question}</h3>

          <div className='space-y-3'>
            {question.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleQuizAnswer(option.value)}
                className='w-full flex items-center p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors text-left group'
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
        </div>

        <div className='flex justify-between'>
          <button
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
            disabled={currentQuestion === 0}
            className='px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50'
          >
            Previous
          </button>
          <button
            onClick={() => setMode('SELECT')}
            className='text-sm text-purple-600 hover:text-purple-700'
          >
            Skip quiz - select manually
          </button>
        </div>
      </div>
    );
  }

  // Manual Selection Mode
  if (mode === 'SELECT') {
    return (
      <div className='bg-white rounded-lg shadow-md p-6'>
        <div className='flex justify-between items-center mb-6'>
          <h2 className='text-xl font-semibold'>Select Your Teaching Style</h2>
          <button
            onClick={() => setMode('VIEW')}
            className='text-sm text-gray-500 hover:text-gray-700'
          >
            Cancel
          </button>
        </div>

        <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-6 max-h-[60vh] overflow-y-auto'>
          {teachingStyles.map(style => {
            const Icon = style.icon;
            const isSelected = selectedStyle === style.id;

            return (
              <button
                key={style.id}
                onClick={() => setSelectedStyle(style.id as PedagogyType)}
                className={`text-left p-4 border rounded-lg transition-all ${
                  isSelected
                    ? 'ring-2 ring-purple-500 border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                }`}
              >
                <div className='flex items-start space-x-3 mb-3'>
                  <div className={`p-2 rounded-lg ${style.color} text-white`}>
                    <Icon className='h-5 w-5' />
                  </div>
                  <div className='flex-1'>
                    <h3 className='font-semibold text-gray-900'>
                      {style.name}
                    </h3>
                    <p className='text-xs text-gray-600 mt-1'>
                      {style.description}
                    </p>
                  </div>
                  {isSelected && (
                    <CheckCircle className='h-5 w-5 text-purple-500 flex-shrink-0' />
                  )}
                </div>

                <div className='space-y-1'>
                  {style.characteristics.slice(0, 2).map((char, index) => (
                    <div
                      key={index}
                      className='text-xs text-gray-500 flex items-center'
                    >
                      <span className='w-1 h-1 bg-gray-400 rounded-full mr-2' />
                      {char}
                    </div>
                  ))}
                </div>
              </button>
            );
          })}
        </div>

        <div className='flex justify-end gap-3'>
          <button
            onClick={() => setMode('VIEW')}
            className='px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200'
          >
            Cancel
          </button>
          <button
            onClick={() => {
              saveTeachingStyle();
              setMode('VIEW');
            }}
            disabled={saving}
            className='px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center'
          >
            {saving ? 'Saving...' : 'Save Selection'}
          </button>
        </div>
      </div>
    );
  }

  // View Mode (default)
  return (
    <div className='bg-white rounded-lg shadow-md p-6'>
      <h2 className='text-xl font-semibold mb-2'>Teaching Style</h2>
      <p className='text-gray-600 mb-6'>
        Your teaching philosophy influences how AI generates content for your
        courses.
      </p>

      {/* Current Style Display */}
      <div className='bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 mb-6'>
        <div className='flex items-start gap-4'>
          <div
            className={`p-3 rounded-lg ${currentStyle?.color || 'bg-purple-500'} text-white`}
          >
            <CurrentIcon className='h-6 w-6' />
          </div>
          <div className='flex-1'>
            <h3 className='text-lg font-semibold text-gray-900'>
              {currentStyle?.name || 'Not Set'}
            </h3>
            <p className='text-gray-600 mt-1'>
              {currentStyle?.description ||
                'Take the quiz or select a style to personalise your AI-generated content.'}
            </p>
            {currentStyle && (
              <div className='flex flex-wrap gap-2 mt-3'>
                {currentStyle.characteristics.map((char, index) => (
                  <span
                    key={index}
                    className='px-2 py-1 bg-white rounded text-xs text-gray-600 border border-gray-200'
                  >
                    {char}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className='flex flex-col sm:flex-row gap-4'>
        <button
          onClick={() => setMode('QUIZ')}
          className='flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors'
        >
          <Sparkles className='h-5 w-5' />
          Take the Quiz
        </button>
        <button
          onClick={() => setMode('SELECT')}
          className='flex-1 flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors'
        >
          <ArrowRight className='h-5 w-5' />
          Select Manually
        </button>
      </div>

      {/* AI Assistance Level */}
      <div className='mt-6'>
        <h3 className='text-lg font-semibold mb-3'>AI Assistance Level</h3>
        <div className='grid grid-cols-1 sm:grid-cols-3 gap-3'>
          {aiLevelOptions.map(opt => {
            const Icon = opt.icon;
            const isActive = aiAssistLevel === opt.level;
            return (
              <button
                key={opt.level}
                onClick={() => handleAILevelChange(opt.level)}
                disabled={saving}
                className={`text-left p-4 border rounded-lg transition-all ${
                  isActive
                    ? 'ring-2 ring-purple-500 border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                <div className='flex items-center gap-2 mb-2'>
                  <Icon
                    className={`h-5 w-5 ${isActive ? 'text-purple-600' : 'text-gray-500'}`}
                  />
                  <span
                    className={`font-medium ${isActive ? 'text-purple-900' : 'text-gray-900'}`}
                  >
                    {opt.label}
                  </span>
                </div>
                <p className='text-xs text-gray-600'>{opt.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Info Box — conditional on AI level */}
      <div className='mt-6 bg-blue-50 rounded-lg p-4'>
        {aiAssistLevel === 'none' ? (
          <>
            <h4 className='font-medium text-blue-900 mb-2'>
              How Teaching Style Guides Your Work
            </h4>
            <ul className='space-y-1 text-sm text-blue-800'>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                Pedagogy tips appear in the editor as you write
              </li>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                Expanded guidance for each teaching style in materials
              </li>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                Structure suggestions based on your philosophy
              </li>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                All AI buttons and features are hidden for a clean workspace
              </li>
            </ul>
          </>
        ) : (
          <>
            <h4 className='font-medium text-blue-900 mb-2'>
              How Teaching Style Affects AI Content
            </h4>
            <ul className='space-y-1 text-sm text-blue-800'>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                Content structure and presentation format
              </li>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                Types of activities and exercises generated
              </li>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                Assessment methods and question styles
              </li>
              <li className='flex items-center gap-2'>
                <CheckCircle className='h-4 w-4 text-blue-600' />
                Recommended resources and materials
              </li>
            </ul>
          </>
        )}
      </div>
    </div>
  );
};

export default TeachingStyleSettings;
