import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, X, ChevronDown } from 'lucide-react';
import { useWorkingContextStore } from '../../stores/workingContextStore';
import { useUnitsStore } from '../../stores/unitsStore';

const WorkingContextIndicator = () => {
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const {
    activeUnitId,
    activeUnitTitle,
    activeUnitCode,
    activeWeek,
    setActiveUnit,
    clearContext,
  } = useWorkingContextStore();
  const units = useUnitsStore(s => s.units);

  const hasContext = activeUnitId !== null;

  const handleUnitSelect = (unit: {
    id: string;
    title: string;
    code: string;
  }) => {
    setActiveUnit(unit);
    setDropdownOpen(false);
  };

  return (
    <div className='relative'>
      {hasContext ? (
        <div className='flex items-center gap-1'>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className='flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition text-sm font-medium'
          >
            <BookOpen className='w-4 h-4' />
            <span className='hidden sm:inline'>
              {activeUnitCode} &middot; {activeUnitTitle}
              {activeWeek != null ? ` \u00B7 Week ${activeWeek}` : ''}
            </span>
            <span className='sm:hidden'>{activeUnitCode}</span>
            <ChevronDown className='w-3 h-3' />
          </button>
          <button
            onClick={() => clearContext()}
            className='p-1 text-indigo-400 hover:text-indigo-600 hover:bg-indigo-100 rounded transition'
            title='Clear working context'
          >
            <X className='w-3.5 h-3.5' />
          </button>
        </div>
      ) : (
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className='flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-500 rounded-lg hover:bg-gray-200 transition text-sm'
        >
          <BookOpen className='w-4 h-4' />
          <span className='hidden sm:inline'>No unit selected</span>
          <ChevronDown className='w-3 h-3' />
        </button>
      )}

      {dropdownOpen && (
        <>
          <div
            className='fixed inset-0 z-10'
            onClick={() => setDropdownOpen(false)}
          />
          <div className='absolute left-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-20'>
            <div className='px-3 py-2 border-b border-gray-100'>
              <p className='text-xs font-semibold text-gray-500 uppercase'>
                Working Context
              </p>
              <p className='text-xs text-gray-400 mt-0.5'>
                Select a unit to set context for AI and tools
              </p>
            </div>
            <div className='max-h-64 overflow-y-auto'>
              {units.length === 0 ? (
                <div className='px-3 py-3 text-sm text-gray-400'>
                  No units available
                </div>
              ) : (
                units.map(unit => (
                  <button
                    key={unit.id}
                    onClick={() =>
                      handleUnitSelect({
                        id: unit.id,
                        title: unit.title,
                        code: unit.code,
                      })
                    }
                    className={`w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center gap-3 ${
                      activeUnitId === unit.id ? 'bg-indigo-50' : ''
                    }`}
                  >
                    <div
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        activeUnitId === unit.id
                          ? 'bg-indigo-600'
                          : 'bg-gray-300'
                      }`}
                    />
                    <div className='min-w-0'>
                      <p
                        className={`text-sm font-medium truncate ${
                          activeUnitId === unit.id
                            ? 'text-indigo-700'
                            : 'text-gray-900'
                        }`}
                      >
                        {unit.code}
                      </p>
                      <p className='text-xs text-gray-500 truncate'>
                        {unit.title}
                      </p>
                    </div>
                  </button>
                ))
              )}
            </div>
            {hasContext && (
              <div className='border-t border-gray-100 pt-1 mt-1'>
                <button
                  onClick={() => {
                    if (activeUnitId) navigate(`/units/${activeUnitId}`);
                    setDropdownOpen(false);
                  }}
                  className='w-full px-3 py-2 text-left text-sm text-indigo-600 hover:bg-indigo-50'
                >
                  Go to {activeUnitCode}
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default WorkingContextIndicator;
