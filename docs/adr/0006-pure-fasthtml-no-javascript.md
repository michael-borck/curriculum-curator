# 6. Pure FastHTML Without JavaScript

Date: 2024-01-15

## Status

Accepted

## Context

When building a web application, there's often a choice between:
1. Traditional JavaScript-heavy Single Page Applications (SPAs)
2. Server-side rendering with progressive enhancement
3. Pure server-side applications with minimal/no client-side JavaScript

FastHTML is designed to work with HTMX, which allows for dynamic web applications without writing JavaScript. The user explicitly expressed a preference for "pure FastHTML" and asked if we could remove all JavaScript from the application.

## Decision

We will build the Curriculum Curator as a pure FastHTML application without any client-side JavaScript. All dynamic interactions will be handled server-side using HTMX attributes.

## Consequences

### Positive
- **Simplicity**: Single language (Python) for the entire application
- **Maintainability**: No need to maintain JavaScript build tools, dependencies, or separate frontend code
- **Accessibility**: Server-side rendering ensures better accessibility by default
- **SEO-friendly**: All content is rendered server-side
- **Reduced complexity**: No state synchronization between client and server
- **Progressive enhancement**: Works without JavaScript enabled
- **Faster initial load**: No JavaScript bundles to download and parse
- **Better security**: No client-side vulnerabilities or exposed business logic

### Negative
- **Limited offline functionality**: Requires server connection for all interactions
- **Increased server load**: Every interaction requires a server round-trip
- **Potential latency**: User interactions may feel less responsive on slow connections
- **Limited rich interactions**: Some complex UI patterns are harder without JavaScript
- **File upload limitations**: Can't show real-time upload progress or drag-and-drop without JS

### Mitigations
- Use HTMX's features like `hx-indicator` for loading states
- Implement proper caching strategies to reduce server load
- Use CSS animations and transitions for visual feedback
- Design UI to work well with server round-trips
- Keep responses lightweight and fast

## Examples

Instead of JavaScript tab switching:
```javascript
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    document.getElementById(tabName).classList.remove('hidden');
}
```

We use HTMX with server-side state:
```python
@rt("/expert/tab/{tab_name:str}")
def get(req, tab_name: str):
    # Return both navigation with active state and content
    return Div(
        tabs_with_active_state(tab_name),
        tab_content(tab_name),
        id="tab-container"
    )
```

## Related Decisions
- ADR-0005: Interactive Interfaces (specifies web-based interface)
- ADR-0007: Simple Authentication for Internal Networks (complementary security approach)