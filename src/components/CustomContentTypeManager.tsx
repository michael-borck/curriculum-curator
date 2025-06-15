// Custom Content Type Management Component

import React, { useState, useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import type { AIContentOptions, CustomContentType } from '../types/settings';

interface CustomContentTypeManagerProps {
  isOpen: boolean;
  onClose: () => void;
  onContentTypesUpdated: (types: CustomContentType[]) => void;
}

const CATEGORY_OPTIONS = [
  { value: 'assessment', label: '📊 Assessment', description: 'Tests, quizzes, evaluations' },
  { value: 'instructional', label: '📚 Instructional', description: 'Lectures, presentations, guides' },
  { value: 'activity', label: '🎯 Activity', description: 'Interactive exercises, labs, projects' },
  { value: 'reference', label: '📖 Reference', description: 'Handouts, cheat sheets, glossaries' },
  { value: 'other', label: '🔧 Other', description: 'Custom or specialized content' }
] as const;

const ICON_OPTIONS = [
  '📄', '📝', '📊', '📋', '📚', '🎯', '🔬', '💡', '🎨', '🔧',
  '📐', '🧮', '📈', '📉', '🗂️', '📑', '📓', '📔', '📕', '📗',
  '📘', '📙', '📒', '🎪', '🎭', '🎨', '🎼', '🎵', '🎶', '🎤'
];

export function CustomContentTypeManager({ isOpen, onClose, onContentTypesUpdated }: CustomContentTypeManagerProps) {
  const { state, actions } = useSettings();
  const [customTypes, setCustomTypes] = useState<CustomContentType[]>([]);
  const [editingType, setEditingType] = useState<CustomContentType | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    icon: '📄',
    category: 'other' as const,
    templateHints: [''],
    defaultAIOptions: {
      enableInteractionPrompts: false,
      includeBrainstormingActivities: false,
      suggestAITools: false,
      createResistantAlternatives: false,
      addLiteracyComponents: false
    } as AIContentOptions
  });

  // Load custom content types from settings
  useEffect(() => {
    if (state.settings?.advanced?.customContentTypes) {
      setCustomTypes(state.settings.advanced.customContentTypes);
    }
  }, [state.settings]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleTemplateHintChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      templateHints: prev.templateHints.map((hint, i) => i === index ? value : hint)
    }));
  };

  const addTemplateHint = () => {
    setFormData(prev => ({
      ...prev,
      templateHints: [...prev.templateHints, '']
    }));
  };

  const removeTemplateHint = (index: number) => {
    if (formData.templateHints.length > 1) {
      setFormData(prev => ({
        ...prev,
        templateHints: prev.templateHints.filter((_, i) => i !== index)
      }));
    }
  };

  const handleAIOptionChange = (option: keyof AIContentOptions, value: boolean) => {
    setFormData(prev => ({
      ...prev,
      defaultAIOptions: {
        ...prev.defaultAIOptions,
        [option]: value
      }
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      icon: '📄',
      category: 'other',
      templateHints: [''],
      defaultAIOptions: {
        enableInteractionPrompts: false,
        includeBrainstormingActivities: false,
        suggestAITools: false,
        createResistantAlternatives: false,
        addLiteracyComponents: false
      }
    });
    setEditingType(null);
    setShowCreateForm(false);
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) return;

    const newType: CustomContentType = {
      id: crypto.randomUUID(),
      name: formData.name.trim(),
      description: formData.description.trim(),
      icon: formData.icon,
      category: formData.category,
      defaultAIOptions: formData.defaultAIOptions,
      templateHints: formData.templateHints.filter(hint => hint.trim()),
      createdAt: new Date(),
      updatedAt: new Date()
    };

    const updatedTypes = [...customTypes, newType];
    await saveCustomTypes(updatedTypes);
    resetForm();
  };

  const handleEdit = (type: CustomContentType) => {
    setFormData({
      name: type.name,
      description: type.description,
      icon: type.icon,
      category: type.category,
      templateHints: type.templateHints.length > 0 ? type.templateHints : [''],
      defaultAIOptions: type.defaultAIOptions
    });
    setEditingType(type);
    setShowCreateForm(true);
  };

  const handleUpdate = async () => {
    if (!editingType || !formData.name.trim()) return;

    const updatedType: CustomContentType = {
      ...editingType,
      name: formData.name.trim(),
      description: formData.description.trim(),
      icon: formData.icon,
      category: formData.category,
      defaultAIOptions: formData.defaultAIOptions,
      templateHints: formData.templateHints.filter(hint => hint.trim()),
      updatedAt: new Date()
    };

    const updatedTypes = customTypes.map(type => 
      type.id === editingType.id ? updatedType : type
    );
    await saveCustomTypes(updatedTypes);
    resetForm();
  };

  const handleDelete = async (typeId: string) => {
    if (confirm('Are you sure you want to delete this custom content type?')) {
      const updatedTypes = customTypes.filter(type => type.id !== typeId);
      await saveCustomTypes(updatedTypes);
    }
  };

  const saveCustomTypes = async (types: CustomContentType[]) => {
    if (state.settings) {
      const updatedSettings = {
        ...state.settings,
        advanced: {
          ...state.settings.advanced,
          customContentTypes: types
        }
      };
      await actions.saveSettings(updatedSettings);
      setCustomTypes(types);
      onContentTypesUpdated(types);
    }
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
        maxWidth: '900px',
        width: '90%',
        maxHeight: '90%',
        overflow: 'hidden',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)'
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
            🔧 Custom Content Types
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

        {/* Content */}
        <div style={{ padding: '24px', overflow: 'auto', maxHeight: '70vh' }}>
          {!showCreateForm ? (
            <div>
              {/* Create Button */}
              <div style={{ marginBottom: '24px' }}>
                <button
                  onClick={() => setShowCreateForm(true)}
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
                  ➕ Create Custom Content Type
                </button>
              </div>

              {/* Custom Types List */}
              {customTypes.length === 0 ? (
                <div style={{
                  padding: '40px',
                  textAlign: 'center',
                  color: '#64748b',
                  backgroundColor: '#f8fafc',
                  borderRadius: '12px',
                  border: '2px dashed #cbd5e1'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎨</div>
                  <h3 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>No Custom Content Types</h3>
                  <p style={{ margin: 0, fontSize: '14px' }}>
                    Create custom content types to extend beyond the standard options like Slides, Worksheets, and Quizzes.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '16px' }}>
                  {customTypes.map(type => (
                    <div
                      key={type.id}
                      style={{
                        padding: '20px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '12px',
                        backgroundColor: 'white'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', flex: 1 }}>
                          <span style={{ fontSize: '32px' }}>{type.icon}</span>
                          <div style={{ flex: 1 }}>
                            <h4 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', margin: '0 0 8px 0' }}>
                              {type.name}
                            </h4>
                            <p style={{ fontSize: '14px', color: '#64748b', margin: '0 0 12px 0' }}>
                              {type.description}
                            </p>
                            
                            <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#64748b' }}>
                              <span>
                                <strong>Category:</strong> {CATEGORY_OPTIONS.find(c => c.value === type.category)?.label}
                              </span>
                              <span>
                                <strong>AI Options:</strong> {Object.values(type.defaultAIOptions).filter(Boolean).length} enabled
                              </span>
                              <span>
                                <strong>Template Hints:</strong> {type.templateHints.length}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => handleEdit(type)}
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
                            onClick={() => handleDelete(type.id)}
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
          ) : (
            <div>
              {/* Create/Edit Form */}
              <h3 style={{ fontSize: '18px', fontWeight: '600', margin: '0 0 24px 0', color: '#1e293b' }}>
                {editingType ? 'Edit Custom Content Type' : 'Create New Custom Content Type'}
              </h3>

              <div style={{ display: 'grid', gap: '20px' }}>
                {/* Basic Info */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                      Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="e.g., Lab Report, Case Study, Reflection Paper"
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
                      Icon
                    </label>
                    <select
                      value={formData.icon}
                      onChange={(e) => handleInputChange('icon', e.target.value)}
                      style={{
                        width: '100%',
                        padding: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '8px',
                        fontSize: '14px',
                        backgroundColor: 'white'
                      }}
                    >
                      {ICON_OPTIONS.map(icon => (
                        <option key={icon} value={icon}>{icon} {icon}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Describe what this content type is used for and how it helps students learn..."
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

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => handleInputChange('category', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '14px',
                      backgroundColor: 'white'
                    }}
                  >
                    {CATEGORY_OPTIONS.map(category => (
                      <option key={category.value} value={category.value}>
                        {category.label} - {category.description}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Template Hints */}
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#374151' }}>
                    Template Hints
                  </label>
                  <p style={{ fontSize: '13px', color: '#6b7280', margin: '0 0 12px 0' }}>
                    Provide guidance for AI on what this content type should include or focus on.
                  </p>
                  {formData.templateHints.map((hint, index) => (
                    <div key={index} style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                      <input
                        type="text"
                        value={hint}
                        onChange={(e) => handleTemplateHintChange(index, e.target.value)}
                        placeholder="e.g., Include methodology section, Focus on practical applications"
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          border: '1px solid #d1d5db',
                          borderRadius: '6px',
                          fontSize: '14px'
                        }}
                      />
                      {formData.templateHints.length > 1 && (
                        <button
                          onClick={() => removeTemplateHint(index)}
                          style={{
                            padding: '8px',
                            border: '1px solid #dc2626',
                            backgroundColor: '#fef2f2',
                            color: '#dc2626',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={addTemplateHint}
                    style={{
                      padding: '8px 12px',
                      border: '1px solid #059669',
                      backgroundColor: '#dcfce7',
                      color: '#166534',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    ➕ Add Hint
                  </button>
                </div>

                {/* Default AI Options */}
                <div>
                  <label style={{ display: 'block', marginBottom: '12px', fontWeight: '500', color: '#374151' }}>
                    Default AI Enhancement Options
                  </label>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.defaultAIOptions.enableInteractionPrompts}
                        onChange={(e) => handleAIOptionChange('enableInteractionPrompts', e.target.checked)}
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span style={{ fontSize: '14px', color: '#374151' }}>
                        💬 Enable interaction prompts and discussion starters
                      </span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.defaultAIOptions.includeBrainstormingActivities}
                        onChange={(e) => handleAIOptionChange('includeBrainstormingActivities', e.target.checked)}
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span style={{ fontSize: '14px', color: '#374151' }}>
                        💡 Include brainstorming and ideation activities
                      </span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.defaultAIOptions.suggestAITools}
                        onChange={(e) => handleAIOptionChange('suggestAITools', e.target.checked)}
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span style={{ fontSize: '14px', color: '#374151' }}>
                        🔧 Suggest relevant AI tools for students
                      </span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.defaultAIOptions.createResistantAlternatives}
                        onChange={(e) => handleAIOptionChange('createResistantAlternatives', e.target.checked)}
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span style={{ fontSize: '14px', color: '#374151' }}>
                        🛡️ Create AI-resistant alternative activities
                      </span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={formData.defaultAIOptions.addLiteracyComponents}
                        onChange={(e) => handleAIOptionChange('addLiteracyComponents', e.target.checked)}
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span style={{ fontSize: '14px', color: '#374151' }}>
                        📚 Add AI literacy and ethics components
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Form Actions */}
              <div style={{ 
                marginTop: '24px',
                paddingTop: '24px',
                borderTop: '1px solid #e5e7eb',
                display: 'flex',
                gap: '12px',
                justifyContent: 'flex-end'
              }}>
                <button
                  onClick={resetForm}
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
                  onClick={editingType ? handleUpdate : handleCreate}
                  disabled={!formData.name.trim()}
                  style={{
                    padding: '12px 24px',
                    border: 'none',
                    backgroundColor: formData.name.trim() ? '#3b82f6' : '#9ca3af',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: formData.name.trim() ? 'pointer' : 'not-allowed',
                    fontSize: '16px',
                    fontWeight: '500'
                  }}
                >
                  {editingType ? 'Update Content Type' : 'Create Content Type'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}