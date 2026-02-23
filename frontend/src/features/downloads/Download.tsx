import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  Monitor,
  Apple,
  Download as DownloadIcon,
  Terminal,
  Github,
  ArrowRight,
  ExternalLink,
  Copy,
  Check,
  AlertCircle,
} from 'lucide-react';

type Platform = 'mac-arm' | 'mac-intel' | 'windows' | 'linux' | 'unknown';

interface ReleaseAsset {
  name: string;
  browser_download_url: string;
  size: number;
}

interface ReleaseInfo {
  tag_name: string;
  html_url: string;
  assets: ReleaseAsset[];
}

const GITHUB_REPO = 'michael-borck/curriculum-curator';
const RELEASES_URL = `https://github.com/${GITHUB_REPO}/releases`;

function detectPlatform(): Platform {
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes('mac')) {
    // Check for Apple Silicon
    // navigator.userAgent doesn't reliably distinguish, but we default to arm64
    // since most modern Macs are Apple Silicon
    return 'mac-arm';
  }
  if (ua.includes('win')) return 'windows';
  if (ua.includes('linux')) return 'linux';
  return 'unknown';
}

function findAsset(
  assets: ReleaseAsset[],
  platform: Platform
): ReleaseAsset | undefined {
  return assets.find(a => {
    const name = a.name.toLowerCase();
    switch (platform) {
      case 'mac-arm':
        return name.endsWith('.dmg') && name.includes('arm64');
      case 'mac-intel':
        return name.endsWith('.dmg') && !name.includes('arm64');
      case 'windows':
        return name.endsWith('.exe');
      case 'linux':
        return name.endsWith('.appimage');
      default:
        return false;
    }
  });
}

function formatSize(bytes: number): string {
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(0)} MB`;
}

const platformLabels: Record<Platform, string> = {
  'mac-arm': 'macOS (Apple Silicon)',
  'mac-intel': 'macOS (Intel)',
  windows: 'Windows',
  linux: 'Linux',
  unknown: 'Your Platform',
};

const platformIcons: Record<Platform, typeof Monitor> = {
  'mac-arm': Apple,
  'mac-intel': Apple,
  windows: Monitor,
  linux: Terminal,
  unknown: DownloadIcon,
};

const Download = () => {
  const navigate = useNavigate();
  const [platform] = useState<Platform>(detectPlatform);
  const [release, setRelease] = useState<ReleaseInfo | null>(null);
  const [error, setError] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    window
      .fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`)
      .then(res => {
        if (!res.ok) throw new Error('GitHub API error');
        return res.json() as Promise<ReleaseInfo>;
      })
      .then(setRelease)
      .catch(() => setError(true));
  }, []);

  const handleCopyDocker = () => {
    void navigator.clipboard.writeText(
      'docker compose up -d curriculum-curator'
    );
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const primaryAsset = release ? findAsset(release.assets, platform) : null;
  const otherPlatforms: Platform[] = (
    ['mac-arm', 'mac-intel', 'windows', 'linux'] as const
  ).filter(p => p !== platform);

  const version = release?.tag_name ?? '';

  return (
    <div className='min-h-screen bg-white'>
      {/* Navigation */}
      <nav className='bg-white px-6 md:px-8 py-4 flex justify-between items-center border-b border-gray-100'>
        <div className='flex items-center gap-2'>
          <GraduationCap className='w-7 h-7 text-purple-600' />
          <span className='text-lg font-bold text-gray-900'>
            Curriculum Curator
          </span>
        </div>
        <div className='flex items-center gap-4'>
          <button
            onClick={() => navigate('/')}
            className='text-gray-600 hover:text-gray-900 transition-colors font-medium text-sm'
          >
            Back to Home
          </button>
          <button
            onClick={() => navigate('/?login=true')}
            className='bg-purple-600 text-white px-5 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm'
          >
            Sign In
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className='bg-gradient-to-br from-purple-50 via-white to-indigo-50 px-6 md:px-8 py-16 md:py-20'>
        <div className='max-w-4xl mx-auto text-center'>
          <h1 className='text-4xl md:text-5xl font-bold text-gray-900 mb-4 leading-tight'>
            Install Curriculum Curator
          </h1>
          <p className='text-lg md:text-xl text-gray-600 max-w-2xl mx-auto'>
            Privacy-first, local-first. Your curriculum data stays on your
            machine.
          </p>
        </div>
      </section>

      {/* Desktop App Section */}
      <section className='px-6 md:px-8 py-16'>
        <div className='max-w-3xl mx-auto'>
          <h2 className='text-2xl font-bold text-gray-900 mb-8 text-center'>
            Desktop App
          </h2>

          {error ? (
            <div className='text-center p-8 bg-gray-50 rounded-xl border border-gray-200'>
              <AlertCircle className='w-10 h-10 text-gray-400 mx-auto mb-3' />
              <p className='text-gray-600 mb-4'>
                Could not fetch the latest release.
              </p>
              <a
                href={RELEASES_URL}
                target='_blank'
                rel='noopener noreferrer'
                className='inline-flex items-center gap-2 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium'
              >
                View All Releases on GitHub
                <ExternalLink className='w-4 h-4' />
              </a>
            </div>
          ) : (
            <>
              {/* Primary download */}
              <div className='text-center mb-8'>
                {primaryAsset ? (
                  <>
                    <a
                      href={primaryAsset.browser_download_url}
                      className='inline-flex items-center gap-3 bg-purple-600 text-white px-8 py-4 rounded-xl hover:bg-purple-700 transition-colors font-semibold text-lg shadow-lg shadow-purple-200'
                    >
                      {(() => {
                        const Icon = platformIcons[platform];
                        return <Icon className='w-6 h-6' />;
                      })()}
                      Download for {platformLabels[platform]}
                    </a>
                    <p className='text-sm text-gray-500 mt-3'>
                      {primaryAsset.name} ({formatSize(primaryAsset.size)})
                    </p>
                  </>
                ) : release ? (
                  <a
                    href={release.html_url}
                    className='inline-flex items-center gap-3 bg-purple-600 text-white px-8 py-4 rounded-xl hover:bg-purple-700 transition-colors font-semibold text-lg shadow-lg shadow-purple-200'
                  >
                    <DownloadIcon className='w-6 h-6' />
                    View Downloads
                  </a>
                ) : (
                  <div className='inline-flex items-center gap-3 bg-gray-200 text-gray-500 px-8 py-4 rounded-xl font-semibold text-lg'>
                    <DownloadIcon className='w-6 h-6' />
                    Loading...
                  </div>
                )}
              </div>

              {/* Other platforms */}
              {release && (
                <div className='flex flex-wrap justify-center gap-4 mb-6'>
                  {otherPlatforms.map(p => {
                    const asset = findAsset(release.assets, p);
                    if (!asset) return null;
                    const Icon = platformIcons[p];
                    return (
                      <a
                        key={p}
                        href={asset.browser_download_url}
                        className='inline-flex items-center gap-2 text-purple-600 hover:text-purple-800 transition-colors font-medium text-sm border border-purple-200 px-4 py-2 rounded-lg hover:bg-purple-50'
                      >
                        <Icon className='w-4 h-4' />
                        {platformLabels[p]}
                      </a>
                    );
                  })}
                </div>
              )}

              {/* Version + all releases link */}
              {release && (
                <p className='text-center text-sm text-gray-500'>
                  {version && <span>Version {version.replace(/^v/, '')}</span>}
                  {version && ' \u00B7 '}
                  <a
                    href={RELEASES_URL}
                    target='_blank'
                    rel='noopener noreferrer'
                    className='text-purple-600 hover:text-purple-800 underline'
                  >
                    All releases
                  </a>
                </p>
              )}
            </>
          )}
        </div>
      </section>

      {/* Docker Section */}
      <section className='px-6 md:px-8 py-16 bg-gray-50'>
        <div className='max-w-3xl mx-auto'>
          <h2 className='text-2xl font-bold text-gray-900 mb-2 text-center'>
            Self-Host with Docker
          </h2>
          <p className='text-gray-600 text-center mb-8'>
            Run your own instance on any server.
          </p>

          <div className='bg-gray-900 rounded-xl p-6 relative'>
            <code className='text-green-400 text-sm md:text-base font-mono'>
              docker compose up -d curriculum-curator
            </code>
            <button
              onClick={handleCopyDocker}
              className='absolute top-4 right-4 text-gray-400 hover:text-white transition-colors'
              aria-label='Copy command'
            >
              {copied ? (
                <Check className='w-5 h-5 text-green-400' />
              ) : (
                <Copy className='w-5 h-5' />
              )}
            </button>
          </div>

          <p className='text-center mt-6 text-sm text-gray-500'>
            See the{' '}
            <a
              href={`https://github.com/${GITHUB_REPO}#deployment`}
              target='_blank'
              rel='noopener noreferrer'
              className='text-purple-600 hover:text-purple-800 underline'
            >
              deployment guide
            </a>{' '}
            for full setup instructions.
          </p>
        </div>
      </section>

      {/* Source Section */}
      <section className='px-6 md:px-8 py-12'>
        <div className='max-w-3xl mx-auto text-center'>
          <a
            href={`https://github.com/${GITHUB_REPO}`}
            target='_blank'
            rel='noopener noreferrer'
            className='inline-flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors font-medium'
          >
            <Github className='w-5 h-5' />
            View Source on GitHub
            <ExternalLink className='w-4 h-4' />
          </a>
        </div>
      </section>

      {/* Footer CTA */}
      <section className='px-6 md:px-8 py-12 bg-purple-50 border-t border-purple-100'>
        <div className='max-w-3xl mx-auto text-center'>
          <p className='text-gray-600 mb-4'>
            Or sign in to the hosted version — no installation needed.
          </p>
          <button
            onClick={() => navigate('/?login=true')}
            className='inline-flex items-center gap-2 text-purple-600 hover:text-purple-800 transition-colors font-semibold'
          >
            Sign In
            <ArrowRight className='w-4 h-4' />
          </button>
        </div>
      </section>

      {/* Footer */}
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

export default Download;
