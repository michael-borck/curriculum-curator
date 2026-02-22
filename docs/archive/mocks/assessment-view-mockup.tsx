import React, { useState } from 'react';
import { Plus, Calendar, Clock, FileText, Target, Edit, Copy, Trash2, MoreVertical, AlertCircle, ChevronRight, BarChart, BookOpen, ClipboardCheck, Users, Link2 } from 'lucide-react';

const AssessmentManagementUI = () => {
  const [activeTab, setActiveTab] = useState('assessments');
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const assessments = [
    {
      id: 1,
      title: 'Pre-course Knowledge Check',
      type: 'formative',
      category: 'quiz',
      weight: 0,
      description: 'Baseline assessment to gauge student knowledge',
      specification: 'A 20-question multiple choice quiz covering prerequisites. Students have unlimited attempts. This ungraded assessment helps identify knowledge gaps.',
      releaseWeek: 1,
      dueWeek: 1,
      releaseDate: '2024-09-02',
      dueDate: '2024-09-08',
      duration: '30 minutes',
      questions: 20,
      status: 'complete',
      learningOutcomes: ['Identify prerequisite knowledge gaps', 'Self-assess readiness for course'],
      linkedMaterials: ['Week 1: Course Introduction Video', 'Week 1: Syllabus & Course Schedule']
    },
    {
      id: 2,
      title: 'Data Analysis Project',
      type: 'summative',
      category: 'project',
      weight: 25,
      description: 'Comprehensive data analysis using real-world dataset',
      specification: 'Students will obtain a dataset, clean and analyze it using techniques from weeks 1-4, and present findings in a 10-page report with visualizations.',
      releaseWeek: 4,
      dueWeek: 7,
      releaseDate: '2024-09-23',
      dueDate: '2024-10-14',
      duration: '3 weeks',
      status: 'in-progress',
      learningOutcomes: ['Apply data cleaning techniques', 'Create meaningful visualizations', 'Interpret statistical results'],
      linkedMaterials: ['Week 4: Data Analysis', 'Week 3: Data Cleaning']
    },
    {
      id: 3,
      title: 'Midterm Exam',
      type: 'summative',
      category: 'exam',
      weight: 30,
      description: 'Comprehensive exam covering weeks 1-6',
      specification: 'In-class closed-book exam. Mix of multiple choice (40%), short answer (30%), and problem-solving questions (30%). Covers all material from weeks 1-6.',
      releaseWeek: 7,
      dueWeek: 7,
      releaseDate: '2024-10-14',
      dueDate: '2024-10-14',
      duration: '2 hours',
      questions: 50,
      status: 'draft',
      learningOutcomes: ['Demonstrate understanding of core concepts', 'Apply statistical methods', 'Solve complex problems'],
      linkedMaterials: []
    },
    {
      id: 4,
      title: 'Weekly Discussion Posts',
      type: 'formative',
      category: 'discussion',
      weight: 10,
      description: 'Weekly participation in online discussions',
      specification: 'Students must post one original response (200+ words) and reply to two peers each week. Graded on insight, engagement, and critical thinking.',
      releaseWeek: 1,
      dueWeek: 12,
      releaseDate: '2024-09-02',
      dueDate: '2024-11-24',
      duration: 'Weekly',
      status: 'complete',
      learningOutcomes: ['Engage with course concepts', 'Develop critical thinking', 'Practice academic discourse'],
      linkedMaterials: []
    }
  ];

  const gradeDistribution = {
    formative: 10,
    summative: 90,
    total: 100
  };

  const getTypeColor = (type) => {
    return type === 'formative' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700';
  };

  const getCategoryIcon = (category) => {
    switch(category) {
      case 'quiz': return ClipboardCheck;
      case 'exam': return FileText;
      case 'project': return BookOpen;
      case 'discussion': return Users;
      default: return FileText;
    }
  };

  const getCategoryColor = (category) => {
    switch(category) {
      case 'quiz': return 'bg-green-100 text-green-600';
      case 'exam': return 'bg-red-100 text-red-600';
      case 'project': return 'bg-orange-100 text-orange-600';
      case 'discussion': return 'bg-cyan-100 text-cyan-600';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('materials')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'materials'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <BookOpen className="w-4 h-4 inline mr-2" />
              Weekly Materials
            </button>
            <button
              onClick={() => setActiveTab('assessments')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'assessments'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <ClipboardCheck className="w-4 h-4 inline mr-2" />
              Assessments
            </button>
            <button
              onClick={() => setActiveTab('grades')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'grades'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <BarChart className="w-4 h-4 inline mr-2" />
              Grade Distribution
            </button>
          </div>
        </div>
      </div>

      {/* Assessment View */}
      {activeTab === 'assessments' && (
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Course Assessments</h2>
              <div className="flex gap-6 mt-2 text-sm text-gray-500">
                <span>{assessments.length} total assessments</span>
                <span>{assessments.filter(a => a.type === 'formative').length} formative</span>
                <span>{assessments.filter(a => a.type === 'summative').length} summative</span>
                <span className="font-medium text-gray-700">Total weight: {gradeDistribution.total}%</span>
              </div>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Assessment
            </button>
          </div>

          {/* Grade Distribution Summary */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <BarChart className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Grade Distribution</h3>
                  <p className="text-sm text-gray-500">Formative: {gradeDistribution.formative}% | Summative: {gradeDistribution.summative}%</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">{gradeDistribution.total}%</p>
                  <p className="text-xs text-gray-500">Total Weight</p>
                </div>
                {gradeDistribution.total !== 100 && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <AlertCircle className="w-4 h-4 text-yellow-600" />
                    <span className="text-sm text-yellow-800">Weights don't sum to 100%</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Assessment List */}
          <div className="grid gap-4">
            {assessments.map((assessment) => {
              const CategoryIcon = getCategoryIcon(assessment.category);
              const categoryStyle = getCategoryColor(assessment.category);
              
              return (
                <div key={assessment.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex gap-3 flex-1">
                      <div className={`p-2 rounded-lg ${categoryStyle}`}>
                        <CategoryIcon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-medium text-gray-900">{assessment.title}</h3>
                            <div className="flex gap-3 mt-1 text-sm">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getTypeColor(assessment.type)}`}>
                                {assessment.type}
                              </span>
                              <span className="text-gray-500 capitalize">{assessment.category}</span>
                              {assessment.weight > 0 && (
                                <span className="font-medium text-gray-700">{assessment.weight}% of grade</span>
                              )}
                              {assessment.duration && (
                                <span className="text-gray-500 flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {assessment.duration}
                                </span>
                              )}
                              {assessment.questions && (
                                <span className="text-gray-500">{assessment.questions} questions</span>
                              )}
                            </div>
                          </div>
                        </div>

                        <p className="mt-2 text-sm text-gray-600">{assessment.description}</p>

                        {/* Timeline */}
                        <div className="mt-3 flex gap-4 text-sm">
                          <div className="flex items-center gap-2 text-gray-500">
                            <Calendar className="w-4 h-4" />
                            <span>Release: Week {assessment.releaseWeek} ({assessment.releaseDate})</span>
                          </div>
                          <div className="flex items-center gap-2 text-gray-500">
                            <Calendar className="w-4 h-4" />
                            <span>Due: Week {assessment.dueWeek} ({assessment.dueDate})</span>
                          </div>
                        </div>

                        {/* Learning Outcomes */}
                        {assessment.learningOutcomes.length > 0 && (
                          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-1 mb-1">
                              <Target className="w-3 h-3 text-gray-600" />
                              <span className="text-xs font-medium text-gray-700">Learning Outcomes</span>
                            </div>
                            <ul className="space-y-1">
                              {assessment.learningOutcomes.map((outcome, index) => (
                                <li key={index} className="flex items-start gap-1.5 text-xs text-gray-600">
                                  <span className="text-blue-500 mt-0.5">•</span>
                                  <span>{outcome}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Linked Materials */}
                        {assessment.linkedMaterials.length > 0 && (
                          <div className="mt-2 flex items-center gap-2">
                            <Link2 className="w-3 h-3 text-gray-500" />
                            <span className="text-xs text-gray-500">
                              Linked to: {assessment.linkedMaterials.join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                        <Copy className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg">
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Timeline View Option */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-blue-600" />
                <div>
                  <h4 className="font-medium text-gray-900">Assessment Timeline</h4>
                  <p className="text-sm text-gray-600">View all assessments on a calendar timeline</p>
                </div>
              </div>
              <button className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 flex items-center gap-2">
                View Timeline
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Assessment Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-3xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Add Assessment</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assessment Title</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Midterm Exam"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="formative">Formative</option>
                    <option value="summative">Summative</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="quiz">Quiz</option>
                    <option value="exam">Exam</option>
                    <option value="project">Project</option>
                    <option value="discussion">Discussion</option>
                    <option value="presentation">Presentation</option>
                    <option value="paper">Paper</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weight (% of final grade)</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0 for ungraded"
                  min="0"
                  max="100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Brief Description</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="One-line description for overview"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Specification</label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={4}
                  placeholder="Detailed requirements, rubric information, instructions..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Release</label>
                  <div className="flex gap-2">
                    <select className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option>Week 1</option>
                      <option>Week 2</option>
                      <option>Week 3</option>
                    </select>
                    <input
                      type="date"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Due</label>
                  <div className="flex gap-2">
                    <select className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option>Week 1</option>
                      <option>Week 2</option>
                      <option>Week 3</option>
                    </select>
                    <input
                      type="date"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Link to Course Materials</label>
                <p className="text-xs text-gray-500 mb-2">Connect this assessment to relevant weekly materials</p>
                <select multiple className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" size={4}>
                  <option>Week 1: Course Introduction Video</option>
                  <option>Week 1: Syllabus & Course Schedule</option>
                  <option>Week 2: Data Collection Methods</option>
                  <option>Week 3: Data Cleaning Techniques</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Assessment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssessmentManagementUI;