# 20. AI-Optional User Empowerment

Date: 2025-12-02

## Status

Accepted

## Context

The Curriculum Curator integrates AI capabilities for content generation, schedule planning, validation, and remediation. However, educators have varying:

- **Comfort levels with AI**: Some embrace it; others are skeptical or prohibited from using it
- **Institutional policies**: Some universities restrict or ban AI-generated content
- **Pedagogical beliefs**: Some educators feel AI undermines the craft of teaching
- **Practical needs**: Sometimes manual entry is faster than explaining to an AI
- **Quality standards**: AI output may not meet specific disciplinary conventions

### The Risk of AI-First Design

Many educational tools make AI central to their value proposition, which creates problems:

1. **Alienates non-AI users**: Tool feels useless without engaging AI features
2. **Creates dependency**: Users lose skills or never develop them
3. **Policy conflicts**: Institutional AI bans make the tool unusable
4. **Quality concerns**: AI-generated content may contain errors or inappropriate tone
5. **Loss of agency**: Users feel the tool is doing the work, not assisting them

### The Opportunity

AI should amplify educator expertise, not replace it. An educator with 20 years of experience shouldn't be forced through an AI workflow when they know exactly what they want to write.

## Decision

**Guiding Principle**: AI features are always optional assistants, never gatekeepers. Every task achievable with AI must be equally achievable without it.

### The Four Pathways Model

For every content creation task, users have four equal pathways:

| Pathway | Description | Use Case |
|---------|-------------|----------|
| **Manual** | Direct creation with rich text editor | Expert users, specific requirements, AI-restricted contexts |
| **AI-Assisted** | Generate draft, then edit and refine | Starting point needed, time-constrained, exploring ideas |
| **Import** | Upload existing files (PDF, DOCX, PPTX, etc.) | Migrating existing materials, digitising legacy content |
| **Research-Informed** | Web search for examples, then create | Learning from peers, checking standards, gathering inspiration |

### Implementation Patterns

**1. Content Creation (Lectures, Tutorials, Assessments)**
```
┌─────────────────────────────────────────────────────┐
│                  Content Creator                     │
├─────────────────────────────────────────────────────┤
│  [Title] [Unit Selection]                           │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ Optional: AI Generation                      │   │
│  │ Topic: [________________]                    │   │
│  │ [Generate with AI]                           │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ Content Editor (always available)            │   │
│  │ - Start typing manually                      │   │
│  │ - Or edit AI-generated content               │   │
│  │ - Or paste from external source              │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  [Save]                                              │
└─────────────────────────────────────────────────────┘
```

**2. Course Planning (Schedule Generation)**
```
┌─────────────────────────────────────────────────────┐
│                  Course Planner                      │
├──────────────────────┬──────────────────────────────┤
│  Research Tab        │  Schedule Tab                 │
│  - Search similar    │  - Manual week-by-week entry │
│    courses           │  - OR generate with AI       │
│  - View examples     │  - Edit either way           │
│  - Get inspiration   │  - Apply to unit             │
└──────────────────────┴──────────────────────────────┘
```

**3. Content Validation & Remediation**
```
┌─────────────────────────────────────────────────────┐
│              Content Quality (Optional)              │
├─────────────────────────────────────────────────────┤
│  [Check Compliance] ← User chooses to validate      │
│                                                      │
│  If issues found:                                    │
│  ├─ View suggestions (informational)                │
│  ├─ [Auto-fix] ← AI remediation (optional)          │
│  └─ Manual edit ← Always available                  │
│                                                      │
│  User can save without validating                    │
└─────────────────────────────────────────────────────┘
```

### UI/UX Principles

1. **No AI gates**: Never block a user action pending AI completion
2. **AI as expansion, not replacement**: AI sections expand/collapse; manual input always visible
3. **Clear labeling**: AI features marked with sparkle icon (✨) but not dominant
4. **Graceful degradation**: If AI service unavailable, tool remains fully functional
5. **No AI defaults**: Don't auto-trigger AI generation; user must explicitly request it
6. **Preserve user input**: Never overwrite manual content with AI content without confirmation

### Feature Matrix

| Feature | Manual | AI-Assisted | Import | Research |
|---------|--------|-------------|--------|----------|
| Create content | ✅ Rich text editor | ✅ Generate + edit | ✅ Upload PDF/DOCX/PPTX | ✅ Search examples |
| Plan schedule | ✅ Week-by-week form | ✅ AI schedule generator | N/A | ✅ Search similar courses |
| Set learning outcomes | ✅ Direct entry | ✅ AI suggestions | ✅ Extract from docs | ✅ Search standards |
| Validate content | ✅ Self-review | ✅ AI validation | ✅ Auto-analyse imports | N/A |
| Fix content issues | ✅ Manual edit | ✅ Auto-remediation | N/A | N/A |
| Choose teaching style | ✅ Direct selection | ✅ Quiz recommendation | N/A | N/A |

## Consequences

### Positive

- **Universal accessibility**: Tool works for all users regardless of AI policy
- **User agency**: Educators feel in control of their content
- **Trust building**: Users trust the tool because it respects their expertise
- **Institutional compliance**: Works in AI-restricted environments
- **Skill preservation**: Users maintain and develop their own capabilities
- **Flexibility**: Users mix approaches based on task and context

### Negative

- **Development overhead**: Every feature needs multiple pathways
- **UI complexity**: More options can overwhelm new users
- **Testing burden**: Must test all pathways independently
- **Documentation**: Must explain when to use each approach

### Neutral

- **AI features still prominent**: Available and discoverable, just not mandatory
- **Default to simplest path**: Manual/direct entry is often the default view

## Alternatives Considered

### AI-First with Manual Override

- **Description**: AI generates by default; users can edit or replace
- **Rejected because**: Creates psychological dependency; users feel they "should" use AI

### AI-Only for Generation

- **Description**: Only AI can create initial content; manual for editing only
- **Rejected because**: Excludes expert users; violates institutional policies

### Separate AI and Manual Tools

- **Description**: Different interfaces for AI vs manual workflows
- **Rejected because**: Fragments experience; users shouldn't need to choose tools

### AI Feature Flags

- **Description**: Admin can disable AI features entirely
- **Rejected because**: Too coarse; users should choose per-task, not globally

## Implementation Notes

### When Adding New Features

1. **Start with manual**: Design the manual workflow first
2. **Add AI as enhancement**: Layer AI assistance on top
3. **Consider research**: Can web search/examples help users?
4. **Test without AI**: Ensure feature works with AI service down
5. **Respect user choice**: Never auto-populate AI content

### Error Handling

- If AI fails: Show error, keep manual workflow available
- If AI slow: Show progress, allow cancel, don't block other actions
- If AI unavailable: Hide AI options gracefully, manual works normally

### Analytics (Future)

Track usage patterns to understand:
- % of content created manually vs AI-assisted
- Time spent editing AI content vs writing manually
- User progression (do they use more/less AI over time?)

## Related Decisions

- [ADR-018: Workflow Flexibility Philosophy](018-workflow-flexibility-philosophy.md) - Parent philosophy
- [ADR-004: Teaching Philosophy System](004-teaching-philosophy-system.md) - Teaching styles are also optional
- [ADR-015: Content Format and Export Strategy](015-content-format-and-export-strategy.md) - Export enables external workflows

## References

- [Human-Centered AI](https://hai.stanford.edu/) - Stanford's approach to AI that augments humans
- [AI Augmentation vs Automation](https://hbr.org/2021/03/ai-should-augment-human-intelligence-not-replace-it) - HBR on AI's proper role
- [The Centaur Model](https://en.wikipedia.org/wiki/Advanced_chess) - Human + AI collaboration outperforms either alone
