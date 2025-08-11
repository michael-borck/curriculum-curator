# AI Instruction Set: Learning Requirements Document (LRD) Creation & Task Execution

## Quick Reference: Workflow at a Glance
1. 📋 Review materials → Ask questions
2. 📝 Create LRD → Get approval
3. ✅ Generate task list → Get approval
4. 🔄 Execute tasks one-by-one → Get approval each
5. 📦 Finalise & deliver

**File Naming Convention:**
- LRD: `LRD-[Unit]-Week[X]-v[#].md`
- Tasks: `tasks-[Unit]-Week[X]-v[#].md`
- Content: `[##]_[type]_[description].md`

**Language Convention:**
- Use Australian-British spelling in all documents (e.g., organise, colour, centre, programme, analyse, recognise, behaviour, honour, favour, labour, modernisation)

---

## Purpose
This document instructs the AI to:
1. Review provided **legacy course materials** and this instruction set.
2. Ask a set of **clarifying questions** to fill knowledge gaps.
3. Generate a **Learning Requirements Document (LRD)** — similar to a Product Requirements Document, but for education/training.
4. Produce a **prioritised, actionable task list** based on the LRD.
5. Work through **one task at a time**, with human review/approval at each step.

The LRD will be the **single source of truth** for all content creation and updates.

**Important:** All generated content must use Australian-British spelling and conventions (e.g., organise not organize, colour not color, programme for educational programmes, analyse not analyze).

---

## Version Control & Change Tracking
- **LRD Version:** Include version numbers (e.g., LRD-Week01-v1.2.md)
- **Change Log:** Brief summary of what changed between versions
- **Approval History:** Date/time stamps for human approvals
- **Current Status:** Draft | Under Review | Approved | In Progress | Complete

---

## Step 1 — Initial Review & Clarifying Questions

**AI must:**
1. Read all provided materials.
2. Identify missing or unclear information.
3. Ask **grouped clarifying questions** to reduce back-and-forth.
4. Wait for all answers before starting the LRD.

**Comprehensive Clarifying Question Areas:**

### Learning Design
- **Learning Objectives:** 
  - What should students know/do by the end of this week?
  - What Bloom's taxonomy levels are targeted?
  - Focus on competencies vs. knowledge acquisition?
- **Success Metrics:**
  - How will learning be measured?
  - What constitutes mastery?
  - Formative vs. summative assessment balance?
- **Delivery Format Preferences:**
  - Traditional worksheets vs. interactive HTML pages?
  - Flipped classroom with pre-class modules?
  - Number and length of pre-class modules if flipped?
  - Live coding vs. guided exercises vs. problem-solving?

### Audience & Context
- **Target Audience:** 
  - Year level and program
  - Assumed prior knowledge
  - Class size and diversity considerations
- **Time Allocation:**
  - Total hours expected per week?
  - Synchronous vs. asynchronous split?
  - Pre-class, in-class, post-class breakdown?

### Content & Resources
- **Legacy Content:** 
  - Key files to preserve
  - Priority areas for modernisation
  - Content to discard or archive
- **Desired Structure:** 
  - Flipped classroom model?
  - Pre/In/Post class format?
  - Self-paced vs. instructor-led?

### Activities & Assessment
- **Activities:** 
  - Types (group work, coding labs, discussions, case studies)
  - Individual vs. collaborative balance
  - Industry/real-world connections
- **Assessment:** 
  - Type and method this week
  - Alignment with program-level outcomes
  - Rubrics or marking criteria available?

### Technical & Compliance
- **Technical Requirements:**
  - LMS platform and constraints?
  - Required tools/software?
  - Mobile compatibility needed?
- **Accessibility Requirements:**
  - WCAG compliance level?
  - Alternative formats needed?
  - Language/cultural considerations?
- **Style/Tone:** 
  - Pedagogical approach (formal, conversational, scaffolded)
  - Discipline-specific conventions
  - Preferred examples/case studies
  - **Language:** Australian-British spelling and terminology

---

## Step 2 — Generate the Learning Requirements Document (LRD)

**LRD Structure:**

```markdown
# Learning Requirements Document
## Version: [X.X] | Status: [Draft/Approved] | Last Updated: [Date]

### 1. Topic
- **Week/Unit:** [Number and Name]
- **Main Theme:** [Core concept or skill focus]
- **Duration:** [Total time commitment expected]

### 2. Learning Objectives
Upon completion, students will be able to:
- [ ] [Specific, measurable objective 1] [Bloom's Level]
- [ ] [Specific, measurable objective 2] [Bloom's Level]
- [ ] [Specific, measurable objective 3] [Bloom's Level]

### 3. Target Audience
- **Course/Program:** [Name and code]
- **Year Level:** [1st year, 2nd year, etc.]
- **Assumed Knowledge:** [Prerequisites and prior learning]
- **Class Size:** [Expected number of students]

### 4. Available Resources
#### Legacy Materials
- [File 1]: [Description and current state]
- [File 2]: [Description and current state]

#### New Resources Required
- [Resource 1]: [URL or description]
- [Resource 2]: [URL or description]

### 5. Desired Structure
- **Pre-Class:** [Duration] - [Activities/content]
  - **Module Breakdown:** [If flipped, list modules with durations]
    - Module 1: [Topic] ([X] minutes)
    - Module 2: [Topic] ([X] minutes)
- **In-Class:** [Duration] - [Activities/content]
  - **Format:** [Interactive HTML/Worksheet/Hybrid]
  - **Facilitation Style:** [Guided/Self-paced/Mixed]
- **Post-Class:** [Duration] - [Activities/content]

### 6. Key Activities & Deliverables
| Activity | Type | Format | Duration | Student Deliverable | Tutor Resources |
|----------|------|--------|----------|-------------------|-----------------|
| [Name] | [Individual/Group] | [HTML/PDF/Mixed] | [Time] | [Output] | [Guide/Solutions] |

### 7. Assessment
- **Type:** [Formative/Summative]
- **Method:** [Quiz/Assignment/Project]
- **Weight:** [% of final grade if applicable]
- **Success Criteria:** [How mastery is demonstrated]

### 8. Constraints & Assumptions
- **Time Limits:** [Specific constraints]
- **Technical Requirements:** [Software, hardware, platforms]
- **Dependencies:** [Other courses, topics, or resources]
- **Accessibility:** [Specific requirements]

### 9. Integration Points
- **LMS Requirements:** [Specific format or features needed]
- **Calendar Alignment:** [Due dates, milestones]
- **Grade Book Mapping:** [How activities map to grade items]

### 10. Change Log
| Version | Date | Changes | Approved By |
|---------|------|---------|-------------|
| 1.0 | [Date] | Initial draft | [Name] |
```

**Save as:** `LRD-[UnitName]-Week[X]-v[Version].md`

Pause and request **human approval** before moving to Step 3.

---

## Step 3 — Generate Task List

**AI must:**
1. Analyze approved LRD.
2. Create **parent tasks** with priority levels.
3. Wait for human confirmation before breaking down into sub-tasks.
4. Expand each parent task into **specific, actionable sub-tasks**.
5. Include a **Relevant Files** section.

### Task Priority Levels
- **P0 (Critical):** Blocks other work or required for assessment
- **P1 (High):** Core learning objectives
- **P2 (Medium):** Enhances understanding
- **P3 (Low):** Nice-to-have enrichment

### Task List Format

```markdown
# Task List for [LRD Name]
## Version: [X.X] | Generated: [Date] | LRD Version: [X.X]

## Summary
- Total Tasks: [X] parent tasks, [Y] sub-tasks
- Estimated Completion Time: [Hours/Days]
- Current Progress: [X]% complete

## Parent Tasks Overview
- [ ] [P0] Parent Task 1: [Description]
- [ ] [P1] Parent Task 2: [Description]
- [ ] [P2] Parent Task 3: [Description]

## Detailed Task Breakdown

### [P0] Parent Task 1: [Name]
- [ ] Sub-task 1.1: [Specific action]
- [ ] Sub-task 1.2: [Specific action]
- [x] Sub-task 1.3: [Completed action]
- [!] Sub-task 1.4: [Blocked action] - Blocker: [Reason]

## Relevant Files
| File Name | Type | Status | Description |
|-----------|------|--------|-------------|
| 01_pre-lab_reading.md | Markdown | Created | Pre-lab reading guide |
| 02_in-lab_activities.md | Markdown | In Progress | Lab activity instructions |
```

**Task Status Indicators:**
- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed
- `[!]` Blocked (include reason)
- `[?]` Needs clarification

**Save as:** `tasks-[UnitName]-Week[X]-v[Version].md`

---

## Step 4 — Iterative Task Execution

**For each sub-task:**

1. **Select** the next incomplete sub-task (respecting priority).
2. **Create/update** content for that task only.
3. **Present** output with progress update.
4. **Update** the task list with current status.
5. **Wait** for explicit approval before continuing.

### Progress Update Template
```
📊 Progress Update - [Date/Time]
━━━━━━━━━━━━━━━━━━━━━━
✅ Completed: X/Y tasks (Z% complete)
🔄 Current Task: [P#] - [task description]
   Started: [time]
   Est. Completion: [time]
⚠️ Blockers: [specific issues or "None"]
⏭️ Next Task: [P#] - [upcoming task]
📁 Files Modified: [list any files created/updated]
━━━━━━━━━━━━━━━━━━━━━━
```

### Quality Assurance Criteria
Before marking any task complete, verify:
- [ ] Content aligns with stated learning objectives
- [ ] Language appropriate for target audience
- [ ] All links/references are functional
- [ ] Accessibility standards met
- [ ] Consistent formatting throughout
- [ ] Follows disciplinary conventions
- [ ] Includes diverse examples/perspectives

---

## Step 5 — Approval Gates

**Explicit approval required at:**

| Stage | Approval Trigger | Acceptable Responses |
|-------|-----------------|---------------------|
| After questions answered | "Proceed to LRD" | "approved", "yes", "continue" |
| After LRD creation | "Approve LRD" | "approved", "approved with changes: [list]" |
| After task list generation | "Approve task list" | "approved", "proceed" |
| After each sub-task | "Task approved" | "approved", "continue", "next" |

**Conditional Approval:**
- "Approved with changes: [specific changes]" - Make changes then continue
- "Revise: [specific feedback]" - Revise and re-submit for approval

**Rejection:**
- "Redo" with specific feedback - Start task over
- "Skip" - Mark as cancelled and move to next task

---

## Step 6 — Error Handling & Recovery

### If Blocked
1. Mark task as `[!]` with specific blocker reason
2. Suggest alternative approach or workaround
3. Request human guidance with specific options:
   - Option A: [Alternative approach]
   - Option B: [Different solution]
   - Option C: [Skip and return later]

### If Requirements Change Mid-Process
1. Flag which completed tasks may need revision
2. Update LRD with change notes and new version number
3. Regenerate affected portions of task list
4. Request approval for revised plan

### Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| Missing source material | Request specific files or proceed with placeholder |
| Conflicting requirements | Present options with pros/cons for decision |
| Technical constraints | Suggest workarounds within platform limits |
| Time overrun | Propose scope reduction with priority preservation |

---

## Content Templates

### Pre-Class Module Template (Flipped Classroom)
```markdown
# Module [X].[Y]: [Module Name]
## Part of Week [X]: [Overall Topic]

### Module Overview
- **Duration:** [X] minutes
- **Position:** Module [Y] of [Total]
- **Prerequisites:** [Previous modules or knowledge]

### Learning Objectives
After this module, you will be able to:
- [ ] [Specific objective for this module]
- [ ] [Another specific objective]

### Content Sections

#### Section 1: [Concept Name] ([X] minutes)
##### Watch
- [Video/Animation Title] ([X] minutes)
  - Key points: [List main takeaways]

##### Read
- [Article/Text section] ([X] minutes)
  - Focus on: [Specific aspects]

##### Try It Yourself
```[code block or interactive element]```

#### Knowledge Check
1. [Quick question about this section]
   <details>
   <summary>Answer</summary>
   [Explanation]
   </details>

### Module Summary
- **Key Takeaway 1:** [Concise point]
- **Key Takeaway 2:** [Concise point]

### Preparation for Lab
- [ ] Completed all sections
- [ ] Attempted practice problems
- [ ] Noted questions for discussion
```

### Interactive HTML Activity Template
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Week [X]: [Activity Name]</title>
    <style>
        /* Responsive, accessible styling */
        .activity-container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .exercise { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .interactive-area { border: 2px solid #007bff; padding: 15px; background: white; }
        .feedback { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .feedback.correct { background: #d4edda; colour: #155724; }
        .feedback.incorrect { background: #f8d7da; colour: #721c24; }
        .progress-bar { height: 30px; background: #e9ecef; border-radius: 4px; }
        .progress-fill { height: 100%; background: #28a745; border-radius: 4px; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="activity-container">
        <h1>Week [X]: [Activity Name]</h1>
        
        <div class="progress-bar">
            <div class="progress-fill" id="progress" style="width: 0%"></div>
        </div>

        <section class="exercise" id="exercise1">
            <h2>Exercise 1: [Name]</h2>
            <p>[Instructions]</p>
            
            <div class="interactive-area">
                <!-- Interactive elements: code editor, drag-drop, etc. -->
                <textarea id="code-input" rows="10" cols="50"></textarea>
                <button onclick="checkAnswer(1)">Check Answer</button>
            </div>
            
            <div id="feedback1" class="feedback" style="display:none;"></div>
        </section>

        <!-- Additional exercises -->
        
        <section class="summary">
            <h2>Summary</h2>
            <p>You've completed [X] of [Y] exercises.</p>
            <button onclick="downloadResults()">Download Progress Report</button>
        </section>
    </div>

    <script>
        // Interactive functionality
        let progress = 0;
        const totalExercises = [Y];
        
        function checkAnswer(exerciseNum) {
            // Validation logic
            // Update progress
            // Provide feedback
        }
        
        function updateProgress() {
            progress++;
            const percentage = (progress / totalExercises) * 100;
            document.getElementById('progress').style.width = percentage + '%';
        }
        
        function downloadResults() {
            // Generate and download progress report
        }
    </script>
</body>
</html>
```

### Tutor Instructions Template
```markdown
# Tutor Instructions: Week [X] - [Topic]

## Session Overview
- **Duration:** [X] hours
- **Format:** [Lab/Workshop/Tutorial]
- **Max Students:** [Number]
- **Room Setup:** [Requirements]

## Pre-Session Checklist
- [ ] Review student pre-class module completion rates
- [ ] Test all interactive HTML pages on lab computers
- [ ] Prepare backup PDF worksheets (if tech fails)
- [ ] Load solution files
- [ ] Set up demonstration environment

## Learning Objectives Review
Students should arrive having completed modules on:
1. [Module 1 topic] - Check understanding of [key concept]
2. [Module 2 topic] - May need reinforcement on [difficult area]

## Session Timeline

### Opening (10 minutes)
1. **Quick Poll:** Use interactive tool to check module completion
2. **Address Common Misconceptions:** Based on pre-class quiz data
3. **Today's Goals:** Display on screen

### Part 1: [Activity Name] (30 minutes)
**Setup:**
- Direct students to [URL/file]
- Form groups of [X] if collaborative

**Facilitation Notes:**
- **At 5 minutes:** Check all students have accessed the activity
- **At 15 minutes:** Pause for common sticking point on [concept]
- **At 25 minutes:** Begin wrap-up, ensure minimum completion

**Common Issues & Solutions:**
| Issue | Solution | Prevention |
|-------|----------|------------|
| [Technical problem] | [Quick fix] | [Advance setup] |
| [Conceptual confusion] | [Explanation approach] | [Emphasize in intro] |

### Part 2: [Activity Name] (40 minutes)
[Similar structure]

### Closing (10 minutes)
1. **Key Takeaways:** Student-generated list
2. **Connect to Next Week:** Preview connection
3. **Remind:** Post-class reflection task

## Differentiation Strategies
- **Fast Finishers:** Extension challenges in HTML page section 4
- **Struggling Students:** Pair with stronger peers, use simplified version
- **Different Learning Styles:** Visual (diagrams), Kinesthetic (interactive), Auditory (peer explanation)

## Assessment During Session
- **Formative:** Monitor progress bars on HTML pages
- **Observation:** Use rubric for participation/collaboration
- **Check-ins:** Quick verbal comprehension checks

## Solution Guide
### Exercise 1
```[language]
// Complete solution with explanation
```

### Common Alternative Approaches
- **Approach A:** [When to validate this]
- **Approach B:** [Why this also works]

## Post-Session Actions
- [ ] Note attendance and participation
- [ ] Log common difficulties for course improvement
- [ ] Send follow-up resources to struggling students
- [ ] Update next week's plan based on progress
```

### Facilitator Guide Template (Master Overview)
```markdown
# Facilitator Guide: [Course Name] - Week [X]

## Delivery Philosophy
This week uses a **flipped classroom** approach:
- **Pre-class:** Self-paced modules (total: [X] hours)
- **In-class:** Active problem-solving and collaboration
- **Post-class:** Reflection and extension

## Module Delivery Map
```
Pre-Class Modules (Release 1 week prior)
    ↓
Module 1: Foundations (20 min) → Module 2: Core Concepts (25 min) → Module 3: Application (15 min)
    ↓
In-Class Session (2 hours)
    ↓
Hour 1: Guided Practice (HTML Interactive) → Hour 2: Collaborative Challenge
    ↓
Post-Class: Reflection + Optional Extension
```

## Key Facilitation Principles
1. **Never Repeat Module Content:** Assume completion, build upon it
2. **Just-in-Time Support:** Address confusion as it arises
3. **Peer Learning:** Students explain to each other
4. **Active Over Passive:** Minimize instructor talking time

## Room Management
### For Interactive HTML Activities
- **Setup:** Browser-based, works on any device
- **Backup:** Have PDF versions ready
- **Monitoring:** Use teacher dashboard if available
- **Collaboration:** Screen sharing for group work

### For Traditional Worksheets
- **When to Use:** Complex diagrams, lengthy code review
- **Distribution:** Digital first, print on demand
- **Collection:** Photo submission acceptable

## Weekly Rhythm
| Day | Activity | Instructor Action |
|-----|----------|------------------|
| Monday | Release modules | Send announcement with expectations |
| Wednesday | Check completion | Message non-completers |
| Thursday | Pre-class deadline | Review completion data |
| Friday | Lab/Workshop | Facilitate active session |
| Monday | Reflection due | Review and provide feedback |

## Technology Troubleshooting
### Interactive HTML Issues
- **Page won't load:** Check browser compatibility (Chrome/Firefox/Safari)
- **Progress not saving:** Use browser local storage, remind to not clear cache
- **Mobile issues:** Responsive design should work, but recommend laptop

## Continuous Improvement
- **Weekly Survey:** Quick feedback on modules vs. in-class
- **Analytics Review:** Which modules/exercises have highest struggle rates
- **Tutor Debrief:** Weekly 15-min check-in with all tutors

## Language & Style Guide
- **Spelling:** Australian-British throughout (e.g., analyse, behaviour, colour, centre)
- **Terminology:** Follow Australian educational conventions
- **Date Format:** DD/MM/YYYY
- **Measurements:** Metric system
- **Cultural References:** Use Australian contexts where possible
```

---

## Finalization

**AI must:**
- Ensure all tasks are completed and marked `[x]`
- Provide a **final summary** of deliverables
- Confirm outputs match the approved LRD
- Create final documentation package

### Final Summary Template
```markdown
# Project Completion Summary
## Course: [Name] | Week: [X] | Date Completed: [Date]

### Deliverables Completed
1. [File 1] - [Description]
2. [File 2] - [Description]

### LRD Objectives Met
- [x] Objective 1: [How it was addressed]
- [x] Objective 2: [How it was addressed]

### Statistics
- Total Tasks Completed: [X]
- Time Invested: [Hours]
- Files Created: [X]
- Files Modified: [Y]

### Ready for LMS Upload
- [ ] All files validated
- [ ] Accessibility checked
- [ ] Links verified
- [ ] Format compliance confirmed

### Notes for Implementation
[Any special instructions or considerations]
```

---

## Recommended Project Folder Structure

```
/[CourseName]_Course-Modernisation/
│
├── 📜 README.md
├── 🗺️ instructional-design-workflow.md
├── 📊 project-status.md
│
├── 1_legacy_materials/
│   └── week-01_intro-topic/
│       ├── lecture-slides.pptx
│       ├── required-reading.pdf
│       └── archive/
│           └── outdated-content.doc
│
├── 2_planning_documents/
│   ├── LRD-Week01-IntroTopic-v1.2.md
│   ├── tasks-Week01-IntroTopic-v1.2.md
│   └── approvals/
│       └── approval-log.md
│
├── 3_modernised_content/
│   └── week-01_intro-topic/
│       ├── pre-class-modules/
│       │   ├── module-1-foundations.md
│       │   ├── module-2-core-concepts.md
│       │   └── module-3-application.md
│       ├── in-class-activities/
│       │   ├── interactive-exercise-1.html
│       │   ├── interactive-exercise-2.html
│       │   ├── worksheet-fallback.pdf
│       │   └── assets/
│       │       ├── style.css
│       │       └── script.js
│       ├── post-class/
│       │   ├── reflection-prompts.md
│       │   └── extension-challenges.md
│       ├── instructor-resources/
│       │   ├── facilitator-guide.md
│       │   ├── tutor-instructions.md
│       │   ├── solution-key.md
│       │   └── session-slides.pptx
│       └── media/
│           ├── diagram-01.png
│           └── demo-video.mp4
│
└── 4_quality_assurance/
    ├── qa-checklist.md
    ├── accessibility-audit.md
    ├── browser-compatibility.md
    └── user-testing-feedback.md
```

### Enhanced Folder Structure Explanation
- **Root Folder:** Contains overview documentation and workflow guides
- **1_legacy_materials/:** Raw, untouched source files organised by week/topic
- **2_planning_documents/:** LRDs, task lists, and approval records
- **3_modernised_content/:** Final materials organised by delivery method:
  - **pre-class-modules/:** Self-contained learning modules for flipped approach
  - **in-class-activities/:** Interactive HTML pages and fallback worksheets
  - **post-class/:** Reflection and extension materials
  - **instructor-resources/:** All teaching support materials including facilitator guides and tutor instructions
- **4_quality_assurance/:** QA documentation including browser testing for HTML content

---

## Interaction Model

### Control Points
- Human remains in control at all decision points
- AI waits for explicit approval before proceeding
- No autonomous decision-making on scope or direction

### Traceability
- Each output links to relevant LRD section
- Version numbers track all iterations
- Change log documents all modifications

### Flexibility
- New tasks may be added with human agreement
- Priorities can be adjusted mid-process
- Scope can be modified with documented approval

### Transparency
- Regular progress updates
- Clear status indicators
- Explicit blocker identification

---

## Integration Considerations

### LMS Integration
- **Upload Format:** SCORM compliance requirements?
- **Metadata:** Required fields for course catalog?
- **Navigation:** How do modules connect?

### Assessment Systems
- **Question Banks:** Required format (QTI, Moodle XML)?
- **Rubrics:** Integration with grading system?
- **Analytics:** Tracking requirements?

### Calendar & Scheduling
- **Due Dates:** Alignment with academic calendar
- **Milestones:** Key dates for releases
- **Dependencies:** Prerequisite management

### Accessibility & Compliance
- **Standards:** WCAG 2.1 AA minimum
- **Testing:** Screen reader compatibility
- **Alternatives:** Captions, transcripts, descriptions

---

## Summary

This enhanced workflow ensures:
- **Comprehensive planning** before content creation
- **Interactive, engaging content** prioritising HTML activities over traditional worksheets
- **Complete instructor support** with facilitator guides and tutor instructions
- **Flipped classroom readiness** with modular pre-class content
- **Step-by-step controlled execution** with clear priorities
- **Quality assurance** at every stage
- **Clear linkage** between goals, tasks, and deliverables
- **Continuous human oversight** and approval
- **Consistent, transparent** file organisation
- **Version control** and change tracking
- **Error handling** and recovery procedures
- **Integration readiness** for LMS and other systems
- **Australian-British spelling** and conventions throughout all materials

The workflow balances AI efficiency with human expertise, ensuring high-quality educational content that meets institutional standards, engages students through interactive formats, and provides comprehensive support for instructors delivering the material.
