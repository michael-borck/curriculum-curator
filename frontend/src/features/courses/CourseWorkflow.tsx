import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Wand2,
  Upload,
  BookOpen,
  Settings,
  FileText,
  Plus,
  Loader2,
  Layout,
  Target,
  Calendar,
  Award
} from 'lucide-react';
import WorkflowWizard from '../../components/Wizard/WorkflowWizard';
import PDFImportDialog from '../../components/Import/PDFImportDialog';
import UnitStructureView from '../../components/UnitStructure/UnitStructureView';
import api from '../../services/api';

interface Unit {
  id: string;
  name: string;
  code: string;
  description: string;
}

interface UnitOutline {
  id: string;
  title: string;
  description?: string;
  duration_weeks: number;
  delivery_mode?: string;
  teaching_pattern?: string;
  is_complete: boolean;
  completion_percentage: number;
}

const CourseWorkflow: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [unitOutline, setUnitOutline] = useState<UnitOutline | null>(null);
  const [learningOutcomes, setLearningOutcomes] = useState<any[]>([]);
  const [weeklyTopics, setWeeklyTopics] = useState<any[]>([]);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [activeView, setActiveView] = useState<'structure' | 'wizard' | 'import'>('structure');
  const [showPDFImport, setShowPDFImport] = useState(false);
  const [showWorkflowWizard, setShowWorkflowWizard] = useState(false);

  useEffect(() => {
    fetchCourseData();
  }, [courseId]);

  const fetchCourseData = async () => {
    try {
      setLoading(true);
      
      // Fetch unit/course data
      const courseResponse = await api.get(`/api/courses/${courseId}`);
      setUnit({
        id: courseResponse.data.id,
        name: courseResponse.data.title,
        code: courseResponse.data.code,
        description: courseResponse.data.description
      });

      // Try to fetch course structure if it exists
      try {
        const outlineResponse = await api.get(`/api/courses/${courseId}/structure`);
        if (outlineResponse.data) {
          setUnitOutline(outlineResponse.data.outline);
          setLearningOutcomes(outlineResponse.data.learning_outcomes || []);
          setWeeklyTopics(outlineResponse.data.weekly_topics || []);
          setAssessments(outlineResponse.data.assessments || []);
        }
      } catch (err) {
        // No structure exists yet
        console.log('No course structure found');
      }
    } catch (error) {
      console.error('Error fetching course data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWorkflowComplete = (outlineId: string) => {
    setShowWorkflowWizard(false);
    fetchCourseData(); // Refresh data
  };

  const handleImportComplete = () => {
    setShowPDFImport(false);
    fetchCourseData(); // Refresh data
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!unit) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Course not found
        </h2>
        <Link to="/courses" className="text-blue-600 hover:text-blue-700">
          ← Back to courses
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/courses"
          className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to units
        </Link>

        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {unit.name}
            </h1>
            <p className="text-gray-600 text-lg mb-2">{unit.code}</p>
            <p className="text-gray-500">{unit.description}</p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/content/new?courseId=${courseId}`)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Plus size={18} />
              Create Content
            </button>
            <button
              onClick={() => navigate(`/courses/${courseId}/settings`)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Settings size={18} />
              Settings
            </button>
          </div>
        </div>
      </div>

      {/* Action Cards or Course Structure */}
      {!unitOutline ? (
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 text-center">
            Get Started with Unit Structure
          </h2>
          <p className="text-gray-600 text-center mb-8">
            Choose how you want to create your unit structure
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Guided Workflow Card */}
            <div className="border-2 border-gray-200 rounded-lg p-6 hover:border-blue-500 transition-colors">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <Wand2 className="w-8 h-8 text-blue-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                Guided Creation
              </h3>
              <p className="text-gray-600 text-center mb-4">
                Answer questions to generate a complete unit structure with AI assistance
              </p>
              <button
                onClick={() => setShowWorkflowWizard(true)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Start Wizard
              </button>
            </div>

            {/* PDF Import Card */}
            <div className="border-2 border-gray-200 rounded-lg p-6 hover:border-green-500 transition-colors">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                  <Upload className="w-8 h-8 text-green-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                Import from PDF
              </h3>
              <p className="text-gray-600 text-center mb-4">
                Upload unit outlines, syllabi, or teaching materials to extract structure
              </p>
              <button
                onClick={() => setShowPDFImport(true)}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Upload PDF
              </button>
            </div>

            {/* Manual Creation Card */}
            <div className="border-2 border-gray-200 rounded-lg p-6 hover:border-purple-500 transition-colors">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
                  <BookOpen className="w-8 h-8 text-purple-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                Manual Creation
              </h3>
              <p className="text-gray-600 text-center mb-4">
                Build your unit structure manually with full control over every detail
              </p>
              <button
                onClick={() => alert('Manual structure editor coming soon! For now, use the Guided Workflow or PDF Import.')}
                className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                Create Manually
              </button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="mt-8 pt-8 border-t grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <Target className="w-6 h-6 text-gray-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900">0</p>
              <p className="text-sm text-gray-500">Learning Outcomes</p>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <Calendar className="w-6 h-6 text-gray-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900">0</p>
              <p className="text-sm text-gray-500">Weekly Topics</p>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <Award className="w-6 h-6 text-gray-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900">0</p>
              <p className="text-sm text-gray-500">Assessments</p>
            </div>
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <FileText className="w-6 h-6 text-gray-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900">0</p>
              <p className="text-sm text-gray-500">Content Items</p>
            </div>
          </div>
        </div>
      ) : (
        <UnitStructureView
          outline={unitOutline}
          learningOutcomes={learningOutcomes}
          weeklyTopics={weeklyTopics}
          assessments={assessments}
        />
      )}

      {/* Workflow Wizard Modal */}
      {showWorkflowWizard && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            <WorkflowWizard
              unitId={courseId!}
              unitName={unit.name}
              onComplete={handleWorkflowComplete}
              onCancel={() => setShowWorkflowWizard(false)}
            />
          </div>
        </div>
      )}

      {/* PDF Import Dialog */}
      {showPDFImport && (
        <PDFImportDialog
          unitId={courseId!}
          unitName={unit.name}
          onClose={() => setShowPDFImport(false)}
          onImportComplete={handleImportComplete}
        />
      )}
    </div>
  );
};

export default CourseWorkflow;