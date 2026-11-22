/** Small URL guards for imported/embeddable content. */

const YOUTUBE_EMBED_HOSTS = new Set([
  'www.youtube.com',
  'youtube.com',
  'www.youtube-nocookie.com',
  'youtube-nocookie.com',
]);

export function isSafeHttpUrl(value: unknown): value is string {
  if (typeof value !== 'string' || !value.trim()) return false;
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

export function isSafeYoutubeEmbed(value: unknown): value is string {
  if (!isSafeHttpUrl(value)) return false;
  const url = new URL(value);
  return (
    YOUTUBE_EMBED_HOSTS.has(url.hostname.toLowerCase()) &&
    url.pathname.startsWith('/embed/')
  );
}
