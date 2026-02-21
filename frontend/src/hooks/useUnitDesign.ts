/**
 * Hook to fetch the best available Learning Design for a unit.
 *
 * Returns the most recent approved design, falling back to draft if none approved.
 */

import { useState, useEffect } from 'react';
import api from '../services/api';

interface DesignContent {
  topic?: string;
  duration?: string;
  teachingPhilosophy?: string;
  objectives?: string[];
  learningOutcomes?: string[];
  prerequisites?: string[];
  pedagogyNotes?: string;
  differentiation?: string;
  assessment?: {
    type?: string;
    weight?: string;
    description?: string;
    criteria?: string[];
  };
  structure?: {
    preClass?: {
      activities?: string[];
      duration?: string;
      materials?: string[];
    };
    inClass?: {
      activities?: string[];
      duration?: string;
      materials?: string[];
    };
    postClass?: {
      activities?: string[];
      duration?: string;
      materials?: string[];
    };
  };
}

interface Design {
  id: string;
  unitId: string;
  version: string;
  status: string;
  content: DesignContent;
}

interface UseUnitDesignResult {
  designId: string | null;
  designContent: DesignContent | null;
  hasDesign: boolean;
  loading: boolean;
}

export function useUnitDesign(unitId: string | undefined): UseUnitDesignResult {
  const [designId, setDesignId] = useState<string | null>(null);
  const [designContent, setDesignContent] = useState<DesignContent | null>(
    null
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!unitId) {
      setDesignId(null);
      setDesignContent(null);
      return;
    }

    let cancelled = false;

    const fetchDesign = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/units/${unitId}/designs`);
        const designs: Design[] = response.data ?? [];

        if (cancelled || designs.length === 0) {
          if (!cancelled) {
            setDesignId(null);
            setDesignContent(null);
          }
          return;
        }

        // Pick approved first, then draft
        const approved = designs.find(d => d.status === 'approved');
        const draft = designs.find(d => d.status === 'draft');
        const best = approved ?? draft ?? designs[0];

        if (!cancelled) {
          setDesignId(best.id);
          setDesignContent(best.content);
        }
      } catch {
        if (!cancelled) {
          setDesignId(null);
          setDesignContent(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchDesign();

    return () => {
      cancelled = true;
    };
  }, [unitId]);

  return {
    designId,
    designContent,
    hasDesign: designId !== null,
    loading,
  };
}
