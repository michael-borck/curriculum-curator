# 48. TipTap Custom Node Extensions

Date: 2026-02-23

## Status

Accepted

## Context

The rich text editor needs to support content types beyond standard prose: live-rendered diagrams (Mermaid), embedded videos (YouTube, MP4/WebM), and potentially other rich media. TipTap's extension system allows custom nodes, but each extension requires decisions about serialisation format, editability, and rendering strategy — decisions that affect whether content survives round-trips through Git storage, HTML export, and LMS import.

## Decision

Build three custom TipTap `Node` extensions as atomic, block-level nodes with HTML serialisation formats chosen for portability and round-trip safety.

### MermaidNode

- `atom: true`, `group: 'block'`
- **Serialisation:** `<pre class="mermaid">{source}</pre>` — source stored as text content inside a standard `<pre>` tag
- **Rendering:** `ReactNodeViewRenderer(MermaidView)` — a React component that calls `mermaid.render()` asynchronously to produce SVG, displayed via `dangerouslySetInnerHTML`
- **Editing:** Click "Edit source" to switch to a `<textarea>` overlay; changes committed back to TipTap via `updateAttributes({ source: draft })`
- **Error handling:** Mermaid parse errors shown in a red box within the node view
- **Unique IDs:** `useId()` generates a stable render ID (`mermaid_${uniqueId}`) to prevent Mermaid container conflicts

### YoutubeNode

- `atom: true`, `group: 'block'`
- **Serialisation:** `<div data-youtube-video=""><iframe src="..." width="640" height="360" allowfullscreen></iframe></div>`
- **URL handling:** `extractYoutubeId()` parses 5 URL patterns (`youtube.com/watch`, `/embed/`, `youtu.be/`, `/shorts/`, `youtube-nocookie.com/embed/`). All URLs are normalised to `https://www.youtube-nocookie.com/embed/{id}` for privacy (no tracking cookies)
- **Rendering:** TipTap's default HTML renderer (no React node view needed)
- **Validation:** Returns `false` from the insert command if the URL doesn't match any known pattern

### VideoNode

- `atom: true`, `group: 'block'`
- **Serialisation:** `<video src="..." controls style="max-width:100%;height:auto;"></video>`
- **Rendering:** TipTap's default HTML renderer
- **No URL normalisation** — accepts any video URL (MP4, WebM, etc.)

### Common Design Choices

All three nodes are `atom: true` — the cursor cannot be placed inside them. This prevents accidental editing of embed markup and ensures the node is always treated as a single unit for copy/paste, drag, and deletion.

HTML serialisation was chosen over custom JSON or markdown syntax because:
1. Content is stored as HTML in Git — custom formats would need an extra conversion layer
2. HTML exports and LMS imports handle standard tags (`<pre>`, `<iframe>`, `<video>`) natively
3. The `data-youtube-video` wrapper attribute survives HTML sanitisers that strip bare `<iframe>` tags

## Consequences

### Positive
- Content round-trips cleanly through Git storage, HTML export, and re-import
- `<pre class="mermaid">` is the standard Mermaid.js convention — any Mermaid-aware renderer can display the diagrams
- YouTube privacy mode (`youtube-nocookie.com`) avoids tracking cookies in educational content
- Atomic nodes prevent accidental corruption of embed markup

### Negative
- Only MermaidNode has a React node view with live preview; YouTube and Video render as static HTML in the editor (functional but less interactive)
- `atom: true` means users can't partially select content within these nodes
- YouTube URL extraction handles 5 patterns but may miss future URL format changes

### Neutral
- No server-side rendering fallback — Mermaid diagrams require JavaScript to render (acceptable for a web/Electron app)
- Video node accepts any URL without validation — broken URLs will show a broken player

## Alternatives Considered

### Markdown-Based Serialisation
- Store Mermaid as ` ```mermaid ` code blocks, YouTube as `![](url)` or custom syntax
- Rejected: requires markdown↔HTML conversion on every save/load; HTML is already the storage format

### Custom JSON Serialisation
- Store node data as JSON attributes in TipTap's internal format
- Rejected: works internally but produces unreadable HTML export; standard HTML tags are more portable

### iframe for All Embeds
- Use `<iframe>` for Mermaid (via a renderer service), YouTube, and video
- Rejected: Mermaid doesn't need an iframe — direct SVG rendering is faster and more accessible; `<video>` tag is semantically correct for direct video files

## Implementation Notes

- All extensions are in `frontend/src/components/Editor/`
- `MermaidView.tsx` is the React node view component; other nodes use TipTap's built-in renderer
- Extensions are registered in `RichTextEditor.tsx` via the TipTap `extensions` array
- YouTube ID extraction regex validates exactly 11 characters for the video ID
- Mermaid rendering is async — the node view shows a loading state until `mermaid.render()` resolves

## References

- `frontend/src/components/Editor/MermaidNode.ts`, `MermaidView.tsx`
- `frontend/src/components/Editor/YoutubeNode.ts`
- `frontend/src/components/Editor/VideoNode.ts`
- `frontend/src/components/Editor/RichTextEditor.tsx`
- [ADR-041: Image Storage in Git](041-image-storage-in-git.md) — same Git content store these nodes round-trip through
