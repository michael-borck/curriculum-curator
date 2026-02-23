import { useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  Target,
  BookOpen,
  Sparkles,
  ArrowRight,
  Upload,
  Brain,
  CheckCircle,
  Globe,
} from 'lucide-react';
import type { LandingProps } from '../../types/index';

const Landing = ({ onSignInClick }: LandingProps) => {
  const navigate = useNavigate();
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Creation',
      description:
        'Generate pedagogically-aligned content with AI that understands your teaching style.',
    },
    {
      icon: Target,
      title: '9 Teaching Styles',
      description:
        'From Traditional to Inquiry-Based - choose the approach that fits your philosophy.',
    },
    {
      icon: BookOpen,
      title: 'Unit Structure',
      description:
        'Plan 12-week units with learning outcomes, weekly materials, and assessments.',
    },
    {
      icon: Upload,
      title: 'Import & Enhance',
      description:
        'Bring existing materials and let AI help improve and align them.',
    },
    {
      icon: CheckCircle,
      title: 'Accreditation Ready',
      description:
        'Map to Graduate Capabilities and AACSB Assurance of Learning standards.',
    },
    {
      icon: Globe,
      title: 'UN Global Goals',
      description:
        'Align your curriculum with the 17 UN Sustainable Development Goals.',
    },
  ];

  return (
    <div className='min-h-screen bg-white'>
      {/* Simple Navigation */}
      <nav className='bg-white px-6 md:px-8 py-4 flex justify-between items-center border-b border-gray-100'>
        <div className='flex items-center gap-2'>
          <GraduationCap className='w-7 h-7 text-purple-600' />
          <span className='text-lg font-bold text-gray-900'>
            Curriculum Curator
          </span>
        </div>
        <div className='flex items-center gap-4'>
          <button
            onClick={() => navigate('/download')}
            className='text-gray-600 hover:text-gray-900 transition-colors font-medium text-sm'
          >
            Install
          </button>
          <button
            onClick={onSignInClick}
            className='bg-purple-600 text-white px-5 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm'
          >
            Sign In
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className='bg-gradient-to-br from-purple-50 via-white to-indigo-50 px-6 md:px-8 py-16 md:py-24'>
        <div className='max-w-4xl mx-auto text-center'>
          <h1 className='text-4xl md:text-5xl font-bold text-gray-900 mb-6 leading-tight'>
            Create Unit Content
            <br />
            <span className='text-purple-600'>That Teaches Your Way</span>
          </h1>
          <p className='text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto'>
            An AI-powered platform for educators. Build pedagogically-aligned
            units with learning outcomes, weekly materials, and assessments.
          </p>
          <button
            onClick={() => navigate('/download')}
            className='bg-purple-600 text-white px-8 py-4 rounded-lg hover:bg-purple-700 transition-colors font-semibold text-lg inline-flex items-center gap-2 shadow-lg shadow-purple-200'
          >
            Get Started
            <ArrowRight className='w-5 h-5' />
          </button>
        </div>
      </section>

      {/* Feature Cards */}
      <section className='px-6 md:px-8 py-16 bg-gray-50'>
        <div className='max-w-5xl mx-auto'>
          <div className='grid sm:grid-cols-2 lg:grid-cols-3 gap-6'>
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className='p-5 bg-white rounded-xl hover:bg-purple-50 transition-colors group border border-gray-100'
                >
                  <div className='w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-3 group-hover:bg-purple-200 transition-colors'>
                    <Icon className='w-5 h-5 text-purple-600' />
                  </div>
                  <h3 className='text-lg font-semibold text-gray-900 mb-2'>
                    {feature.title}
                  </h3>
                  <p className='text-gray-600 text-sm'>{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className='px-6 md:px-8 py-16 bg-purple-600'>
        <div className='max-w-3xl mx-auto text-center text-white'>
          <Sparkles className='w-10 h-10 mx-auto mb-4 opacity-80' />
          <h2 className='text-2xl md:text-3xl font-bold mb-4'>
            Ready to Create Better Unit Content?
          </h2>
          <p className='text-lg opacity-90 mb-8'>
            Join educators using AI to build pedagogically-aligned materials.
          </p>
          <button
            onClick={onSignInClick}
            className='bg-white text-purple-600 px-8 py-4 rounded-lg hover:bg-gray-50 transition-colors font-semibold text-lg inline-flex items-center gap-2'
          >
            Get Started Free
            <ArrowRight className='w-5 h-5' />
          </button>
        </div>
      </section>

      {/* Simple Footer */}
      <footer className='px-6 md:px-8 py-8 bg-gray-900 text-gray-400'>
        <div className='max-w-5xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4'>
          <div className='flex items-center gap-2'>
            <GraduationCap className='w-5 h-5 text-purple-400' />
            <span className='text-sm font-medium text-white'>
              Curriculum Curator
            </span>
          </div>
          <p className='text-sm'>
            Built by educators, for educators. Open source.
          </p>
          <p className='text-sm'>&copy; 2025</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
