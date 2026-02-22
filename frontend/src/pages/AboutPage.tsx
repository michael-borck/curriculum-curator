import {
  GraduationCap,
  BookOpen,
  Shield,
  Globe,
  Pencil,
  Search,
  Award,
  FileOutput,
  FolderKanban,
  Server,
  Monitor,
} from 'lucide-react';

const AboutPage = () => {
  return (
    <div className='max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6'>
      {/* Header */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center'>
        <GraduationCap className='w-16 h-16 text-purple-600 mx-auto mb-4' />
        <h1 className='text-3xl font-bold text-gray-900'>Curriculum Curator</h1>
        <p className='mt-3 text-lg text-gray-600 max-w-2xl mx-auto'>
          You choose how to install it. You choose how to teach with it.
        </p>
        <p className='mt-2 text-sm text-gray-500'>
          Deploy on your institution&apos;s server or run it on your laptop.
          Pick your AI provider or go fully offline. Select from 9 teaching
          philosophies, then build, import, and curate curriculum your way.
        </p>
      </div>

      {/* Overview */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-2 mb-4'>
          <BookOpen className='w-5 h-5 text-purple-600' />
          <h2 className='text-xl font-semibold text-gray-900'>Overview</h2>
        </div>
        <p className='text-gray-700 leading-relaxed'>
          Curriculum Curator is a{' '}
          <strong>content creation tool, not a presentation tool</strong>. It
          helps educators design, structure, and refine unit materials — then
          export them to the LMS or format of their choice. Think of it as the
          workshop where you build your curriculum, not the classroom where you
          deliver it.
        </p>
        <p className='mt-4 text-gray-700'>
          The same philosophy runs through every layer:{' '}
          <strong>you choose</strong>.
        </p>
        <ul className='mt-3 space-y-2 text-gray-700'>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>How to host</strong>: institution VPS, personal Docker, or
              desktop app
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>Which AI</strong>: OpenAI, Anthropic, Gemini, local
              Ollama, or none at all
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>How to teach</strong>: 9 pedagogical styles shape every
              piece of generated content
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>What to export</strong>: IMS Common Cartridge, SCORM, PDF,
              DOCX, PPTX, HTML
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>How much AI help</strong>: full generation, refine-only,
              or write everything yourself
            </span>
          </li>
        </ul>
      </div>

      {/* Two Ways to Run */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-2 mb-4'>
          <Server className='w-5 h-5 text-purple-600' />
          <h2 className='text-xl font-semibold text-gray-900'>
            Two Ways to Run
          </h2>
        </div>
        <div className='overflow-x-auto'>
          <table className='w-full text-sm text-left'>
            <thead>
              <tr className='border-b border-gray-200'>
                <th className='py-3 pr-4 font-semibold text-gray-900'></th>
                <th className='py-3 px-4 font-semibold text-gray-900'>
                  <div className='flex items-center gap-1.5'>
                    <Server className='w-4 h-4' />
                    Institutional Server
                  </div>
                </th>
                <th className='py-3 px-4 font-semibold text-gray-900'>
                  <div className='flex items-center gap-1.5'>
                    <Monitor className='w-4 h-4' />
                    Personal / Desktop
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className='text-gray-700'>
              <tr className='border-b border-gray-100'>
                <td className='py-2.5 pr-4 font-medium'>Who it&apos;s for</td>
                <td className='py-2.5 px-4'>A teaching team or department</td>
                <td className='py-2.5 px-4'>An individual educator</td>
              </tr>
              <tr className='border-b border-gray-100'>
                <td className='py-2.5 pr-4 font-medium'>Deployment</td>
                <td className='py-2.5 px-4'>
                  Docker on your institution&apos;s VPS
                </td>
                <td className='py-2.5 px-4'>
                  Desktop app (Mac, Windows, Linux) or Docker locally
                </td>
              </tr>
              <tr className='border-b border-gray-100'>
                <td className='py-2.5 pr-4 font-medium'>Accounts</td>
                <td className='py-2.5 px-4'>
                  Registration, email verification, whitelist
                </td>
                <td className='py-2.5 px-4'>
                  No login needed (LOCAL_MODE=true)
                </td>
              </tr>
              <tr className='border-b border-gray-100'>
                <td className='py-2.5 pr-4 font-medium'>Security</td>
                <td className='py-2.5 px-4'>
                  JWT auth, rate limiting, account lockout
                </td>
                <td className='py-2.5 px-4'>Single-user, no auth overhead</td>
              </tr>
              <tr className='border-b border-gray-100'>
                <td className='py-2.5 pr-4 font-medium'>AI keys</td>
                <td className='py-2.5 px-4'>Shared keys or BYOK</td>
                <td className='py-2.5 px-4'>
                  Your own keys, or offline with Ollama
                </td>
              </tr>
              <tr>
                <td className='py-2.5 pr-4 font-medium'>Database</td>
                <td className='py-2.5 px-4'>SQLite on the server</td>
                <td className='py-2.5 px-4'>SQLite on your machine</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Privacy-First */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-2 mb-4'>
          <Shield className='w-5 h-5 text-purple-600' />
          <h2 className='text-xl font-semibold text-gray-900'>
            Privacy-First, Bring Your Own Key
          </h2>
        </div>
        <p className='text-gray-700 mb-3'>
          No matter how you deploy, Curriculum Curator never phones home:
        </p>
        <ul className='space-y-2 text-gray-700'>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>BYOK</strong>: Bring your own API keys for OpenAI,
              Anthropic, Google Gemini — or run fully offline with local Ollama
              models
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>No telemetry</strong>: Zero analytics, zero tracking, zero
              external calls beyond the AI provider you choose
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>Data stays with you</strong>: SQLite in a single file you
              control — no cloud database, no vendor lock-in
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <span className='text-purple-500 mt-1'>•</span>
            <span>
              <strong>Air-gapped capable</strong>: Ollama + Local Mode means the
              app works without any internet connection
            </span>
          </li>
        </ul>
      </div>

      {/* Australian Terminology */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-2 mb-4'>
          <Globe className='w-5 h-5 text-purple-600' />
          <h2 className='text-xl font-semibold text-gray-900'>
            Australian University Terminology
          </h2>
        </div>
        <p className='text-gray-700'>
          This application uses Australian university terminology where a{' '}
          <strong>Unit</strong> is an individual subject (e.g.,
          &quot;Programming 101&quot;) and a <strong>Course</strong> is a degree
          program.
        </p>
      </div>

      {/* Key Features */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <h2 className='text-xl font-semibold text-gray-900 mb-6'>
          Key Features
        </h2>

        {/* Content Creation */}
        <div className='mb-6'>
          <div className='flex items-center gap-2 mb-3'>
            <Pencil className='w-4 h-4 text-purple-600' />
            <h3 className='text-lg font-medium text-gray-900'>
              Content Creation &amp; Structuring
            </h3>
          </div>
          <ul className='space-y-1.5 text-gray-700 text-sm'>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>9 Teaching Philosophies</strong>: Traditional,
                Inquiry-Based, Project-Based, Collaborative, Game-Based,
                Flipped, Differentiated, Constructivist, Experiential
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>AI-Powered Content</strong>: Generation, enhancement,
                and scaffolding using multiple LLM providers
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>AI Assistance Levels</strong>: None, refine only, or
                full creation
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Multi-Scale Workflows</strong>: 12-week unit structures,
                weekly modules, or individual materials
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Rich Text Editing</strong>: TipTap-based editor with
                tables, code blocks, and formatting
              </span>
            </li>
          </ul>
        </div>

        {/* Research */}
        <div className='mb-6'>
          <div className='flex items-center gap-2 mb-3'>
            <Search className='w-4 h-4 text-purple-600' />
            <h3 className='text-lg font-medium text-gray-900'>
              Research &amp; Discovery
            </h3>
          </div>
          <ul className='space-y-1.5 text-gray-700 text-sm'>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Tiered Academic Search</strong>: OpenAlex, Semantic
                Scholar, Google CSE, Brave, Tavily, SearXNG
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>URL Import</strong>: Extract content from papers,
                syllabi, or blogs
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>AI Outline Synthesis</strong>: Generate scaffolds from
                research sources
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Propose/Apply Pattern</strong>: AI suggests, you review,
                then commit
              </span>
            </li>
          </ul>
        </div>

        {/* Accreditation */}
        <div className='mb-6'>
          <div className='flex items-center gap-2 mb-3'>
            <Award className='w-4 h-4 text-purple-600' />
            <h3 className='text-lg font-medium text-gray-900'>
              Accreditation &amp; Mapping
            </h3>
          </div>
          <ul className='space-y-1.5 text-gray-700 text-sm'>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Unit Learning Outcomes</strong>: Bloom&apos;s
                taxonomy-aligned with visual mapping
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Graduate Capabilities</strong>: GC1-GC6 mapping to ULOs
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Assurance of Learning</strong>: AACSB competency mapping
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>UN SDG Mapping</strong>: Sustainable Development Goals
                alignment
              </span>
            </li>
          </ul>
        </div>

        {/* Export */}
        <div className='mb-6'>
          <div className='flex items-center gap-2 mb-3'>
            <FileOutput className='w-4 h-4 text-purple-600' />
            <h3 className='text-lg font-medium text-gray-900'>
              Export &amp; Interoperability
            </h3>
          </div>
          <ul className='space-y-1.5 text-gray-700 text-sm'>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>IMS Common Cartridge v1.1</strong> — Moodle, Canvas,
                Blackboard
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>SCORM 1.2</strong> — universal LMS compatibility
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Document Export</strong>: PDF, DOCX, PPTX, HTML
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Round-trip Metadata</strong>: Preserves pedagogy,
                outcomes, and accreditation data
              </span>
            </li>
          </ul>
        </div>

        {/* Unit Management */}
        <div>
          <div className='flex items-center gap-2 mb-3'>
            <FolderKanban className='w-4 h-4 text-purple-600' />
            <h3 className='text-lg font-medium text-gray-900'>
              Unit Management
            </h3>
          </div>
          <ul className='space-y-1.5 text-gray-700 text-sm'>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Soft Delete / Archive</strong>: Remove units with full
                restore capability
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Git-backed Content</strong>: Per-unit version history
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Analytics Dashboard</strong>: Bloom&apos;s coverage,
                assessment distribution, workload visualisation
              </span>
            </li>
            <li className='flex items-start gap-2'>
              <span className='text-purple-500 mt-0.5'>•</span>
              <span>
                <strong>Quality Dashboard</strong>: 6-dimension scoring with
                star ratings and AI-powered suggestions
              </span>
            </li>
          </ul>
        </div>
      </div>

      {/* Version Footer */}
      <div className='text-center text-sm text-gray-400 pb-4'>
        Version {__APP_VERSION__}
      </div>
    </div>
  );
};

export default AboutPage;
