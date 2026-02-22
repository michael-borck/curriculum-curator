import { useState } from 'react';
import {
  Link2,
  Loader2,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Award,
  FileText,
  BookOpen,
  Globe,
  Video,
  HelpCircle,
} from 'lucide-react';
import * as researchApi from '../../services/researchApi';
import SourceSelector from './SourceSelector';
import ProposalReview from './ProposalReview';
import type { ActionParams } from './SourceSelector';
import type {
  ExtractedUrlItem,
  SourceInput,
  ResearchStage,
  ResearchAction,
  ScaffoldUnitResponse,
  ComparisonProposal,
  ReadingListProposal,
} from '../../types/research';

const CONTENT_TYPE_ICONS: Record<string, typeof FileText> = {
  paper: FileText,
  syllabus: BookOpen,
  blog: Globe,
  video: Video,
  unknown: HelpCircle,
};

const CONTENT_TYPE_COLORS: Record<string, string> = {
  paper: 'bg-blue-50 text-blue-700',
  syllabus: 'bg-green-50 text-green-700',
  blog: 'bg-orange-50 text-orange-700',
  video: 'bg-pink-50 text-pink-700',
  unknown: 'bg-gray-50 text-gray-700',
};

const UrlExtractPanel = () => {
  const [urlText, setUrlText] = useState('');
  const [summarize, setSummarize] = useState(true);
  const [stage, setStage] = useState<ResearchStage>('input');
  const [results, setResults] = useState<ExtractedUrlItem[]>([]);
  const [extractStats, setExtractStats] = useState({
    successful: 0,
    failed: 0,
  });
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [proposing, setProposing] = useState(false);

  // Proposal state
  const [proposalAction, setProposalAction] = useState<ResearchAction | null>(
    null
  );
  const [proposal, setProposal] = useState<
    ScaffoldUnitResponse | ComparisonProposal | ReadingListProposal | null
  >(null);

  const parseUrls = (): string[] => {
    return urlText
      .split('\n')
      .map(line => line.trim())
      .filter(
        line =>
          line.length > 0 &&
          (line.startsWith('http://') || line.startsWith('https://'))
      );
  };

  const handleExtract = async () => {
    const urls = parseUrls();
    if (urls.length === 0) return;
    setError(null);
    setStage('searching');
    try {
      const res = await researchApi.extractUrls({
        urls,
        summarize,
      });
      setResults(res.results);
      setExtractStats({ successful: res.successful, failed: res.failed });
      // Auto-select successful ones
      const successIdxs = new Set<number>();
      res.results.forEach((r, i) => {
        if (!r.error) successIdxs.add(i);
      });
      setSelected(successIdxs);
      setStage('results');
    } catch (e: unknown) {
      const msg =
        e instanceof Error ? e.message : 'Extraction failed. Please try again.';
      setError(msg);
      setStage('input');
    }
  };

  const toggleSelect = (idx: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const selectedSources: SourceInput[] = [...selected].map(i => ({
    title: results[i].title || results[i].url,
    url: results[i].url,
    summary: results[i].summary,
    keyPoints: results[i].keyPoints,
  }));

  const handleAction = async (actionParams: ActionParams) => {
    setProposing(true);
    setError(null);
    setStage('proposing');
    try {
      let result:
        | ScaffoldUnitResponse
        | ComparisonProposal
        | ReadingListProposal;
      if (actionParams.action === 'scaffold') {
        result = await researchApi.proposeScaffold({
          sourceData: selectedSources,
          unitTitle: actionParams.params.unitTitle,
          unitDescription: actionParams.params.unitDescription,
          durationWeeks: actionParams.params.durationWeeks,
          pedagogyStyle: actionParams.params.pedagogyStyle,
        });
      } else if (actionParams.action === 'compare') {
        result = await researchApi.proposeComparison({
          sourceData: selectedSources,
          unitId: actionParams.params.unitId,
        });
      } else {
        result = await researchApi.proposeReadingList({
          sourceData: selectedSources,
          unitId: actionParams.params.unitId,
        });
      }
      setProposalAction(actionParams.action);
      setProposal(result);
      setStage('review');
    } catch (e: unknown) {
      const msg =
        e instanceof Error
          ? e.message
          : 'Failed to generate proposal. Please try again.';
      setError(msg);
      setStage('select-action');
    } finally {
      setProposing(false);
    }
  };

  const handleReset = () => {
    setStage('input');
    setResults([]);
    setSelected(new Set());
    setProposal(null);
    setProposalAction(null);
    setError(null);
    setUrlText('');
  };

  const urlCount = parseUrls().length;

  return (
    <div className='space-y-6'>
      {/* URL Input */}
      {(stage === 'input' || stage === 'searching') && (
        <div className='space-y-4'>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Paste URLs (one per line)
            </label>
            <textarea
              value={urlText}
              onChange={e => setUrlText(e.target.value)}
              rows={6}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm'
              placeholder={`https://example.com/paper1\nhttps://example.com/syllabus\nhttps://example.com/article`}
            />
            <p className='text-xs text-gray-500 mt-1'>
              {urlCount} URL{urlCount !== 1 ? 's' : ''} detected (max 20)
            </p>
          </div>

          <div className='flex items-center justify-between'>
            <label className='flex items-center gap-2 text-sm'>
              <input
                type='checkbox'
                checked={summarize}
                onChange={e => setSummarize(e.target.checked)}
                className='h-4 w-4 text-purple-600 rounded border-gray-300'
              />
              Summarise with AI
            </label>

            <button
              onClick={handleExtract}
              disabled={urlCount === 0 || stage === 'searching'}
              className='px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2'
            >
              {stage === 'searching' ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                <Link2 className='w-4 h-4' />
              )}
              Extract Content
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className='p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-red-800'>{error}</span>
        </div>
      )}

      {/* Results */}
      {(stage === 'results' ||
        stage === 'select-action' ||
        stage === 'proposing') && (
        <>
          <div className='flex items-center justify-between'>
            <div className='text-sm text-gray-500'>
              {extractStats.successful} extracted
              {extractStats.failed > 0 && (
                <span className='text-red-500'>
                  , {extractStats.failed} failed
                </span>
              )}
            </div>
            <div className='flex gap-2'>
              {selected.size > 0 && stage === 'results' && (
                <button
                  onClick={() => setStage('select-action')}
                  className='px-4 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition'
                >
                  Continue with {selected.size} selected
                </button>
              )}
              <button
                onClick={handleReset}
                className='px-4 py-1.5 text-gray-600 text-sm border rounded-lg hover:bg-gray-50 transition'
              >
                Start Over
              </button>
            </div>
          </div>

          {stage !== 'select-action' && stage !== 'proposing' && (
            <div className='space-y-3'>
              {results.map((item, i) => {
                const TypeIcon =
                  CONTENT_TYPE_ICONS[item.contentType] ||
                  CONTENT_TYPE_ICONS.unknown;
                const typeColor =
                  CONTENT_TYPE_COLORS[item.contentType] ||
                  CONTENT_TYPE_COLORS.unknown;

                return (
                  <div
                    key={i}
                    className={`border rounded-lg transition ${
                      item.error
                        ? 'border-red-200 bg-red-50/30'
                        : selected.has(i)
                          ? 'border-purple-300 bg-purple-50/50'
                          : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className='flex items-start gap-3 p-4'>
                      {!item.error && (
                        <input
                          type='checkbox'
                          checked={selected.has(i)}
                          onChange={() => toggleSelect(i)}
                          className='mt-1 h-4 w-4 text-purple-600 rounded border-gray-300'
                        />
                      )}
                      <div className='flex-1 min-w-0'>
                        <div className='flex items-start justify-between gap-2'>
                          <div className='flex items-center gap-2'>
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${typeColor}`}
                            >
                              <TypeIcon className='w-3 h-3' />
                              {item.contentType}
                            </span>
                            {item.title ? (
                              <a
                                href={item.url}
                                target='_blank'
                                rel='noreferrer'
                                className='font-medium text-sm text-blue-700 hover:underline flex items-center gap-1'
                              >
                                {item.title}
                                <ExternalLink className='w-3 h-3 flex-shrink-0' />
                              </a>
                            ) : (
                              <a
                                href={item.url}
                                target='_blank'
                                rel='noreferrer'
                                className='text-sm text-blue-600 hover:underline truncate'
                              >
                                {item.url}
                              </a>
                            )}
                          </div>
                          {!item.error && (
                            <span className='flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-medium'>
                              <Award className='w-3 h-3' />
                              {(item.academicScore * 100).toFixed(0)}
                            </span>
                          )}
                        </div>

                        {item.error && (
                          <p className='text-sm text-red-600 mt-1'>
                            {item.error}
                          </p>
                        )}

                        {item.summary && (
                          <p
                            className={`text-sm text-gray-600 mt-2 ${expandedIdx === i ? '' : 'line-clamp-2'}`}
                          >
                            {item.summary}
                          </p>
                        )}

                        {item.keyPoints.length > 0 && expandedIdx === i && (
                          <ul className='mt-2 text-xs text-gray-600 list-disc list-inside space-y-0.5'>
                            {item.keyPoints.map((kp, j) => (
                              <li key={j}>{kp}</li>
                            ))}
                          </ul>
                        )}

                        {(item.summary || item.keyPoints.length > 0) && (
                          <button
                            onClick={() =>
                              setExpandedIdx(expandedIdx === i ? null : i)
                            }
                            className='text-xs text-purple-600 hover:underline mt-1 flex items-center gap-0.5'
                          >
                            {expandedIdx === i ? (
                              <>
                                Show less <ChevronUp className='w-3 h-3' />
                              </>
                            ) : (
                              <>
                                Show more <ChevronDown className='w-3 h-3' />
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Source Selector */}
          {(stage === 'select-action' || stage === 'proposing') && (
            <SourceSelector
              sources={selectedSources}
              onAction={handleAction}
              loading={proposing}
            />
          )}
        </>
      )}

      {/* Proposal Review */}
      {stage === 'review' && proposal && proposalAction && (
        <div>
          <button
            onClick={() => setStage('select-action')}
            className='mb-4 text-sm text-purple-600 hover:underline'
          >
            &larr; Back to action selection
          </button>
          <ProposalReview
            action={proposalAction}
            proposal={proposal}
            onDone={handleReset}
          />
        </div>
      )}

      {/* Done */}
      {stage === 'done' && (
        <div className='text-center py-8'>
          <p className='text-gray-600 mb-4'>Action completed successfully.</p>
          <button
            onClick={handleReset}
            className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition'
          >
            Import More URLs
          </button>
        </div>
      )}
    </div>
  );
};

export default UrlExtractPanel;
