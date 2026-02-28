/**
 * Content API client — typed wrappers for content CRUD + versioning endpoints.
 *
 * Backend routes live under /api/units/{unitId}/content/...
 */

import api from './api';
import type { Content } from '../types';

// ─── Export Types ────────────────────────────────────────────────────────────

export interface ExportAvailability {
  pandoc: boolean;
  pandocVersion: string | null;
  typst: boolean;
  typstVersion: string | null;
  pdfAvailable: boolean;
  htmlAvailable: boolean;
  docxAvailable: boolean;
  pptxAvailable: boolean;
}

// ─── Version History Types ───────────────────────────────────────────────────

export interface ContentVersion {
  commit: string;
  date: string;
  message: string;
  authorEmail: string | null;
}

export interface ContentHistory {
  contentId: string;
  versions: ContentVersion[];
}

export interface ContentDiff {
  contentId: string;
  oldCommit: string;
  newCommit: string;
  diff: string;
}

export interface ContentAtVersion {
  commit: string;
  body: string;
}

// ─── CRUD ────────────────────────────────────────────────────────────────────

export const contentApi = {
  /** List all content for a unit (metadata only). */
  list(unitId: string, week?: number) {
    const params = week != null ? { week } : undefined;
    return api.get<{ contents: Content[]; total: number }>(
      `/units/${unitId}/content`,
      { params }
    );
  },

  /** Get a single content item with body. */
  get(unitId: string, contentId: string) {
    return api.get<Content>(`/units/${unitId}/content/${contentId}`);
  },

  /** Create new content. */
  create(
    unitId: string,
    data: {
      title: string;
      contentType: string;
      body?: string;
      summary?: string;
      weekNumber?: number;
      estimatedDurationMinutes?: number;
    }
  ) {
    return api.post<Content>(`/units/${unitId}/content`, data);
  },

  /** Update content (new Git version if body changes). */
  update(
    unitId: string,
    contentId: string,
    data: {
      title?: string;
      body?: string;
      contentJson?: Record<string, unknown>;
      summary?: string;
      weekNumber?: number;
      estimatedDurationMinutes?: number;
    }
  ) {
    return api.put<Content>(`/units/${unitId}/content/${contentId}`, data);
  },

  /** Delete content. */
  delete(unitId: string, contentId: string) {
    return api.delete(`/units/${unitId}/content/${contentId}`);
  },

  // ─── Version History ─────────────────────────────────────────────────────

  /** Get commit history for a content item. */
  history(unitId: string, contentId: string, limit = 20) {
    return api.get<ContentHistory>(
      `/units/${unitId}/content/${contentId}/history`,
      { params: { limit } }
    );
  },

  /** Get content body at a specific commit. */
  versionBody(unitId: string, contentId: string, commit: string) {
    return api.get<ContentAtVersion>(
      `/units/${unitId}/content/${contentId}/version/${commit}`
    );
  },

  /** Get a Git diff between two commits. */
  diff(
    unitId: string,
    contentId: string,
    oldCommit: string,
    newCommit = 'HEAD'
  ) {
    return api.get<ContentDiff>(`/units/${unitId}/content/${contentId}/diff`, {
      params: { old_commit: oldCommit, new_commit: newCommit },
    });
  },

  /** Revert to a previous commit (creates a new commit). */
  revert(unitId: string, contentId: string, commit: string) {
    return api.post<Content>(`/units/${unitId}/content/${contentId}/revert`, {
      commit,
    });
  },

  // ─── Export ─────────────────────────────────────────────────────────────────

  /** Check which export formats the backend can produce (Pandoc/Typst installed). */
  exportAvailability() {
    return api.get<ExportAvailability>('/export/availability');
  },

  /** Render a content item to a document format and return the blob. */
  exportDocumentBlob(
    contentId: string,
    format: 'pdf' | 'html' | 'docx' | 'pptx',
    title?: string | undefined
  ) {
    return api.post<Blob>(
      `/content/${contentId}/export/document`,
      { format, title },
      { responseType: 'blob' }
    );
  },
};
