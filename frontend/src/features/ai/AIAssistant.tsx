import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Brain,
  Send,
  Loader2,
  Sparkles,
  FileText,
  AlertCircle,
  CheckCircle,
  X,
  ChevronDown,
  ChevronRight,
  Check,
} from 'lucide-react';
import api from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import { useWorkingContextStore } from '../../stores/workingContextStore';
import {
  promptTemplateApi,
  type PromptTemplate,
  type PromptTemplateDetail,
  type TemplateVariable,
} from '../../services/promptTemplateApi';
import { materialsApi } from '../../services/unitStructureApi';
import type { MaterialResponse } from '../../types/unitStructure';
import SaveToUnitButton from './SaveToUnitButton';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isError?: boolean | undefined;
}

interface AIAssistantProps {
  /** When provided, unit context is prepended to every prompt. */
  unitId?: string;
  unitTitle?: string;
  unitULOs?: Array<{ code: string; description: string }>;
  /** Learning Design ID — when set, the backend injects design context. */
  designId?: string | undefined;
  /** Render as a compact sidebar panel instead of full page. */
  embedded?: boolean;
  onClose?: () => void;
}

function renderTemplate(content: string, vars: Record<string, string>): string {
  return content.replace(
    /\{\{\s*(\w+)\s*\}\}/g,
    (_, key: string) => vars[key] ?? `[${key}]`
  );
}

const AIAssistant = ({
  unitId,
  unitTitle,
  unitULOs,
  designId,
  embedded = false,
  onClose,
}: AIAssistantProps) => {
  const { user } = useAuthStore();
  const ctx = useWorkingContextStore();
  const effectiveUnitId = unitId ?? ctx.activeUnitId ?? undefined;
  const effectiveUnitTitle = unitTitle ?? ctx.activeUnitTitle ?? undefined;
  const effectiveUnitULOs =
    unitULOs ?? (ctx.activeULOs.length > 0 ? ctx.activeULOs : undefined);
  const effectiveDesignId = designId ?? ctx.activeDesignId ?? undefined;
  const effectiveWeek = ctx.activeWeek;

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        (unitTitle ?? ctx.activeUnitTitle)
          ? `Hi! I'm your AI teaching assistant for **${unitTitle ?? ctx.activeUnitTitle}**. I can generate lecture content, quizzes, discussion questions, and more — all aligned to this unit's learning outcomes. How can I help?`
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

  // DB-driven prompt templates
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [activeTemplate, setActiveTemplate] =
    useState<PromptTemplateDetail | null>(null);
  const [templateVars, setTemplateVars] = useState<Record<string, string>>({});

  // Source material selection
  const [weekMaterials, setWeekMaterials] = useState<MaterialResponse[]>([]);
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [showSources, setShowSources] = useState(false);

  // Load prompt templates
  useEffect(() => {
    promptTemplateApi
      .list()
      .then(setTemplates)
      .catch(() => {
        /* non-critical */
      });
  }, []);

  // Load week materials for source selection
  useEffect(() => {
    if (!effectiveUnitId || !effectiveWeek) {
      setWeekMaterials([]);
      setSelectedSourceIds([]);
      return;
    }
    materialsApi
      .getMaterialsByWeek(effectiveUnitId, effectiveWeek)
      .then(data => setWeekMaterials(data.materials))
      .catch(() => setWeekMaterials([]));
  }, [effectiveUnitId, effectiveWeek]);

  // Build unit-context prefix for prompts
  const buildContextPrefix = useCallback(() => {
    if (!effectiveUnitTitle) return '';
    let prefix = `[Unit Context] Unit: "${effectiveUnitTitle}"`;
    if (effectiveWeek) {
      prefix += ` | Current Week: ${effectiveWeek}`;
    }
    if (effectiveUnitULOs?.length) {
      prefix +=
        '\nLearning Outcomes:\n' +
        effectiveUnitULOs.map(u => `  ${u.code}: ${u.description}`).join('\n');
    }
    prefix += '\n\n';
    return prefix;
  }, [effectiveUnitTitle, effectiveWeek, effectiveUnitULOs]);

  // Fallback suggestions when no templates loaded
  const fallbackSuggestions = effectiveUnitTitle
    ? [
        `Generate a lecture outline for ${effectiveUnitTitle}`,
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
          isError: true,
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
    setActiveTemplate(null);
    setLoading(true);

    try {
      const response = await api.post('/ai/generate', {
        context: buildContextPrefix() + text,
        contentType: 'assistant_response',
        pedagogyStyle: user?.teachingPhilosophy || 'mixed_approach',
        stream: false,
        unitId: effectiveUnitId,
        designId: effectiveDesignId,
        weekNumber: effectiveWeek ?? undefined,
        sourceMaterialIds:
          selectedSourceIds.length > 0 ? selectedSourceIds : undefined,
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
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateClick = async (template: PromptTemplate) => {
    const hasVars =
      template.variables && template.variables.some(v => !v.default);

    if (!hasVars) {
      // No unfilled variables — fetch full template and send immediately
      try {
        const full = await promptTemplateApi.get(template.id);
        const defaults: Record<string, string> = {};
        for (const v of full.variables ?? []) {
          defaults[v.name] = v.default ?? '';
        }
        const rendered = renderTemplate(full.templateContent, defaults);
        promptTemplateApi.incrementUsage(template.id).catch(() => {});
        sendMessage(rendered);
      } catch {
        /* fallback: just send the name */
        sendMessage(template.name);
      }
    } else {
      // Has variables — show inline form
      try {
        const full = await promptTemplateApi.get(template.id);
        setActiveTemplate(full);
        // Pre-fill from context where possible
        const prefilled: Record<string, string> = {};
        for (const v of full.variables ?? []) {
          if (v.name === 'unit_level') {
            prefilled[v.name] = v.default ?? 'undergraduate';
          } else if (v.name === 'unit_code' && ctx.activeUnitCode) {
            prefilled[v.name] = ctx.activeUnitCode;
          } else {
            prefilled[v.name] = v.default ?? '';
          }
        }
        setTemplateVars(prefilled);
      } catch {
        /* non-critical */
      }
    }
  };

  const handleTemplateSubmit = () => {
    if (!activeTemplate) return;
    const rendered = renderTemplate(
      activeTemplate.templateContent,
      templateVars
    );
    promptTemplateApi.incrementUsage(activeTemplate.id).catch(() => {});
    setActiveTemplate(null);
    setTemplateVars({});
    sendMessage(rendered);
  };

  const toggleSource = (id: string) => {
    setSelectedSourceIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  // ─── Template Variable Form ───────────────────────────────────────────────

  const renderTemplateForm = () => {
    if (!activeTemplate) return null;

    return (
      <div className='mx-3 mb-2 p-3 bg-purple-50 border border-purple-200 rounded-lg'>
        <div className='flex items-center justify-between mb-2'>
          <span className='text-sm font-medium text-purple-900'>
            {activeTemplate.name}
          </span>
          <button
            onClick={() => setActiveTemplate(null)}
            className='p-0.5 text-purple-400 hover:text-purple-600'
          >
            <X className='h-3.5 w-3.5' />
          </button>
        </div>
        <div className='space-y-2'>
          {(activeTemplate.variables ?? []).map((v: TemplateVariable) => (
            <div key={v.name}>
              <label className='block text-xs font-medium text-purple-700 mb-0.5'>
                {v.label}
              </label>
              {v.name === 'content' ||
              v.name === 'rubric_content' ||
              v.name === 'submission_content' ? (
                <textarea
                  value={templateVars[v.name] ?? ''}
                  onChange={e =>
                    setTemplateVars(prev => ({
                      ...prev,
                      [v.name]: e.target.value,
                    }))
                  }
                  rows={3}
                  className='w-full px-2 py-1 text-sm border border-purple-200 rounded focus:ring-1 focus:ring-purple-400 resize-y'
                  placeholder={v.label}
                />
              ) : (
                <input
                  type='text'
                  value={templateVars[v.name] ?? ''}
                  onChange={e =>
                    setTemplateVars(prev => ({
                      ...prev,
                      [v.name]: e.target.value,
                    }))
                  }
                  className='w-full px-2 py-1 text-sm border border-purple-200 rounded focus:ring-1 focus:ring-purple-400'
                  placeholder={v.label}
                />
              )}
            </div>
          ))}
        </div>
        <button
          onClick={handleTemplateSubmit}
          className='mt-2 w-full px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center justify-center gap-1'
        >
          <Send className='h-3.5 w-3.5' />
          Generate
        </button>
      </div>
    );
  };

  // ─── Source Material Picker ─────────────────────────────────────────────

  const renderSourcePicker = () => {
    if (!effectiveUnitId || !effectiveWeek || weekMaterials.length === 0)
      return null;

    return (
      <div className='mx-3 mb-2'>
        <button
          onClick={() => setShowSources(!showSources)}
          className='flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700'
        >
          {showSources ? (
            <ChevronDown className='h-3 w-3' />
          ) : (
            <ChevronRight className='h-3 w-3' />
          )}
          Source Materials
          {selectedSourceIds.length > 0 && (
            <span className='ml-1 px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs'>
              {selectedSourceIds.length}
            </span>
          )}
        </button>
        {showSources && (
          <div className='mt-1 space-y-1 max-h-32 overflow-y-auto'>
            {weekMaterials.map(m => (
              <label
                key={m.id}
                className='flex items-center gap-2 px-2 py-1 text-xs rounded hover:bg-gray-50 cursor-pointer'
              >
                <div
                  className={`w-3.5 h-3.5 rounded border flex items-center justify-center ${
                    selectedSourceIds.includes(m.id)
                      ? 'bg-purple-600 border-purple-600'
                      : 'border-gray-300'
                  }`}
                  onClick={() => toggleSource(m.id)}
                >
                  {selectedSourceIds.includes(m.id) && (
                    <Check className='h-2.5 w-2.5 text-white' />
                  )}
                </div>
                <span
                  className='text-gray-700 truncate'
                  onClick={() => toggleSource(m.id)}
                >
                  {m.title}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>
    );
  };

  // ─── Quick Actions (DB-driven or fallback) ──────────────────────────────

  const renderQuickActions = (limit: number, compact: boolean) => {
    if (templates.length > 0) {
      return templates.slice(0, limit).map(t => (
        <button
          key={t.id}
          onClick={() => handleTemplateClick(t)}
          className={
            compact
              ? 'px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 truncate max-w-full'
              : 'px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200'
          }
          title={t.description ?? t.name}
        >
          {compact && t.name.length > 30 ? t.name.slice(0, 30) + '...' : t.name}
        </button>
      ));
    }

    // Fallback hardcoded suggestions
    const items = fallbackSuggestions.slice(0, limit);
    return items.map((s, i) => (
      <button
        key={i}
        onClick={() => sendMessage(s)}
        className={
          compact
            ? 'px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 truncate max-w-full'
            : 'px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200'
        }
        title={s}
      >
        {compact && s.length > 30 ? s.slice(0, 30) + '...' : s}
      </button>
    ));
  };

  // ─── Sidebar Quick Actions (DB-driven) ──────────────────────────────────

  const renderSidebarActions = () => {
    if (templates.length > 0) {
      return templates.slice(0, 6).map(t => (
        <button
          key={t.id}
          onClick={() => handleTemplateClick(t)}
          className='w-full text-left px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center'
        >
          <FileText className='h-4 w-4 mr-2 text-purple-600 shrink-0' />
          <span className='truncate'>{t.name}</span>
        </button>
      ));
    }

    // Fallback
    return (
      <>
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
          <FileText className='h-4 w-4 mr-2 text-green-600' />
          Create Quiz
        </button>
      </>
    );
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
            {effectiveWeek && (
              <span className='text-xs text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded'>
                Week {effectiveWeek}
              </span>
            )}
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
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
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
              {msg.role === 'assistant' && msg.id !== '1' && !msg.isError && (
                <SaveToUnitButton
                  messageContent={msg.content}
                  unitId={effectiveUnitId}
                  unitTitle={effectiveUnitTitle}
                />
              )}
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

        {/* Template Variable Form */}
        {renderTemplateForm()}

        {/* Source Material Picker */}
        {renderSourcePicker()}

        {/* Quick Actions */}
        <div className='px-3 py-2 border-t border-gray-100 flex flex-wrap gap-1'>
          {renderQuickActions(3, true)}
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
                {effectiveUnitTitle
                  ? `Context: ${effectiveUnitTitle}${effectiveWeek ? ` — Week ${effectiveWeek}` : ''}`
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
              className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}
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
              {message.role === 'assistant' &&
                message.id !== '1' &&
                !message.isError && (
                  <SaveToUnitButton
                    messageContent={message.content}
                    unitId={effectiveUnitId}
                    unitTitle={effectiveUnitTitle}
                  />
                )}
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

        {/* Template Variable Form (full-page) */}
        {activeTemplate && (
          <div className='mx-4 mb-2 p-4 bg-purple-50 border border-purple-200 rounded-lg'>
            <div className='flex items-center justify-between mb-3'>
              <span className='font-medium text-purple-900'>
                {activeTemplate.name}
              </span>
              <button
                onClick={() => setActiveTemplate(null)}
                className='p-1 text-purple-400 hover:text-purple-600'
              >
                <X className='h-4 w-4' />
              </button>
            </div>
            <div className='grid grid-cols-2 gap-3'>
              {(activeTemplate.variables ?? []).map((v: TemplateVariable) => (
                <div
                  key={v.name}
                  className={
                    v.name === 'content' ||
                    v.name === 'rubric_content' ||
                    v.name === 'submission_content'
                      ? 'col-span-2'
                      : ''
                  }
                >
                  <label className='block text-xs font-medium text-purple-700 mb-1'>
                    {v.label}
                  </label>
                  {v.name === 'content' ||
                  v.name === 'rubric_content' ||
                  v.name === 'submission_content' ? (
                    <textarea
                      value={templateVars[v.name] ?? ''}
                      onChange={e =>
                        setTemplateVars(prev => ({
                          ...prev,
                          [v.name]: e.target.value,
                        }))
                      }
                      rows={4}
                      className='w-full px-3 py-2 text-sm border border-purple-200 rounded-lg focus:ring-1 focus:ring-purple-400 resize-y'
                      placeholder={v.label}
                    />
                  ) : (
                    <input
                      type='text'
                      value={templateVars[v.name] ?? ''}
                      onChange={e =>
                        setTemplateVars(prev => ({
                          ...prev,
                          [v.name]: e.target.value,
                        }))
                      }
                      className='w-full px-3 py-2 text-sm border border-purple-200 rounded-lg focus:ring-1 focus:ring-purple-400'
                      placeholder={v.label}
                    />
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={handleTemplateSubmit}
              className='mt-3 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-1'
            >
              <Send className='h-4 w-4' />
              Generate
            </button>
          </div>
        )}

        {/* Source Material Picker (full-page) */}
        {effectiveUnitId &&
          effectiveWeek &&
          weekMaterials.length > 0 &&
          !embedded && (
            <div className='mx-4 mb-2'>
              <button
                onClick={() => setShowSources(!showSources)}
                className='flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700'
              >
                {showSources ? (
                  <ChevronDown className='h-4 w-4' />
                ) : (
                  <ChevronRight className='h-4 w-4' />
                )}
                Source Materials (Week {effectiveWeek})
                {selectedSourceIds.length > 0 && (
                  <span className='ml-1 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs'>
                    {selectedSourceIds.length} selected
                  </span>
                )}
              </button>
              {showSources && (
                <div className='mt-2 space-y-1 max-h-40 overflow-y-auto pl-6'>
                  {weekMaterials.map(m => (
                    <label
                      key={m.id}
                      className='flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-gray-50 cursor-pointer'
                    >
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center ${
                          selectedSourceIds.includes(m.id)
                            ? 'bg-purple-600 border-purple-600'
                            : 'border-gray-300'
                        }`}
                        onClick={() => toggleSource(m.id)}
                      >
                        {selectedSourceIds.includes(m.id) && (
                          <Check className='h-3 w-3 text-white' />
                        )}
                      </div>
                      <span
                        className='text-gray-700'
                        onClick={() => toggleSource(m.id)}
                      >
                        {m.title}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}

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
            {renderQuickActions(4, false)}
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
          <div className='space-y-2'>{renderSidebarActions()}</div>
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
                {effectiveUnitTitle || 'None selected'}
              </span>
            </div>
            {effectiveWeek && (
              <div>
                <span className='text-gray-600'>Active Week:</span>
                <span className='ml-2 font-medium'>{effectiveWeek}</span>
              </div>
            )}
            {effectiveUnitULOs && effectiveUnitULOs.length > 0 && (
              <div>
                <span className='text-gray-600'>ULOs:</span>
                <ul className='mt-1 ml-2 space-y-0.5'>
                  {effectiveUnitULOs.map(u => (
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
