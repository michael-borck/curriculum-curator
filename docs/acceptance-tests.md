# Acceptance Tests — Curriculum Curator

> Manual test scenarios covering core user journeys.
> Each scenario chains multiple user stories into a realistic end-to-end workflow.
>
> **How to use:** Work through each scenario in order. Tick the checkbox when a step passes.
> Earlier scenarios set up data used by later ones (e.g. Scenario 1 creates the account used everywhere).

---

## Scenario 1 — Registration, Login & Settings

**Covers:** 10.1, 10.2, 10.5, 10.6, 10.7

- [ ] 1. Open the app. Click "Register". Fill in email, full name, password. Submit.
- [ ] 2. Registration succeeds — you are redirected to login (or auto-logged-in).
- [ ] 3. Log in with the credentials you just created. A JWT session is established (you land on the dashboard).
- [ ] 4. Navigate to **Settings**. Set your preferred teaching style (e.g. "Problem-Based Learning").
- [ ] 5. On the same settings page, enter an LLM API key (OpenAI or Anthropic). Save.
- [ ] 6. Verify the key is saved (page reload shows the key masked but present).
- [ ] 7. *(Optional — if Ollama is installed)* Select "Ollama" as AI provider. Verify the app detects the local instance.

---

## Scenario 2 — Create a Unit with Custom Topic Label

**Covers:** 1.1, 1.2, 1.3, topic_label feature, 17.1

- [ ] 1. From the dashboard, click **Create Unit**.
- [ ] 2. Fill in: title "Web Development Fundamentals", code "ICT101", credits 12, semester "S1 2026", 12 weeks.
- [ ] 3. Set the topic label to "Module" (instead of default "Week"). Save the unit.
- [ ] 4. Verify the unit page shows "Module 1", "Module 2", etc. — not "Week".
- [ ] 5. Set a teaching philosophy (e.g. "Constructivist"). Verify it saves.
- [ ] 6. Add topic titles for Modules 1–3 (e.g. "HTML Basics", "CSS Layout", "JavaScript Intro"). Verify they appear in the sidebar/list.
- [ ] 7. Verify you can work in any order — skip to Module 3 and add content there without completing Module 1 first.

---

## Scenario 3 — ULOs, Assessments & Alignment

**Covers:** 2.1–2.8, 4.1–4.6, 7.4–7.6

- [ ] 1. In the unit from Scenario 2, navigate to **Learning Outcomes**.
- [ ] 2. Add a ULO manually: "Construct responsive web pages using HTML and CSS" at Bloom's level "Apply". Verify it saves.
- [ ] 3. Use **bulk create** — paste 3 more ULOs (one per line). Verify all 3 appear.
- [ ] 4. Reorder ULOs by drag-and-drop. Verify the new order persists after page reload.
- [ ] 5. Navigate to **Assessments**. Add an assessment: "Portfolio Website", type "Project", weight 40%, due Module 10.
- [ ] 6. Add a second assessment: "Final Exam", weight 60%, due Module 12.
- [ ] 7. Verify the weight total shows 100% (no validation error).
- [ ] 8. Change one weight to 50% — verify a validation warning appears (total != 100%).
- [ ] 9. Fix the weight back. Map both assessments to ULOs (select at least one ULO per assessment).
- [ ] 10. Navigate to the **Alignment** or **Analytics** view. Verify the alignment report shows ULO coverage across materials and assessments.
- [ ] 11. Verify the **quality score** is visible (graded A–F) and any validation warnings are listed.
- [ ] 12. Check that recommendations are shown for improving the unit.

---

## Scenario 4 — Materials & Rich Text Editor

**Covers:** 3.1–3.9, 15.1–15.4, 15.7, 15.8, 2.7

- [ ] 1. In Module 1 of the unit, click **Add Material**. Select type "Lecture", title "Introduction to HTML".
- [ ] 2. Open the material in the **rich text editor**. Add a heading, a paragraph, a bulleted list, and a code block with HTML.
- [ ] 3. Insert a table (e.g. comparing HTML elements). Verify it renders correctly.
- [ ] 4. Toggle to **advanced editing mode** — verify raw markdown/YAML is visible. Toggle back to simple mode.
- [ ] 5. Insert an image by URL. Verify it renders in the editor.
- [ ] 6. Upload an image from your computer. Verify it appears in the material.
- [ ] 7. Insert a YouTube embed link. Verify the video preview renders.
- [ ] 8. Add a Mermaid diagram (e.g. a simple flowchart). Verify the live preview renders.
- [ ] 9. Set the material status from "Draft" to "Review". Verify the status badge updates.
- [ ] 10. Add a second material to Module 1 (type "Tutorial"). Reorder materials via drag-and-drop. Verify the order persists.
- [ ] 11. Duplicate the lecture material to Module 2. Verify it appears there with the same content.
- [ ] 12. Check the Module 1 summary — verify material count and type breakdown are shown.
- [ ] 13. Use the filter/search to find materials by type or search term.
- [ ] 14. Define a Local Learning Outcome (LLO) on the lecture material. Verify it saves.

---

## Scenario 5 — AI Scaffold, Fill Gaps & AI Sidebar

**Covers:** 1.6, 1.7, 5.1–5.11, 17.3

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

**Covers:** 6.1–6.4, 6.6, 6.7, 1.4

- [ ] 1. Navigate to **Import** for a unit.
- [ ] 2. Upload a PDF file (e.g. an existing unit outline or lecture notes).
- [ ] 3. Verify the system extracts structure (topics, outcomes, content sections).
- [ ] 4. In the **review UI**, correct any mis-detected items. Assign content to specific weeks/modules.
- [ ] 5. Commit the import. Verify materials appear in the unit at the assigned weeks.
- [ ] 6. Verify you land in the normal editing flow — open an imported material and make changes.
- [ ] 7. Click **Enhance with AI** on an imported material. Verify the content improves (better formatting, added examples) while preserving the original meaning.
- [ ] 8. Upload a PPTX file. Verify text and images are extracted and converted to editable content.
- [ ] 9. Upload a DOCX file. Verify it is parsed into materials.

---

## Scenario 8 — Package Import (ZIP, IMSCC, SCORM)

**Covers:** 6.5, 9.2, 9.7

- [ ] 1. Prepare or obtain an .imscc file (exported from a Moodle/Canvas course, or from Scenario 9).
- [ ] 2. Import the .imscc file. Verify the system creates a unit with the imported structure (topics, materials, assessments).
- [ ] 3. Verify imported content is editable — open a material and make changes.
- [ ] 4. Import a SCORM 1.2 package. Verify the system creates a unit from it.
- [ ] 5. Upload a ZIP file containing multiple documents. Verify batch analysis detects the files and allows import.

---

## Scenario 9 — Export (HTML, SCORM, IMSCC, Document)

**Covers:** 9.1, 9.3–9.6

- [ ] 1. In a unit with materials and assessments (from Scenario 2 or 5), go to **Export**.
- [ ] 2. Export as **IMS Common Cartridge** (.imscc). Download and verify the file is valid (non-zero size, correct extension).
- [ ] 3. Export as **SCORM 1.2** package. Download and verify.
- [ ] 4. Export as **standalone HTML**. Open the HTML file in a browser — verify content renders with inline styles.
- [ ] 5. Export as **PDF**. Verify the document contains unit content with proper formatting.
- [ ] 6. Export as **DOCX**. Open in a word processor — verify content and structure.
- [ ] 7. Use **Copy to clipboard** on a material. Paste into a rich text field (e.g. email or LMS) — verify formatting is preserved.
- [ ] 8. *(Validation)* Import the .imscc file from step 2 back into the app (round-trip). Verify the structure matches the original.

---

## Scenario 10 — Quality Validation & Analytics

**Covers:** 7.1, 7.2, 7.5–7.8, 8.1–8.5

- [ ] 1. Open a unit with several weeks of materials. Navigate to the **Analytics** or **Dashboard** view.
- [ ] 2. Verify the **unit overview** shows counts: ULOs, materials, assessments, total assessment weight.
- [ ] 3. Verify **unit progress** is displayed (completion percentage, draft vs published counts).
- [ ] 4. Check **weekly workload analysis** — verify duration per week and assessment load are charted.
- [ ] 5. View **Bloom's taxonomy distribution** and material type breakdowns.
- [ ] 6. Run **unit validation**. Verify it flags any issues (missing ULOs, weight imbalance, empty weeks).
- [ ] 7. Open a material. Check the **quality panel** — verify readability score (Flesch-Kincaid) is shown.
- [ ] 8. Verify **structure validation** results are shown (heading hierarchy, section balance).
- [ ] 9. If issues are found, click **Auto-fix All** (markdown cleanup). Verify the content improves.
- [ ] 10. Export unit data as **JSON or CSV**. Verify the download contains structured unit data.

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

## Coverage Matrix

| Category | Stories | Scenarios |
|----------|---------|-----------|
| 1. Unit Setup | 1.1–1.7 | 2, 5, 7 |
| 2. Learning Outcomes | 2.1–2.8 | 3, 4, 5 |
| 3. Weekly Materials | 3.1–3.9 | 4 |
| 4. Assessments | 4.1–4.6 | 3 |
| 5. AI Content | 5.1–5.11 | 5 |
| 6. Import | 6.1–6.7 | 7, 8 |
| 7. Quality | 7.1–7.8 | 3, 10 |
| 8. Analytics | 8.1–8.5 | 10 |
| 9. Export | 9.1–9.7 | 8, 9 |
| 10. Auth & Settings | 10.1–10.7 | 1 |
| 12. Research | 12.1–12.4 | 11 |
| 13. Version Control | 13.1–13.4 | 12 |
| 14. Learning Design | 14.1–14.4 | 6 |
| 15. Editor | 15.1–15.4, 15.7–15.9 | 4 |
| 17. Flexibility | 17.1–17.3 | 2, 5 |

### Not Covered (by design)

| Category | Reason |
|----------|--------|
| 11. Administration | Separate admin role — test independently |
| 16. Desktop App | Different build target (Electron) — test via desktop installer |
| P4 Planned (7.3, 9.8–9.10) | Not yet implemented |
| 15.5, 15.6 | Cut from scope |

*Last updated: 2026-02-22*
