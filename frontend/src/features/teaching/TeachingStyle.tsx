import { useState } from 'react';
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
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import api from '../../services/api';

const teachingStyles = [
  {
    id: 'TRADITIONAL',
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
    id: 'FLIPPED_CLASSROOM',
    name: 'Flipped Classroom',
    icon: Rocket,
    color: 'bg-purple-500',
    description: 'Students learn content at home, practice and apply in class',
    characteristics: [
      'Pre-class preparation',
      'Active in-class learning',
      'Problem-solving focus',
      'Collaborative activities',
    ],
  },
  {
    id: 'CONSTRUCTIVIST',
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
    id: 'PROJECT_BASED',
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
    id: 'INQUIRY_BASED',
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
    id: 'COLLABORATIVE',
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
    id: 'EXPERIENTIAL',
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
    id: 'PROBLEM_BASED',
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
];

const TeachingStyle = () => {
  const { user } = useAuthStore();
  const [selectedStyle, setSelectedStyle] = useState(
    user?.teachingPhilosophy || 'TRADITIONAL'
  );
  const [quizStarted, setQuizStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);

  const questions = [
    {
      id: 0,
      question: 'How do you prefer to introduce new concepts?',
      options: [
        {
          value: 'TRADITIONAL',
          label: 'Through structured lectures and presentations',
        },
        {
          value: 'CONSTRUCTIVIST',
          label: 'By letting students explore and discover',
        },
        {
          value: 'FLIPPED_CLASSROOM',
          label: 'Students read/watch at home, practice in class',
        },
        {
          value: 'INQUIRY_BASED',
          label: 'Start with questions and investigations',
        },
      ],
    },
    {
      id: 1,
      question: "What's your ideal classroom dynamic?",
      options: [
        {
          value: 'COLLABORATIVE',
          label: 'Students working in groups and teams',
        },
        {
          value: 'TRADITIONAL',
          label: 'Teacher leading, students listening and taking notes',
        },
        {
          value: 'PROJECT_BASED',
          label: 'Students working on long-term projects',
        },
        {
          value: 'EXPERIENTIAL',
          label: 'Students learning through hands-on activities',
        },
      ],
    },
    {
      id: 2,
      question: 'How do you assess student learning?',
      options: [
        { value: 'TRADITIONAL', label: 'Tests, quizzes, and exams' },
        {
          value: 'PROJECT_BASED',
          label: 'Project presentations and portfolios',
        },
        { value: 'PROBLEM_BASED', label: 'Problem-solving demonstrations' },
        {
          value: 'CONSTRUCTIVIST',
          label: 'Reflective journals and self-assessment',
        },
      ],
    },
    {
      id: 3,
      question: 'What role do you prefer in the classroom?',
      options: [
        {
          value: 'TRADITIONAL',
          label: 'Expert and primary source of knowledge',
        },
        { value: 'CONSTRUCTIVIST', label: 'Facilitator and guide' },
        { value: 'COLLABORATIVE', label: 'Collaborator and co-learner' },
        {
          value: 'INQUIRY_BASED',
          label: 'Question prompter and research advisor',
        },
      ],
    },
    {
      id: 4,
      question: 'How do you prefer to structure learning time?',
      options: [
        {
          value: 'FLIPPED_CLASSROOM',
          label: 'Content at home, application in class',
        },
        { value: 'TRADITIONAL', label: 'Lecture first, then practice' },
        {
          value: 'EXPERIENTIAL',
          label: 'Experience first, then reflect and theorize',
        },
        {
          value: 'PROBLEM_BASED',
          label: 'Present problem, then learn as needed',
        },
      ],
    },
  ];

  const calculateRecommendedStyle = () => {
    const styleCounts: Record<string, number> = {};
    Object.values(answers).forEach(style => {
      styleCounts[style] = (styleCounts[style] || 0) + 1;
    });

    const maxCount = Math.max(...Object.values(styleCounts));
    const recommended = Object.entries(styleCounts).find(
      ([_, count]) => count === maxCount
    )?.[0];
    return recommended || 'MIXED_APPROACH';
  };

  const saveTeachingStyle = async () => {
    try {
      setSaving(true);
      await api.patch('/auth/profile', {
        teachingPhilosophy: selectedStyle,
      });
      // Update local store
      if (user) {
        const updatedUser = { ...user, teachingPhilosophy: selectedStyle };
        useAuthStore.setState({ user: updatedUser });
      }
    } catch (error) {
      console.error('Error saving teaching style:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleQuizComplete = () => {
    const recommended = calculateRecommendedStyle();
    setSelectedStyle(recommended);
    setQuizStarted(false);
    setCurrentQuestion(0);
    setAnswers({});
  };

  if (quizStarted) {
    return (
      <div className='p-6 max-w-4xl mx-auto'>
        <div className='bg-white rounded-lg shadow-md p-8'>
          <div className='mb-6'>
            <div className='flex justify-between items-center mb-4'>
              <h2 className='text-2xl font-bold'>Teaching Style Quiz</h2>
              <span className='text-sm text-gray-600'>
                Question {currentQuestion + 1} of {questions.length}
              </span>
            </div>
            <div className='w-full bg-gray-200 rounded-full h-2'>
              <div
                className='bg-blue-600 h-2 rounded-full transition-all'
                style={{
                  width: `${((currentQuestion + 1) / questions.length) * 100}%`,
                }}
              />
            </div>
          </div>

          <div className='mb-8'>
            <h3 className='text-xl font-medium mb-6'>
              {questions[currentQuestion].question}
            </h3>

            <div className='space-y-3'>
              {questions[currentQuestion].options.map((option, index) => (
                <label
                  key={index}
                  className='flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer'
                >
                  <input
                    type='radio'
                    name={`question-${currentQuestion}`}
                    value={option.value}
                    checked={answers[currentQuestion] === option.value}
                    onChange={e =>
                      setAnswers({
                        ...answers,
                        [currentQuestion]: e.target.value,
                      })
                    }
                    className='mr-3'
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className='flex justify-between'>
            <button
              onClick={() =>
                setCurrentQuestion(Math.max(0, currentQuestion - 1))
              }
              disabled={currentQuestion === 0}
              className='px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50'
            >
              Previous
            </button>

            {currentQuestion === questions.length - 1 ? (
              <button
                onClick={handleQuizComplete}
                disabled={!answers[currentQuestion]}
                className='px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center'
              >
                <CheckCircle className='h-4 w-4 mr-2' />
                Complete Quiz
              </button>
            ) : (
              <button
                onClick={() => setCurrentQuestion(currentQuestion + 1)}
                disabled={!answers[currentQuestion]}
                className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center'
              >
                Next
                <ArrowRight className='h-4 w-4 ml-2' />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='p-6 max-w-6xl mx-auto'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          Teaching Style
        </h1>
        <p className='text-gray-600'>
          Select your preferred teaching philosophy to customize content
          generation
        </p>
      </div>

      {/* Current Selection */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <div className='flex justify-between items-center mb-4'>
          <h2 className='text-xl font-semibold'>Your Current Teaching Style</h2>
          <button
            onClick={() => setQuizStarted(true)}
            className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700'
          >
            Take Quiz
          </button>
        </div>

        {selectedStyle && (
          <div className='flex items-center space-x-4'>
            {(() => {
              const style = teachingStyles.find(s => s.id === selectedStyle);
              const Icon = style?.icon || BookOpen;
              return (
                <>
                  <div
                    className={`p-3 rounded-lg ${style?.color || 'bg-gray-500'} text-white`}
                  >
                    <Icon className='h-6 w-6' />
                  </div>
                  <div>
                    <h3 className='text-lg font-medium'>
                      {style?.name || 'Mixed Approach'}
                    </h3>
                    <p className='text-gray-600'>
                      {style?.description ||
                        'A combination of teaching methods'}
                    </p>
                  </div>
                </>
              );
            })()}
          </div>
        )}
      </div>

      {/* Teaching Styles Grid */}
      <div className='grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-6'>
        {teachingStyles.map(style => {
          const Icon = style.icon;
          const isSelected = selectedStyle === style.id;

          return (
            <div
              key={style.id}
              onClick={() => setSelectedStyle(style.id)}
              className={`bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all ${
                isSelected ? 'ring-2 ring-blue-500' : 'hover:shadow-lg'
              }`}
            >
              <div className='flex items-start space-x-4 mb-4'>
                <div className={`p-3 rounded-lg ${style.color} text-white`}>
                  <Icon className='h-6 w-6' />
                </div>
                <div className='flex-1'>
                  <h3 className='text-lg font-semibold mb-1'>{style.name}</h3>
                  <p className='text-sm text-gray-600'>{style.description}</p>
                </div>
                {isSelected && (
                  <CheckCircle className='h-5 w-5 text-blue-500' />
                )}
              </div>

              <div className='space-y-2'>
                <h4 className='text-sm font-medium text-gray-700'>
                  Key Characteristics:
                </h4>
                <ul className='space-y-1'>
                  {style.characteristics.map((char, index) => (
                    <li
                      key={index}
                      className='text-sm text-gray-600 flex items-center'
                    >
                      <span className='w-1.5 h-1.5 bg-gray-400 rounded-full mr-2' />
                      {char}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>

      {/* Save Button */}
      <div className='flex justify-end'>
        <button
          onClick={saveTeachingStyle}
          disabled={saving}
          className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
        >
          {saving ? 'Saving...' : 'Save Teaching Style'}
        </button>
      </div>

      {/* Info Section */}
      <div className='mt-8 bg-blue-50 rounded-lg p-6'>
        <h3 className='text-lg font-semibold mb-2'>
          How Teaching Style Affects Content
        </h3>
        <p className='text-gray-700 mb-4'>
          Your selected teaching philosophy influences how AI generates and
          structures educational content:
        </p>
        <ul className='space-y-2 text-gray-700'>
          <li className='flex items-start'>
            <CheckCircle className='h-5 w-5 text-blue-600 mr-2 mt-0.5' />
            <span>Content structure and presentation format</span>
          </li>
          <li className='flex items-start'>
            <CheckCircle className='h-5 w-5 text-blue-600 mr-2 mt-0.5' />
            <span>Types of activities and exercises generated</span>
          </li>
          <li className='flex items-start'>
            <CheckCircle className='h-5 w-5 text-blue-600 mr-2 mt-0.5' />
            <span>Assessment methods and question styles</span>
          </li>
          <li className='flex items-start'>
            <CheckCircle className='h-5 w-5 text-blue-600 mr-2 mt-0.5' />
            <span>Recommended resources and materials</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default TeachingStyle;
