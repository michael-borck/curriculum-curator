# Claude Code Prompts for Playwright Visual Guides

> **How to use:** Run each prompt in Claude Code from the root of your Curriculum Curator project.
> Before running the first one, make sure Playwright is installed:
>
> ```bash
> npm install playwright
> npx playwright install chromium
> mkdir -p guides/screenshots
> ```
>
> Each prompt tells Claude Code to read your codebase, write a Playwright script, and run it.
> Adjust the base URL, credentials, and sample data to match your environment.

---

## Preamble (paste once at the start of a session)

```
Read the project structure, focusing on:
- Route/router definitions (all page URLs and route names)
- Component files for pages, forms, buttons, modals, and navigation
- Any data-testid attributes or accessible names used in the UI

You'll be writing Playwright scripts that automate walkthroughs of the app and
capture screenshots at each meaningful step for a visual user guide.

Base URL: https://curriculumcurator.serveur.au
Screenshots go in: guides/screenshots/{guide-name}/
Viewport: 1280 x 800, headless: false

For every screenshot:
1. Before capturing, inject a red outline (3px solid red, 4px offset) around the
   element the user should focus on (the button they're about to click, the field
   they just filled in, etc.)
2. Remove the highlight after the screenshot
3. Name files with a zero-padded step number and descriptive slug,
   e.g. 01-login-page.png, 02-credentials-entered.png
4. Add a 500ms pause before each screenshot so animations settle

Create a helper function for the highlight-and-screenshot pattern so the scripts
stay DRY.

If a selector doesn't work when you run the script, read the relevant component
source to find the correct selector and fix it. Keep iterating until the script
runs cleanly.
```

---

## Guide 1: Registration, Login & Settings

```
Write and run a Playwright guide script: guides/scripts/01-registration-login-settings.js

Walk through:
1. Navigate to the app landing page. Screenshot.
2. Click "Register". Screenshot the registration form.
3. Fill in:
   - Email: guide-user@example.com
   - Full name: Alex Demo
   - Password: GuidePass123!
   Screenshot with the form filled.
4. Submit registration. Wait for redirect. Screenshot the result (login page or dashboard).
5. If not auto-logged-in, log in with those credentials. Screenshot the dashboard.
6. Navigate to Settings. Screenshot the settings page.
7. Set teaching style to "Problem-Based Learning". Screenshot.
8. Set education sector to "Higher Education". Screenshot.
9. Save settings. Reload the page. Screenshot showing the settings persisted.
10. Scroll to the API key section. Enter a dummy key "sk-demo-1234". Screenshot.
11. Save. Reload. Screenshot showing the key is masked but present.

Read the relevant component files for Settings, Registration, and Login to get
the exact form field selectors, button text, and route paths.
```

---

## Guide 2: Create Your First Unit

```
Write and run a Playwright guide script: guides/scripts/02-create-first-unit.js

Prerequisite: User is logged in (reuse login steps or assume session from Guide 1).

Walk through:
1. From the dashboard, screenshot showing the dashboard/unit list.
2. Click "Create Unit". Screenshot the creation form/modal.
3. If there's a structure preset selector, choose one (e.g. "Lecture-heavy").
   Screenshot showing the preset options, then screenshot after selection.
4. Fill in:
   - Title: "Web Development Fundamentals"
   - Code: "ICT101"
   - Credits: 12
   - Semester: "S1 2026"
   - Weeks: 12
   Screenshot with the form filled.
5. Change the topic label from "Week" to "Module". Screenshot highlighting the
   topic label selector.
6. Save/create the unit. Screenshot the unit page.
7. Screenshot the sidebar/list showing "Module 1", "Module 2", etc. (not "Week").
8. Set a teaching philosophy (e.g. "Constructivist"). Screenshot.
9. Add topic titles for Module 1: "HTML Basics", Module 2: "CSS Layout",
   Module 3: "JavaScript Intro". Screenshot after each one showing the updated list.

Read the unit creation form component, the unit page/layout component, and the
sidebar/topic list component to find the correct selectors.
```

---

## Guide 3: Adding Materials & Using the Editor

```
Write and run a Playwright guide script: guides/scripts/03-materials-and-editor.js

Prerequisite: The unit from Guide 2 exists. Navigate to it.

Walk through:
1. Navigate to Module 1 of the unit. Screenshot.
2. Click "Add Material". Screenshot the material type selector/combobox.
3. Select type "Lecture", set title "Introduction to HTML", category "In-class".
   Screenshot.
4. Save. Add a second material: type "Reading", title "HTML Reference Guide",
   category "Pre-class". Screenshot.
5. Add a third: type "Quiz", title "HTML Basics Check", category "Post-class".
   Screenshot.
6. Screenshot Module 1 showing materials grouped by category headers
   (Pre-class, In-class, Post-class).
7. Open the "Introduction to HTML" lecture in the rich text editor.
   Screenshot the editor.
8. Add a heading "What is HTML?", a paragraph of sample text, and a bulleted list
   with 3 items. Screenshot the editor with content.
9. Insert a simple table (e.g. 2 columns: "Element" / "Purpose", 3 rows).
   Screenshot.
10. If there's a toggle for advanced/raw editing mode, toggle it. Screenshot the
    raw view. Toggle back.
11. Change the material status from "Draft" to "Review". Screenshot showing the
    status badge update.
12. Reorder materials via drag-and-drop (move the Reading above the Lecture).
    Screenshot showing the new order.
13. Screenshot the Module 1 summary showing material count and type breakdown.

Read the material form components, the editor component (rich text / markdown),
the material list/topic component, and the status badge component.
```

---

## Guide 4: Learning Outcomes & Assessments

```
Write and run a Playwright guide script: guides/scripts/04-ulos-and-assessments.js

Prerequisite: The unit from Guide 2 exists. Navigate to it.

Walk through:
1. Navigate to the Learning Outcomes section. Screenshot.
2. Add a ULO manually: "Construct responsive web pages using HTML and CSS" at
   Bloom's level "Apply". Screenshot showing the ULO added.
3. Use bulk create: paste 3 more ULOs (one per line):
   - "Explain core web development concepts and standards"
   - "Design user interfaces following accessibility principles"
   - "Evaluate website performance using developer tools"
   Screenshot showing all 4 ULOs.
4. Reorder ULOs via drag-and-drop. Screenshot the reordered list.
5. Navigate to the Assessments section. Screenshot.
6. Click "Add Assessment". Screenshot the category combobox showing Higher Ed
   defaults.
7. Type "port" in the category search. Screenshot showing filtered results
   with "Portfolio" visible.
8. Select "Portfolio". Fill in: title "Portfolio Website", weight 40%, due
   Module 10. Screenshot the filled form.
9. Save. Add a second: category "Exam", title "Final Exam", weight 60%, due
   Module 12. Screenshot showing both assessments.
10. Screenshot showing the weight total at 100%.
11. Map both assessments to ULOs (select at least one each). Screenshot the
    mapping UI.
12. Open the rubric section on the Portfolio assessment. Select "Analytic" rubric
    type. Screenshot the rubric grid.
13. Edit criterion name to "Design Quality", set weight 30. Add "Code Quality"
    (weight 40) and "Documentation" (weight 30). Screenshot the completed rubric.
14. Save. Screenshot showing the purple "Rubric" badge on the assessment card.
15. Navigate to the Alignment/Analytics view. Screenshot the alignment report.

Read the ULO components, assessment form, rubric editor, category combobox, and
alignment/analytics view components.
```

---

## Guide 5: AI Scaffold & Content Generation

```
Write and run a Playwright guide script: guides/scripts/05-ai-scaffold.js

Walk through:
1. From the dashboard, create a new unit with just the title:
   "Data Science Essentials". Leave everything else at defaults. Screenshot.
2. Click "Quick Scaffold". Screenshot the scaffold loading/progress state.
3. When results appear, screenshot the scaffold preview (showing generated topics,
   ULOs, assessments, weekly plan).
4. Accept the scaffold. Screenshot the populated unit.
5. Open a material. Click "Generate Content". Screenshot the provider/style
   selection dialog.
6. Select a provider and teaching style. Screenshot showing content streaming in
   (capture mid-stream if possible, otherwise after completion).
7. Open the AI Sidebar. Screenshot it.
8. Type a question like "What are the key topics for week 3?" in the sidebar.
   Screenshot the contextual response.
9. Screenshot any "Save to Unit" option on the AI response.

Read the scaffold components, AI content generation components, AI sidebar
component, and the SSE/streaming handler to understand the UI states.

NOTE: This guide requires a working AI/LLM API key configured in settings.
If the key is not set, screenshot the prompt to configure it instead, and
add a note.
```

---

## Guide 6: Importing Existing Content

```
Write and run a Playwright guide script: guides/scripts/06-import-content.js

Prerequisite: A unit exists to import into.

Walk through:
1. Navigate to the Import section of a unit. Screenshot.
2. Upload a sample PDF file. Use a simple test PDF - create one first if needed
   with just a few paragraphs of course content. Screenshot the upload in progress
   or the file selected.
3. Screenshot the extraction results (detected structure: topics, outcomes,
   content sections).
4. In the review UI, screenshot showing how you can reassign content to specific
   modules.
5. Commit the import. Screenshot the unit with imported materials.
6. Open an imported material. Screenshot it in the editor ready for editing.
7. If there's an "Enhance with AI" button, screenshot it highlighted.
   (Don't click it if it requires API calls - just show it's available.)
8. Navigate back to Import. Screenshot showing the file type options
   (PDF, PPTX, DOCX if visible).

Read the import components, file upload handler, review/mapping UI, and the
enhance feature component.

For the test PDF: create a minimal one with headings like "Week 1: Introduction",
"Learning Outcomes", and some body text. Save it to guides/test-files/sample.pdf
before running.
```

---

## Guide 7: Exporting Your Unit

```
Write and run a Playwright guide script: guides/scripts/07-export.js

Prerequisite: A unit with materials and assessments exists (from earlier guides).

Walk through:
1. Navigate to the Export section. Screenshot.
2. Screenshot the Target LMS dropdown showing options (Generic, Canvas, Moodle,
   Blackboard, Brightspace).
3. Select "Canvas" as the target. Screenshot.
4. Screenshot the export format options (IMS Common Cartridge, SCORM, HTML, PDF,
   DOCX).
5. Click export as HTML. Screenshot the download triggered / success state.
6. Click export as PDF. Screenshot.
7. Click export as DOCX. Screenshot.
8. If there's a "Copy to clipboard" option on a material, screenshot it
   highlighted.

Read the export page component, LMS selector, format options, and download
handler components.

NOTE: Don't actually wait for large file downloads to complete. Screenshot the
UI state when export is initiated.
```

---

## Guide 8: Quality Dashboard & Recommendations

```
Write and run a Playwright guide script: guides/scripts/08-quality-dashboard.js

Prerequisite: A unit with several weeks of content exists (from earlier guides).

Walk through:
1. Navigate to the Analytics/Dashboard view. Screenshot.
2. Screenshot the unit overview (counts: ULOs, materials, assessments, weight).
3. Screenshot the unit progress display (completion percentage, draft vs published).
4. Screenshot the weekly workload analysis chart.
5. Screenshot the Bloom's taxonomy distribution.
6. Run unit validation. Screenshot any flagged issues.
7. Navigate to the Quality tab. Screenshot the Quality Dashboard showing the
   overall score (A-F) and 6-dimension breakdown.
8. Screenshot the per-week quality scores grid.
9. Click "Get AI Recommendations". Screenshot the AI suggestions
   (or screenshot the button if API not available).
10. Scroll to the UDL Dashboard. Screenshot showing the star rating and 4
    sub-scores (Representation, Engagement, Action & Expression, Accessibility).
11. Screenshot any UDL improvement suggestions.

Read the analytics/dashboard components, quality score components, UDL dashboard,
validation runner, and recommendation components.
```

---

## Running All Guides

Once all scripts are written and tested individually, you can create a runner:

```
Create a script guides/run-all.js that executes all 8 guide scripts in sequence.
Add a 2-second delay between scripts. If a script fails, log the error and
continue with the next one. At the end, print a summary of which guides
succeeded and which failed, plus the total screenshot count per guide.
```

---

## Post-Processing (Optional)

```
After all screenshots are generated, create a script guides/build-guide.js that:
1. Reads all screenshots from guides/screenshots/
2. Generates a markdown file for each guide with the screenshots embedded
   as images, grouped by guide, with the filename slug converted to a
   readable caption (e.g. "02-credentials-entered" becomes "Credentials Entered")
3. Outputs to guides/output/
4. Optionally generates a single combined HTML file with all guides as sections,
   with a table of contents at the top
```
