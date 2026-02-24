import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Target,
  Layers,
  Brain,
  Users,
  Award,
  BarChart3,
  Lightbulb,
  ArrowRight,
  GraduationCap,
  Eye,
  Ear,
  Hand,
  PenTool,
  CheckCircle2,
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

// ── Bloom's level pill ─────────────────────────────────────

const bloomLevels = [
  {
    level: 1,
    name: 'Remember',
    verbs: 'Define, list, recall, identify, name',
    color: 'bg-red-100 text-red-800 border-red-200',
    description: 'Retrieve relevant knowledge from long-term memory',
  },
  {
    level: 2,
    name: 'Understand',
    verbs: 'Explain, summarise, classify, compare, interpret',
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    description: 'Construct meaning from instructional messages',
  },
  {
    level: 3,
    name: 'Apply',
    verbs: 'Implement, solve, use, demonstrate, execute',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    description: 'Carry out a procedure in a given situation',
  },
  {
    level: 4,
    name: 'Analyse',
    verbs: 'Compare, contrast, examine, differentiate, organise',
    color: 'bg-green-100 text-green-800 border-green-200',
    description: 'Break material into parts, determine relationships',
  },
  {
    level: 5,
    name: 'Evaluate',
    verbs: 'Critique, justify, assess, judge, defend',
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    description: 'Make judgements based on criteria and standards',
  },
  {
    level: 6,
    name: 'Create',
    verbs: 'Design, construct, develop, produce, formulate',
    color: 'bg-purple-100 text-purple-800 border-purple-200',
    description: 'Put elements together to form a novel, coherent whole',
  },
];

// ── Main component ─────────────────────────────────────────

const LearningDesignGuide = () => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['overview']));

  const toggle = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    setExpanded(
      new Set([
        'overview',
        'alignment',
        'blooms',
        'udl',
        'outcomes',
        'assessment',
        'sessions',
        'accreditation',
        'pedagogy',
        'glossary',
      ])
    );
  };

  const collapseAll = () => {
    setExpanded(new Set());
  };

  return (
    <div className='max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6'>
      {/* Header */}
      <div className='bg-gradient-to-br from-purple-600 to-indigo-700 rounded-lg shadow-lg p-8 text-white'>
        <div className='flex items-center gap-3 mb-4'>
          <BookOpen className='w-10 h-10' />
          <h1 className='text-3xl font-bold'>Learning Design Guide</h1>
        </div>
        <p className='text-purple-100 text-lg max-w-2xl'>
          A practical guide to curriculum design concepts. Whether you&apos;re
          new to teaching or an experienced academic, this guide explains the
          frameworks that underpin good unit design.
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
            { id: 'overview', label: 'Overview' },
            { id: 'alignment', label: 'Constructive Alignment' },
            { id: 'blooms', label: "Bloom's Taxonomy" },
            { id: 'udl', label: 'Universal Design' },
            { id: 'outcomes', label: 'Learning Outcomes' },
            { id: 'assessment', label: 'Assessment' },
            { id: 'sessions', label: 'Session Design' },
            { id: 'accreditation', label: 'Accreditation' },
            { id: 'pedagogy', label: 'Teaching Approaches' },
            { id: 'glossary', label: 'Glossary' },
          ].map(item => (
            <button
              key={item.id}
              onClick={() => {
                if (!expanded.has(item.id)) toggle(item.id);
                document
                  .getElementById(`section-${item.id}`)
                  ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className='px-3 py-1 text-sm bg-gray-100 hover:bg-purple-100 hover:text-purple-700 rounded-full transition'
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Sections */}
      <div className='space-y-4'>
        {/* ── Overview ──────────────────────────────── */}
        <div id='section-overview'>
          <Section
            id='overview'
            title='The Big Picture'
            icon={<Layers className='w-5 h-5 text-purple-600' />}
            color='bg-purple-100'
            expanded={expanded}
            toggle={toggle}
            defaultOpen
          >
            <p className='text-gray-600 mb-4'>
              Good curriculum design isn&apos;t about creating content in
              isolation. It&apos;s about aligning five layers so they reinforce
              each other:
            </p>

            {/* Five-layer visual */}
            <div className='space-y-2 mb-6'>
              {[
                {
                  layer: 5,
                  title: 'Accreditation & External Alignment',
                  desc: 'PLOs, Graduate Capabilities, AoL, SDGs',
                  color: 'bg-indigo-50 border-indigo-200 text-indigo-900',
                },
                {
                  layer: 4,
                  title: 'Unit Learning Outcomes (ULOs)',
                  desc: 'What students will be able to DO',
                  color: 'bg-blue-50 border-blue-200 text-blue-900',
                },
                {
                  layer: 3,
                  title: 'Assessment Design',
                  desc: 'How we MEASURE achievement',
                  color: 'bg-green-50 border-green-200 text-green-900',
                },
                {
                  layer: 2,
                  title: 'Teaching & Learning Activities',
                  desc: 'How we TEACH so students can achieve',
                  color: 'bg-yellow-50 border-yellow-200 text-yellow-900',
                },
                {
                  layer: 1,
                  title: 'Universal Design for Learning',
                  desc: 'Making it ACCESSIBLE to all learners',
                  color: 'bg-orange-50 border-orange-200 text-orange-900',
                },
              ].map(l => (
                <div
                  key={l.layer}
                  className={`flex items-center gap-4 p-3 rounded-lg border ${l.color}`}
                >
                  <span className='text-2xl font-bold opacity-40'>
                    {l.layer}
                  </span>
                  <div>
                    <p className='font-semibold'>{l.title}</p>
                    <p className='text-sm opacity-80'>{l.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className='bg-purple-50 border border-purple-200 rounded-lg p-4'>
              <p className='text-sm text-purple-800'>
                <strong>Curriculum Curator&apos;s approach:</strong> Start with
                your learning outcomes (Layer 4), align assessments and
                activities to them (Layers 3 &amp; 2), then map upward to
                accreditation requirements (Layer 5). UDL principles (Layer 1)
                are woven throughout by encouraging varied content formats and
                delivery modes.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Constructive Alignment ────────────────── */}
        <div id='section-alignment'>
          <Section
            id='alignment'
            title='Constructive Alignment'
            icon={<Target className='w-5 h-5 text-blue-600' />}
            color='bg-blue-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Constructive alignment (Biggs &amp; Tang, 2011) is the single most
              important concept in curriculum design. It means three things must
              align:
            </p>

            <div className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
              {[
                {
                  title: 'Learning Outcomes',
                  desc: 'What students should be able to do after completing the unit',
                  icon: <Target className='w-6 h-6 text-blue-600' />,
                  where: 'ULOs tab',
                },
                {
                  title: 'Teaching Activities',
                  desc: 'Learning experiences that help students practise and develop',
                  icon: <Users className='w-6 h-6 text-green-600' />,
                  where: 'Weekly structure',
                },
                {
                  title: 'Assessment Tasks',
                  desc: 'How students demonstrate they have achieved the outcomes',
                  icon: <BarChart3 className='w-6 h-6 text-amber-600' />,
                  where: 'Assessments tab',
                },
              ].map(item => (
                <div
                  key={item.title}
                  className='bg-gray-50 rounded-lg p-4 border border-gray-200'
                >
                  <div className='flex items-center gap-2 mb-2'>
                    {item.icon}
                    <h4 className='font-semibold text-gray-900'>
                      {item.title}
                    </h4>
                  </div>
                  <p className='text-sm text-gray-600 mb-2'>{item.desc}</p>
                  <p className='text-xs text-purple-600 font-medium'>
                    In the app: {item.where}
                  </p>
                </div>
              ))}
            </div>

            {/* Alignment flow */}
            <div className='flex items-center justify-center gap-2 text-sm text-gray-500 mb-4'>
              <span className='font-medium text-blue-700'>Outcomes</span>
              <ArrowRight className='w-4 h-4' />
              <span className='font-medium text-green-700'>Activities</span>
              <ArrowRight className='w-4 h-4' />
              <span className='font-medium text-amber-700'>Assessment</span>
            </div>

            <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
              <p className='text-sm text-blue-800'>
                <strong>How the app helps:</strong> The quality score checks
                that every ULO is assessed by at least one summative assessment,
                and that weekly materials link to relevant ULOs. Gaps are
                flagged in the Quality tab.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Bloom's Taxonomy ──────────────────────── */}
        <div id='section-blooms'>
          <Section
            id='blooms'
            title="Bloom's Taxonomy (Revised)"
            icon={<Brain className='w-5 h-5 text-green-600' />}
            color='bg-green-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Bloom&apos;s taxonomy classifies cognitive skills into six levels,
              from simple recall to complex creation. Use it to write learning
              outcomes at the right level of challenge, and to design
              assessments that actually measure the intended cognitive skill.
            </p>

            <div className='space-y-2 mb-6'>
              {bloomLevels.map(b => (
                <div
                  key={b.level}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${b.color}`}
                >
                  <span className='text-lg font-bold opacity-60 min-w-[2rem] text-center'>
                    L{b.level}
                  </span>
                  <div className='flex-1'>
                    <div className='flex items-baseline gap-2'>
                      <h4 className='font-semibold'>{b.name}</h4>
                      <span className='text-xs opacity-70'>
                        {b.description}
                      </span>
                    </div>
                    <p className='text-sm mt-1'>
                      <span className='font-medium'>Action verbs: </span>
                      {b.verbs}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='bg-green-50 border border-green-200 rounded-lg p-4'>
                <h4 className='font-semibold text-green-800 mb-2'>
                  Writing good ULOs
                </h4>
                <ul className='text-sm text-green-700 space-y-1'>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                    Start with an action verb from the target Bloom&apos;s level
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                    Be specific about the context or conditions
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                    Make it measurable &mdash; how will you know they achieved
                    it?
                  </li>
                  <li className='flex items-start gap-2'>
                    <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                    Aim for 4&ndash;8 ULOs per unit (more becomes unmanageable)
                  </li>
                </ul>
              </div>
              <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
                <h4 className='font-semibold text-amber-800 mb-2'>
                  Common mistakes
                </h4>
                <ul className='text-sm text-amber-700 space-y-1'>
                  <li>
                    &ldquo;Understand X&rdquo; &mdash; too vague, how do you
                    assess understanding?
                  </li>
                  <li>
                    &ldquo;Know about X&rdquo; &mdash; not an action verb, not
                    measurable
                  </li>
                  <li>
                    All ULOs at the same Bloom&apos;s level &mdash; aim for a
                    range
                  </li>
                  <li>
                    20+ ULOs &mdash; too many to align and assess meaningfully
                  </li>
                </ul>
              </div>
            </div>

            <div className='bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4'>
              <p className='text-sm text-gray-600'>
                <strong>In the app:</strong> When you write a ULO, the system
                automatically detects the Bloom&apos;s level from the action
                verb. You can override it if needed. The detected level helps
                with quality scoring and AI-suggested accreditation mappings.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Universal Design for Learning ─────────── */}
        <div id='section-udl'>
          <Section
            id='udl'
            title='Universal Design for Learning (UDL)'
            icon={<Users className='w-5 h-5 text-orange-600' />}
            color='bg-orange-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              UDL (CAST, 2018) is a framework for designing learning experiences
              that work for <strong>all</strong> learners, not just the
              &ldquo;average&rdquo; student. Rather than retrofitting
              accommodations, UDL builds flexibility in from the start.
            </p>

            <div className='bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4'>
              <p className='text-sm text-orange-800'>
                <strong>Important terminology:</strong> Modern evidence-based
                practice uses <strong>learning modalities</strong> (visual,
                auditory, read/write, kinaesthetic) &mdash; varied presentation
                modes that benefit all learners. The older term &ldquo;learning
                styles&rdquo; (the idea that each student has a fixed preferred
                style) has been <strong>debunked by research</strong>. We design
                for <em>multimodal delivery</em>, not personalised style
                matching.
              </p>
            </div>

            <div className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
              {[
                {
                  title: 'Multiple Means of Engagement',
                  desc: 'The WHY of learning. Offer choices in how students engage with material and stay motivated.',
                  icon: <Lightbulb className='w-6 h-6 text-orange-600' />,
                  examples: [
                    'Varied session formats (lecture, lab, workshop)',
                    'Choice of pedagogy (inquiry, collaborative, experiential)',
                    'Pre/in/post-class structure gives varied entry points',
                  ],
                },
                {
                  title: 'Multiple Means of Representation',
                  desc: 'The WHAT of learning. Present information in different modalities and formats.',
                  icon: <Eye className='w-6 h-6 text-blue-600' />,
                  examples: [
                    'Slides, notes, video, readings for the same topic',
                    'Visual diagrams alongside written explanations',
                    'Case studies providing real-world context',
                  ],
                },
                {
                  title: 'Multiple Means of Action & Expression',
                  desc: 'The HOW of learning. Let students demonstrate knowledge in different ways.',
                  icon: <PenTool className='w-6 h-6 text-green-600' />,
                  examples: [
                    'Mix of assessment types (quiz, project, presentation)',
                    'Formative activities alongside summative tasks',
                    'Worksheets, discussions, and hands-on activities',
                  ],
                },
              ].map(principle => (
                <div
                  key={principle.title}
                  className='bg-gray-50 rounded-lg p-4 border border-gray-200'
                >
                  <div className='flex items-center gap-2 mb-2'>
                    {principle.icon}
                    <h4 className='font-semibold text-gray-900 text-sm'>
                      {principle.title}
                    </h4>
                  </div>
                  <p className='text-xs text-gray-600 mb-3'>{principle.desc}</p>
                  <ul className='text-xs text-gray-500 space-y-1'>
                    {principle.examples.map(ex => (
                      <li key={ex} className='flex items-start gap-1.5'>
                        <CheckCircle2 className='w-3 h-3 mt-0.5 text-green-500 flex-shrink-0' />
                        {ex}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <div className='bg-gray-50 border border-gray-200 rounded-lg p-4'>
              <p className='text-sm text-gray-600'>
                <strong>In the app:</strong> UDL isn&apos;t a separate checkbox
                &mdash; the app encourages it naturally. When you build a week
                with varied content types (slides + reading + activity), use
                pre/in/post-class phases, and mix assessment formats,
                you&apos;re applying UDL principles. The quality score rewards
                this variety.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Learning Outcomes Hierarchy ───────────── */}
        <div id='section-outcomes'>
          <Section
            id='outcomes'
            title='Learning Outcomes Hierarchy'
            icon={<Target className='w-5 h-5 text-indigo-600' />}
            color='bg-indigo-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Outcomes exist at multiple levels, each getting more specific.
              Think of it as a zoom: program → unit → week → session.
            </p>

            <div className='space-y-3 mb-6'>
              {[
                {
                  level: 'Program Learning Outcomes (PLOs)',
                  scope: 'Whole degree program',
                  desc: 'What graduates of the entire program can do. Set by the program coordinator. A single unit typically addresses 2-5 of 8-12 PLOs.',
                  example:
                    '"Graduates will apply advanced knowledge of computing to solve real-world problems"',
                  appNote:
                    'Optional mapping — add relevant PLOs to your unit and link them to ULOs',
                },
                {
                  level: 'Unit Learning Outcomes (ULOs)',
                  scope: 'Single unit (subject)',
                  desc: "What students will be able to do after completing this unit. The core of constructive alignment. Written with Bloom's taxonomy verbs.",
                  example:
                    '"Analyse competing design patterns and justify selection for a given scenario" (Bloom\'s L4)',
                  appNote: 'Outcomes tab — the primary anchor for alignment',
                },
                {
                  level: 'Local Learning Outcomes (LOs)',
                  scope: 'Weekly material / session',
                  desc: 'Session-level objectives that break a ULO into achievable weekly steps. Typically 2-4 per session.',
                  example:
                    '"By the end of this lab, identify three common design patterns in the provided codebase"',
                  appNote:
                    'Set on individual materials within weekly structure',
                },
              ].map(o => (
                <div
                  key={o.level}
                  className='bg-gray-50 rounded-lg p-4 border border-gray-200'
                >
                  <div className='flex items-baseline gap-2 mb-1'>
                    <h4 className='font-semibold text-gray-900'>{o.level}</h4>
                    <span className='text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full'>
                      {o.scope}
                    </span>
                  </div>
                  <p className='text-sm text-gray-600 mb-2'>{o.desc}</p>
                  <p className='text-sm text-gray-500 italic mb-2'>
                    {o.example}
                  </p>
                  <p className='text-xs text-purple-600 font-medium'>
                    In the app: {o.appNote}
                  </p>
                </div>
              ))}
            </div>

            <div className='flex items-center justify-center gap-2 text-sm text-gray-400 mb-2'>
              <span className='font-medium text-indigo-600'>PLOs</span>
              <ArrowRight className='w-4 h-4' />
              <span className='font-medium text-blue-600'>ULOs</span>
              <ArrowRight className='w-4 h-4' />
              <span className='font-medium text-green-600'>Local Outcomes</span>
            </div>
            <p className='text-xs text-center text-gray-400'>
              Each level traces back to the one above
            </p>
          </Section>
        </div>

        {/* ── Assessment Design ─────────────────────── */}
        <div id='section-assessment'>
          <Section
            id='assessment'
            title='Assessment Design'
            icon={<BarChart3 className='w-5 h-5 text-amber-600' />}
            color='bg-amber-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Assessment is how you determine whether students have achieved the
              learning outcomes. Good assessment design balances formative
              feedback with summative measurement.
            </p>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-4 mb-6'>
              <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
                <h4 className='font-semibold text-blue-800 mb-2'>
                  Formative Assessment
                </h4>
                <p className='text-sm text-blue-700 mb-2'>
                  Low-stakes, feedback-focused. Helps students (and you)
                  understand progress <em>during</em> learning.
                </p>
                <ul className='text-sm text-blue-600 space-y-1'>
                  <li>Weekly quizzes</li>
                  <li>Discussion participation</li>
                  <li>Draft submissions with feedback</li>
                  <li>Peer review exercises</li>
                  <li>In-class polling / concept checks</li>
                </ul>
              </div>
              <div className='bg-green-50 border border-green-200 rounded-lg p-4'>
                <h4 className='font-semibold text-green-800 mb-2'>
                  Summative Assessment
                </h4>
                <p className='text-sm text-green-700 mb-2'>
                  Higher-stakes, contributes to the final grade. Measures
                  achievement <em>after</em> learning.
                </p>
                <ul className='text-sm text-green-600 space-y-1'>
                  <li>Exams (mid-semester, final)</li>
                  <li>Major projects or portfolios</li>
                  <li>Research papers</li>
                  <li>Presentations</li>
                  <li>Lab reports</li>
                </ul>
              </div>
            </div>

            <div className='bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4'>
              <h4 className='font-semibold text-amber-800 mb-2'>
                Alignment checklist
              </h4>
              <ul className='text-sm text-amber-700 space-y-1'>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                  Every ULO is assessed by at least one summative task
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                  Assessment weights total exactly 100%
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                  Bloom&apos;s level of the assessment matches the ULO it
                  measures (don&apos;t assess &ldquo;Create&rdquo; with a
                  multiple-choice quiz)
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                  Formative tasks prepare students for related summative tasks
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0' />
                  Assessment is spread across the semester, not bunched at the
                  end
                </li>
              </ul>
            </div>

            <div className='bg-gray-50 border border-gray-200 rounded-lg p-4'>
              <p className='text-sm text-gray-600'>
                <strong>In the app:</strong> The Assessments tab lets you create
                formative and summative tasks, set weights, link them to ULOs,
                and define rubric criteria. The quality score checks alignment
                and weight totals automatically.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Session Design ────────────────────────── */}
        <div id='section-sessions'>
          <Section
            id='sessions'
            title='Session Design: Pre / In / Post'
            icon={<Layers className='w-5 h-5 text-teal-600' />}
            color='bg-teal-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Each teaching week has three phases. Designing with these phases
              in mind creates a complete learning cycle, regardless of your
              teaching approach.
            </p>

            <div className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
              {[
                {
                  phase: 'Pre-class',
                  desc: 'Preparation before the session. Students come ready to engage.',
                  examples: [
                    'Readings (textbook chapters, articles)',
                    'Introductory videos',
                    'Pre-class quiz to check prior knowledge',
                  ],
                  color: 'bg-sky-50 border-sky-200',
                  textColor: 'text-sky-800',
                },
                {
                  phase: 'In-class',
                  desc: 'Active learning during the session. Where deeper understanding happens.',
                  examples: [
                    'Lectures (with interactive elements)',
                    'Workshops and lab exercises',
                    'Group discussions and activities',
                  ],
                  color: 'bg-emerald-50 border-emerald-200',
                  textColor: 'text-emerald-800',
                },
                {
                  phase: 'Post-class',
                  desc: 'Consolidation after the session. Students integrate and extend learning.',
                  examples: [
                    'Reflection journals',
                    'Practice worksheets',
                    'Follow-up discussion forums',
                  ],
                  color: 'bg-violet-50 border-violet-200',
                  textColor: 'text-violet-800',
                },
              ].map(p => (
                <div
                  key={p.phase}
                  className={`rounded-lg p-4 border ${p.color}`}
                >
                  <h4 className={`font-semibold ${p.textColor} mb-2`}>
                    {p.phase}
                  </h4>
                  <p className={`text-sm ${p.textColor} opacity-80 mb-3`}>
                    {p.desc}
                  </p>
                  <ul className={`text-sm ${p.textColor} opacity-70 space-y-1`}>
                    {p.examples.map(ex => (
                      <li key={ex} className='flex items-start gap-1.5'>
                        <ArrowRight className='w-3 h-3 mt-0.5 flex-shrink-0' />
                        {ex}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <div className='bg-teal-50 border border-teal-200 rounded-lg p-4'>
              <p className='text-sm text-teal-800'>
                <strong>Flipped classroom tip:</strong> In a flipped approach,
                content delivery (lectures, readings) moves to pre-class, and
                in-class time is freed for active learning (problem-solving,
                discussion, labs). The app&apos;s material categories make this
                structure explicit.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Accreditation ─────────────────────────── */}
        <div id='section-accreditation'>
          <Section
            id='accreditation'
            title='Accreditation Mapping'
            icon={<Award className='w-5 h-5 text-rose-600' />}
            color='bg-rose-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Accreditation mapping demonstrates that your unit contributes to
              broader institutional and professional goals. Not all frameworks
              apply to every unit &mdash; use what&apos;s relevant to your
              context.
            </p>

            <div className='space-y-3 mb-6'>
              {[
                {
                  title: 'Program Learning Outcomes (PLOs)',
                  desc: 'Degree-level outcomes set by your program coordinator. You select the subset your unit addresses and link them to your ULOs.',
                  when: 'Units within a formal degree program',
                  icon: <GraduationCap className='w-5 h-5 text-indigo-600' />,
                },
                {
                  title: 'Graduate Capabilities (GCs)',
                  desc: 'Institution-wide attributes all graduates should demonstrate (e.g. critical thinking, communication, cultural competence).',
                  when: 'Most units within degree programs',
                  icon: <Award className='w-5 h-5 text-blue-600' />,
                },
                {
                  title: 'AACSB Assurance of Learning (AoL)',
                  desc: 'Business school accreditation competencies with three progression levels: Introduce, Reinforce, Master.',
                  when: 'Business school units under AACSB accreditation',
                  icon: <BarChart3 className='w-5 h-5 text-purple-600' />,
                },
                {
                  title: 'UN Sustainable Development Goals (SDGs)',
                  desc: 'The 17 global goals for sustainable development. Map your unit to relevant SDGs for sustainability reporting.',
                  when: 'Any unit — increasingly expected across disciplines',
                  icon: <Users className='w-5 h-5 text-green-600' />,
                },
              ].map(f => (
                <div
                  key={f.title}
                  className='flex items-start gap-3 bg-gray-50 rounded-lg p-4 border border-gray-200'
                >
                  <div className='mt-0.5'>{f.icon}</div>
                  <div>
                    <h4 className='font-semibold text-gray-900'>{f.title}</h4>
                    <p className='text-sm text-gray-600 mt-1'>{f.desc}</p>
                    <p className='text-xs text-gray-500 mt-1'>
                      <strong>When to use:</strong> {f.when}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className='bg-rose-50 border border-rose-200 rounded-lg p-4'>
              <p className='text-sm text-rose-800'>
                <strong>Not all units need all mappings.</strong> An executive
                education short course typically doesn&apos;t need AoL or GC
                mappings. A Bachelor unit in the humanities needs GCs but
                probably not AoL. The app lets you show or hide accreditation
                panels based on what&apos;s relevant to your unit.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Teaching Approaches (Pedagogy) ─────────── */}
        <div id='section-pedagogy'>
          <Section
            id='pedagogy'
            title='Teaching Approaches'
            icon={<Lightbulb className='w-5 h-5 text-yellow-600' />}
            color='bg-yellow-100'
            expanded={expanded}
            toggle={toggle}
          >
            <p className='text-gray-600 mb-4'>
              Your teaching approach (pedagogy) shapes how you design activities
              and structure the learning experience. The app supports nine
              approaches &mdash; most units blend elements of several.
            </p>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-3 mb-6'>
              {[
                {
                  name: 'Traditional / Direct Instruction',
                  desc: 'Structured, teacher-led delivery with clear sequencing. Effective for foundational knowledge.',
                },
                {
                  name: 'Inquiry-Based',
                  desc: 'Students explore questions and problems to construct understanding. Teacher as facilitator.',
                },
                {
                  name: 'Project-Based',
                  desc: 'Extended projects as the primary vehicle for learning. Authentic, real-world problems.',
                },
                {
                  name: 'Problem-Based',
                  desc: 'Similar to project-based but centred on specific problems. Common in medicine and engineering.',
                },
                {
                  name: 'Collaborative',
                  desc: 'Group learning emphasising peer interaction, discussion, and shared knowledge construction.',
                },
                {
                  name: 'Experiential',
                  desc: 'Learning through doing and reflecting. Placements, simulations, field work.',
                },
                {
                  name: 'Constructivist',
                  desc: 'Students actively build knowledge from experience. Prior knowledge is the starting point.',
                },
                {
                  name: 'Game-Based',
                  desc: 'Game mechanics (points, challenges, competition) to motivate engagement.',
                },
                {
                  name: 'Competency-Based',
                  desc: 'Progress based on demonstrated mastery rather than time spent. Self-paced.',
                },
              ].map(p => (
                <div
                  key={p.name}
                  className='bg-gray-50 rounded-lg p-3 border border-gray-200'
                >
                  <h4 className='font-semibold text-gray-900 text-sm'>
                    {p.name}
                  </h4>
                  <p className='text-xs text-gray-600 mt-1'>{p.desc}</p>
                </div>
              ))}
            </div>

            <div className='bg-yellow-50 border border-yellow-200 rounded-lg p-4'>
              <p className='text-sm text-yellow-800'>
                <strong>In the app:</strong> Select a teaching approach in the
                header dropdown or in unit settings. When AI features are
                enabled, this guides how content is generated (e.g.
                inquiry-based content includes guiding questions; collaborative
                content includes group activities). When AI is off, it provides
                static pedagogy tips.
              </p>
            </div>
          </Section>
        </div>

        {/* ── Glossary ──────────────────────────────── */}
        <div id='section-glossary'>
          <Section
            id='glossary'
            title='Glossary of Terms'
            icon={<BookOpen className='w-5 h-5 text-gray-600' />}
            color='bg-gray-100'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-3'>
              {[
                {
                  term: 'Constructive Alignment',
                  def: 'The principle that learning outcomes, teaching activities, and assessment must be aligned with each other (Biggs & Tang, 2011).',
                },
                {
                  term: "Bloom's Taxonomy",
                  def: 'A hierarchy of cognitive skills from Remember (lowest) to Create (highest). Used to classify the complexity of learning outcomes and assessment tasks.',
                },
                {
                  term: 'Universal Design for Learning (UDL)',
                  def: 'A framework for designing flexible learning experiences that accommodate all learners through multiple means of engagement, representation, and action/expression.',
                },
                {
                  term: 'Learning Modalities',
                  def: 'Different presentation modes (visual, auditory, read/write, kinaesthetic) that benefit all learners. Replaces the debunked "learning styles" concept.',
                },
                {
                  term: 'Unit Learning Outcome (ULO)',
                  def: "A statement of what students will be able to do after completing a unit. Written with Bloom's taxonomy action verbs.",
                },
                {
                  term: 'Program Learning Outcome (PLO)',
                  def: 'A degree-level outcome that describes what graduates of an entire program will achieve. Units contribute to a subset of PLOs.',
                },
                {
                  term: 'Local Learning Outcome (LO)',
                  def: 'A session-level or material-level objective that breaks down a ULO into weekly achievable steps.',
                },
                {
                  term: 'Formative Assessment',
                  def: 'Low-stakes assessment designed to provide feedback during the learning process. May or may not contribute to the final grade.',
                },
                {
                  term: 'Summative Assessment',
                  def: 'Assessment that measures student achievement and contributes significantly to the final grade.',
                },
                {
                  term: 'Graduate Capabilities (GCs)',
                  def: 'Institution-wide attributes that all graduates should demonstrate, regardless of discipline (e.g. critical thinking, cultural competence).',
                },
                {
                  term: 'Assurance of Learning (AoL)',
                  def: 'AACSB accreditation framework for business schools. Maps competencies at three levels: Introduce (I), Reinforce (R), Master (M).',
                },
                {
                  term: 'Sustainable Development Goals (SDGs)',
                  def: "The United Nations' 17 global goals (2015-2030) for sustainable development. Increasingly mapped in higher education for sustainability reporting.",
                },
                {
                  term: 'Session Format',
                  def: 'The type of teaching session (lecture, tutorial, lab, workshop, seminar, independent study). Describes the delivery mode, not the content.',
                },
                {
                  term: 'Content Type',
                  def: "The type of learning artifact (slides, notes, worksheet, quiz, video, etc.). Describes what you create, independent of the session it's used in.",
                },
                {
                  term: 'Material Category',
                  def: 'When in the learning cycle a material is used: pre-class (preparation), in-class (during session), post-class (consolidation), or resources (anytime reference).',
                },
                {
                  term: 'Pedagogy / Teaching Approach',
                  def: 'The overall philosophy guiding how you teach (e.g. inquiry-based, flipped, experiential). Influences activity design and AI content generation.',
                },
                {
                  term: 'Unit (Australian terminology)',
                  def: 'A single subject or course of study within a degree program. Equivalent to a "course" in US terminology.',
                },
              ].map(item => (
                <div
                  key={item.term}
                  className='flex items-start gap-3 py-2 border-b border-gray-100 last:border-0'
                >
                  <dt className='font-semibold text-gray-900 min-w-[200px] text-sm'>
                    {item.term}
                  </dt>
                  <dd className='text-sm text-gray-600'>{item.def}</dd>
                </div>
              ))}
            </div>
          </Section>
        </div>
      </div>

      {/* Footer */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center'>
        <p className='text-sm text-gray-500 mb-3'>
          This guide is based on established educational research. For the
          architectural decisions behind these features, see the{' '}
          <Link
            to='/about'
            className='text-purple-600 hover:text-purple-700 underline'
          >
            About page
          </Link>
          .
        </p>
        <div className='flex items-center justify-center gap-4 text-xs text-gray-400'>
          <span className='flex items-center gap-1'>
            <Eye className='w-3 h-3' />
            Biggs &amp; Tang (2011)
          </span>
          <span className='flex items-center gap-1'>
            <Ear className='w-3 h-3' />
            CAST UDL Guidelines (2018)
          </span>
          <span className='flex items-center gap-1'>
            <Hand className='w-3 h-3' />
            Anderson &amp; Krathwohl (2001)
          </span>
        </div>
      </div>
    </div>
  );
};

export default LearningDesignGuide;
