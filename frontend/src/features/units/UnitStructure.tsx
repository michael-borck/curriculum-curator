import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { UnitStructureDashboard } from '../../components/UnitStructure';
import api from '../../services/api';

interface Unit {
  id: string;
  title: string;
  code: string;
  description?: string;
}

const UnitStructure: React.FC = () => {
  const { unitId } = useParams<{ unitId: string }>();
  const [unit, setUnit] = useState<Unit | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (unitId) {
      fetchUnit();
    }
  }, [unitId]);

  const fetchUnit = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/units/${unitId}`);
      setUnit(response.data);
    } catch (error) {
      console.error('Error fetching unit:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!unit || !unitId) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Unit not found</p>
      </div>
    );
  }

  return (
    <UnitStructureDashboard 
      unitId={unitId} 
      unitName={`${unit.code} - ${unit.title}`}
    />
  );
};

export default UnitStructure;