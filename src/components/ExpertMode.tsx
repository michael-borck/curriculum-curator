import React, { useState } from 'react';
import { useAppContext } from '../context/AppContext';
import { ContentType } from '../types';
import './ExpertMode.css';

export function ExpertMode() {
  const { state, setContentRequest } = useAppContext();
  const [activeTab, setActiveTab] = useState('planner');
  const [formData, setFormData] = useState({
    topic: '',
    learningObjectives: [''],
    duration: '50 minutes',
    audience: '',
    contentTypes: [] as ContentType[],
    customPrompts: {},
    batchGeneration: false,
    qualitySettings: {
      complexity: 'intermediate',
      style: 'interactive',
      accessibility: true,
      rubrics: false,
      extensions: false,
    },
  });

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const addLearningObjective = () => {
    setFormData(prev => ({
      ...prev,
      learningObjectives: [...prev.learningObjectives, ''],
    }));
  };

  const updateLearningObjective = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      learningObjectives: prev.learningObjectives.map((obj, i) => i === index ? value : obj),
    }));
  };

  const removeLearningObjective = (index: number) => {
    setFormData(prev => ({
      ...prev,
      learningObjectives: prev.learningObjectives.filter((_, i) => i !== index),
    }));
  };

  const toggleContentType = (contentType: ContentType) => {
    setFormData(prev => ({
      ...prev,
      contentTypes: prev.contentTypes.includes(contentType)
        ? prev.contentTypes.filter(t => t !== contentType)
        : [...prev.contentTypes, contentType],
    }));
  };

  const handleGenerate = () => {
    const request = {
      topic: formData.topic,
      learningObjectives: formData.learningObjectives.filter(obj => obj.trim() !== ''),
      duration: formData.duration,
      audience: formData.audience,
      contentTypes: formData.contentTypes,
    };
    setContentRequest(request);
  };

  return (
    <div className="expert-mode">
      <div className="expert-header">
        <h1>Expert Content Planner</h1>
        <div className="expert-tabs">
          <button 
            className={`tab-btn ${activeTab === 'planner' ? 'active' : ''}`}
            onClick={() => setActiveTab('planner')}
          >
            Content Planner
          </button>
          <button 
            className={`tab-btn ${activeTab === 'templates' ? 'active' : ''}`}
            onClick={() => setActiveTab('templates')}
          >
            Template Editor
          </button>
          <button 
            className={`tab-btn ${activeTab === 'batch' ? 'active' : ''}`}
            onClick={() => setActiveTab('batch')}
          >
            Batch Generator
          </button>
          <button 
            className={`tab-btn ${activeTab === 'quality' ? 'active' : ''}`}
            onClick={() => setActiveTab('quality')}
          >
            Quality Control
          </button>
        </div>
      </div>

      <div className="expert-content">
        {activeTab === 'planner' && (
          <div className="planner-tab">
            <div className="planner-grid">
              <div className="planner-section">
                <h2>Course Information</h2>
                <div className="form-group">
                  <label htmlFor="expert-topic">Topic/Subject</label>
                  <input
                    id="expert-topic"
                    type="text"
                    value={formData.topic}
                    onChange={(e) => handleInputChange('topic', e.target.value)}
                    placeholder="Enter the lesson topic"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="expert-audience">Target Audience</label>
                  <input
                    id="expert-audience"
                    type="text"
                    value={formData.audience}
                    onChange={(e) => handleInputChange('audience', e.target.value)}
                    placeholder="Describe your students"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="expert-duration">Session Duration</label>
                  <select
                    id="expert-duration"
                    value={formData.duration}
                    onChange={(e) => handleInputChange('duration', e.target.value)}
                    className="form-select"
                  >
                    <option value="30 minutes">30 minutes</option>
                    <option value="50 minutes">50 minutes</option>
                    <option value="75 minutes">75 minutes</option>
                    <option value="90 minutes">90 minutes</option>
                    <option value="2 hours">2 hours</option>
                    <option value="3 hours">3 hours</option>
                    <option value="Custom">Custom duration</option>
                  </select>
                </div>
              </div>

              <div className="planner-section">
                <h2>Learning Objectives</h2>
                <div className="objectives-editor">
                  {formData.learningObjectives.map((objective, index) => (
                    <div key={index} className="objective-row">
                      <input
                        type="text"
                        value={objective}
                        onChange={(e) => updateLearningObjective(index, e.target.value)}
                        placeholder={`Learning objective ${index + 1}`}
                        className="form-input"
                      />
                      <div className="objective-controls">
                        {formData.learningObjectives.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeLearningObjective(index)}
                            className="btn-icon danger"
                            title="Remove objective"
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addLearningObjective}
                    className="add-btn"
                  >
                    + Add Objective
                  </button>
                </div>
              </div>

              <div className="planner-section full-width">
                <h2>Content Types</h2>
                <div className="content-selection">
                  {(['Slides', 'InstructorNotes', 'Worksheet', 'Quiz', 'ActivityGuide'] as ContentType[]).map((type) => (
                    <div
                      key={type}
                      className={`content-card ${formData.contentTypes.includes(type) ? 'selected' : ''}`}
                      onClick={() => toggleContentType(type)}
                    >
                      <div className="content-header">
                        <input
                          type="checkbox"
                          checked={formData.contentTypes.includes(type)}
                          onChange={() => toggleContentType(type)}
                        />
                        <h3>{type.replace(/([A-Z])/g, ' $1').trim()}</h3>
                      </div>
                      <div className="content-options">
                        <label>
                          <input type="checkbox" /> Advanced formatting
                        </label>
                        <label>
                          <input type="checkbox" /> Include media placeholders
                        </label>
                        <label>
                          <input type="checkbox" /> Auto-generate assessment
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="planner-actions">
              <button className="btn secondary">Save Draft</button>
              <button className="btn secondary">Load Template</button>
              <button 
                className="btn primary"
                onClick={handleGenerate}
                disabled={!formData.topic || formData.contentTypes.length === 0}
              >
                Generate Content
              </button>
            </div>
          </div>
        )}

        {activeTab === 'templates' && (
          <div className="templates-tab">
            <div className="templates-header">
              <h2>Template Editor</h2>
              <div className="template-actions">
                <button className="btn secondary">Import Template</button>
                <button className="btn secondary">Export Template</button>
                <button className="btn primary">New Template</button>
              </div>
            </div>

            <div className="templates-content">
              <div className="template-list">
                <h3>Available Templates</h3>
                <div className="template-items">
                  <div className="template-item active">
                    <h4>Standard Lecture</h4>
                    <p>Traditional lecture format with slides and notes</p>
                    <div className="template-meta">
                      <span>Modified: 2 days ago</span>
                    </div>
                  </div>
                  <div className="template-item">
                    <h4>Interactive Workshop</h4>
                    <p>Activity-focused session with group work</p>
                    <div className="template-meta">
                      <span>Modified: 1 week ago</span>
                    </div>
                  </div>
                  <div className="template-item">
                    <h4>Assessment Heavy</h4>
                    <p>Multiple quizzes and practice exercises</p>
                    <div className="template-meta">
                      <span>Modified: 2 weeks ago</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="template-editor">
                <h3>Template Preview</h3>
                <div className="editor-placeholder">
                  <p>Select a template to edit or create a new one</p>
                  <button className="btn primary">Create New Template</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'batch' && (
          <div className="batch-tab">
            <div className="batch-header">
              <h2>Batch Content Generator</h2>
              <p>Generate content for multiple lessons at once</p>
            </div>

            <div className="batch-content">
              <div className="batch-setup">
                <h3>Batch Configuration</h3>
                <div className="form-group">
                  <label>Course Name</label>
                  <input type="text" placeholder="e.g., Introduction to Psychology" className="form-input" />
                </div>
                <div className="form-group">
                  <label>Number of Lessons</label>
                  <input type="number" placeholder="12" min="1" max="50" className="form-input" />
                </div>
                <div className="form-group">
                  <label>Content Types (for all lessons)</label>
                  <div className="checkbox-group">
                    <label><input type="checkbox" /> Slides</label>
                    <label><input type="checkbox" /> Instructor Notes</label>
                    <label><input type="checkbox" /> Worksheets</label>
                    <label><input type="checkbox" /> Quizzes</label>
                  </div>
                </div>
              </div>

              <div className="batch-preview">
                <h3>Batch Preview</h3>
                <div className="batch-placeholder">
                  <p>Configure your batch settings to see a preview</p>
                </div>
              </div>
            </div>

            <div className="batch-actions">
              <button className="btn secondary">Import CSV</button>
              <button className="btn secondary">Save Configuration</button>
              <button className="btn primary">Start Batch Generation</button>
            </div>
          </div>
        )}

        {activeTab === 'quality' && (
          <div className="quality-tab">
            <div className="quality-header">
              <h2>Quality Control</h2>
              <p>Configure validation rules and quality standards</p>
            </div>

            <div className="quality-content">
              <div className="quality-section">
                <h3>Content Validation</h3>
                <div className="validation-rules">
                  <label className="rule-item">
                    <input type="checkbox" defaultChecked />
                    <div className="rule-info">
                      <strong>Readability Check</strong>
                      <p>Ensure content matches target reading level</p>
                    </div>
                  </label>
                  <label className="rule-item">
                    <input type="checkbox" defaultChecked />
                    <div className="rule-info">
                      <strong>Learning Objective Alignment</strong>
                      <p>Verify content supports stated objectives</p>
                    </div>
                  </label>
                  <label className="rule-item">
                    <input type="checkbox" />
                    <div className="rule-info">
                      <strong>Accessibility Standards</strong>
                      <p>Check for accessibility compliance</p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="quality-section">
                <h3>Generation Settings</h3>
                <div className="form-group">
                  <label>Content Complexity</label>
                  <select className="form-select">
                    <option>Beginner</option>
                    <option>Intermediate</option>
                    <option>Advanced</option>
                    <option>Mixed</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Quality Threshold</label>
                  <input type="range" min="1" max="10" defaultValue="7" />
                  <span>7/10</span>
                </div>
              </div>

              <div className="quality-section">
                <h3>Review Process</h3>
                <div className="checkbox-group">
                  <label>
                    <input type="checkbox" defaultChecked />
                    <span>Require manual review before export</span>
                  </label>
                  <label>
                    <input type="checkbox" />
                    <span>Auto-fix common issues</span>
                  </label>
                  <label>
                    <input type="checkbox" />
                    <span>Generate quality report</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}