# ADR 0033: Pandoc + Typst as Export Engine (replacing Quarto)

## Status

Accepted — supersedes ADR-0015's Quarto dependency

## Date

2026-02-21

## Context

ADR-0015 chose Quarto as the universal export engine for converting Markdown content to HTML, PDF, DOCX, and PPTX. Quarto is built on Pandoc and adds Jupyter notebook execution, cross-references, and academic publishing features.

In practice, three problems have emerged:

1. **Bundling difficulty.** Quarto is a ~500 MB install that bundles its own Pandoc, Deno runtime, and LaTeX toolchain. PyInstaller cannot bundle it; Electron `extraResources` would balloon the app to over 700 MB. Users installing it locally face a multi-step process unfamiliar to most lecturers.

2. **Unused features.** Curriculum Curator does not use Quarto's notebook execution, cross-references, or academic publishing features. We use it as a Markdown → {format} converter — which is exactly what Pandoc alone does.

3. **PDF via LaTeX.** Quarto's PDF path requires a LaTeX distribution (TeX Live / TinyTeX, ~400 MB+). This is the largest single dependency and the most fragile part of the export pipeline.

Meanwhile, **Typst** has matured as a modern typesetting system that produces high-quality PDF from its own markup. It is a single static binary (~30 MB), requires no LaTeX, and renders fast. Pandoc has native Typst output support (`--to typst`), making the pipeline: Markdown → Pandoc → Typst markup → Typst → PDF.

### Target users

90%+ of our users are non-technical lecturers who want to export curriculum content to common formats. They should not need to install Quarto, LaTeX, or any external tool. The desktop app (Electron) must bundle everything.

### What we lose

- **Jupyter notebook execution** — our content is authored in a WYSIWYG editor, not notebooks. Not needed.
- **Quarto cross-references** — we use our own learning outcome cross-referencing system.
- **Quarto-specific themes** — replaced by Typst templates (PDF) and CSS (HTML).
- **RevealJS slides** — can revisit later if needed; current users export to PPTX.

## Decision

Replace Quarto with **Pandoc + Typst** as the document export engine.

### Export pipeline

```
Markdown (canonical internal format, per ADR-0015)
    │
    ├──► Pandoc ──► HTML      (LMS paste, web embedding)
    ├──► Pandoc ──► DOCX      (offline editing in Word)
    ├──► Pandoc ──► PPTX      (lecture slides for PowerPoint)
    └──► Pandoc ──► Typst ──► PDF  (printed handouts, worksheets)
```

### Binary sizes (bundled in Electron)

| Binary | Size | Notes |
|--------|------|-------|
| Pandoc | ~150 MB | Single static binary, no dependencies |
| Typst | ~30 MB | Single static binary, no dependencies |
| **Total** | **~180 MB** | vs ~500 MB+ for Quarto + TinyTeX |

### Architecture

A new `ExportService` class replaces `QuartoService`:

- **Input:** Markdown content + export settings (format, title, author, theme)
- **Process:** Writes Markdown to temp file, invokes Pandoc (or Pandoc → Typst for PDF)
- **Output:** `BytesIO` buffer with the rendered file
- **Binary resolution:** Checks `PANDOC_PATH` / `TYPST_PATH` env vars, then `process.resourcesPath` (Electron), then system PATH

The service operates at two levels:
1. **Content-level export** — single content item (worksheet, handout, quiz)
2. **Unit-level export** — full unit with outline, weekly materials, assessments compiled into a single document

### Preset system

The existing Quarto preset system (per-content YAML settings stored in `ContentQuartoSettings`) is replaced with a simpler export settings model that stores format preferences without Quarto-specific YAML.

### Docker deployment

Docker images bundle Pandoc and Typst directly:

```dockerfile
# Pandoc
COPY --from=pandoc/core:latest /usr/local/bin/pandoc /usr/local/bin/pandoc

# Typst
ADD https://github.com/typst/typst/releases/download/v0.12.0/typst-x86_64-unknown-linux-musl.tar.xz /tmp/
RUN tar -xf /tmp/typst-*.tar.xz -C /usr/local/bin/ --strip-components=1
```

### Electron desktop

Both binaries are included via `extraResources` in `electron-builder.yml`, alongside the PyInstaller backend binary (per ADR-0024):

```yaml
extraResources:
  - from: "vendor/pandoc/${os}/"
    to: "pandoc"
  - from: "vendor/typst/${os}/"
    to: "typst"
```

The backend resolves binary paths from environment variables set by the Electron main process.

## Consequences

### Positive

- **~60% smaller bundle** — 180 MB vs 500 MB+ (Quarto + TinyTeX)
- **Zero external dependencies** — both are single static binaries; no LaTeX, no Deno, no runtime downloads
- **Simpler error surface** — fewer moving parts means fewer failure modes
- **Fast PDF rendering** — Typst compiles to PDF in milliseconds, vs seconds for LaTeX
- **Bundleable everywhere** — works in Docker, Electron (extraResources), and system installs
- **Pandoc is battle-tested** — 15+ years of development, handles edge cases in DOCX/PPTX generation

### Negative

- **No notebook execution** — if we ever need executable code cells, we'd need to add Jupyter separately
- **Typst template ecosystem is young** — fewer ready-made templates than LaTeX; we'll need to create our own PDF templates
- **Two binaries instead of one** — slightly more complex binary management (Pandoc + Typst vs just Quarto)

### Neutral

- **ADR-0015 remains valid** — Markdown as canonical format, dual-mode editing, and the export format table are unchanged. Only the export engine changes.
- **Existing Quarto preset/settings models** — will be migrated or deprecated as part of the export service rewrite

## Alternatives Considered

### Keep Quarto

- **Rejected because:** Too large to bundle, requires LaTeX for PDF, installation friction for non-technical users

### Pandoc only (WeasyPrint for PDF)

- **Rejected because:** WeasyPrint requires Python C dependencies (cairo, pango) that are problematic with PyInstaller. Typst is a single binary with no dependencies.

### Pandoc only (wkhtmltopdf for PDF)

- **Rejected because:** wkhtmltopdf is unmaintained (last release 2020), has security concerns, and produces lower-quality PDF than Typst

### python-docx + python-pptx + WeasyPrint (no Pandoc)

- **Rejected because:** Multiple code paths per format, less consistent output, more maintenance burden. Pandoc unifies all conversions behind a single tool.

### Docker-only Quarto for technical users

- **Considered and deferred.** If demand emerges for notebook execution or advanced Quarto features, we can offer a separate Docker image with Quarto pre-installed. The Pandoc + Typst version covers 95%+ of use cases.

## References

- [ADR-0015: Content Format and Export Strategy](0015-content-format-and-export-strategy.md)
- [ADR-0024: LOCAL_MODE and PyInstaller Compatibility](0024-local-mode-pyinstaller-compatibility.md)
- [Pandoc User's Guide](https://pandoc.org/MANUAL.html)
- [Typst Documentation](https://typst.app/docs/)
- [Pandoc Typst output](https://pandoc.org/MANUAL.html#typst)
