// Content Generation Manager with Progress Tracking

import type { ContentType, QuizType } from '../types/settings';
import type { GenerationStep, GenerationProgress } from '../components/ProgressIndicator';
import { crossSessionLearning } from './crossSessionLearning';

export interface GenerationConfig {
  topic: string;
  audience: string;
  subject: string;
  duration: string;
  complexity: string;
  learningObjectives: string[];
  contentTypes: ContentType[];
  quizTypes: QuizType[];
  additionalOptions: {
    includeAnswerKeys: boolean;
    includeInstructorGuides: boolean;
    accessibility: boolean;
    rubrics: boolean;
    extensions: boolean;
  };
}

export interface GenerationResult {
  success: boolean;
  contentFiles: GeneratedFile[];
  errors: GenerationError[];
  metadata: {
    generationId: string;
    startTime: Date;
    endTime: Date;
    totalDuration: number;
    config: GenerationConfig;
  };
}

export interface GeneratedFile {
  id: string;
  name: string;
  type: ContentType;
  content: string;
  format: 'markdown' | 'html' | 'json';
  size: number;
  generatedAt: Date;
  metadata?: Record<string, any>;
}

export interface GenerationError {
  stepId: string;
  type: 'network' | 'validation' | 'processing' | 'timeout' | 'ai_service';
  message: string;
  details?: string;
  timestamp: Date;
  retryable: boolean;
}

type ProgressCallback = (progress: GenerationProgress) => void;
type ErrorCallback = (error: GenerationError) => void;

export class GenerationManager {
  private static instance: GenerationManager;
  private currentGeneration: GenerationProgress | null = null;
  private progressCallback: ProgressCallback | null = null;
  private errorCallback: ErrorCallback | null = null;
  private abortController: AbortController | null = null;

  static getInstance(): GenerationManager {
    if (!GenerationManager.instance) {
      GenerationManager.instance = new GenerationManager();
    }
    return GenerationManager.instance;
  }

  // Start content generation
  async startGeneration(
    config: GenerationConfig,
    onProgress?: ProgressCallback,
    onError?: ErrorCallback
  ): Promise<GenerationResult> {
    this.progressCallback = onProgress || null;
    this.errorCallback = onError || null;
    this.abortController = new AbortController();

    // Track generation start
    crossSessionLearning.trackInteraction({
      type: 'content_generated',
      data: {
        contentTypes: config.contentTypes,
        complexity: config.complexity,
        generationStarted: true
      }
    });

    const generationId = crypto.randomUUID();
    const startTime = new Date();

    // Initialize progress
    const steps = this.createGenerationSteps(config);
    const estimatedTotalTime = this.calculateEstimatedTime(config);

    this.currentGeneration = {
      currentStep: 0,
      totalSteps: steps.length,
      overallProgress: 0,
      steps,
      startTime,
      estimatedTotalTime,
      elapsedTime: 0,
      remainingTime: estimatedTotalTime
    };

    this.notifyProgress();

    try {
      // Start progress timer
      const progressTimer = setInterval(() => {
        if (this.currentGeneration) {
          this.currentGeneration.elapsedTime = (Date.now() - startTime.getTime()) / 1000;
          this.currentGeneration.remainingTime = Math.max(0, 
            this.currentGeneration.estimatedTotalTime - this.currentGeneration.elapsedTime
          );
          this.notifyProgress();
        }
      }, 1000);

      // Execute generation steps
      const result = await this.executeGeneration(config, generationId);

      clearInterval(progressTimer);
      
      // Final progress update
      if (this.currentGeneration) {
        this.currentGeneration.overallProgress = 100;
        this.currentGeneration.elapsedTime = (Date.now() - startTime.getTime()) / 1000;
        this.currentGeneration.remainingTime = 0;
        this.notifyProgress();
      }

      return result;

    } catch (error) {
      const generationError: GenerationError = {
        stepId: 'generation',
        type: 'processing',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        timestamp: new Date(),
        retryable: true
      };

      this.errorCallback?.(generationError);
      
      return {
        success: false,
        contentFiles: [],
        errors: [generationError],
        metadata: {
          generationId,
          startTime,
          endTime: new Date(),
          totalDuration: (Date.now() - startTime.getTime()) / 1000,
          config
        }
      };
    }
  }

  // Cancel current generation
  cancelGeneration(): void {
    if (this.abortController) {
      this.abortController.abort();
    }
    
    if (this.currentGeneration) {
      this.currentGeneration.steps.forEach(step => {
        if (step.status === 'in_progress' || step.status === 'pending') {
          step.status = 'error';
          step.errorMessage = 'Generation cancelled by user';
        }
      });
      this.notifyProgress();
    }

    // Track cancellation
    crossSessionLearning.trackInteraction({
      type: 'error_encountered',
      data: { type: 'user_cancelled', step: 'generation' }
    });
  }

  // Retry a specific step
  async retryStep(stepId: string): Promise<void> {
    if (!this.currentGeneration) return;

    const step = this.currentGeneration.steps.find(s => s.id === stepId);
    if (!step) return;

    step.status = 'pending';
    step.progress = 0;
    step.errorMessage = undefined;
    
    this.notifyProgress();

    try {
      await this.executeStep(step);
    } catch (error) {
      step.status = 'error';
      step.errorMessage = error instanceof Error ? error.message : 'Retry failed';
      this.notifyProgress();
    }
  }

  // Create generation steps based on config
  private createGenerationSteps(config: GenerationConfig): GenerationStep[] {
    const steps: GenerationStep[] = [];

    // Step 1: Validation and Setup
    steps.push({
      id: 'validation',
      name: 'Validating Configuration',
      description: 'Checking inputs and preparing generation pipeline',
      status: 'pending',
      progress: 0,
      estimatedTime: 5
    });

    // Step 2: Learning Objectives Analysis
    steps.push({
      id: 'objectives',
      name: 'Analyzing Learning Objectives',
      description: 'Processing educational goals and alignment requirements',
      status: 'pending',
      progress: 0,
      estimatedTime: 10
    });

    // Step 3: Content Structure Planning
    steps.push({
      id: 'planning',
      name: 'Planning Content Structure',
      description: 'Organizing content flow and pedagogical approach',
      status: 'pending',
      progress: 0,
      estimatedTime: 15
    });

    // Steps for each content type
    config.contentTypes.forEach(contentType => {
      const estimatedTime = this.getContentTypeEstimatedTime(contentType, config.complexity);
      
      steps.push({
        id: `generate_${contentType.toLowerCase()}`,
        name: `Generating ${contentType}`,
        description: this.getContentTypeDescription(contentType),
        status: 'pending',
        progress: 0,
        estimatedTime
      });
    });

    // Additional content steps
    if (config.additionalOptions.includeAnswerKeys && config.contentTypes.includes('Quiz')) {
      steps.push({
        id: 'answer_keys',
        name: 'Creating Answer Keys',
        description: 'Generating detailed answer explanations and grading guides',
        status: 'pending',
        progress: 0,
        estimatedTime: 15
      });
    }

    if (config.additionalOptions.includeInstructorGuides) {
      steps.push({
        id: 'instructor_guides',
        name: 'Creating Instructor Guides',
        description: 'Developing teaching notes and facilitation guidelines',
        status: 'pending',
        progress: 0,
        estimatedTime: 20
      });
    }

    if (config.additionalOptions.rubrics) {
      steps.push({
        id: 'rubrics',
        name: 'Generating Assessment Rubrics',
        description: 'Creating evaluation criteria and performance indicators',
        status: 'pending',
        progress: 0,
        estimatedTime: 10
      });
    }

    // Final steps
    steps.push({
      id: 'formatting',
      name: 'Formatting and Review',
      description: 'Applying final formatting and quality checks',
      status: 'pending',
      progress: 0,
      estimatedTime: 10
    });

    steps.push({
      id: 'packaging',
      name: 'Preparing Downloads',
      description: 'Packaging files and generating metadata',
      status: 'pending',
      progress: 0,
      estimatedTime: 5
    });

    return steps;
  }

  // Execute the generation process
  private async executeGeneration(config: GenerationConfig, generationId: string): Promise<GenerationResult> {
    const contentFiles: GeneratedFile[] = [];
    const errors: GenerationError[] = [];
    const startTime = new Date();

    for (let i = 0; i < this.currentGeneration!.steps.length; i++) {
      const step = this.currentGeneration!.steps[i];
      
      this.currentGeneration!.currentStep = i + 1;
      this.updateOverallProgress();
      
      try {
        const stepResult = await this.executeStep(step);
        
        if (stepResult && stepResult.files) {
          contentFiles.push(...stepResult.files);
        }
        
      } catch (error) {
        const generationError: GenerationError = {
          stepId: step.id,
          type: 'processing',
          message: error instanceof Error ? error.message : 'Step execution failed',
          timestamp: new Date(),
          retryable: true
        };
        
        errors.push(generationError);
        this.errorCallback?.(generationError);
      }

      // Check for cancellation
      if (this.abortController?.signal.aborted) {
        throw new Error('Generation cancelled');
      }
    }

    return {
      success: errors.length === 0,
      contentFiles,
      errors,
      metadata: {
        generationId,
        startTime,
        endTime: new Date(),
        totalDuration: (Date.now() - startTime.getTime()) / 1000,
        config
      }
    };
  }

  // Execute a single generation step
  private async executeStep(step: GenerationStep): Promise<{ files?: GeneratedFile[] }> {
    step.status = 'in_progress';
    step.startTime = new Date();
    step.progress = 0;
    
    this.notifyProgress();

    // Simulate step execution with progress updates
    const progressInterval = setInterval(() => {
      if (step.status === 'in_progress') {
        step.progress = Math.min(90, step.progress + Math.random() * 10);
        this.notifyProgress();
      }
    }, 500);

    try {
      // Simulate actual generation time
      const duration = (step.estimatedTime || 10) * 1000;
      await new Promise(resolve => setTimeout(resolve, duration));

      // Check for cancellation
      if (this.abortController?.signal.aborted) {
        throw new Error('Cancelled');
      }

      clearInterval(progressInterval);
      
      step.status = 'completed';
      step.progress = 100;
      step.endTime = new Date();
      
      // Add completion details
      step.details = this.getStepCompletionDetails(step.id);
      
      this.notifyProgress();

      // Return mock generated files for content generation steps
      if (step.id.startsWith('generate_')) {
        const contentType = step.id.replace('generate_', '') as ContentType;
        return {
          files: [{
            id: crypto.randomUUID(),
            name: `${contentType.toLowerCase()}.md`,
            type: contentType,
            content: `# Generated ${contentType}\n\nContent would be here...`,
            format: 'markdown' as const,
            size: 1024,
            generatedAt: new Date()
          }]
        };
      }

      return {};

    } catch (error) {
      clearInterval(progressInterval);
      
      step.status = 'error';
      step.errorMessage = error instanceof Error ? error.message : 'Unknown error';
      step.endTime = new Date();
      
      this.notifyProgress();
      throw error;
    }
  }

  // Calculate estimated total time
  private calculateEstimatedTime(config: GenerationConfig): number {
    let baseTime = 45; // Base setup time
    
    // Add time for each content type
    config.contentTypes.forEach(type => {
      baseTime += this.getContentTypeEstimatedTime(type, config.complexity);
    });

    // Add time for additional options
    if (config.additionalOptions.includeAnswerKeys) baseTime += 15;
    if (config.additionalOptions.includeInstructorGuides) baseTime += 20;
    if (config.additionalOptions.rubrics) baseTime += 10;
    if (config.additionalOptions.accessibility) baseTime += 5;

    // Complexity multiplier
    const complexityMultiplier = config.complexity === 'advanced' ? 1.5 : 
                                config.complexity === 'basic' ? 0.8 : 1.0;

    return Math.round(baseTime * complexityMultiplier);
  }

  // Get estimated time for content type
  private getContentTypeEstimatedTime(contentType: ContentType, complexity: string): number {
    const baseTimes: Record<ContentType, number> = {
      'Slides': 25,
      'InstructorNotes': 20,
      'Worksheet': 30,
      'Quiz': 35,
      'ActivityGuide': 25,
      'Custom': 20
    };

    const complexityMultiplier = complexity === 'advanced' ? 1.4 : 
                                complexity === 'basic' ? 0.7 : 1.0;

    return Math.round((baseTimes[contentType] || 20) * complexityMultiplier);
  }

  // Get content type description
  private getContentTypeDescription(contentType: ContentType): string {
    const descriptions: Record<ContentType, string> = {
      'Slides': 'Creating presentation slides with engaging content and visuals',
      'InstructorNotes': 'Developing comprehensive teaching notes and guidance',
      'Worksheet': 'Generating practice exercises and learning activities',
      'Quiz': 'Creating assessment questions with varied difficulty levels',
      'ActivityGuide': 'Designing interactive activities and group exercises',
      'Custom': 'Generating custom content based on your specifications'
    };

    return descriptions[contentType] || 'Generating content';
  }

  // Get step completion details
  private getStepCompletionDetails(stepId: string): string[] {
    const details: Record<string, string[]> = {
      'validation': [
        'Input validation completed',
        'Content requirements verified',
        'Generation pipeline initialized'
      ],
      'objectives': [
        'Learning objectives analyzed',
        'Bloom\'s taxonomy alignment checked',
        'Assessment strategy determined'
      ],
      'planning': [
        'Content structure outlined',
        'Pedagogical approach selected',
        'Resource requirements identified'
      ]
    };

    return details[stepId] || ['Step completed successfully'];
  }

  // Update overall progress
  private updateOverallProgress(): void {
    if (!this.currentGeneration) return;

    const completedSteps = this.currentGeneration.steps.filter(s => s.status === 'completed').length;
    const currentStepProgress = this.currentGeneration.steps[this.currentGeneration.currentStep - 1]?.progress || 0;
    
    const baseProgress = (completedSteps / this.currentGeneration.totalSteps) * 100;
    const currentStepContribution = (currentStepProgress / 100) * (1 / this.currentGeneration.totalSteps) * 100;
    
    this.currentGeneration.overallProgress = Math.min(100, baseProgress + currentStepContribution);
  }

  // Notify progress callback
  private notifyProgress(): void {
    if (this.currentGeneration && this.progressCallback) {
      this.progressCallback({ ...this.currentGeneration });
    }
  }

  // Get current generation progress
  getCurrentProgress(): GenerationProgress | null {
    return this.currentGeneration ? { ...this.currentGeneration } : null;
  }

  // Check if generation is in progress
  isGenerating(): boolean {
    return this.currentGeneration !== null && 
           this.currentGeneration.steps.some(s => s.status === 'in_progress' || s.status === 'pending');
  }
}

// Export singleton instance
export const generationManager = GenerationManager.getInstance();