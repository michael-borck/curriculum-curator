/**
 * Session storage rules.
 *
 * Web builds authenticate with the backend's httpOnly session cookie, so the
 * token is never written to JavaScript-readable storage. The packaged desktop
 * app loads the renderer from `file://`, where cross-site cookies are not sent,
 * so it keeps the Bearer token locally (scoped to the app's own renderer).
 */

export const isDesktopClient = (): boolean => {
  if (typeof window === 'undefined') return false;
  return (
    window.location.protocol === 'file:' ||
    Boolean((window as { api?: { isDesktop?: boolean } }).api?.isDesktop)
  );
};

export const getStoredToken = (): string | null =>
  typeof localStorage === 'undefined' ? null : localStorage.getItem('token');

/** Persist the token only on desktop; web discards it in favour of the cookie. */
export const setStoredToken = (token?: string | null): void => {
  if (typeof localStorage === 'undefined') return;
  if (token && isDesktopClient()) {
    localStorage.setItem('token', token);
  } else {
    localStorage.removeItem('token');
  }
};

export const clearStoredToken = (): void => {
  if (typeof localStorage !== 'undefined') localStorage.removeItem('token');
};

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const prefix = `${name}=`;
  const match = document.cookie
    .split(';')
    .map(part => part.trim())
    .find(part => part.startsWith(prefix));
  return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

/** Bearer (desktop) + CSRF header (web cookie sessions). */
export const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {};
  const token = getStoredToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const csrf = readCookie('cc_csrf');
  if (csrf) headers['X-CSRF-Token'] = csrf;
  if (isDesktopClient() && typeof window !== 'undefined') {
    const desktopToken = new URLSearchParams(window.location.search).get(
      'desktopToken'
    );
    if (desktopToken) headers['X-Desktop-Token'] = desktopToken;
  }
  return headers;
};

/** fetch wrapper that sends cookies on web and Bearer on desktop. */
export const fetchWithAuth = (
  input: RequestInfo | URL,
  init: RequestInit = {}
): Promise<Response> =>
  globalThis.fetch(input, {
    ...init,
    credentials: 'include',
    headers: {
      ...getAuthHeaders(),
      ...(init.headers as Record<string, string> | undefined),
    },
  });
