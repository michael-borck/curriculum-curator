# ADR-056: PPTX Template Extraction on Import

Date: 2026-02-24

## Status

Accepted

## Context

Users who already have branded PowerPoint decks (with custom themes, colours, fonts, slide masters, and layouts) want to reuse that branding for all future PPTX exports from the app. The export template system already exists (ADR not numbered; implemented in `export_templates.py`): templates are stored at `backend/user_templates/{user_id}/{template_id}.pptx`, metadata lives in `teaching_preferences.export_templates`, and Pandoc's `--reference-doc` flag applies them automatically.

Currently, the only way to add an export template is via Settings > Export, which requires the user to prepare and upload a separate reference document. This is friction — the user already has a branded PPTX in hand during import. They shouldn't need to go to a different screen and strip it manually.

### Constraints

- **Pandoc ignores animations**: Pandoc's PPTX writer doesn't support animations or transitions, so stripping content slides (which removes all animations) has no practical downside.
- **python-pptx has no native slide deletion**: The library doesn't expose a `delete_slide()` method. Removing slides requires XML manipulation of the `sldIdLst` element and dropping the corresponding part relationships.
- **Slide masters and layouts are preserved automatically**: python-pptx stores masters in `prs.slide_masters` (not `prs.slides`), so deleting all slides leaves the theme intact.

## Decision

When a user imports a PPTX file, the Import Materials UI offers an opt-in checkbox: **"Save PPTX theme as export template"**. When enabled, after the normal import completes, the frontend sends the same file to a new endpoint that:

1. Opens the PPTX with python-pptx
2. Iterates through `prs.slides._sldIdLst` in reverse and removes each slide ID element, dropping the corresponding part relationship via `prs.part.drop_rel()`
3. Saves the stripped PPTX (masters, layouts, theme, dimensions intact; all content slides removed)
4. Stores the result as an export template using the shared `template_storage` module
5. Auto-sets it as the default PPTX template if none exists

### New endpoint

```
POST /content/import/pptx/extract-template
```

Accepts the same `UploadFile` as import, requires authentication. Returns `TemplateInfo` (id, filename, format, uploaded_at, is_default).

### Shared template helpers

The helpers `user_templates_dir`, `get_export_templates`, and `save_export_templates` were extracted from `export_templates.py` into `services/template_storage.py` so both the Settings upload and the import extraction can reuse them without circular imports.

### Frontend behaviour

- Checkbox only appears when at least one `.pptx` file is in the upload queue
- Extraction runs sequentially after the normal import completes (doesn't block import)
- Only the first PPTX in a batch is used for template extraction
- Success shows a green checkmark; failure is logged but doesn't fail the import

## Consequences

### Positive

- Zero-friction template setup: users get branded exports just by importing their existing deck
- Reuses the existing export template infrastructure — no new storage, metadata, or Pandoc changes
- Extracted templates are smaller than the originals (no content slides = smaller file size)

### Negative

- python-pptx's slide deletion uses internal XML APIs (`_sldIdLst`, `drop_rel`) that could break in future library versions
- Users might not understand what "theme" means — the checkbox description explains it but some may still be confused

### Neutral

- The extracted template filename is `{original name} (extracted theme)` to distinguish it from manually uploaded templates
- Animations are inherently lost (content slides removed), which is fine since Pandoc doesn't support them anyway

## Alternatives Considered

### Require users to upload templates separately via Settings

- This is the existing flow and remains available
- Rejected as the *only* path because it adds friction for the most common case (user already has a branded deck)

### Automatically extract template from every PPTX import

- Rejected because not every PPTX import is a branded deck — some are plain content with no custom theme worth saving
- Opt-in checkbox respects user intent

### Use Pandoc to strip slides

- Pandoc can convert PPTX to PPTX with `--reference-doc`, but there's no clean way to produce an *empty* reference doc from an input deck
- python-pptx gives direct control over what's preserved

## Implementation Notes

- `strip_pptx_to_template()` lives in `FileImportService` (not `template_storage`) because it's a file-processing concern, not a storage concern
- The lxml `etree.QName` is used to correctly resolve the `r:id` attribute namespace when removing slide relationships
- Template size limit is the same as for manual uploads (`TEMPLATE_MAX_SIZE`, currently 5 MB)

## References

- `backend/app/services/file_import_service.py` — `strip_pptx_to_template()` method
- `backend/app/api/routes/import_content.py` — `extract_template_from_pptx` endpoint
- `backend/app/services/template_storage.py` — shared helpers
- `frontend/src/features/import/ImportMaterials.tsx` — checkbox UI
