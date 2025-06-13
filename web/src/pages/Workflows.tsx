import React, { useEffect, useState } from 'react';
import { Play, Plus } from 'lucide-react';
import { workflowApi } from '../services/api';
import { WorkflowListResponse, WorkflowRunRequest } from '../types';

const Workflows: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningWorkflow, setRunningWorkflow] = useState<string | null>(null);
  const [showRunModal, setShowRunModal] = useState<string | null>(null);
  const [variables, setVariables] = useState<string>('{}');

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const data = await workflowApi.listWorkflows();
        setWorkflows(data);
      } catch (error) {
        console.error('Error fetching workflows:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflows();
  }, []);

  const handleRunWorkflow = async (workflowName: string) => {
    try {
      setRunningWorkflow(workflowName);
      
      let parsedVariables = {};
      try {
        parsedVariables = JSON.parse(variables);
      } catch (e) {
        alert('Invalid JSON in variables field');
        return;
      }

      const request: WorkflowRunRequest = {
        workflow: workflowName,
        variables: parsedVariables,
      };

      const response = await workflowApi.runWorkflow(request);
      alert(`Workflow started successfully! Session ID: ${response.session_id}`);
      setShowRunModal(null);
      setVariables('{}');
    } catch (error) {
      console.error('Error running workflow:', error);
      alert('Failed to run workflow');
    } finally {
      setRunningWorkflow(null);
    }
  };

  const WorkflowCard: React.FC<{ name: string; workflow: any; type: 'config' | 'predefined' }> = ({
    name,
    workflow,
    type,
  }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-medium text-gray-900">{name}</h3>
          <p className="mt-1 text-sm text-gray-500">
            {workflow.description || 'No description available'}
          </p>
          <div className="mt-2">
            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
              type === 'config' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
            }`}>
              {type === 'config' ? 'Custom' : 'Built-in'}
            </span>
          </div>
        </div>
        <button
          onClick={() => setShowRunModal(name)}
          disabled={runningWorkflow === name}
          className="ml-4 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
        >
          <Play className="w-4 h-4 mr-2" />
          {runningWorkflow === name ? 'Running...' : 'Run'}
        </button>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
          <p className="mt-2 text-gray-600">
            Manage and run your curriculum curation workflows
          </p>
        </div>
        <button
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Workflow
        </button>
      </div>

      {/* Built-in Workflows */}
      {workflows?.predefined_workflows && Object.keys(workflows.predefined_workflows).length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Built-in Workflows</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(workflows.predefined_workflows).map(([name, workflow]) => (
              <WorkflowCard key={name} name={name} workflow={workflow} type="predefined" />
            ))}
          </div>
        </div>
      )}

      {/* Custom Workflows */}
      {workflows?.config_workflows && Object.keys(workflows.config_workflows).length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Custom Workflows</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(workflows.config_workflows).map(([name, workflow]) => (
              <WorkflowCard key={name} name={name} workflow={workflow} type="config" />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!workflows?.predefined_workflows || Object.keys(workflows.predefined_workflows).length === 0) &&
       (!workflows?.config_workflows || Object.keys(workflows.config_workflows).length === 0) && (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No workflows found</h3>
            <p className="text-gray-500 mb-4">
              Create your first workflow or check your configuration file.
            </p>
            <button
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Workflow
            </button>
          </div>
        </div>
      )}

      {/* Run Workflow Modal */}
      {showRunModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Run Workflow: {showRunModal}
              </h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Variables (JSON)
                </label>
                <textarea
                  value={variables}
                  onChange={(e) => setVariables(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows={4}
                  placeholder='{"key": "value"}'
                />
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => handleRunWorkflow(showRunModal)}
                  disabled={runningWorkflow === showRunModal}
                  className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  <Play className="w-4 h-4 mr-2" />
                  {runningWorkflow === showRunModal ? 'Running...' : 'Run Workflow'}
                </button>
                <button
                  onClick={() => {
                    setShowRunModal(null);
                    setVariables('{}');
                  }}
                  className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workflows;