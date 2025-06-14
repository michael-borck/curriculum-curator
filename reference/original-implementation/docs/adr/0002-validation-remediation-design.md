# 2. Validation and Remediation Design

Date: 2025-04-05

## Status

Accepted

## Context

The Curriculum Curator needs to ensure high-quality educational content. This requires both validation (detecting quality issues) and remediation (fixing those issues). We need to define the relationship between these two components and how they should work together in the system.

## Decision

We will implement a two-stage approach with validation followed by remediation, but allow for flexibility in how they're used:

1. **Validation System**:
   - Modular validators that check specific aspects of content quality
   - Each validator focuses on a single concern (readability, structure, factuality, etc.)
   - Validation produces a list of issues with detailed metadata
   - Validators don't modify content; they only detect problems

2. **Remediation System**:
   - Modular remediators that fix specific types of issues
   - Organized into categories based on remediation strategy:
     - **AutoFix**: Automated fixes without LLM assistance (format, spelling, etc.)
     - **Rewrite**: LLM-assisted content rewriting (rephrasing, elaboration, etc.)
     - **Workflow**: Process actions that might require human intervention (flagging, quarantine, etc.)
   - Remediators can be invoked either:
     - Reactively in response to validation failures
     - Proactively as part of content processing (optional)

3. **Configuration-Driven Behavior**:
   - Both validators and remediators are configurable through the application configuration
   - Configuration determines which validators and remediators are active
   - Default behavior is validation-driven but can be customized

4. **Workflow Integration**:
   - Standard workflow steps include validation and remediation
   - Workflows can be configured to:
     - Validate and fail on issues
     - Validate and auto-remediate
     - Validate, remediate, and re-validate
     - Skip validation and apply proactive remediation

## Alternative Approaches Considered

1. **Combined Validator-Remediator Components**:
   - Components that both detect and fix issues
   - Rejected because it violates single responsibility principle
   - Would make it harder to mix and match validation and remediation strategies

2. **LLM-Only Approach**:
   - Using LLMs for all validation and remediation
   - Rejected because specialized tools are more efficient for many tasks
   - Hybrid approach using specialized tools and LLMs is more flexible

3. **Manual Review Only**:
   - Flagging all issues for human review
   - Rejected because many issues can be fixed automatically
   - Retained as an option for critical issues

## Planned Validator Types

| Category | Validator Type | Description |
|----------|---------------|-------------|
| Quality | Structure | Checks if content has required sections and organization |
| Quality | Readability | Evaluates reading level, sentence complexity, etc. |
| Quality | Similarity | Detects duplicate or highly similar content |
| Quality | Coherence | Checks logical flow and transitions |
| Quality | Completeness | Verifies all required content is present |
| Quality | Consistency | Identifies internal contradictions |
| Quality | Generic Content | Flags overly generic or formulaic content |
| Accuracy | Factuality | Checks for factual accuracy or hallucinations |
| Accuracy | References | Validates citations and references |
| Alignment | Objectives | Verifies alignment with learning objectives |
| Alignment | Relevance | Checks if content stays on topic |
| Alignment | Age Appropriateness | Ensures content is suitable for target audience |
| Alignment | Instruction Adherence | Verifies compliance with prompt instructions |
| Style | Bias | Detects potential bias in language or examples |
| Style | Tone | Checks if tone matches requirements |
| Language | Language Detection | Identifies the language of content |
| Language | Grammar | Checks for grammatical correctness |
| Language | Spelling | Detects spelling errors |
| Safety | Content Safety | Checks for harmful or inappropriate content |

## Planned Remediator Types

| Category | Remediator Type | Description |
|----------|----------------|-------------|
| AutoFix | Format Corrector | Fixes markdown syntax and formatting |
| AutoFix | Sentence Splitter | Breaks long sentences to improve readability |
| AutoFix | Terminology Enforcer | Ensures consistent terminology usage |
| AutoFix | Synonym Replacer | Varies word choice to reduce repetition |
| AutoFix | Punctuation Corrector | Fixes punctuation errors |
| AutoFix | Filler Remover | Eliminates vague or generic filler content |
| AutoFix | Grammar Corrector | Fixes grammatical errors |
| AutoFix | Spelling Corrector | Fixes spelling errors |
| Rewrite | Rephrasing Prompter | Uses LLM to rewrite problematic content |
| Rewrite | Detail Enhancer | Uses LLM to add specific details |
| Rewrite | Tone Adjuster | Uses LLM to adjust content tone |
| Rewrite | Prompt Refiner | Suggests improvements to original prompt |
| Workflow | Flag for Review | Marks content for human review |
| Workflow | Quarantine Content | Prevents problematic content from inclusion |
| Workflow | Content Merger | Combines or reconciles duplicate content |
| Language | Translator | Translates content between languages |

## Validation-Remediation Mapping

Some validators have natural corresponding remediators:

| Validator | Remediator |
|-----------|------------|
| Readability | Sentence Splitter |
| Similarity | Rephrasing Prompter |
| Structure | Format Corrector |
| Factuality | Flag for Review |
| Bias | Flag for Review |
| Grammar | Grammar Corrector |
| Spelling | Spelling Corrector |
| Language Detection | Translator |

## Consequences

**Positive:**
- Clear separation of concerns between validation and remediation
- Flexible architecture that can be extended with new validators and remediators
- Configurable behavior to support different use cases
- Support for both automated and human-in-the-loop processes

**Negative:**
- Increased system complexity
- Need to maintain mappings between validators and appropriate remediators
- Configuration becomes more complex

**Neutral:**
- Validators and remediators need to follow consistent interfaces
- Dependency on LLMs for some remediation strategies introduces variability
