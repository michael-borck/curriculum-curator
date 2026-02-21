/**
 * Material version history API client.
 *
 * Follows the same pattern as contentApi.ts versioning endpoints.
 */

import api from './api';

export interface MaterialVersion {
  commit: string;
  date: string;
  message: string;
  authorEmail: string | null;
}

export interface MaterialHistory {
  materialId: string;
  versions: MaterialVersion[];
}

export interface MaterialDiff {
  materialId: string;
  oldCommit: string;
  newCommit: string;
  diff: string;
}

export interface MaterialAtVersion {
  commit: string;
  body: string;
}

export const materialVersionApi = {
  /** Get commit history for a material's description. */
  history(materialId: string, limit = 20) {
    return api.get<MaterialHistory>(`/materials/${materialId}/history`, {
      params: { limit },
    });
  },

  /** Get material description body at a specific commit. */
  versionBody(materialId: string, commit: string) {
    return api.get<MaterialAtVersion>(
      `/materials/${materialId}/version/${commit}`
    );
  },

  /** Get diff between two commits for a material. */
  diff(materialId: string, oldCommit: string, newCommit = 'HEAD') {
    return api.get<MaterialDiff>(`/materials/${materialId}/diff`, {
      params: { old_commit: oldCommit, new_commit: newCommit },
    });
  },

  /** Revert to a previous commit (creates a new commit). */
  revert(materialId: string, commit: string) {
    return api.post(`/materials/${materialId}/revert`, { commit });
  },
};
