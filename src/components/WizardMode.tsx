import React, { useState } from 'react';
import { useAppContext } from '../context/AppContext';
import { ContentType } from '../types';
import './WizardMode.css';

export function WizardMode() {
  const { state, setContentRequest } = useAppContext();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    topic: '',
    learningObjectives: [''],
    duration: '50 minutes',
    audience: '',
    contentTypes: [] as ContentType[],
  });

  const handleInputChange = (field: string, value: string | string[] | ContentType[]) => {
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

  const nextStep = () => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.topic.trim() !== '' && formData.audience.trim() !== '';
      case 2:
        return formData.learningObjectives.some(obj => obj.trim() !== '');
      case 3:
        return formData.contentTypes.length > 0;
      case 4:
        return true; // Configuration is optional
      default:
        return false;
    }
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
    setCurrentStep(5); // Move to generation step
  };

  return (
    <div className="wizard-mode">
      <div className="wizard-header">
        <div className="wizard-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(currentStep / 5) * 100}%` }}
            />
          </div>
          <span className="progress-text">Step {currentStep} of 5</span>
        </div>
      </div>

      <div className="wizard-content">
        {currentStep === 1 && (
          <div className="wizard-step">
            <h2>Topic & Audience</h2>
            <p>Let's start by defining what you want to teach and who your students are.</p>
            
            <div className="form-group">
              <label htmlFor="topic">What topic will you be teaching?</label>
              <input
                id="topic"
                type="text"
                value={formData.topic}
                onChange={(e) => handleInputChange('topic', e.target.value)}
                placeholder="e.g., Introduction to Calculus, World War I, Cell Biology"
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="audience">Who is your audience?</label>
              <input
                id="audience"
                type="text"
                value={formData.audience}
                onChange={(e) => handleInputChange('audience', e.target.value)}
                placeholder="e.g., High school seniors, College freshmen, Adult learners"
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="duration">How long is your class session?</label>
              <select
                id="duration"
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
              </select>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="wizard-step">
            <h2>Learning Objectives</h2>
            <p>What should students be able to do after this lesson?</p>
            
            <div className="learning-objectives">
              {formData.learningObjectives.map((objective, index) => (
                <div key={index} className="objective-input-group">
                  <input
                    type="text"
                    value={objective}
                    onChange={(e) => updateLearningObjective(index, e.target.value)}
                    placeholder={`Learning objective ${index + 1}`}
                    className="form-input"
                  />
                  {formData.learningObjectives.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeLearningObjective(index)}
                      className="remove-btn"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              
              <button
                type="button"
                onClick={addLearningObjective}
                className="add-objective-btn"
              >
                + Add another objective
              </button>
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div className="wizard-step">
            <h2>Content Selection</h2>
            <p>What types of content would you like to generate?</p>
            
            <div className="content-types-grid">
              {(['Slides', 'InstructorNotes', 'Worksheet', 'Quiz', 'ActivityGuide'] as ContentType[]).map((type) => (
                <div
                  key={type}
                  className={`content-type-card ${formData.contentTypes.includes(type) ? 'selected' : ''}`}
                  onClick={() => toggleContentType(type)}
                >
                  <div className="content-type-icon">
                    {type === 'Slides' && (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="4" width="18" height="12" rx="2" ry="2" />
                        <line x1="7" y1="8" x2="17" y2="8" />
                        <line x1="7" y1="12" x2="13" y2="12" />
                      </svg>
                    )}
                    {type === 'InstructorNotes' && (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                        <polyline points="14,2 14,8 20,8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                        <polyline points="10,9 9,9 8,9" />
                      </svg>
                    )}
                    {type === 'Worksheet' && (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                        <polyline points="14,2 14,8 20,8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                        <line x1="10" y1="9" x2="8" y2="9" />
                      </svg>
                    )}
                    {type === 'Quiz' && (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
                        <path d="M12 17h.01" />
                        <circle cx="12" cy="12" r="10" />
                      </svg>
                    )}
                    {type === 'ActivityGuide' && (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                        <circle cx="9" cy="7" r="4" />
                        <path d="M23 21v-2a4 4 0 00-3-3.87" />
                        <path d="M16 3.13a4 4 0 010 7.75" />
                      </svg>
                    )}
                  </div>
                  <h3>{type.replace(/([A-Z])/g, ' $1').trim()}</h3>
                  <p>
                    {type === 'Slides' && 'Presentation slides with key points'}
                    {type === 'InstructorNotes' && 'Detailed teaching notes and talking points'}
                    {type === 'Worksheet' && 'Student practice exercises and problems'}
                    {type === 'Quiz' && 'Assessment questions with answer keys'}
                    {type === 'ActivityGuide' && 'Interactive learning activities and group work'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div className="wizard-step">
            <h2>Configuration</h2>
            <p>Fine-tune your content generation settings.</p>
            
            <div className="config-section">
              <h3>Content Complexity</h3>
              <div className="radio-group">
                <label>
                  <input type="radio" name="complexity" value="basic" defaultChecked />
                  <span>Basic - Simple language and concepts</span>
                </label>
                <label>
                  <input type="radio" name="complexity" value="intermediate" />
                  <span>Intermediate - Moderate complexity</span>
                </label>
                <label>
                  <input type="radio" name="complexity" value="advanced" />
                  <span>Advanced - Complex concepts and terminology</span>
                </label>
              </div>
            </div>

            <div className="config-section">
              <h3>Teaching Style</h3>
              <div className="radio-group">
                <label>
                  <input type="radio" name="style" value="traditional" defaultChecked />
                  <span>Traditional lecture format</span>
                </label>
                <label>
                  <input type="radio" name="style" value="interactive" />
                  <span>Interactive and discussion-based</span>
                </label>
                <label>
                  <input type="radio" name="style" value="hands-on" />
                  <span>Hands-on and activity-focused</span>
                </label>
              </div>
            </div>

            <div className="config-section">
              <h3>Additional Options</h3>
              <div className="checkbox-group">
                <label>
                  <input type="checkbox" />
                  <span>Include accessibility features</span>
                </label>
                <label>
                  <input type="checkbox" />
                  <span>Add assessment rubrics</span>
                </label>
                <label>
                  <input type="checkbox" />
                  <span>Include extension activities</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {currentStep === 5 && (
          <div className="wizard-step">
            <h2>Ready to Generate!</h2>
            <p>Review your selections and start generating your content.</p>
            
            <div className="summary-card">
              <h3>Summary</h3>
              <div className="summary-item">
                <strong>Topic:</strong> {formData.topic}
              </div>
              <div className="summary-item">
                <strong>Audience:</strong> {formData.audience}
              </div>
              <div className="summary-item">
                <strong>Duration:</strong> {formData.duration}
              </div>
              <div className="summary-item">
                <strong>Learning Objectives:</strong>
                <ul>
                  {formData.learningObjectives.filter(obj => obj.trim()).map((obj, index) => (
                    <li key={index}>{obj}</li>
                  ))}
                </ul>
              </div>
              <div className="summary-item">
                <strong>Content Types:</strong> {formData.contentTypes.join(', ')}
              </div>
            </div>

            {state.isGenerating ? (
              <div className="generating-state">
                <div className="spinner" />
                <p>Generating your content...</p>
              </div>
            ) : (
              <button className="generate-btn" onClick={handleGenerate}>
                🚀 Generate Content
              </button>
            )}
          </div>
        )}
      </div>

      <div className="wizard-footer">
        <div className="wizard-nav">
          {currentStep > 1 && currentStep < 5 && (
            <button className="nav-btn secondary" onClick={prevStep}>
              ← Previous
            </button>
          )}
          
          {currentStep < 4 && (
            <button 
              className="nav-btn primary" 
              onClick={nextStep}
              disabled={!canProceed()}
            >
              Next →
            </button>
          )}
          
          {currentStep === 4 && (
            <button 
              className="nav-btn primary" 
              onClick={nextStep}
            >
              Review →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}