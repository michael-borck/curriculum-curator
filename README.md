# Curriculum Curator

> **You choose how to install it. You choose how to teach with it.**
> Deploy on your institution's server or run it on your laptop. Pick your AI provider or go fully offline. Select from 9 teaching philosophies, then build curriculum your way.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Node](https://img.shields.io/badge/node-20%2B-green)
![License](https://img.shields.io/badge/license-MIT-green.svg)

[![DeepWiki](https://img.shields.io/badge/DeepWiki-Interactive%20Docs-blue)](https://deepwiki.com/michael-borck/curriculum-curator)

## Overview

Curriculum Curator is a **content creation tool, not a presentation tool**. It helps educators design, structure, and refine unit materials — then export them to the LMS or format of their choice. Think of it as the workshop where you build your curriculum, not the classroom where you deliver it.

The same philosophy runs through every layer: **you choose**.

- **How to host**: institution VPS, personal Docker, or desktop app
- **Which AI**: OpenAI, Anthropic, Gemini, local Ollama, or none at all
- **How to teach**: 9 pedagogical styles shape every piece of generated content
- **What to export**: IMS Common Cartridge, SCORM, PDF, DOCX, PPTX, HTML
- **How much AI help**: full generation, refine-only, or write everything yourself

### Two Ways to Run

| | Institutional Server | Personal / Desktop |
|---|---|---|
| **Who it's for** | A teaching team or department | An individual educator |
| **Deployment** | Docker on your institution's VPS | Desktop app (Mac, Windows, Linux) or Docker locally |
| **Accounts** | Registration, email verification, email whitelist, forgotten-password flow | No login needed (`LOCAL_MODE=true`) |
| **Security** | JWT auth, rate limiting, account lockout, role-based access | Single-user, no auth overhead |
| **AI keys** | Shared keys set by admin, or each user brings their own | Your own keys, or fully offline with Ollama |
| **Database** | SQLite on the server — one file, no external DB service | SQLite on your machine |

Both modes ship in the same codebase. Flip `LOCAL_MODE=true` for personal use, or leave it off for multi-user institutional hosting.

### Privacy-First, Bring Your Own Key

No matter how you deploy, Curriculum Curator never phones home:

- **BYOK**: Bring your own API keys for OpenAI, Anthropic, Google Gemini — or run fully offline with local Ollama models
- **No telemetry**: Zero analytics, zero tracking, zero external calls beyond the AI provider you choose
- **Data stays with you**: SQLite in a single file you control — no cloud database, no vendor lock-in
- **Air-gapped capable**: Ollama + Local Mode means the app works without any internet connection

**Note**: This application uses Australian university terminology where a **Unit** is an individual subject (e.g., "Programming 101") and a **Course** is a degree program.

## Key Features

### Content Creation & Structuring
- **9 Teaching Philosophies**: Traditional, Inquiry-Based, Project-Based, Collaborative, Game-Based, Flipped, Differentiated, Constructivist, Experiential
- **AI-Powered Content**: Generation, enhancement, and scaffolding using multiple LLM providers (OpenAI, Anthropic, Google Gemini, Ollama for local/private AI)
- **AI Assistance Levels**: Educators choose their level of AI involvement — none, refine only, or full creation
- **Multi-Scale Workflows**: Create 12-week unit structures, weekly modules, or individual materials
- **Rich Text Editing**: TipTap-based editor with tables, code blocks, and formatting
- **Unit Scaffolding**: AI-generated unit structures (ULOs, assessments, weekly topics) from a description

### Research & Discovery
- **Tiered Academic Search**: Search OpenAlex and Semantic Scholar (always free, no key needed), or add Google CSE / Brave / Tavily / SearXNG for broader results
- **URL Import**: Paste URLs from papers, syllabi, or blogs — the app extracts content, classifies type, and summarises key points
- **AI Outline Synthesis**: Generate a full unit scaffold from research sources, compare sources against an existing unit, or auto-match readings to weekly topics
- **Propose/Apply Pattern**: AI suggests, you review and correct, then commit — nothing changes without your approval

### Accreditation & Mapping
- **Unit Learning Outcomes (ULOs)**: Bloom's taxonomy-aligned outcomes with visual mapping
- **Graduate Capabilities**: Curtin GC1-GC6 mapping to ULOs
- **Assurance of Learning (AoL)**: AACSB competency mapping
- **UN SDG Mapping**: Sustainable Development Goals alignment
- **Learning Outcome Map**: Visual hierarchy from ULOs through weekly materials and assessments

### Export & Interoperability
Once your content is ready, export it to wherever you deliver:
- **IMS Common Cartridge v1.1** (.imscc) — works with Moodle, Canvas, Blackboard
- **SCORM 1.2** (.zip) — universal LMS compatibility
- **Document Export**: PDF (via Pandoc + Typst), DOCX, PPTX, HTML
- **Round-trip Metadata**: Exports include `curriculum_curator_meta.json` preserving pedagogy, outcomes, and accreditation data for future re-import

### Unit Management
- **Soft Delete / Archive**: Remove units from dashboard with full restore capability
- **Git-backed Content**: Per-unit version history via Git repositories
- **Analytics Dashboard**: Bloom's coverage, assessment distribution, weekly workload visualisation
- **Quality Dashboard**: 6-dimension quality scoring with star ratings, per-week breakdown, and AI-powered improvement suggestions

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, LiteLLM |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Editor | TipTap (rich text with tables, code blocks) |
| Database | SQLite (development and production) |
| Auth | JWT (multi-user) or LOCAL_MODE (no login) |
| AI | OpenAI, Anthropic, Google Gemini, Ollama |
| Export | Pandoc + Typst (documents), stdlib (IMSCC/SCORM) |
| Tooling | uv, ruff, basedpyright, pytest, ESLint, Vitest |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Git
- Optional: [Pandoc](https://pandoc.org/) + [Typst](https://typst.app/) for PDF/DOCX/PPTX export

### Installation

```bash
# Clone the repository
git clone https://github.com/michael-borck/curriculum-curator.git
cd curriculum-curator

# Start backend (handles venv, deps, and server)
./backend.sh

# In a new terminal, start frontend
./frontend.sh
```

Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Deployment

Single-container build — frontend is compiled and served by the backend:

```bash
./setup.sh                    # Create data directories and configure
docker compose up --build -d  # Build and run
```

The Docker image includes Node.js (frontend build), Pandoc, and Typst — all export formats work out of the box.

For production deployment, see [docs/guides/docker-vps-deployment.md](docs/guides/docker-vps-deployment.md).

### Local AI with Ollama

Run with a local Ollama sidecar for fully private AI (no API keys needed):

```bash
LOCAL_MODE=true docker compose --profile local-ai up --build -d
```

## Project Structure

```
curriculum-curator/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Config, security, database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic (LLM, export, analytics)
│   └── tests/               # pytest test suites
├── frontend/                # React frontend
│   └── src/
│       ├── components/      # Reusable UI components
│       ├── features/        # Feature modules (auth, units, ai)
│       ├── pages/           # Route-level page components
│       ├── services/        # API integration
│       ├── stores/          # Zustand state management
│       └── hooks/           # Custom React hooks
├── docs/                    # Documentation and ADRs
│   └── adr/                 # Architecture Decision Records (34 ADRs)
├── Dockerfile               # Single-container build
└── docker-compose.yml       # Production deployment
```

## Development

### Code Quality

```bash
# Backend (run from backend/)
cd backend
.venv/bin/ruff check .       # Linting (must be 0 errors)
.venv/bin/ruff format .      # Formatting
.venv/bin/basedpyright       # Type checking (must be 0 errors)
.venv/bin/pytest             # Tests

# Frontend (run from frontend/)
cd frontend
npm run lint                 # ESLint (must be 0 errors)
npm run format               # Prettier
npm run type-check           # TypeScript (must be 0 errors)
npm test                     # Vitest
```

### Export Formats

| Format | Standard Version | LMS Compatibility | Dependencies |
|--------|-----------------|-------------------|--------------|
| IMSCC | v1.1 | Moodle, Canvas, Blackboard | Python stdlib only |
| SCORM | 1.2 | All SCORM-compliant LMS | Python stdlib only |
| PDF | - | - | Pandoc + Typst |
| DOCX | - | - | Pandoc |
| PPTX | - | - | Pandoc |
| HTML | - | - | Pandoc |

## Configuration

Create `.env` in the backend directory:

```env
# Security
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./curriculum_curator.db

# LLM API Keys (all optional — configure in-app or use Ollama)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Local Mode (no login, privacy-first)
LOCAL_MODE=true
```

## Documentation

- [DeepWiki - Interactive Knowledge Base](https://deepwiki.com/michael-borck/curriculum-curator)
- [Getting Started](docs/guides/getting-started.md)
- [Docker VPS Deployment](docs/guides/docker-vps-deployment.md)
- [Teaching Styles Guide](docs/guides/teaching-styles.md)
- [Architecture Decision Records](docs/adr/index.md)

## License

MIT License - see [LICENSE](LICENSE)
