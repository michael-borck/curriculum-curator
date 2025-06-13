import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Shield } from 'lucide-react';
import { validatorApi } from '../services/api';
import { ValidatorInfo } from '../types';

const Validators: React.FC = () => {
  const [validators, setValidators] = useState<Record<string, ValidatorInfo[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchValidators = async () => {
      try {
        const data = await validatorApi.listValidators();
        setValidators(data);
      } catch (error) {
        console.error('Error fetching validators:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchValidators();
  }, []);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'quality':
        return <CheckCircle className="w-6 h-6 text-blue-500" />;
      case 'safety':
        return <Shield className="w-6 h-6 text-red-500" />;
      case 'language':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      default:
        return <CheckCircle className="w-6 h-6 text-gray-500" />;
    }
  };

  const getCategoryDescription = (category: string) => {
    switch (category) {
      case 'quality':
        return 'Validators that check content quality, readability, and structure';
      case 'accuracy':
        return 'Validators that verify factual accuracy and references';
      case 'alignment':
        return 'Validators that ensure content aligns with objectives and requirements';
      case 'style':
        return 'Validators that check writing style, tone, and bias';
      case 'language':
        return 'Validators for grammar, spelling, and language detection';
      case 'safety':
        return 'Validators that check for content safety and appropriateness';
      default:
        return 'Content validation tools';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const totalValidators = Object.values(validators).flat().length;
  const implementedValidators = Object.values(validators).flat().filter(v => v.implemented).length;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Validators</h1>
        <p className="mt-2 text-gray-600">
          Content validation tools for ensuring quality and accuracy
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Validators</p>
              <p className="text-2xl font-semibold text-gray-900">{totalValidators}</p>
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
              <p className="text-2xl font-semibold text-gray-900">{implementedValidators}</p>
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
              <p className="text-2xl font-semibold text-gray-900">{totalValidators - implementedValidators}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Validator Categories */}
      <div className="space-y-8">
        {Object.entries(validators).map(([category, categoryValidators]) => (
          categoryValidators.length > 0 && (
            <div key={category} className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center">
                  {getCategoryIcon(category)}
                  <div className="ml-3">
                    <h2 className="text-lg font-medium text-gray-900 capitalize">
                      {category} Validators
                    </h2>
                    <p className="text-sm text-gray-500">
                      {getCategoryDescription(category)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="divide-y divide-gray-200">
                {categoryValidators.map((validator) => (
                  <div key={validator.name} className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          {validator.implemented ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <XCircle className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">
                            {validator.name}
                          </p>
                          <p className="text-sm text-gray-500">
                            {validator.implemented ? 'Ready to use' : 'In development'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          validator.implemented 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {validator.implemented ? 'Implemented' : 'Planned'}
                        </span>
                        {validator.implemented && (
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
      {totalValidators === 0 && (
        <div className="text-center py-12">
          <CheckCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No validators found</h3>
          <p className="text-gray-500">
            Check your validator registry configuration.
          </p>
        </div>
      )}
    </div>
  );
};

export default Validators;