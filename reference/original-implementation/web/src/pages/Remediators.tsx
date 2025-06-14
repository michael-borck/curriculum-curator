import React, { useEffect, useState } from 'react';
import { Settings, CheckCircle, XCircle, Wrench } from 'lucide-react';
import { remediatorApi } from '../services/api';
import { RemediatorInfo } from '../types';

const Remediators: React.FC = () => {
  const [remediators, setRemediators] = useState<Record<string, RemediatorInfo[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRemediators = async () => {
      try {
        const data = await remediatorApi.listRemediators();
        setRemediators(data);
      } catch (error) {
        console.error('Error fetching remediators:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRemediators();
  }, []);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'autofix':
        return <Wrench className="w-6 h-6 text-blue-500" />;
      case 'rewrite':
        return <Settings className="w-6 h-6 text-green-500" />;
      case 'workflow':
        return <Settings className="w-6 h-6 text-purple-500" />;
      case 'language':
        return <Settings className="w-6 h-6 text-orange-500" />;
      default:
        return <Settings className="w-6 h-6 text-gray-500" />;
    }
  };

  const getCategoryDescription = (category: string) => {
    switch (category) {
      case 'autofix':
        return 'Automated fixes for common formatting and structural issues';
      case 'rewrite':
        return 'Content rewriting and rephrasing tools';
      case 'workflow':
        return 'Workflow management and review tools';
      case 'language':
        return 'Language translation and localization tools';
      default:
        return 'Content remediation tools';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const totalRemediators = Object.values(remediators).flat().length;
  const implementedRemediators = Object.values(remediators).flat().filter(r => r.implemented).length;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Remediators</h1>
        <p className="mt-2 text-gray-600">
          Content remediation tools for fixing and improving content
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Settings className="w-8 h-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Remediators</p>
              <p className="text-2xl font-semibold text-gray-900">{totalRemediators}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Implemented</p>
              <p className="text-2xl font-semibold text-gray-900">{implementedRemediators}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <XCircle className="w-8 h-8 text-gray-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">In Development</p>
              <p className="text-2xl font-semibold text-gray-900">{totalRemediators - implementedRemediators}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Remediator Categories */}
      <div className="space-y-8">
        {Object.entries(remediators).map(([category, categoryRemediators]) => (
          categoryRemediators.length > 0 && (
            <div key={category} className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center">
                  {getCategoryIcon(category)}
                  <div className="ml-3">
                    <h2 className="text-lg font-medium text-gray-900 capitalize">
                      {category} Remediators
                    </h2>
                    <p className="text-sm text-gray-500">
                      {getCategoryDescription(category)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="divide-y divide-gray-200">
                {categoryRemediators.map((remediator) => (
                  <div key={remediator.name} className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          {remediator.implemented ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <XCircle className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">
                            {remediator.name}
                          </p>
                          <p className="text-sm text-gray-500">
                            {remediator.implemented ? 'Ready to use' : 'In development'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          remediator.implemented 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {remediator.implemented ? 'Implemented' : 'Planned'}
                        </span>
                        {remediator.implemented && (
                          <button className="text-primary-600 hover:text-primary-900 text-sm font-medium">
                            Configure
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        ))}
      </div>

      {/* Empty State */}
      {totalRemediators === 0 && (
        <div className="text-center py-12">
          <Settings className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No remediators found</h3>
          <p className="text-gray-500">
            Check your remediator registry configuration.
          </p>
        </div>
      )}
    </div>
  );
};

export default Remediators;