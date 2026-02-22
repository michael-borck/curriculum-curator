# Assessment Management View - UI/UX Integration Guide

## Overview
This document describes the Assessment Management functionality to be integrated into the existing Course Authoring Tool. The Assessment View is accessed via a tab system in the main content area, sitting alongside the Weekly Materials view. This view allows educators to create, manage, and organize all course assessments in one centralized location.

## Core Functionality
The Assessment Management system enables educators to:
1. Create and manage various assessment types (quizzes, exams, projects, discussions, papers, presentations)
2. Distinguish between formative (learning-focused) and summative (grade-focused) assessments
3. Define grade weights and calculate total grade distribution
4. Map assessments to Course Learning Outcomes (CLOs)
5. Link assessments to relevant weekly materials
6. Track release and due dates using both week numbers and calendar dates
7. Specify detailed requirements and rubrics

## UI Layout Structure

### Tab Navigation
Located at the top of the main content area:
```
[📚 Weekly Materials] [📊 Assessments] [📈 Grade Distribution]
```
- Assessments tab shows all course assessments in a unified view
- Clear visual indication of active tab (blue underline, text color)

### Assessment View Components

#### 1. **Header Section**
- Title: "Course Assessments"
- Summary statistics: Total assessments, formative count, summative count, total weight
- "Add Assessment" button (primary action, blue)

#### 2. **Grade Distribution Alert**
- Visual summary box showing:
  - Current total weight percentage
  - Formative vs. Summative breakdown
  - Warning if weights don't sum to 100%
  - Visual progress bar or pie chart (optional)

#### 3. **Assessment List**
Each assessment card displays:
- **Icon & Category**: Visual indicator of assessment type
- **Title**: Assessment name
- **Type Badge**: Formative (blue) or Summative (purple)
- **Weight**: Percentage of final grade (if applicable)
- **Description**: Brief one-line summary
- **Timeline**: Release week/date and due week/date
- **Duration/Scope**: Time limit, number of questions, or project duration
- **Learning Outcomes**: Assessment-specific outcomes
- **Mapped CLOs**: Related Course Learning Outcomes (see below)
- **Linked Materials**: Connected weekly content
- **Actions**: Edit, Copy, Delete, More Options

### Learning Outcome Mapping

#### Display Format
Each assessment shows a two-tier learning outcome structure:

```
Learning Outcomes:
• Analyze statistical data using R
• Create meaningful visualizations
• Interpret regression results

Aligned with Course Learning Outcomes:
→ CLO 2: Apply statistical methods to analyze data
→ CLO 3: Build and evaluate machine learning models
```

#### Visual Design
- Assessment-specific outcomes use bullet points
- Mapped CLOs use arrow indicators (→) and reference numbers
- CLOs displayed in a subtle background color (e.g., light blue tint)
- Expandable/collapsible if many outcomes listed

## Data Model

```typescript
interface Assessment {
  id: number;
  title: string;
  type: 'formative' | 'summative';
  category: 'quiz' | 'exam' | 'project' | 'discussion' | 'paper' | 'presentation';
  weight: number; // 0-100, percentage of final grade
  description: string; // Brief one-liner
  specification: string; // Detailed requirements, rubric
  
  // Timeline
  releaseWeek: number;
  releaseDate: string; // ISO date format
  dueWeek: number;
  dueDate: string;
  duration?: string; // "2 hours", "3 weeks", etc.
  
  // Academic alignment
  learningOutcomes: string[]; // Assessment-specific outcomes
  mappedCLOs: number[]; // IDs of related Course Learning Outcomes
  linkedMaterials: number[]; // IDs of related weekly materials
  
  // Metadata
  questions?: number; // For quizzes/exams
  wordCount?: number; // For papers
  status: 'draft' | 'complete' | 'needs-review';
  lastModified: string;
  
  // Optional fields
  rubric?: Rubric;
  prerequisites?: number[]; // IDs of assessments that must come first
  groupWork?: boolean;
  submissionType?: 'online' | 'in-person' | 'both';
}

interface Rubric {
  criteria: RubricCriterion[];
  totalPoints: number;
}

interface RubricCriterion {
  name: string;
  description: string;
  points: number;
  levels: string[]; // Performance levels
}
```

## Assessment Categories

### Visual Coding System
Each category has distinct icon and color:
- **Quiz**: ClipboardCheck icon, green accent (#10B981)
- **Exam**: FileText icon, red accent (#EF4444)
- **Project**: BookOpen icon, orange accent (#F97316)
- **Discussion**: Users icon, cyan accent (#06B6D4)
- **Paper**: Edit icon, indigo accent (#6366F1)
- **Presentation**: Monitor icon, purple accent (#8B5CF6)

### Type Differentiation
- **Formative**: Blue badge (#3B82F6) - Focuses on learning process
- **Summative**: Purple badge (#8B5CF6) - Focuses on grade/evaluation

## Add/Edit Assessment Modal

### Required Fields
1. **Basic Information**
   - Title
   - Type (Formative/Summative)
   - Category (Quiz/Exam/Project/etc.)
   - Weight (0-100%)

2. **Descriptions**
   - Brief description (one line)
   - Full specification (detailed requirements)

3. **Timeline**
   - Release: Week number + calendar date
   - Due: Week number + calendar date
   - Duration (if applicable)

4. **Academic Alignment**
   - Assessment learning outcomes (free text, multiple entries)
   - Map to Course Learning Outcomes (checkbox list)
   - Link to weekly materials (multi-select)

### Optional Fields
- Number of questions (for quizzes/exams)
- Word count requirements (for papers)
- Group work settings
- Submission type
- Rubric builder
- Prerequisites

## Key UX Patterns

### Timeline Management
- **Dual Dating**: Shows both "Week 4" and "Sept 23, 2024"
- **Date Synchronization**: Changing week auto-updates date based on course calendar
- **Conflict Detection**: Warns if multiple major assessments due same week

### Grade Weight Validation
- Real-time calculation of total weight
- Visual warning if total ≠ 100%
- Breakdown by assessment type
- Suggested weight distribution templates

### CLO Mapping Workflow
1. In edit modal, show all Course Learning Outcomes as checkboxes
2. Educator selects which CLOs the assessment addresses
3. System displays mapped CLOs on assessment card
4. Optional: Show coverage report (which CLOs lack assessments)

### Quick Actions
- **Duplicate**: Copy assessment with "[Copy]" suffix
- **Convert Type**: Change formative ↔ summative
- **Adjust Dates**: Bulk shift all dates by X weeks
- **Preview**: See student view of assessment

## Integration Points

### With Weekly Materials View
- Assessments appear as indicators in relevant weeks
- "Assessment Due" badges on week cards
- Quick jump links between views

### With Export System
- Include assessment schedule in course package
- Format assessments for LMS compatibility
- Generate assessment calendar

### With Learning Outcomes
- CLO coverage analysis
- Alignment matrix generation
- Gap identification (unmapped outcomes)

## Additional Features

### Timeline Visualization
- Optional calendar/Gantt view of all assessments
- Visual load balancing (identify heavy weeks)
- Drag-and-drop rescheduling

### Templates
- Common assessment patterns by discipline
- Reusable rubric templates
- Standard weight distributions

### Analytics (Future)
- Historical performance data
- Difficulty calibration
- Time-on-task estimates

## Accessibility Requirements
- Clear visual hierarchy with proper heading structure
- Color not sole indicator (use icons + text)
- Keyboard navigation for all actions
- Screen reader announcements for state changes
- High contrast mode support

## Responsive Behavior
- On tablets: Stack assessment cards vertically
- On mobile: Simplified card view with expandable details
- Touch-friendly action buttons
- Swipe gestures for quick actions

## Performance Considerations
- Lazy load assessment specifications
- Paginate if >20 assessments
- Cache CLO mappings
- Optimistic UI updates for edits

## Success Metrics
- All assessments have mapped CLOs
- Grade weights sum to 100%
- Even distribution across weeks
- No scheduling conflicts
- Complete specifications for all assessments

---

*This Assessment Management View integrates seamlessly with the existing Course Authoring Tool, providing educators with a comprehensive system for planning, organizing, and aligning their course assessments with learning outcomes.*