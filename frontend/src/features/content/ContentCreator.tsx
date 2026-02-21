import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import RichTextEditor from '../../components/Editor/RichTextEditor';
import PedagogySelector from '../../components/Wizard/PedagogySelector';
import {
  enhanceContent,
  createContent,
  updateContent,
  getContent,
  getUnits,
  generateContentStream,
  validateContent,
  remediateContentStream,
  runPluginValidation,
  runPluginRemediation,
} from '../../services/api';
import type {
  PluginResultData,
  PluginValidateResponse,
} from '../../services/api';
import {
  Loader2,
  Sparkles,
  Save,
  Download,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Wand2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAILevel } from '../../hooks/useAILevel';
import { useUnitDesign } from '../../hooks/useUnitDesign';
import type { ContentType, PedagogyType, Unit } from '../../types/index';

interface ValidationResult {
  validatorName: string;
  passed: boolean;
  message: string;
  score?: number;
  suggestions?: string[];
  remediationPrompt?: string;
}

interface ValidationResponse {
  results: ValidationResult[];
  overallPassed: boolean;
  overallScore?: number;
}

const scoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-amber-600';
  return 'text-red-600';
};

const PluginResultCard: React.FC<{
  name: string;
  result: PluginResultData;
}> = ({ name, result }) => {
  const [expanded, setExpanded] = useState(false);
  const score =
    result.data && typeof result.data.score === 'number'
      ? result.data.score
      : null;
  const issues =
    result.data && Array.isArray(result.data.issues)
      ? (result.data.issues as string[])
      : [];

  return (
    <div
      className={`p-3 rounded-lg border ${
        result.success ? 'bg-white border-gray-200' : 'bg-red-50 border-red-200'
      }`}
    >
      <button
        type='button'
        className='flex items-center justify-between w-full text-left'
        onClick={() => setExpanded(!expanded)}
      >
        <span className='font-medium text-sm'>
          {name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
        </span>
        <div className='flex items-center gap-2'>
          {score !== null && (
            <span className={`text-xs font-semibold ${scoreColor(score)}`}>
              {Math.round(score)}%
            </span>
          )}
          {result.success ? (
            <CheckCircle2 className='text-green-500' size={16} />
          ) : (
            <XCircle className='text-red-500' size={16} />
          )}
        </div>
      </button>

      <p className='text-xs text-gray-600 mt-1'>{result.message}</p>

      {expanded && (
        <>
          {issues.length > 0 && (
            <ul className='mt-2 space-y-1 max-h-40 overflow-y-auto'>
              {issues.map((issue, idx) => (
                <li
                  key={idx}
                  className='text-xs text-gray-600 flex items-start gap-1'
                >
                  <span className='text-gray-400 shrink-0'>•</span>
                  {issue}
                </li>
              ))}
            </ul>
          )}

          {result.suggestions && result.suggestions.length > 0 && (
            <ul className='mt-2 space-y-1'>
              {result.suggestions.map((suggestion, idx) => (
                <li
                  key={idx}
                  className='text-xs text-blue-700 flex items-start gap-1'
                >
                  <span className='text-blue-400 shrink-0'>→</span>
                  {suggestion}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
};

const ContentCreator = () => {
  const { type, unitId, contentId } = useParams<{
    type?: ContentType;
    unitId?: string;
    contentId?: string;
  }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [selectedUnitId, setSelectedUnitId] = useState<string>('');
  const [contentType, setContentType] = useState<string>(type || 'lecture');
  const [units, setUnits] = useState<Unit[]>([]);
  const [pedagogy, setPedagogy] = useState<PedagogyType>('inquiry-based');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isRemediating, setIsRemediating] = useState(false);
  const [validationResults, setValidationResults] =
    useState<ValidationResponse | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [pluginResults, setPluginResults] = useState<Record<
    string,
    PluginResultData
  > | null>(null);
  const [pluginOverallScore, setPluginOverallScore] = useState<number | null>(
    null
  );
  const [isRunningPlugins, setIsRunningPlugins] = useState(false);
  const [isRunningRemediation, setIsRunningRemediation] = useState(false);
  const { canGenerate, canRefine } = useAILevel();
  const { designId } = useUnitDesign(selectedUnitId || unitId);

  // Determine if we're in edit mode
  const isEditMode = Boolean(unitId && contentId);

  useEffect(() => {
    fetchUnits();
  }, []);

  // Load existing content if in edit mode
  useEffect(() => {
    const loadExistingContent = async () => {
      if (!unitId || !contentId) return;

      setIsLoading(true);
      try {
        const response = await getContent(unitId, contentId);
        const data = response.data;
        setTitle(data.title);
        setContent(data.body || '');
        setContentType(data.contentType);
        setSelectedUnitId(data.unitId);
      } catch (error) {
        console.error('Failed to load content:', error);
        toast.error('Failed to load content for editing');
      } finally {
        setIsLoading(false);
      }
    };

    if (isEditMode && unitId && contentId) {
      loadExistingContent();
    }
  }, [isEditMode, unitId, contentId]);

  // Pre-select unit if unitId is in URL (either route param or query param)
  useEffect(() => {
    const unitFromQuery = searchParams.get('unit');
    if (unitId) {
      setSelectedUnitId(unitId);
    } else if (unitFromQuery) {
      setSelectedUnitId(unitFromQuery);
    }
  }, [unitId, searchParams]);

  const fetchUnits = async () => {
    try {
      const response = await getUnits();
      setUnits(response.data?.units ?? []);
    } catch (error) {
      console.error('Failed to fetch units:', error);
      toast.error('Failed to load units');
    }
  };

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a topic to generate content about');
      return;
    }

    setIsGenerating(true);
    setStreamingContent('');
    setContent('');
    setValidationResults(null);

    try {
      await generateContentStream(
        (type as ContentType) || 'lecture',
        pedagogy,
        topic,
        chunk => {
          setStreamingContent(prev => prev + chunk);
        },
        () => {
          setStreamingContent(prev => {
            setContent(prev);
            return '';
          });
          setIsGenerating(false);
          toast.success('Content generated successfully!');
        },
        error => {
          console.error('Error generating content:', error);
          toast.error(error.message || 'Failed to generate content');
          setIsGenerating(false);
        },
        {
          unitId: selectedUnitId || unitId,
          designId: designId ?? undefined,
        }
      );
    } catch (error: unknown) {
      console.error('Error generating content:', error);
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to generate content';
      toast.error(errorMessage);
      setIsGenerating(false);
    }
  };

  const handleEnhance = async () => {
    if (!content) {
      toast.error('Please add some content first');
      return;
    }

    setIsGenerating(true);
    try {
      const enhanced = await enhanceContent(content, pedagogy, {
        unitId: selectedUnitId || unitId,
        designId: designId ?? undefined,
      });
      setContent(enhanced.data.content);
      toast.success('Content enhanced!');
    } catch (error) {
      console.error('Error enhancing content:', error);
      toast.error('Failed to enhance content');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!title.trim()) {
      toast.error('Please enter a title');
      return;
    }

    if (!selectedUnitId) {
      toast.error('Please select a unit');
      return;
    }

    if (!content.trim()) {
      toast.error('Please add some content first');
      return;
    }

    setIsSaving(true);
    try {
      if (isEditMode && contentId) {
        // Update existing content
        await updateContent(selectedUnitId, contentId, {
          title: title.trim(),
          body: content,
        });
        toast.success('Content updated successfully!');
      } else {
        // Create new content
        await createContent(selectedUnitId, {
          title: title.trim(),
          contentType: contentType || 'lecture',
          body: content,
        });
        toast.success('Content saved successfully!');
      }
      navigate(`/units/${selectedUnitId}`);
    } catch (error: unknown) {
      console.error('Error saving content:', error);
      const axiosError = error as { response?: { data?: { detail?: string } } };
      toast.error(
        axiosError.response?.data?.detail || 'Failed to save content'
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleValidate = async () => {
    if (!content.trim()) {
      toast.error('Please add some content to validate');
      return;
    }

    setIsValidating(true);
    setValidationResults(null);

    try {
      const response = await validateContent(content, [
        'readability',
        'structure',
      ]);
      // Map snake_case to camelCase
      const mapped: ValidationResponse = {
        results: response.data.results.map(
          (r: {
            validator_name: string;
            passed: boolean;
            message: string;
            score?: number;
            suggestions?: string[];
            remediation_prompt?: string;
          }) => ({
            validatorName: r.validator_name,
            passed: r.passed,
            message: r.message,
            score: r.score,
            suggestions: r.suggestions,
            remediationPrompt: r.remediation_prompt,
          })
        ),
        overallPassed: response.data.overall_passed,
        overallScore: response.data.overall_score,
      };
      setValidationResults(mapped);

      if (mapped.overallPassed) {
        toast.success('Content passed all validations!');
      } else {
        toast('Content has some issues that could be improved', {
          icon: '⚠️',
        });
      }
    } catch (error) {
      console.error('Error validating content:', error);
      toast.error('Failed to validate content');
    } finally {
      setIsValidating(false);
    }
  };

  const handleRemediate = async (remediationType: string) => {
    if (!content.trim()) {
      toast.error('No content to remediate');
      return;
    }

    setIsRemediating(true);
    setStreamingContent('');

    try {
      await remediateContentStream(
        content,
        remediationType,
        undefined,
        chunk => {
          setStreamingContent(prev => prev + chunk);
        },
        () => {
          setStreamingContent(prev => {
            setContent(prev);
            return '';
          });
          setIsRemediating(false);
          setValidationResults(null);
          toast.success('Content remediated successfully!');
        },
        error => {
          console.error('Error remediating content:', error);
          toast.error(error.message || 'Failed to remediate content');
          setIsRemediating(false);
        }
      );
    } catch (error) {
      console.error('Error remediating content:', error);
      toast.error('Failed to remediate content');
      setIsRemediating(false);
    }
  };

  const handlePluginValidation = async () => {
    if (!content.trim()) {
      toast.error('Please add some content to validate');
      return;
    }

    setIsRunningPlugins(true);
    setPluginResults(null);
    setPluginOverallScore(null);

    try {
      const response = await runPluginValidation(content);
      const data: PluginValidateResponse = response.data;
      setPluginResults(data.results);
      setPluginOverallScore(data.overallScore);

      if (data.overallScore >= 80) {
        toast.success(
          `Quality checks passed (${Math.round(data.overallScore)}%)`
        );
      } else {
        toast('Quality issues found — review results below', {
          icon: '\u26A0\uFE0F',
        });
      }
    } catch (error) {
      console.error('Error running plugin validation:', error);
      toast.error('Failed to run quality checks');
    } finally {
      setIsRunningPlugins(false);
    }
  };

  const handlePluginRemediation = async (remediators?: string[]) => {
    if (!content.trim()) {
      toast.error('No content to fix');
      return;
    }

    setIsRunningRemediation(true);

    try {
      const response = await runPluginRemediation(content, remediators);
      const data = response.data;
      if (data.content && data.content !== content) {
        setContent(data.content);
        setPluginResults(null);
        setPluginOverallScore(null);
        const changeCount = data.changesMade.length;
        toast.success(
          `Applied ${changeCount} fix${changeCount === 1 ? '' : 'es'}`
        );
      } else {
        toast('No changes needed');
      }
    } catch (error) {
      console.error('Error running plugin remediation:', error);
      toast.error('Failed to auto-fix content');
    } finally {
      setIsRunningRemediation(false);
    }
  };

  if (isLoading) {
    return (
      <div className='max-w-6xl mx-auto p-6 flex items-center justify-center h-64'>
        <Loader2 className='animate-spin text-purple-600' size={48} />
      </div>
    );
  }

  return (
    <div className='max-w-6xl mx-auto p-6'>
      <div className='mb-6'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          {isEditMode ? 'Edit' : 'Create'}{' '}
          {contentType
            ? contentType.charAt(0).toUpperCase() + contentType.slice(1)
            : 'Content'}
        </h1>
        <p className='text-gray-600'>
          {isEditMode
            ? 'Update your content below'
            : 'AI-powered content creation with pedagogical alignment'}
        </p>
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
        <div className='lg:col-span-2'>
          <div className='bg-white rounded-lg shadow-md p-6'>
            <div className='mb-4 space-y-4'>
              <div className='flex gap-4'>
                <div className='flex-1'>
                  <label
                    htmlFor='title'
                    className='block text-sm font-medium text-gray-700 mb-1'
                  >
                    Title *
                  </label>
                  <input
                    id='title'
                    type='text'
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder='Enter content title...'
                    className='w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
                  />
                </div>
                <div className='w-64'>
                  <label
                    htmlFor='unit'
                    className='block text-sm font-medium text-gray-700 mb-1'
                  >
                    Unit *
                  </label>
                  <select
                    id='unit'
                    value={selectedUnitId}
                    onChange={e => setSelectedUnitId(e.target.value)}
                    disabled={isEditMode}
                    className='w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed'
                  >
                    <option value=''>Select a unit...</option>
                    {units.map(unit => (
                      <option key={unit.id} value={unit.id}>
                        {unit.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {canGenerate && (
                <div>
                  <label
                    htmlFor='topic'
                    className='block text-sm font-medium text-gray-700 mb-1'
                  >
                    Topic for AI Generation
                  </label>
                  <input
                    id='topic'
                    type='text'
                    value={topic}
                    onChange={e => setTopic(e.target.value)}
                    placeholder='e.g., Introduction to Machine Learning, Photosynthesis in Plants...'
                    className='w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
                  />
                  <p className='text-xs text-gray-500 mt-1'>
                    Describe what you want the AI to generate content about
                  </p>
                </div>
              )}

              <div className='flex justify-between items-center'>
                <h2 className='text-xl font-semibold'>Content Editor</h2>
                <div className='flex gap-2'>
                  {canGenerate && (
                    <button
                      onClick={handleGenerate}
                      disabled={isGenerating || !topic.trim()}
                      className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2'
                    >
                      {isGenerating ? (
                        <Loader2 className='animate-spin' size={18} />
                      ) : (
                        <Sparkles size={18} />
                      )}
                      {isGenerating ? 'Generating...' : 'Generate'}
                    </button>
                  )}
                  {canRefine && (
                    <button
                      onClick={handleEnhance}
                      disabled={isGenerating || !content}
                      className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
                    >
                      Enhance
                    </button>
                  )}
                  <button
                    onClick={handleSave}
                    disabled={isSaving || !title || !selectedUnitId || !content}
                    className='px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2'
                  >
                    {isSaving ? (
                      <Loader2 className='animate-spin' size={18} />
                    ) : (
                      <Save size={18} />
                    )}
                    {isEditMode ? 'Update' : 'Save'}
                  </button>
                </div>
              </div>
            </div>

            {isGenerating || isRemediating ? (
              <div className='border border-gray-300 rounded-lg p-6 min-h-[400px] bg-gray-50'>
                <div className='flex items-center gap-2 mb-4'>
                  <Loader2 className='animate-spin text-purple-600' size={20} />
                  <span className='text-gray-600 font-medium'>
                    {isRemediating
                      ? 'Remediating content...'
                      : 'Generating content...'}
                  </span>
                </div>
                {streamingContent ? (
                  <div className='prose prose-sm max-w-none'>
                    <div
                      className='whitespace-pre-wrap text-gray-700'
                      dangerouslySetInnerHTML={{ __html: streamingContent }}
                    />
                    <span className='inline-block w-2 h-4 bg-purple-600 animate-pulse ml-1' />
                  </div>
                ) : (
                  <p className='text-gray-500 text-sm'>
                    Starting {isRemediating ? 'remediation' : 'generation'}...
                  </p>
                )}
              </div>
            ) : (
              <RichTextEditor
                content={content}
                onChange={setContent}
                pedagogyHints={[getPedagogyHint(pedagogy)]}
                unitId={selectedUnitId || unitId}
                materialId={contentId}
              />
            )}
          </div>
        </div>

        <div className='space-y-6'>
          <div className='bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-lg font-semibold mb-4'>Teaching Philosophy</h3>
            <PedagogySelector selected={pedagogy} onChange={setPedagogy} />
          </div>

          <div className='bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-lg font-semibold mb-4'>Content Settings</h3>
            <div className='space-y-4'>
              <div>
                <label
                  htmlFor='difficulty-level'
                  className='block text-sm font-medium text-gray-700 mb-1'
                >
                  Difficulty Level
                </label>
                <select
                  id='difficulty-level'
                  className='w-full p-2 border border-gray-300 rounded-lg'
                >
                  <option>Beginner</option>
                  <option>Intermediate</option>
                  <option>Advanced</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor='duration'
                  className='block text-sm font-medium text-gray-700 mb-1'
                >
                  Duration
                </label>
                <input
                  id='duration'
                  type='text'
                  placeholder='e.g., 50 minutes'
                  className='w-full p-2 border border-gray-300 rounded-lg'
                />
              </div>

              <div>
                <label
                  htmlFor='learning-objectives'
                  className='block text-sm font-medium text-gray-700 mb-1'
                >
                  Learning Objectives
                </label>
                <textarea
                  id='learning-objectives'
                  rows={3}
                  className='w-full p-2 border border-gray-300 rounded-lg'
                  placeholder='Enter key learning objectives...'
                />
              </div>
            </div>
          </div>

          {/* Content Quality Section */}
          <div className='bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-lg font-semibold mb-4'>Content Quality</h3>

            <button
              onClick={handleValidate}
              disabled={isValidating || !content.trim()}
              className='w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2 mb-4'
            >
              {isValidating ? (
                <Loader2 className='animate-spin' size={18} />
              ) : (
                <CheckCircle2 size={18} />
              )}
              {isValidating ? 'Validating...' : 'Check Compliance'}
            </button>

            {validationResults && (
              <div className='space-y-3'>
                {/* Overall Status */}
                <div
                  className={`p-3 rounded-lg ${
                    validationResults.overallPassed
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-amber-50 border border-amber-200'
                  }`}
                >
                  <div className='flex items-center gap-2'>
                    {validationResults.overallPassed ? (
                      <CheckCircle2 className='text-green-600' size={18} />
                    ) : (
                      <AlertTriangle className='text-amber-600' size={18} />
                    )}
                    <span
                      className={`font-medium ${
                        validationResults.overallPassed
                          ? 'text-green-700'
                          : 'text-amber-700'
                      }`}
                    >
                      {validationResults.overallPassed
                        ? 'All checks passed'
                        : 'Issues found'}
                    </span>
                  </div>
                  {validationResults.overallScore !== undefined && (
                    <p className='text-sm text-gray-600 mt-1'>
                      Overall score:{' '}
                      {Math.round(validationResults.overallScore)}%
                    </p>
                  )}
                </div>

                {/* Individual Results */}
                {validationResults.results.map((result, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border ${
                      result.passed
                        ? 'bg-white border-gray-200'
                        : 'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className='flex items-center justify-between mb-1'>
                      <span className='font-medium text-sm'>
                        {result.validatorName}
                      </span>
                      {result.passed ? (
                        <CheckCircle2 className='text-green-500' size={16} />
                      ) : (
                        <XCircle className='text-red-500' size={16} />
                      )}
                    </div>
                    <p className='text-xs text-gray-600'>{result.message}</p>
                    {result.score !== undefined && (
                      <p className='text-xs text-gray-500 mt-1'>
                        Score: {result.score}%
                      </p>
                    )}

                    {/* Suggestions */}
                    {result.suggestions && result.suggestions.length > 0 && (
                      <ul className='mt-2 space-y-1'>
                        {result.suggestions.map((suggestion, sIdx) => (
                          <li
                            key={sIdx}
                            className='text-xs text-gray-600 flex items-start gap-1'
                          >
                            <span className='text-gray-400'>•</span>
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    )}

                    {/* Auto-fix button */}
                    {!result.passed && result.remediationPrompt && (
                      <button
                        onClick={() =>
                          handleRemediate(result.validatorName.toLowerCase())
                        }
                        disabled={isRemediating}
                        className='mt-2 w-full px-3 py-1.5 bg-purple-100 text-purple-700 rounded hover:bg-purple-200 disabled:opacity-50 flex items-center justify-center gap-1 text-xs font-medium'
                      >
                        {isRemediating ? (
                          <Loader2 className='animate-spin' size={14} />
                        ) : (
                          <Wand2 size={14} />
                        )}
                        Auto-fix
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {!validationResults && (
              <p className='text-sm text-gray-500'>
                Run validation to check content readability and structure
              </p>
            )}
          </div>

          {/* Plugin Quality Checks */}
          <div className='bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-lg font-semibold mb-4'>Quality Checks</h3>

            <button
              onClick={handlePluginValidation}
              disabled={isRunningPlugins || !content.trim()}
              className='w-full px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 flex items-center justify-center gap-2 mb-3'
            >
              {isRunningPlugins ? (
                <Loader2 className='animate-spin' size={18} />
              ) : (
                <CheckCircle2 size={18} />
              )}
              {isRunningPlugins ? 'Running...' : 'Run Quality Checks'}
            </button>

            {pluginResults && (
              <div className='space-y-3'>
                {/* Overall score */}
                {pluginOverallScore !== null && (
                  <div
                    className={`p-3 rounded-lg ${
                      pluginOverallScore >= 80
                        ? 'bg-green-50 border border-green-200'
                        : pluginOverallScore >= 60
                          ? 'bg-amber-50 border border-amber-200'
                          : 'bg-red-50 border border-red-200'
                    }`}
                  >
                    <div className='flex items-center gap-2'>
                      {pluginOverallScore >= 80 ? (
                        <CheckCircle2 className='text-green-600' size={18} />
                      ) : (
                        <AlertTriangle className='text-amber-600' size={18} />
                      )}
                      <span className='font-medium text-sm'>
                        Overall: {Math.round(pluginOverallScore)}%
                      </span>
                    </div>
                  </div>
                )}

                {/* Per-plugin results */}
                {Object.entries(pluginResults).map(([pluginName, result]) => (
                  <PluginResultCard
                    key={pluginName}
                    name={pluginName}
                    result={result}
                  />
                ))}

                {/* Auto-fix All button */}
                <button
                  onClick={() => handlePluginRemediation()}
                  disabled={isRunningRemediation}
                  className='w-full px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 disabled:opacity-50 flex items-center justify-center gap-2 text-sm font-medium'
                >
                  {isRunningRemediation ? (
                    <Loader2 className='animate-spin' size={16} />
                  ) : (
                    <Wand2 size={16} />
                  )}
                  {isRunningRemediation ? 'Fixing...' : 'Auto-fix All'}
                </button>
              </div>
            )}

            {!pluginResults && (
              <p className='text-sm text-gray-500'>
                Run rule-based checks for spelling, grammar, readability,
                accessibility, and inclusive language.
              </p>
            )}
          </div>

          <div className='bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-lg font-semibold mb-4'>Export Options</h3>
            <div className='space-y-2'>
              <button className='w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2'>
                <Download size={18} />
                Export as Word
              </button>
              <button className='w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2'>
                <Download size={18} />
                Export as PDF
              </button>
              <button className='w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2'>
                <Download size={18} />
                Export as Markdown
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const getPedagogyHint = (style: PedagogyType): string => {
  const hints: Record<PedagogyType, string> = {
    'inquiry-based':
      'Start with thought-provoking questions to encourage exploration.',
    'project-based': 'Include real-world applications and hands-on activities.',
    traditional: 'Focus on clear explanations and structured examples.',
    collaborative: 'Add group activities and discussion prompts.',
    'game-based': 'Incorporate challenges, points, or competitive elements.',
    constructivist: 'Help students build knowledge through guided discovery.',
    'problem-based': 'Present real-world problems that require investigation.',
    experiential: 'Include hands-on experiences and reflective activities.',
    'competency-based':
      'Focus on measurable skills and clear learning outcomes.',
  };
  return hints[style] || '';
};

export default ContentCreator;
