# Creating Custom Validators

This guide shows how to create custom validators for the Curriculum Curator plugin system.

## Overview

Validators analyze content and identify potential issues without modifying the content. They're perfect for:

- Checking content quality
- Ensuring consistency
- Validating formatting
- Detecting potential problems
- Enforcing standards

## Basic Validator Structure

### 1. Create the Validator File

Create a new file in the appropriate category under `plugins/validators/`:

```
plugins/validators/
├── quality/       # For content quality checks
├── language/      # For language and grammar
├── alignment/     # For curriculum alignment
├── style/         # For style consistency
├── safety/        # For content safety
└── custom/        # For your custom validators
```

### 2. Implement the Validator Class

```python
# plugins/validators/custom/word_count_validator.py

from plugins.validators.base import BaseValidator, ValidationResult, ValidationIssue
from plugins.base import PluginMetadata, Severity

class WordCountValidator(BaseValidator):
    """Validates that content meets word count requirements."""
    
    metadata = PluginMetadata(
        name="word_count",
        version="1.0.0",
        description="Checks if content meets word count requirements",
        author="Your Name",
        category="quality",
        tags=["length", "word count", "content size"]
    )
    
    async def validate(self, content: str, context=None):
        """Validate content word count."""
        issues = []
        
        # Get configuration
        min_words = self.config.get("min_words", 100)
        max_words = self.config.get("max_words", 5000)
        target_words = self.config.get("target_words", 1000)
        
        # Count words
        word_count = len(content.split())
        
        # Check minimum
        if word_count < min_words:
            issues.append(ValidationIssue(
                type="word_count_too_low",
                severity=Severity.ERROR,
                message=f"Content has {word_count} words, minimum is {min_words}",
                suggestion=f"Add at least {min_words - word_count} more words"
            ))
        
        # Check maximum
        elif word_count > max_words:
            issues.append(ValidationIssue(
                type="word_count_too_high",
                severity=Severity.WARNING,
                message=f"Content has {word_count} words, maximum is {max_words}",
                suggestion=f"Consider removing {word_count - max_words} words"
            ))
        
        # Check target (informational)
        elif abs(word_count - target_words) > target_words * 0.2:
            issues.append(ValidationIssue(
                type="word_count_off_target",
                severity=Severity.INFO,
                message=f"Content has {word_count} words, target is {target_words}"
            ))
        
        # Calculate score (0-100)
        if word_count < min_words:
            score = (word_count / min_words) * 50
        elif word_count > max_words:
            score = max(0, 100 - ((word_count - max_words) / max_words) * 50)
        else:
            # Score based on distance from target
            distance = abs(word_count - target_words) / target_words
            score = max(0, 100 - (distance * 100))
        
        return ValidationResult(
            issues=issues,
            score=score,
            metadata={"word_count": word_count}
        )
```

## Advanced Validator Examples

### Context-Aware Validator

```python
class CurriculumAlignmentValidator(BaseValidator):
    """Validates content alignment with curriculum standards."""
    
    metadata = PluginMetadata(
        name="curriculum_alignment",
        version="1.0.0",
        description="Checks alignment with curriculum standards",
        author="Education Team",
        category="alignment",
        tags=["curriculum", "standards", "objectives"]
    )
    
    async def validate(self, content: str, context=None):
        issues = []
        
        # Extract learning objectives from context
        if not context or "objectives" not in context:
            issues.append(ValidationIssue(
                type="missing_objectives",
                severity=Severity.ERROR,
                message="No learning objectives provided for alignment check"
            ))
            return ValidationResult(issues=issues, score=0)
        
        objectives = context["objectives"]
        grade_level = context.get("grade_level", "unknown")
        
        # Check each objective
        covered_objectives = []
        for objective in objectives:
            if self._is_objective_covered(content, objective):
                covered_objectives.append(objective)
        
        coverage = len(covered_objectives) / len(objectives)
        
        if coverage < 0.8:
            missing = set(objectives) - set(covered_objectives)
            issues.append(ValidationIssue(
                type="incomplete_coverage",
                severity=Severity.WARNING,
                message=f"Only {coverage*100:.0f}% of objectives covered",
                suggestion=f"Add content for: {', '.join(missing)}"
            ))
        
        return ValidationResult(
            issues=issues,
            score=coverage * 100,
            metadata={
                "covered_objectives": covered_objectives,
                "coverage_percentage": coverage * 100
            }
        )
    
    def _is_objective_covered(self, content: str, objective: str):
        """Check if objective is covered in content."""
        # Simple keyword matching - could use NLP here
        keywords = objective.lower().split()
        content_lower = content.lower()
        
        # Require at least 60% of keywords
        matches = sum(1 for kw in keywords if kw in content_lower)
        return matches >= len(keywords) * 0.6
```

### Async Validator with External API

```python
import httpx

class PlagiarismValidator(BaseValidator):
    """Checks content for potential plagiarism."""
    
    metadata = PluginMetadata(
        name="plagiarism_check",
        version="1.0.0",
        description="Detects potential plagiarism in content",
        author="Academic Integrity Team",
        category="safety",
        tags=["plagiarism", "originality", "academic integrity"]
    )
    
    async def validate(self, content: str, context=None):
        issues = []
        
        # Call external plagiarism API
        api_key = self.config.get("api_key")
        if not api_key:
            issues.append(ValidationIssue(
                type="missing_api_key",
                severity=Severity.ERROR,
                message="Plagiarism API key not configured"
            ))
            return ValidationResult(issues=issues, score=0)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.plagiarismchecker.example/check",
                    json={"content": content},
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    similarity_score = result["similarity_percentage"]
                    
                    if similarity_score > 20:
                        issues.append(ValidationIssue(
                            type="high_similarity",
                            severity=Severity.WARNING,
                            message=f"Content has {similarity_score}% similarity to existing sources",
                            suggestion="Review and revise similar sections",
                            metadata={"sources": result.get("matched_sources", [])}
                        ))
                    
                    return ValidationResult(
                        issues=issues,
                        score=100 - similarity_score,
                        metadata={"similarity_percentage": similarity_score}
                    )
                    
        except Exception as e:
            self.logger.error(f"Plagiarism check failed: {e}")
            issues.append(ValidationIssue(
                type="check_failed",
                severity=Severity.ERROR,
                message="Could not complete plagiarism check"
            ))
        
        return ValidationResult(issues=issues, score=0)
```

## Configuration

### Plugin Configuration

Validators can be configured in `config.yaml`:

```yaml
validation:
  validator_config:
    word_count:
      min_words: 500
      max_words: 2000
      target_words: 1000
    
    plagiarism_check:
      api_key: ${PLAGIARISM_API_KEY}
      threshold: 20
    
    curriculum_alignment:
      strict_mode: true
      min_coverage: 0.8
```

### Per-Course Configuration

Validators can also receive course-specific configuration:

```python
# When calling the validator
context = {
    "course_id": "cs101",
    "grade_level": "undergraduate",
    "objectives": ["understand loops", "implement functions"],
    "config_overrides": {
        "min_words": 1000  # Override for this specific validation
    }
}

result = await validator.validate(content, context)
```

## Testing Your Validator

### Unit Test Example

```python
# tests/test_validators/test_word_count.py

import pytest
from plugins.validators.custom.word_count_validator import WordCountValidator

@pytest.mark.asyncio
async def test_word_count_validator():
    validator = WordCountValidator({
        "min_words": 10,
        "max_words": 100,
        "target_words": 50
    })
    
    # Test too short
    result = await validator.validate("Short content")
    assert len(result.issues) == 1
    assert result.issues[0].severity == "ERROR"
    assert result.score < 50
    
    # Test good length
    good_content = " ".join(["word"] * 50)
    result = await validator.validate(good_content)
    assert len(result.issues) == 0
    assert result.score == 100
    
    # Test too long
    long_content = " ".join(["word"] * 200)
    result = await validator.validate(long_content)
    assert len(result.issues) == 1
    assert result.issues[0].severity == "WARNING"
```

### Integration Test

```python
@pytest.mark.asyncio
async def test_validator_in_pipeline():
    manager = ValidationManager()
    
    content = "Test content for validation"
    results = await manager.validate(
        content,
        validators=["word_count", "readability"]
    )
    
    assert "word_count" in results
    assert "readability" in results
```

## Best Practices

### 1. Clear Metadata

- Use descriptive names
- Version your validators
- Add helpful descriptions
- Include relevant tags

### 2. Meaningful Severity Levels

- **ERROR**: Content fails requirements
- **WARNING**: Content should be improved
- **INFO**: Suggestions for enhancement

### 3. Helpful Messages

```python
# Good
issue = ValidationIssue(
    type="passive_voice",
    severity=Severity.INFO,
    message="Sentence uses passive voice",
    line=5,
    suggestion="Consider: 'The student completed the assignment'"
)

# Bad
issue = ValidationIssue(
    type="error",
    severity=Severity.WARNING,
    message="Bad sentence"
)
```

### 4. Performance Considerations

- Use async for I/O operations
- Cache expensive computations
- Limit external API calls
- Process large content in chunks

### 5. Error Handling

```python
async def validate(self, content: str, context=None):
    try:
        # Main validation logic
        pass
    except SpecificError as e:
        # Handle known errors gracefully
        return ValidationResult(
            issues=[ValidationIssue(
                type="validation_error",
                severity=Severity.ERROR,
                message=f"Validation failed: {str(e)}"
            )],
            score=0
        )
    except Exception as e:
        # Log unexpected errors
        self.logger.error(f"Unexpected error: {e}")
        raise
```

## Common Validator Patterns

### Pattern Matching

```python
import re

patterns = {
    "questions": re.compile(r'\?\s*$', re.MULTILINE),
    "lists": re.compile(r'^\s*[-*+•]\s+', re.MULTILINE),
    "headings": re.compile(r'^#{1,6}\s+', re.MULTILINE)
}

question_count = len(patterns["questions"].findall(content))
```

### Natural Language Processing

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp(content)

# Analyze sentences
for sent in doc.sents:
    if len(sent) > 30:
        issues.append(ValidationIssue(
            type="long_sentence",
            severity=Severity.INFO,
            message=f"Long sentence ({len(sent)} words)"
        ))
```

### Statistical Analysis

```python
import textstat

# Readability scores
flesch_score = textstat.flesch_reading_ease(content)
grade_level = textstat.flesch_kincaid_grade(content)

if grade_level > target_grade + 2:
    issues.append(ValidationIssue(
        type="reading_level_high",
        severity=Severity.WARNING,
        message=f"Content is at grade {grade_level}, target is {target_grade}"
    ))
```

## Publishing Your Validator

### 1. Package Structure

```
my-validator-package/
├── setup.py
├── README.md
├── LICENSE
├── requirements.txt
├── my_validators/
│   ├── __init__.py
│   └── academic_validator.py
└── tests/
    └── test_academic_validator.py
```

### 2. Make it Installable

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="curriculum-curator-academic-validators",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "curriculum-curator>=1.0.0",
        "spacy>=3.0.0"
    ],
    entry_points={
        "curriculum_curator.validators": [
            "academic = my_validators:AcademicValidator"
        ]
    }
)
```

### 3. Document Usage

```markdown
# Academic Validators for Curriculum Curator

## Installation

```bash
pip install curriculum-curator-academic-validators
```

## Usage

The validators will be automatically discovered...
```

## Next Steps

- Learn about [Creating Remediators](custom-remediators.md)
- Explore [Teaching Style Integration](teaching-styles.md)
- Review [Plugin Architecture](../concepts/plugin-system.md)