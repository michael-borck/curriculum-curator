import { useState, useEffect, useRef } from 'react';
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
  CheckCircle,
  X,
} from 'lucide-react';
import api from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AIAssistantProps {
  /** When provided, unit context is prepended to every prompt. */
  unitId?: string;
  unitTitle?: string;
  unitULOs?: Array<{ code: string; description: string }>;
  /** Render as a compact sidebar panel instead of full page. */
  embedded?: boolean;
  onClose?: () => void;
}

const AIAssistant = ({
  // unitId reserved for future per-unit API calls
  unitTitle,
  unitULOs,
  embedded = false,
  onClose,
}: AIAssistantProps) => {
  const { user } = useAuthStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: unitTitle
        ? `Hi! I'm your AI teaching assistant for **${unitTitle}**. I can generate lecture content, quizzes, discussion questions, and more — all aligned to this unit's learning outcomes. How can I help?`
        : "Hi! I'm your AI teaching assistant. I can help you create unit content, answer pedagogical questions, and provide teaching suggestions. How can I assist you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [providerStatus, setProviderStatus] = useState<{
    is_configured: boolean;
    provider?: string;
    actual_provider?: string;
    model?: string;
  } | null>(null);

  // Build unit-context prefix for prompts
  const buildContextPrefix = () => {
    if (!unitTitle) return '';
    let ctx = `[Unit Context] Unit: "${unitTitle}"`;
    if (unitULOs?.length) {
      ctx +=
        '\nLearning Outcomes:\n' +
        unitULOs.map(u => `  ${u.code}: ${u.description}`).join('\n');
    }
    ctx += '\n\n';
    return ctx;
  };

  // Quick-action suggestions — contextual when unit is set
  const suggestions = unitTitle
    ? [
        `Generate a lecture outline for ${unitTitle}`,
        `Create a quiz covering the learning outcomes`,
        `Suggest discussion questions for this unit`,
        `Write a case study activity`,
      ]
    : [
        'Create a quiz about Python basics',
        'Suggest active learning strategies for online classes',
        'Generate discussion questions for ethics in AI',
        'Explain the flipped classroom model',
      ];

  useEffect(() => {
    const checkProviderStatus = async () => {
      try {
        const response = await api.get('/ai/provider-status');
        setProviderStatus(response.data);
      } catch (error) {
        console.error('Error checking provider status:', error);
      }
    };
    checkProviderStatus();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (overrideInput?: string) => {
    const text = overrideInput ?? input;
    if (!text.trim() || loading) return;

    if (providerStatus && !providerStatus.is_configured) {
      setMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content:
            'LLM provider is not configured. Please go to Settings > AI/LLM Settings to configure your API key.',
          timestamp: new Date(),
        },
      ]);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.post('/ai/generate', {
        context: buildContextPrefix() + text,
        content_type: 'assistant_response',
        pedagogy_style: user?.teachingPhilosophy || 'mixed_approach',
        stream: false,
      });

      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.content,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content:
            'Sorry, I encountered an error. Please check your LLM settings or try again later.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ─── Embedded / Sidebar Layout ─────────────────────────────────────────────

  if (embedded) {
    return (
      <div className='flex flex-col h-full bg-white rounded-lg shadow-md border border-gray-200'>
        {/* Header */}
        <div className='flex items-center justify-between p-3 border-b border-gray-200'>
          <div className='flex items-center gap-2'>
            <Brain className='h-5 w-5 text-purple-600' />
            <span className='font-semibold text-sm'>AI Assistant</span>
          </div>
          {onClose && (
            <button onClick={onClose} className='p-1 rounded hover:bg-gray-100'>
              <X className='h-4 w-4' />
            </button>
          )}
        </div>

        {/* Messages */}
        <div className='flex-1 overflow-y-auto p-3 space-y-3'>
          {messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className='whitespace-pre-wrap'>{msg.content}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className='flex justify-start'>
              <div className='bg-gray-100 px-3 py-2 rounded-lg'>
                <Loader2 className='h-4 w-4 animate-spin text-gray-600' />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        <div className='px-3 py-2 border-t border-gray-100 flex flex-wrap gap-1'>
          {suggestions.slice(0, 3).map((s, i) => (
            <button
              key={i}
              onClick={() => sendMessage(s)}
              className='px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 truncate max-w-full'
              title={s}
            >
              {s.length > 35 ? s.slice(0, 35) + '...' : s}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className='p-3 border-t border-gray-200'>
          <div className='flex gap-2'>
            <input
              type='text'
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder='Ask anything...'
              className='flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className='px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
            >
              <Send className='h-4 w-4' />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─── Full-Page Layout ──────────────────────────────────────────────────────

  return (
    <div className='flex h-[calc(100vh-8rem)]'>
      {/* Chat Area */}
      <div className='flex-1 flex flex-col bg-white rounded-lg shadow-md mr-4'>
        {/* Header */}
        <div className='p-4 border-b border-gray-200'>
          <div className='flex items-center space-x-3'>
            <div className='p-2 bg-purple-100 rounded-lg'>
              <Brain className='h-6 w-6 text-purple-600' />
            </div>
            <div>
              <h2 className='text-lg font-semibold'>AI Teaching Assistant</h2>
              <p className='text-sm text-gray-600'>
                {unitTitle
                  ? `Context: ${unitTitle}`
                  : 'Powered by advanced pedagogy models'}
              </p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className='flex-1 overflow-y-auto p-4 space-y-4'>
          {messages.map(message => (
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
                <p className='whitespace-pre-wrap'>{message.content}</p>
                <p
                  className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className='flex justify-start'>
              <div className='bg-gray-100 px-4 py-3 rounded-lg'>
                <Loader2 className='h-5 w-5 animate-spin text-gray-600' />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className='p-4 border-t border-gray-200'>
          <div className='flex space-x-2'>
            <input
              type='text'
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder='Ask me anything about teaching or course creation...'
              className='flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
            >
              <Send className='h-5 w-5' />
            </button>
          </div>

          {/* Quick Actions */}
          <div className='mt-3 flex flex-wrap gap-2'>
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => sendMessage(suggestion)}
                className='px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200'
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div className='w-80 space-y-4'>
        {/* Quick Actions */}
        <div className='bg-white rounded-lg shadow-md p-4'>
          <h3 className='font-semibold mb-3 flex items-center'>
            <Sparkles className='h-5 w-5 mr-2 text-yellow-500' />
            Quick Actions
          </h3>
          <div className='space-y-2'>
            <button
              onClick={() => sendMessage('Generate a lecture outline')}
              className='w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center'
            >
              <FileText className='h-4 w-4 mr-2 text-blue-600' />
              Generate Lecture
            </button>
            <button
              onClick={() => sendMessage('Create a quiz')}
              className='w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center'
            >
              <PlusCircle className='h-4 w-4 mr-2 text-green-600' />
              Create Quiz
            </button>
            <button
              onClick={() =>
                sendMessage('Improve the quality of existing content')
              }
              className='w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center'
            >
              <Edit className='h-4 w-4 mr-2 text-purple-600' />
              Improve Content
            </button>
            <button
              onClick={() => sendMessage('Give me teaching tips')}
              className='w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center'
            >
              <HelpCircle className='h-4 w-4 mr-2 text-orange-600' />
              Teaching Tips
            </button>
          </div>
        </div>

        {/* Context */}
        <div className='bg-white rounded-lg shadow-md p-4'>
          <h3 className='font-semibold mb-3'>Current Context</h3>
          <div className='space-y-2 text-sm'>
            <div>
              <span className='text-gray-600'>Teaching Style:</span>
              <span className='ml-2 font-medium'>
                {user?.teachingPhilosophy
                  ?.replace(/_/g, ' ')
                  .replace(/\b\w/g, l => l.toUpperCase()) || 'Mixed Approach'}
              </span>
            </div>
            <div>
              <span className='text-gray-600'>Active Unit:</span>
              <span className='ml-2 font-medium'>
                {unitTitle || 'None selected'}
              </span>
            </div>
            {unitULOs && unitULOs.length > 0 && (
              <div>
                <span className='text-gray-600'>ULOs:</span>
                <ul className='mt-1 ml-2 space-y-0.5'>
                  {unitULOs.map(u => (
                    <li key={u.code} className='text-gray-700 text-xs'>
                      <strong>{u.code}</strong>: {u.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <span className='text-gray-600'>Language:</span>
              <span className='ml-2 font-medium'>
                {user?.languagePreference || 'English (AU)'}
              </span>
            </div>
          </div>
        </div>

        {/* LLM Provider Status */}
        <div className='bg-white rounded-lg shadow-md p-4'>
          <h3 className='font-semibold mb-3'>AI Provider Status</h3>
          {providerStatus ? (
            <div className='space-y-2 text-sm'>
              <div className='flex items-center justify-between'>
                <span className='text-gray-600'>Provider:</span>
                <span className='font-medium'>
                  {providerStatus.provider === 'system'
                    ? `System (${providerStatus.actual_provider})`
                    : providerStatus.provider?.toUpperCase()}
                </span>
              </div>
              <div className='flex items-center justify-between'>
                <span className='text-gray-600'>Status:</span>
                <span className='flex items-center'>
                  {providerStatus.is_configured ? (
                    <>
                      <CheckCircle className='h-4 w-4 text-green-500 mr-1' />
                      <span className='text-green-600 font-medium'>
                        Configured
                      </span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className='h-4 w-4 text-yellow-500 mr-1' />
                      <span className='text-yellow-600 font-medium'>
                        Not Configured
                      </span>
                    </>
                  )}
                </span>
              </div>
              {providerStatus.model && (
                <div className='flex items-center justify-between'>
                  <span className='text-gray-600'>Model:</span>
                  <span className='font-medium'>{providerStatus.model}</span>
                </div>
              )}
            </div>
          ) : (
            <div className='text-sm text-gray-500'>Loading...</div>
          )}
        </div>

        {/* Tips */}
        <div className='bg-blue-50 rounded-lg p-4'>
          <h3 className='font-semibold mb-2 text-blue-900'>Pro Tips</h3>
          <ul className='space-y-1 text-sm text-blue-800'>
            <li>Be specific about your requirements</li>
            <li>Mention target audience level</li>
            <li>Specify desired format (slides, text, etc.)</li>
            <li>Ask for examples when needed</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
