// Cross-Session Learning and Analytics

import type { 
  SessionData, 
  UserInteraction, 
  SessionOutcome, 
  LearningInsights, 
  CrossSessionLearningData, 
  BehaviorPattern, 
  ContentDefaults, 
  ContentType, 
  AIContentOptions 
} from '../types/settings';

const STORAGE_KEYS = {
  LEARNING_DATA: 'curriculum_curator_learning_data',
  SESSION_ANALYTICS: 'curriculum_curator_session_analytics',
  BEHAVIOR_PATTERNS: 'curriculum_curator_behavior_patterns'
} as const;

export class CrossSessionLearningManager {
  private static instance: CrossSessionLearningManager;
  private currentSession: SessionData | null = null;
  private sessionStartTime: number = 0;
  
  static getInstance(): CrossSessionLearningManager {
    if (!CrossSessionLearningManager.instance) {
      CrossSessionLearningManager.instance = new CrossSessionLearningManager();
    }
    return CrossSessionLearningManager.instance;
  }

  // Start a new session
  startSession(initialData: Partial<SessionData>): string {
    const sessionId = crypto.randomUUID();
    this.sessionStartTime = Date.now();
    
    this.currentSession = {
      id: sessionId,
      timestamp: new Date().toISOString(),
      duration: 0,
      contentTypes: initialData.contentTypes || [],
      subject: initialData.subject || 'General',
      complexity: initialData.complexity || 'intermediate',
      aiEnhancements: initialData.aiEnhancements || {} as Record<ContentType, AIContentOptions>,
      userInteractions: [],
      outcome: {
        completed: false,
        contentGenerated: false,
        errorsEncountered: []
      }
    };
    
    return sessionId;
  }

  // Track user interaction
  trackInteraction(interaction: Omit<UserInteraction, 'timestamp'>): void {
    if (!this.currentSession) return;
    
    this.currentSession.userInteractions.push({
      ...interaction,
      timestamp: new Date().toISOString()
    });
    
    // Auto-save interaction data
    this.saveCurrentSession();
  }

  // Update session data
  updateSession(updates: Partial<SessionData>): void {
    if (!this.currentSession) return;
    
    this.currentSession = {
      ...this.currentSession,
      ...updates,
      duration: Math.round((Date.now() - this.sessionStartTime) / 60000) // in minutes
    };
  }

  // End current session
  endSession(outcome: Partial<SessionOutcome>): SessionData | null {
    if (!this.currentSession) return null;
    
    const finalSession: SessionData = {
      ...this.currentSession,
      duration: Math.round((Date.now() - this.sessionStartTime) / 60000),
      outcome: {
        ...this.currentSession.outcome,
        ...outcome,
        timeToCompletion: Math.round((Date.now() - this.sessionStartTime) / 60000)
      }
    };
    
    // Save final session data
    this.saveSession(finalSession);
    
    // Trigger learning analysis
    this.analyzeUserBehavior();
    
    this.currentSession = null;
    this.sessionStartTime = 0;
    
    return finalSession;
  }

  // Save session data
  private saveSession(session: SessionData): void {
    try {
      const existingSessions = this.getSessionHistory();
      existingSessions.unshift(session);
      
      // Keep last 50 sessions
      const trimmedSessions = existingSessions.slice(0, 50);
      localStorage.setItem(STORAGE_KEYS.SESSION_ANALYTICS, JSON.stringify(trimmedSessions));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  }

  // Save current session state
  private saveCurrentSession(): void {
    if (!this.currentSession) return;
    
    try {
      const currentSessionData = {
        ...this.currentSession,
        duration: Math.round((Date.now() - this.sessionStartTime) / 60000)
      };
      localStorage.setItem('curriculum_curator_current_session', JSON.stringify(currentSessionData));
    } catch (error) {
      console.error('Failed to save current session:', error);
    }
  }

  // Get session history
  getSessionHistory(): SessionData[] {
    try {
      const sessionsJson = localStorage.getItem(STORAGE_KEYS.SESSION_ANALYTICS);
      return sessionsJson ? JSON.parse(sessionsJson) : [];
    } catch (error) {
      console.error('Failed to load session history:', error);
      return [];
    }
  }

  // Analyze user behavior and generate insights
  analyzeUserBehavior(): LearningInsights {
    const sessions = this.getSessionHistory();
    
    if (sessions.length === 0) {
      return this.getDefaultInsights();
    }

    const completedSessions = sessions.filter(s => s.outcome.completed);
    const successfulSessions = sessions.filter(s => s.outcome.contentGenerated && s.outcome.completed);
    
    // Analyze content type preferences
    const contentTypeFrequency: Record<string, number> = {};
    sessions.forEach(session => {
      session.contentTypes.forEach(type => {
        contentTypeFrequency[type] = (contentTypeFrequency[type] || 0) + 1;
      });
    });
    
    const preferredContentTypes = Object.entries(contentTypeFrequency)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([type]) => type as ContentType);

    // Calculate average session duration
    const avgDuration = sessions.reduce((sum, s) => sum + s.duration, 0) / sessions.length;
    
    // Analyze common subjects
    const subjectFrequency: Record<string, number> = {};
    sessions.forEach(session => {
      subjectFrequency[session.subject] = (subjectFrequency[session.subject] || 0) + 1;
    });
    
    const commonSubjects = Object.entries(subjectFrequency)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([subject]) => subject);

    // Analyze frequently used settings
    const complexityFrequency: Record<string, number> = {};
    sessions.forEach(session => {
      complexityFrequency[session.complexity] = (complexityFrequency[session.complexity] || 0) + 1;
    });
    
    const mostUsedComplexity = Object.entries(complexityFrequency)
      .sort(([,a], [,b]) => b - a)[0]?.[0] as 'basic' | 'intermediate' | 'advanced' || 'intermediate';

    // Analyze error patterns
    const errorPatterns: string[] = [];
    sessions.forEach(session => {
      session.outcome.errorsEncountered.forEach(error => {
        if (!errorPatterns.includes(error)) {
          errorPatterns.push(error);
        }
      });
    });

    // Generate improvement suggestions
    const suggestions = this.generateImprovementSuggestions(sessions, successfulSessions);
    
    // Create adapted defaults based on usage patterns
    const adaptedDefaults: Partial<ContentDefaults> = {
      complexity: mostUsedComplexity,
      contentTypes: preferredContentTypes,
      duration: this.suggestOptimalDuration(avgDuration)
    };

    const insights: LearningInsights = {
      preferredContentTypes,
      averageSessionDuration: avgDuration,
      commonSubjects,
      frequentlyUsedSettings: adaptedDefaults,
      errorPatterns,
      improvementSuggestions: suggestions,
      adaptedDefaults
    };

    // Save learning data
    this.saveLearningData(insights, sessions.length, successfulSessions.length);
    
    return insights;
  }

  // Generate improvement suggestions based on user behavior
  private generateImprovementSuggestions(allSessions: SessionData[], successfulSessions: SessionData[]): string[] {
    const suggestions: string[] = [];
    
    const successRate = allSessions.length > 0 ? successfulSessions.length / allSessions.length : 0;
    const avgDuration = allSessions.reduce((sum, s) => sum + s.duration, 0) / allSessions.length;
    
    // Success rate suggestions
    if (successRate < 0.5) {
      suggestions.push("Consider using simpler content types initially to build confidence");
      suggestions.push("Try using the wizard mode for guided content creation");
    }
    
    // Duration-based suggestions
    if (avgDuration > 45) {
      suggestions.push("Consider breaking complex content into smaller, focused sessions");
      suggestions.push("Use saved settings to speed up the content creation process");
    }
    
    // Error pattern suggestions
    const commonErrors = this.analyzeCommonErrors(allSessions);
    if (commonErrors.includes('ai-configuration')) {
      suggestions.push("Configure your AI preferences in settings to avoid repeated setup");
    }
    
    if (commonErrors.includes('template-complexity')) {
      suggestions.push("Start with simpler templates and gradually explore advanced features");
    }
    
    // Content type suggestions
    const contentTypeVariety = new Set(allSessions.flatMap(s => s.contentTypes)).size;
    if (contentTypeVariety <= 2) {
      suggestions.push("Explore different content types to create more engaging learning experiences");
    }
    
    return suggestions;
  }

  // Analyze common error patterns
  private analyzeCommonErrors(sessions: SessionData[]): string[] {
    const errorCounts: Record<string, number> = {};
    
    sessions.forEach(session => {
      session.outcome.errorsEncountered.forEach(error => {
        // Categorize errors
        let category = 'general';
        if (error.includes('AI') || error.includes('ai')) category = 'ai-configuration';
        if (error.includes('template') || error.includes('Template')) category = 'template-complexity';
        if (error.includes('settings') || error.includes('Settings')) category = 'settings-issue';
        
        errorCounts[category] = (errorCounts[category] || 0) + 1;
      });
    });
    
    return Object.entries(errorCounts)
      .filter(([, count]) => count >= 2) // Only patterns that occur multiple times
      .sort(([,a], [,b]) => b - a)
      .map(([category]) => category);
  }

  // Suggest optimal duration based on usage patterns
  private suggestOptimalDuration(avgDuration: number): string {
    if (avgDuration <= 20) return '30 minutes';
    if (avgDuration <= 40) return '50 minutes';
    if (avgDuration <= 60) return '75 minutes';
    if (avgDuration <= 80) return '90 minutes';
    if (avgDuration <= 110) return '2 hours';
    return '3 hours';
  }

  // Save learning data
  private saveLearningData(insights: LearningInsights, totalSessions: number, successfulSessions: number): void {
    try {
      const learningData: CrossSessionLearningData = {
        totalSessions,
        successfulSessions,
        lastAnalyzed: new Date(),
        insights,
        behaviorPatterns: this.detectBehaviorPatterns()
      };
      
      localStorage.setItem(STORAGE_KEYS.LEARNING_DATA, JSON.stringify(learningData));
    } catch (error) {
      console.error('Failed to save learning data:', error);
    }
  }

  // Detect behavior patterns
  private detectBehaviorPatterns(): BehaviorPattern[] {
    const sessions = this.getSessionHistory();
    const patterns: BehaviorPattern[] = [];
    
    // Pattern: Consistent content type usage
    const contentTypeUsage = this.analyzeContentTypeConsistency(sessions);
    if (contentTypeUsage.consistency > 0.7) {
      patterns.push({
        pattern: 'consistent-content-types',
        frequency: contentTypeUsage.frequency,
        confidence: contentTypeUsage.consistency,
        recommendation: 'Consider exploring new content types to diversify your teaching materials',
        lastSeen: new Date()
      });
    }
    
    // Pattern: Session timing patterns
    const timingPattern = this.analyzeSessionTiming(sessions);
    if (timingPattern.confidence > 0.6) {
      patterns.push({
        pattern: 'optimal-session-timing',
        frequency: timingPattern.frequency,
        confidence: timingPattern.confidence,
        recommendation: `Your most productive sessions are around ${timingPattern.optimalDuration} minutes`,
        lastSeen: new Date()
      });
    }
    
    return patterns;
  }

  // Analyze content type consistency
  private analyzeContentTypeConsistency(sessions: SessionData[]): { consistency: number; frequency: number } {
    if (sessions.length < 3) return { consistency: 0, frequency: 0 };
    
    const contentTypeSets = sessions.map(s => new Set(s.contentTypes));
    const intersections = contentTypeSets.reduce((acc, set) => {
      return new Set([...acc].filter(x => set.has(x)));
    });
    
    const avgSetSize = contentTypeSets.reduce((sum, set) => sum + set.size, 0) / contentTypeSets.length;
    const consistency = intersections.size / avgSetSize;
    
    return {
      consistency,
      frequency: sessions.length
    };
  }

  // Analyze session timing patterns
  private analyzeSessionTiming(sessions: SessionData[]): { confidence: number; frequency: number; optimalDuration: number } {
    if (sessions.length < 5) return { confidence: 0, frequency: 0, optimalDuration: 0 };
    
    const successfulSessions = sessions.filter(s => s.outcome.completed && s.outcome.contentGenerated);
    const durations = successfulSessions.map(s => s.duration);
    
    if (durations.length === 0) return { confidence: 0, frequency: 0, optimalDuration: 0 };
    
    const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
    const variance = durations.reduce((sum, d) => sum + Math.pow(d - avgDuration, 2), 0) / durations.length;
    const standardDeviation = Math.sqrt(variance);
    
    // Lower variance indicates more consistent timing
    const consistency = Math.max(0, 1 - (standardDeviation / avgDuration));
    
    return {
      confidence: consistency,
      frequency: durations.length,
      optimalDuration: Math.round(avgDuration)
    };
  }

  // Get default insights for new users
  private getDefaultInsights(): LearningInsights {
    return {
      preferredContentTypes: ['Slides', 'InstructorNotes'],
      averageSessionDuration: 0,
      commonSubjects: [],
      frequentlyUsedSettings: {
        complexity: 'intermediate',
        duration: '50 minutes',
        contentTypes: ['Slides', 'InstructorNotes']
      },
      errorPatterns: [],
      improvementSuggestions: [
        'Start with the wizard mode for guided content creation',
        'Configure your teaching profile for personalized defaults',
        'Explore different content types to find what works best for you'
      ],
      adaptedDefaults: {
        complexity: 'intermediate',
        duration: '50 minutes',
        contentTypes: ['Slides', 'InstructorNotes']
      }
    };
  }

  // Get learning insights
  getLearningInsights(): LearningInsights {
    try {
      const learningDataJson = localStorage.getItem(STORAGE_KEYS.LEARNING_DATA);
      if (learningDataJson) {
        const learningData: CrossSessionLearningData = JSON.parse(learningDataJson);
        return learningData.insights;
      }
      return this.getDefaultInsights();
    } catch (error) {
      console.error('Failed to load learning insights:', error);
      return this.getDefaultInsights();
    }
  }

  // Get adapted defaults for new sessions
  getAdaptedDefaults(): Partial<ContentDefaults> {
    const insights = this.getLearningInsights();
    return insights.adaptedDefaults;
  }

  // Clear all learning data
  clearLearningData(): void {
    localStorage.removeItem(STORAGE_KEYS.LEARNING_DATA);
    localStorage.removeItem(STORAGE_KEYS.SESSION_ANALYTICS);
    localStorage.removeItem(STORAGE_KEYS.BEHAVIOR_PATTERNS);
    localStorage.removeItem('curriculum_curator_current_session');
  }

  // Get learning statistics
  getLearningStatistics(): CrossSessionLearningData | null {
    try {
      const learningDataJson = localStorage.getItem(STORAGE_KEYS.LEARNING_DATA);
      return learningDataJson ? JSON.parse(learningDataJson) : null;
    } catch (error) {
      console.error('Failed to load learning statistics:', error);
      return null;
    }
  }

  // Backup learning data
  exportLearningData(): string {
    const sessions = this.getSessionHistory();
    const learningData = this.getLearningStatistics();
    
    return JSON.stringify({
      sessions,
      learningData,
      exportDate: new Date().toISOString(),
      version: '1.0'
    }, null, 2);
  }

  // Import learning data
  importLearningData(dataJson: string): boolean {
    try {
      const data = JSON.parse(dataJson);
      
      if (data.sessions) {
        localStorage.setItem(STORAGE_KEYS.SESSION_ANALYTICS, JSON.stringify(data.sessions));
      }
      
      if (data.learningData) {
        localStorage.setItem(STORAGE_KEYS.LEARNING_DATA, JSON.stringify(data.learningData));
      }
      
      return true;
    } catch (error) {
      console.error('Failed to import learning data:', error);
      return false;
    }
  }
}

// Export singleton instance
export const crossSessionLearning = CrossSessionLearningManager.getInstance();