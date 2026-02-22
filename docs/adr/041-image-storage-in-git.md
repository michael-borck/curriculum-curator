# 41. Image Storage in Git Content Repositories

Date: 2026-02-22

## Status

Accepted

## Context

Materials need to include images — both uploaded by users via the editor and extracted automatically from imported PPTX files. We already use per-unit Git repositories for content versioning (ADR-013), so images need a storage strategy that works with the existing content pipeline.

The options range from simple (put images next to content in Git) to complex (introduce a separate storage system). The app targets single-instance deployments including a desktop Electron build, so infrastructure complexity is a real cost.

## Decision

Store images as binary blobs inside the same per-unit Git repositories that hold content, using a sibling directory convention: `{material_git_path}.images/{filename}`.

**Two ingestion paths, same storage:**

1. **Editor upload** (`POST /api/materials/units/{unit_id}/materials/{material_id}/images`) — file extension and size validated, filename sanitised (non-alphanumeric → hyphens), hash suffix added on collision. Saved via `git.save_binary()`.

2. **PPTX import** — images extracted by `python-pptx` arrive as `{"filename", "data"}` dicts. Saved to Git, then `{{IMAGE:filename}}` placeholders in the HTML body are replaced with `<img>` tags pointing to the serve endpoint.

**Serving:** Auth-gated GET endpoints read via `git.read_binary()` and return the image with `Cache-Control: public, max-age=86400`. Content-type is guessed from the filename extension.

## Consequences

### Positive
- Images are versioned alongside content — restore a version and its images come back too
- No additional infrastructure (no S3, no separate filesystem, no database BLOBs)
- Works identically in server and Electron desktop deployments
- Auth-gated serving — no risk of public URL leakage

### Negative
- Git is not designed for binary blobs — repositories grow permanently (even after image deletion, objects remain in Git history)
- No CDN or edge caching — every image request hits the backend
- Large units with many images may cause slow `git clone` or backup operations

### Neutral
- Image deduplication is per-material (hash suffix prevents collisions within a material, but the same image in two materials is stored twice)
- No image optimisation or resizing — images are stored and served as-is

## Alternatives Considered

### S3 / Object Storage
- Standard for web apps at scale, with CDN integration
- Rejected: adds infrastructure dependency that breaks the single-binary desktop deployment model and contradicts the privacy-first, local-first philosophy (ADR-037)

### Database BLOBs
- Simple, transactional, no extra service
- Rejected: SQLite has practical size limits for BLOBs; would bloat the database and slow queries

### Filesystem Outside Git
- Store images in a plain directory, reference by path
- Rejected: loses version coupling (restoring content version wouldn't restore its images), adds a second storage path to back up and manage

## Implementation Notes

- Filename sanitisation: `re.sub(r'[^a-zA-Z0-9._-]', '-', name)`, collapse runs, strip leading/trailing hyphens
- Collision handling: append `sha256(data)[:8]` before extension if filename already exists
- PPTX placeholder format: `{{IMAGE:filename}}` replaced after Git save with full API URL
- Allowed extensions and max size configured via `settings.IMAGE_EXTENSIONS` and `settings.MAX_IMAGE_SIZE`

## References

- [ADR-013: Git-Backed Content Storage](013-git-backed-content-storage.md)
- [ADR-037: Privacy-First, BYOK Architecture](037-privacy-first-byok-architecture.md)
- `backend/app/api/routes/materials.py` — upload, serve, list, delete endpoints
- `backend/app/api/routes/content.py` — `_save_extracted_images()` for PPTX flow
