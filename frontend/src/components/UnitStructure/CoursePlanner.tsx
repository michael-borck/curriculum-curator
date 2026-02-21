import { useState } from 'react';
import {
  Sparkles,
  Calendar,
  Globe,
  ArrowRight,
  Loader2,
  CheckCircle,
  X,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import type { Unit } from '../../types';

interface ScheduleWeek {
  weekNumber: number;
  title: string;
  topics: string[];
  learningObjectives?: string[];
}

interface CoursePlannerProps {
  unit: Unit;
  designId?: string | undefined;
  onApplySchedule: (weeks: ScheduleWeek[]) => void;
  onClose: () => void;
}

type Tab = 'RESEARCH' | 'SCHEDULE';

const CoursePlanner = ({
  unit,
  designId,
  onApplySchedule,
  onClose,
}: CoursePlannerProps) => {
  const [activeTab, setActiveTab] = useState<Tab>('SCHEDULE');

  // Research state
  const [searchQuery, setSearchQuery] = useState(
    `${unit.title} syllabus australia university`
  );
  const [searchResults, setSearchResults] = useState<
    Array<{ title: string; url: string }>
  >([]);
  const [isSearching, setIsSearching] = useState(false);

  // Schedule state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedSchedule, setGeneratedSchedule] = useState<ScheduleWeek[]>(
    []
  );
  const [expandedWeeks, setExpandedWeeks] = useState<Set<number>>(new Set());

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setSearchResults([]);

    try {
      // Use AI to search for similar courses
      const response = await api.post('/ai/chat', {
        messages: [
          {
            role: 'system',
            content:
              'You are a helpful assistant that finds university course syllabi and outlines.',
          },
          {
            role: 'user',
            content: `Find and list 5-8 real university courses similar to: "${searchQuery}". Focus on Australian universities but include international ones too. For each course, provide the course name and a real URL to its syllabus or outline. Format as JSON array: [{"title": "Course Name - University", "url": "https://..."}]`,
          },
        ],
        temperature: 0.3,
      });

      // Try to parse JSON from response
      let results: Array<{ title: string; url: string }> = [];
      const content = response.data?.content || '';

      try {
        // Extract JSON from response
        const jsonMatch = content.match(/\[[\s\S]*\]/);
        if (jsonMatch) {
          results = JSON.parse(jsonMatch[0]);
        }
      } catch {
        // If JSON parsing fails, show a generic message
        toast.error('Could not parse search results');
      }

      setSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleGenerateSchedule = async () => {
    setIsGenerating(true);

    try {
      const response = await api.post('/ai/generate-schedule', {
        unitTitle: unit.title,
        unitDescription: unit.description || '',
        learningOutcomes: [],
        durationWeeks: unit.durationWeeks || 12,
        teachingStyle: unit.pedagogyType,
        unitId: unit.id,
        designId,
      });

      const schedule = response.data?.weeks || [];
      setGeneratedSchedule(schedule);

      if (schedule.length > 0) {
        toast.success(`Generated ${schedule.length}-week schedule!`);
      }
    } catch (error) {
      console.error('Schedule generation error:', error);
      toast.error('Failed to generate schedule. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleWeekExpanded = (weekNumber: number) => {
    setExpandedWeeks(prev => {
      const next = new Set(prev);
      if (next.has(weekNumber)) {
        next.delete(weekNumber);
      } else {
        next.add(weekNumber);
      }
      return next;
    });
  };

  const handleApply = () => {
    onApplySchedule(generatedSchedule);
    toast.success('Schedule applied to unit!');
  };

  return (
    <div className='bg-purple-50 border border-purple-200 rounded-lg p-6 mb-6'>
      {/* Header */}
      <div className='flex items-center justify-between mb-4'>
        <div className='flex items-center gap-2'>
          <Sparkles className='w-5 h-5 text-purple-600' />
          <h3 className='text-lg font-semibold text-purple-900'>
            Course Planner & AI Assistant
          </h3>
        </div>
        <div className='flex items-center gap-3'>
          {/* Tab Switcher */}
          <div className='flex bg-white rounded-lg p-1 border border-gray-200'>
            <button
              onClick={() => setActiveTab('RESEARCH')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'RESEARCH'
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Globe className='w-4 h-4 inline mr-1' />
              Research
            </button>
            <button
              onClick={() => setActiveTab('SCHEDULE')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'SCHEDULE'
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Calendar className='w-4 h-4 inline mr-1' />
              Schedule
            </button>
          </div>
          <button
            onClick={onClose}
            className='p-1 text-gray-400 hover:text-gray-600'
          >
            <X className='w-5 h-5' />
          </button>
        </div>
      </div>

      {/* Research Tab */}
      {activeTab === 'RESEARCH' && (
        <div className='space-y-4'>
          <p className='text-sm text-gray-600'>
            Search for similar university courses to see how others structure
            their content.
          </p>

          <div className='flex gap-2'>
            <input
              type='text'
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
              placeholder='Search for existing courses...'
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
            />
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2'
            >
              {isSearching ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                <Globe className='w-4 h-4' />
              )}
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>

          {searchResults.length > 0 && (
            <div className='bg-white rounded-lg border border-gray-200 overflow-hidden'>
              <div className='px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase'>
                Similar Courses Found
              </div>
              <ul className='divide-y divide-gray-100'>
                {searchResults.map((result, i) => (
                  <li
                    key={i}
                    className='p-3 hover:bg-gray-50 flex items-center justify-between'
                  >
                    <a
                      href={result.url}
                      target='_blank'
                      rel='noreferrer'
                      className='text-sm text-purple-600 hover:underline font-medium truncate flex-1 mr-4 flex items-center gap-2'
                    >
                      {result.title}
                      <ExternalLink className='w-3 h-3 flex-shrink-0' />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {searchResults.length === 0 && !isSearching && (
            <p className='text-sm text-gray-500 italic'>
              Search for similar university units to see how they structure
              their content.
            </p>
          )}
        </div>
      )}

      {/* Schedule Tab */}
      {activeTab === 'SCHEDULE' && (
        <div className='space-y-4'>
          {generatedSchedule.length === 0 ? (
            <div className='text-center py-8'>
              <Calendar className='w-12 h-12 text-purple-300 mx-auto mb-4' />
              <p className='text-gray-600 mb-4'>
                Automatically generate a {unit.durationWeeks || 12}-week
                structure based on your unit title, description, and learning
                outcomes.
              </p>
              <button
                onClick={handleGenerateSchedule}
                disabled={isGenerating}
                className='px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 mx-auto'
              >
                {isGenerating ? (
                  <>
                    <Loader2 className='w-5 h-5 animate-spin' />
                    Crafting Schedule...
                  </>
                ) : (
                  <>
                    <Calendar className='w-5 h-5' />
                    Generate {unit.durationWeeks || 12}-Week Plan
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className='space-y-4'>
              {/* Schedule Preview */}
              <div className='max-h-80 overflow-y-auto bg-white rounded-lg border border-gray-200 p-4 space-y-3'>
                {generatedSchedule.map(week => (
                  <div
                    key={week.weekNumber}
                    className='border-b border-gray-100 pb-3 last:border-0'
                  >
                    <button
                      onClick={() => toggleWeekExpanded(week.weekNumber)}
                      className='w-full flex items-start text-left'
                    >
                      <div className='bg-purple-100 text-purple-800 text-xs font-bold px-2 py-1 rounded mr-3 mt-0.5 flex-shrink-0'>
                        W{week.weekNumber}
                      </div>
                      <div className='flex-1'>
                        <p className='font-semibold text-gray-800 text-sm'>
                          {week.title}
                        </p>
                        <p className='text-xs text-gray-500 mt-1'>
                          {week.topics.slice(0, 2).join(', ')}
                          {week.topics.length > 2 && '...'}
                        </p>
                      </div>
                      {expandedWeeks.has(week.weekNumber) ? (
                        <ChevronUp className='w-4 h-4 text-gray-400' />
                      ) : (
                        <ChevronDown className='w-4 h-4 text-gray-400' />
                      )}
                    </button>

                    {expandedWeeks.has(week.weekNumber) && (
                      <div className='mt-3 ml-10 pl-3 border-l-2 border-purple-200'>
                        <div className='mb-2'>
                          <p className='text-xs font-medium text-gray-500 uppercase mb-1'>
                            Topics
                          </p>
                          <ul className='space-y-1'>
                            {week.topics.map((topic, i) => (
                              <li
                                key={i}
                                className='text-sm text-gray-700 flex items-center gap-2'
                              >
                                <span className='w-1 h-1 bg-purple-400 rounded-full' />
                                {topic}
                              </li>
                            ))}
                          </ul>
                        </div>
                        {week.learningObjectives &&
                          week.learningObjectives.length > 0 && (
                            <div>
                              <p className='text-xs font-medium text-gray-500 uppercase mb-1'>
                                Learning Objectives
                              </p>
                              <ul className='space-y-1'>
                                {week.learningObjectives.map((obj, i) => (
                                  <li
                                    key={i}
                                    className='text-sm text-gray-600 flex items-start gap-2'
                                  >
                                    <CheckCircle className='w-3 h-3 text-green-500 mt-0.5 flex-shrink-0' />
                                    {obj}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className='flex justify-end gap-3'>
                <button
                  onClick={() => setGeneratedSchedule([])}
                  className='px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50'
                >
                  Discard
                </button>
                <button
                  onClick={handleGenerateSchedule}
                  disabled={isGenerating}
                  className='px-4 py-2 text-purple-600 bg-white border border-purple-300 rounded-lg hover:bg-purple-50 disabled:opacity-50'
                >
                  Regenerate
                </button>
                <button
                  onClick={handleApply}
                  className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2'
                >
                  <ArrowRight className='w-4 h-4' />
                  Apply to Unit
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CoursePlanner;
