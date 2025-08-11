# 4. Teaching Philosophy and Style System

Date: 2025-08-01

## Status

Accepted

## Context

Educational content generation should adapt to different teaching philosophies and styles. The Tauri version included a teaching style detection system that influenced how content was generated. We need to:
- Support multiple teaching philosophies (constructivist, direct instruction, etc.)
- Detect a user's teaching style through a questionnaire
- Use teaching style to influence content generation
- Make the system pedagogically aware

## Decision

We will implement a comprehensive teaching philosophy system with:

1. **Nine Teaching Styles**:
   - Traditional Lecture
   - Constructivist
   - Direct Instruction
   - Inquiry-Based
   - Flipped Classroom
   - Project-Based
   - Competency-Based
   - Culturally Responsive
   - Mixed Approach

2. **Teaching Style Indicators**:
   - Interaction Level (0-10)
   - Structure Preference (0-10)
   - Student-Centered Approach (0-10)
   - Technology Integration (0-10)
   - Assessment Frequency (low/medium/high)
   - Collaboration Emphasis (0-10)

3. **Detection System**:
   - 5-question questionnaire
   - Algorithm to match responses to teaching styles
   - Confidence scoring
   - Primary and secondary style detection

4. **Integration Points**:
   - LLM prompt customization based on style
   - Validation criteria adjustments
   - Content structure adaptations
   - Assessment type recommendations

## Consequences

### Positive
- Pedagogically-aware content generation
- Personalized experience for educators
- Better alignment with teaching practices
- Supports diverse educational approaches
- Improves content relevance

### Negative
- Increased complexity in prompt generation
- More user onboarding steps
- Risk of oversimplifying teaching philosophies
- Need to maintain teaching style definitions

### Neutral
- Requires ongoing refinement based on user feedback
- May need academic validation
- Cultural considerations for international use

## Alternatives Considered

### Simple Style Selection
- Basic dropdown with 3-4 styles
- Rejected as too limiting

### No Teaching Style System
- One-size-fits-all approach
- Rejected as it ignores pedagogical diversity

### ML-Based Style Detection
- Analyze user's existing content to detect style
- Rejected as too complex for MVP

### Academic Framework Integration
- Use established educational frameworks
- Deferred for future enhancement

## Implementation Notes

```python
# Teaching style influences prompt generation
def get_prompt_adaptations(style: TeachingStyle) -> Dict[str, str]:
    if style == TeachingStyle.CONSTRUCTIVIST:
        return {
            "structure": "Create open-ended activities for exploration",
            "interaction": "Include reflection prompts and discussions",
            "assessment": "Use portfolio and self-assessment methods"
        }
    # ... other styles
```

- Store teaching style in user profile
- Allow manual style selection or detection
- Provide explanations for each teaching style
- Show how style influences generation

## References

- [Tauri Teaching Styles Implementation](../../TAURI_CONCEPTS_EXTRACTION.md#1-teaching-philosophies--styles)
- [Educational Theory Resources](#)
- [ADR-0003](0003-plugin-architecture.md) - How validators adapt to teaching styles