/**
 * Single source of truth for where the backend API lives.
 *
 * - Web (served same-origin by the backend): relative `/api`.
 * - Packaged desktop (Electron loads the renderer over `file://`, which has no
 *   origin): target the bundled backend directly on localhost.
 * - Override for either via the `VITE_API_URL` build env.
 */
function resolveApiOrigin(): string {
  // Explicit override wins in every mode.
  const envUrl = import.meta.env.VITE_API_URL as string | undefined;
  if (envUrl) {
    return envUrl.replace(/\/$/, '');
  }
  // Packaged Electron: the renderer is loaded from disk over file://, so a
  // relative `/api` request would resolve to `file:///api/...` and fail.
  if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
    // The desktop main process picks a free port per launch and passes it in.
    const port = new URLSearchParams(window.location.search).get('backendPort');
    return `http://127.0.0.1:${port || '8000'}`;
  }
  return '';
}

/** Scheme + host of the backend, or '' for same-origin web. */
export const API_ORIGIN: string = resolveApiOrigin();

/** Base URL for the JSON API (axios baseURL and fetch prefixes). */
export const API_BASE_URL: string = `${API_ORIGIN}/api`;
