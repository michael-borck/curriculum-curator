# E2E Test Fixtures

Test packages for the package import E2E tests (`13-package-import.spec.ts`).

## Reference Packages (from external sources)

These are real-world packages from industry-standard sources — not hand-crafted by us — so we're testing against the same formats real users will import.

| File | Format | Source | Size | Description |
|------|--------|--------|------|-------------|
| `canvas-sample.imscc` | IMS CC v1.3 | [Instructure public S3](https://s3.amazonaws.com/public-imscc/facc0607309246638c298c6a1b01abcf.imscc) via [common-cartridge-viewer](https://github.com/instructure/common-cartridge-viewer) | 3 MB | Real Canvas-exported course: "Ally: Accessibility Workshop". Contains PDFs, DOCXs, images, and HTML web content. CC BY-SA 4.0 licensed. |
| `golf-scorm12.zip` | SCORM 1.2 | [SCORM.com Golf Examples](https://scorm.com/scorm-explained/technical-scorm/golf-examples/) (RuntimeBasicCalls) | 353 KB | The industry-standard SCORM 1.2 test package by Rustici Software. Multi-page HTML SCO with JavaScript, images, and runtime API calls. |

## Synthetic Packages (generated)

Minimal hand-crafted packages for quick sanity checks. Created by `create-fixtures.sh`.

| File | Format | Size | Description |
|------|--------|------|-------------|
| `sample-course.imscc` | IMS CC v1.1 | 3 KB | 2 weeks, 3 HTML resources + 1 QTI assessment |
| `sample-scorm.zip` | SCORM 1.2 | 2 KB | 2 modules with HTML content |

## Re-downloading reference packages

If the reference packages are lost or need updating:

```bash
# Canvas IMSCC (Instructure public sample)
curl -sL -o canvas-sample.imscc \
  "https://s3.amazonaws.com/public-imscc/facc0607309246638c298c6a1b01abcf.imscc"

# SCORM.com Golf Examples (RuntimeBasicCalls, SCORM 1.2)
curl -sL -o golf-scorm12.zip \
  "https://scorm.com/wp-content/assets/golf_examples/PIFS/RuntimeBasicCalls_SCORM12.zip"
```

## Gitignored files

Large real-world exports (e.g. Blackboard course dumps) are gitignored since they exceed 100MB. These can be used for manual testing via the app UI but not in automated E2E tests.
