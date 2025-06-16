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
  metadata?: Record<string, unknown>;
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

    // Store config for use during generation steps
    this.storeConfig(config);

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

    // Progress update interval
    const progressInterval = setInterval(() => {
      if (step.status === 'in_progress') {
        step.progress = Math.min(90, step.progress + Math.random() * 5);
        this.notifyProgress();
      }
    }, 1000);

    try {
      // Execute different types of steps
      const result = await this.executeStepLogic(step);

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

      return result;

    } catch (error) {
      clearInterval(progressInterval);
      
      step.status = 'error';
      step.errorMessage = error instanceof Error ? error.message : 'Unknown error';
      step.endTime = new Date();
      
      this.notifyProgress();
      throw error;
    }
  }

  // Execute the actual logic for different step types
  private async executeStepLogic(step: GenerationStep): Promise<{ files?: GeneratedFile[] }> {
    switch (step.id) {
      case 'validation':
        return await this.executeValidationStep();
      
      case 'objectives':
        return await this.executeObjectivesStep();
      
      case 'planning':
        return await this.executePlanningStep();
      
      default:
        if (step.id.startsWith('generate_')) {
          const contentType = step.id.replace('generate_', '') as ContentType;
          return await this.executeContentGenerationStep(contentType);
        } else if (step.id === 'answer_keys') {
          return await this.executeAnswerKeysStep();
        } else if (step.id === 'instructor_guides') {
          return await this.executeInstructorGuidesStep();
        } else if (step.id === 'rubrics') {
          return await this.executeRubricsStep();
        } else if (step.id === 'formatting') {
          return await this.executeFormattingStep();
        } else if (step.id === 'packaging') {
          return await this.executePackagingStep();
        }
        
        // Fallback for unknown steps
        await new Promise(resolve => setTimeout(resolve, 2000));
        return {};
    }
  }

  // Import the invoke function for Tauri commands
  private async invokeTauriCommand(command: string, args?: Record<string, unknown>): Promise<unknown> {
    // Import dynamically to avoid issues during SSR or when Tauri is not available
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      return await invoke(command, args);
    } catch {
      // Fallback for development or when Tauri is not available
      console.warn('Tauri not available, using mock data:', command, args);
      return this.getMockResponse(command, args);
    }
  }

  // Validation step - check inputs and system readiness
  private async executeValidationStep(): Promise<{ files?: GeneratedFile[] }> {
    // Check if we have a working LLM provider
    const providers = await this.invokeTauriCommand('get_available_providers');
    const availableProvider = (providers as Array<{ status: string }>).find(p => p.status === 'available');
    
    if (!availableProvider) {
      throw new Error('No LLM provider available. Please configure Ollama or add API keys for external providers.');
    }

    // Test LLM connectivity
    const healthCheck = await this.invokeTauriCommand('test_llm_generation', {
      prompt: 'Test connection',
      model: null,
      temperature: 0.1
    });

    if (!healthCheck.success) {
      throw new Error(`LLM provider test failed: ${healthCheck.error || 'Unknown error'}`);
    }

    return {};
  }

  // Learning objectives analysis step
  private async executeObjectivesStep(): Promise<{ files?: GeneratedFile[] }> {
    // Use LLM to analyze and enhance learning objectives if needed
    const config = this.getCurrentConfig();
    if (!config) throw new Error('No generation config available');

    const objectivesPrompt = `Analyze these learning objectives for educational alignment:

Topic: ${config.topic}
Audience: ${config.audience}
Duration: ${config.duration}
Complexity: ${config.complexity}

Learning Objectives:
${config.learningObjectives.map((obj, i) => `${i + 1}. ${obj}`).join('\n')}

Please verify these objectives are:
1. Specific and measurable
2. Appropriate for the audience level
3. Achievable within the given timeframe
4. Aligned with Bloom's Taxonomy

Provide brief feedback and suggest improvements if needed.`;

    const response = await this.invokeTauriCommand('test_llm_generation', {
      prompt: objectivesPrompt,
      temperature: 0.3
    });

    if (!response.success) {
      throw new Error(`Objectives analysis failed: ${response.error}`);
    }

    return {};
  }

  // Content structure planning step
  private async executePlanningStep(): Promise<{ files?: GeneratedFile[] }> {
    const config = this.getCurrentConfig();
    if (!config) throw new Error('No generation config available');

    const planningPrompt = `Create a content structure plan for this educational material:

Topic: ${config.topic}
Audience: ${config.audience}
Duration: ${config.duration}
Complexity: ${config.complexity}

Learning Objectives:
${config.learningObjectives.map((obj, i) => `${i + 1}. ${obj}`).join('\n')}

Content Types to Generate: ${config.contentTypes.join(', ')}

Please outline:
1. Content flow and sequence
2. Key concepts to cover
3. Pedagogical approach recommendations
4. Assessment strategy

Keep it concise and focused.`;

    const response = await this.invokeTauriCommand('test_llm_generation', {
      prompt: planningPrompt,
      temperature: 0.4
    });

    if (!response.success) {
      throw new Error(`Planning step failed: ${response.error}`);
    }

    return {};
  }

  // Content generation step for specific content types
  private async executeContentGenerationStep(contentType: ContentType): Promise<{ files?: GeneratedFile[] }> {
    const config = this.getCurrentConfig();
    if (!config) throw new Error('No generation config available');

    const prompt = this.buildContentPrompt(contentType, config);
    
    const response = await this.invokeTauriCommand('test_llm_generation', {
      prompt,
      temperature: 0.6,
      maxTokens: 2000
    });

    if (!response.success) {
      throw new Error(`${contentType} generation failed: ${response.error}`);
    }

    // Create the generated file
    const file: GeneratedFile = {
      id: crypto.randomUUID(),
      name: `${contentType.toLowerCase().replace(/\s+/g, '_')}.md`,
      type: contentType,
      content: response.content || `# ${contentType}\n\nContent generation in progress...`,
      format: 'markdown' as const,
      size: (response.content || '').length,
      generatedAt: new Date(),
      metadata: {
        model_used: response.model_used,
        tokens_used: response.tokens_used,
        generation_time_ms: response.response_time_ms,
        cost_usd: response.cost_usd
      }
    };

    return { files: [file] };
  }

  // Build content-specific prompts
  private buildContentPrompt(contentType: ContentType, config: GenerationConfig): string {
    const baseContext = `Topic: ${config.topic}
Audience: ${config.audience}
Duration: ${config.duration}
Complexity Level: ${config.complexity}

Learning Objectives:
${config.learningObjectives.map((obj, i) => `${i + 1}. ${obj}`).join('\n')}`;

    const prompts: Record<ContentType, string> = {
      'Slides': `Create presentation slides for this topic:

${baseContext}

Generate a structured slide presentation with:
- Title slide
- Learning objectives slide
- 8-12 content slides with clear headings
- Activity/discussion slides
- Summary/conclusion slide

Format as markdown with slide breaks (---). Include speaker notes where helpful.`,

      'InstructorNotes': `Create comprehensive instructor notes for this lesson:

${baseContext}

Include:
- Lesson preparation checklist
- Timing guidance for each section
- Teaching tips and common student misconceptions
- Discussion prompts and facilitation guidance
- Assessment strategies
- Additional resources

Format as detailed markdown documentation.`,

      'Worksheet': `Create a student worksheet for this topic:

${baseContext}

Design a worksheet with:
- Clear instructions
- Varied exercise types (short answer, problem-solving, analysis)
- Progressive difficulty
- Space for student responses
- Extension activities for advanced learners

Format as markdown with clear section breaks.`,

      'Quiz': `Create an assessment quiz for this topic:

${baseContext}

Quiz Types to Include: ${config.quizTypes.join(', ')}

Generate:
- 10-15 questions of varied types and difficulty
- Clear instructions
- Point values for each question
- ${config.additionalOptions.includeAnswerKeys ? 'Answer key with explanations' : 'Questions only'}

Format as structured markdown.`,

      'ActivityGuide': `Create an activity guide for this topic:

${baseContext}

Design engaging activities including:
- Group exercises
- Hands-on activities
- Discussion prompts
- Problem-solving scenarios
- Real-world applications

Include timing, materials needed, and facilitation tips.`,

      'Custom': `Create custom educational content for this topic:

${baseContext}

Generate comprehensive educational material that covers the learning objectives effectively for the specified audience and timeframe.`
    };

    return prompts[contentType] || prompts['Custom'];
  }

  // Answer keys generation step
  private async executeAnswerKeysStep(): Promise<{ files?: GeneratedFile[] }> {
    const config = this.getCurrentConfig();
    if (!config || !config.contentTypes.includes('Quiz')) {
      return {};
    }

    const prompt = `Create detailed answer keys for the quiz content:

${this.buildContentPrompt('Quiz', config)}

For each question, provide:
- Correct answer
- Detailed explanation
- Common misconceptions to address
- Difficulty level (Easy/Medium/Hard)
- Learning objective alignment

Format as structured markdown.`;

    const response = await this.invokeTauriCommand('test_llm_generation', {
      prompt,
      temperature: 0.3
    });

    if (!response.success) {
      throw new Error(`Answer keys generation failed: ${response.error}`);
    }

    const file: GeneratedFile = {
      id: crypto.randomUUID(),
      name: 'quiz_answer_keys.md',
      type: 'Quiz',
      content: response.content || '# Answer Keys\n\nGeneration in progress...',
      format: 'markdown' as const,
      size: (response.content || '').length,
      generatedAt: new Date()
    };

    return { files: [file] };
  }

  // Instructor guides step
  private async executeInstructorGuidesStep(): Promise<{ files?: GeneratedFile[] }> {
    const config = this.getCurrentConfig();
    if (!config) throw new Error('No generation config available');

    const prompt = `Create comprehensive instructor guides for this lesson:

${this.buildContentPrompt('InstructorNotes', config)}

Additional focus on:
- Class management strategies
- Technology integration tips
- Differentiation for diverse learners
- Assessment rubrics
- Follow-up activities

Format as detailed instructor documentation.`;

    const response = await this.invokeTauriCommand('test_llm_generation', {
      prompt,
      temperature: 0.4
    });

    if (!response.success) {
      throw new Error(`Instructor guides generation failed: ${response.error}`);
    }

    const file: GeneratedFile = {
      id: crypto.randomUUID(),
      name: 'instructor_guides.md',
      type: 'InstructorNotes',
      content: response.content || '# Instructor Guides\n\nGeneration in progress...',
      format: 'markdown' as const,
      size: (response.content || '').length,
      generatedAt: new Date()
    };

    return { files: [file] };
  }

  // Rubrics generation step
  private async executeRubricsStep(): Promise<{ files?: GeneratedFile[] }> {
    const config = this.getCurrentConfig();
    if (!config) throw new Error('No generation config available');

    const prompt = `Create assessment rubrics for this educational content:

${this.buildContentPrompt('Custom', config)}

Generate rubrics for:
- Learning objective achievement
- Participation and engagement
- Assignment quality
- ${config.contentTypes.includes('Quiz') ? 'Quiz performance levels' : ''}

Use 4-point scale (Excellent, Good, Satisfactory, Needs Improvement) with clear criteria.`;

    const response = await this.invokeTauriCommand('test_llm_generation', {
      prompt,
      temperature: 0.3
    });

    if (!response.success) {
      throw new Error(`Rubrics generation failed: ${response.error}`);
    }

    const file: GeneratedFile = {
      id: crypto.randomUUID(),
      name: 'assessment_rubrics.md',
      type: 'Custom',
      content: response.content || '# Assessment Rubrics\n\nGeneration in progress...',
      format: 'markdown' as const,
      size: (response.content || '').length,
      generatedAt: new Date()
    };

    return { files: [file] };
  }

  // Formatting step - final content review and formatting
  private async executeFormattingStep(): Promise<{ files?: GeneratedFile[] }> {
    // This step would apply final formatting, spell-check, and quality review
    // For now, just a delay to simulate processing
    await new Promise(resolve => setTimeout(resolve, 3000));
    return {};
  }

  // Packaging step - prepare downloads and metadata
  private async executePackagingStep(): Promise<{ files?: GeneratedFile[] }> {
    // This step would package files for download, generate metadata, etc.
    // For now, just a delay to simulate processing
    await new Promise(resolve => setTimeout(resolve, 2000));
    return {};
  }

  // Get current generation config (stored during generation start)
  private getCurrentConfig(): GenerationConfig | null {
    // This would be stored when generation starts
    // For now, return null to indicate no config available
    return (this as GenerationManager & { _currentConfig?: GenerationConfig })._currentConfig || null;
  }

  // Store config for use during generation
  private storeConfig(config: GenerationConfig): void {
    (this as GenerationManager & { _currentConfig?: GenerationConfig })._currentConfig = config;
  }

  // Mock response for development when Tauri is not available
  private getMockResponse(command: string, args?: Record<string, unknown>): unknown {
    switch (command) {
      case 'get_available_providers':
        return [
          {
            id: 'ollama',
            name: 'Local Ollama',
            type: 'Ollama',
            is_local: true,
            requires_api_key: false,
            status: 'available'
          }
        ];
      
      case 'test_llm_generation':
        return {
          success: true,
          content: `Mock response for: ${args?.prompt?.substring(0, 100)}...`,
          model_used: 'mock-model',
          tokens_used: { prompt_tokens: 50, completion_tokens: 100, total_tokens: 150 },
          response_time_ms: 1500,
          cost_usd: 0.001
        };
      
      default:
        return { success: true, data: 'mock response' };
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