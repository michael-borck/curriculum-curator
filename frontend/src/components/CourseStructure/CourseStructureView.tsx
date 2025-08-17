import React, { useState } from 'react';
import {
  Calendar,
  Target,
  BookOpen,
  FileText,
  ChevronDown,
  ChevronRight,
  Clock,
  Users,
  Award,
  Activity,
  CheckSquare,
  Layers
} from 'lucide-react';

interface LearningOutcome {
  id: string;
  outcome_code: string;
  outcome_text: string;
  bloom_level: string;
  outcome_type: string;
}

interface WeeklyTopic {
  id: string;
  week_number: number;
  week_type: string;
  topic_title: string;
  topic_description?: string;
  learning_objectives?: string;
  pre_class_modules?: any[];
  in_class_activities?: any[];
  post_class_tasks?: any[];
  required_readings?: any[];
}

interface Assessment {
  id: string;
  assessment_name: string;
  assessment_type: string;
  assessment_mode: string;
  weight_percentage: number;
  due_week: number;
  description?: string;
}

interface CourseOutline {
  id: string;
  title: string;
  description?: string;
  duration_weeks: number;
  delivery_mode?: string;
  teaching_pattern?: string;
  is_complete: boolean;
  completion_percentage: number;
}

interface CourseStructureViewProps {
  outline: CourseOutline;
  learningOutcomes: LearningOutcome[];
  weeklyTopics: WeeklyTopic[];
  assessments: Assessment[];
  onEdit?: (section: string, id: string) => void;
}

const BLOOM_COLORS: Record<string, string> = {
  remember: 'bg-blue-100 text-blue-800',
  understand: 'bg-green-100 text-green-800',
  apply: 'bg-yellow-100 text-yellow-800',
  analyze: 'bg-orange-100 text-orange-800',
  evaluate: 'bg-purple-100 text-purple-800',
  create: 'bg-red-100 text-red-800'
};

const CourseStructureView: React.FC<CourseStructureViewProps> = ({
  outline,
  learningOutcomes,
  weeklyTopics,
  assessments
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['outline', 'outcomes', 'weekly', 'assessments'])
  );
  const [expandedWeeks, setExpandedWeeks] = useState<Set<number>>(new Set());

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const toggleWeek = (weekNumber: number) => {
    const newExpanded = new Set(expandedWeeks);
    if (newExpanded.has(weekNumber)) {
      newExpanded.delete(weekNumber);
    } else {
      newExpanded.add(weekNumber);
    }
    setExpandedWeeks(newExpanded);
  };

  const getAssessmentIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'exam':
        return <FileText className="w-4 h-4" />;
      case 'assignment':
        return <CheckSquare className="w-4 h-4" />;
      case 'quiz':
        return <Activity className="w-4 h-4" />;
      case 'project':
        return <Layers className="w-4 h-4" />;
      default:
        return <Award className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Course Outline Section */}
      <div className="bg-white rounded-lg shadow">
        <div
          className="px-6 py-4 border-b cursor-pointer hover:bg-gray-50"
          onClick={() => toggleSection('outline')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <BookOpen className="w-5 h-5 text-blue-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">Course Outline</h3>
            </div>
            {expandedSections.has('outline') ? (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-500" />
            )}
          </div>
        </div>
        
        {expandedSections.has('outline') && (
          <div className="px-6 py-4">
            <div className="space-y-3">
              <div>
                <h4 className="text-xl font-semibold text-gray-900">{outline.title}</h4>
                {outline.description && (
                  <p className="text-gray-600 mt-2">{outline.description}</p>
                )}
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div className="flex items-center">
                  <Clock className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600">
                    {outline.duration_weeks} weeks
                  </span>
                </div>
                {outline.delivery_mode && (
                  <div className="flex items-center">
                    <Users className="w-4 h-4 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-600">
                      {outline.delivery_mode}
                    </span>
                  </div>
                )}
                {outline.teaching_pattern && (
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-600">
                      {outline.teaching_pattern}
                    </span>
                  </div>
                )}
                <div className="flex items-center">
                  <Activity className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600">
                    {outline.completion_percentage}% complete
                  </span>
                </div>
              </div>

              {outline.completion_percentage < 100 && (
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${outline.completion_percentage}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Learning Outcomes Section */}
      <div className="bg-white rounded-lg shadow">
        <div
          className="px-6 py-4 border-b cursor-pointer hover:bg-gray-50"
          onClick={() => toggleSection('outcomes')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Target className="w-5 h-5 text-green-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">
                Learning Outcomes ({learningOutcomes.length})
              </h3>
            </div>
            {expandedSections.has('outcomes') ? (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-500" />
            )}
          </div>
        </div>

        {expandedSections.has('outcomes') && (
          <div className="px-6 py-4">
            <div className="space-y-3">
              {learningOutcomes.map((outcome) => (
                <div
                  key={outcome.id}
                  className="flex items-start p-3 border rounded-lg hover:bg-gray-50"
                >
                  <span className="font-semibold text-gray-700 mr-3">
                    {outcome.outcome_code}:
                  </span>
                  <div className="flex-1">
                    <p className="text-gray-700">{outcome.outcome_text}</p>
                    <div className="mt-2 flex items-center space-x-2">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          BLOOM_COLORS[outcome.bloom_level] || 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {outcome.bloom_level}
                      </span>
                      <span className="text-xs text-gray-500">
                        {outcome.outcome_type.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Weekly Topics Section */}
      <div className="bg-white rounded-lg shadow">
        <div
          className="px-6 py-4 border-b cursor-pointer hover:bg-gray-50"
          onClick={() => toggleSection('weekly')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Calendar className="w-5 h-5 text-purple-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">
                Weekly Schedule ({weeklyTopics.length} weeks)
              </h3>
            </div>
            {expandedSections.has('weekly') ? (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-500" />
            )}
          </div>
        </div>

        {expandedSections.has('weekly') && (
          <div className="px-6 py-4">
            <div className="space-y-2">
              {weeklyTopics.map((week) => (
                <div key={week.id} className="border rounded-lg">
                  <div
                    className="px-4 py-3 cursor-pointer hover:bg-gray-50"
                    onClick={() => toggleWeek(week.week_number)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="flex items-center justify-center w-8 h-8 bg-purple-100 text-purple-600 rounded-full font-semibold text-sm mr-3">
                          {week.week_number}
                        </span>
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {week.topic_title}
                          </h4>
                          {week.week_type !== 'regular' && (
                            <span className="text-xs text-gray-500">
                              {week.week_type}
                            </span>
                          )}
                        </div>
                      </div>
                      {expandedWeeks.has(week.week_number) ? (
                        <ChevronDown className="w-5 h-5 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-500" />
                      )}
                    </div>
                  </div>

                  {expandedWeeks.has(week.week_number) && (
                    <div className="px-4 py-3 border-t bg-gray-50">
                      {week.topic_description && (
                        <p className="text-gray-600 mb-3">{week.topic_description}</p>
                      )}
                      {week.learning_objectives && (
                        <div className="mb-3">
                          <h5 className="font-medium text-gray-700 mb-1">Objectives:</h5>
                          <p className="text-sm text-gray-600">{week.learning_objectives}</p>
                        </div>
                      )}
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                        {week.pre_class_modules && week.pre_class_modules.length > 0 && (
                          <div>
                            <h5 className="font-medium text-gray-700 mb-1">Pre-class:</h5>
                            <ul className="text-gray-600 space-y-1">
                              {week.pre_class_modules.map((item, idx) => (
                                <li key={idx} className="flex items-start">
                                  <span className="mr-1">•</span>
                                  <span>{item.title || item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {week.in_class_activities && week.in_class_activities.length > 0 && (
                          <div>
                            <h5 className="font-medium text-gray-700 mb-1">In-class:</h5>
                            <ul className="text-gray-600 space-y-1">
                              {week.in_class_activities.map((item, idx) => (
                                <li key={idx} className="flex items-start">
                                  <span className="mr-1">•</span>
                                  <span>{item.title || item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {week.post_class_tasks && week.post_class_tasks.length > 0 && (
                          <div>
                            <h5 className="font-medium text-gray-700 mb-1">Post-class:</h5>
                            <ul className="text-gray-600 space-y-1">
                              {week.post_class_tasks.map((item, idx) => (
                                <li key={idx} className="flex items-start">
                                  <span className="mr-1">•</span>
                                  <span>{item.title || item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Assessments Section */}
      <div className="bg-white rounded-lg shadow">
        <div
          className="px-6 py-4 border-b cursor-pointer hover:bg-gray-50"
          onClick={() => toggleSection('assessments')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Award className="w-5 h-5 text-orange-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">
                Assessment Plan ({assessments.length})
              </h3>
            </div>
            {expandedSections.has('assessments') ? (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-500" />
            )}
          </div>
        </div>

        {expandedSections.has('assessments') && (
          <div className="px-6 py-4">
            <div className="space-y-3">
              {assessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className="flex items-start p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="mr-3 mt-1">
                    {getAssessmentIcon(assessment.assessment_type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">
                          {assessment.assessment_name}
                        </h4>
                        {assessment.description && (
                          <p className="text-sm text-gray-600 mt-1">
                            {assessment.description}
                          </p>
                        )}
                      </div>
                      <div className="text-right ml-4">
                        <span className="text-lg font-semibold text-gray-900">
                          {assessment.weight_percentage}%
                        </span>
                        <p className="text-xs text-gray-500">Week {assessment.due_week}</p>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center space-x-2">
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">
                        {assessment.assessment_type}
                      </span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                        {assessment.assessment_mode}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Total Weight */}
              <div className="mt-4 pt-4 border-t">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-700">Total Weight:</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {assessments.reduce((sum, a) => sum + a.weight_percentage, 0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseStructureView;