# Acceptance Tests — Curriculum Curator

> Manual test scenarios covering core user journeys.
> Each scenario chains multiple user stories into a realistic end-to-end workflow.
>
> **How to use:** Work through each scenario in order. Tick the checkbox when a step passes.
> Earlier scenarios set up data used by later ones (e.g. Scenario 1 creates the account used everywhere).

---

## Scenario 1 — Registration, Login & Settings

**Covers:** 10.1, 10.2, 10.5, 10.6, 10.7, 17A.1

- [ ] 1. Open the app. Click "Register". Fill in email, full name, password. Submit.
- [ ] 2. Registration succeeds — you are redirected to login (or auto-logged-in).
- [ ] 3. Log in with the credentials you just created. A JWT session is established (you land on the dashboard).
- [ ] 4. Navigate to **Settings**. Set your preferred teaching style (e.g. "Problem-Based Learning").
- [ ] 5. Set your **education sector** to "Higher Education". Save. Verify it persists after reload.
- [ ] 6. On the same settings page, enter an LLM API key (OpenAI or Anthropic). Save.
- [ ] 7. Verify the key is saved (page reload shows the key masked but present).
- [ ] 8. *(Optional — if Ollama is installed)* Select "Ollama" as AI provider. Verify the app detects the local instance.

---

## Scenario 2 — Create a Unit with Custom Topic Label

**Covers:** 1.1, 1.2, 1.3, 1.8, 1.9, 1.10, 18.1

- [ ] 1. From the dashboard, click **Create Unit**.
- [ ] 2. Verify the form is streamlined — only essential fields (title, code, credits, semester, weeks) are shown upfront.
- [ ] 3. Select a **structure preset** (e.g. "Lecture-heavy" or "Practical"). Verify the form pre-fills sensible defaults.
- [ ] 4. Fill in: title "Web Development Fundamentals", code "ICT101", credits 12, semester "S1 2026", 12 weeks.
- [ ] 5. Set the topic label to "Module" (instead of default "Week"). Save the unit.
- [ ] 6. Verify the unit page shows "Module 1", "Module 2", etc. — not "Week".
- [ ] 7. Set a teaching philosophy (e.g. "Constructivist"). Verify it saves.
- [ ] 8. Add topic titles for Modules 1–3 (e.g. "HTML Basics", "CSS Layout", "JavaScript Intro"). Verify they appear in the sidebar/list.
- [ ] 9. Verify you can work in any order — skip to Module 3 and add content there without completing Module 1 first.
- [ ] 10. Create a second unit using **Create and Import** — verify you land directly on the import flow after creation.

---

## Scenario 3 — ULOs, Assessments, Rubrics & Alignment

**Covers:** 2.1–2.8, 4.1–4.10, 7.4–7.6, 17A.3, 17A.4

- [ ] 1. In the unit from Scenario 2, navigate to **Learning Outcomes**.
- [ ] 2. Add a ULO manually: "Construct responsive web pages using HTML and CSS" at Bloom's level "Apply". Verify it saves.
- [ ] 3. Use **bulk create** — paste 3 more ULOs (one per line). Verify all 3 appear.
- [ ] 4. Reorder ULOs by drag-and-drop. Verify the new order persists after page reload.
- [ ] 5. Navigate to **Assessments**. Click **Add Assessment**. Open the **Category** combobox. Verify Higher Ed defaults appear first (Exam, Assignment, Quiz, Project, Paper, Presentation, Lab Report) with an "All categories" section below.
- [ ] 6. Type "port" in the category search box. Verify the list filters to show "Portfolio" (and any other matches). Select "Portfolio". Set title "Portfolio Website", weight 40%, due Module 10.
- [ ] 7. Add a second assessment: category "Exam", title "Final Exam", weight 60%, due Module 12.
- [ ] 8. Verify the weight total shows 100% (no validation error).
- [ ] 9. Change one weight to 50% — verify a validation warning appears (total != 100%).
- [ ] 10. Fix the weight back. Map both assessments to ULOs (select at least one ULO per assessment).
- [ ] 11. Navigate to the **Alignment** or **Analytics** view. Verify the alignment report shows ULO coverage across materials and assessments.
- [ ] 12. Verify the **quality score** is visible (graded A–F) and any validation warnings are listed.
- [ ] 13. Check that recommendations are shown for improving the unit.
- [ ] 14. Add a third assessment. In the category combobox, click **Custom...** and type "Design Critique". Press Enter. Verify the category saves as "design_critique" and displays as a neutral gray pill labelled "Design Critique".
- [ ] 15. Edit the "Portfolio Website" assessment. Expand the **Rubric** section (collapsed by default, showing "No rubric").
- [ ] 16. Select **Analytic** rubric type. Verify a grid appears with 4 default levels (Excellent/Good/Satisfactory/Unsatisfactory) and 1 criterion row.
- [ ] 17. Edit the criterion name to "Design Quality". Set weight to 30. Fill in cell descriptions for each level. Add a second criterion "Code Quality" (weight 40) and a third "Documentation" (weight 30).
- [ ] 18. Add a 5th level column (e.g. "Outstanding"). Verify all criteria rows gain an extra cell. Remove the column — verify all rows shrink back.
- [ ] 19. Set Total Points to 100. Save the assessment. Reload the page — verify the rubric data persists (4 levels, 3 criteria, all cell text intact).
- [ ] 20. Verify the assessment card now shows a purple **Rubric** badge.
- [ ] 21. Collapse the Rubric section. Verify the summary reads "Analytic: 3 criteria, 4 levels".
- [ ] 22. Edit the assessment again. Change the rubric type to **Holistic**. Verify a confirmation dialog warns about data reset. Accept.
- [ ] 23. Verify the editor now shows level cards with label, points, and a paragraph textarea (no criteria rows). Add descriptions to each level. Save.
- [ ] 24. Edit the "Final Exam" assessment. Add a **Checklist** rubric. Verify the editor shows simple criteria rows with a checkbox placeholder. Add 5 criteria. Save and reload — verify persistence.
- [ ] 25. Create a new assessment "Peer Review" (formative, 0%). Add a **Single-Point** rubric. Verify the editor shows a 3-column layout: "Concerns" (read-only) | criterion name + proficient description (editable) | "Advanced" (read-only). Add 3 criteria. Save.
- [ ] 26. On the "Peer Review" assessment, click **Remove Rubric** inside the rubric editor. Confirm. Verify the rubric is cleared and the card no longer shows a Rubric badge.

---

## Scenario 4 — Materials & Rich Text Editor

**Covers:** 3.1–3.12, 15.1–15.4, 15.7–15.9, 2.7, 17A.2, 17A.4

- [ ] 1. In Module 1 of the unit, click **Add Material**. Open the **Type** combobox. Verify Higher Ed defaults appear first (Lecture, Tutorial, Lab, Workshop, Seminar, Independent). Select "Lecture", title "Introduction to HTML". Set category to **In-class**.
- [ ] 2. Add a second material: type "Reading", title "HTML Reference Guide", category **Pre-class**.
- [ ] 3. Add a third material: type "Quiz", title "HTML Basics Check", category **Post-class**.
- [ ] 4. Verify Module 1 shows materials grouped under category headers (Pre-class, In-class, Post-class) — not a flat list.
- [ ] 5. Open the lecture material in the **rich text editor**. Add a heading, a paragraph, a bulleted list, and a code block with HTML.
- [ ] 6. Insert a table (e.g. comparing HTML elements). Verify it renders correctly.
- [ ] 7. Toggle to **advanced editing mode** — verify raw markdown/YAML is visible. Toggle back to simple mode.
- [ ] 8. Insert an image by URL. Verify it renders in the editor.
- [ ] 9. Upload an image from your computer. Verify it appears in the material.
- [ ] 10. Insert a YouTube embed link. Verify the video preview renders.
- [ ] 11. Add a Mermaid diagram (e.g. a simple flowchart). Verify the live preview renders.
- [ ] 12. Use the **image prompt generator** (wand button in editor toolbar). Pick a style and aspect ratio — verify a copy-paste prompt is generated.
- [ ] 13. Set the material status from "Draft" to "Review". Verify the status badge updates.
- [ ] 14. Reorder materials within Module 1 via drag-and-drop. Verify the order persists.
- [ ] 15. Duplicate the lecture material to Module 2. Verify it appears there with the same content **and the same category** (In-class).
- [ ] 16. Check the Module 1 summary — verify material count and type breakdown are shown.
- [ ] 17. Use the filter/search to find materials by type or search term.
- [ ] 18. Define a Local Learning Outcome (LLO) on the lecture material. Verify it saves.
- [ ] 19. Click **Add Module** at the bottom of the accordion. Verify a new module appears (Module 13).
- [ ] 20. Click the delete button on the empty Module 13. Verify it disappears and week count returns to 12.
- [ ] 21. Click **Apply Module 1 Structure**. Choose **Copy material stubs**. Verify all empty modules now have the same 3 materials (same titles, types, categories) but no content.
- [ ] 22. Delete materials from Modules 4–6. Click **Apply Module 1 Structure** again → choose **Categories only**. Verify Modules 4–6 now have one placeholder per category (Pre-class, In-class, Post-class) but modules 2, 3, 7–12 are unchanged (non-destructive).
- [ ] 23. Delete a module that has materials. Verify you get a confirmation dialog. Confirm — verify the module is removed and subsequent modules shift down.
- [ ] 24. Add a material. In the Type combobox, click **Custom...** and type "Studio Session". Submit. Verify it saves and displays as a neutral gray pill labelled "Studio Session".

---

## Scenario 5 — AI Scaffold, Fill Gaps & AI Sidebar

**Covers:** 1.6, 1.7, 5.1–5.11, 18.3

- [ ] 1. Create a new unit with just a title: "Data Science Essentials". Leave everything else empty.
- [ ] 2. Click **Quick Scaffold**. Verify AI generates topics, ULOs, assessments, and a weekly plan.
- [ ] 3. Review the scaffold results before accepting. Verify you can adjust items before committing.
- [ ] 4. Accept the scaffold. Verify the unit is populated with the generated structure.
- [ ] 5. Delete a few ULOs and one topic, then use **Fill Gaps**. Verify AI detects what's missing and offers to generate replacements.
- [ ] 6. Open a material. Click **Generate Content** — select an LLM provider and a teaching style. Verify content streams in via SSE.
- [ ] 7. Verify the generated content reflects the chosen teaching philosophy.
- [ ] 8. With existing content in the editor, click **Enhance**. Verify AI improves the content while preserving the core ideas.
- [ ] 9. Open the **AI Sidebar**. Ask it a question about the unit. Verify the response is contextual (references ULOs, topics, or materials from this unit).
- [ ] 10. In the AI sidebar, use **Save to Unit** on a response — verify you can choose the content type and target material, and the content appears in the unit.
- [ ] 11. Use **AI-assist** on a text field (e.g. a ULO description) — verify inline AI suggestions work outside the sidebar.

---

## Scenario 6 — Learning Design & Tasks

**Covers:** 14.1–14.4

- [ ] 1. In any unit, navigate to the **Learning Design** (LRD) section.
- [ ] 2. Create a structured Learning Requirements Document — fill in the required fields (objectives, constraints, audience, etc.).
- [ ] 3. Submit the LRD for approval. Verify the status changes.
- [ ] 4. Approve the LRD. Verify a prioritised **task list** is generated from it.
- [ ] 5. Work through a few tasks — mark some as complete. Verify progress tracking updates.

---

## Scenario 7 — File Import & Enhance

**Covers:** 6.1–6.4, 6.6, 6.7, 6.8, 1.4

- [ ] 1. Navigate to **Import** for a unit.
- [ ] 2. Upload a PDF file (e.g. an existing unit outline or lecture notes).
- [ ] 3. Verify the system extracts structure (topics, outcomes, content sections).
- [ ] 4. In the **review UI**, correct any mis-detected items. Assign content to specific weeks/modules.
- [ ] 5. Commit the import. Verify materials appear in the unit at the assigned weeks.
- [ ] 6. Verify you land in the normal editing flow — open an imported material and make changes.
- [ ] 7. Click **Enhance with AI** on an imported material. Verify the content improves (better formatting, added examples) while preserving the original meaning.
- [ ] 8. Upload a PPTX file. Verify text and images are extracted and converted to editable content.
- [ ] 9. Upload a DOCX file. Verify it is parsed into materials.
- [ ] 10. Upload a branded PPTX (with custom theme/colours). In **Import Options**, tick **"Save PPTX theme as export template"**. Import.
- [ ] 11. Verify a green checkmark appears next to the template checkbox after import completes.
- [ ] 12. Navigate to **Settings > Export**. Verify the extracted template appears in the template list (filename ends with "(extracted theme)").
- [ ] 13. Import a PPTX *without* the template checkbox ticked. Verify no new template is created.

---

## Scenario 8 — Package Import (ZIP, IMSCC, SCORM)

**Covers:** 6.5, 9.2, 9.7, 9.8, 9.9

- [ ] 1. Prepare or obtain an .imscc file (exported from a Moodle/Canvas course, or from Scenario 9).
- [ ] 2. Import the .imscc file. Verify the system creates a unit with the imported structure (topics, materials, assessments).
- [ ] 3. If the package contained QTI quiz data, verify quiz questions are imported as structured `QuizQuestion` rows (question text, options, correct answers, points).
- [ ] 4. Verify imported content is editable — open a material and make changes.
- [ ] 5. Import an .imscc or SCORM package originally exported from Canvas or Moodle. Verify the importer detects the source LMS and uses its terminology to correctly classify materials vs assessments (e.g. Canvas "Assignments" → assessments).
- [ ] 6. Import a SCORM 1.2 package. Verify the system creates a unit from it.
- [ ] 7. Upload a ZIP file containing multiple documents. Verify batch analysis detects the files and allows import.

---

## Scenario 9 — Export (HTML, SCORM, IMSCC, Document, QTI)

**Covers:** 9.1, 9.3–9.6, 9.10–9.12

- [ ] 1. In a unit with materials, assessments, and quiz questions (from Scenario 2 or 5), go to **Export**.
- [ ] 2. In the export menu, verify the **Target LMS** dropdown is visible with options: Generic, Canvas, Moodle, Blackboard, Brightspace.
- [ ] 3. Select **Canvas** as the target LMS. Export as **IMS Common Cartridge** (.imscc). Download and verify the file is valid.
- [ ] 4. Export as **SCORM 1.2** package with a different target LMS (e.g. Moodle). Download and verify.
- [ ] 4. Export as **standalone HTML**. Open the HTML file in a browser — verify content renders with inline styles.
- [ ] 5. Export as **PDF**. Verify the document contains unit content with proper formatting.
- [ ] 6. Export as **DOCX**. Open in a word processor — verify content and structure.
- [ ] 7. Use **Copy to clipboard** on a material. Paste into a rich text field (e.g. email or LMS) — verify formatting is preserved.
- [ ] 8. Export **QTI 2.1** quiz package (standalone ZIP). Verify it contains quiz XML with question data.
- [ ] 9. Verify the .imscc from step 2 contains embedded QTI quiz items (not just static description pages).
- [ ] 10. *(Validation)* Import the .imscc file from step 2 back into the app (round-trip). Verify the structure matches the original.

---

## Scenario 10 — Quality Validation, UDL & Analytics

**Covers:** 7.1–7.3, 7.5–7.10, 8.1–8.5

- [ ] 1. Open a unit with several weeks of materials. Navigate to the **Analytics** or **Dashboard** view.
- [ ] 2. Verify the **unit overview** shows counts: ULOs, materials, assessments, total assessment weight.
- [ ] 3. Verify **unit progress** is displayed (completion percentage, draft vs published counts).
- [ ] 4. Check **weekly workload analysis** — verify duration per week and assessment load are charted.
- [ ] 5. View **Bloom's taxonomy distribution** and material type breakdowns.
- [ ] 6. Run **unit validation**. Verify it flags any issues (missing ULOs, weight imbalance, empty weeks).
- [ ] 7. Open a material. Check the **quality panel** — verify readability score (Flesch-Kincaid) is shown.
- [ ] 8. Verify **structure validation** results are shown (heading hierarchy, section balance).
- [ ] 9. Verify **accessibility checks** run (alt text, heading structure, link text, table headers). Confirm any WCAG issues are reported.
- [ ] 10. If issues are found, click **Auto-fix All** (markdown cleanup). Verify the content improves.
- [ ] 11. Export unit data as **JSON or CSV**. Verify the download contains structured unit data.
- [ ] 12. Navigate to the **Quality** tab. Verify the **Quality Dashboard** shows an overall score (A–F) and a 6-dimension breakdown (Completeness, Content Quality, ULO Alignment, Workload Balance, Material Diversity, Assessment Distribution).
- [ ] 13. Verify **per-week quality scores** are displayed in a grid.
- [ ] 14. Click **"Get AI Recommendations"**. Verify AI-generated improvement suggestions appear (with model attribution).
- [ ] 15. On the same tab, verify the **UDL Dashboard** is visible alongside the Quality Dashboard.
- [ ] 16. Verify UDL shows an overall star rating and 4 sub-scores: Representation, Engagement, Action & Expression, Accessibility.
- [ ] 17. Verify **per-week UDL scores** are displayed.
- [ ] 18. Verify **UDL improvement suggestions** are shown (e.g. "Week 3 relies solely on passive formats").
- [ ] 19. For a unit with no materials, verify UDL and Quality dashboards show a sensible empty state (not errors).

---

## Scenario 11 — Research & Scaffold from Sources

**Covers:** 12.1–12.4

- [ ] 1. Navigate to the **Research** page for a unit.
- [ ] 2. Search for academic sources related to the unit topic (e.g. "web development pedagogy").
- [ ] 3. Verify search results appear with titles, descriptions, and URLs.
- [ ] 4. Save several sources — verify metadata is captured (authors, year, URL).
- [ ] 5. Generate a citation for a saved source in **APA7** format. Verify it's correctly formatted.
- [ ] 6. Switch citation format to **Harvard** or **IEEE**. Verify the output changes.
- [ ] 7. Use **Scaffold from sources** — select saved sources and generate a unit structure based on them. Verify the scaffold reflects the research material.

---

## Scenario 12 — Version History & Restore

**Covers:** 13.1–13.4

- [ ] 1. Open a material with content (from any earlier scenario).
- [ ] 2. Make a change to the content. Click **Save Version** (commit). Add a commit message.
- [ ] 3. Make a second change and save another version.
- [ ] 4. Open **Version History**. Verify both versions are listed with timestamps and messages.
- [ ] 5. Select a previous version — verify the **diff view** highlights what changed between versions.
- [ ] 6. Click **Restore** on the first version. Verify the material content reverts to that version.
- [ ] 7. Verify the restored state is now the current content (and you can continue editing from here).

---

## Scenario 13 — Unit Settings & Feature Toggles

**Covers:** 1.11, 1.12, 7.10

- [ ] 1. Open a unit. Navigate to the **Settings** tab.
- [ ] 2. Verify academic details are editable (year, semester, delivery mode, credit points).
- [ ] 3. Change the delivery mode (e.g. "On-campus" → "Hybrid"). Save. Verify it persists after page reload.
- [ ] 4. Find the **Alignment & Accreditation** toggles. Verify toggles exist for Graduate Capabilities, AoL Mapping, SDG Mapping, and Custom Frameworks.
- [ ] 5. Disable **SDG Mapping**. Return to the **Structure** tab. Verify the SDG panel is hidden.
- [ ] 6. Re-enable SDG Mapping in Settings. Return to Structure — verify the panel is back.
- [ ] 7. Disable all accreditation toggles. Verify all mapping panels disappear from the Structure tab.
- [ ] 8. Find the **Quality Metrics** toggles. Verify 6 dimensions can be toggled individually (Completeness, Content Quality, ULO Alignment, Workload Balance, Material Diversity, Assessment Distribution).
- [ ] 9. Disable **Workload Balance**. Navigate to the Quality tab. Verify the Workload Balance dimension is hidden from the dashboard.
- [ ] 10. Find the **UDL Metrics** toggles. Verify 4 dimensions can be toggled (Representation, Engagement, Action & Expression, Accessibility).
- [ ] 11. Disable **Accessibility**. Navigate to the Quality tab. Verify the UDL Dashboard hides the Accessibility dimension.
- [ ] 12. Re-enable all toggles. Verify all dimensions reappear.
- [ ] 13. Set **Target Audience Level** to "High School". Verify UDL accessibility scores adjust (readability expectations change).

---

## Scenario 14 — Custom Alignment Frameworks

**Covers:** 1.12

- [ ] 1. Open a unit. Navigate to **Settings**. Enable **Custom Frameworks** if not already on.
- [ ] 2. Return to the **Structure** tab. Verify a Custom Frameworks panel is visible.
- [ ] 3. Click **Add Framework**. Select a preset (e.g. "Program Learning Outcomes"). Verify it pre-fills with default items.
- [ ] 4. Edit an item name. Add a new item. Delete an item. Save the framework.
- [ ] 5. Verify the framework appears with its items listed.
- [ ] 6. Map a ULO to one or more framework items. Verify the mapping saves.
- [ ] 7. Create a second framework (e.g. "ABET Criteria") from presets. Verify both frameworks display.
- [ ] 8. Delete a framework. Verify it disappears and ULO mappings to it are removed.

---

## Scenario 15 — Sector-Aware Defaults

**Covers:** 17A.1–17A.5

- [ ] 1. Navigate to **Settings**. Change education sector to **VET**. Save.
- [ ] 2. Create or open a unit. Add a material — open the **Type** combobox. Verify VET defaults appear first (Practical, Tutorial, Workshop, Simulation, Placement, Assessment).
- [ ] 3. Verify "All formats" section below contains the remaining formats (Lecture, Seminar, etc.).
- [ ] 4. Navigate to **Assessments**. Add an assessment — open the **Category** combobox. Verify VET defaults appear first (Practical Assessment, Skills Demonstration, Assignment, Portfolio, Project, Reflection).
- [ ] 5. Click **Custom...** in the category combobox. Type "Competency Logbook". Submit. Verify it saves and displays as a neutral gray pill.
- [ ] 6. Change sector to **K-12** in Settings. Return to the unit.
- [ ] 7. Add a material — verify K-12 defaults now appear first (Lesson, Workshop, Excursion, Independent, Assessment).
- [ ] 8. Add an assessment — verify K-12 defaults now appear first (Test, Assignment, Project, Homework, Presentation, Participation).
- [ ] 9. Verify previously saved custom values ("Competency Logbook", "Design Critique") still display correctly with their neutral gray pill styling.
- [ ] 10. Change sector to **Corporate**. Add an assessment — verify Corporate defaults (Case Study, Presentation, Project, Reflection, Peer Review, Portfolio) appear first.

---

## Scenario 16 — Unit Outline Import

**Covers:** 1.13, 1.14, 1.15, 6.9, 6.10

### Happy Path

- [ ] 1. From the dashboard, click **Create from Outline** (or equivalent entry point).
- [ ] 2. Verify the upload form shows a file input (accepts PDF, DOCX, TXT) and a parser dropdown.
- [ ] 3. Verify the parser dropdown lists "Generic (AI-Powered)" (selected by default) and "Curtin University".
- [ ] 4. Upload a Curtin University unit outline PDF. Select "Curtin University" parser. Click Parse.
- [ ] 5. Verify the review form appears with extracted data: unit code, title, description, credit points, duration, semester.
- [ ] 6. Verify extracted **Learning Outcomes** are shown in an editable table with Bloom's level dropdowns.
- [ ] 7. Verify extracted **Weekly Schedule** is shown in an editable table (week number, topic title, activities, readings).
- [ ] 8. Verify extracted **Assessments** are shown in an editable table (title, type, weight, due week).
- [ ] 9. Verify extracted **Textbooks** are shown (title, authors, required/recommended toggle).
- [ ] 10. Verify **Supplementary Info** section shows unmapped content with Keep/Drop toggles for each item.
- [ ] 11. Edit a ULO's text in the review form. Verify the change is reflected.
- [ ] 12. Remove an extracted assessment (delete row). Verify it disappears.
- [ ] 13. Drop a supplementary info item. Keep another.
- [ ] 14. Click **Create Unit**. Verify the unit is created with all reviewed data.
- [ ] 15. Verify the created unit has: correct code, title, ULOs (with edited text), weekly topics, assessments (minus the deleted one), textbooks in unit metadata.
- [ ] 16. Verify kept supplementary info is stored in `unit_metadata["supplementary_info"]`.
- [ ] 17. Verify dropped supplementary info is not stored.

### Generic Parser

- [ ] 18. Upload a non-Curtin university outline PDF with "Generic (AI-Powered)" parser selected.
- [ ] 19. Verify extraction produces reasonable results (at minimum: title, code, ULOs, weekly topics).
- [ ] 20. Verify a confidence score is displayed.
- [ ] 21. Upload a DOCX outline. Verify it parses successfully.
- [ ] 22. Upload a TXT outline. Verify it parses successfully.

### Parser Selection & Fallback

- [ ] 23. Verify `GET /api/import/outline/parsers` returns available parsers with id, name, description, and supported formats.
- [ ] 24. Upload a non-Curtin document with Curtin parser selected. Verify it falls back to generic parser with a notification.
- [ ] 25. Switch parser in the dropdown and re-parse. Verify results update.

### Validation & Edge Cases

- [ ] 26. Verify assessment weights are validated (warning if sum != 100%) before creation.
- [ ] 27. Verify Create button is disabled until required fields (title, code) are filled.
- [ ] 28. Upload an empty or near-empty document. Verify a meaningful error message (not a crash).
- [ ] 29. Upload a non-outline document (e.g. a novel excerpt). Verify generic parser extracts what it can with low confidence.
- [ ] 30. Upload a large document (30+ pages). Verify it handles gracefully (completes or shows a page-limit message).
- [ ] 31. Attempt to create a unit with a duplicate code+semester+year. Verify validation error — user can edit the code in the form.

---

## Coverage Matrix

| Category | Stories | Scenarios |
|----------|---------|-----------|
| 1. Unit Setup | 1.1–1.15 | 2, 5, 7, 13, 14, 16 |
| 2. Learning Outcomes | 2.1–2.8 | 3, 4, 5 |
| 3. Weekly Materials | 3.1–3.12 | 4 |
| 4. Assessments | 4.1–4.10 | 3 |
| 5. AI Content | 5.1–5.11 | 5 |
| 6. Import | 6.1–6.10 | 7, 8, 16 |
| 7. Quality | 7.1–7.10 | 3, 10, 13 |
| 8. Analytics | 8.1–8.5 | 10 |
| 9. Export & LMS | 9.1–9.12 | 8, 9 |
| 10. Auth & Settings | 10.1–10.7 | 1 |
| 12. Research | 12.1–12.4 | 11 |
| 13. Version Control | 13.1–13.4 | 12 |
| 14. Learning Design | 14.1–14.4 | 6 |
| 15. Editor | 15.1–15.4, 15.7–15.9 | 4 |
| 17. Sector & Personalisation | 17A.1–17A.5 | 1, 3, 4, 15 |
| 18. Flexibility | 18.1–18.3 | 2, 5 |

### Not Covered (by design)

| Category | Reason |
|----------|--------|
| 11. Administration | Separate admin role — test independently |
| 16. Desktop App | Different build target (Electron) — test via desktop installer |
| 15.5, 15.6 | Cut from scope |

*Last updated: 2026-03-09*
