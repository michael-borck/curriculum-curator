import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { UnitStructureDashboard } from '../../components/UnitStructure';
import api from '../../services/api';

interface Unit {
  id: string;
  title: string;
  code: string;
  description?: string;
  durationWeeks?: number;
  weeks?: number;
}

const UnitStructure: React.FC = () => {
  const { unitId } = useParams<{ unitId: string }>();
  const [unit, setUnit] = useState<Unit | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (unitId) {
      fetchUnitAndEnsureOutline();
    }
    // TECH-DEBT: Missing dependency 'fetchUnitAndEnsureOutline' - needs refactoring to useCallback
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unitId]);

  const fetchUnitAndEnsureOutline = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/units/${unitId}`);
      setUnit(response.data);

      // Check if unit has an outline, create one if it doesn't
      try {
        await api.get(`/api/units/${unitId}/structure`);
      } catch (error: any) {
        if (error.response?.status === 404) {
          // No outline exists, create an empty one
          await api.post(`/api/units/${unitId}/outline/create`, {
            title: `${response.data.code} - ${response.data.title}`,
            description: response.data.description || '',
            durationWeeks:
              response.data.durationWeeks || response.data.weeks || 12,
            deliveryMode: 'Blended',
            teachingPattern: 'Lecture + Tutorial',
          });
        }
      }
    } catch (error) {
      console.error('Error fetching unit:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600'></div>
      </div>
    );
  }

  if (!unit || !unitId) {
    return (
      <div className='text-center py-8'>
        <p className='text-gray-500'>Unit not found</p>
      </div>
    );
  }

  return (
    <UnitStructureDashboard
      unitId={unitId}
      unitName={`${unit.code} - ${unit.title}`}
      durationWeeks={unit.durationWeeks || unit.weeks || 12}
    />
  );
};

export default UnitStructure;
