# Tauri Implementation Concepts Extraction

## Overview
This document extracts key concepts from the Tauri implementation that should be adapted for the FastHTML curriculum curator.

## 1. Teaching Philosophies & Styles

### Teaching Styles (from `settings.ts`)
- **traditional-lecture**: High structure, low interaction, teacher-centered
- **constructivist**: Student builds knowledge through exploration
- **direct-instruction**: Clear, step-by-step teaching with guided practice
- **inquiry-based**: Question-driven investigation and discovery
- **flipped-classroom**: Pre-class content with in-class application
- **project-based**: Real-world project scenarios with collaboration
- **competency-based**: Focus on skill mastery and assessment
- **culturally-responsive**: High interaction, culturally aware approach
- **mixed-approach**: Balanced combination of styles

### Teaching Style Indicators
- **interactionLevel** (0-10): Amount of student-teacher interaction
- **structurePreference** (0-10): Low = flexible, High = structured
- **studentCenteredApproach** (0-10): How much focus on student agency
- **technologyIntegration** (0-10): Use of digital tools
- **assessmentFrequency**: low/medium/high
- **collaborationEmphasis** (0-10): Group work emphasis

### Teaching Style Detection System
- 5-question wizard to detect teaching style
- Questions cover:
  - Classroom structure preferences
  - Student interaction levels
  - Technology integration
  - Assessment approaches
  - Learning methodologies
- Algorithm matches responses to teaching styles with confidence scores
- Provides personalized recommendations

## 2. UI Modes & Workflows

### Wizard Mode
- **Step-by-step guided interface**:
  1. Topic & Audience (topic, audience, duration)
  2. Learning Objectives (addable/removable list)
  3. Content Selection (visual cards for content types)
  4. Configuration (complexity, teaching style, options)
  5. Review & Generate

- **Features**:
  - Progress bar showing current step
  - Validation before proceeding
  - Visual content type selection with icons
  - Summary review before generation

### Expert Mode
- **Single-page power user interface**:
  - All options visible at once
  - Tabbed interface: Planner | Workflow | Batch | Quality
  - Advanced AI customization options
  - Batch generation capabilities
  - Custom prompt editing
  - Template selection

### Content Types
- **Slides**: Presentation slides with key points
- **InstructorNotes**: Detailed teaching notes and talking points
- **Worksheet**: Student practice exercises and problems
- **Quiz**: Assessment questions with answer keys
- **ActivityGuide**: Interactive learning activities and group work
- **Custom**: User-defined content types

## 3. Content Generation Pipeline

### Generation Configuration
```typescript
interface GenerationConfig {
  topic: string;
  audience: string;
  subject: string;
  duration: string;
  complexity: 'basic' | 'intermediate' | 'advanced';
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
```

### Generation Steps
1. **Planning Phase**: Collect requirements, objectives
2. **Context Building**: Combine user input with teaching style
3. **Prompt Construction**: Build LLM prompts based on configuration
4. **Content Generation**: Stream responses from LLM
5. **Validation**: Check content quality and completeness
6. **Enhancement**: Apply teaching style adaptations
7. **Export**: Generate files in requested formats

### Progress Tracking
- Real-time progress indicators
- Step-by-step status updates
- Error handling with retry capabilities
- Ability to cancel/pause generation

## 4. AI Integration Features

### AI Customization Settings
- **Content-specific AI options** per content type
- **Prompt customization** with style selection
- **AI resistance strategies** for creating non-AI-detectable content
- **AI literacy components** for teaching about AI

### AI Enhancement Options
- Enable interaction prompts
- Include brainstorming activities
- Suggest AI tools for students
- Create resistant alternatives
- Add literacy components

## 5. Advanced Features

### Cross-Session Learning
- Tracks user preferences across sessions
- Learns from usage patterns
- Adapts defaults based on behavior
- Provides improvement suggestions
- Stores insights about:
  - Preferred content types
  - Average session duration
  - Common subjects
  - Frequently used settings
  - Error patterns

### Batch Generation
- Generate multiple lessons at once
- Course-wide content planning
- Consistent styling across materials
- Progress tracking for batch operations

### Template System
- Pre-built templates per content type
- Custom template creation
- Template variables and conditionals
- Version control for templates
- Public template sharing

### Quality Assurance
- Built-in content validators
- Readability checks
- Alignment verification
- Grammar and style checking
- Accessibility compliance

## 6. User Settings & Preferences

### Content Defaults
- Duration preferences
- Complexity levels
- Default content types
- Quiz type preferences
- Include options (answer keys, guides, rubrics)
- Accessibility features

### UI Preferences
- Form complexity levels (essential/enhanced/advanced)
- Auto-save settings
- Theme selection
- Default mode (wizard/expert)

### Advanced Settings
- Custom content types
- Custom templates
- AI customization
- Export preferences
- Branding options

## 7. Export & Integration

### Export Formats
- PDF with styling
- HTML with interactivity
- Markdown for editing
- PowerPoint presentations
- Word documents
- LaTeX for academic use

### Branding Options
- Institution name and logo
- Custom colors and fonts
- Quality settings
- Metadata inclusion

## Implementation Priority for FastHTML

### Phase 1: Core Features
1. Basic wizard mode with step-by-step flow
2. Essential content types (Slides, Worksheet, Quiz)
3. Simple teaching style selection
4. Basic LLM integration

### Phase 2: Enhanced Features
1. Teaching style detection wizard
2. Expert mode interface
3. Cross-session learning
4. Advanced content types

### Phase 3: Advanced Features
1. Batch generation
2. Custom templates
3. Full AI customization
4. Quality assurance system

### Phase 4: Polish & Integration
1. Export system with multiple formats
2. Branding and customization
3. Public template sharing
4. Analytics and insights