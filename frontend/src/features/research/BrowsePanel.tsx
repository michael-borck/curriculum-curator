import { useState, useRef, useEffect, useCallback } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  RotateCw,
  Camera,
  Globe,
  ExternalLink,
} from 'lucide-react';
import CaptureForm from './CaptureForm';
import type { CapturedPageMetadata } from '../../types/research';

// Electron webview element type (not in standard DOM typings)
interface WebviewElement extends HTMLElement {
  src: string;
  getURL: () => string;
  getTitle: () => string;
  canGoBack: () => boolean;
  canGoForward: () => boolean;
  goBack: () => void;
  goForward: () => void;
  reload: () => void;
  stop: () => void;
  isLoading: () => boolean;
  executeJavaScript: (code: string) => Promise<unknown>;
  addEventListener: (
    event: string,
    handler: (...args: unknown[]) => void
  ) => void;
  removeEventListener: (
    event: string,
    handler: (...args: unknown[]) => void
  ) => void;
}

const QUICK_LINKS = [
  {
    name: 'Google Scholar',
    url: 'https://scholar.google.com',
    description: 'Academic papers, theses, books, and court opinions',
  },
  {
    name: 'Semantic Scholar',
    url: 'https://www.semanticscholar.org',
    description: 'AI-powered research tool for scientific literature',
  },
  {
    name: 'CORE',
    url: 'https://core.ac.uk',
    description: "World's largest collection of open access research papers",
  },
  {
    name: 'arXiv',
    url: 'https://arxiv.org',
    description: 'Open access preprints in STEM fields',
  },
  {
    name: 'PubMed',
    url: 'https://pubmed.ncbi.nlm.nih.gov',
    description: 'Biomedical and life sciences literature',
  },
  {
    name: 'ERIC',
    url: 'https://eric.ed.gov',
    description: 'Education research and information',
  },
];

// Script injected into the webview to extract metadata from the page DOM
const EXTRACTION_SCRIPT = `
(function() {
  function getMeta(nameOrProp) {
    const selectors = [
      'meta[name="' + nameOrProp + '"]',
      'meta[property="' + nameOrProp + '"]',
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) return el.getAttribute('content') || '';
    }
    return '';
  }

  function getAllMeta(prefix) {
    const result = {};
    document.querySelectorAll('meta').forEach(el => {
      const name = el.getAttribute('name') || el.getAttribute('property') || '';
      if (name.startsWith(prefix)) {
        const key = name.replace(prefix, '');
        if (!result[key]) result[key] = [];
        const content = el.getAttribute('content');
        if (content) result[key].push(content);
      }
    });
    return result;
  }

  // Standard citation_* meta tags (Google Scholar, publishers)
  const citation = getAllMeta('citation_');
  const dc = getAllMeta('DC.');
  const og = getAllMeta('og:');

  // Extract DOI from meta tags or page content
  let doi = getMeta('citation_doi') || getMeta('DC.identifier') || '';
  if (!doi) {
    const doiMatch = document.body.innerText.match(/10\\.\\d{4,}[^\\s]*/);
    if (doiMatch) doi = doiMatch[0].replace(/[.,;)\\]]+$/, '');
  }

  // Authors from citation_author or DC.creator
  const authors = (citation['author'] || dc['creator'] || []).filter(Boolean);

  return {
    title: getMeta('citation_title') || getMeta('DC.title') || getMeta('og:title') || document.title || '',
    description: getMeta('citation_abstract') || getMeta('DC.description') || getMeta('og:description') || getMeta('description') || '',
    doi: doi,
    authors: authors,
    publicationDate: getMeta('citation_publication_date') || getMeta('citation_date') || getMeta('DC.date') || '',
    publisher: getMeta('citation_publisher') || getMeta('DC.publisher') || (og['site_name'] ? og['site_name'][0] : '') || '',
    journalName: getMeta('citation_journal_title') || '',
    volume: getMeta('citation_volume') || '',
    issue: getMeta('citation_issue') || '',
    pages: getMeta('citation_firstpage') ? (getMeta('citation_firstpage') + (getMeta('citation_lastpage') ? '-' + getMeta('citation_lastpage') : '')) : '',
    isbn: getMeta('citation_isbn') || '',
    contentText: (document.body.innerText || '').substring(0, 5000),
  };
})()
`;

const BrowsePanel = () => {
  const webviewRef = useRef<WebviewElement | null>(null);
  const addressRef = useRef<HTMLInputElement>(null);

  const [addressBarValue, setAddressBarValue] = useState('');
  const [currentUrl, setCurrentUrl] = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [showStartPage, setShowStartPage] = useState(true);

  // Capture state
  const [showCaptureForm, setShowCaptureForm] = useState(false);
  const [capturedMetadata, setCapturedMetadata] =
    useState<CapturedPageMetadata | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const navigateTo = useCallback((url: string) => {
    let normalised = url.trim();
    if (!normalised) return;
    if (!/^https?:\/\//i.test(normalised)) {
      normalised = 'https://' + normalised;
    }
    setShowStartPage(false);
    setLoadError(null);
    if (webviewRef.current) {
      webviewRef.current.src = normalised;
    }
    setAddressBarValue(normalised);
  }, []);

  const handleAddressKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      navigateTo(addressBarValue);
    }
  };

  // Keyboard shortcut: Cmd/Ctrl+L focuses address bar
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'l') {
        e.preventDefault();
        addressRef.current?.focus();
        addressRef.current?.select();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Attach webview event listeners
  useEffect(() => {
    const wv = webviewRef.current;
    if (!wv) return;

    const onDidNavigate = () => {
      const url = wv.getURL();
      setCurrentUrl(url);
      setAddressBarValue(url);
      setCanGoBack(wv.canGoBack());
      setCanGoForward(wv.canGoForward());
      setLoadError(null);
    };

    const onStartLoading = () => {
      setIsLoading(true);
      setLoadProgress(10);
      setLoadError(null);
    };

    const onStopLoading = () => {
      setIsLoading(false);
      setLoadProgress(100);
      setCanGoBack(wv.canGoBack());
      setCanGoForward(wv.canGoForward());
      const title = wv.getTitle();
      if (title) setPageTitle(title);
    };

    const onTitleUpdated = (_e: unknown) => {
      setPageTitle(wv.getTitle());
    };

    const onDidFailLoad = (..._args: unknown[]) => {
      const errorCode = _args[1] as number;
      const errorDescription = _args[2] as string;
      // Ignore aborted loads (e.g. user navigated away)
      if (errorCode === -3) return;
      setIsLoading(false);
      setLoadProgress(0);
      setLoadError(`Failed to load page: ${errorDescription} (${errorCode})`);
    };

    const onNewWindow = (e: unknown) => {
      const event = e as { url: string };
      if (event.url) {
        navigateTo(event.url);
      }
    };

    wv.addEventListener('did-navigate', onDidNavigate);
    wv.addEventListener('did-navigate-in-page', onDidNavigate);
    wv.addEventListener('did-start-loading', onStartLoading);
    wv.addEventListener('did-stop-loading', onStopLoading);
    wv.addEventListener('page-title-updated', onTitleUpdated);
    wv.addEventListener('did-fail-load', onDidFailLoad);
    wv.addEventListener('new-window', onNewWindow);

    return () => {
      wv.removeEventListener('did-navigate', onDidNavigate);
      wv.removeEventListener('did-navigate-in-page', onDidNavigate);
      wv.removeEventListener('did-start-loading', onStartLoading);
      wv.removeEventListener('did-stop-loading', onStopLoading);
      wv.removeEventListener('page-title-updated', onTitleUpdated);
      wv.removeEventListener('did-fail-load', onDidFailLoad);
      wv.removeEventListener('new-window', onNewWindow);
    };
  }, [navigateTo]);

  // Simulate load progress
  useEffect(() => {
    if (!isLoading) return;
    const interval = setInterval(() => {
      setLoadProgress(prev => Math.min(prev + 15, 90));
    }, 300);
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleCapture = async () => {
    setIsCapturing(true);
    const url = currentUrl || addressBarValue;
    const title = pageTitle || url;

    try {
      // Step 1: Extract metadata from page DOM
      let extracted: Partial<CapturedPageMetadata> = {};
      if (webviewRef.current && !showStartPage) {
        try {
          const result =
            await webviewRef.current.executeJavaScript(EXTRACTION_SCRIPT);
          extracted = result as Partial<CapturedPageMetadata>;
        } catch {
          extracted = { extractionError: 'Could not extract page content' };
        }
      }

      const metadata: CapturedPageMetadata = {
        url,
        title: extracted.title || title,
        description: extracted.description || undefined,
        doi: extracted.doi || undefined,
        authors:
          extracted.authors && extracted.authors.length > 0
            ? extracted.authors
            : undefined,
        publicationDate: extracted.publicationDate || undefined,
        publisher: extracted.publisher || undefined,
        journalName: extracted.journalName || undefined,
        volume: extracted.volume || undefined,
        issue: extracted.issue || undefined,
        pages: extracted.pages || undefined,
        isbn: extracted.isbn || undefined,
        contentText: extracted.contentText || undefined,
        extractionError: extracted.extractionError || undefined,
      };

      setCapturedMetadata(metadata);
      setShowCaptureForm(true);
    } finally {
      setIsCapturing(false);
    }
  };

  const handleCaptureClose = () => {
    setShowCaptureForm(false);
    setCapturedMetadata(null);
  };

  return (
    <div className='flex flex-col h-[calc(100vh-16rem)]'>
      {/* Navigation bar */}
      <div className='flex items-center gap-2 mb-3'>
        <button
          onClick={() => webviewRef.current?.goBack()}
          disabled={!canGoBack}
          className='p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition'
          title='Back'
        >
          <ArrowLeft className='w-4 h-4' />
        </button>
        <button
          onClick={() => webviewRef.current?.goForward()}
          disabled={!canGoForward}
          className='p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition'
          title='Forward'
        >
          <ArrowRight className='w-4 h-4' />
        </button>
        <button
          onClick={() => {
            if (isLoading) {
              webviewRef.current?.stop();
            } else {
              webviewRef.current?.reload();
            }
          }}
          className='p-2 rounded-lg hover:bg-gray-100 transition'
          title={isLoading ? 'Stop' : 'Reload'}
        >
          <RotateCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>

        {/* Address bar */}
        <div className='flex-1 relative'>
          <Globe className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400' />
          <input
            ref={addressRef}
            type='text'
            value={addressBarValue}
            onChange={e => setAddressBarValue(e.target.value)}
            onKeyDown={handleAddressKeyDown}
            placeholder='Enter URL or search...'
            className='w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'
          />
        </div>

        {/* Capture button */}
        <button
          onClick={handleCapture}
          disabled={isCapturing || (showStartPage && !addressBarValue)}
          className='flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition'
        >
          <Camera className='w-4 h-4' />
          {isCapturing ? 'Capturing...' : 'Capture'}
        </button>
      </div>

      {/* Loading progress bar */}
      {isLoading && (
        <div className='h-0.5 bg-gray-200 rounded-full overflow-hidden mb-1'>
          <div
            className='h-full bg-purple-600 transition-all duration-300'
            style={{ width: `${loadProgress}%` }}
          />
        </div>
      )}

      {/* Content area */}
      <div className='flex-1 rounded-lg overflow-hidden border border-gray-200 relative'>
        {showStartPage ? (
          <div className='h-full flex items-center justify-center bg-gray-50 p-8'>
            <div className='max-w-lg w-full'>
              <h2 className='text-lg font-semibold text-gray-900 mb-1 text-center'>
                Browse & Capture
              </h2>
              <p className='text-sm text-gray-500 mb-6 text-center'>
                Browse academic sites and capture pages as research sources
              </p>
              <div className='grid grid-cols-2 gap-3'>
                {QUICK_LINKS.map(link => (
                  <button
                    key={link.url}
                    onClick={() => navigateTo(link.url)}
                    className='flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition text-left'
                  >
                    <ExternalLink className='w-4 h-4 text-purple-500 mt-0.5 shrink-0' />
                    <div>
                      <div className='text-sm font-medium text-gray-900'>
                        {link.name}
                      </div>
                      <div className='text-xs text-gray-500 mt-0.5'>
                        {link.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {loadError && (
              <div className='absolute inset-0 flex items-center justify-center bg-gray-50 z-10'>
                <div className='text-center p-6'>
                  <div className='text-amber-600 text-sm font-medium mb-2'>
                    {loadError}
                  </div>
                  <p className='text-xs text-gray-500'>
                    You can still capture this URL with manual entry
                  </p>
                </div>
              </div>
            )}
            <webview
              ref={webviewRef as React.RefObject<HTMLElement>}
              className='w-full h-full'
            />
          </>
        )}
      </div>

      {/* Page title bar */}
      {!showStartPage && pageTitle && (
        <div className='mt-1 text-xs text-gray-500 truncate'>{pageTitle}</div>
      )}

      {/* Capture form modal */}
      {showCaptureForm && capturedMetadata && (
        <CaptureForm metadata={capturedMetadata} onClose={handleCaptureClose} />
      )}
    </div>
  );
};

export default BrowsePanel;
