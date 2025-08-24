import React, { useState } from 'react';
import { Plus, ChevronDown, ChevronRight, FileText, Video, BookOpen, ClipboardList, Link, StickyNote, Trash2, Edit, Copy, Search, Calendar, MoreVertical, Eye, Download, Upload, Target, Check, X, Package, FolderOpen, Layout, Clock, Tag, AlertCircle, CheckCircle2, ArrowUpDown, Library, Sparkles, Save, FolderPlus } from 'lucide-react';

const CourseManagementUI = () => {
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [expandedWeeks, setExpandedWeeks] = useState(new Set([1]));
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedMaterialType, setSelectedMaterialType] = useState('');
  const [showCourseOutcomes, setShowCourseOutcomes] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [showMaterialMenu, setShowMaterialMenu] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [selectedTags, setSelectedTags] = useState([]);
  const [showExportModal, setShowExportModal] = useState(false);

  const materialTypes = [
    { type: 'lecture', icon: Video, color: 'bg-blue-100 text-blue-600', label: 'Lecture' },
    { type: 'handout', icon: FileText, color: 'bg-green-100 text-green-600', label: 'Handout' },
    { type: 'quiz', icon: ClipboardList, color: 'bg-purple-100 text-purple-600', label: 'Quiz' },
    { type: 'case-study', icon: BookOpen, color: 'bg-orange-100 text-orange-600', label: 'Case Study' },
    { type: 'resource', icon: Link, color: 'bg-cyan-100 text-cyan-600', label: 'Resource' },
    { type: 'notes', icon: StickyNote, color: 'bg-yellow-100 text-yellow-600', label: 'Notes' }
  ];

  const availableTags = ['Introduction', 'Advanced', 'Required', 'Optional', 'Interactive', 'Assessment', 'Reading', 'Practical'];

  const [courseData, setCourseData] = useState({
    courseTitle: 'Introduction to Data Science',
    courseStatus: 'in-progress', // in-progress, ready, needs-review
    lastModified: '2024-10-28',
    totalWeeks: 12,
    completionPercentage: 25,
    courseLearningOutcomes: [
      'Understand fundamental concepts of data science and its applications',
      'Apply statistical methods to analyze and interpret data',
      'Build and evaluate machine learning models',
      'Communicate data insights effectively to stakeholders'
    ],
    weeks: Array.from({ length: 12 }, (_, i) => ({
      weekNumber: i + 1,
      title: `Week ${i + 1}: ${['Introduction & Overview', 'Data Collection', 'Data Cleaning', 'Exploratory Analysis', 'Statistical Methods', 'Machine Learning Basics', 'Supervised Learning', 'Unsupervised Learning', 'Deep Learning', 'Model Evaluation', 'Real-world Applications', 'Final Projects'][i]}`,
      estimatedHours: i === 0 ? 4.5 : 0,
      completionStatus: i === 0 ? 'complete' : i === 1 ? 'in-progress' : 'empty',
      weeklyLearningOutcomes: i === 0 ? [
        'Define data science and explain its role in modern decision-making',
        'Set up development environment with required tools',
        'Navigate course structure and expectations'
      ] : [],
      materials: i === 0 ? [
        { 
          id: 1, 
          type: 'lecture', 
          title: 'Course Introduction Video', 
          duration: '45 min',
          estimatedTime: 45,
          status: 'complete',
          tags: ['Introduction', 'Required'],
          learningOutcomes: [
            'Explain the interdisciplinary nature of data science',
            'Identify real-world applications of data science'
          ],
          lastModified: '2024-10-25'
        },
        { 
          id: 2, 
          type: 'handout', 
          title: 'Syllabus & Course Schedule', 
          pages: 8,
          estimatedTime: 20,
          status: 'complete',
          tags: ['Required', 'Reading'],
          learningOutcomes: [
            'Understand course requirements and grading criteria',
            'Plan study schedule for the semester'
          ],
          lastModified: '2024-10-20'
        },
        { 
          id: 3, 
          type: 'quiz', 
          title: 'Pre-course Assessment', 
          questions: 20,
          estimatedTime: 30,
          status: 'in-progress',
          tags: ['Assessment', 'Optional'],
          learningOutcomes: [
            'Self-assess current knowledge level',
            'Identify areas for focused learning'
          ],
          lastModified: '2024-10-28'
        },
        { 
          id: 4, 
          type: 'resource', 
          title: 'Required Textbooks & Software',
          estimatedTime: 15,
          status: 'complete',
          tags: ['Required', 'Reading'],
          learningOutcomes: [],
          lastModified: '2024-10-15'
        }
      ] : i === 1 ? [
        { 
          id: 5, 
          type: 'lecture', 
          title: 'Data Collection Methods', 
          duration: '60 min',
          estimatedTime: 60,
          status: 'in-progress',
          tags: ['Required'],
          learningOutcomes: [],
          lastModified: '2024-10-28'
        }
      ] : []
    }))
  });

  const toggleWeekExpansion = (weekNum) => {
    const newExpanded = new Set(expandedWeeks);
    if (newExpanded.has(weekNum)) {
      newExpanded.delete(weekNum);
    } else {
      newExpanded.add(weekNum);
    }
    setExpandedWeeks(newExpanded);
  };

  const getMaterialIcon = (type) => {
    const material = materialTypes.find(m => m.type === type);
    return material ? material.icon : FileText;
  };

  const getMaterialStyle = (type) => {
    const material = materialTypes.find(m => m.type === type);
    return material ? material.color : 'bg-gray-100 text-gray-600';
  };

  const handleAddMaterial = () => {
    if (selectedMaterialType) {
      const newMaterial = {
        id: Date.now(),
        type: selectedMaterialType,
        title: `New ${materialTypes.find(m => m.type === selectedMaterialType).label}`,
        status: 'in-progress',
        tags: [],
        learningOutcomes: [],
        lastModified: new Date().toISOString().split('T')[0]
      };
      
      const updatedWeeks = [...courseData.weeks];
      updatedWeeks[selectedWeek - 1].materials.push(newMaterial);
      setCourseData({ ...courseData, weeks: updatedWeeks });
      setShowAddModal(false);
      setSelectedMaterialType('');
    }
  };

  const getWeekStatusIcon = (status) => {
    switch(status) {
      case 'complete':
        return <CheckCircle2 className="w-4 h-4 text-green-600" />;
      case 'in-progress':
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getWeekStatusColor = (status) => {
    switch(status) {
      case 'complete':
        return 'bg-green-50 border-green-200';
      case 'in-progress':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">{courseData.courseTitle}</h1>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  courseData.courseStatus === 'ready' 
                    ? 'bg-green-100 text-green-700' 
                    : courseData.courseStatus === 'needs-review'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {courseData.courseStatus === 'ready' ? 'Ready for Export' : 
                   courseData.courseStatus === 'needs-review' ? 'Needs Review' : 'In Progress'}
                </span>
              </div>
              <div className="flex items-center gap-4 mt-2">
                <p className="text-sm text-gray-500">12-Week Course • Last modified {courseData.lastModified}</p>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{width: `${courseData.completionPercentage}%`}}></div>
                  </div>
                  <span className="text-sm text-gray-600">{courseData.completionPercentage}% complete</span>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button 
                onClick={() => setShowImportModal(true)}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Import
              </button>
              <button 
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <Layout className="w-4 h-4" />
                Templates
              </button>
              <button 
                onClick={() => setShowExportModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Package className="w-4 h-4" />
                Export Course
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-88px)]">
        {/* Sidebar - Week Navigation */}
        <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              <button className="px-3 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 flex items-center gap-2 text-sm">
                <Sparkles className="w-4 h-4" />
                AI Assist
              </button>
              <button className="px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 flex items-center gap-2 text-sm">
                <Library className="w-4 h-4" />
                My Library
              </button>
            </div>

            {/* Course Learning Outcomes */}
            <button
              onClick={() => setShowCourseOutcomes(!showCourseOutcomes)}
              className="w-full mb-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg hover:from-blue-100 hover:to-indigo-100 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-sm text-gray-900">Course Learning Outcomes</span>
                </div>
                {showCourseOutcomes ? 
                  <ChevronDown className="w-4 h-4 text-gray-500" /> : 
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                }
              </div>
            </button>

            {showCourseOutcomes && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
                <ul className="space-y-2">
                  {courseData.courseLearningOutcomes.map((outcome, index) => (
                    <li key={index} className="flex items-start gap-2 text-xs text-gray-700">
                      <Check className="w-3 h-3 text-blue-600 mt-0.5 flex-shrink-0" />
                      <span>{outcome}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="relative mb-4">
              <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search materials..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Filter Tags */}
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-600 mb-2">Filter by tags</p>
              <div className="flex flex-wrap gap-1">
                {availableTags.slice(0, 4).map(tag => (
                  <button
                    key={tag}
                    onClick={() => setSelectedTags(prev => 
                      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
                    )}
                    className={`px-2 py-1 text-xs rounded-full transition-colors ${
                      selectedTags.includes(tag)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1">
              {courseData.weeks.map((week) => (
                <div key={week.weekNumber} className={`border border-gray-200 rounded-lg overflow-hidden ${getWeekStatusColor(week.completionStatus)}`}>
                  <button
                    onClick={() => {
                      setSelectedWeek(week.weekNumber);
                      toggleWeekExpansion(week.weekNumber);
                    }}
                    className={`w-full px-3 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors ${
                      selectedWeek === week.weekNumber ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {expandedWeeks.has(week.weekNumber) ? 
                        <ChevronDown className="w-4 h-4 text-gray-500" /> : 
                        <ChevronRight className="w-4 h-4 text-gray-500" />
                      }
                      <div className="text-left">
                        <div className="font-medium text-sm flex items-center gap-2">
                          Week {week.weekNumber}
                          {getWeekStatusIcon(week.completionStatus)}
                        </div>
                        <div className="text-xs text-gray-500 truncate max-w-[180px]">
                          {week.title.split(': ')[1]}
                        </div>
                        {week.estimatedHours > 0 && (
                          <div className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                            <Clock className="w-3 h-3" />
                            {week.estimatedHours} hours
                          </div>
                        )}
                      </div>
                    </div>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      {week.materials.length}
                    </span>
                  </button>
                  
                  {expandedWeeks.has(week.weekNumber) && week.materials.length > 0 && (
                    <div className="px-3 py-2 bg-gray-50 border-t border-gray-200">
                      {week.materials.map((material) => {
                        const Icon = getMaterialIcon(material.type);
                        return (
                          <div key={material.id} className="flex items-center gap-2 py-1.5 text-xs text-gray-600 hover:text-gray-900 cursor-pointer">
                            <Icon className="w-3 h-3" />
                            <span className="truncate flex-1">{material.title}</span>
                            {material.status === 'in-progress' && (
                              <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6">
            {/* Week Header */}
            <div className="mb-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-gray-900">
                    {courseData.weeks[selectedWeek - 1].title}
                  </h2>
                  <div className="flex gap-4 mt-2 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      Sept {2 + (selectedWeek - 1) * 7} - {8 + (selectedWeek - 1) * 7}, 2024
                    </span>
                    <span>{courseData.weeks[selectedWeek - 1].materials.length} materials</span>
                    {courseData.weeks[selectedWeek - 1].estimatedHours > 0 && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {courseData.weeks[selectedWeek - 1].estimatedHours} hours total
                      </span>
                    )}
                  </div>
                  
                  {/* Weekly Learning Outcomes */}
                  {courseData.weeks[selectedWeek - 1].weeklyLearningOutcomes.length > 0 && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-blue-600" />
                        <span className="font-medium text-sm text-gray-900">Weekly Learning Outcomes</span>
                      </div>
                      <ul className="space-y-1">
                        {courseData.weeks[selectedWeek - 1].weeklyLearningOutcomes.map((outcome, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                            <Check className="w-3 h-3 text-blue-600 mt-0.5 flex-shrink-0" />
                            <span>{outcome}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <button className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
                    <ArrowUpDown className="w-4 h-4" />
                    Reorder
                  </button>
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Material
                  </button>
                </div>
              </div>
            </div>

            {/* Materials Grid */}
            <div className="grid gap-4">
              {courseData.weeks[selectedWeek - 1].materials.length > 0 ? (
                courseData.weeks[selectedWeek - 1].materials.map((material) => {
                  const Icon = getMaterialIcon(material.type);
                  const styleClass = getMaterialStyle(material.type);
                  
                  return (
                    <div key={material.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex gap-3 flex-1">
                          <div className={`p-2 rounded-lg ${styleClass}`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900">{material.title}</h3>
                            <div className="flex gap-3 mt-1 text-sm text-gray-500">
                              <span className="capitalize">{material.type.replace('-', ' ')}</span>
                              {material.duration && <span>• {material.duration}</span>}
                              {material.pages && <span>• {material.pages} pages</span>}
                              {material.questions && <span>• {material.questions} questions</span>}
                              {material.estimatedTime && (
                                <span className="flex items-center gap-1">
                                  • <Clock className="w-3 h-3" />
                                  {material.estimatedTime} min
                                </span>
                              )}
                              <span className={`px-2 py-0.5 rounded-full text-xs ${
                                material.status === 'complete' 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-yellow-100 text-yellow-700'
                              }`}>
                                {material.status === 'complete' ? 'Complete' : 'In Progress'}
                              </span>
                            </div>

                            {/* Tags */}
                            {material.tags && material.tags.length > 0 && (
                              <div className="flex gap-1 mt-2">
                                {material.tags.map((tag, index) => (
                                  <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                            
                            {/* Material Learning Outcomes */}
                            {material.learningOutcomes && material.learningOutcomes.length > 0 && (
                              <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center gap-1 mb-1">
                                  <Target className="w-3 h-3 text-gray-600" />
                                  <span className="text-xs font-medium text-gray-700">Learning Outcomes</span>
                                </div>
                                <ul className="space-y-1">
                                  {material.learningOutcomes.map((outcome, index) => (
                                    <li key={index} className="flex items-start gap-1.5 text-xs text-gray-600">
                                      <span className="text-blue-500 mt-0.5">•</span>
                                      <span>{outcome}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                              <span>Last modified: {material.lastModified}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2 relative">
                          <button 
                            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                            onClick={() => setEditingMaterial(material)}
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                            <Copy className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                            <FolderPlus className="w-4 h-4" />
                          </button>
                          <button 
                            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                            onClick={() => setShowMaterialMenu(showMaterialMenu === material.id ? null : material.id)}
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>
                          
                          {/* Material Actions Dropdown */}
                          {showMaterialMenu === material.id && (
                            <div className="absolute right-0 top-10 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                              <button className="w-full px-4 py-2 text-sm text-left hover:bg-gray-50 flex items-center gap-2">
                                <Eye className="w-4 h-4" />
                                Preview
                              </button>
                              <button className="w-full px-4 py-2 text-sm text-left hover:bg-gray-50 flex items-center gap-2">
                                <Download className="w-4 h-4" />
                                Download
                              </button>
                              <button className="w-full px-4 py-2 text-sm text-left hover:bg-gray-50 flex items-center gap-2">
                                <Save className="w-4 h-4" />
                                Save to Library
                              </button>
                              <hr className="my-1" />
                              <button className="w-full px-4 py-2 text-sm text-left hover:bg-red-50 text-red-600 flex items-center gap-2">
                                <Trash2 className="w-4 h-4" />
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                  <div className="max-w-sm mx-auto">
                    <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-gray-900 font-medium mb-2">No materials yet</h3>
                    <p className="text-gray-500 text-sm mb-4">
                      Start building your week by adding lectures, handouts, quizzes, and other course materials.
                    </p>
                    <div className="flex gap-3 justify-center">
                      <button
                        onClick={() => setShowAddModal(true)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 inline-flex items-center gap-2"
                      >
                        <Plus className="w-4 h-4" />
                        Create New
                      </button>
                      <button
                        onClick={() => setShowImportModal(true)}
                        className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 inline-flex items-center gap-2"
                      >
                        <Upload className="w-4 h-4" />
                        Import Existing
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add Material Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl">
            <h3 className="text-lg font-semibold mb-4">Add Course Material</h3>
            <div className="mb-4">
              <div className="flex gap-2 border-b border-gray-200">
                <button className="px-4 py-2 border-b-2 border-blue-600 text-blue-600 font-medium">
                  Create New
                </button>
                <button className="px-4 py-2 text-gray-500 hover:text-gray-700">
                  From Template
                </button>
                <button className="px-4 py-2 text-gray-500 hover:text-gray-700">
                  From Library
                </button>
                <button className="px-4 py-2 text-gray-500 hover:text-gray-700 flex items-center gap-1">
                  <Sparkles className="w-4 h-4" />
                  AI Generate
                </button>
              </div>
            </div>
            
            <p className="text-sm text-gray-500 mb-4">Choose the type of material to add to Week {selectedWeek}</p>
            
            <div className="grid grid-cols-3 gap-3 mb-6">
              {materialTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.type}
                    onClick={() => setSelectedMaterialType(type.type)}
                    className={`p-4 border-2 rounded-lg hover:border-blue-500 transition-colors ${
                      selectedMaterialType === type.type ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                    }`}
                  >
                    <Icon className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                    <span className="text-sm font-medium">{type.label}</span>
                  </button>
                );
              })}
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setSelectedMaterialType('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddMaterial}
                disabled={!selectedMaterialType}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Import Materials</h3>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-sm text-gray-600 mb-2">Drag and drop files here, or click to browse</p>
              <p className="text-xs text-gray-500">Supports: PDF, DOCX, PPT, MP4, ZIP</p>
              <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Select Files
              </button>
            </div>
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Or import from:</p>
              <div className="grid grid-cols-2 gap-2">
                <button className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                  Google Drive
                </button>
                <button className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                  OneDrive
                </button>
                <button className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                  Dropbox
                </button>
                <button className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                  Previous Course
                </button>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowImportModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Export Course Package</h3>
            
            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-3">Select export format:</p>
              <div className="space-y-2">
                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input type="radio" name="export" className="mr-3" defaultChecked />
                  <div>
                    <div className="font-medium text-sm">Canvas</div>
                    <div className="text-xs text-gray-500">Export as Canvas-compatible package</div>
                  </div>
                </label>
                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input type="radio" name="export" className="mr-3" />
                  <div>
                    <div className="font-medium text-sm">Blackboard</div>
                    <div className="text-xs text-gray-500">Export for Blackboard Learn</div>
                  </div>
                </label>
                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input type="radio" name="export" className="mr-3" />
                  <div>
                    <div className="font-medium text-sm">Moodle</div>
                    <div className="text-xs text-gray-500">Export as Moodle backup file</div>
                  </div>
                </label>
                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input type="radio" name="export" className="mr-3" />
                  <div>
                    <div className="font-medium text-sm">SCORM Package</div>
                    <div className="text-xs text-gray-500">Universal SCORM 1.2/2004 format</div>
                  </div>
                </label>
                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input type="radio" name="export" className="mr-3" />
                  <div>
                    <div className="font-medium text-sm">ZIP Archive</div>
                    <div className="text-xs text-gray-500">All materials in organized folders</div>
                  </div>
                </label>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
                <div className="text-xs text-yellow-800">
                  <p className="font-medium mb-1">3 items need attention:</p>
                  <ul className="space-y-0.5">
                    <li>• Week 2 has no materials</li>
                    <li>• Quiz in Week 1 is incomplete</li>
                    <li>• 5 materials missing learning outcomes</li>
                  </ul>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowExportModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Export
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Material Modal */}
      {editingMaterial && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Edit Material</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  defaultValue={editingMaterial.title}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estimated Time (minutes)</label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    defaultValue={editingMaterial.estimatedTime}
                    placeholder="30"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="in-progress">In Progress</option>
                    <option value="complete">Complete</option>
                    <option value="needs-review">Needs Review</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {availableTags.map(tag => (
                    <button
                      key={tag}
                      className={`px-3 py-1 text-sm rounded-full transition-colors ${
                        (editingMaterial.tags || []).includes(tag)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Learning Outcomes</label>
                <p className="text-xs text-gray-500 mb-2">Define what students will be able to do after completing this material</p>
                <div className="space-y-2">
                  {(editingMaterial.learningOutcomes || []).map((outcome, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        defaultValue={outcome}
                      />
                      <button className="p-2 text-red-500 hover:bg-red-50 rounded-lg">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button className="w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 text-gray-500 hover:text-blue-600 flex items-center justify-center gap-2">
                    <Plus className="w-4 h-4" />
                    Add Learning Outcome
                  </button>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setEditingMaterial(null)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => setEditingMaterial(null)}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseManagementUI;