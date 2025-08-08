import {
  GraduationCap,
  Target,
  RotateCcw,
  Bot,
  BookOpen,
  Wand2,
  Play,
  ArrowRight,
} from 'lucide-react';
import type { LandingProps } from '../../types/index';

const Landing = ({ onSignInClick }: LandingProps) => {
  const features = [
    {
      icon: Target,
      title: '9 Teaching Philosophies',
      description:
        'Choose from Traditional, Inquiry-Based, Project-Based, and more. Our AI adapts to your unique teaching style.',
    },
    {
      icon: RotateCcw,
      title: 'Multi-Scale Workflows',
      description:
        'Start from a full syllabus or focus on a single worksheet. Work at the scale that suits your needs.',
    },
    {
      icon: Bot,
      title: 'AI Enhancement',
      description:
        'Intelligent suggestions for content improvement, alignment checks, and automated quality validation.',
    },
    {
      icon: BookOpen,
      title: 'Import & Enhance',
      description:
        'Bring your existing materials. Support for DOCX, PPTX, Markdown, and more with smart remediation.',
    },
    {
      icon: Wand2,
      title: 'Dual Interface',
      description:
        'Wizard mode for guided creation or Expert mode for power users. Choose your comfort level.',
    },
  ];

  return (
    <div className='min-h-screen bg-white'>
      {/* Navigation */}
      <nav className='bg-white px-8 py-6 flex justify-between items-center border-b border-gray-100'>
        <div className='flex items-center gap-3'>
          <GraduationCap className='w-8 h-8 text-purple-600' />
          <span className='text-xl font-bold text-gray-900'>
            Curriculum Curator
          </span>
        </div>
        <div className='flex items-center gap-8'>
          <a
            href='#features'
            className='text-gray-600 hover:text-gray-900 font-medium'
          >
            Features
          </a>
          <a
            href='#pedagogies'
            className='text-gray-600 hover:text-gray-900 font-medium'
          >
            Pedagogies
          </a>
          <a
            href='#about'
            className='text-gray-600 hover:text-gray-900 font-medium'
          >
            About
          </a>
          <button
            onClick={onSignInClick}
            className='bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium'
          >
            Sign In
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className='bg-gradient-to-br from-purple-50 to-indigo-50 px-8 py-20'>
        <div className='max-w-6xl mx-auto text-center'>
          <h1 className='text-5xl font-bold text-gray-900 mb-6 leading-tight'>
            Create Course Content
            <br />
            <span className='text-purple-600'>That Teaches Your Way</span>
          </h1>
          <p className='text-xl text-gray-600 mb-8 max-w-3xl mx-auto'>
            AI-powered platform that aligns with your teaching philosophy. From
            high-level syllabi to individual worksheets, create and curate
            content that resonates with your pedagogical approach.
          </p>
          <div className='flex gap-4 justify-center'>
            <button
              onClick={onSignInClick}
              className='bg-purple-600 text-white px-8 py-4 rounded-lg hover:bg-purple-700 transition-colors font-semibold text-lg flex items-center gap-2'
            >
              Get Started
              <ArrowRight className='w-5 h-5' />
            </button>
            <button className='border border-gray-300 text-gray-700 px-8 py-4 rounded-lg hover:bg-gray-50 transition-colors font-semibold text-lg flex items-center gap-2'>
              <Play className='w-5 h-5' />
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id='features' className='px-8 py-20 bg-white'>
        <div className='max-w-6xl mx-auto'>
          <div className='text-center mb-16'>
            <h2 className='text-3xl font-bold text-gray-900 mb-4'>
              Everything You Need for Pedagogically-Aware Content Creation
            </h2>
            <p className='text-gray-600 text-lg max-w-2xl mx-auto'>
              Our platform adapts to your teaching style, whether you&apos;re a
              traditionalist or an innovator.
            </p>
          </div>

          <div className='grid md:grid-cols-2 lg:grid-cols-3 gap-8'>
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className='p-6 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors'
                >
                  <div className='w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4'>
                    <Icon className='w-6 h-6 text-purple-600' />
                  </div>
                  <h3 className='text-xl font-semibold text-gray-900 mb-3'>
                    {feature.title}
                  </h3>
                  <p className='text-gray-600'>{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pedagogies Section */}
      <section id='pedagogies' className='px-8 py-20 bg-gray-50'>
        <div className='max-w-6xl mx-auto'>
          <div className='text-center mb-16'>
            <h2 className='text-3xl font-bold text-gray-900 mb-4'>
              Nine Teaching Philosophies Supported
            </h2>
            <p className='text-gray-600 text-lg max-w-2xl mx-auto'>
              Our AI understands different pedagogical approaches and tailors
              content generation accordingly.
            </p>
          </div>

          <div className='grid sm:grid-cols-2 lg:grid-cols-3 gap-6'>
            {[
              'Traditional',
              'Inquiry-Based',
              'Project-Based',
              'Collaborative',
              'Game-Based',
              'Constructivist',
              'Problem-Based',
              'Experiential',
              'Competency-Based',
            ].map((pedagogy, index) => (
              <div
                key={index}
                className='bg-white p-6 rounded-lg shadow-sm border border-gray-100'
              >
                <h4 className='font-semibold text-gray-900 mb-2'>{pedagogy}</h4>
                <p className='text-gray-600 text-sm'>
                  Tailored content generation that aligns with{' '}
                  {pedagogy.toLowerCase()} teaching methods.
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className='px-8 py-20 bg-purple-600'>
        <div className='max-w-4xl mx-auto text-center text-white'>
          <h2 className='text-3xl font-bold mb-4'>
            Ready to Transform Your Content Creation?
          </h2>
          <p className='text-xl opacity-90 mb-8'>
            Join educators who are already creating better course materials with
            AI assistance.
          </p>
          <button
            onClick={onSignInClick}
            className='bg-white text-purple-600 px-8 py-4 rounded-lg hover:bg-gray-50 transition-colors font-semibold text-lg inline-flex items-center gap-2'
          >
            Access Platform
            <ArrowRight className='w-5 h-5' />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer id='about' className='px-8 py-12 bg-gray-900 text-gray-300'>
        <div className='max-w-6xl mx-auto'>
          <div className='flex items-center gap-3 mb-6'>
            <GraduationCap className='w-6 h-6 text-purple-400' />
            <span className='text-lg font-bold text-white'>
              Curriculum Curator
            </span>
          </div>
          <div className='grid md:grid-cols-3 gap-8'>
            <div>
              <h4 className='font-semibold text-white mb-3'>Platform</h4>
              <div className='space-y-2'>
                <p>AI-powered content creation</p>
                <p>Multiple pedagogical approaches</p>
                <p>Import and enhance existing materials</p>
              </div>
            </div>
            <div>
              <h4 className='font-semibold text-white mb-3'>For Educators</h4>
              <div className='space-y-2'>
                <p>Lecturers and professors</p>
                <p>Instructional designers</p>
                <p>Training organizations</p>
              </div>
            </div>
            <div>
              <h4 className='font-semibold text-white mb-3'>About</h4>
              <div className='space-y-2'>
                <p>Built by educators, for educators</p>
                <p>Modern tech stack</p>
                <p>Open source approach</p>
              </div>
            </div>
          </div>
          <div className='border-t border-gray-800 mt-8 pt-8 text-center text-sm'>
            <p>&copy; 2025 Curriculum Curator. Made with ❤️ for educators.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
