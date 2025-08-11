# Plugin Catalog

This document lists all available plugins for Curriculum Curator, including built-in plugins and community contributions.

## Built-in Validators

### Quality Validators

#### Readability Validator
- **Name**: `readability`
- **Version**: 1.0.0
- **Category**: quality
- **Description**: Analyzes text readability using multiple metrics
- **Features**:
  - Flesch Reading Ease score
  - Flesch-Kincaid Grade Level
  - Gunning Fog Index
  - SMOG Index
  - Automated Readability Index
- **Configuration**:
  ```yaml
  readability:
    target_grade_level: 12
    min_flesch_score: 30
    max_sentence_length: 25
    max_syllables_per_word: 4
  ```

#### Structure Validator
- **Name**: `structure`
- **Version**: 1.0.0
- **Category**: quality
- **Description**: Validates document structure and organization
- **Features**:
  - Heading hierarchy check
  - Section balance analysis
  - Table of contents validation
  - Introduction/conclusion detection
- **Configuration**:
  ```yaml
  structure:
    require_title: true
    require_headings: true
    min_sections: 3
    max_heading_depth: 3
    require_introduction: true
    require_conclusion: true
  ```

#### Similarity Validator
- **Name**: `similarity`
- **Version**: 1.0.0
- **Category**: quality
- **Description**: Checks content similarity and plagiarism
- **Features**:
  - Internal similarity detection
  - External source checking (requires API)
  - Citation verification
- **Configuration**:
  ```yaml
  similarity:
    max_similarity_percentage: 20
    check_external: false
    api_key: ${PLAGIARISM_API_KEY}
  ```

### Language Validators

#### Grammar Validator
- **Name**: `grammar`
- **Version**: 1.0.0
- **Category**: language
- **Description**: Comprehensive grammar and spell checking
- **Features**:
  - Spelling correction
  - Grammar rules
  - Punctuation checking
  - Style consistency
- **Configuration**:
  ```yaml
  grammar:
    language: "en-US"
    check_spelling: true
    check_grammar: true
    check_style: true
    dictionary: "academic"
  ```

#### Language Detector
- **Name**: `language_detector`
- **Version**: 1.0.0
- **Category**: language
- **Description**: Detects and validates content language
- **Features**:
  - Multi-language detection
  - Mixed language warnings
  - Language consistency check
- **Configuration**:
  ```yaml
  language_detector:
    expected_language: "en"
    allow_mixed: false
    min_confidence: 0.8
  ```

### Alignment Validators

#### Learning Objectives Validator
- **Name**: `objectives_alignment`
- **Version**: 1.0.0
- **Category**: alignment
- **Description**: Validates alignment with learning objectives
- **Features**:
  - Objective coverage analysis
  - Bloom's taxonomy alignment
  - Assessment alignment check
- **Configuration**:
  ```yaml
  objectives_alignment:
    min_coverage: 0.8
    check_bloom_levels: true
    require_explicit_mapping: false
  ```

#### Curriculum Standards Validator
- **Name**: `standards_alignment`
- **Version**: 1.0.0
- **Category**: alignment
- **Description**: Checks alignment with curriculum standards
- **Features**:
  - Standards mapping
  - Coverage analysis
  - Gap identification
- **Configuration**:
  ```yaml
  standards_alignment:
    standards_set: "common_core"
    min_alignment_score: 0.7
    strict_mode: false
  ```

### Style Validators

#### Academic Style Validator
- **Name**: `academic_style`
- **Version**: 1.0.0
- **Category**: style
- **Description**: Ensures academic writing standards
- **Features**:
  - Formal tone checking
  - Citation format validation
  - Passive voice detection
  - Jargon analysis
- **Configuration**:
  ```yaml
  academic_style:
    formality_level: "high"
    citation_style: "APA"
    max_passive_voice_percentage: 10
    allow_contractions: false
  ```

#### Tone Consistency Validator
- **Name**: `tone_consistency`
- **Version**: 1.0.0
- **Category**: style
- **Description**: Maintains consistent tone throughout content
- **Features**:
  - Tone analysis
  - Formality consistency
  - Voice consistency
- **Configuration**:
  ```yaml
  tone_consistency:
    target_tone: "professional"
    allow_variance: 0.2
    check_sections: true
  ```

### Safety Validators

#### Content Safety Validator
- **Name**: `content_safety`
- **Version**: 1.0.0
- **Category**: safety
- **Description**: Ensures content is appropriate for educational use
- **Features**:
  - Inappropriate content detection
  - Age-appropriate checking
  - Sensitive topic handling
- **Configuration**:
  ```yaml
  content_safety:
    target_age_group: "13+"
    sensitivity_level: "medium"
    check_images: true
  ```

#### Accessibility Validator
- **Name**: `accessibility`
- **Version**: 1.0.0
- **Category**: safety
- **Description**: Validates content accessibility
- **Features**:
  - Alt text checking
  - Color contrast validation
  - Screen reader compatibility
  - Heading structure
- **Configuration**:
  ```yaml
  accessibility:
    wcag_level: "AA"
    check_images: true
    check_links: true
    require_alt_text: true
  ```

## Built-in Remediators

### AutoFix Remediators

#### Sentence Splitter
- **Name**: `sentence_splitter`
- **Version**: 1.0.0
- **Category**: autofix
- **Description**: Splits long sentences for better readability
- **Features**:
  - Intelligent sentence breaking
  - Conjunction detection
  - Meaning preservation
- **Configuration**:
  ```yaml
  sentence_splitter:
    max_words: 20
    split_on_conjunctions: true
    preserve_quotes: true
  ```

#### Format Corrector
- **Name**: `format_corrector`
- **Version**: 1.0.0
- **Category**: autofix
- **Description**: Fixes common formatting issues
- **Features**:
  - Heading normalization
  - List formatting
  - Quote standardization
  - Whitespace cleanup
- **Configuration**:
  ```yaml
  format_corrector:
    fix_headings: true
    fix_lists: true
    normalize_quotes: true
    trim_whitespace: true
  ```

#### Terminology Enforcer
- **Name**: `terminology_enforcer`
- **Version**: 1.0.0
- **Category**: autofix
- **Description**: Ensures consistent terminology usage
- **Features**:
  - Term replacement
  - Acronym expansion
  - Consistency checking
- **Configuration**:
  ```yaml
  terminology_enforcer:
    glossary_file: "terms.yaml"
    case_sensitive: false
    expand_acronyms: true
  ```

### Language Remediators

#### Translator
- **Name**: `translator`
- **Version**: 1.0.0
- **Category**: language
- **Description**: Translates content between languages
- **Features**:
  - Multi-language support
  - Context preservation
  - Educational terminology
- **Configuration**:
  ```yaml
  translator:
    source_language: "auto"
    target_language: "es"
    preserve_formatting: true
    api_provider: "google"
  ```

#### Simplifier
- **Name**: `simplifier`
- **Version**: 1.0.0
- **Category**: language
- **Description**: Simplifies complex language
- **Features**:
  - Vocabulary simplification
  - Sentence restructuring
  - Jargon removal
- **Configuration**:
  ```yaml
  simplifier:
    target_reading_level: 8
    preserve_technical_terms: true
    explain_complex_terms: true
  ```

### Rewrite Remediators

#### Style Adjuster
- **Name**: `style_adjuster`
- **Version**: 1.0.0
- **Category**: rewrite
- **Description**: Adjusts writing style to match preferences
- **Features**:
  - Tone adjustment
  - Formality changes
  - Voice conversion
- **Configuration**:
  ```yaml
  style_adjuster:
    target_style: "conversational"
    formality: "medium"
    voice: "active"
  ```

#### Rephrasing Prompter
- **Name**: `rephrasing_prompter`
- **Version**: 1.0.0
- **Category**: rewrite
- **Description**: Rephrases content for clarity
- **Features**:
  - LLM-powered rephrasing
  - Context awareness
  - Multiple alternatives
- **Configuration**:
  ```yaml
  rephrasing_prompter:
    llm_provider: "openai"
    temperature: 0.7
    alternatives: 3
  ```

### Workflow Remediators

#### Flag for Review
- **Name**: `flag_for_review`
- **Version**: 1.0.0
- **Category**: workflow
- **Description**: Flags content for human review
- **Features**:
  - Issue categorization
  - Review assignment
  - Comment system
- **Configuration**:
  ```yaml
  flag_for_review:
    auto_assign: false
    priority_threshold: "high"
    notification_enabled: true
  ```

## Community Plugins

### Featured Community Validators

#### Math Formula Validator
- **Name**: `math_validator`
- **Author**: Community Contributor
- **Description**: Validates mathematical formulas and LaTeX
- **Installation**: `pip install curriculum-curator-math-validator`
- **Features**:
  - LaTeX syntax checking
  - Formula rendering validation
  - Mathematical correctness

#### Code Block Validator
- **Name**: `code_validator`
- **Author**: DevEd Team
- **Description**: Validates code examples in content
- **Installation**: `pip install curriculum-curator-code-validator`
- **Features**:
  - Syntax highlighting check
  - Code execution testing
  - Language detection

#### Media Validator
- **Name**: `media_validator`
- **Author**: MediaEd Collective
- **Description**: Validates embedded media content
- **Installation**: `pip install curriculum-curator-media-validator`
- **Features**:
  - Image optimization
  - Video accessibility
  - Alt text quality

### Featured Community Remediators

#### Interactive Element Generator
- **Name**: `interactive_generator`
- **Author**: InteractEd
- **Description**: Adds interactive elements to content
- **Installation**: `pip install curriculum-curator-interactive`
- **Features**:
  - Quiz generation
  - Interactive diagrams
  - Embedded exercises

#### Visual Enhancement
- **Name**: `visual_enhancer`
- **Author**: VisualLearn
- **Description**: Enhances content with visual elements
- **Installation**: `pip install curriculum-curator-visual`
- **Features**:
  - Diagram generation
  - Infographic creation
  - Chart recommendations

## Plugin Development

### Creating Your Own Plugin

1. **Choose a Base Class**
   - Extend `BaseValidator` for validators
   - Extend `BaseRemediator` for remediators

2. **Implement Required Methods**
   - `validate()` for validators
   - `remediate()` for remediators

3. **Add Metadata**
   ```python
   metadata = PluginMetadata(
       name="my_plugin",
       version="1.0.0",
       description="My custom plugin",
       author="Your Name",
       category="custom",
       tags=["tag1", "tag2"]
   )
   ```

4. **Package and Distribute**
   - Create setup.py
   - Upload to PyPI
   - Share with community

### Plugin Submission Guidelines

1. **Quality Standards**
   - Comprehensive tests
   - Clear documentation
   - Example usage

2. **Performance Requirements**
   - Async support
   - Efficient algorithms
   - Resource limits

3. **Security Review**
   - No malicious code
   - Safe file operations
   - API key protection

## Plugin Compatibility

### Version Compatibility Matrix

| Plugin | CC 1.0 | CC 1.1 | CC 2.0 |
|--------|--------|--------|--------|
| readability | ✅ | ✅ | ✅ |
| structure | ✅ | ✅ | ✅ |
| grammar | ✅ | ✅ | 🔄 |
| math_validator | ❌ | ✅ | ✅ |
| code_validator | ❌ | ✅ | ✅ |

- ✅ Fully compatible
- 🔄 Requires update
- ❌ Not compatible

### Teaching Style Compatibility

Plugins work best with certain teaching styles:

| Plugin | Traditional | Constructivist | Project-Based | Flipped |
|--------|------------|----------------|---------------|----------|
| academic_style | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ |
| interactive_generator | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| simplifier | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| visual_enhancer | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## Plugin Resources

### Documentation
- [Plugin Development Guide](../guides/plugin-development.md)
- [API Reference](../api/plugins.md)
- [Example Plugins](https://github.com/curriculum-curator/example-plugins)

### Community
- [Plugin Forum](https://forum.curriculum-curator.org/plugins)
- [Discord Channel](https://discord.gg/curriculum-curator)
- [Plugin Marketplace](https://plugins.curriculum-curator.org)

### Support
- [Issue Tracker](https://github.com/curriculum-curator/curriculum-curator/issues)
- [Plugin FAQ](https://docs.curriculum-curator.org/faq/plugins)
- [Contact Support](mailto:plugins@curriculum-curator.org)