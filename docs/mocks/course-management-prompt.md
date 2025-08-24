# Course Authoring Tool - UI/UX Integration Guide

## Overview
I need to integrate a course authoring interface into our existing application. The interface allows educators to create, organize, and export course materials for university/college courses (typically 12-week semesters). Below is the React component code and a screenshot showing the desired UI/UX.

## Core Functionality
This is a **course creation and curation tool** (NOT a Learning Management System). Educators use it to:
1. Structure course content across multiple weeks (flexible: 1-12+ weeks)
2. Add various material types (lectures, handouts, quizzes, case studies, resources, notes)
3. Define learning outcomes at three levels (course, weekly, material)
4. Export completed courses to LMS platforms (Canvas, Blackboard, Moodle, SCORM)

## UI Layout Structure

### Three-Panel Design:
1. **Header Bar** (top):
   - Course title with completion status badge
   - Progress bar showing overall completion percentage
   - View toggle: [All Weeks] [Active Weeks Only] [Compact]
   - Action buttons: Import, Templates, Export Course

2. **Sidebar** (left, 320px width):
   - Quick action buttons (AI Assist, My Library)
   - Collapsible Course Learning Outcomes section
   - Search bar for materials
   - Filter tags (Required, Optional, Interactive, etc.)
   - Week list with completion indicators and material counts
   - Expandable week items showing material previews
   - Visual differentiation for empty vs. populated weeks

3. **Main Content Area** (center/right):
   - Selected week details with learning outcomes
   - Material cards with metadata and actions
   - Empty state with creation prompts
   - Reorder mode for drag-and-drop organization

## Key UX Patterns

### Learning Outcome Alignment System
The tool supports hierarchical learning outcome mapping across three levels:

#### Three-Tier Hierarchy:
1. **Course Learning Outcomes (CLOs)**: Top-level outcomes for entire course
2. **Weekly Learning Outcomes**: Week-specific goals that support CLOs
3. **Material/Assessment Learning Outcomes**: Specific outcomes that map upward

#### Material-to-CLO Mapping:
- Each material can have its own specific learning outcomes
- Materials can be mapped to one or more Course Learning Outcomes
- In edit modal: Show CLOs as checkboxes for selection
- Display format on material cards:
  ```
  Learning Outcomes:
  • Explain data types in Python
  • Write basic Python functions
  
  Aligned with Course Learning Outcomes:
  → CLO 1: Understand fundamental programming concepts
  → CLO 3: Build and evaluate machine learning models
  ```

#### Coverage Tracking:
- Visual indicators show which CLOs are well-covered vs. gaps
- Analytics view to see outcome alignment across all materials
- Warnings for CLOs with no mapped materials/assessments

### Assessment Management Tab
*(See companion "Assessment Management View - UI/UX Integration Guide" for full details)*

The system includes a dedicated Assessments tab alongside Weekly Materials:
- **Tab Navigation**: [📚 Weekly Materials] [📊 Assessments] [📈 Grade Distribution]
- **Assessment Types**: Formative and Summative
- **CLO Mapping**: Assessments also map to Course Learning Outcomes
- **Grade Weighting**: Track and validate total adds to 100%
- **Timeline Management**: Dual week/calendar date system
- **Integration**: Assessments appear as indicators in weekly view

### Flexible Week Management
The system must accommodate different teaching styles:
- **Some lecturers** plan all 12 weeks upfront
- **Others** develop incrementally (week by week)
- **Many** create partial courses (e.g., only weeks 1, 4, and 7)

#### Entry Point Behavior:
- **Via Setup Wizard**: Display all 12 weeks (empty weeks are ghosted/de-emphasized)
- **Via Manual Creation**: Start with Week 1 only, with prominent "Add Week" button

#### View Modes:
- **All Weeks**: Shows complete structure (empty weeks at 50% opacity)
- **Active Weeks Only**: Shows only weeks containing materials
- **Compact**: Shows active weeks + "Add Week" gaps

### Visual Status System
- **Weeks**: 
  - Green check (✓) = complete
  - Yellow warning (⚠) = in progress
  - Gray/ghosted = empty
- **Materials**: Color-coded by type
  - Blue = lecture/video
  - Green = handout/document
  - Purple = quiz/assessment
  - Orange = case study
  - Cyan = external resource
  - Yellow = notes
- **Completion Badges**: "Complete", "In Progress", "Needs Review"

### Material Management
Each material card displays:
- Type icon and color coding
- Title and metadata (duration/pages/questions)
- Tags for categorization
- Learning outcomes (collapsible)
- Last modified timestamp
- Inline actions: Edit, Copy, Save to Library, More Options

### Creation Workflows
Multiple creation paths to support different workflows:
1. **Create New**: Build from scratch
2. **From Template**: Use pre-built structures
3. **From Library**: Reuse saved materials
4. **AI Generate**: Auto-create with AI assistance
5. **Import**: Bulk upload or cloud import

## Data Model Requirements

```typescript
interface Course {
  courseTitle: string;
  courseStatus: 'in-progress' | 'ready' | 'needs-review';
  viewMode: 'all-weeks' | 'active-only' | 'compact';
  totalWeeks: number;
  completionPercentage: number;
  courseLearningOutcomes: string[];
  weeks: Week[];
}

interface Week {
  weekNumber: number;
  title: string;
  isVisible: boolean;  // For show/hide functionality
  estimatedHours: number;
  completionStatus: 'complete' | 'in-progress' | 'empty';
  weeklyLearningOutcomes: string[];
  materials: Material[];
}

interface Material {
  id: number;
  type: 'lecture' | 'handout' | 'quiz' | 'case-study' | 'resource' | 'notes';
  title: string;
  status: 'complete' | 'in-progress' | 'needs-review';
  tags: string[];
  learningOutcomes: string[];
  lastModified: string;
  estimatedTime?: number;
  duration?: string;  // for videos
  pages?: number;      // for documents
  questions?: number;  // for quizzes
}
```

## Integration Points Needed

1. **File Management**: 
   - Upload functionality for PDFs, DOCX, PPT, MP4, ZIP
   - Cloud storage integration (Google Drive, OneDrive, Dropbox)
   - Drag-and-drop support with progress indicators

2. **Export Functionality**:
   - Generate packages for Canvas, Blackboard, Moodle
   - SCORM 1.2/2004 compliance
   - Pre-export validation and error reporting
   - Option to compress week numbering on export

3. **Template System**:
   - Subject-specific templates
   - Custom template creation and saving
   - Template marketplace/sharing (future)

4. **AI Integration**:
   - Generate learning outcomes
   - Create quiz questions from content
   - Suggest complementary materials
   - Auto-tag materials

5. **Personal Library**:
   - Persistent storage of reusable materials
   - Tagging and categorization system
   - Version control for materials
   - Cross-course searching

## Week Management Features

### Required Functionality:
1. **Add/Remove Weeks**: Dynamic week management
2. **Reorder Weeks**: Drag-and-drop or move up/down
3. **Duplicate Week**: Copy entire week with materials
4. **Bulk Operations**: Select multiple weeks for actions
5. **Week Templates**: Save week as template
6. **Skip Week**: Mark as "No class" while preserving numbering
7. **Custom Labels**: Beyond just "Week 1", allow custom naming

### Week Numbering Options:
- Sequential (1, 2, 3...)
- Calendar-based (Week of Sept 2, Sept 9...)
- Custom labels (Introduction, Midterm, Finals...)
- Module-based (Module 1.1, 1.2, 2.1...)

## UI/UX Requirements

### Styling
- **Color Palette**: 
  - Primary: Blue-600 (#2563EB)
  - Success: Green for completion
  - Warning: Yellow for in-progress
  - Neutral: Gray scale for UI elements
- **Spacing**: 4px base unit system
- **Border Radius**: 8px for cards and modals
- **Shadows**: Subtle elevation on hover
- **Typography**: System fonts with clear hierarchy

### Responsive Design
- Minimum width: 1024px (tablet landscape)
- Collapsible sidebar for smaller screens
- Stack material cards on mobile
- Full-screen modals on mobile devices

### Accessibility
- Full keyboard navigation
- ARIA labels for all controls
- High contrast mode support
- Screen reader announcements for state changes
- Focus indicators on all interactive elements

### State Management
- Persist view preferences (all weeks vs. active only)
- Auto-save with conflict resolution
- Undo/redo stack for operations
- Unsaved changes warnings
- Offline draft capability

## Performance Considerations
- Lazy load week contents when expanded
- Virtual scrolling for long material lists
- Optimistic UI updates
- Debounced search and filters
- Progressive image loading for material previews

## User Onboarding
- First-time tooltips for view modes
- Interactive tour for new users
- Contextual help buttons
- Sample course for experimentation
- Quick-start templates by discipline

Please integrate this UI into our existing application, maintaining the core functionality and UX patterns described above. The system should be flexible enough to accommodate different teaching styles while providing structure for those who need it. The provided React code shows a working implementation, and the screenshot demonstrates the visual design target.