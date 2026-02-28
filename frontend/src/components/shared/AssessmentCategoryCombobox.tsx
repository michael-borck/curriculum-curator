import { useState, useRef, useEffect, useMemo } from 'react';
import {
  Presentation,
  Users,
  FlaskConical,
  BookOpen,
  FileText,
  MessageSquare,
  Wrench,
  ClipboardCheck,
  ChevronDown,
  type LucideIcon,
} from 'lucide-react';
import {
  getCategoryMeta,
  ALL_KNOWN_CATEGORIES,
} from '../../constants/assessmentCategories';
import { getSectorProfile } from '../../constants/sectorProfiles';

const ICON_MAP: Record<string, LucideIcon> = {
  Presentation,
  Users,
  FlaskConical,
  BookOpen,
  FileText,
  MessageSquare,
  Wrench,
  ClipboardCheck,
};

function CategoryIcon({
  iconName,
  className,
}: {
  iconName: string;
  className?: string | undefined;
}) {
  const Icon = ICON_MAP[iconName] ?? FileText;
  return <Icon className={className} />;
}

interface AssessmentCategoryComboboxProps {
  value: string;
  onChange: (value: string) => void;
  sectorId?: string | undefined;
}

export function AssessmentCategoryCombobox({
  value,
  onChange,
  sectorId,
}: AssessmentCategoryComboboxProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [customMode, setCustomMode] = useState(false);
  const [customText, setCustomText] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const customInputRef = useRef<HTMLInputElement>(null);

  const profile = getSectorProfile(sectorId);
  const sectorDefaults = profile.defaultAssessmentCategories;

  const { sectorOptions, otherOptions } = useMemo(() => {
    const sectorSet = new Set(sectorDefaults);
    const others = ALL_KNOWN_CATEGORIES.filter(c => !sectorSet.has(c));
    return { sectorOptions: sectorDefaults, otherOptions: others };
  }, [sectorDefaults]);

  const filteredSector = useMemo(() => {
    if (!search) return sectorOptions;
    const q = search.toLowerCase();
    return sectorOptions.filter(c => {
      const meta = getCategoryMeta(c);
      return c.includes(q) || meta.label.toLowerCase().includes(q);
    });
  }, [sectorOptions, search]);

  const filteredOther = useMemo(() => {
    if (!search) return otherOptions;
    const q = search.toLowerCase();
    return otherOptions.filter(c => {
      const meta = getCategoryMeta(c);
      return c.includes(q) || meta.label.toLowerCase().includes(q);
    });
  }, [otherOptions, search]);

  const noResults = filteredSector.length === 0 && filteredOther.length === 0;

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setSearch('');
        setCustomMode(false);
      }
    };
    if (open) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  // Focus custom input when entering custom mode
  useEffect(() => {
    if (customMode) {
      window.setTimeout(() => customInputRef.current?.focus(), 0);
    }
  }, [customMode]);

  const select = (cat: string) => {
    onChange(cat);
    setOpen(false);
    setSearch('');
    setCustomMode(false);
  };

  const handleCustomSubmit = () => {
    const trimmed = customText.trim().toLowerCase().replace(/\s+/g, '_');
    if (trimmed) {
      select(trimmed);
      setCustomText('');
    }
  };

  const currentMeta = getCategoryMeta(value);

  const renderOption = (cat: string) => {
    const meta = getCategoryMeta(cat);
    const isSelected = cat === value;
    return (
      <button
        key={cat}
        type='button'
        onClick={() => select(cat)}
        className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-50 ${
          isSelected ? 'bg-purple-50 text-purple-700' : 'text-gray-700'
        }`}
      >
        <span
          className={`inline-flex items-center justify-center w-5 h-5 rounded ${meta.color}`}
        >
          <CategoryIcon iconName={meta.icon} className='w-3 h-3' />
        </span>
        <span>{meta.label}</span>
      </button>
    );
  };

  return (
    <div ref={containerRef} className='relative'>
      {/* Trigger button */}
      <button
        type='button'
        onClick={() => {
          setOpen(!open);
          if (!open) window.setTimeout(() => inputRef.current?.focus(), 0);
        }}
        className='mt-1 w-full flex items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
      >
        <span className='flex items-center gap-2'>
          <span
            className={`inline-flex items-center justify-center w-5 h-5 rounded ${currentMeta.color}`}
          >
            <CategoryIcon iconName={currentMeta.icon} className='w-3 h-3' />
          </span>
          <span className='text-sm text-gray-900'>{currentMeta.label}</span>
        </span>
        <ChevronDown className='w-4 h-4 text-gray-400' />
      </button>

      {/* Dropdown */}
      {open && (
        <div className='absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-72 overflow-hidden flex flex-col'>
          {/* Search */}
          <div className='p-2 border-b border-gray-100'>
            <input
              ref={inputRef}
              type='text'
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder='Search categories...'
              className='w-full px-2 py-1.5 text-sm border border-gray-200 rounded focus:border-purple-400 focus:ring-1 focus:ring-purple-400 outline-none'
            />
          </div>

          <div className='overflow-y-auto flex-1'>
            {/* Sector defaults */}
            {filteredSector.length > 0 && (
              <>
                <div className='px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider'>
                  {profile.label} defaults
                </div>
                {filteredSector.map(renderOption)}
              </>
            )}

            {/* Other known categories */}
            {filteredOther.length > 0 && (
              <>
                <div className='px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider border-t border-gray-100 mt-1'>
                  All categories
                </div>
                {filteredOther.map(renderOption)}
              </>
            )}

            {noResults && !customMode && (
              <div className='px-3 py-3 text-sm text-gray-500 text-center'>
                No matching categories
              </div>
            )}

            {/* Custom entry */}
            <div className='border-t border-gray-100 mt-1'>
              {!customMode ? (
                <button
                  type='button'
                  onClick={() => {
                    setCustomMode(true);
                    setCustomText(search);
                  }}
                  className='w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-purple-600'
                >
                  <FileText className='w-4 h-4' />
                  Custom...
                </button>
              ) : (
                <div className='p-2 flex gap-2'>
                  <input
                    ref={customInputRef}
                    type='text'
                    value={customText}
                    onChange={e => setCustomText(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleCustomSubmit();
                      }
                    }}
                    placeholder='Enter custom category name'
                    className='flex-1 px-2 py-1.5 text-sm border border-gray-200 rounded focus:border-purple-400 focus:ring-1 focus:ring-purple-400 outline-none'
                  />
                  <button
                    type='button'
                    onClick={handleCustomSubmit}
                    disabled={!customText.trim()}
                    className='px-3 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50'
                  >
                    Add
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
