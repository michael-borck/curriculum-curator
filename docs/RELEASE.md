# Release checklist

Run every gate on the commit you intend to tag. A release is not ready if any
step fails.

## 1. Versions

Keep these identical (the desktop release workflow also rewrites them from the
tag):

- `backend/pyproject.toml` → `[project].version`
- `frontend/package.json` → `version`
- `desktop/package.json` → `version`

## 2. Backend gates

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/basedpyright
.venv/bin/pytest -q
```

## 3. Frontend and desktop gates

```bash
cd frontend
npm ci
npm run lint
npm run type-check
npm run format:check
npm run test -- --run
npm run build

cd ../desktop
npm ci
npm run type-check
npm run build
```

## 4. Dependency audit

```bash
cd backend && uv run --with pip-audit -- pip-audit
cd ../frontend && npm audit --audit-level=high
cd ../desktop && npm audit --audit-level=high
```

## 5. Fresh and upgraded databases

```bash
# Fresh install
rm -f backend/data/curriculum_curator.db
cd backend && .venv/bin/python init_db.py

# Upgrade path: keep a copy of an older DB and start the app once.
# `_ensure_sqlite_schema` must add new columns and rebuild legacy code tables
# without errors. Check registers/unverified users still load.
```

## 6. Docker smoke test

```bash
SECRET_KEY=$(openssl rand -hex 32) docker compose build
SECRET_KEY=... docker compose up -d
curl -fsS http://127.0.0.1:8081/health
curl -fsS http://127.0.0.1:8081/api/auth/config
docker compose down
```

Confirm `/health` is healthy, the login page loads, and registration/login
work against the fresh database.

## 7. Desktop packaging

- Trigger the release workflow from a tag.
- Confirm both macOS architectures are signed, notarized and stapled.
- Confirm the combined `latest-mac.yml` lists both DMGs.
- Windows is intentionally unsigned until Azure Trusted Signing is configured.
- Verify auto-update sees the new version and the opt-out still works.

## 8. Tag and publish

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The desktop workflow creates the draft release, builds, notarizes, merges the
mac manifest and publishes. The Docker workflow runs CI first, then publishes
SBOM/provenance-attached images.

## 9. Post-release

- Download the released DMGs and confirm they open on a clean machine.
- Check `/docs` is disabled in production and the configured `FRONTEND_URL` is
  used in magic-link emails.
- Confirm background cleanup: no orphaned git repos after a deleted account.
- Record the release in the changelog.
