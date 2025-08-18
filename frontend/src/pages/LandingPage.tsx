import { useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  Target,
  Shuffle,
  Brain,
  Upload,
  Wand2,
  Puzzle,
  ArrowRight,
} from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Target className='w-8 h-8 text-purple-600' />,
      title: '9 Teaching Philosophies',
      description:
        'Choose from Traditional, Inquiry-Based, Project-Based, and more. Our AI adapts to your unique teaching style.',
    },
    {
      icon: <Shuffle className='w-8 h-8 text-purple-600' />,
      title: 'Multi-Scale Workflows',
      description:
        'Start from a full syllabus or focus on a single worksheet. Work at the scale that suits your needs.',
    },
    {
      icon: <Brain className='w-8 h-8 text-purple-600' />,
      title: 'AI Enhancement',
      description:
        'Intelligent suggestions for content improvement, alignment checks, and automated quality validation.',
    },
    {
      icon: <Upload className='w-8 h-8 text-purple-600' />,
      title: 'Import & Enhance',
      description:
        'Bring your existing materials. Support for DOCX, PPTX, Markdown, and more with smart remediation.',
    },
    {
      icon: <Wand2 className='w-8 h-8 text-purple-600' />,
      title: 'Dual Interface',
      description:
        'Wizard mode for guided creation or Expert mode for power users. Choose your comfort level.',
    },
    {
      icon: <Puzzle className='w-8 h-8 text-purple-600' />,
      title: 'Extensible Platform',
      description:
        'Plugin system for custom validators, remediation tools, and workflow extensions.',
    },
  ];

  return (
    <div className='min-h-screen bg-white'>
      {/* Navigation */}
      <nav className='bg-white border-b border-gray-200 sticky top-0 z-50'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
          <div className='flex justify-between h-16'>
            <div className='flex items-center'>
              <GraduationCap className='w-8 h-8 text-purple-600 mr-2' />
              <span className='text-xl font-bold text-gray-900'>
                Curriculum Curator
              </span>
            </div>
            <div className='hidden md:flex items-center space-x-8'>
              <a
                href='#features'
                className='text-gray-600 hover:text-purple-600 transition'
              >
                Features
              </a>
              <a
                href='#pedagogies'
                className='text-gray-600 hover:text-purple-600 transition'
              >
                Pedagogies
              </a>
              <a
                href='#pricing'
                className='text-gray-600 hover:text-purple-600 transition'
              >
                Pricing
              </a>
              <a
                href='#about'
                className='text-gray-600 hover:text-purple-600 transition'
              >
                About
              </a>
              <button
                onClick={() => navigate('/login')}
                className='bg-purple-600 text-white px-5 py-2 rounded-lg hover:bg-purple-700 transition'
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className='bg-gradient-to-br from-purple-50 via-white to-blue-50 py-20'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center'>
          <h1 className='text-5xl font-bold text-gray-900 mb-6'>
            Create Unit Content That{' '}
            <span className='bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent'>
              Teaches Your Way
            </span>
          </h1>
          <p className='text-xl text-gray-600 max-w-3xl mx-auto mb-10'>
            AI-powered platform that aligns with your teaching philosophy. From
            high-level syllabi to individual worksheets, create and curate
            content that resonates with your pedagogical approach.
          </p>
          <div className='flex justify-center gap-4'>
            <button
              onClick={() => navigate('/register')}
              className='bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:shadow-lg transform hover:-translate-y-0.5 transition flex items-center gap-2'
            >
              Start Free Trial <ArrowRight className='w-5 h-5' />
            </button>
            <button className='bg-white text-purple-600 px-8 py-3 rounded-lg font-semibold border-2 border-purple-600 hover:bg-purple-50 transition'>
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id='features' className='py-20 bg-white'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
          <div className='text-center mb-12'>
            <h2 className='text-3xl font-bold text-gray-900 mb-4'>
              Everything You Need to Create Exceptional Content
            </h2>
            <p className='text-lg text-gray-600'>
              Powerful features designed for modern educators
            </p>
          </div>
          <div className='grid md:grid-cols-2 lg:grid-cols-3 gap-8'>
            {features.map((feature, index) => (
              <div
                key={index}
                className='p-6 bg-white border border-gray-200 rounded-xl hover:shadow-lg transition-all hover:-translate-y-1'
              >
                <div className='mb-4'>{feature.icon}</div>
                <h3 className='text-xl font-semibold text-gray-900 mb-2'>
                  {feature.title}
                </h3>
                <p className='text-gray-600'>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className='py-20 bg-gradient-to-r from-purple-600 to-blue-600'>
        <div className='max-w-4xl mx-auto text-center px-4'>
          <h2 className='text-3xl font-bold text-white mb-6'>
            Ready to Transform Your Unit Creation?
          </h2>
          <p className='text-xl text-purple-100 mb-8'>
            Join educators who are saving hours while creating better content
          </p>
          <button
            onClick={() => navigate('/register')}
            className='bg-white text-purple-600 px-8 py-3 rounded-lg font-semibold hover:shadow-lg transform hover:-translate-y-0.5 transition'
          >
            Get Started Free
          </button>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
