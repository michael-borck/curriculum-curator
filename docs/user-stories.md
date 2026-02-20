# User Stories — Curriculum Curator

> Living document tracking what the system does and should do.
> Status: **Done** | **Partial** | **Planned** | **Cut**
>
> Phase tags (P1–P4) indicate implementation priority — see
> [implementation-plan.md](implementation-plan.md) for the phased roadmap.

## Personas

| Alias | Role | Primary Goal |
|-------|------|-------------|
| **Creator** | Lecturer building a new unit from scratch | Generate complete, aligned materials fast |
| **Enhancer** | Educator with existing materials to modernise | Improve legacy content without starting over |
| **Curator** | Department head / quality assurer | Ensure consistency and standards across units |
| **Admin** | System administrator | Manage users, providers, and platform config |

---

## 1. Unit Setup & Structure

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 1.1 | As a **Creator**, I want to create a new unit with metadata (title, code, credits, semester, weeks) so I have a container for all my materials. | P1 | **Done** |
| 1.2 | As a **Creator**, I want to define weekly topics for my unit so content is organised by teaching week. | P1 | **Done** |
| 1.3 | As a **Creator**, I want to set a teaching philosophy (from 9 options) for my unit so AI-generated content matches my pedagogical approach. | P1 | **Done** |
| 1.4 | As an **Enhancer**, I want to import a unit outline (PDF/document) so the system can pre-populate structure from my existing syllabus. | P2 | **Partial** — upload + PDF parsing works, review UI incomplete |
| 1.5 | As a **Creator**, I want to duplicate an existing unit as a starting point for a new semester. | P3 | **Planned** |
| 1.6 | As a **Creator**, I want to type just a title/topic and have AI scaffold an entire unit (topics, ULOs, assessments, weekly plan) in one action. | P2 | **Partial** — `workflow_structure_creator` exists, needs one-click UX |
| 1.7 | As a **Creator**, I want the system to show me what's missing in my unit and offer to fill the gaps (generate missing ULOs, topics, materials, assessments). | P2 | **Planned** — analytics knows gaps, no "fill" action yet |

## 2. Learning Outcomes

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 2.1 | As a **Creator**, I want to define Unit Learning Outcomes (ULOs) with Bloom's taxonomy levels so I can track what students should achieve. | P1 | **Done** |
| 2.2 | As a **Creator**, I want to bulk-create ULOs (e.g. paste a list) so I don't have to enter them one by one. | P1 | **Done** |
| 2.3 | As a **Creator**, I want to reorder ULOs by drag-and-drop so they reflect my preferred sequence. | P1 | **Done** |
| 2.4 | As a **Creator**, I want to map ULOs to materials and assessments so I can verify constructive alignment. | P1 | **Done** |
| 2.5 | As a **Creator**, I want to see a coverage report showing which ULOs are covered by materials and assessments (and which have gaps). | P1 | **Done** |
| 2.6 | As a **Curator**, I want to map ULOs to accreditation graduate attributes so I can demonstrate standards compliance. | P1 | **Done** |
| 2.7 | As a **Creator**, I want to define Local Learning Outcomes (LLOs) per material for granular weekly objectives. | P1 | **Done** |
| 2.8 | As a **Creator**, I want AI to suggest ULOs based on my unit title and description so I have a starting point. | P2 | **Planned** |

## 3. Weekly Materials

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 3.1 | As a **Creator**, I want to add materials (lecture, tutorial, lab, quiz, reading, etc.) to a specific week so my content is organised chronologically. | P1 | **Done** |
| 3.2 | As a **Creator**, I want to edit material content in a rich-text editor (headings, tables, code blocks) so I can produce professional-looking content. | P1 | **Done** — TipTap editor |
| 3.3 | As a **Creator**, I want to reorder materials within a week via drag-and-drop. | P1 | **Done** |
| 3.4 | As a **Creator**, I want to duplicate a material (same week or different week) so I can reuse structure. | P1 | **Done** |
| 3.5 | As a **Creator**, I want to see a week summary (material count, total duration, types breakdown). | P1 | **Done** |
| 3.6 | As a **Creator**, I want to filter materials by type, status, or search term. | P1 | **Done** |
| 3.7 | As a **Creator**, I want to set material status (draft → review → published) to track my progress. | P1 | **Done** |
| 3.8 | As a **Creator**, I want to create just a single quiz, worksheet, or material without needing a full unit structure — no ULOs required, no forced workflow. | P1 | **Done** — materials are independent of ULO mappings |
| 3.9 | As a **Creator**, I want to link to external videos (YouTube, Vimeo) in my materials rather than uploading video files. | P1 | **Done** — content field supports links |

## 4. Assessments

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 4.1 | As a **Creator**, I want to define assessments with type, weight, due week, and duration. | P1 | **Done** |
| 4.2 | As a **Creator**, I want assessment weights to be validated (must total 100%). | P1 | **Done** |
| 4.3 | As a **Creator**, I want to map assessments to ULOs so I can verify alignment. | P1 | **Done** |
| 4.4 | As a **Creator**, I want to duplicate an assessment to create variations. | P1 | **Done** |
| 4.5 | As a **Creator**, I want to reorder assessments. | P1 | **Done** |
| 4.6 | As a **Creator**, I want to link assessments to specific materials (assessment-material links). | P1 | **Done** |

## 5. AI-Assisted Content Creation

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 5.1 | As a **Creator**, I want to generate content for a material using AI (selecting provider and teaching style) so I get a quality first draft. | P1 | **Done** — streaming SSE |
| 5.2 | As a **Creator**, I want to enhance existing content with AI (improve readability, add examples, restructure). | P1 | **Done** — `/api/llm/enhance` |
| 5.3 | As a **Creator**, I want AI generation to respect my chosen teaching philosophy. | P1 | **Done** — 9 pedagogies supported |
| 5.4 | As a **Creator**, I want to choose between LLM providers (OpenAI, Anthropic, Gemini, local Ollama). | P1 | **Done** — multi-provider service |
| 5.5 | As a **Creator**, I want a guided content workflow (chat-style) that walks me through creating a unit outline step by step. | P1 | **Done** — `content_workflow_service` |
| 5.6 | As a **Creator**, I want AI to generate the full unit structure (topics, outcomes, assessments) from a unit description. | P2 | **Partial** — backend works, needs streamlined UX |
| 5.7 | As a **Creator**, I want to use prompt templates so I can customise how AI generates content. | P1 | **Done** — CRUD for templates |
| 5.8 | As a **Creator**, I want the AI sidebar to be aware of my active unit (its ULOs, topics, materials) so suggestions are contextual, not generic. | P2 | **Planned** — sidebar works but has no unit context |
| 5.9 | As a **Creator**, I want AI-assist available on any text field (generate from blank, improve existing, get recommendations) so I don't have to use the sidebar for everything. | P2 | **Planned** |
| 5.10 | As a **Creator**, I want to partially complete a unit (e.g. some ULOs and a couple of topics) and have AI generate the rest, using what I've provided as context. | P2 | **Planned** — ties to 1.7 "fill the gaps" |

## 6. Content Import & Enhancement

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 6.1 | As an **Enhancer**, I want to upload existing materials (PDF, DOCX, PPTX, MD, HTML) so the system can parse and import them. | P2 | **Partial** — backend services work, UI flow needs polish |
| 6.2 | As an **Enhancer**, I want the system to extract structure from uploaded PDFs (topics, outcomes, assessments). | P2 | **Partial** — `pdf_parser_service` + `document_analyzer_service` work |
| 6.3 | As an **Enhancer**, I want to review and correct auto-detected structure before committing the import. | P2 | **Planned** — no review/confirm UI step |
| 6.4 | As an **Enhancer**, I want AI to enhance imported content while preserving my original intent. | P3 | **Partial** — enhancement API works, import-to-enhance pipeline incomplete |
| 6.5 | As an **Enhancer**, I want batch import of multiple files at once (or ZIP upload). | P2 | **Partial** — ZIP endpoint exists, UI unclear |
| 6.6 | As an **Enhancer**, I want to import a PowerPoint and have it converted to editable content (text extracted, slides become sections). | P3 | **Partial** — text extraction works, images lost |
| 6.7 | As an **Enhancer**, I want imported content to go straight into the normal editing flow so I can refine it immediately. | P2 | **Planned** — import and edit flows not connected |

## 7. Content Validation & Quality

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 7.1 | As a **Curator**, I want automatic readability scoring (Flesch-Kincaid) on generated content. | P3 | **Partial** — plugin architecture done, validators incomplete |
| 7.2 | As a **Curator**, I want structure validation (heading hierarchy, section balance). | P3 | **Partial** — same as above |
| 7.3 | As a **Curator**, I want accessibility checking (WCAG compliance). | P4 | **Planned** |
| 7.4 | As a **Curator**, I want an alignment report showing ULO coverage across materials and assessments. | P1 | **Done** — `analytics_service.get_alignment_report` |
| 7.5 | As a **Curator**, I want a quality score for each unit (graded A–F) based on coverage, weights, workload balance. | P1 | **Done** — `analytics_service.calculate_quality_score` |
| 7.6 | As a **Curator**, I want unit validation that flags errors (missing ULOs, weights != 100%, no materials). | P1 | **Done** — `analytics_service.validate_unit` |
| 7.7 | As a **Curator**, I want recommendations for improving a unit (AI-generated suggestions). | P1 | **Done** — `analytics_service.get_recommendations` |

## 8. Analytics & Reporting

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 8.1 | As a **Creator**, I want a unit overview dashboard (counts of ULOs, materials, assessments, total weight). | P1 | **Done** |
| 8.2 | As a **Creator**, I want to see unit progress (draft vs published, completion percentage). | P1 | **Done** |
| 8.3 | As a **Creator**, I want weekly workload analysis (duration per week, assessment load). | P1 | **Done** |
| 8.4 | As a **Creator**, I want to export unit data as JSON or CSV for external reporting. | P1 | **Done** |
| 8.5 | As a **Creator**, I want unit statistics (Bloom's distribution, type breakdowns). | P1 | **Done** |

## 9. Export & LMS Integration

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 9.1 | As a **Creator**, I want to export my unit as an IMS Common Cartridge (.imscc) file so I can import it into my LMS (Canvas, Blackboard). | P1 | **Done** |
| 9.2 | As a **Creator**, I want to import an .imscc file from my LMS to create a unit in the system. | P3 | **Planned** — spec exists |
| 9.3 | As a **Creator**, I want to export content as standalone HTML (with inline styles) for pasting into an LMS. | P3 | **Planned** |
| 9.4 | As a **Creator**, I want to export my unit as PDF or PPTX via Quarto. | P3 | **Partial** — `quarto_service` backend works, not wired to UI fully |
| 9.5 | As a **Creator**, I want to copy formatted content to clipboard for quick LMS pasting. | P3 | **Planned** |

## 10. Authentication & User Management

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 10.1 | As a **user**, I want to register with email/password. | P1 | **Done** |
| 10.2 | As a **user**, I want to log in and receive a JWT session. | P1 | **Done** |
| 10.3 | As a **user**, I want to verify my email address. | P1 | **Done** |
| 10.4 | As a **user**, I want to reset my password via email. | P1 | **Done** |
| 10.5 | As a **user**, I want to configure my preferred teaching style in settings. | P1 | **Done** |
| 10.6 | As a **user**, I want to configure my own LLM API keys (bring your own key). | P1 | **Done** |
| 10.7 | As a **user**, I want to set up local Ollama as my AI provider (no cloud keys needed). | P1 | **Done** |

## 11. Administration

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 11.1 | As an **Admin**, I want to manage users (view, roles, deactivate). | P1 | **Done** |
| 11.2 | As an **Admin**, I want to configure system-wide LLM provider settings and API keys. | P1 | **Done** |
| 11.3 | As an **Admin**, I want to manage the email whitelist (allowed registration domains). | P1 | **Done** |
| 11.4 | As an **Admin**, I want to view security logs (login attempts, admin actions). | P1 | **Done** |
| 11.5 | As an **Admin**, I want to configure password policy (min length, complexity). | P1 | **Done** |
| 11.6 | As an **Admin**, I want to configure session and lockout settings. | P1 | **Done** |
| 11.7 | As an **Admin**, I want to view system health and monitoring info. | P1 | **Done** |

## 12. Research & Citation

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 12.1 | As a **Creator**, I want to search the web for academic sources to reference in my materials. | P2 | **Partial** — `web_search_service` is a stub (~20%), needs implementation |
| 12.2 | As a **Creator**, I want to save research sources with metadata (authors, year, DOI, URL). | P1 | **Done** |
| 12.3 | As a **Creator**, I want to generate citations in multiple formats (APA7, Harvard, MLA, Chicago, IEEE, Vancouver). | P1 | **Done** |
| 12.4 | As a **Creator**, I want to search for similar courses/units across the internet, see results with titles and descriptions, select the ones I like, and use those as a basis for my unit structure. | P3 | **Planned** |

## 13. Version Control & History

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 13.1 | As a **Creator**, I want to save a version of my material when I'm happy with it ("commit"). | P2 | **Partial** — DB model supports versions, UI has VersionHistory component |
| 13.2 | As a **Creator**, I want to see previous versions of a material and compare changes (diff view). | P2 | **Partial** — diff viewer component exists |
| 13.3 | As a **Creator**, I want to restore a previous version if I don't like my changes. | P2 | **Partial** — restore capability in UI component |
| 13.4 | As a **Creator**, I want simple version control — just save/view/restore, no branches or merging. | P2 | **Partial** — components exist, unclear if end-to-end flow works |

## 14. LRD Workflow (Learning Requirements Document)

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 14.1 | As a **Creator**, I want to create a structured Learning Requirements Document for comprehensive unit planning. | P1 | **Done** |
| 14.2 | As a **Creator**, I want to submit an LRD for approval before generating content. | P1 | **Done** |
| 14.3 | As a **Creator**, I want to generate a prioritised task list from an approved LRD. | P1 | **Done** |
| 14.4 | As a **Creator**, I want to track task completion as I work through LRD-generated tasks. | P1 | **Done** |

## 15. Editor Experience

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 15.1 | As a **Creator**, I want a simple editing mode that hides technical details (YAML, raw markdown) so I can focus on content. | P2 | **Partial** — TipTap rich editor works, but no explicit simple/advanced toggle |
| 15.2 | As a **power user**, I want an advanced editing mode where I can see and edit YAML front matter and raw markdown directly. | P2 | **Partial** — QuartoEditor has YAML editing, no unified toggle |
| 15.3 | As a **Creator**, I want to add images to my materials by providing a URL/link. | P2 | **Planned** — TipTap supports image nodes, needs UI for inserting |
| 15.4 | As a **Creator**, I want to upload images from my computer to include in materials. | P3 | **Planned** — needs media upload endpoint + storage |
| 15.5 | As a **Creator**, I want AI to generate images for my materials (diagrams, illustrations) when the LLM provider supports it. | P4 | **Planned** |
| 15.6 | As a **Creator**, I want to search for free stock images (e.g. Unsplash) and insert them into my materials. | P4 | **Planned** |

## 16. Flexibility & Workflow Freedom

| # | Story | Phase | Status |
|---|-------|-------|--------|
| 16.1 | As a **Creator**, I want to work on my unit in any order — I shouldn't be forced to define ULOs before creating materials, or complete all weeks before exporting. | P1 | **Done** — no enforced sequence |
| 16.2 | As a **Creator**, I want to create a standalone piece of content (a quiz, a worksheet) without setting up a full unit, for quick one-off needs. | P2 | **Planned** — currently materials require a unit_id |
| 16.3 | As a **Creator**, I want quality to improve progressively — the system should work with minimal input but produce better results as I add more detail (ULOs, descriptions, pedagogy). | P2 | **Planned** — ties to "fill the gaps" (1.7) |

---

## Status Summary

| Status | Count |
|--------|-------|
| **Done** | ~55 |
| **Partial** | ~18 |
| **Planned** | ~18 |

| Phase | Description | Stories |
|-------|-------------|---------|
| **P1** | Manual editing, core CRUD, auth, analytics | ~50 (mostly Done) |
| **P2** | AI integration, smart completion, import flow, version control, editor UX | ~20 (mostly Partial/Planned) |
| **P3** | Advanced import/export, web search, image upload, IMSCC import | ~8 (mostly Planned) |
| **P4** | AI image generation, stock photos, accessibility validation | ~3 (all Planned) |

*Last updated: 2026-02-20*
