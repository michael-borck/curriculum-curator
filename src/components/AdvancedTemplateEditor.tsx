// Advanced Template Editor for Power Users

import React, { useState, useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import type { ContentType, CustomContentType, CustomTemplate, TemplateVariable, ConditionalSection } from '../types/settings';

interface AdvancedTemplateEditorProps {
  isOpen: boolean;
  onClose: () => void;
  editingTemplate?: CustomTemplate | null;
  contentTypes: (ContentType | string)[];
  customContentTypes: CustomContentType[];
  onTemplateUpdated: (templates: CustomTemplate[]) => void;
}

const VARIABLE_TYPES = [
  { value: 'text', label: '📝 Text Input', description: 'Single line text field' },
  { value: 'textarea', label: '📄 Long Text', description: 'Multi-line text area' },
  { value: 'number', label: '🔢 Number', description: 'Numeric input' },
  { value: 'boolean', label: '☑️ Checkbox', description: 'True/false option' },
  { value: 'select', label: '📋 Dropdown', description: 'Select from options' }
];

const TEMPLATE_EXAMPLES = {
  basic: `# {{title}}

**Duration:** {{duration}}
**Complexity:** {{complexity}}
**Audience:** {{audience}}

## Learning Objectives
{{#each learningObjectives}}
- {{this}}
{{/each}}

## Content
{{content}}

{{#if includeAssessment}}
## Assessment
{{assessmentContent}}
{{/if}}`,
  
  advanced: `# {{title}}
{{#if subtitle}}_{{subtitle}}_{{/if}}

**Course:** {{course}}
**Duration:** {{duration}} | **Level:** {{complexity}}
**Target Audience:** {{audience}}

## Overview
{{overview}}

## Learning Objectives
By the end of this {{contentType}}, students will be able to:
{{#each learningObjectives}}
{{@index}}. {{this}}
{{/each}}

{{#if prerequisites}}
## Prerequisites
{{prerequisites}}
{{/if}}

## Content Structure
{{#each sections}}
### {{@index}}. {{title}}
**Time:** {{time}} minutes

{{content}}

{{#if interactive}}
#### Interactive Elements
{{interactiveContent}}
{{/if}}

{{#if hasAssessment}}
#### Quick Check
{{assessmentContent}}
{{/if}}
{{/each}}

{{#if extensionActivities}}
## Extension Activities
{{extensionActivities}}
{{/if}}

{{#if resources}}
## Additional Resources
{{#each resources}}
- [{{title}}]({{url}}) - {{description}}
{{/each}}
{{/if}}`
};

export function AdvancedTemplateEditor({ 
  isOpen, 
  onClose, 
  editingTemplate, 
  contentTypes, 
  customContentTypes, 
  onTemplateUpdated 
}: AdvancedTemplateEditorProps) {
  const { state, actions } = useSettings();
  const [templates, setTemplates] = useState<CustomTemplate[]>([]);
  const [currentTab, setCurrentTab] = useState<'list' | 'editor' | 'preview'>('list');
  const [formData, setFormData] = useState<Partial<CustomTemplate>>({
    name: '',
    description: '',
    contentType: 'Slides',
    category: 'standard',
    template: TEMPLATE_EXAMPLES.basic,
    variables: [],
    conditionalSections: [],
    customPrompts: {},
    metadata: {
      author: '',
      version: '1.0.0',
      tags: [],
      difficulty: 'beginner',
      estimatedTime: 10
    },
    isPublic: false
  });
  const [previewData, setPreviewData] = useState<Record<string, any>>({});
  const [newVariable, setNewVariable] = useState<Partial<TemplateVariable>>({
    name: '',
    type: 'text',
    label: '',
    required: false
  });
  const [showAddVariable, setShowAddVariable] = useState(false);
  const [newCondition, setNewCondition] = useState<Partial<ConditionalSection>>({
    name: '',
    condition: '',
    description: ''
  });
  const [showAddCondition, setShowAddCondition] = useState(false);

  // Load templates from settings
  useEffect(() => {
    if (state.settings?.advanced?.customTemplates) {
      setTemplates(state.settings.advanced.customTemplates);
    }
  }, [state.settings]);

  // Initialize form when editing
  useEffect(() => {
    if (editingTemplate) {
      setFormData(editingTemplate);
      setCurrentTab('editor');
    }
  }, [editingTemplate]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleMetadataChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      metadata: { ...prev.metadata!, [field]: value }
    }));
  };

  const handlePromptChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      customPrompts: { ...prev.customPrompts!, [field]: value }
    }));
  };

  const addVariable = () => {
    if (!newVariable.name || !newVariable.label) return;

    const variable: TemplateVariable = {
      name: newVariable.name!,
      type: newVariable.type!,
      label: newVariable.label!,
      description: newVariable.description,
      required: newVariable.required!,
      defaultValue: newVariable.defaultValue,
      options: newVariable.options,
      validation: newVariable.validation
    };

    setFormData(prev => ({
      ...prev,
      variables: [...(prev.variables || []), variable]
    }));

    setNewVariable({
      name: '',
      type: 'text',
      label: '',
      required: false
    });
    setShowAddVariable(false);
  };

  const removeVariable = (index: number) => {
    setFormData(prev => ({
      ...prev,
      variables: prev.variables?.filter((_, i) => i !== index) || []
    }));
  };

  const addConditionalSection = () => {
    if (!newCondition.name || !newCondition.condition) return;

    const condition: ConditionalSection = {
      id: crypto.randomUUID(),
      name: newCondition.name!,
      condition: newCondition.condition!,
      description: newCondition.description || ''
    };

    setFormData(prev => ({
      ...prev,
      conditionalSections: [...(prev.conditionalSections || []), condition]
    }));

    setNewCondition({
      name: '',
      condition: '',
      description: ''
    });
    setShowAddCondition(false);
  };

  const removeConditionalSection = (id: string) => {
    setFormData(prev => ({
      ...prev,
      conditionalSections: prev.conditionalSections?.filter(c => c.id !== id) || []
    }));
  };

  const saveTemplate = async () => {
    if (!formData.name || !formData.template) return;

    const template: CustomTemplate = {
      id: editingTemplate?.id || crypto.randomUUID(),
      name: formData.name!,
      description: formData.description || '',
      contentType: formData.contentType!,
      category: formData.category!,
      template: formData.template!,
      variables: formData.variables || [],
      conditionalSections: formData.conditionalSections || [],
      customPrompts: formData.customPrompts || {},
      metadata: {
        author: formData.metadata?.author || 'Anonymous',
        version: formData.metadata?.version || '1.0.0',
        tags: formData.metadata?.tags || [],
        difficulty: formData.metadata?.difficulty || 'beginner',
        estimatedTime: formData.metadata?.estimatedTime || 10
      },
      createdAt: editingTemplate?.createdAt || new Date(),
      updatedAt: new Date(),
      isPublic: formData.isPublic || false,
      usageCount: editingTemplate?.usageCount || 0
    };

    const updatedTemplates = editingTemplate
      ? templates.map(t => t.id === editingTemplate.id ? template : t)
      : [...templates, template];

    await saveTemplates(updatedTemplates);
    setCurrentTab('list');
    resetForm();
  };

  const deleteTemplate = async (templateId: string) => {
    if (confirm('Are you sure you want to delete this template?')) {
      const updatedTemplates = templates.filter(t => t.id !== templateId);
      await saveTemplates(updatedTemplates);
    }
  };

  const saveTemplates = async (newTemplates: CustomTemplate[]) => {
    if (state.settings) {
      const updatedSettings = {
        ...state.settings,
        advanced: {
          ...state.settings.advanced,
          customTemplates: newTemplates
        }
      };
      await actions.saveSettings(updatedSettings);
      setTemplates(newTemplates);
      onTemplateUpdated(newTemplates);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      contentType: 'Slides',
      category: 'standard',
      template: TEMPLATE_EXAMPLES.basic,
      variables: [],
      conditionalSections: [],
      customPrompts: {},
      metadata: {
        author: '',
        version: '1.0.0',
        tags: [],
        difficulty: 'beginner',
        estimatedTime: 10
      },
      isPublic: false
    });
    setPreviewData({});
  };

  const generatePreview = () => {
    // Simple template preview - in a real implementation, this would use a proper template engine
    let preview = formData.template || '';
    
    // Replace simple variables
    Object.entries(previewData).forEach(([key, value]) => {
      const regex = new RegExp(`{{${key}}}`, 'g');
      preview = preview.replace(regex, String(value));
    });

    // Handle simple conditionals (basic implementation)
    preview = preview.replace(/{{#if\s+(\w+)}}([\s\S]*?){{\/if}}/g, (match, condition, content) => {
      return previewData[condition] ? content : '';
    });

    // Handle simple each loops (basic implementation)
    preview = preview.replace(/{{#each\s+(\w+)}}([\s\S]*?){{\/each}}/g, (match, arrayName, content) => {
      const array = previewData[arrayName];
      if (Array.isArray(array)) {
        return array.map(item => 
          content.replace(/{{this}}/g, String(item))
                 .replace(/{{@index}}/g, String(array.indexOf(item) + 1))
        ).join('\n');
      }
      return '';
    });

    return preview;
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        maxWidth: '1200px',
        width: '95%',
        maxHeight: '95%',
        overflow: 'hidden',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1e293b' }}>
            🔧 Advanced Template Editor
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#64748b'
            }}
          >
            ×
          </button>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#f8fafc'
        }}>
          {[
            { id: 'list', label: '📋 Templates', icon: '📋' },
            { id: 'editor', label: '✏️ Editor', icon: '✏️' },
            { id: 'preview', label: '👁️ Preview', icon: '👁️' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id as any)}
              style={{
                flex: 1,
                padding: '16px 24px',
                border: 'none',
                backgroundColor: currentTab === tab.id ? 'white' : 'transparent',
                color: currentTab === tab.id ? '#3b82f6' : '#64748b',
                borderBottom: currentTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '500'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
          {currentTab === 'list' && (
            <div>
              {/* Create Button */}
              <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                  Custom Templates
                </h3>
                <button
                  onClick={() => {
                    resetForm();
                    setCurrentTab('editor');
                  }}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '16px',
                    fontWeight: '500',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  ➕ Create New Template
                </button>
              </div>

              {/* Templates List */}
              {templates.length === 0 ? (
                <div style={{
                  padding: '40px',
                  textAlign: 'center',
                  color: '#64748b',
                  backgroundColor: '#f8fafc',
                  borderRadius: '12px',
                  border: '2px dashed #cbd5e1'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>📝</div>
                  <h3 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>No Custom Templates</h3>
                  <p style={{ margin: 0, fontSize: '14px' }}>
                    Create advanced templates with variables, conditionals, and custom prompts for precise content generation.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '16px' }}>
                  {templates.map(template => (
                    <div
                      key={template.id}
                      style={{
                        padding: '20px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '12px',
                        backgroundColor: 'white'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ flex: 1 }}>
                          <h4 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', margin: '0 0 8px 0' }}>
                            {template.name}
                          </h4>
                          <p style={{ fontSize: '14px', color: '#64748b', margin: '0 0 12px 0' }}>
                            {template.description}
                          </p>
                          
                          <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#64748b' }}>
                            <span><strong>Type:</strong> {template.contentType}</span>
                            <span><strong>Variables:</strong> {template.variables.length}</span>
                            <span><strong>Difficulty:</strong> {template.metadata.difficulty}</span>
                            <span><strong>Used:</strong> {template.usageCount} times</span>
                          </div>
                        </div>
                        
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => {
                              setFormData(template);
                              setCurrentTab('editor');
                            }}
                            style={{
                              padding: '8px 12px',
                              border: '1px solid #3b82f6',
                              backgroundColor: '#dbeafe',
                              color: '#1e40af',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '14px'
                            }}
                          >
                            ✏️ Edit
                          </button>
                          <button
                            onClick={() => deleteTemplate(template.id)}
                            style={{
                              padding: '8px 12px',
                              border: '1px solid #dc2626',
                              backgroundColor: '#fef2f2',
                              color: '#dc2626',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '14px'
                            }}
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {currentTab === 'editor' && (
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '600', margin: '0 0 24px 0', color: '#1e293b' }}>
                Template Editor
              </h3>

              <div style={{ display: 'grid', gap: '24px' }}>
                {/* Basic Info */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                      Template Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name || ''}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="e.g., Advanced Lab Report Template"
                      style={{
                        width: '100%',
                        padding: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '8px',
                        fontSize: '14px'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                      Content Type
                    </label>
                    <select
                      value={formData.contentType || ''}
                      onChange={(e) => handleInputChange('contentType', e.target.value)}
                      style={{
                        width: '100%',
                        padding: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '8px',
                        fontSize: '14px',
                        backgroundColor: 'white'
                      }}
                    >
                      {contentTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                      {customContentTypes.map(type => (
                        <option key={type.id} value={type.name}>{type.name} (Custom)</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                    Description
                  </label>
                  <textarea
                    value={formData.description || ''}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Describe what this template is for and how to use it..."
                    rows={3}
                    style={{
                      width: '100%',
                      padding: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '14px',
                      resize: 'vertical'
                    }}
                  />
                </div>

                {/* Template Content */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ fontWeight: '500', color: '#374151' }}>
                      Template Content *
                    </label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => handleInputChange('template', TEMPLATE_EXAMPLES.basic)}
                        style={{
                          padding: '4px 8px',
                          border: '1px solid #d1d5db',
                          backgroundColor: '#f9fafb',
                          color: '#374151',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Load Basic Example
                      </button>
                      <button
                        onClick={() => handleInputChange('template', TEMPLATE_EXAMPLES.advanced)}
                        style={{
                          padding: '4px 8px',
                          border: '1px solid #d1d5db',
                          backgroundColor: '#f9fafb',
                          color: '#374151',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Load Advanced Example
                      </button>
                    </div>
                  </div>
                  <textarea
                    value={formData.template || ''}
                    onChange={(e) => handleInputChange('template', e.target.value)}
                    placeholder="Enter your template content with {{variables}} and {{#if conditions}}...{{/if}}"
                    rows={12}
                    style={{
                      width: '100%',
                      padding: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '14px',
                      fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                      resize: 'vertical'
                    }}
                  />
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: '8px 0 0 0' }}>
                    Use Handlebars syntax: <code>{{`{{variable}}`}}</code> for values, <code>{{`{{#if condition}}...{{/if}}`}}</code> for conditionals, <code>{{`{{#each array}}...{{/each}}`}}</code> for loops
                  </p>
                </div>

                {/* Variables Section */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                      Template Variables
                    </h4>
                    <button
                      onClick={() => setShowAddVariable(true)}
                      style={{
                        padding: '8px 12px',
                        backgroundColor: '#059669',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px'
                      }}
                    >
                      ➕ Add Variable
                    </button>
                  </div>

                  {formData.variables && formData.variables.length > 0 ? (
                    <div style={{ display: 'grid', gap: '12px' }}>
                      {formData.variables.map((variable, index) => (
                        <div
                          key={index}
                          style={{
                            padding: '16px',
                            backgroundColor: '#f8fafc',
                            borderRadius: '8px',
                            border: '1px solid #e2e8f0'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                              <h5 style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b', margin: '0 0 4px 0' }}>
                                {{`{{${variable.name}}}`}} - {variable.label}
                              </h5>
                              <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 8px 0' }}>
                                Type: {variable.type} | Required: {variable.required ? 'Yes' : 'No'}
                              </p>
                              {variable.description && (
                                <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                                  {variable.description}
                                </p>
                              )}
                            </div>
                            <button
                              onClick={() => removeVariable(index)}
                              style={{
                                padding: '4px 8px',
                                border: '1px solid #dc2626',
                                backgroundColor: '#fef2f2',
                                color: '#dc2626',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '12px'
                              }}
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ fontSize: '14px', color: '#6b7280', fontStyle: 'italic' }}>
                      No variables defined. Add variables to make your template dynamic.
                    </p>
                  )}

                  {/* Add Variable Modal */}
                  {showAddVariable && (
                    <div style={{
                      position: 'fixed',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      backgroundColor: 'rgba(0, 0, 0, 0.5)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      zIndex: 1001
                    }}>
                      <div style={{
                        backgroundColor: 'white',
                        borderRadius: '12px',
                        padding: '24px',
                        maxWidth: '500px',
                        width: '90%',
                        maxHeight: '80vh',
                        overflow: 'auto'
                      }}>
                        <h4 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', margin: '0 0 16px 0' }}>
                          Add Template Variable
                        </h4>
                        
                        <div style={{ display: 'grid', gap: '16px' }}>
                          <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                              Variable Name *
                            </label>
                            <input
                              type="text"
                              value={newVariable.name || ''}
                              onChange={(e) => setNewVariable(prev => ({ ...prev, name: e.target.value }))}
                              placeholder="e.g., title, complexity, duration"
                              style={{
                                width: '100%',
                                padding: '8px 12px',
                                border: '1px solid #d1d5db',
                                borderRadius: '6px',
                                fontSize: '14px'
                              }}
                            />
                          </div>

                          <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                              Display Label *
                            </label>
                            <input
                              type="text"
                              value={newVariable.label || ''}
                              onChange={(e) => setNewVariable(prev => ({ ...prev, label: e.target.value }))}
                              placeholder="e.g., Course Title, Complexity Level"
                              style={{
                                width: '100%',
                                padding: '8px 12px',
                                border: '1px solid #d1d5db',
                                borderRadius: '6px',
                                fontSize: '14px'
                              }}
                            />
                          </div>

                          <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                              Variable Type
                            </label>
                            <select
                              value={newVariable.type || 'text'}
                              onChange={(e) => setNewVariable(prev => ({ ...prev, type: e.target.value as any }))}
                              style={{
                                width: '100%',
                                padding: '8px 12px',
                                border: '1px solid #d1d5db',
                                borderRadius: '6px',
                                fontSize: '14px',
                                backgroundColor: 'white'
                              }}
                            >
                              {VARIABLE_TYPES.map(type => (
                                <option key={type.value} value={type.value}>
                                  {type.label} - {type.description}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                              Description
                            </label>
                            <textarea
                              value={newVariable.description || ''}
                              onChange={(e) => setNewVariable(prev => ({ ...prev, description: e.target.value }))}
                              placeholder="Optional description or instructions for this variable"
                              rows={2}
                              style={{
                                width: '100%',
                                padding: '8px 12px',
                                border: '1px solid #d1d5db',
                                borderRadius: '6px',
                                fontSize: '14px',
                                resize: 'vertical'
                              }}
                            />
                          </div>

                          <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                              <input
                                type="checkbox"
                                checked={newVariable.required || false}
                                onChange={(e) => setNewVariable(prev => ({ ...prev, required: e.target.checked }))}
                                style={{ width: '16px', height: '16px' }}
                              />
                              <span style={{ fontSize: '14px', color: '#374151' }}>
                                Required field
                              </span>
                            </label>
                          </div>

                          {newVariable.type === 'select' && (
                            <div>
                              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                                Options (one per line)
                              </label>
                              <textarea
                                value={newVariable.options?.join('\n') || ''}
                                onChange={(e) => setNewVariable(prev => ({ 
                                  ...prev, 
                                  options: e.target.value.split('\n').filter(o => o.trim()) 
                                }))}
                                placeholder="Option 1&#10;Option 2&#10;Option 3"
                                rows={4}
                                style={{
                                  width: '100%',
                                  padding: '8px 12px',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '6px',
                                  fontSize: '14px',
                                  resize: 'vertical'
                                }}
                              />
                            </div>
                          )}
                        </div>

                        <div style={{ 
                          marginTop: '24px',
                          display: 'flex',
                          gap: '12px',
                          justifyContent: 'flex-end'
                        }}>
                          <button
                            onClick={() => {
                              setShowAddVariable(false);
                              setNewVariable({
                                name: '',
                                type: 'text',
                                label: '',
                                required: false
                              });
                            }}
                            style={{
                              padding: '8px 16px',
                              border: '1px solid #d1d5db',
                              backgroundColor: '#f3f4f6',
                              color: '#374151',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '14px'
                            }}
                          >
                            Cancel
                          </button>
                          <button
                            onClick={addVariable}
                            disabled={!newVariable.name || !newVariable.label}
                            style={{
                              padding: '8px 16px',
                              border: 'none',
                              backgroundColor: newVariable.name && newVariable.label ? '#059669' : '#9ca3af',
                              color: 'white',
                              borderRadius: '6px',
                              cursor: newVariable.name && newVariable.label ? 'pointer' : 'not-allowed',
                              fontSize: '14px'
                            }}
                          >
                            Add Variable
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Save Actions */}
                <div style={{ 
                  marginTop: '24px',
                  paddingTop: '24px',
                  borderTop: '1px solid #e5e7eb',
                  display: 'flex',
                  gap: '12px',
                  justifyContent: 'flex-end'
                }}>
                  <button
                    onClick={() => {
                      resetForm();
                      setCurrentTab('list');
                    }}
                    style={{
                      padding: '12px 24px',
                      border: '1px solid #d1d5db',
                      backgroundColor: '#f3f4f6',
                      color: '#374151',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontSize: '16px'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveTemplate}
                    disabled={!formData.name || !formData.template}
                    style={{
                      padding: '12px 24px',
                      border: 'none',
                      backgroundColor: formData.name && formData.template ? '#3b82f6' : '#9ca3af',
                      color: 'white',
                      borderRadius: '8px',
                      cursor: formData.name && formData.template ? 'pointer' : 'not-allowed',
                      fontSize: '16px',
                      fontWeight: '500'
                    }}
                  >
                    Save Template
                  </button>
                </div>
              </div>
            </div>
          )}

          {currentTab === 'preview' && (
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '600', margin: '0 0 24px 0', color: '#1e293b' }}>
                Template Preview
              </h3>
              
              {formData.variables && formData.variables.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                  {/* Preview Data Input */}
                  <div>
                    <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', margin: '0 0 16px 0' }}>
                      Test Data
                    </h4>
                    <div style={{ display: 'grid', gap: '16px' }}>
                      {formData.variables.map((variable, index) => (
                        <div key={index}>
                          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                            {variable.label}
                            {variable.required && <span style={{ color: '#dc2626' }}> *</span>}
                          </label>
                          {variable.type === 'textarea' ? (
                            <textarea
                              value={previewData[variable.name] || ''}
                              onChange={(e) => setPreviewData(prev => ({ ...prev, [variable.name]: e.target.value }))}
                              placeholder={variable.description}
                              rows={3}
                              style={{
                                width: '100%',
                                padding: '8px 12px',
                                border: '1px solid #d1d5db',
                                borderRadius: '6px',
                                fontSize: '14px',
                                resize: 'vertical'
                              }}
                            />
                          ) : variable.type === 'select' ? (
                            <select
                              value={previewData[variable.name] || ''}
                              onChange={(e) => setPreviewData(prev => ({ ...prev, [variable.name]: e.target.value }))}
                              style={{
                                width: '100%',
                                padding: '8px 12px',
                                border: '1px solid #d1d5db',
                                borderRadius: '6px',
                                fontSize: '14px',
                                backgroundColor: 'white'
                              }}
                            >
                              <option value="">Select {variable.label}</option>
                              {variable.options?.map(option => (
                                <option key={option} value={option}>{option}</option>
                              ))}
                            </select>
                          ) : variable.type === 'boolean' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                              <input
                                type="checkbox"
                                checked={previewData[variable.name] || false}
                                onChange={(e) => setPreviewData(prev => ({ ...prev, [variable.name]: e.target.checked }))}
                                style={{ width: '16px', height: '16px' }}
                              />
                              <span style={{ fontSize: '14px', color: '#374151' }}>
                                {variable.description || 'Enable this option'}
                              </span>
                            </label>
                          ) : (
                            <input
                              type={variable.type === 'number' ? 'number' : 'text'}
                              value={previewData[variable.name] || ''}
                              onChange={(e) => setPreviewData(prev => ({ 
                                ...prev, 
                                [variable.name]: variable.type === 'number' ? Number(e.target.value) : e.target.value 
                              }))}
                              placeholder={variable.description}
                              style={{
                                width: '100%',
                                padding: '8px 12px',
                                border: '1px solid #d1d5db',
                                borderRadius: '6px',
                                fontSize: '14px'
                              }}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Preview Output */}
                  <div>
                    <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', margin: '0 0 16px 0' }}>
                      Generated Content
                    </h4>
                    <div style={{
                      padding: '16px',
                      backgroundColor: '#f8fafc',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      fontFamily: 'Georgia, serif',
                      lineHeight: '1.6',
                      minHeight: '400px',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {generatePreview()}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{
                  padding: '40px',
                  textAlign: 'center',
                  color: '#64748b',
                  backgroundColor: '#f8fafc',
                  borderRadius: '12px',
                  border: '2px dashed #cbd5e1'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>👁️</div>
                  <h3 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>No Variables to Preview</h3>
                  <p style={{ margin: 0, fontSize: '14px' }}>
                    Add variables to your template to see a live preview with test data.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}