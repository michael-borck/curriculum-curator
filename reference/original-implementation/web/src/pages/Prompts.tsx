import React, { useEffect, useState } from 'react';
import { FileText, Search } from 'lucide-react';
import { promptApi } from '../services/api';
import { PromptListResponse } from '../types';

const Prompts: React.FC = () => {
  const [prompts, setPrompts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTag, setSearchTag] = useState('');

  const fetchPrompts = async (tag?: string) => {
    try {
      setLoading(true);
      const data: PromptListResponse = await promptApi.listPrompts(tag);
      setPrompts(data.prompts);
    } catch (error) {
      console.error('Error fetching prompts:', error);
      setPrompts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPrompts(searchTag || undefined);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Prompt Templates</h1>
        <p className="mt-2 text-gray-600">
          Manage your prompt templates for curriculum generation
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <form onSubmit={handleSearch} className="flex space-x-4">
          <div className="flex-1">
            <label htmlFor="search" className="sr-only">
              Search by tag
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                id="search"
                value={searchTag}
                onChange={(e) => setSearchTag(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Filter by tag (e.g., assessment, course, lecture)"
              />
            </div>
          </div>
          <button
            type="submit"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Search
          </button>
          {searchTag && (
            <button
              type="button"
              onClick={() => {
                setSearchTag('');
                fetchPrompts();
              }}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Prompts List */}
      {prompts.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTag ? 'No prompts found' : 'No prompt templates found'}
          </h3>
          <p className="text-gray-500 mb-4">
            {searchTag 
              ? `No prompts match the tag "${searchTag}"`
              : 'Create your first prompt template to get started.'
            }
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              Available Prompts {searchTag && `(filtered by "${searchTag}")`}
            </h2>
          </div>
          <div className="divide-y divide-gray-200">
            {prompts.map((prompt, index) => (
              <div key={index} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="w-5 h-5 text-gray-400 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{prompt}</p>
                      <p className="text-sm text-gray-500">
                        {prompt.split('/').slice(-1)[0].replace('.txt', '')} template
                      </p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button className="text-primary-600 hover:text-primary-900 text-sm font-medium">
                      View
                    </button>
                    <button className="text-primary-600 hover:text-primary-900 text-sm font-medium">
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {prompts.length > 0 && (
        <div className="mt-6 text-sm text-gray-500">
          Showing {prompts.length} prompt template{prompts.length !== 1 ? 's' : ''}
          {searchTag && ` matching "${searchTag}"`}
        </div>
      )}
    </div>
  );
};

export default Prompts;