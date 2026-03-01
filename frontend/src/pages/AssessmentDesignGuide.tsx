import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ClipboardList,
  ChevronDown,
  ChevronRight,
  Shield,
  GitFork,
  Search,
  Star,
  Grid3X3,
  AlignLeft,
  Layers,
  CheckSquare,
  Scale,
  CheckCircle2,
  ArrowRight,
  AlertTriangle,
  BookOpen,
} from 'lucide-react';

// ── Collapsible section ────────────────────────────────────

interface SectionProps {
  id: string;
  title: string;
  icon: React.ReactNode;
  color: string;
  children: React.ReactNode;
  defaultOpen?: boolean | undefined;
  expanded: Set<string>;
  toggle: (id: string) => void;
}

const Section = ({
  id,
  title,
  icon,
  color,
  children,
  expanded,
  toggle,
}: SectionProps) => {
  const isOpen = expanded.has(id);
  return (
    <div className='bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden'>
      <button
        onClick={() => toggle(id)}
        className='w-full flex items-center gap-3 px-6 py-4 text-left hover:bg-gray-50 transition'
      >
        <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
        <h2 className='flex-1 text-lg font-semibold text-gray-900'>{title}</h2>
        {isOpen ? (
          <ChevronDown className='w-5 h-5 text-gray-400' />
        ) : (
          <ChevronRight className='w-5 h-5 text-gray-400' />
        )}
      </button>
      {isOpen && (
        <div className='px-6 pb-6 border-t border-gray-100 pt-4'>
          {children}
        </div>
      )}
    </div>
  );
};

// ── Section IDs ────────────────────────────────────────────

const ALL_SECTIONS = [
  'principles',
  'spectrum',
  'stress-test',
  'criteria',
  'analytic',
  'single-point',
  'holistic',
  'checklist',
  'choosing',
] as const;

// ── Main component ─────────────────────────────────────────

const AssessmentDesignGuide = () => {
  const [expanded, setExpanded] = useState<Set<string>>(
    new Set(['principles'])
  );

  const toggle = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    setExpanded(new Set([...ALL_SECTIONS]));
  };

  const collapseAll = () => {
    setExpanded(new Set());
  };

  return (
    <div className='max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6'>
      {/* Header */}
      <div className='bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg shadow-lg p-8 text-white'>
        <div className='flex items-center gap-3 mb-4'>
          <ClipboardList className='w-10 h-10' />
          <h1 className='text-3xl font-bold'>Assessment Design Guide</h1>
        </div>
        <p className='text-amber-100 text-lg max-w-2xl'>
          Practical guidance for designing assessments and rubrics in an
          AI-enabled world. Covers integrity-by-design principles, the AI
          integration spectrum, and all four rubric formats.
        </p>
        <div className='mt-4 flex gap-3'>
          <button
            onClick={expandAll}
            className='px-3 py-1.5 text-sm bg-white/20 hover:bg-white/30 rounded-lg transition'
          >
            Expand all sections
          </button>
          <button
            onClick={collapseAll}
            className='px-3 py-1.5 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition'
          >
            Collapse all
          </button>
        </div>
      </div>

      {/* Quick nav */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
        <p className='text-sm font-medium text-gray-500 mb-2'>Jump to:</p>
        <div className='flex flex-wrap gap-2'>
          {[
            { id: 'principles', label: 'Six Principles' },
            { id: 'spectrum', label: 'AI Spectrum' },
            { id: 'stress-test', label: 'Stress-Testing' },
            { id: 'criteria', label: 'AI Criteria' },
            { id: 'analytic', label: 'Analytic Rubric' },
            { id: 'single-point', label: 'Single-Point' },
            { id: 'holistic', label: 'Holistic' },
            { id: 'checklist', label: 'Checklist' },
            { id: 'choosing', label: 'Choosing a Format' },
          ].map(item => (
            <button
              key={item.id}
              onClick={() => {
                if (!expanded.has(item.id)) toggle(item.id);
                document
                  .getElementById(`section-${item.id}`)
                  ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className='px-3 py-1 text-sm bg-gray-100 hover:bg-amber-100 hover:text-amber-700 rounded-full transition'
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Part 1 divider */}
      <div className='flex items-center gap-3 pt-2'>
        <div className='h-px flex-1 bg-gray-300' />
        <span className='text-sm font-semibold text-gray-500 uppercase tracking-wider'>
          Part 1: Assessment in an AI-Enabled World
        </span>
        <div className='h-px flex-1 bg-gray-300' />
      </div>

      {/* Sections */}
      <div className='space-y-4'>
        {/* ── Six Principles ──────────────────────────── */}
        <div id='section-principles'>
          <Section
            id='principles'
            title='Six Principles for AI-Era Assessment'
            icon={<Shield className='w-5 h-5 text-amber-600' />}
            color='bg-amber-100'
            expanded={expanded}
            toggle={toggle}
            defaultOpen
          >
            <p className='text-gray-600 mb-4'>
              These principles guide assessment design when AI tools are
              available to students. Rather than trying to ban AI, design
              assessments that remain meaningful regardless of whether AI is
              used.
            </p>

            <div className='space-y-3 mb-6'>
              {[
                {
                  num: 1,
                  title: 'Design Assuming AI Is Present',
                  desc: 'Assume students have access to AI tools. Design tasks where AI alone cannot produce a passing submission without genuine student engagement.',
                  color: 'bg-amber-50 border-amber-200 text-amber-900',
                },
                {
                  num: 2,
                  title: 'AI Integration Spectrum',
                  desc: 'Position each assessment along a spectrum from AI-restricted to AI-integrated. Let the learning outcomes determine where on the spectrum each task sits.',
                  color: 'bg-orange-50 border-orange-200 text-orange-900',
                },
                {
                  num: 3,
                  title: 'Authentic Assessment',
                  desc: 'Ground tasks in real-world contexts, personal experience, or discipline-specific scenarios that require situated knowledge AI lacks.',
                  color: 'bg-yellow-50 border-yellow-200 text-yellow-900',
                },
                {
                  num: 4,
                  title: 'Explicit AI Use Expectations',
                  desc: 'Clearly state what AI use is permitted, required, or prohibited for each task. Ambiguity undermines integrity and student confidence.',
                  color: 'bg-lime-50 border-lime-200 text-lime-900',
                },
                {
                  num: 5,
                  title: 'Integrity Through Design',
                  desc: 'Build integrity into the task structure itself (process documentation, in-class components, personal reflection) rather than relying solely on detection tools.',
                  color: 'bg-green-50 border-green-200 text-green-900',
                },
                {
                  num: 6,
                  title: 'Sustainability & Inclusion',
                  desc: 'Ensure assessment approaches are sustainable for staff workload and inclusive for students with varied access to AI tools and digital literacy.',
                  color: 'bg-teal-50 border-teal-200 text-teal-900',
                },
              ].map(p => (
                <div
                  key={p.num}
                  className={`flex items-start gap-4 p-3 rounded-lg border ${p.color}`}
                >
                  <span className='text-2xl font-bold opacity-40'>{p.num}</span>
                  <div>
                    <p className='font-semibold'>{p.title}</p>
                    <p className='text-sm opacity-80 mt-1'>{p.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
              <p className='text-sm text-amber-800'>
                <strong>Key insight:</strong> The goal is not to prevent AI use,
                but to design assessments where AI becomes a tool that supports
                &mdash; rather than replaces &mdash; genuine learning. Students
                who use AI well still need to demonstrate critical thinking,
                personal application, and disciplinary understanding.
              </p>
            </div>
          </Section>
        </div>

        {/* ── AI Integration Spectrum ─────────────────── */}
        <div id='section-spectrum'>
          <Section
            id='spectrum'
            title='AI Integration Spectrum by Assessment Type'
            icon={<GitFork className='w-5 h-5 text-orange-600' />}
            color='bg-orange-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Each assessment sits somewhere on a spectrum from AI-restricted
              (where AI use is limited or prohibited) to AI-integrated (where AI
              use is expected and assessed). Learning outcomes should determine
              the appropriate position on this spectrum.
            </p>

            <div className='overflow-x-auto mb-6'>
              <table className='w-full text-sm border-collapse'>
                <thead>
                  <tr className='bg-gray-50'>
                    <th className='border border-gray-200 px-3 py-2 text-left font-semibold text-gray-700'>
                      Assessment Type
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-left font-semibold text-red-700'>
                      AI-Restricted
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-left font-semibold text-green-700'>
                      AI-Integrated
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      type: 'Essays & Reports',
                      restricted:
                        'In-class timed writing, handwritten components, oral defence of written work',
                      enabled:
                        'AI-assisted drafting with reflective commentary on AI contributions, annotated revision logs',
                    },
                    {
                      type: 'Exams',
                      restricted:
                        'Invigilated closed-book exams, oral viva voce, practical demonstrations',
                      enabled:
                        'Open-book with AI access but novel scenario-based questions requiring synthesis and judgement',
                    },
                    {
                      type: 'Group Work',
                      restricted:
                        'In-class collaborative tasks with observed participation, peer evaluation',
                      enabled:
                        'Team projects using AI tools with individual AI-use logs and contribution statements',
                    },
                    {
                      type: 'Presentations',
                      restricted:
                        'Live presentations with Q&A, impromptu follow-up questions',
                      enabled:
                        'AI-assisted slide preparation with live delivery and unscripted audience questions',
                    },
                    {
                      type: 'Portfolios',
                      restricted:
                        'Process portfolios with dated drafts, in-class workshops, reflective journals',
                      enabled:
                        'Curated portfolios with AI-interaction logs showing how AI was used and evaluated',
                    },
                  ].map(row => (
                    <tr key={row.type}>
                      <td className='border border-gray-200 px-3 py-2 font-medium text-gray-900'>
                        {row.type}
                      </td>
                      <td className='border border-gray-200 px-3 py-2 text-gray-600'>
                        {row.restricted}
                      </td>
                      <td className='border border-gray-200 px-3 py-2 text-gray-600'>
                        {row.enabled}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className='bg-orange-50 border border-orange-200 rounded-lg p-4'>
              <p className='text-sm text-orange-800'>
                <strong>Blending modes:</strong> Many effective assessment
                designs combine positions on the spectrum. For example, an
                AI-assisted report (integrated mode) coupled with an in-class
                oral defence (restricted mode) verifies both the quality of the
                output and the student&apos;s understanding of it.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Stress-Testing ─────────────────────────── */}
        <div id='section-stress-test'>
          <Section
            id='stress-test'
            title='Stress-Testing Your Assessments'
            icon={<Search className='w-5 h-5 text-red-600' />}
            color='bg-red-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Before finalising any assessment, run it through these diagnostic
              questions. If you answer &ldquo;yes&rdquo; to any, consider
              redesigning using the pathways below.
            </p>

            <div className='bg-red-50 border border-red-200 rounded-lg p-4 mb-6'>
              <h4 className='font-semibold text-red-800 mb-3'>
                Self-test questions
              </h4>
              <ul className='space-y-2'>
                {[
                  'Could a student paste this prompt into ChatGPT and submit the output with minimal editing?',
                  'Does the task rely on generic knowledge that AI can easily reproduce?',
                  'Is the task purely knowledge recall without application to a specific context?',
                  'Could a student complete this without attending any classes or engaging with course materials?',
                  'Does the marking rubric focus only on the final product with no process evidence?',
                ].map(q => (
                  <li
                    key={q}
                    className='flex items-start gap-2 text-sm text-red-700'
                  >
                    <AlertTriangle className='w-4 h-4 mt-0.5 flex-shrink-0' />
                    {q}
                  </li>
                ))}
              </ul>
            </div>

            <h4 className='font-semibold text-gray-900 mb-3'>
              Three redesign pathways
            </h4>
            <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
              {[
                {
                  title: 'Process Documentation',
                  desc: 'Require students to submit evidence of their working process: drafts, AI-interaction logs, annotated revisions, or version histories.',
                  examples: [
                    'Annotated bibliography with search strategy',
                    'AI prompt log with critical commentary',
                    'Three-draft submission with revision notes',
                  ],
                  color: 'bg-blue-50 border-blue-200',
                  textColor: 'text-blue-800',
                },
                {
                  title: 'In-Class Components',
                  desc: 'Add observed, time-limited components that verify understanding: oral defences, live coding, in-class writing, or practical demonstrations.',
                  examples: [
                    'Viva voce (oral exam) on submitted work',
                    'In-class written reflection under exam conditions',
                    'Live demonstration of project with Q&A',
                  ],
                  color: 'bg-green-50 border-green-200',
                  textColor: 'text-green-800',
                },
                {
                  title: 'Personal Application',
                  desc: 'Ground the task in personal experience, local context, or unique data that AI cannot access or fabricate convincingly.',
                  examples: [
                    'Analyse a workplace scenario from placement',
                    'Apply theory to a self-selected case study',
                    'Reflect on personal growth using specific evidence',
                  ],
                  color: 'bg-purple-50 border-purple-200',
                  textColor: 'text-purple-800',
                },
              ].map(pathway => (
                <div
                  key={pathway.title}
                  className={`rounded-lg p-4 border ${pathway.color}`}
                >
                  <h4
                    className={`font-semibold ${pathway.textColor} mb-2 text-sm`}
                  >
                    {pathway.title}
                  </h4>
                  <p className={`text-xs ${pathway.textColor} opacity-80 mb-3`}>
                    {pathway.desc}
                  </p>
                  <ul
                    className={`text-xs ${pathway.textColor} opacity-70 space-y-1`}
                  >
                    {pathway.examples.map(ex => (
                      <li key={ex} className='flex items-start gap-1.5'>
                        <ArrowRight className='w-3 h-3 mt-0.5 flex-shrink-0' />
                        {ex}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Section>
        </div>
      </div>

      {/* Part 2 divider */}
      <div className='flex items-center gap-3 pt-2'>
        <div className='h-px flex-1 bg-gray-300' />
        <span className='text-sm font-semibold text-gray-500 uppercase tracking-wider'>
          Part 2: Rubric Design
        </span>
        <div className='h-px flex-1 bg-gray-300' />
      </div>

      <div className='space-y-4'>
        {/* ── Five Criteria ──────────────────────────── */}
        <div id='section-criteria'>
          <Section
            id='criteria'
            title='Five Criteria for AI-Integrated Assessment'
            icon={<Star className='w-5 h-5 text-purple-600' />}
            color='bg-purple-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              When assessing work where AI tools are permitted, these five
              criteria capture the skills that matter most. Suggested weights
              indicate relative importance but should be adapted to your
              discipline.
            </p>

            <div className='space-y-3 mb-6'>
              {[
                {
                  criterion: 'Critical Engagement with AI',
                  weight: '25%',
                  desc: 'Evaluates, challenges, and refines AI outputs rather than accepting them uncritically. Shows awareness of AI limitations and biases.',
                  color: 'bg-purple-50 border-purple-200 text-purple-900',
                },
                {
                  criterion: 'Quality of Inquiry',
                  weight: '20%',
                  desc: 'Formulates sophisticated questions and prompts. Demonstrates iterative refinement of AI interactions to achieve deeper understanding.',
                  color: 'bg-blue-50 border-blue-200 text-blue-900',
                },
                {
                  criterion: 'Reflective Practice',
                  weight: '20%',
                  desc: 'Articulates how and why AI was used, what was learned from the process, and how AI interactions shaped thinking.',
                  color: 'bg-green-50 border-green-200 text-green-900',
                },
                {
                  criterion: 'Communication & Synthesis',
                  weight: '20%',
                  desc: 'Integrates AI-generated content with own analysis to produce coherent, well-structured work with a clear authorial voice.',
                  color: 'bg-amber-50 border-amber-200 text-amber-900',
                },
                {
                  criterion: 'Disciplinary Integration',
                  weight: '15%',
                  desc: 'Applies discipline-specific knowledge, methods, and conventions. Uses AI as a tool within professional practice norms.',
                  color: 'bg-rose-50 border-rose-200 text-rose-900',
                },
              ].map(c => (
                <div
                  key={c.criterion}
                  className={`flex items-start gap-4 p-3 rounded-lg border ${c.color}`}
                >
                  <span className='text-lg font-bold opacity-50 min-w-[3rem] text-center'>
                    {c.weight}
                  </span>
                  <div>
                    <p className='font-semibold'>{c.criterion}</p>
                    <p className='text-sm opacity-80 mt-1'>{c.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className='bg-purple-50 border border-purple-200 rounded-lg p-4'>
              <p className='text-sm text-purple-800'>
                <strong>Adapting weights:</strong> These weights suit an
                assignment where AI use is explicitly expected. For tasks with
                restricted AI use, shift weight toward Disciplinary Integration
                and Communication. For reflective tasks, increase Reflective
                Practice.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Analytic Rubric ────────────────────────── */}
        <div id='section-analytic'>
          <Section
            id='analytic'
            title='Analytic Rubric'
            icon={<Grid3X3 className='w-5 h-5 text-blue-600' />}
            color='bg-blue-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              An analytic rubric breaks assessment into separate criteria, each
              with defined performance levels. It provides the most detailed
              feedback but takes longer to complete.
            </p>

            <div className='overflow-x-auto mb-6'>
              <table className='w-full text-xs border-collapse'>
                <thead>
                  <tr className='bg-blue-50'>
                    <th className='border border-gray-200 px-2 py-2 text-left font-semibold text-gray-700 w-28'>
                      Criterion
                    </th>
                    <th className='border border-gray-200 px-2 py-2 text-center font-semibold text-red-700'>
                      Beginning (1)
                    </th>
                    <th className='border border-gray-200 px-2 py-2 text-center font-semibold text-amber-700'>
                      Developing (2)
                    </th>
                    <th className='border border-gray-200 px-2 py-2 text-center font-semibold text-blue-700'>
                      Proficient (3)
                    </th>
                    <th className='border border-gray-200 px-2 py-2 text-center font-semibold text-green-700'>
                      Exemplary (4)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      criterion: 'Critical Engagement',
                      levels: [
                        'Accepts AI output without question',
                        'Identifies some AI limitations but does not address them',
                        'Evaluates and refines AI outputs with supporting evidence',
                        'Systematically challenges AI outputs; demonstrates sophisticated understanding of AI capabilities and limitations',
                      ],
                    },
                    {
                      criterion: 'Quality of Inquiry',
                      levels: [
                        'Uses simple, unrefined prompts',
                        'Shows some prompt iteration but limited depth',
                        'Demonstrates iterative refinement with clear rationale',
                        'Crafts sophisticated, multi-step inquiry strategies that push beyond surface-level AI responses',
                      ],
                    },
                    {
                      criterion: 'Reflective Practice',
                      levels: [
                        'No reflection on AI use',
                        'Describes AI use at surface level',
                        'Analyses how AI shaped thinking and process',
                        'Deep meta-cognitive reflection connecting AI use to learning goals and professional development',
                      ],
                    },
                    {
                      criterion: 'Communication',
                      levels: [
                        'AI-generated text with minimal editing',
                        'Some integration but inconsistent voice',
                        'Well-integrated with clear authorial voice throughout',
                        'Seamless synthesis with distinctive perspective; AI content thoughtfully woven into original analysis',
                      ],
                    },
                    {
                      criterion: 'Disciplinary Integration',
                      levels: [
                        'Generic content lacking disciplinary context',
                        'Some disciplinary terms but superficial application',
                        'Applies disciplinary methods and conventions appropriately',
                        'Advances disciplinary understanding; uses AI as a professional tool within field norms',
                      ],
                    },
                  ].map(row => (
                    <tr key={row.criterion}>
                      <td className='border border-gray-200 px-2 py-2 font-medium text-gray-900'>
                        {row.criterion}
                      </td>
                      {row.levels.map((level, i) => (
                        <td
                          key={i}
                          className='border border-gray-200 px-2 py-2 text-gray-600'
                        >
                          {level}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
                <h4 className='font-semibold text-blue-800 mb-2 text-sm'>
                  Strengths
                </h4>
                <ul className='text-xs text-blue-700 space-y-1'>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Most detailed and transparent feedback
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Clear expectations for each criterion
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Best for high-stakes summative assessment
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Excellent LMS compatibility
                  </li>
                </ul>
              </div>
              <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
                <h4 className='font-semibold text-amber-800 mb-2 text-sm'>
                  Considerations
                </h4>
                <ul className='text-xs text-amber-700 space-y-1'>
                  <li>Slowest to complete &mdash; plan time accordingly</li>
                  <li>Can feel mechanical if descriptors are too rigid</li>
                  <li>Requires well-calibrated level descriptors</li>
                  <li>
                    Works best with 3&ndash;6 criteria; more becomes unwieldy
                  </li>
                </ul>
              </div>
            </div>
          </Section>
        </div>

        {/* ── Single-Point Rubric ────────────────────── */}
        <div id='section-single-point'>
          <Section
            id='single-point'
            title='Single-Point Rubric'
            icon={<AlignLeft className='w-5 h-5 text-green-600' />}
            color='bg-green-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              A single-point rubric describes only the &ldquo;proficient&rdquo;
              level for each criterion. The marker writes specific feedback in
              the &ldquo;not yet&rdquo; and &ldquo;exceeds&rdquo; columns. This
              encourages personalised feedback over checkbox marking.
            </p>

            <div className='overflow-x-auto mb-6'>
              <table className='w-full text-xs border-collapse'>
                <thead>
                  <tr className='bg-green-50'>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-red-700 w-1/3'>
                      Areas for Growth
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-gray-700 w-1/3'>
                      Proficient (Criteria)
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-green-700 w-1/3'>
                      Exceeds Expectations
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    'Critically evaluates and refines AI-generated content with supporting evidence',
                    'Demonstrates iterative prompt refinement with clear rationale for each iteration',
                    'Articulates how AI interactions shaped thinking and connects to learning goals',
                    'Integrates AI content with original analysis in a coherent authorial voice',
                    'Applies disciplinary methods and professional conventions appropriately',
                  ].map(criterion => (
                    <tr key={criterion}>
                      <td className='border border-gray-200 px-3 py-3 text-gray-400 italic text-center'>
                        (Marker writes specific feedback)
                      </td>
                      <td className='border border-gray-200 px-3 py-3 text-gray-700'>
                        {criterion}
                      </td>
                      <td className='border border-gray-200 px-3 py-3 text-gray-400 italic text-center'>
                        (Marker writes specific feedback)
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='bg-green-50 border border-green-200 rounded-lg p-4'>
                <h4 className='font-semibold text-green-800 mb-2 text-sm'>
                  Strengths
                </h4>
                <ul className='text-xs text-green-700 space-y-1'>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Most personalised feedback
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Avoids students targeting specific level descriptors
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Excellent for formative assessment and drafts
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Fastest to create (only one level to describe)
                  </li>
                </ul>
              </div>
              <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
                <h4 className='font-semibold text-amber-800 mb-2 text-sm'>
                  Considerations
                </h4>
                <ul className='text-xs text-amber-700 space-y-1'>
                  <li>
                    Requires experienced markers who can write quality feedback
                  </li>
                  <li>
                    Less structured &mdash; harder to ensure consistency across
                    markers
                  </li>
                  <li>Limited LMS rubric tool support</li>
                  <li>
                    Students may find it less transparent than analytic rubrics
                  </li>
                </ul>
              </div>
            </div>
          </Section>
        </div>

        {/* ── Holistic Rubric ────────────────────────── */}
        <div id='section-holistic'>
          <Section
            id='holistic'
            title='Holistic Rubric'
            icon={<Layers className='w-5 h-5 text-indigo-600' />}
            color='bg-indigo-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              A holistic rubric provides a single paragraph descriptor for each
              grade level, assessing overall quality rather than individual
              criteria. Best when the task requires integrated judgement.
            </p>

            <div className='space-y-3 mb-6'>
              {[
                {
                  grade: 'High Distinction',
                  color: 'bg-green-50 border-green-200 text-green-900',
                  desc: 'Demonstrates sophisticated critical engagement with AI, including systematic evaluation and refinement of outputs. Inquiry is iterative and strategically designed. Reflection shows deep meta-cognitive awareness connecting AI use to professional development. Communication seamlessly integrates AI and original analysis with a distinctive authorial voice. Disciplinary knowledge is applied with nuance, advancing understanding beyond the immediate task.',
                },
                {
                  grade: 'Distinction',
                  color: 'bg-blue-50 border-blue-200 text-blue-900',
                  desc: 'Evaluates and refines AI outputs with supporting evidence. Shows clear prompt iteration strategy with rationale. Reflects analytically on how AI shaped the work. Writing integrates AI content with consistent authorial voice. Applies disciplinary methods and conventions appropriately throughout.',
                },
                {
                  grade: 'Credit',
                  color: 'bg-amber-50 border-amber-200 text-amber-900',
                  desc: 'Identifies some AI limitations and makes corrections. Demonstrates prompt refinement but with inconsistent depth. Describes AI use with some analysis of its impact. Integration of AI and original content is adequate but voice may be uneven. Disciplinary context is present but may be superficial in places.',
                },
                {
                  grade: 'Pass',
                  color: 'bg-orange-50 border-orange-200 text-orange-900',
                  desc: 'Shows minimal critical engagement with AI outputs. Prompts are basic with limited refinement. Reflection is descriptive rather than analytical. AI-generated content is present but poorly integrated with own work. Disciplinary application is limited or generic.',
                },
                {
                  grade: 'Fail',
                  color: 'bg-red-50 border-red-200 text-red-900',
                  desc: 'Accepts AI outputs uncritically with no evidence of evaluation or refinement. No meaningful reflection on AI use or its relationship to learning. Submission appears largely AI-generated with little to no original contribution or disciplinary application.',
                },
              ].map(level => (
                <div
                  key={level.grade}
                  className={`rounded-lg p-4 border ${level.color}`}
                >
                  <h4 className='font-semibold mb-2'>{level.grade}</h4>
                  <p className='text-sm opacity-80'>{level.desc}</p>
                </div>
              ))}
            </div>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='bg-indigo-50 border border-indigo-200 rounded-lg p-4'>
                <h4 className='font-semibold text-indigo-800 mb-2 text-sm'>
                  Strengths
                </h4>
                <ul className='text-xs text-indigo-700 space-y-1'>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Fastest to mark &mdash; one overall judgement
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Assesses integrated performance naturally
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Good for creative or complex tasks
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Aligns with Australian grade descriptors
                  </li>
                </ul>
              </div>
              <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
                <h4 className='font-semibold text-amber-800 mb-2 text-sm'>
                  Considerations
                </h4>
                <ul className='text-xs text-amber-700 space-y-1'>
                  <li>Less specific feedback on individual criteria</li>
                  <li>Harder to explain borderline grades to students</li>
                  <li>
                    Can mask strengths in one area and weaknesses in another
                  </li>
                  <li>Limited LMS rubric tool compatibility</li>
                </ul>
              </div>
            </div>
          </Section>
        </div>

        {/* ── Checklist Rubric ───────────────────────── */}
        <div id='section-checklist'>
          <Section
            id='checklist'
            title='Checklist Rubric'
            icon={<CheckSquare className='w-5 h-5 text-teal-600' />}
            color='bg-teal-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              A checklist rubric uses binary (met / not met) criteria. It&apos;s
              the simplest format, ideal for compliance tasks, technical
              requirements, or formative self-checks.
            </p>

            <div className='overflow-x-auto mb-6'>
              <table className='w-full text-sm border-collapse'>
                <thead>
                  <tr className='bg-teal-50'>
                    <th className='border border-gray-200 px-3 py-2 text-left font-semibold text-gray-700'>
                      Criterion
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-green-700 w-20'>
                      Met
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-red-700 w-20'>
                      Not Met
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    'AI tools used are explicitly identified and cited',
                    'AI-generated content is clearly distinguished from original work',
                    'Critical commentary on AI outputs is included (not just accepted)',
                    'Prompt strategies are documented with rationale',
                    'Reflection addresses what was learned from AI interactions',
                    'Disciplinary conventions and referencing standards are followed',
                    'Final submission demonstrates coherent authorial voice',
                    'Word count / format requirements are met',
                  ].map(item => (
                    <tr key={item}>
                      <td className='border border-gray-200 px-3 py-2 text-gray-700'>
                        {item}
                      </td>
                      <td className='border border-gray-200 px-3 py-2 text-center text-gray-300'>
                        &#9744;
                      </td>
                      <td className='border border-gray-200 px-3 py-2 text-center text-gray-300'>
                        &#9744;
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='bg-teal-50 border border-teal-200 rounded-lg p-4'>
                <h4 className='font-semibold text-teal-800 mb-2 text-sm'>
                  Strengths
                </h4>
                <ul className='text-xs text-teal-700 space-y-1'>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Simplest and fastest to use
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Clear binary expectations
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Excellent for student self-assessment
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-3 h-3 mt-0.5 flex-shrink-0' />
                    Great pre-submission quality gate
                  </li>
                </ul>
              </div>
              <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
                <h4 className='font-semibold text-amber-800 mb-2 text-sm'>
                  Considerations
                </h4>
                <ul className='text-xs text-amber-700 space-y-1'>
                  <li>No quality gradation &mdash; either met or not</li>
                  <li>Not suitable as sole rubric for graded work</li>
                  <li>Doesn&apos;t capture nuance or partial achievement</li>
                  <li>Best combined with another format for summative tasks</li>
                </ul>
              </div>
            </div>
          </Section>
        </div>

        {/* ── Choosing a Format ──────────────────────── */}
        <div id='section-choosing'>
          <Section
            id='choosing'
            title='Choosing the Right Rubric Format'
            icon={<Scale className='w-5 h-5 text-gray-600' />}
            color='bg-gray-200'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              No single rubric format suits every situation. Use this comparison
              to select the right format, or combine formats for a comprehensive
              assessment strategy.
            </p>

            <div className='overflow-x-auto mb-6'>
              <table className='w-full text-xs border-collapse'>
                <thead>
                  <tr className='bg-gray-50'>
                    <th className='border border-gray-200 px-3 py-2 text-left font-semibold text-gray-700'>
                      Factor
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-blue-700'>
                      Analytic
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-green-700'>
                      Single-Point
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-indigo-700'>
                      Holistic
                    </th>
                    <th className='border border-gray-200 px-3 py-2 text-center font-semibold text-teal-700'>
                      Checklist
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      factor: 'Best for',
                      values: [
                        'High-stakes summative',
                        'Formative & drafts',
                        'Creative & integrated tasks',
                        'Compliance & self-check',
                      ],
                    },
                    {
                      factor: 'Feedback richness',
                      values: [
                        'High (per criterion)',
                        'Very high (personalised)',
                        'Moderate (overall)',
                        'Low (binary)',
                      ],
                    },
                    {
                      factor: 'Marking speed',
                      values: ['Slow', 'Moderate', 'Fast', 'Very fast'],
                    },
                    {
                      factor: 'LMS compatibility',
                      values: ['Excellent', 'Limited', 'Limited', 'Good'],
                    },
                    {
                      factor: 'Marker consistency',
                      values: ['High', 'Lower', 'Moderate', 'Very high'],
                    },
                    {
                      factor: 'Setup effort',
                      values: ['High', 'Low', 'Moderate', 'Low'],
                    },
                  ].map(row => (
                    <tr key={row.factor}>
                      <td className='border border-gray-200 px-3 py-2 font-medium text-gray-900'>
                        {row.factor}
                      </td>
                      {row.values.map((val, i) => (
                        <td
                          key={i}
                          className='border border-gray-200 px-3 py-2 text-center text-gray-600'
                        >
                          {val}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className='bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4'>
              <h4 className='font-semibold text-gray-800 mb-2 text-sm'>
                Combining formats
              </h4>
              <p className='text-sm text-gray-600 mb-3'>
                The most effective assessment strategies often combine rubric
                formats:
              </p>
              <ul className='text-sm text-gray-600 space-y-2'>
                <li className='flex items-start gap-2'>
                  <ArrowRight className='w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400' />
                  <span>
                    <strong>Checklist + Analytic:</strong> Use a checklist as a
                    pre-submission gate (student self-check), then an analytic
                    rubric for formal grading.
                  </span>
                </li>
                <li className='flex items-start gap-2'>
                  <ArrowRight className='w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400' />
                  <span>
                    <strong>Single-point + Holistic:</strong> Use a single-point
                    rubric for draft feedback, then a holistic rubric for the
                    final submission grade.
                  </span>
                </li>
                <li className='flex items-start gap-2'>
                  <ArrowRight className='w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400' />
                  <span>
                    <strong>Checklist + Holistic:</strong> Checklist ensures
                    compliance requirements are met; holistic descriptor
                    determines the quality grade.
                  </span>
                </li>
              </ul>
            </div>

            <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
              <p className='text-sm text-amber-800'>
                <strong>In the app:</strong> The rubric editor supports all four
                formats. You can create multiple rubrics per assessment &mdash;
                for example, a checklist for students to self-assess before
                submission, and an analytic rubric for the marking team.
              </p>
            </div>
          </Section>
        </div>
      </div>

      {/* Further Reading */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-2 mb-4'>
          <BookOpen className='w-5 h-5 text-gray-500' />
          <h3 className='font-semibold text-gray-900'>Further Reading</h3>
        </div>
        <ul className='space-y-3 text-sm text-gray-600 mb-6'>
          <li>
            UNESCO (2023).{' '}
            <a
              href='https://unesdoc.unesco.org/ark:/48223/pf0000386693'
              target='_blank'
              rel='noopener noreferrer'
              className='text-amber-600 hover:text-amber-700 underline'
            >
              Guidance for generative AI in education and research
            </a>
            . Paris: UNESCO.
          </li>
          <li>
            UNESCO (2024).{' '}
            <a
              href='https://unesdoc.unesco.org/ark:/48223/pf0000391104'
              target='_blank'
              rel='noopener noreferrer'
              className='text-amber-600 hover:text-amber-700 underline'
            >
              AI competency frameworks for teachers and for school students
            </a>
            . Paris: UNESCO.
          </li>
          <li>
            Bearman, M., Ryan, J. &amp; Ajjawi, R. (2023). Discourses of
            artificial intelligence in higher education.{' '}
            <em>Higher Education</em>, 86, 1227&ndash;1246.
          </li>
          <li>
            TEQSA (2023).{' '}
            <a
              href='https://www.teqsa.gov.au/guides-resources/higher-education-good-practice-hub/assessment-reform-age-artificial-intelligence'
              target='_blank'
              rel='noopener noreferrer'
              className='text-amber-600 hover:text-amber-700 underline'
            >
              Assessment reform for the age of artificial intelligence
            </a>
            . Melbourne: Tertiary Education Quality and Standards Agency.
          </li>
          <li>
            Lodge, J. M., Howard, S., Bearman, M. et al. (2024). Assessment
            reform for the age of artificial intelligence.{' '}
            <em>Assessment &amp; Evaluation in Higher Education</em>, 49(8).
          </li>
        </ul>

        <div className='border-t border-gray-100 pt-4 text-center'>
          <p className='text-sm text-gray-500 mb-2'>
            For foundational curriculum design concepts, see the{' '}
            <Link
              to='/guide/learning-design'
              className='text-amber-600 hover:text-amber-700 underline'
            >
              Learning Design Guide
            </Link>
            .
          </p>
          <p className='text-sm text-gray-500'>
            For content authoring philosophy and the export workflow, see the{' '}
            <Link
              to='/guide/content'
              className='text-amber-600 hover:text-amber-700 underline'
            >
              Content Guide
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
};

export default AssessmentDesignGuide;
