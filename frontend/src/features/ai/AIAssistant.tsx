import React, { useState, useEffect } from 'react';
import {
  Brain,
  Send,
  Loader2,
  Sparkles,
  FileText,
  PlusCircle,
  Edit,
  HelpCircle,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import api from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const AIAssistant = () => {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your AI teaching assistant. I can help you create course content, answer pedagogical questions, and provide teaching suggestions. How can I assist you today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [providerStatus, setProviderStatus] = useState<any>(null);

  const suggestions = [
    "Create a quiz about Python basics",
    "Suggest active learning strategies for online classes",
    "Generate discussion questions for ethics in AI",
    "Explain the flipped classroom model"
  ];

  useEffect(() => {
    // Check LLM provider status
    const checkProviderStatus = async () => {
      try {
        const response = await api.get('/llm/provider-status');
        setProviderStatus(response.data);
      } catch (error) {
        console.error('Error checking provider status:', error);
      }
    };
    checkProviderStatus();
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    // Check if LLM is configured
    if (providerStatus && !providerStatus.is_configured) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: "⚠️ LLM provider is not configured. Please go to Settings > AI/LLM Settings to configure your API key or contact your administrator.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Real API call to generate content
      const response = await api.post('/llm/generate', {
        context: input,
        content_type: 'assistant_response',
        pedagogy_style: user?.teaching_philosophy || 'mixed_approach',
        stream: false
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.content,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "Sorry, I encountered an error. Please check your LLM settings or try again later.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)]">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-white rounded-lg shadow-md mr-4">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">AI Teaching Assistant</h2>
              <p className="text-sm text-gray-600">Powered by advanced pedagogy models</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                <p className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-lg">
                <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me anything about teaching or course creation..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
          
          {/* Quick Actions */}
          <div className="mt-3 flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setInput(suggestion)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div className="w-80 space-y-4">
        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="font-semibold mb-3 flex items-center">
            <Sparkles className="h-5 w-5 mr-2 text-yellow-500" />
            Quick Actions
          </h3>
          <div className="space-y-2">
            <button className="w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center">
              <FileText className="h-4 w-4 mr-2 text-blue-600" />
              Generate Lecture
            </button>
            <button className="w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center">
              <PlusCircle className="h-4 w-4 mr-2 text-green-600" />
              Create Quiz
            </button>
            <button className="w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center">
              <Edit className="h-4 w-4 mr-2 text-purple-600" />
              Improve Content
            </button>
            <button className="w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center">
              <HelpCircle className="h-4 w-4 mr-2 text-orange-600" />
              Teaching Tips
            </button>
          </div>
        </div>

        {/* Context */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="font-semibold mb-3">Current Context</h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-600">Teaching Style:</span>
              <span className="ml-2 font-medium">
                {user?.teaching_philosophy?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Mixed Approach'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Active Course:</span>
              <span className="ml-2 font-medium">None selected</span>
            </div>
            <div>
              <span className="text-gray-600">Language:</span>
              <span className="ml-2 font-medium">{user?.language_preference || 'English (AU)'}</span>
            </div>
          </div>
        </div>

        {/* LLM Provider Status */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="font-semibold mb-3">AI Provider Status</h3>
          {providerStatus ? (
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Provider:</span>
                <span className="font-medium">
                  {providerStatus.provider === 'system' 
                    ? `System (${providerStatus.actual_provider})`
                    : providerStatus.provider?.toUpperCase()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="flex items-center">
                  {providerStatus.is_configured ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-500 mr-1" />
                      <span className="text-green-600 font-medium">Configured</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-4 w-4 text-yellow-500 mr-1" />
                      <span className="text-yellow-600 font-medium">Not Configured</span>
                    </>
                  )}
                </span>
              </div>
              {providerStatus.model && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Model:</span>
                  <span className="font-medium">{providerStatus.model}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="text-sm text-gray-500">Loading...</div>
          )}
        </div>

        {/* Tips */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2 text-blue-900">Pro Tips</h3>
          <ul className="space-y-1 text-sm text-blue-800">
            <li>• Be specific about your requirements</li>
            <li>• Mention target audience level</li>
            <li>• Specify desired format (slides, text, etc.)</li>
            <li>• Ask for examples when needed</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;