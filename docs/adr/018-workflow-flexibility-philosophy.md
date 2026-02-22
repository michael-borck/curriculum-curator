# 18. Workflow Flexibility Philosophy

Date: 2025-12-01

## Status

Accepted

## Context

The Curriculum Curator serves educators with diverse backgrounds, tool preferences, and institutional constraints:

- **Traditional lecturers**: Comfortable with PowerPoint, Word, LMS interfaces
- **Technical educators**: Prefer Markdown, CLI tools, version control
- **Institutional constraints**: Must upload to specific LMS, use mandated templates
- **Personal workflows**: Some draft in Word, others in Notion, others directly in LMS

Previous educational tools often fail because they:
1. Force users to adopt a new workflow entirely
2. Become "yet another tool" in an already crowded toolkit
3. Don't integrate with existing practices
4. Assume a single "correct" way to create content

### The Risk

If we build an opinionated tool that enforces a specific workflow, we risk:
- Low adoption ("I don't have time to learn another system")
- Partial use ("I'll just use it for generation, then copy elsewhere")
- Abandonment ("It doesn't fit how I work")

## Decision

**Guiding Principle**: The Curriculum Curator assists educators in their existing workflows rather than enforcing a new one.

### What This Means

| Principle | Implementation |
|-----------|----------------|
| **Meet users where they are** | Support multiple input/output formats |
| **Provide defaults, not mandates** | Sensible defaults with override options |
| **Enable, don't require** | Features are opt-in, not forced |
| **Draft, don't dictate** | Tool generates first drafts; users refine elsewhere if preferred |
| **Integrate, don't replace** | Work alongside existing tools (Word, LMS, etc.) |

### Concrete Examples

**Content Creation:**
- Generate content in our tool → Export to Word → Continue editing in Word ✓
- Generate content → Copy HTML → Paste into LMS ✓
- Generate content → Edit in our tool → Save internally ✓
- Import existing PDF → Enhance → Export to preferred format ✓

**Editing Modes:**
- Simple: WYSIWYG for non-technical users (default)
- Power: Raw Markdown for technical users (opt-in)
- Neither mode is "better" - they serve different users

**Storage:**
- Content stored internally with Git versioning
- User can export and maintain their own copies
- No lock-in - all content exportable at any time

**LLM Generation:**
- Generates a starting point, not a final product
- User always has final editorial control
- Suggestions, not requirements

### What This Does NOT Mean

- **Not "anything goes"**: We still have consistent internal formats (Markdown)
- **Not "no opinions"**: We provide sensible defaults and recommendations
- **Not "no structure"**: The tool has a clear architecture and patterns
- **Not "infinite customization"**: We support common workflows, not every edge case

## Consequences

### Positive

- **Higher adoption**: Lower barrier - fits into existing practices
- **Reduced friction**: Users don't need to change how they work
- **Broader appeal**: Serves both technical and non-technical educators
- **Sustainable use**: Tool remains useful even if workflows evolve
- **Trust building**: Users feel in control, not controlled

### Negative

- **More development work**: Supporting multiple formats/modes takes effort
- **Testing complexity**: More code paths to validate
- **Documentation burden**: Must explain multiple ways to do things
- **Feature creep risk**: "Support my workflow too" requests

### Neutral

- **Opinionated defaults**: We still recommend best practices
- **Internal consistency**: One internal format (Markdown) enables flexibility

## How This Affects Other Decisions

This philosophy influenced:

| Decision | How Philosophy Applied |
|----------|----------------------|
| **ADR-015 (Content Format)** | Markdown internal, export to any format |
| **ADR-004 (Teaching Philosophy)** | 9 styles, none mandatory |
| **ADR-015 (Dual Editing)** | WYSIWYG + Power mode, user choice |
| **Export Strategy** | HTML, PDF, DOCX, PPTX - user picks |
| **Import Support** | Accept PDF, DOCX, not just our format |

Future decisions should ask: **"Does this assist the user's workflow or impose ours?"**

## Alternatives Considered

### Opinionated Single Workflow

- **Description**: One way to create content, optimized for that path
- **Rejected because**: Conflicts with diverse user needs; would limit adoption

### Fully Customizable Everything

- **Description**: Let users configure every aspect of the tool
- **Rejected because**: Complexity explosion; analysis paralysis for users

### Plugin-Based Workflow Extensions

- **Description**: Core workflow with plugins for variations
- **Rejected because**: Too complex for MVP; may revisit post-launch

## Implementation Notes

When implementing new features, apply this checklist:

1. **Default behavior**: What should happen for a user who just wants it to work?
2. **Override option**: Can advanced users customize this?
3. **Export path**: Can the output be used outside our tool?
4. **Import path**: Can existing content be brought in?
5. **No lock-in**: Is the user's data portable?

## References

- [ADR-004: Teaching Philosophy System](004-teaching-philosophy-system.md)
- [ADR-015: Content Format and Export Strategy](015-content-format-and-export-strategy.md)
- [The Tyranny of the Marginal User](https://nothinghuman.substack.com/p/the-tyranny-of-the-marginal-user) - Why flexibility matters
