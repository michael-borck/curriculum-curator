import { useState, useEffect } from 'react';
import { X, AlertTriangle, Loader2, BookOpen, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import type { CapturedPageMetadata } from '../../types/research';
import {
  saveFromCapture,
  crossrefLookup,
} from '../../services/researchSourceApi';

interface CaptureFormProps {
  metadata: CapturedPageMetadata;
  onClose: () => void;
}

interface CrossRefData {
  title?: string | undefined;
  authors?: string[] | undefined;
  publisher?: string | undefined;
  journalName?: string | undefined;
  volume?: string | undefined;
  issue?: string | undefined;
  pages?: string | undefined;
  publicationDate?: string | undefined;
  isbn?: string | undefined;
}

const SOURCE_TYPES = [
  { value: 'journal_article', label: 'Journal Article' },
  { value: 'book', label: 'Book' },
  { value: 'book_chapter', label: 'Book Chapter' },
  { value: 'conference_paper', label: 'Conference Paper' },
  { value: 'thesis', label: 'Thesis' },
  { value: 'website', label: 'Website' },
  { value: 'report', label: 'Report' },
  { value: 'video', label: 'Video' },
  { value: 'other', label: 'Other' },
];

const CaptureForm: React.FC<CaptureFormProps> = ({ metadata, onClose }) => {
  const [url, setUrl] = useState(metadata.url);
  const [title, setTitle] = useState(metadata.title);
  const [description, setDescription] = useState(metadata.description ?? '');
  const [doi, setDoi] = useState(metadata.doi ?? '');
  const [authorsText, setAuthorsText] = useState(
    (metadata.authors ?? []).join(', ')
  );
  const [publicationDate, setPublicationDate] = useState(
    metadata.publicationDate ?? ''
  );
  const [publisher, setPublisher] = useState(metadata.publisher ?? '');
  const [journalName, setJournalName] = useState(metadata.journalName ?? '');
  const [volume, setVolume] = useState(metadata.volume ?? '');
  const [issue, setIssue] = useState(metadata.issue ?? '');
  const [pages, setPages] = useState(metadata.pages ?? '');
  const [isbn, setIsbn] = useState(metadata.isbn ?? '');
  const [sourceType, setSourceType] = useState('website');
  const [manualContent, setManualContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [saved, setSaved] = useState(false);

  const hasExtractionError =
    !!metadata.extractionError || !metadata.contentText;
  const contentPreview = metadata.contentText
    ? metadata.contentText.substring(0, 500) +
      (metadata.contentText.length > 500 ? '...' : '')
    : null;

  // Auto-detect source type from DOI or journal name
  useEffect(() => {
    if (journalName || doi) {
      setSourceType('journal_article');
    }
  }, [journalName, doi]);

  // CrossRef DOI enrichment
  useEffect(() => {
    if (!doi) return;
    let cancelled = false;

    const enrichFromCrossRef = async () => {
      setEnriching(true);
      try {
        const resp = await crossrefLookup(doi);
        const data = resp.data as CrossRefData;
        if (cancelled) return;

        // Only fill empty fields — don't overwrite user edits
        if (data.title && !title) setTitle(data.title);
        if (data.authors && data.authors.length > 0 && !authorsText) {
          setAuthorsText(data.authors.join(', '));
        }
        if (data.publisher && !publisher) setPublisher(data.publisher);
        if (data.journalName && !journalName) setJournalName(data.journalName);
        if (data.volume && !volume) setVolume(data.volume);
        if (data.issue && !issue) setIssue(data.issue);
        if (data.pages && !pages) setPages(data.pages);
        if (data.publicationDate && !publicationDate)
          setPublicationDate(data.publicationDate);
        if (data.isbn && !isbn) setIsbn(data.isbn);
      } catch {
        // DOI enrichment is opportunistic — silent failure
      } finally {
        if (!cancelled) setEnriching(false);
      }
    };

    enrichFromCrossRef();
    return () => {
      cancelled = true;
    };
    // Only run when DOI changes, not on every field change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doi]);

  const handleSave = async () => {
    if (!url || !title) {
      toast.error('URL and title are required');
      return;
    }

    setSaving(true);
    try {
      // Parse authors from comma-separated string into first/last name pairs
      const authorsList = authorsText
        .split(',')
        .map(a => a.trim())
        .filter(Boolean);

      await saveFromCapture({
        url,
        title,
        description: description || undefined,
        doi: doi || undefined,
        authors: authorsList.length > 0 ? authorsList : undefined,
        publicationDate: publicationDate || undefined,
        publisher: publisher || undefined,
        journalName: journalName || undefined,
        volume: volume || undefined,
        issue: issue || undefined,
        pages: pages || undefined,
        isbn: isbn || undefined,
        sourceType,
        contentText: manualContent || metadata.contentText || undefined,
        academicScore: metadata.academicScore,
      });

      setSaved(true);
      toast.success('Source saved to library');
      setTimeout(onClose, 1000);
    } catch {
      toast.error('Failed to save source');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className='fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4'>
      <div className='bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto'>
        {/* Header */}
        <div className='flex items-center justify-between p-4 border-b'>
          <div className='flex items-center gap-2'>
            <BookOpen className='w-5 h-5 text-purple-600' />
            <h2 className='text-lg font-semibold'>Capture Source</h2>
            {enriching && (
              <span className='flex items-center gap-1 text-xs text-purple-600'>
                <Loader2 className='w-3 h-3 animate-spin' />
                Enriching from CrossRef...
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className='p-1 hover:bg-gray-100 rounded-lg transition'
          >
            <X className='w-5 h-5' />
          </button>
        </div>

        <div className='p-4 space-y-4'>
          {/* Extraction warning */}
          {hasExtractionError && (
            <div className='flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg'>
              <AlertTriangle className='w-4 h-4 text-amber-600 mt-0.5 shrink-0' />
              <div>
                <p className='text-sm text-amber-800 font-medium'>
                  Page content could not be fully extracted
                </p>
                <p className='text-xs text-amber-600 mt-1'>
                  You can paste content or an abstract below to improve metadata
                </p>
              </div>
            </div>
          )}

          {/* Academic score badge */}
          {metadata.academicScore != null && metadata.academicScore > 0 && (
            <div className='flex items-center gap-2'>
              <span className='text-xs font-medium text-gray-500'>
                Academic Score:
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  metadata.academicScore >= 0.7
                    ? 'bg-green-100 text-green-700'
                    : metadata.academicScore >= 0.4
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-600'
                }`}
              >
                {Math.round(metadata.academicScore * 100)}%
              </span>
            </div>
          )}

          {/* URL */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              URL
            </label>
            <input
              type='url'
              value={url}
              onChange={e => setUrl(e.target.value)}
              className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            />
          </div>

          {/* Title */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Title
            </label>
            <input
              type='text'
              value={title}
              onChange={e => setTitle(e.target.value)}
              className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            />
          </div>

          {/* Two-column layout for metadata */}
          <div className='grid grid-cols-2 gap-4'>
            {/* DOI */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                DOI
              </label>
              <input
                type='text'
                value={doi}
                onChange={e => setDoi(e.target.value)}
                placeholder='10.xxxx/...'
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>

            {/* Source type */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Source Type
              </label>
              <select
                value={sourceType}
                onChange={e => setSourceType(e.target.value)}
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              >
                {SOURCE_TYPES.map(t => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Publication date */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Publication Date
              </label>
              <input
                type='text'
                value={publicationDate}
                onChange={e => setPublicationDate(e.target.value)}
                placeholder='2024 or 2024-03-15'
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>

            {/* Publisher */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Publisher
              </label>
              <input
                type='text'
                value={publisher}
                onChange={e => setPublisher(e.target.value)}
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>

            {/* Journal */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Journal Name
              </label>
              <input
                type='text'
                value={journalName}
                onChange={e => setJournalName(e.target.value)}
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>

            {/* ISBN */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                ISBN
              </label>
              <input
                type='text'
                value={isbn}
                onChange={e => setIsbn(e.target.value)}
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>

            {/* Volume */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Volume
              </label>
              <input
                type='text'
                value={volume}
                onChange={e => setVolume(e.target.value)}
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>

            {/* Issue */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Issue
              </label>
              <input
                type='text'
                value={issue}
                onChange={e => setIssue(e.target.value)}
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>

            {/* Pages */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Pages
              </label>
              <input
                type='text'
                value={pages}
                onChange={e => setPages(e.target.value)}
                placeholder='123-145'
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>
          </div>

          {/* Authors */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Authors (comma-separated)
            </label>
            <input
              type='text'
              value={authorsText}
              onChange={e => setAuthorsText(e.target.value)}
              placeholder='Jane Smith, John Doe'
              className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            />
          </div>

          {/* Description */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Description / Abstract
            </label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-y'
            />
          </div>

          {/* Content preview or manual paste */}
          {contentPreview && !hasExtractionError ? (
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Content Preview
              </label>
              <div className='p-3 bg-gray-50 rounded-lg text-xs text-gray-600 max-h-32 overflow-y-auto whitespace-pre-wrap'>
                {contentPreview}
              </div>
            </div>
          ) : (
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Paste content or abstract here
              </label>
              <textarea
                value={manualContent}
                onChange={e => setManualContent(e.target.value)}
                rows={4}
                placeholder='Paste the page content, abstract, or key text here...'
                className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-y'
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className='flex items-center justify-end gap-3 p-4 border-t bg-gray-50 rounded-b-xl'>
          <button
            onClick={onClose}
            className='px-4 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded-lg transition'
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || saved || !url || !title}
            className='flex items-center gap-2 px-5 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition'
          >
            {saved ? (
              <>
                <CheckCircle className='w-4 h-4' />
                Saved
              </>
            ) : saving ? (
              <>
                <Loader2 className='w-4 h-4 animate-spin' />
                Saving...
              </>
            ) : (
              'Save to Library'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CaptureForm;
