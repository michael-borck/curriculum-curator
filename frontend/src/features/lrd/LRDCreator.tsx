import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Target,
  Clock,
  Users,
  FileText,
  CheckCircle,
  AlertCircle,
  Save,
  Send,
  Loader2,
  Plus,
  X,
} from 'lucide-react';
import api from '../../services/api';

interface Unit {
  id: string;
  title: string;
  code: string;
  teachingPhilosophy: string;
}

interface LRDErrors {
  topic?: string;
  duration?: string;
  objectives?: string;
  learningOutcomes?: string;
  submit?: string;
}

interface LRDContent {
  topic: string;
  duration: string;
  objectives: string[];
  learningOutcomes: string[];
  prerequisites: string[];
  structure: {
    preClass: {
      activities: string[];
      duration: string;
      materials: string[];
    };
    inClass: {
      activities: string[];
      duration: string;
      materials: string[];
    };
    postClass: {
      activities: string[];
      duration: string;
      materials: string[];
    };
  };
  assessment: {
    type: string;
    weight: string;
    description: string;
    criteria: string[];
  };
  resources: {
    required: string[];
    recommended: string[];
    supplementary: string[];
  };
  pedagogyNotes: string;
  differentiation: string;
  technologyRequirements: string[];
  teachingPhilosophy?: string;
}

interface LRDData {
  unitId: string | undefined;
  version: string;
  status: string;
  content: LRDContent;
  [key: string]: any;
}

const LRDCreator = () => {
  const { unitId } = useParams<{ unitId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [errors, setErrors] = useState<LRDErrors>({});

  // LRD Form State
  const [lrdData, setLrdData] = useState<LRDData>({
    unitId: unitId,
    version: '1.0',
    status: 'DRAFT',
    content: {
      topic: '',
      duration: '',
      objectives: [''],
      learningOutcomes: [''],
      prerequisites: [''],
      structure: {
        preClass: {
          activities: [''],
          duration: '',
          materials: [''],
        },
        inClass: {
          activities: [''],
          duration: '',
          materials: [''],
        },
        postClass: {
          activities: [''],
          duration: '',
          materials: [''],
        },
      },
      assessment: {
        type: '',
        weight: '',
        description: '',
        criteria: [''],
      },
      resources: {
        required: [''],
        recommended: [''],
        supplementary: [''],
      },
      pedagogyNotes: '',
      differentiation: '',
      technologyRequirements: [''],
    },
  });

  // Fetch unit details
  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/units/${unitId}`);
        setUnit(response.data);

        // Set teaching philosophy from course
        setLrdData(prev => ({
          ...prev,
          content: {
            ...prev.content,
            teachingPhilosophy: response.data.teachingPhilosophy,
          },
        }));
      } catch (error) {
        console.error('Error fetching unit:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourse();
  }, [unitId]);

  // Handle array field operations
  const addArrayItem = (path: string) => {
    const keys = path.split('.');
    setLrdData(prev => {
      const newData = { ...prev };
      let current = newData;

      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }

      const lastKey = keys[keys.length - 1];
      current[lastKey] = [...current[lastKey], ''];

      return newData;
    });
  };

  const removeArrayItem = (path: string, index: number) => {
    const keys = path.split('.');
    setLrdData(prev => {
      const newData = { ...prev };
      let current = newData;

      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }

      const lastKey = keys[keys.length - 1];
      current[lastKey] = current[lastKey].filter(
        (_: any, i: number) => i !== index
      );

      return newData;
    });
  };

  const updateArrayItem = (path: string, index: number, value: string) => {
    const keys = path.split('.');
    setLrdData(prev => {
      const newData = { ...prev };
      let current = newData;

      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }

      const lastKey = keys[keys.length - 1];
      current[lastKey][index] = value;

      return newData;
    });
  };

  // Validate form
  const validateForm = () => {
    const newErrors: LRDErrors = {};

    if (!lrdData.content.topic) {
      newErrors.topic = 'Topic is required';
    }

    if (!lrdData.content.duration) {
      newErrors.duration = 'Duration is required';
    }

    if (
      lrdData.content.objectives.filter((o: string) => o.trim()).length === 0
    ) {
      newErrors.objectives = 'At least one objective is required';
    }

    if (
      lrdData.content.learningOutcomes.filter((o: string) => o.trim())
        .length === 0
    ) {
      newErrors.learningOutcomes = 'At least one learning outcome is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Save LRD
  const saveLRD = async (submitForReview: boolean = false) => {
    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);

      // Clean empty arrays
      const cleanedData = {
        ...lrdData,
        content: {
          ...lrdData.content,
          objectives: lrdData.content.objectives.filter((o: string) =>
            o.trim()
          ),
          learningOutcomes: lrdData.content.learningOutcomes.filter(
            (o: string) => o.trim()
          ),
          prerequisites: lrdData.content.prerequisites.filter((p: string) =>
            p.trim()
          ),
          structure: {
            preClass: {
              ...lrdData.content.structure.preClass,
              activities: lrdData.content.structure.preClass.activities.filter(
                (a: string) => a.trim()
              ),
              materials: lrdData.content.structure.preClass.materials.filter(
                (m: string) => m.trim()
              ),
            },
            inClass: {
              ...lrdData.content.structure.inClass,
              activities: lrdData.content.structure.inClass.activities.filter(
                (a: string) => a.trim()
              ),
              materials: lrdData.content.structure.inClass.materials.filter(
                (m: string) => m.trim()
              ),
            },
            postClass: {
              ...lrdData.content.structure.postClass,
              activities: lrdData.content.structure.postClass.activities.filter(
                (a: string) => a.trim()
              ),
              materials: lrdData.content.structure.postClass.materials.filter(
                (m: string) => m.trim()
              ),
            },
          },
          assessment: {
            ...lrdData.content.assessment,
            criteria: lrdData.content.assessment.criteria.filter((c: string) =>
              c.trim()
            ),
          },
          resources: {
            required: lrdData.content.resources.required.filter((r: string) =>
              r.trim()
            ),
            recommended: lrdData.content.resources.recommended.filter(
              (r: string) => r.trim()
            ),
            supplementary: lrdData.content.resources.supplementary.filter(
              (r: string) => r.trim()
            ),
          },
          technologyRequirements: lrdData.content.technologyRequirements.filter(
            (t: string) => t.trim()
          ),
        },
      };

      const response = await api.post('/lrds', cleanedData);

      if (submitForReview && response.data.id) {
        // Submit for review
        await api.post(`/lrds/${response.data.id}/submit-review`);
      }

      // Generate tasks if requested
      if (window.confirm('Would you like to generate tasks from this LRD?')) {
        await api.post(`/lrds/${response.data.id}/generate-tasks`);
      }

      navigate(`/units/${unitId}/lrds`);
    } catch (error) {
      console.error('Error saving LRD:', error);
      setErrors({
        submit: (error as any).response?.data?.detail || 'Failed to save LRD',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className='flex justify-center items-center h-64'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  return (
    <div className='max-w-6xl mx-auto p-6'>
      {/* Header */}
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          Create Learning Resource Document (LRD)
        </h1>
        {unit && (
          <p className='text-gray-600'>
            For: {unit.title} ({unit.code})
          </p>
        )}
      </div>

      {/* Error Alert */}
      {errors.submit && (
        <div className='mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start'>
          <AlertCircle className='h-5 w-5 text-red-600 mt-0.5 mr-2' />
          <span className='text-red-800'>{errors.submit}</span>
        </div>
      )}

      {/* Basic Information */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <h2 className='text-xl font-semibold mb-4 flex items-center'>
          <BookOpen className='h-5 w-5 mr-2 text-blue-600' />
          Basic Information
        </h2>

        <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Topic/Module Title *
            </label>
            <input
              type='text'
              value={lrdData.content.topic}
              onChange={e =>
                setLrdData(prev => ({
                  ...prev,
                  content: { ...prev.content, topic: e.target.value },
                }))
              }
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.topic ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder='e.g., Introduction to Python Programming'
            />
            {errors.topic && (
              <p className='text-red-500 text-sm mt-1'>{errors.topic}</p>
            )}
          </div>

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Duration *
            </label>
            <input
              type='text'
              value={lrdData.content.duration}
              onChange={e =>
                setLrdData(prev => ({
                  ...prev,
                  content: { ...prev.content, duration: e.target.value },
                }))
              }
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.duration ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder='e.g., 2 weeks, 6 hours'
            />
            {errors.duration && (
              <p className='text-red-500 text-sm mt-1'>{errors.duration}</p>
            )}
          </div>

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Version
            </label>
            <input
              type='text'
              value={lrdData.version}
              onChange={e =>
                setLrdData(prev => ({ ...prev, version: e.target.value }))
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              placeholder='1.0'
            />
          </div>

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Teaching Philosophy
            </label>
            <select
              value={
                lrdData.content.teachingPhilosophy ||
                unit?.teachingPhilosophy ||
                'TRADITIONAL'
              }
              onChange={e =>
                setLrdData(prev => ({
                  ...prev,
                  content: {
                    ...prev.content,
                    teachingPhilosophy: e.target.value,
                  },
                }))
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            >
              <option value='TRADITIONAL'>Traditional</option>
              <option value='FLIPPED_CLASSROOM'>Flipped Classroom</option>
              <option value='CONSTRUCTIVIST'>Constructivist</option>
              <option value='PROJECT_BASED'>Project Based</option>
              <option value='INQUIRY_BASED'>Inquiry Based</option>
              <option value='COLLABORATIVE'>Collaborative</option>
              <option value='EXPERIENTIAL'>Experiential</option>
              <option value='PROBLEM_BASED'>Problem Based</option>
              <option value='MIXED_APPROACH'>Mixed Approach</option>
            </select>
          </div>
        </div>
      </div>

      {/* Learning Objectives */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <h2 className='text-xl font-semibold mb-4 flex items-center'>
          <Target className='h-5 w-5 mr-2 text-green-600' />
          Learning Objectives & Outcomes
        </h2>

        <div className='space-y-6'>
          {/* Objectives */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Learning Objectives *
            </label>
            {lrdData.content.objectives.map((objective, index) => (
              <div key={index} className='flex mb-2'>
                <input
                  type='text'
                  value={objective}
                  onChange={e =>
                    updateArrayItem('content.objectives', index, e.target.value)
                  }
                  className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  placeholder='Enter learning objective'
                />
                <button
                  onClick={() => removeArrayItem('content.objectives', index)}
                  className='ml-2 p-2 text-red-600 hover:bg-red-50 rounded-lg'
                  disabled={lrdData.content.objectives.length === 1}
                >
                  <X className='h-5 w-5' />
                </button>
              </div>
            ))}
            <button
              onClick={() => addArrayItem('content.objectives')}
              className='mt-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center'
            >
              <Plus className='h-4 w-4 mr-1' />
              Add Objective
            </button>
            {errors.objectives && (
              <p className='text-red-500 text-sm mt-1'>{errors.objectives}</p>
            )}
          </div>

          {/* Learning Outcomes */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Learning Outcomes *
            </label>
            {lrdData.content.learningOutcomes.map((outcome, index) => (
              <div key={index} className='flex mb-2'>
                <input
                  type='text'
                  value={outcome}
                  onChange={e =>
                    updateArrayItem(
                      'content.learningOutcomes',
                      index,
                      e.target.value
                    )
                  }
                  className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  placeholder='Enter learning outcome'
                />
                <button
                  onClick={() =>
                    removeArrayItem('content.learningOutcomes', index)
                  }
                  className='ml-2 p-2 text-red-600 hover:bg-red-50 rounded-lg'
                  disabled={lrdData.content.learningOutcomes.length === 1}
                >
                  <X className='h-5 w-5' />
                </button>
              </div>
            ))}
            <button
              onClick={() => addArrayItem('content.learningOutcomes')}
              className='mt-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center'
            >
              <Plus className='h-4 w-4 mr-1' />
              Add Outcome
            </button>
            {errors.learningOutcomes && (
              <p className='text-red-500 text-sm mt-1'>
                {errors.learningOutcomes}
              </p>
            )}
          </div>

          {/* Prerequisites */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Prerequisites
            </label>
            {lrdData.content.prerequisites.map((prereq, index) => (
              <div key={index} className='flex mb-2'>
                <input
                  type='text'
                  value={prereq}
                  onChange={e =>
                    updateArrayItem(
                      'content.prerequisites',
                      index,
                      e.target.value
                    )
                  }
                  className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  placeholder='Enter prerequisite'
                />
                <button
                  onClick={() =>
                    removeArrayItem('content.prerequisites', index)
                  }
                  className='ml-2 p-2 text-red-600 hover:bg-red-50 rounded-lg'
                  disabled={lrdData.content.prerequisites.length === 1}
                >
                  <X className='h-5 w-5' />
                </button>
              </div>
            ))}
            <button
              onClick={() => addArrayItem('content.prerequisites')}
              className='mt-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center'
            >
              <Plus className='h-4 w-4 mr-1' />
              Add Prerequisite
            </button>
          </div>
        </div>
      </div>

      {/* Class Structure */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <h2 className='text-xl font-semibold mb-4 flex items-center'>
          <Clock className='h-5 w-5 mr-2 text-purple-600' />
          Class Structure
        </h2>

        <div className='space-y-6'>
          {/* Pre-Class */}
          <div className='border-l-4 border-yellow-400 pl-4'>
            <h3 className='font-semibold mb-3'>Pre-Class Activities</h3>

            <div className='mb-4'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Duration
              </label>
              <input
                type='text'
                value={lrdData.content.structure.preClass.duration}
                onChange={e =>
                  setLrdData(prev => ({
                    ...prev,
                    content: {
                      ...prev.content,
                      structure: {
                        ...prev.content.structure,
                        preClass: {
                          ...prev.content.structure.preClass,
                          duration: e.target.value,
                        },
                      },
                    },
                  }))
                }
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                placeholder='e.g., 2 hours'
              />
            </div>

            <div className='mb-4'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Activities
              </label>
              {lrdData.content.structure.preClass.activities.map(
                (activity, index) => (
                  <div key={index} className='flex mb-2'>
                    <input
                      type='text'
                      value={activity}
                      onChange={e =>
                        updateArrayItem(
                          'content.structure.preClass.activities',
                          index,
                          e.target.value
                        )
                      }
                      className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      placeholder='Enter pre-class activity'
                    />
                    <button
                      onClick={() =>
                        removeArrayItem(
                          'content.structure.preClass.activities',
                          index
                        )
                      }
                      className='ml-2 p-2 text-red-600 hover:bg-red-50 rounded-lg'
                      disabled={
                        lrdData.content.structure.preClass.activities.length ===
                        1
                      }
                    >
                      <X className='h-5 w-5' />
                    </button>
                  </div>
                )
              )}
              <button
                onClick={() =>
                  addArrayItem('content.structure.preClass.activities')
                }
                className='mt-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center'
              >
                <Plus className='h-4 w-4 mr-1' />
                Add Activity
              </button>
            </div>
          </div>

          {/* In-Class */}
          <div className='border-l-4 border-green-400 pl-4'>
            <h3 className='font-semibold mb-3'>In-Class Activities</h3>

            <div className='mb-4'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Duration
              </label>
              <input
                type='text'
                value={lrdData.content.structure.inClass.duration}
                onChange={e =>
                  setLrdData(prev => ({
                    ...prev,
                    content: {
                      ...prev.content,
                      structure: {
                        ...prev.content.structure,
                        inClass: {
                          ...prev.content.structure.inClass,
                          duration: e.target.value,
                        },
                      },
                    },
                  }))
                }
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                placeholder='e.g., 2 hours'
              />
            </div>

            <div className='mb-4'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Activities
              </label>
              {lrdData.content.structure.inClass.activities.map(
                (activity, index) => (
                  <div key={index} className='flex mb-2'>
                    <input
                      type='text'
                      value={activity}
                      onChange={e =>
                        updateArrayItem(
                          'content.structure.inClass.activities',
                          index,
                          e.target.value
                        )
                      }
                      className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      placeholder='Enter in-class activity'
                    />
                    <button
                      onClick={() =>
                        removeArrayItem(
                          'content.structure.inClass.activities',
                          index
                        )
                      }
                      className='ml-2 p-2 text-red-600 hover:bg-red-50 rounded-lg'
                      disabled={
                        lrdData.content.structure.inClass.activities.length ===
                        1
                      }
                    >
                      <X className='h-5 w-5' />
                    </button>
                  </div>
                )
              )}
              <button
                onClick={() =>
                  addArrayItem('content.structure.inClass.activities')
                }
                className='mt-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center'
              >
                <Plus className='h-4 w-4 mr-1' />
                Add Activity
              </button>
            </div>
          </div>

          {/* Post-Class */}
          <div className='border-l-4 border-blue-400 pl-4'>
            <h3 className='font-semibold mb-3'>Post-Class Activities</h3>

            <div className='mb-4'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Duration
              </label>
              <input
                type='text'
                value={lrdData.content.structure.postClass.duration}
                onChange={e =>
                  setLrdData(prev => ({
                    ...prev,
                    content: {
                      ...prev.content,
                      structure: {
                        ...prev.content.structure,
                        postClass: {
                          ...prev.content.structure.postClass,
                          duration: e.target.value,
                        },
                      },
                    },
                  }))
                }
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                placeholder='e.g., 3 hours'
              />
            </div>

            <div className='mb-4'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Activities
              </label>
              {lrdData.content.structure.postClass.activities.map(
                (activity, index) => (
                  <div key={index} className='flex mb-2'>
                    <input
                      type='text'
                      value={activity}
                      onChange={e =>
                        updateArrayItem(
                          'content.structure.postClass.activities',
                          index,
                          e.target.value
                        )
                      }
                      className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      placeholder='Enter post-class activity'
                    />
                    <button
                      onClick={() =>
                        removeArrayItem(
                          'content.structure.postClass.activities',
                          index
                        )
                      }
                      className='ml-2 p-2 text-red-600 hover:bg-red-50 rounded-lg'
                      disabled={
                        lrdData.content.structure.postClass.activities
                          .length === 1
                      }
                    >
                      <X className='h-5 w-5' />
                    </button>
                  </div>
                )
              )}
              <button
                onClick={() =>
                  addArrayItem('content.structure.postClass.activities')
                }
                className='mt-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center'
              >
                <Plus className='h-4 w-4 mr-1' />
                Add Activity
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Assessment */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <h2 className='text-xl font-semibold mb-4 flex items-center'>
          <CheckCircle className='h-5 w-5 mr-2 text-orange-600' />
          Assessment
        </h2>

        <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Assessment Type
            </label>
            <input
              type='text'
              value={lrdData.content.assessment.type}
              onChange={e =>
                setLrdData(prev => ({
                  ...prev,
                  content: {
                    ...prev.content,
                    assessment: {
                      ...prev.content.assessment,
                      type: e.target.value,
                    },
                  },
                }))
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              placeholder='e.g., Quiz, Assignment, Project'
            />
          </div>

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Weight
            </label>
            <input
              type='text'
              value={lrdData.content.assessment.weight}
              onChange={e =>
                setLrdData(prev => ({
                  ...prev,
                  content: {
                    ...prev.content,
                    assessment: {
                      ...prev.content.assessment,
                      weight: e.target.value,
                    },
                  },
                }))
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              placeholder='e.g., 20%'
            />
          </div>
        </div>

        <div className='mt-4'>
          <label className='block text-sm font-medium text-gray-700 mb-2'>
            Description
          </label>
          <textarea
            value={lrdData.content.assessment.description}
            onChange={e =>
              setLrdData(prev => ({
                ...prev,
                content: {
                  ...prev.content,
                  assessment: {
                    ...prev.content.assessment,
                    description: e.target.value,
                  },
                },
              }))
            }
            className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            rows={3}
            placeholder='Describe the assessment...'
          />
        </div>
      </div>

      {/* Resources */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <h2 className='text-xl font-semibold mb-4 flex items-center'>
          <FileText className='h-5 w-5 mr-2 text-indigo-600' />
          Resources
        </h2>

        <div className='space-y-4'>
          {/* Required Resources */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Required Resources
            </label>
            {lrdData.content.resources.required.map((resource, index) => (
              <div key={index} className='flex mb-2'>
                <input
                  type='text'
                  value={resource}
                  onChange={e =>
                    updateArrayItem(
                      'content.resources.required',
                      index,
                      e.target.value
                    )
                  }
                  className='flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  placeholder='Enter required resource'
                />
                <button
                  onClick={() =>
                    removeArrayItem('content.resources.required', index)
                  }
                  className='ml-2 p-2 text-red-600 hover:bg-red-50 rounded-lg'
                  disabled={lrdData.content.resources.required.length === 1}
                >
                  <X className='h-5 w-5' />
                </button>
              </div>
            ))}
            <button
              onClick={() => addArrayItem('content.resources.required')}
              className='mt-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center'
            >
              <Plus className='h-4 w-4 mr-1' />
              Add Resource
            </button>
          </div>
        </div>
      </div>

      {/* Additional Notes */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <h2 className='text-xl font-semibold mb-4 flex items-center'>
          <Users className='h-5 w-5 mr-2 text-teal-600' />
          Additional Information
        </h2>

        <div className='space-y-4'>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Pedagogy Notes
            </label>
            <textarea
              value={lrdData.content.pedagogyNotes}
              onChange={e =>
                setLrdData(prev => ({
                  ...prev,
                  content: { ...prev.content, pedagogyNotes: e.target.value },
                }))
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              rows={3}
              placeholder='Notes about teaching approach...'
            />
          </div>

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Differentiation Strategies
            </label>
            <textarea
              value={lrdData.content.differentiation}
              onChange={e =>
                setLrdData(prev => ({
                  ...prev,
                  content: { ...prev.content, differentiation: e.target.value },
                }))
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              rows={3}
              placeholder='How to adapt for different learners...'
            />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className='flex justify-end space-x-4'>
        <button
          onClick={() => navigate(`/units/${unitId}`)}
          className='px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50'
        >
          Cancel
        </button>
        <button
          onClick={() => saveLRD(false)}
          disabled={saving}
          className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center'
        >
          {saving ? (
            <Loader2 className='h-4 w-4 mr-2 animate-spin' />
          ) : (
            <Save className='h-4 w-4 mr-2' />
          )}
          Save as Draft
        </button>
        <button
          onClick={() => saveLRD(true)}
          disabled={saving}
          className='px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center'
        >
          {saving ? (
            <Loader2 className='h-4 w-4 mr-2 animate-spin' />
          ) : (
            <Send className='h-4 w-4 mr-2' />
          )}
          Submit for Review
        </button>
      </div>
    </div>
  );
};

export default LRDCreator;
