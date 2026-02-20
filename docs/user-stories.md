# User Stories — Curriculum Curator

> Living document tracking what the system does and should do.
> Status: **Done** | **Partial** | **Planned** | **Cut**

## Personas

| Alias | Role | Primary Goal |
|-------|------|-------------|
| **Creator** | Lecturer building a new unit from scratch | Generate complete, aligned materials fast |
| **Enhancer** | Educator with existing materials to modernise | Improve legacy content without starting over |
| **Curator** | Department head / quality assurer | Ensure consistency and standards across units |
| **Admin** | System administrator | Manage users, providers, and platform config |

---

## 1. Unit Setup & Structure

| # | Story | Status |
|---|-------|--------|
| 1.1 | As a **Creator**, I want to create a new unit with metadata (title, code, credits, semester, weeks) so I have a container for all my materials. | **Done** |
| 1.2 | As a **Creator**, I want to define weekly topics for my unit so content is organised by teaching week. | **Done** |
| 1.3 | As a **Creator**, I want to set a teaching philosophy (from 9 options) for my unit so AI-generated content matches my pedagogical approach. | **Done** |
| 1.4 | As a **Creator**, I want to import a unit outline (PDF/document) so the system can pre-populate structure from my existing syllabus. | **Partial** — upload works, full PDF parsing not complete |
| 1.5 | As a **Creator**, I want to duplicate an existing unit as a starting point for a new semester. | **Planned** |

## 2. Learning Outcomes

| # | Story | Status |
|---|-------|--------|
| 2.1 | As a **Creator**, I want to define Unit Learning Outcomes (ULOs) with Bloom's taxonomy levels so I can track what students should achieve. | **Done** |
| 2.2 | As a **Creator**, I want to bulk-create ULOs (e.g. paste a list) so I don't have to enter them one by one. | **Done** |
| 2.3 | As a **Creator**, I want to reorder ULOs by drag-and-drop so they reflect my preferred sequence. | **Done** |
| 2.4 | As a **Creator**, I want to map ULOs to materials and assessments so I can verify constructive alignment. | **Done** |
| 2.5 | As a **Creator**, I want to see a coverage report showing which ULOs are covered by materials and assessments (and which have gaps). | **Done** |
| 2.6 | As a **Curator**, I want to map ULOs to accreditation graduate attributes so I can demonstrate standards compliance. | **Done** — model + routes exist |
| 2.7 | As a **Creator**, I want to define Local Learning Outcomes (LLOs) per material for granular weekly objectives. | **Done** |

## 3. Weekly Materials

| # | Story | Status |
|---|-------|--------|
| 3.1 | As a **Creator**, I want to add materials (lecture, tutorial, lab, quiz, reading, etc.) to a specific week so my content is organised chronologically. | **Done** |
| 3.2 | As a **Creator**, I want to edit material content in a rich-text editor (headings, tables, code blocks) so I can produce professional-looking content. | **Done** — TipTap editor |
| 3.3 | As a **Creator**, I want to reorder materials within a week via drag-and-drop. | **Done** |
| 3.4 | As a **Creator**, I want to duplicate a material (same week or different week) so I can reuse structure. | **Done** |
| 3.5 | As a **Creator**, I want to see a week summary (material count, total duration, types breakdown). | **Done** |
| 3.6 | As a **Creator**, I want to filter materials by type, status, or search term. | **Done** |
| 3.7 | As a **Creator**, I want to set material status (draft → review → published) to track my progress. | **Done** |

## 4. Assessments

| # | Story | Status |
|---|-------|--------|
| 4.1 | As a **Creator**, I want to define assessments with type, weight, due week, and duration. | **Done** |
| 4.2 | As a **Creator**, I want assessment weights to be validated (must total 100%). | **Done** |
| 4.3 | As a **Creator**, I want to map assessments to ULOs so I can verify alignment. | **Done** |
| 4.4 | As a **Creator**, I want to duplicate an assessment to create variations. | **Done** |
| 4.5 | As a **Creator**, I want to reorder assessments. | **Done** |
| 4.6 | As a **Creator**, I want to link assessments to specific materials (assessment-material links). | **Done** |

## 5. AI-Assisted Content Creation

| # | Story | Status |
|---|-------|--------|
| 5.1 | As a **Creator**, I want to generate content for a material using AI (selecting provider and teaching style) so I get a quality first draft. | **Done** — streaming SSE |
| 5.2 | As a **Creator**, I want to enhance existing content with AI (improve readability, add examples, restructure). | **Done** — `/api/llm/enhance` |
| 5.3 | As a **Creator**, I want AI generation to respect my chosen teaching philosophy. | **Done** — 9 pedagogies supported |
| 5.4 | As a **Creator**, I want to choose between LLM providers (OpenAI, Anthropic, Gemini, local Ollama). | **Done** — multi-provider service |
| 5.5 | As a **Creator**, I want a guided content workflow (chat-style) that walks me through creating a unit outline step by step. | **Done** — `content_workflow_service` |
| 5.6 | As a **Creator**, I want AI to generate the full unit structure (topics, outcomes, assessments) from a unit description. | **Done** — `workflow_structure_creator` |
| 5.7 | As a **Creator**, I want to use prompt templates so I can customise how AI generates content. | **Done** — CRUD for templates |

## 6. Content Import & Enhancement

| # | Story | Status |
|---|-------|--------|
| 6.1 | As an **Enhancer**, I want to upload existing materials (PDF, DOCX, PPTX, MD, HTML) so the system can parse and import them. | **Partial** — upload endpoint exists, full parsing incomplete |
| 6.2 | As an **Enhancer**, I want the system to extract structure from uploaded PDFs (topics, outcomes, assessments). | **Partial** — `pdf_parser_service` + `document_analyzer_service` exist |
| 6.3 | As an **Enhancer**, I want to review and correct auto-detected structure before committing the import. | **Planned** |
| 6.4 | As an **Enhancer**, I want AI to enhance imported content while preserving my original intent. | **Partial** — enhancement API works, import-to-enhance pipeline incomplete |
| 6.5 | As an **Enhancer**, I want batch import of multiple files at once. | **Planned** |

## 7. Content Validation & Quality

| # | Story | Status |
|---|-------|--------|
| 7.1 | As a **Curator**, I want automatic readability scoring (Flesch-Kincaid) on generated content. | **Partial** — plugin architecture done, validator implementations incomplete |
| 7.2 | As a **Curator**, I want structure validation (heading hierarchy, section balance). | **Partial** — same as above |
| 7.3 | As a **Curator**, I want accessibility checking (WCAG compliance). | **Planned** |
| 7.4 | As a **Curator**, I want an alignment report showing ULO coverage across materials and assessments. | **Done** — `analytics_service.get_alignment_report` |
| 7.5 | As a **Curator**, I want a quality score for each unit (graded A–F) based on coverage, weights, workload balance. | **Done** — `analytics_service.calculate_quality_score` |
| 7.6 | As a **Curator**, I want unit validation that flags errors (missing ULOs, weights != 100%, no materials). | **Done** — `analytics_service.validate_unit` |
| 7.7 | As a **Curator**, I want recommendations for improving a unit (AI-generated suggestions). | **Done** — `analytics_service.get_recommendations` |

## 8. Analytics & Reporting

| # | Story | Status |
|---|-------|--------|
| 8.1 | As a **Creator**, I want a unit overview dashboard (counts of ULOs, materials, assessments, total weight). | **Done** |
| 8.2 | As a **Creator**, I want to see unit progress (draft vs published, completion percentage). | **Done** |
| 8.3 | As a **Creator**, I want weekly workload analysis (duration per week, assessment load). | **Done** |
| 8.4 | As a **Creator**, I want to export unit data as JSON or CSV for external reporting. | **Done** |
| 8.5 | As a **Creator**, I want unit statistics (Bloom's distribution, type breakdowns). | **Done** |

## 9. Export & LMS Integration

| # | Story | Status |
|---|-------|--------|
| 9.1 | As a **Creator**, I want to export my unit as an IMS Common Cartridge (.imscc) file so I can import it into my LMS (Canvas, Blackboard). | **Done** — spec + service + route |
| 9.2 | As a **Creator**, I want to import an .imscc file from my LMS to create a unit in the system. | **Planned** — spec exists |
| 9.3 | As a **Creator**, I want to export content as standalone HTML (with inline styles) for pasting into an LMS. | **Planned** |
| 9.4 | As a **Creator**, I want to export my unit as PDF or PPTX via Quarto. | **Planned** — `quarto_service` exists but not wired up |
| 9.5 | As a **Creator**, I want to copy formatted content to clipboard for quick LMS pasting. | **Planned** |

## 10. Authentication & User Management

| # | Story | Status |
|---|-------|--------|
| 10.1 | As a **user**, I want to register with email/password. | **Done** |
| 10.2 | As a **user**, I want to log in and receive a JWT session. | **Done** |
| 10.3 | As a **user**, I want to verify my email address. | **Done** |
| 10.4 | As a **user**, I want to reset my password via email. | **Done** |
| 10.5 | As a **user**, I want to configure my preferred teaching style in settings. | **Done** |
| 10.6 | As a **user**, I want to configure my own LLM API keys (bring your own key). | **Done** — settings UI + backend |
| 10.7 | As a **user**, I want to set up local Ollama as my AI provider (no cloud keys needed). | **Done** — Docker sidecar + setup UI |

## 11. Administration

| # | Story | Status |
|---|-------|--------|
| 11.1 | As an **Admin**, I want to manage users (view, roles, deactivate). | **Done** — routes + UI |
| 11.2 | As an **Admin**, I want to configure system-wide LLM provider settings and API keys. | **Done** — `admin_config` routes |
| 11.3 | As an **Admin**, I want to manage the email whitelist (allowed registration domains). | **Done** — model + routes + UI |
| 11.4 | As an **Admin**, I want to view security logs (login attempts, admin actions). | **Done** — `security_logger` + monitoring routes |
| 11.5 | As an **Admin**, I want to configure password policy (min length, complexity). | **Done** — `config_service` |
| 11.6 | As an **Admin**, I want to configure session and lockout settings. | **Done** — `config_service` |
| 11.7 | As an **Admin**, I want to view system health and monitoring info. | **Done** — monitoring routes |

## 12. Research & Citation

| # | Story | Status |
|---|-------|--------|
| 12.1 | As a **Creator**, I want to search the web for academic sources to reference in my materials. | **Done** — `web_search_service` |
| 12.2 | As a **Creator**, I want to save research sources with metadata (authors, year, DOI, URL). | **Done** — `research_source` model |
| 12.3 | As a **Creator**, I want to generate citations in multiple formats (APA7, Harvard, MLA, Chicago, IEEE, Vancouver). | **Done** — `citation_service` |

## 13. Version Control & History

| # | Story | Status |
|---|-------|--------|
| 13.1 | As a **Creator**, I want to see the version history of my materials. | **Partial** — model exists, `VersionHistory.tsx` component exists |
| 13.2 | As a **Creator**, I want to rollback to a previous version. | **Partial** — model supports it, UI uncertain |
| 13.3 | As a **Creator**, I want git-backed content storage for reliable versioning. | **Partial** — `git_content_service` exists |

## 14. LRD Workflow (Learning Requirements Document)

| # | Story | Status |
|---|-------|--------|
| 14.1 | As a **Creator**, I want to create a structured Learning Requirements Document for comprehensive unit planning. | **Done** — model + API + UI |
| 14.2 | As a **Creator**, I want to submit an LRD for approval before generating content. | **Done** — approval workflow |
| 14.3 | As a **Creator**, I want to generate a prioritised task list from an approved LRD. | **Done** — `task_list` model + service |
| 14.4 | As a **Creator**, I want to track task completion as I work through LRD-generated tasks. | **Done** — `TaskBoard.tsx` |

---

## Status Summary

| Status | Count |
|--------|-------|
| **Done** | ~55 |
| **Partial** | ~10 |
| **Planned** | ~10 |

*Last updated: 2026-02-20*
