# E2E Tests (Playwright)

End-to-end tests for Curriculum Curator using Playwright.

## Quick Start

### 1. Install dependencies

```bash
cd e2e
npm install
npx playwright install chromium
```

### 2. Run tests

#### Against the VPS (production/staging)

```bash
cd e2e
BASE_URL=https://curriculumcurator.serveur.au npm test
```

**Important:** Tests 01 (registration) require either a clean database or pre-existing test accounts. For the VPS, you may want to start from test 02 with existing accounts:

```bash
BASE_URL=https://curriculumcurator.serveur.au npx playwright test --grep-invert "register"
```

#### Against local dev

```bash
# Terminal 1: Start backend with test env
cp e2e/.env.test backend/.env
cd e2e && node scripts/setup-test-db.js && cd ..
./backend.sh

# Terminal 2: Start frontend
./frontend.sh

# Terminal 3: Run tests
cd e2e
npm test              # Run all tests (headless)
npm run test:headed   # Run with browser visible
npm run test:ui       # Interactive UI mode
npm run test:debug    # Step-through debugger
npm run report        # View HTML report from last run
```

### Test environment (.env.test)

For local testing, the `.env.test` provides:
- Separate database: `data/test_e2e.db`
- Dev email provider (prints verification codes to console + stores in DB)
- Rate limiting disabled
- No LLM API keys needed (AI tests are optional)

## Test Structure

Tests are numbered and run **sequentially** — later tests depend on data created by earlier ones.

| File | Tier | Description | Dependencies |
|------|------|-------------|-------------|
| `00-health-check` | 0 | Backend + frontend responding | None |
| `01-registration-login` | 1 | Admin + regular user auth | Clean DB |
| `02-create-unit` | 2 | Unit CRUD | Logged-in user |
| `03-unit-settings` | 2 | Settings, toggles, sector | Unit exists |
| `04-learning-outcomes` | 3 | ULOs, Bloom's levels | Unit exists |
| `05-weekly-schedule` | 3 | Topics, presets | Unit exists |
| `06-materials-editor` | 3 | Materials, TipTap editor | Unit + topics |
| `07-assessments-rubrics` | 3 | Assessments, rubrics, mapping | Unit + ULOs |
| `08-file-import` | 4 | Import page navigation | Logged-in user |
| `09-outline-import` | 4 | Outline parser upload flow | Logged-in user |
| `10-export` | 4 | Export formats | Populated unit |
| `11-quality-analytics` | 5 | Quality + analytics dashboards | Populated unit |
| `12-user-settings` | 5 | Preferences, templates | Logged-in user |

| `13-package-import` | 4 | IMSCC/SCORM import | Logged-in user |
| `14-ai-scaffold` | 6 | Quick scaffold, review, accept | API key required |
| `15-ai-content` | 6 | AI sidebar, generate, enhance | API key required |
| `16-research` | 7 | Academic search, saved sources | API key optional |
| `17-version-history` | 7 | Material detail, history tab | Unit with content |
| `18-alignment` | 7 | Custom frameworks, mapping | Unit + ULOs |

## Auth Strategy

- **First user** registered on a clean DB is auto-verified as admin (no email needed)
- **Subsequent users** require a 6-digit verification code — the test reads it directly from the SQLite database via `helpers/db.ts` (the backend also prints it to console in dev mode)
- **VPS testing**: Use pre-existing test accounts, or reset the DB via Docker and register fresh
- No backend code changes needed for testing

## Running Specific Tests

```bash
# Run a single test file
npx playwright test tests/02-create-unit.spec.ts

# Run tests matching a pattern
npx playwright test --grep "create unit"

# Skip registration tests (if DB already has users)
npx playwright test --grep-invert "register"

# Run with visible browser
npx playwright test --headed

# Run with trace viewer for debugging
npx playwright test --trace on
```

## Resetting (Local)

```bash
cd e2e && node scripts/setup-test-db.js
# Then restart backend.sh
```

## Resetting (VPS/Docker)

```bash
# SSH into VPS, then:
docker exec <container> rm /app/data/curriculum_curator.db
docker restart <container>
```
