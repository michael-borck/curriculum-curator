// Settings Storage Utilities

import type { UserSettings, UserProfile, SettingsStorageOptions, SettingsValidationResult, LearningInsights } from '../types/settings';
import { crossSessionLearning } from './crossSessionLearning';

const STORAGE_KEYS = {
  USER_SETTINGS: 'curriculum_curator_settings',
  USER_PROFILE: 'curriculum_curator_profile',
  RECENT_SESSIONS: 'curriculum_curator_recent_sessions',
  PREFERENCES: 'curriculum_curator_preferences'
} as const;

export class SettingsStorage {
  private static instance: SettingsStorage;
  
  static getInstance(): SettingsStorage {
    if (!SettingsStorage.instance) {
      SettingsStorage.instance = new SettingsStorage();
    }
    return SettingsStorage.instance;
  }

  // Load settings from localStorage
  loadSettings(): UserSettings | null {
    try {
      const settingsJson = localStorage.getItem(STORAGE_KEYS.USER_SETTINGS);
      if (!settingsJson) return null;
      
      const settings = JSON.parse(settingsJson);
      
      // Convert date strings back to Date objects
      if (settings.profile) {
        settings.profile.createdAt = new Date(settings.profile.createdAt);
        settings.profile.updatedAt = new Date(settings.profile.updatedAt);
      }
      
      const validation = this.validateSettings(settings);
      if (!validation.isValid) {
        console.warn('Invalid settings detected:', validation.errors);
        return null;
      }
      
      return settings;
    } catch (error) {
      console.error('Failed to load settings:', error);
      return null;
    }
  }

  // Save settings to localStorage
  saveSettings(settings: UserSettings, options: SettingsStorageOptions = { scope: 'global', autoSave: true }): boolean {
    try {
      const validation = this.validateSettings(settings);
      if (!validation.isValid) {
        console.error('Cannot save invalid settings:', validation.errors);
        return false;
      }

      // Update timestamp
      settings.profile.updatedAt = new Date();
      
      const settingsJson = JSON.stringify(settings);
      localStorage.setItem(STORAGE_KEYS.USER_SETTINGS, settingsJson);
      
      // Store scope-specific settings if needed
      if (options.scope !== 'global') {
        const scopeKey = `${STORAGE_KEYS.USER_SETTINGS}_${options.scope}_${settings.profile.subject}`;
        localStorage.setItem(scopeKey, settingsJson);
      }
      
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    }
  }

  // Load user profile specifically
  loadProfile(): UserProfile | null {
    try {
      const settings = this.loadSettings();
      return settings?.profile || null;
    } catch (error) {
      console.error('Failed to load profile:', error);
      return null;
    }
  }

  // Save user profile specifically
  saveProfile(profile: UserProfile): boolean {
    try {
      const settings = this.loadSettings();
      if (settings) {
        settings.profile = profile;
        return this.saveSettings(settings);
      } else {
        // Create new settings with this profile
        const newSettings = this.createDefaultSettings(profile);
        return this.saveSettings(newSettings);
      }
    } catch (error) {
      console.error('Failed to save profile:', error);
      return false;
    }
  }

  // Create default settings for a new user
  createDefaultSettings(profile?: Partial<UserProfile>): UserSettings {
    const defaultProfile: UserProfile = {
      id: crypto.randomUUID(),
      name: profile?.name || 'New User',
      email: profile?.email,
      institution: profile?.institution,
      subject: profile?.subject || 'General',
      level: profile?.level || 'college',
      teachingStyle: profile?.teachingStyle || 'mixed-approach',
      aiPreference: profile?.aiPreference || 'ai-enhanced',
      createdAt: new Date(),
      updatedAt: new Date(),
      ...profile
    };

    return {
      profile: defaultProfile,
      defaults: {
        duration: '50 minutes',
        complexity: 'intermediate',
        contentTypes: ['Slides', 'InstructorNotes'],
        quizTypes: ['multiple-choice', 'true-false'],
        includeAnswerKeys: true,
        includeInstructorGuides: true,
        includeRubrics: false,
        includeAccessibilityFeatures: false,
        answerKeyOptions: {
          includeExplanations: true,
          includeDifficulty: true,
          includePoints: false
        },
        instructorGuideOptions: {
          includeTiming: true,
          includeGradingTips: true,
          includeDiscussionPrompts: false,
          includeExtensions: false
        }
      },
      preferences: {
        formComplexity: 'essential',
        showAdvancedOptions: false,
        autoSaveSettings: true,
        useSettingsByDefault: true,
        theme: 'light'
      },
      advanced: {
        customContentTypes: [],
        customTemplates: [],
        templatePreferences: {
          visualTheme: 'modern-clean',
          contentDepth: 5,
          pacingStrategy: 'instructor-led',
          assessmentFocus: ['formative']
        },
        aiCustomization: {
          contentSpecificOptions: {
            'Slides': {
              enableInteractionPrompts: true,
              includeBrainstormingActivities: false,
              suggestAITools: true,
              createResistantAlternatives: false,
              addLiteracyComponents: false
            },
            'InstructorNotes': {
              enableInteractionPrompts: false,
              includeBrainstormingActivities: false,
              suggestAITools: false,
              createResistantAlternatives: false,
              addLiteracyComponents: false
            },
            'Worksheet': {
              enableInteractionPrompts: false,
              includeBrainstormingActivities: true,
              suggestAITools: false,
              createResistantAlternatives: true,
              addLiteracyComponents: false
            },
            'Quiz': {
              enableInteractionPrompts: false,
              includeBrainstormingActivities: false,
              suggestAITools: false,
              createResistantAlternatives: true,
              addLiteracyComponents: true
            },
            'ActivityGuide': {
              enableInteractionPrompts: true,
              includeBrainstormingActivities: true,
              suggestAITools: true,
              createResistantAlternatives: false,
              addLiteracyComponents: true
            },
            'Custom': {
              enableInteractionPrompts: false,
              includeBrainstormingActivities: false,
              suggestAITools: false,
              createResistantAlternatives: false,
              addLiteracyComponents: false
            }
          },
          promptCustomization: {
            customPrompts: {},
            promptStyle: 'academic',
            includeExamples: true,
            adaptToAudience: true
          },
          resistanceStrategies: ['process-focused', 'authentic-context']
        },
        exportSettings: {
          defaultFormat: 'pdf',
          includeMetadata: true,
          brandingOptions: {
            colors: {
              primary: '#3b82f6',
              secondary: '#64748b',
              accent: '#f59e0b'
            },
            fonts: {
              heading: 'Inter',
              body: 'Inter'
            }
          },
          qualitySettings: {
            imageResolution: 'high',
            compressionLevel: 80,
            includeSourceFiles: false,
            generateMultipleFormats: false
          }
        }
      }
    };
  }

  // Validate settings structure
  validateSettings(settings: any): SettingsValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check required fields
    if (!settings.profile) {
      errors.push('Profile is required');
    } else {
      if (!settings.profile.id) errors.push('Profile ID is required');
      if (!settings.profile.name) errors.push('Profile name is required');
      if (!settings.profile.subject) errors.push('Profile subject is required');
    }

    if (!settings.defaults) {
      errors.push('Default settings are required');
    }

    if (!settings.preferences) {
      errors.push('UI preferences are required');
    }

    // Check data types and ranges
    if (settings.defaults?.complexity && !['basic', 'intermediate', 'advanced'].includes(settings.defaults.complexity)) {
      errors.push('Invalid complexity level');
    }

    if (settings.preferences?.formComplexity && !['essential', 'enhanced', 'advanced'].includes(settings.preferences.formComplexity)) {
      errors.push('Invalid form complexity level');
    }

    // Warnings for potential issues
    if (settings.defaults?.contentTypes?.length === 0) {
      warnings.push('No default content types selected');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  // Clear all settings
  clearSettings(): boolean {
    try {
      localStorage.removeItem(STORAGE_KEYS.USER_SETTINGS);
      localStorage.removeItem(STORAGE_KEYS.USER_PROFILE);
      localStorage.removeItem(STORAGE_KEYS.RECENT_SESSIONS);
      localStorage.removeItem(STORAGE_KEYS.PREFERENCES);
      return true;
    } catch (error) {
      console.error('Failed to clear settings:', error);
      return false;
    }
  }

  // Export settings for backup
  exportSettings(): string {
    const settings = this.loadSettings();
    if (!settings) return '';
    
    return JSON.stringify(settings, null, 2);
  }

  // Import settings from backup
  importSettings(settingsJson: string): boolean {
    try {
      const settings = JSON.parse(settingsJson);
      const validation = this.validateSettings(settings);
      
      if (!validation.isValid) {
        console.error('Cannot import invalid settings:', validation.errors);
        return false;
      }
      
      return this.saveSettings(settings);
    } catch (error) {
      console.error('Failed to import settings:', error);
      return false;
    }
  }

  // Get subject-specific settings
  getSubjectSettings(subject: string): UserSettings | null {
    try {
      const scopeKey = `${STORAGE_KEYS.USER_SETTINGS}_subject_${subject}`;
      const settingsJson = localStorage.getItem(scopeKey);
      
      if (settingsJson) {
        return JSON.parse(settingsJson);
      }
      
      // Fall back to global settings
      return this.loadSettings();
    } catch (error) {
      console.error('Failed to load subject settings:', error);
      return null;
    }
  }

  // Save recent session data
  saveRecentSession(sessionData: any): void {
    try {
      const recent = this.getRecentSessions();
      recent.unshift({
        ...sessionData,
        timestamp: new Date().toISOString()
      });
      
      // Keep only last 10 sessions
      const trimmed = recent.slice(0, 10);
      localStorage.setItem(STORAGE_KEYS.RECENT_SESSIONS, JSON.stringify(trimmed));
    } catch (error) {
      console.error('Failed to save recent session:', error);
    }
  }

  // Get recent sessions
  getRecentSessions(): any[] {
    try {
      const sessionsJson = localStorage.getItem(STORAGE_KEYS.RECENT_SESSIONS);
      return sessionsJson ? JSON.parse(sessionsJson) : [];
    } catch (error) {
      console.error('Failed to load recent sessions:', error);
      return [];
    }
  }

  // Get learning-enhanced defaults
  getLearningEnhancedDefaults(baseProfile?: Partial<UserProfile>): UserSettings {
    const defaultSettings = this.createDefaultSettings(baseProfile);
    
    try {
      // Get learning insights
      const insights = crossSessionLearning.getLearningInsights();
      const adaptedDefaults = crossSessionLearning.getAdaptedDefaults();
      
      // Apply learning insights to defaults
      if (adaptedDefaults.contentTypes && adaptedDefaults.contentTypes.length > 0) {
        defaultSettings.defaults.contentTypes = adaptedDefaults.contentTypes;
      }
      
      if (adaptedDefaults.complexity) {
        defaultSettings.defaults.complexity = adaptedDefaults.complexity;
      }
      
      if (adaptedDefaults.duration) {
        defaultSettings.defaults.duration = adaptedDefaults.duration;
      }
      
      // Apply subject-specific learning if available
      if (baseProfile?.subject && insights.commonSubjects.includes(baseProfile.subject)) {
        const subjectSettings = this.getSubjectSettings(baseProfile.subject);
        if (subjectSettings) {
          // Merge subject-specific patterns
          defaultSettings.defaults = {
            ...defaultSettings.defaults,
            ...subjectSettings.defaults
          };
        }
      }
      
      return defaultSettings;
    } catch (error) {
      console.error('Failed to apply learning enhancements:', error);
      return defaultSettings;
    }
  }

  // Save settings with learning tracking
  saveSettingsWithLearning(settings: UserSettings, options: SettingsStorageOptions = { scope: 'global', autoSave: true }): boolean {
    const success = this.saveSettings(settings, options);
    
    if (success) {
      // Track settings change
      crossSessionLearning.trackInteraction({
        type: 'setting_changed',
        data: {
          scope: options.scope,
          profileSubject: settings.profile.subject,
          contentTypes: settings.defaults.contentTypes,
          complexity: settings.defaults.complexity
        }
      });
    }
    
    return success;
  }

  // Get personalized suggestions based on learning data
  getPersonalizedSuggestions(): string[] {
    try {
      const insights = crossSessionLearning.getLearningInsights();
      return insights.improvementSuggestions;
    } catch (error) {
      console.error('Failed to get personalized suggestions:', error);
      return [
        'Complete your teaching profile for better personalized defaults',
        'Try different content types to find what works best for your teaching style',
        'Use the wizard mode for guided content creation'
      ];
    }
  }

  // Get learning insights for display
  getLearningInsights(): LearningInsights {
    return crossSessionLearning.getLearningInsights();
  }

  // Check if user should see learning-based recommendations
  shouldShowLearningRecommendations(): boolean {
    const stats = crossSessionLearning.getLearningStatistics();
    return stats ? stats.totalSessions >= 3 : false;
  }

  // Get smart defaults based on context
  getSmartDefaults(context: { subject?: string; previousSession?: any }): Partial<UserSettings> {
    const insights = crossSessionLearning.getLearningInsights();
    const baseDefaults = this.createDefaultSettings();
    
    // Context-aware adjustments
    if (context.subject && insights.commonSubjects.includes(context.subject)) {
      const subjectSettings = this.getSubjectSettings(context.subject);
      if (subjectSettings) {
        return {
          defaults: {
            ...baseDefaults.defaults,
            ...subjectSettings.defaults
          }
        };
      }
    }
    
    // Previous session continuity
    if (context.previousSession) {
      return {
        defaults: {
          ...baseDefaults.defaults,
          contentTypes: context.previousSession.contentTypes || baseDefaults.defaults.contentTypes,
          complexity: context.previousSession.complexity || baseDefaults.defaults.complexity
        }
      };
    }
    
    // Apply general learning insights
    return {
      defaults: {
        ...baseDefaults.defaults,
        ...insights.adaptedDefaults
      }
    };
  }
}

// Export singleton instance
export const settingsStorage = SettingsStorage.getInstance();