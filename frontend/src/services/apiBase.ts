/**
 * Single source of truth for where the backend API lives.
 *
 * - Web (served same-origin by the backend): relative `/api`.
 * - Packaged desktop (Electron loads the renderer over `file://`, which has no
 *   origin): target the bundled backend directly on localhost.
 * - Override for either via the `VITE_API_URL` build env.
 */
function resolveApiOrigin(): string {
  // Packaged Electron: the renderer is loaded from disk over file://, so a
  // relative `/api` request would resolve to `file:///api/...` and fail.
  if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
    return 'http://127.0.0.1:8000';
  }
  const envUrl = import.meta.env.VITE_API_URL as string | undefined;
  if (envUrl) {
    return envUrl.replace(/\/$/, '');
  }
  return '';
}

/** Scheme + host of the backend, or '' for same-origin web. */
export const API_ORIGIN: string = resolveApiOrigin();

/** Base URL for the JSON API (axios baseURL and fetch prefixes). */
export const API_BASE_URL: string = `${API_ORIGIN}/api`;
