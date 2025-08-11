# UI/UX Redesign Plan

## Current State Issues
- Single-page upload → analyze flow is too limiting
- No user context or course management
- Missing guided workflows for content creation
- No teaching philosophy integration
- Limited to analysis rather than creation

## Proposed New User Flow

### 1. Landing Page
```
[Curriculum Curator Logo]

Welcome to Curriculum Curator
Your AI-powered course creation assistant

[Login] [Register] [Learn More]

Features:
✓ Create complete courses from scratch
✓ Import and enhance existing materials  
✓ Generate lectures, worksheets, labs, and more
✓ Customized to your teaching style
✓ Multi-course management
```

### 2. Dashboard (After Login)
```
Welcome back, [Name]!

My Courses                                    [+ New Course]
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ CS101           │ │ CS202           │ │ + Create New    │
│ Intro to Python │ │ Data Structures │ │                 │
│ ████████░░ 80%  │ │ ████░░░░░░ 40%  │ │                 │
│ [Continue]      │ │ [Continue]      │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘

Recent Activity:
• Generated Week 3 materials for CS101
• Updated syllabus for CS202
• Created new worksheet: "Recursion Practice"

Quick Actions:
[Upload Materials] [Generate Content] [My Templates]
```

### 3. Course Creation Wizard
```
Step 1: Basic Information
┌──────────────────────────────────┐
│ Let's create your course         │
│                                  │
│ Course Title: [_______________]  │
│ Course Code:  [_______________]  │
│ Semester:     [Fall 2024    ▼]  │
│                                  │
│ Teaching Style:                  │
│ ○ Traditional Lecture           │
│ ● Flipped Classroom            │
│ ○ Project-Based Learning       │
│ ○ Socratic Method              │
│                                  │
│ [Back] [Next: Schedule →]       │
└──────────────────────────────────┘
```

### 4. Content Generation Interface
```
Generate: Lecture Materials                Week 3: Functions & Modules

┌─ Planning ──────────────────────────┐ ┌─ Preview ────────────────┐
│ Based on your course structure,     │ │ [Live preview of         │
│ here's what I'll create:           │ │  generated content]      │
│                                    │ │                          │
│ ✓ Learning Objectives (3)          │ │                          │
│ ✓ Lecture Slides (15-20)          │ │                          │
│ ✓ Code Examples (5)               │ │                          │
│ ✓ In-class Activities (2)         │ │                          │
│ ✓ Homework Assignment             │ │                          │
│                                    │ │                          │
│ Context:                           │ │                          │
│ • Previous: Variables & Types      │ │                          │
│ • Next: Object-Oriented Basics     │ │                          │
│                                    │ │                          │
│ Additional Requirements:           │ │                          │
│ [_____________________________]    │ │                          │
│                                    │ │                          │
│ [Generate] [Modify Plan]           │ │ [Accept] [Regenerate]    │
└─────────────────────────────────────┘ └──────────────────────────┘
```

## Key UI Components to Build

### 1. Navigation Component
```python
# components/navigation.py
def Navigation(user, current_page):
    return Nav(
        Div(
            A("Curriculum Curator", href="/", cls="logo"),
            cls="nav-brand"
        ),
        Div(
            A("Dashboard", href="/dashboard", 
              cls="active" if current_page == "dashboard" else ""),
            A("My Courses", href="/courses"),
            A("Templates", href="/templates"),
            A("Settings", href="/settings"),
            cls="nav-links"
        ),
        Div(
            Span(f"Hello, {user.name}"),
            A("Logout", href="/logout", cls="btn-secondary"),
            cls="nav-user"
        ),
        cls="navigation"
    )
```

### 2. Course Card Component
```python
# components/course_card.py
def CourseCard(course):
    progress = calculate_progress(course)
    return Div(
        Div(
            H3(course.code, cls="course-code"),
            H4(course.title, cls="course-title"),
            cls="course-header"
        ),
        Div(
            ProgressBar(progress),
            Span(f"{progress}% Complete", cls="progress-text"),
            cls="course-progress"
        ),
        Div(
            Span(f"{course.weeks_completed}/{course.total_weeks} weeks"),
            Span(f"• {course.materials_count} materials"),
            cls="course-stats"
        ),
        Div(
            A("Continue", href=f"/course/{course.id}", 
              cls="btn-primary"),
            A("Manage", href=f"/course/{course.id}/settings", 
              cls="btn-secondary"),
            cls="course-actions"
        ),
        cls="course-card"
    )
```

### 3. Wizard Component
```python
# components/wizard.py
def Wizard(steps, current_step, data):
    return Div(
        # Progress indicator
        Div(
            *[WizardStep(step, i <= current_step) 
              for i, step in enumerate(steps)],
            cls="wizard-progress"
        ),
        
        # Current step content
        Div(
            id="wizard-content",
            cls="wizard-body"
        ),
        
        # Navigation
        Div(
            Button("← Back", 
                   hx_post=f"/wizard/back",
                   cls="btn-secondary",
                   disabled=current_step == 0),
            Button("Next →", 
                   hx_post=f"/wizard/next",
                   cls="btn-primary"),
            cls="wizard-nav"
        ),
        cls="wizard-container"
    )
```

### 4. Content Generator Interface
```python
# components/content_generator.py
def ContentGenerator(course, week, content_type):
    return Div(
        # Left Panel: Configuration
        Div(
            H3("Configure Your Content"),
            
            # Content type selector
            Select(
                Option("Lecture", value="lecture"),
                Option("Worksheet", value="worksheet"),
                Option("Lab Exercise", value="lab"),
                Option("Quiz", value="quiz"),
                Option("Case Study", value="case_study"),
                name="content_type",
                value=content_type
            ),
            
            # Context inputs
            Textarea(
                placeholder="Learning objectives for this content...",
                name="objectives",
                rows="4"
            ),
            
            # Teaching style options
            Fieldset(
                Legend("Apply Teaching Style"),
                *[Checkbox(style, name="styles", value=style)
                  for style in course.teaching_styles],
            ),
            
            # Generate button
            Button(
                "Generate Plan",
                hx_post="/api/generate/plan",
                hx_target="#plan-preview",
                cls="btn-primary w-full"
            ),
            
            cls="generator-config"
        ),
        
        # Right Panel: Preview
        Div(
            Div(
                H3("Generation Plan"),
                Div(id="plan-preview", cls="plan-content"),
                cls="plan-section"
            ),
            Div(
                H3("Preview"),
                Div(id="content-preview", cls="preview-content"),
                cls="preview-section"
            ),
            cls="generator-preview"
        ),
        
        cls="content-generator"
    )
```

## CSS Design System

```css
/* design_system.css */
:root {
  /* Colors */
  --primary: #3B82F6;
  --secondary: #6B7280;
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  
  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
}

/* Component Styles */
.course-card {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 0.5rem;
  padding: var(--space-lg);
  transition: box-shadow 0.2s;
}

.course-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.wizard-container {
  max-width: 800px;
  margin: 0 auto;
}

.wizard-progress {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-xl);
}

.wizard-step {
  flex: 1;
  text-align: center;
  position: relative;
}

.wizard-step.active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--primary);
}

.content-generator {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: var(--space-xl);
  height: calc(100vh - 200px);
}

.generator-config {
  background: #F9FAFB;
  padding: var(--space-lg);
  border-radius: 0.5rem;
  overflow-y: auto;
}

.generator-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}
```

## Migration Path

### Phase 1: Authentication & Structure (Week 1)
1. Add user authentication system
2. Create database schema
3. Build landing page
4. Implement basic navigation

### Phase 2: Dashboard & Course Management (Week 2)
1. Build dashboard with course cards
2. Create course CRUD operations
3. Add course creation wizard
4. Implement progress tracking

### Phase 3: Content Generation (Week 3-4)
1. Integrate teaching philosophy system
2. Build content generator UI
3. Create plan → review → generate workflow
4. Add content type templates

### Phase 4: Enhancement & Polish (Week 5)
1. Add import/upload functionality
2. Implement export options
3. Create help system
4. Add keyboard shortcuts for power users

This redesign transforms the app from a simple analyzer to a comprehensive course creation platform while maintaining the FastHTML architecture.