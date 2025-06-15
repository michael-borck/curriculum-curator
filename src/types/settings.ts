// Settings and User Profile Types

export interface UserProfile {
  id: string;
  name: string;
  email?: string;
  institution?: string;
  subject: string;
  level: EducationLevel;
  teachingStyle: TeachingStyle;
  aiPreference: AIIntegrationPreference;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserSettings {
  profile: UserProfile;
  defaults: ContentDefaults;
  preferences: UIPreferences;
  advanced: AdvancedSettings;
}

export interface ContentDefaults {
  duration: string;
  complexity: 'basic' | 'intermediate' | 'advanced';
  contentTypes: ContentType[];
  quizTypes: QuizType[];
  includeAnswerKeys: boolean;
  includeInstructorGuides: boolean;
  includeRubrics: boolean;
  includeAccessibilityFeatures: boolean;
  answerKeyOptions: AnswerKeyOptions;
  instructorGuideOptions: InstructorGuideOptions;
}

export interface AnswerKeyOptions {
  includeExplanations: boolean;
  includeDifficulty: boolean;
  includePoints: boolean;
}

export interface InstructorGuideOptions {
  includeTiming: boolean;
  includeGradingTips: boolean;
  includeDiscussionPrompts: boolean;
  includeExtensions: boolean;
}

export interface UIPreferences {
  formComplexity: 'essential' | 'enhanced' | 'advanced';
  showAdvancedOptions: boolean;
  autoSaveSettings: boolean;
  useSettingsByDefault: boolean;
  theme: 'light' | 'dark' | 'auto';
}

export interface AdvancedSettings {
  customContentTypes: CustomContentType[];
  customTemplates: CustomTemplate[];
  templatePreferences: TemplatePreferences;
  aiCustomization: AICustomizationSettings;
  exportSettings: ExportSettings;
}

// Education and Teaching Types
export type EducationLevel = 
  | 'elementary'
  | 'middle-school'
  | 'high-school'
  | 'college'
  | 'graduate'
  | 'professional'
  | 'adult-learning';

export type TeachingStyle = 
  | 'traditional-lecture'
  | 'constructivist'
  | 'direct-instruction'
  | 'inquiry-based'
  | 'flipped-classroom'
  | 'project-based'
  | 'competency-based'
  | 'culturally-responsive'
  | 'mixed-approach';

export type AIIntegrationPreference = 
  | 'ai-enhanced'
  | 'ai-resistant'
  | 'ai-literate'
  | 'mixed-approach'
  | 'context-dependent';

// Content Types
export type ContentType = 
  | 'Slides'
  | 'InstructorNotes'
  | 'Worksheet'
  | 'Quiz'
  | 'ActivityGuide'
  | 'Custom';

export type QuizType = 
  | 'multiple-choice'
  | 'true-false'
  | 'short-answer'
  | 'essay'
  | 'fill-in-blank'
  | 'matching'
  | 'custom';

export interface CustomContentType {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'assessment' | 'instructional' | 'activity' | 'reference' | 'other';
  defaultAIOptions: AIContentOptions;
  templateHints: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface TemplateVariable {
  name: string;
  type: 'text' | 'number' | 'boolean' | 'select' | 'textarea';
  label: string;
  description?: string;
  required: boolean;
  defaultValue?: any;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    errorMessage?: string;
  };
}

export interface ConditionalSection {
  id: string;
  name: string;
  condition: string;
  description: string;
}

export interface CustomTemplate {
  id: string;
  name: string;
  description: string;
  contentType: ContentType | string;
  category: 'standard' | 'assessment' | 'activity' | 'reference' | 'custom';
  template: string;
  variables: TemplateVariable[];
  conditionalSections: ConditionalSection[];
  customPrompts: {
    systemPrompt?: string;
    userPrompt?: string;
    contextPrompt?: string;
  };
  metadata: {
    author: string;
    version: string;
    tags: string[];
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    estimatedTime: number;
  };
  createdAt: Date;
  updatedAt: Date;
  isPublic: boolean;
  usageCount: number;
}

export interface TemplatePreferences {
  visualTheme: 'modern-clean' | 'academic-traditional' | 'creative-colorful' | 'minimalist';
  contentDepth: number; // 1-10 scale
  pacingStrategy: 'self-paced' | 'instructor-led' | 'mixed' | 'flexible';
  assessmentFocus: AssessmentFocus[];
}

export type AssessmentFocus = 
  | 'formative'
  | 'summative'
  | 'peer-assessment'
  | 'self-assessment';

export interface AICustomizationSettings {
  contentSpecificOptions: Record<ContentType, AIContentOptions>;
  promptCustomization: AIPromptSettings;
  resistanceStrategies: AIResistanceStrategy[];
}

export interface AIContentOptions {
  enableInteractionPrompts: boolean;
  includeBrainstormingActivities: boolean;
  suggestAITools: boolean;
  createResistantAlternatives: boolean;
  addLiteracyComponents: boolean;
}

export interface AIPromptSettings {
  customPrompts: Record<string, string>;
  promptStyle: 'concise' | 'detailed' | 'creative' | 'academic';
  includeExamples: boolean;
  adaptToAudience: boolean;
}

export type AIResistanceStrategy = 
  | 'process-focused'
  | 'authentic-context'
  | 'collaborative-elements'
  | 'real-time-components'
  | 'meta-cognitive'
  | 'hands-on-physical';

export interface ExportSettings {
  defaultFormat: 'pdf' | 'html' | 'markdown' | 'pptx';
  includeMetadata: boolean;
  brandingOptions: BrandingOptions;
  qualitySettings: QualitySettings;
}

export interface BrandingOptions {
  institutionName?: string;
  logo?: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
  fonts: {
    heading: string;
    body: string;
  };
}

export interface QualitySettings {
  imageResolution: 'low' | 'medium' | 'high' | 'ultra';
  compressionLevel: number; // 0-100
  includeSourceFiles: boolean;
  generateMultipleFormats: boolean;
}

// Teaching Style Detection Types
export interface TeachingStyleIndicators {
  interactionLevel: number; // 0-10
  structurePreference: number; // 0-10 (low = flexible, high = structured)
  studentCenteredApproach: number; // 0-10
  technologyIntegration: number; // 0-10
  assessmentFrequency: 'low' | 'medium' | 'high';
  collaborationEmphasis: number; // 0-10
}

export interface TeachingStyleDetectionResult {
  primaryStyle: TeachingStyle;
  secondaryStyle?: TeachingStyle;
  confidence: number; // 0-100
  indicators: TeachingStyleIndicators;
  recommendations: string[];
}

// Settings Storage Types
export interface SettingsStorageOptions {
  scope: 'global' | 'subject' | 'course' | 'session';
  autoSave: boolean;
  syncAcrossDevices?: boolean;
}

export interface SettingsValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}