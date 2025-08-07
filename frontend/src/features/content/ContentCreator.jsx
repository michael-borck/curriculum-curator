import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import RichTextEditor from '../../components/Editor/RichTextEditor';
import PedagogySelector from '../../components/Wizard/PedagogySelector';
import { generateContent, enhanceContent } from '../../services/api';
import { Loader2, Sparkles, Save, Download } from 'lucide-react';
import toast from 'react-hot-toast';

const ContentCreator = () => {
  const { type } = useParams();
  const [content, setContent] = useState('');
  const [pedagogy, setPedagogy] = useState('inquiry-based');
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamedContent, setStreamedContent] = useState('');
  
  const handleGenerate = async () => {
    setIsGenerating(true);
    setStreamedContent('');
    
    try {
      const eventSource = new EventSource(
        `http://localhost:8000/api/llm/generate?` +
        `type=${type}&pedagogy=${pedagogy}&stream=true`
      );
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setStreamedContent(prev => prev + data.content);
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        setIsGenerating(false);
        setContent(streamedContent);
        toast.success('Content generated successfully!');
      };
    } catch (error) {
      toast.error('Failed to generate content');
      setIsGenerating(false);
    }
  };
  
  const handleEnhance = async () => {
    if (!content) {
      toast.error('Please add some content first');
      return;
    }
    
    setIsGenerating(true);
    try {
      const enhanced = await enhanceContent(content, pedagogy);
      setContent(enhanced.content);
      toast.success('Content enhanced!');
    } catch (error) {
      toast.error('Failed to enhance content');
    } finally {
      setIsGenerating(false);
    }
  };
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Create {type.charAt(0).toUpperCase() + type.slice(1)}
        </h1>
        <p className="text-gray-600">
          AI-powered content creation with pedagogical alignment
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-xl font-semibold">Content Editor</h2>
              <div className="flex gap-2">
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {isGenerating ? (
                    <Loader2 className="animate-spin" size={18} />
                  ) : (
                    <Sparkles size={18} />
                  )}
                  Generate
                </button>
                <button
                  onClick={handleEnhance}
                  disabled={isGenerating || !content}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Enhance
                </button>
                <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2">
                  <Save size={18} />
                  Save
                </button>
              </div>
            </div>
            
            {isGenerating && streamedContent ? (
              <div className="border border-gray-300 rounded-lg p-4 min-h-[400px] bg-gray-50">
                <div className="prose max-w-none">
                  <div dangerouslySetInnerHTML={{ __html: streamedContent }} />
                  <span className="inline-block w-2 h-4 bg-gray-600 animate-pulse" />
                </div>
              </div>
            ) : (
              <RichTextEditor
                content={content}
                onChange={setContent}
                pedagogyHints={getPedagogyHint(pedagogy)}
              />
            )}
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Teaching Philosophy</h3>
            <PedagogySelector
              selected={pedagogy}
              onChange={setPedagogy}
            />
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Content Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Difficulty Level
                </label>
                <select className="w-full p-2 border border-gray-300 rounded-lg">
                  <option>Beginner</option>
                  <option>Intermediate</option>
                  <option>Advanced</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duration
                </label>
                <input
                  type="text"
                  placeholder="e.g., 50 minutes"
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Learning Objectives
                </label>
                <textarea
                  rows="3"
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Enter key learning objectives..."
                />
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Export Options</h3>
            <div className="space-y-2">
              <button className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2">
                <Download size={18} />
                Export as Word
              </button>
              <button className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2">
                <Download size={18} />
                Export as PDF
              </button>
              <button className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2">
                <Download size={18} />
                Export as Markdown
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const getPedagogyHint = (style) => {
  const hints = {
    'inquiry-based': 'Start with thought-provoking questions to encourage exploration.',
    'project-based': 'Include real-world applications and hands-on activities.',
    'traditional': 'Focus on clear explanations and structured examples.',
    'collaborative': 'Add group activities and discussion prompts.',
    'game-based': 'Incorporate challenges, points, or competitive elements.'
  };
  return hints[style] || '';
};

export default ContentCreator;