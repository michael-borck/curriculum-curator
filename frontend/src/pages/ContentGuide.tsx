import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  ChevronDown,
  ChevronRight,
  Layers,
  Sliders,
  Download,
  Table2,
  Upload,
  Link2,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Monitor,
  Wrench,
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

// ── Main component ─────────────────────────────────────────

const SECTIONS = [
  { id: 'why', label: 'Why a Curriculum Tool?' },
  { id: 'content-first', label: 'Content First, Style Later' },
  { id: 'control', label: "You're in Control" },
  { id: 'export-workflow', label: 'The Export Workflow' },
  { id: 'export-map', label: 'What Gets Exported Where' },
  { id: 'import', label: "Import, Don't Recreate" },
  { id: 'alignment', label: 'The Alignment Advantage' },
  { id: 'other-tools', label: 'When to Use Other Tools' },
] as const;

const ContentGuide = () => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['why']));

  const toggle = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const expandAll = () => setExpanded(new Set(SECTIONS.map(s => s.id)));
  const collapseAll = () => setExpanded(new Set());

  return (
    <div className='max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6'>
      {/* Header */}
      <div className='bg-gradient-to-r from-teal-600 to-cyan-700 rounded-xl p-6 sm:p-8 text-white'>
        <div className='flex items-center gap-3 mb-3'>
          <FileText className='w-8 h-8' />
          <h1 className='text-2xl sm:text-3xl font-bold'>
            Content Authoring Guide
          </h1>
        </div>
        <p className='text-teal-100 text-sm sm:text-base max-w-2xl'>
          Why a unified curriculum tool beats working in PowerPoint, Word, and
          your LMS separately &mdash; and how to get the most out of it.
        </p>
      </div>

      {/* Quick nav */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
        <div className='flex items-center justify-between mb-3'>
          <h3 className='font-semibold text-gray-900 text-sm'>
            Quick Navigation
          </h3>
          <div className='flex gap-2'>
            <button
              onClick={expandAll}
              className='text-xs text-teal-600 hover:text-teal-700 font-medium'
            >
              Expand all
            </button>
            <span className='text-gray-300'>|</span>
            <button
              onClick={collapseAll}
              className='text-xs text-teal-600 hover:text-teal-700 font-medium'
            >
              Collapse all
            </button>
          </div>
        </div>
        <div className='flex flex-wrap gap-2'>
          {SECTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => {
                if (!expanded.has(s.id)) toggle(s.id);
                document
                  .getElementById(`section-${s.id}`)
                  ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className='px-3 py-1 text-xs rounded-full bg-teal-50 text-teal-700 hover:bg-teal-100 transition'
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Sections */}
      <div className='space-y-4'>
        {/* 1 — Why a Curriculum Tool? */}
        <div id='section-why'>
          <Section
            id='why'
            title='Why a Curriculum Tool?'
            icon={<Layers className='w-5 h-5 text-white' />}
            color='bg-teal-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                Most educators author curriculum materials in isolation: slides
                in PowerPoint, readings in Word, quizzes in the LMS, rubrics in
                a spreadsheet. Each tool is excellent at its job, but none of
                them talk to each other. The result? Outcomes drift out of
                alignment, assessment weights don&apos;t add up, and
                accreditation evidence is scattered across a dozen files.
              </p>

              <div className='bg-teal-50 border border-teal-200 rounded-lg p-4'>
                <p className='text-sm text-teal-800 font-medium mb-2'>
                  Think of it like a conductor and an orchestra
                </p>
                <p className='text-sm text-teal-700'>
                  A conductor doesn&apos;t play every instrument &mdash; but
                  they make the orchestra work together. This tool is your
                  conductor: you still write the content, but the tool ensures
                  every piece connects to your outcomes, your assessments, and
                  your accreditation requirements.
                </p>
              </div>

              <p>
                Curriculum Curator connects your content to your outcomes, your
                outcomes to your assessments, and your assessments to
                accreditation frameworks. When you change an outcome, you can
                immediately see which materials and assessments are affected.
                That&apos;s something no combination of individual tools can
                offer.
              </p>

              <ul className='space-y-2'>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0 text-teal-500' />
                  <span>
                    <strong>Connected, not siloed:</strong> content, outcomes,
                    assessments, and accreditation in one place
                  </span>
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0 text-teal-500' />
                  <span>
                    <strong>Change propagation:</strong> update an outcome and
                    see every affected material and assessment instantly
                  </span>
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0 text-teal-500' />
                  <span>
                    <strong>Accreditation-ready:</strong> evidence is built into
                    your workflow, not assembled after the fact
                  </span>
                </li>
              </ul>
            </div>
          </Section>
        </div>

        {/* 2 — Content First, Style Later */}
        <div id='section-content-first'>
          <Section
            id='content-first'
            title='Content First, Style Later'
            icon={<FileText className='w-5 h-5 text-white' />}
            color='bg-cyan-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                The most common trap in content creation: spending hours on
                slide transitions and font choices before the learning content
                is solid. This tool enforces a deliberate separation of concerns
                &mdash; <strong>what</strong> you teach comes first;{' '}
                <strong>how it looks</strong> comes later.
              </p>

              <div className='grid grid-cols-1 sm:grid-cols-2 gap-4'>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-2'>
                    Structure (this tool)
                  </h4>
                  <ul className='space-y-1.5 text-xs text-gray-600'>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-teal-500' />
                      Learning outcomes and alignment
                    </li>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-teal-500' />
                      Content hierarchy and sequence
                    </li>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-teal-500' />
                      Quiz questions and rubric criteria
                    </li>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-teal-500' />
                      Quality and inclusivity scoring
                    </li>
                  </ul>
                </div>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-2'>
                    Styling (native tools)
                  </h4>
                  <ul className='space-y-1.5 text-xs text-gray-600'>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400' />
                      Brand colours and typography
                    </li>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400' />
                      Slide animations and transitions
                    </li>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400' />
                      Complex page layouts
                    </li>
                    <li className='flex items-start gap-1.5'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400' />
                      Print-ready formatting
                    </li>
                  </ul>
                </div>
              </div>

              <div className='bg-teal-50 border border-teal-200 rounded-lg p-4'>
                <p className='text-sm text-teal-800 font-medium mb-1'>
                  The 80/20 principle
                </p>
                <p className='text-sm text-teal-700'>
                  We handle the 80% that matters most &mdash; structure,
                  alignment, content quality, and clean default formatting. The
                  remaining 20% (custom animations, branded slide transitions,
                  pixel-perfect layouts) belongs in specialised tools, after
                  export. Power users refine in native tools; everyone else gets
                  professional output by default.
                </p>
              </div>

              <p>
                Your exported PPTX, DOCX, and PDF files use clean templates that
                look professional out of the box. If your institution has
                branded templates, upload them in Settings and every export will
                use your branding automatically.
              </p>
            </div>
          </Section>
        </div>

        {/* 3 — You're in Control */}
        <div id='section-control'>
          <Section
            id='control'
            title="You're in Control"
            icon={<Sliders className='w-5 h-5 text-white' />}
            color='bg-emerald-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                This tool is designed around educator agency. Every major
                decision &mdash; from deployment to AI to export &mdash; is
                yours to make.
              </p>

              <div className='space-y-3'>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-2 flex items-center gap-2'>
                    <Monitor className='w-4 h-4 text-emerald-600' />
                    Deployment
                  </h4>
                  <p className='text-sm text-gray-600'>
                    Run it centrally hosted, self-hosted on your own server, in
                    a Docker container, or as a standalone desktop app. Your
                    data stays where you decide.
                  </p>
                </div>

                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-2 flex items-center gap-2'>
                    <Sliders className='w-4 h-4 text-emerald-600' />
                    AI assistance
                  </h4>
                  <ul className='space-y-1.5 text-sm text-gray-600'>
                    <li className='flex items-start gap-2'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-emerald-500' />
                      <span>
                        <strong>Level:</strong> none (fully manual), refine (AI
                        enhances your drafts), or create (AI generates first
                        drafts for you to review)
                      </span>
                    </li>
                    <li className='flex items-start gap-2'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-emerald-500' />
                      <span>
                        <strong>Provider:</strong> OpenAI, Anthropic, Google
                        Gemini, or local Ollama &mdash; use your own API keys
                      </span>
                    </li>
                    <li className='flex items-start gap-2'>
                      <ArrowRight className='w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-emerald-500' />
                      <span>
                        <strong>Or no AI at all:</strong> every feature works
                        without AI enabled
                      </span>
                    </li>
                  </ul>
                </div>

                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-2 flex items-center gap-2'>
                    <Download className='w-4 h-4 text-emerald-600' />
                    Export
                  </h4>
                  <p className='text-sm text-gray-600'>
                    Pick your output formats, set defaults per content type, and
                    override per material when needed. Upload institutional
                    templates for branded output.
                  </p>
                </div>

                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-2 flex items-center gap-2'>
                    <CheckCircle2 className='w-4 h-4 text-emerald-600' />
                    Quality
                  </h4>
                  <p className='text-sm text-gray-600'>
                    Choose which metrics matter to you: Bloom&apos;s taxonomy
                    distribution, UDL inclusivity scoring, assessment weight
                    validation, or custom framework alignment. Enable what
                    helps; ignore what doesn&apos;t.
                  </p>
                </div>
              </div>

              <div className='bg-emerald-50 border border-emerald-200 rounded-lg p-4'>
                <p className='text-sm text-emerald-800'>
                  <strong>The educator makes every decision.</strong> AI
                  suggests, the tool validates, but you approve. Nothing is
                  published or exported without your explicit action.
                </p>
              </div>
            </div>
          </Section>
        </div>

        {/* 4 — The Export Workflow */}
        <div id='section-export-workflow'>
          <Section
            id='export-workflow'
            title='The Export Workflow'
            icon={<Download className='w-5 h-5 text-white' />}
            color='bg-sky-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                Export uses a three-tier system that maps structured content to
                the right output format automatically &mdash; no manual
                reformatting needed.
              </p>

              <div className='space-y-3'>
                <div className='bg-sky-50 border-l-4 border-sky-400 rounded-r-lg p-4'>
                  <h4 className='font-medium text-sky-900 mb-1'>
                    Tier 1: Author structured content
                  </h4>
                  <p className='text-sm text-sky-800'>
                    Write your materials using structured content nodes:
                    quizzes, slide decks, branching scenarios, readings, and
                    activities. Each node type knows what export formats it
                    supports.
                  </p>
                </div>

                <div className='flex justify-center'>
                  <ArrowRight className='w-5 h-5 text-sky-400 rotate-90' />
                </div>

                <div className='bg-sky-50 border-l-4 border-sky-400 rounded-r-lg p-4'>
                  <h4 className='font-medium text-sky-900 mb-1'>
                    Tier 2: Choose per-material export targets
                  </h4>
                  <p className='text-sm text-sky-800'>
                    For each material, select the output format: HTML for web,
                    QTI for LMS-native quizzes, H5P for interactive content,
                    PPTX for presentations, DOCX or PDF for documents. Your
                    defaults apply automatically; override where needed.
                  </p>
                </div>

                <div className='flex justify-center'>
                  <ArrowRight className='w-5 h-5 text-sky-400 rotate-90' />
                </div>

                <div className='bg-sky-50 border-l-4 border-sky-400 rounded-r-lg p-4'>
                  <h4 className='font-medium text-sky-900 mb-1'>
                    Tier 3: Bundle into packages
                  </h4>
                  <p className='text-sm text-sky-800'>
                    Group exported materials into standard packages: IMS Common
                    Cartridge (IMSCC) for LMS import, SCORM for tracking-enabled
                    delivery, or a plain ZIP for file-based distribution. Each
                    package includes metadata and manifest files that your LMS
                    understands.
                  </p>
                </div>
              </div>

              <div className='bg-gray-50 rounded-lg p-4'>
                <p className='text-sm text-gray-700'>
                  <strong>Why three tiers?</strong> Because the same quiz can
                  become a QTI file for Moodle, an H5P widget for interactive
                  practice, or a PDF for a printed exam &mdash; without you
                  rewriting anything. The structure carries the meaning; the
                  export tier handles the formatting.
                </p>
              </div>
            </div>
          </Section>
        </div>

        {/* 5 — What Gets Exported Where */}
        <div id='section-export-map'>
          <Section
            id='export-map'
            title='What Gets Exported Where'
            icon={<Table2 className='w-5 h-5 text-white' />}
            color='bg-indigo-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                Each content type supports specific export formats. The table
                below shows what&apos;s available:
              </p>

              <div className='overflow-x-auto'>
                <table className='w-full text-sm border-collapse'>
                  <thead>
                    <tr className='bg-indigo-50'>
                      <th className='text-left px-3 py-2 border border-indigo-100 font-medium text-indigo-900'>
                        Content Type
                      </th>
                      <th className='text-left px-3 py-2 border border-indigo-100 font-medium text-indigo-900'>
                        Export Formats
                      </th>
                      <th className='text-left px-3 py-2 border border-indigo-100 font-medium text-indigo-900'>
                        Best For
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className='px-3 py-2 border border-gray-100 font-medium text-gray-800'>
                        Quiz / Test
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        QTI, H5P, PDF
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        QTI for LMS native import; H5P for interactive practice;
                        PDF for printable exams
                      </td>
                    </tr>
                    <tr className='bg-gray-50'>
                      <td className='px-3 py-2 border border-gray-100 font-medium text-gray-800'>
                        Slide Deck
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        PPTX, H5P, PDF
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        PPTX for presentations; H5P Course Presentation for
                        interactive slides; PDF for handouts
                      </td>
                    </tr>
                    <tr>
                      <td className='px-3 py-2 border border-gray-100 font-medium text-gray-800'>
                        Branching Scenario
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>H5P</td>
                      <td className='px-3 py-2 border border-gray-100'>
                        H5P Branching Scenario for interactive decision-based
                        learning
                      </td>
                    </tr>
                    <tr className='bg-gray-50'>
                      <td className='px-3 py-2 border border-gray-100 font-medium text-gray-800'>
                        Reading / Text
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        HTML, PDF, DOCX
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        HTML for LMS pages; PDF for distribution; DOCX for
                        further editing
                      </td>
                    </tr>
                    <tr>
                      <td className='px-3 py-2 border border-gray-100 font-medium text-gray-800'>
                        Activity / Worksheet
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        HTML, PDF, DOCX, H5P
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        HTML/H5P for interactive; PDF/DOCX for printable
                        worksheets
                      </td>
                    </tr>
                    <tr className='bg-gray-50'>
                      <td className='px-3 py-2 border border-gray-100 font-medium text-gray-800'>
                        Rubric
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        HTML, PDF, DOCX
                      </td>
                      <td className='px-3 py-2 border border-gray-100'>
                        HTML for LMS rubric import; PDF/DOCX for student
                        handouts
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className='bg-indigo-50 border border-indigo-200 rounded-lg p-4'>
                <p className='text-sm text-indigo-800'>
                  <strong>Defaults and overrides:</strong> Set your preferred
                  export format per content type in Settings. When exporting
                  individual materials, you can override the default for that
                  specific item. Your institution&apos;s template (if uploaded)
                  is applied automatically to PPTX and DOCX exports.
                </p>
              </div>
            </div>
          </Section>
        </div>

        {/* 6 — Import, Don't Recreate */}
        <div id='section-import'>
          <Section
            id='import'
            title="Import, Don't Recreate"
            icon={<Upload className='w-5 h-5 text-white' />}
            color='bg-violet-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                You don&apos;t need to start from scratch. Bring your existing
                materials into the tool and let it extract what it can.
              </p>

              <ul className='space-y-2'>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0 text-violet-500' />
                  <span>
                    <strong>PDF, DOCX, PPTX:</strong> Upload existing files. The
                    system extracts text, structure, and (for PPTX) slide themes
                    for branded re-export.
                  </span>
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0 text-violet-500' />
                  <span>
                    <strong>IMSCC &amp; SCORM:</strong> Import LMS course
                    packages. The system unpacks content, quizzes, and structure
                    into editable materials.
                  </span>
                </li>
                <li className='flex items-start gap-2'>
                  <CheckCircle2 className='w-4 h-4 mt-0.5 flex-shrink-0 text-violet-500' />
                  <span>
                    <strong>PPTX theme extraction:</strong> When you import a
                    branded PPTX, the tool strips the content and saves the
                    theme as a reusable export template.
                  </span>
                </li>
              </ul>

              <div className='bg-violet-50 border border-violet-200 rounded-lg p-4'>
                <p className='text-sm text-violet-800 mb-2'>
                  <strong>The import workflow:</strong>
                </p>
                <ol className='space-y-1.5 text-sm text-violet-700 list-decimal list-inside'>
                  <li>Upload your existing files</li>
                  <li>Review the extracted structure and content</li>
                  <li>Preserve what works, edit what needs updating</li>
                  <li>
                    Optionally enhance with AI &mdash; map to outcomes, suggest
                    improvements, fill gaps
                  </li>
                  <li>
                    Re-export in any supported format with alignment and quality
                    built in
                  </li>
                </ol>
              </div>

              <p>
                The goal is to get your existing content into the system quickly
                so you can start benefiting from alignment tracking, quality
                scoring, and structured exports &mdash; without retyping
                everything.
              </p>
            </div>
          </Section>
        </div>

        {/* 7 — The Alignment Advantage */}
        <div id='section-alignment'>
          <Section
            id='alignment'
            title='The Alignment Advantage'
            icon={<Link2 className='w-5 h-5 text-white' />}
            color='bg-rose-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                This is what no individual tool can offer. When all your content
                lives in one system with structured metadata, alignment checks
                happen automatically:
              </p>

              <div className='grid grid-cols-1 sm:grid-cols-2 gap-3'>
                <div className='bg-rose-50 rounded-lg p-3'>
                  <h4 className='font-medium text-rose-900 text-xs uppercase tracking-wide mb-1.5'>
                    Outcome Mapping
                  </h4>
                  <p className='text-xs text-rose-700'>
                    Every material and assessment is linked to Unit Learning
                    Outcomes. See at a glance which outcomes are well-covered
                    and which have gaps.
                  </p>
                </div>
                <div className='bg-rose-50 rounded-lg p-3'>
                  <h4 className='font-medium text-rose-900 text-xs uppercase tracking-wide mb-1.5'>
                    Bloom&apos;s Taxonomy
                  </h4>
                  <p className='text-xs text-rose-700'>
                    Track the cognitive level distribution across your unit.
                    Ensure you&apos;re not stuck at &ldquo;remember&rdquo; and
                    &ldquo;understand&rdquo; when your outcomes demand
                    &ldquo;analyse&rdquo; and &ldquo;evaluate.&rdquo;
                  </p>
                </div>
                <div className='bg-rose-50 rounded-lg p-3'>
                  <h4 className='font-medium text-rose-900 text-xs uppercase tracking-wide mb-1.5'>
                    Assessment Validation
                  </h4>
                  <p className='text-xs text-rose-700'>
                    Assessment weights must total 100%. Each outcome needs at
                    least one assessment. The tool catches these issues before
                    your students do.
                  </p>
                </div>
                <div className='bg-rose-50 rounded-lg p-3'>
                  <h4 className='font-medium text-rose-900 text-xs uppercase tracking-wide mb-1.5'>
                    UDL Inclusivity
                  </h4>
                  <p className='text-xs text-rose-700'>
                    Universal Design for Learning scoring across four
                    dimensions: representation, engagement, action &amp;
                    expression, and diversity. Automatic suggestions for
                    improvement.
                  </p>
                </div>
                <div className='bg-rose-50 rounded-lg p-3'>
                  <h4 className='font-medium text-rose-900 text-xs uppercase tracking-wide mb-1.5'>
                    Accreditation Frameworks
                  </h4>
                  <p className='text-xs text-rose-700'>
                    Map outcomes to graduate capabilities, Assurance of Learning
                    (AoL) goals, SDGs, or custom frameworks. Generate compliance
                    evidence automatically.
                  </p>
                </div>
                <div className='bg-rose-50 rounded-lg p-3'>
                  <h4 className='font-medium text-rose-900 text-xs uppercase tracking-wide mb-1.5'>
                    Quality Scoring
                  </h4>
                  <p className='text-xs text-rose-700'>
                    Per-week and per-unit star ratings based on content
                    completeness, alignment coverage, and pedagogical quality.
                    See your whole unit at a glance.
                  </p>
                </div>
              </div>

              <div className='bg-rose-50 border border-rose-200 rounded-lg p-4'>
                <p className='text-sm text-rose-800'>
                  <strong>All connected, all automatic.</strong> These checks
                  run continuously as you author. No separate audit step, no
                  spreadsheet mapping exercise, no last-minute scramble before
                  accreditation review.
                </p>
              </div>
            </div>
          </Section>
        </div>

        {/* 8 — When to Use Other Tools */}
        <div id='section-other-tools'>
          <Section
            id='other-tools'
            title='When to Use Other Tools'
            icon={<Wrench className='w-5 h-5 text-white' />}
            color='bg-gray-600'
            expanded={expanded}
            toggle={toggle}
          >
            <div className='space-y-4 text-sm text-gray-600'>
              <p>
                We believe in honest guidance. This tool is not trying to
                replace every application in your workflow &mdash; it&apos;s
                trying to handle the structural and alignment work so you can
                use specialist tools where they genuinely add value.
              </p>

              <div className='space-y-3'>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-1'>
                    Use PowerPoint when&hellip;
                  </h4>
                  <p className='text-sm text-gray-600'>
                    You need complex animations, embedded videos with precise
                    timing, or pixel-perfect branded layouts. Export your slides
                    from here, then refine transitions and animations in
                    PowerPoint.
                  </p>
                </div>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-1'>
                    Use your LMS quiz builder when&hellip;
                  </h4>
                  <p className='text-sm text-gray-600'>
                    You need adaptive release, question pools with
                    randomisation, or LMS-specific features like SafeAssign
                    integration. Export your questions as QTI and import them,
                    then configure the LMS-specific settings there.
                  </p>
                </div>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-1'>
                    Use InDesign or Canva when&hellip;
                  </h4>
                  <p className='text-sm text-gray-600'>
                    You need print-ready documents with complex multi-column
                    layouts, infographics, or publication-quality typography.
                    Export your content as DOCX and use it as a starting point.
                  </p>
                </div>
                <div className='bg-gray-50 rounded-lg p-4'>
                  <h4 className='font-medium text-gray-900 mb-1'>
                    Use specialist video tools when&hellip;
                  </h4>
                  <p className='text-sm text-gray-600'>
                    You&apos;re creating screencasts, lecture recordings, or
                    video-based learning. This tool manages the curriculum
                    structure and metadata; video production belongs in
                    dedicated tools.
                  </p>
                </div>
              </div>

              <div className='bg-teal-50 border border-teal-200 rounded-lg p-4'>
                <p className='text-sm text-teal-800'>
                  <strong>The pattern:</strong> author and align here, export,
                  then refine in specialist tools where needed. You get the
                  alignment and quality benefits without giving up the tools you
                  already know.
                </p>
              </div>
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
            Biggs, J. &amp; Tang, C. (2011).{' '}
            <em>Teaching for quality learning at university</em> (4th ed.).
            Maidenhead: Open University Press.
          </li>
          <li>
            Wiggins, G. &amp; McTighe, J. (2005).{' '}
            <em>Understanding by design</em> (2nd ed.). Alexandria, VA: ASCD.
          </li>
          <li>
            CAST (2018).{' '}
            <a
              href='https://udlguidelines.cast.org/'
              target='_blank'
              rel='noopener noreferrer'
              className='text-teal-600 hover:text-teal-700 underline'
            >
              Universal Design for Learning Guidelines version 2.2
            </a>
            . Wakefield, MA: CAST.
          </li>
          <li>
            IMS Global Learning Consortium (2019).{' '}
            <a
              href='https://www.imsglobal.org/activity/common-cartridge'
              target='_blank'
              rel='noopener noreferrer'
              className='text-teal-600 hover:text-teal-700 underline'
            >
              IMS Common Cartridge specification
            </a>
            .
          </li>
          <li>
            IMS Global Learning Consortium (2012).{' '}
            <a
              href='https://www.imsglobal.org/question/index.html'
              target='_blank'
              rel='noopener noreferrer'
              className='text-teal-600 hover:text-teal-700 underline'
            >
              QTI (Question &amp; Test Interoperability) specification
            </a>
            .
          </li>
        </ul>

        <div className='border-t border-gray-100 pt-4 text-center'>
          <p className='text-sm text-gray-500 mb-2'>
            For foundational curriculum design concepts, see the{' '}
            <Link
              to='/guide/learning-design'
              className='text-teal-600 hover:text-teal-700 underline'
            >
              Learning Design Guide
            </Link>
            . For assessment and rubric design, see the{' '}
            <Link
              to='/guide/assessment-design'
              className='text-teal-600 hover:text-teal-700 underline'
            >
              Assessment Design Guide
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
};

export default ContentGuide;
