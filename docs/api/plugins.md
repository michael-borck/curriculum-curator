# Plugin APIs

This document describes the APIs for creating custom validators and remediators.

## Base Plugin API

### BasePlugin Class

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging

@dataclass
class PluginMetadata:
    """Metadata for plugin identification and discovery."""
    name: str                # Unique plugin identifier
    version: str            # Semantic version (e.g., "1.0.0")
    description: str        # Human-readable description
    author: str            # Plugin author
    category: str          # Plugin category
    tags: List[str]        # Searchable tags
    
class BasePlugin(ABC):
    """Base class for all plugins."""
    
    # Must be defined by subclasses
    metadata: PluginMetadata = None
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin with optional configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
```

## Validator API

### BaseValidator Class

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

class Severity(Enum):
    """Issue severity levels."""
    ERROR = "error"      # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"       # Consider fixing

@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    type: str                       # Issue type identifier
    severity: Severity              # Issue severity
    message: str                    # Human-readable message
    line: Optional[int] = None      # Line number (1-based)
    column: Optional[int] = None    # Column number (1-based)
    suggestion: Optional[str] = None # Fix suggestion
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result of validation."""
    issues: List[ValidationIssue]   # List of issues found
    score: float                    # Overall score (0-100)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseValidator(BasePlugin):
    """Base class for validators."""
    
    @abstractmethod
    async def validate(
        self, 
        content: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate content and return issues.
        
        Args:
            content: The content to validate
            context: Optional context information
                - material_type: Type of material (lecture, quiz, etc.)
                - grade_level: Target grade level
                - subject: Subject area
                - course_id: Course identifier
                - teaching_style: Teaching philosophy
                - custom: Any custom context data
        
        Returns:
            ValidationResult with issues and score
        """
        pass
```

### Validator Implementation Example

```python
from plugins.validators.base import (
    BaseValidator, ValidationResult, ValidationIssue, Severity
)
from plugins.base import PluginMetadata
import re

class URLValidator(BaseValidator):
    """Validates URLs in content."""
    
    metadata = PluginMetadata(
        name="url_validator",
        version="1.0.0",
        description="Checks URLs for validity and accessibility",
        author="Curriculum Team",
        category="quality",
        tags=["urls", "links", "accessibility"]
    )
    
    async def validate(self, content: str, context=None):
        issues = []
        
        # Find all URLs
        url_pattern = re.compile(
            r'https?://[^\s<>"{}\\|\^\[\]`]+'
        )
        
        urls = url_pattern.findall(content)
        
        for url in urls:
            # Check URL format
            if not self._is_valid_url(url):
                issues.append(ValidationIssue(
                    type="invalid_url",
                    severity=Severity.ERROR,
                    message=f"Invalid URL format: {url}"
                ))
            
            # Check if educational
            if self.config.get("require_educational", False):
                if not self._is_educational_url(url):
                    issues.append(ValidationIssue(
                        type="non_educational_url",
                        severity=Severity.WARNING,
                        message=f"URL may not be educational: {url}",
                        suggestion="Consider using academic sources"
                    ))
        
        # Calculate score
        if not urls:
            score = 100
        else:
            error_count = sum(1 for i in issues if i.severity == Severity.ERROR)
            score = max(0, 100 - (error_count * 20))
        
        return ValidationResult(
            issues=issues,
            score=score,
            metadata={"url_count": len(urls)}
        )
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        # Basic validation logic
        return url.startswith(('http://', 'https://'))
    
    def _is_educational_url(self, url: str) -> bool:
        """Check if URL is from educational domain."""
        educational_domains = [
            '.edu', '.ac.uk', '.edu.au', 'wikipedia.org',
            'khanacademy.org', 'coursera.org'
        ]
        return any(domain in url for domain in educational_domains)
```

## Remediator API

### BaseRemediator Class

```python
@dataclass
class RemediationResult:
    """Result of remediation attempt."""
    content: str                # Modified content
    changes_made: List[str]     # Description of changes
    success: bool              # Whether remediation succeeded
    error: Optional[str] = None # Error message if failed
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseRemediator(BasePlugin):
    """Base class for remediators."""
    
    @abstractmethod
    async def remediate(
        self,
        content: str,
        issues: Optional[List[ValidationIssue]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RemediationResult:
        """
        Remediate content based on issues.
        
        Args:
            content: The content to remediate
            issues: Validation issues to address
            context: Optional context information
        
        Returns:
            RemediationResult with modified content
        """
        pass
    
    def can_handle(self, issue: ValidationIssue) -> bool:
        """
        Check if this remediator can handle the issue.
        
        Override this method to specify which issues
        this remediator can fix.
        """
        return True
```

### Remediator Implementation Example

```python
from plugins.remediators.base import (
    BaseRemediator, RemediationResult
)
from plugins.base import PluginMetadata
import re

class HeadingHierarchyFixer(BaseRemediator):
    """Fixes heading hierarchy issues."""
    
    metadata = PluginMetadata(
        name="heading_hierarchy_fixer",
        version="1.0.0",
        description="Ensures proper heading hierarchy in documents",
        author="Curriculum Team",
        category="structure",
        tags=["headings", "structure", "markdown"]
    )
    
    async def remediate(self, content: str, issues=None, context=None):
        changes = []
        lines = content.split('\n')
        
        # Track heading levels
        last_level = 0
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check if line is a heading
            heading_match = re.match(r'^(#+)\s+(.+)$', line)
            
            if heading_match:
                hashes = heading_match.group(1)
                title = heading_match.group(2)
                current_level = len(hashes)
                
                # Fix hierarchy jumps
                if last_level > 0 and current_level > last_level + 1:
                    # Adjust level
                    new_level = last_level + 1
                    new_line = '#' * new_level + ' ' + title
                    fixed_lines.append(new_line)
                    changes.append(
                        f"Fixed heading hierarchy at line {i+1}: "
                        f"changed level {current_level} to {new_level}"
                    )
                    last_level = new_level
                else:
                    fixed_lines.append(line)
                    last_level = current_level
            else:
                fixed_lines.append(line)
        
        # Join lines back
        fixed_content = '\n'.join(fixed_lines)
        
        return RemediationResult(
            content=fixed_content,
            changes_made=changes,
            success=True,
            metadata={"headings_fixed": len(changes)}
        )
    
    def can_handle(self, issue: ValidationIssue) -> bool:
        """Check if we can handle this issue type."""
        return issue.type in [
            "heading_hierarchy",
            "heading_skip",
            "multiple_h1"
        ]
```

## Plugin Registry API

### PluginRegistry Class

```python
class PluginRegistry:
    """Central registry for all plugins."""
    
    def __init__(self):
        self._validators: Dict[str, Type[BaseValidator]] = {}
        self._remediators: Dict[str, Type[BaseRemediator]] = {}
        self._instances: Dict[str, BasePlugin] = {}
    
    def register_validator(
        self, 
        name: str, 
        validator_class: Type[BaseValidator]
    ) -> None:
        """Register a validator."""
        if not issubclass(validator_class, BaseValidator):
            raise TypeError(f"{validator_class} must inherit from BaseValidator")
        self._validators[name] = validator_class
    
    def register_remediator(
        self, 
        name: str, 
        remediator_class: Type[BaseRemediator]
    ) -> None:
        """Register a remediator."""
        if not issubclass(remediator_class, BaseRemediator):
            raise TypeError(f"{remediator_class} must inherit from BaseRemediator")
        self._remediators[name] = remediator_class
    
    def get_validator(
        self, 
        name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseValidator]:
        """Get validator instance by name."""
        if name not in self._validators:
            return None
        
        # Check if instance exists
        instance_key = f"validator:{name}"
        if instance_key not in self._instances:
            # Create new instance
            validator_class = self._validators[name]
            self._instances[instance_key] = validator_class(config)
        
        return self._instances[instance_key]
    
    def get_remediator(
        self, 
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseRemediator]:
        """Get remediator instance by name."""
        if name not in self._remediators:
            return None
        
        # Check if instance exists
        instance_key = f"remediator:{name}"
        if instance_key not in self._instances:
            # Create new instance
            remediator_class = self._remediators[name]
            self._instances[instance_key] = remediator_class(config)
        
        return self._instances[instance_key]
    
    def list_validators(self) -> List[Dict[str, Any]]:
        """List all registered validators."""
        validators = []
        for name, validator_class in self._validators.items():
            if hasattr(validator_class, 'metadata'):
                metadata = validator_class.metadata
                validators.append({
                    "name": name,
                    "version": metadata.version,
                    "description": metadata.description,
                    "author": metadata.author,
                    "category": metadata.category,
                    "tags": metadata.tags
                })
        return validators
    
    def list_remediators(self) -> List[Dict[str, Any]]:
        """List all registered remediators."""
        remediators = []
        for name, remediator_class in self._remediators.items():
            if hasattr(remediator_class, 'metadata'):
                metadata = remediator_class.metadata
                remediators.append({
                    "name": name,
                    "version": metadata.version,
                    "description": metadata.description,
                    "author": metadata.author,
                    "category": metadata.category,
                    "tags": metadata.tags
                })
        return remediators
```

## Plugin Discovery

### Automatic Discovery

```python
import importlib
import inspect
from pathlib import Path

def discover_plugins(
    plugin_type: str,
    plugin_dir: Path = None
) -> int:
    """
    Discover and register plugins.
    
    Args:
        plugin_type: 'validators' or 'remediators'
        plugin_dir: Directory to search (default: plugins/{plugin_type})
    
    Returns:
        Number of plugins discovered
    """
    if plugin_dir is None:
        plugin_dir = Path(__file__).parent / plugin_type
    
    count = 0
    base_module = f"plugins.{plugin_type}"
    
    # Search for Python files
    for file_path in plugin_dir.rglob("*.py"):
        if file_path.name.startswith("_"):
            continue
        
        # Build module path
        relative_path = file_path.relative_to(plugin_dir.parent)
        module_path = str(relative_path).replace("/", ".")[:-3]
        
        try:
            # Import module
            module = importlib.import_module(module_path)
            
            # Find plugin classes
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    # Check if it's a plugin
                    if plugin_type == "validators":
                        if issubclass(obj, BaseValidator) and obj != BaseValidator:
                            if hasattr(obj, 'metadata') and obj.metadata:
                                registry.register_validator(
                                    obj.metadata.name, obj
                                )
                                count += 1
                    elif plugin_type == "remediators":
                        if issubclass(obj, BaseRemediator) and obj != BaseRemediator:
                            if hasattr(obj, 'metadata') and obj.metadata:
                                registry.register_remediator(
                                    obj.metadata.name, obj
                                )
                                count += 1
        
        except Exception as e:
            logger.error(f"Failed to load plugin from {module_path}: {e}")
    
    return count
```

## Manager APIs

### ValidationManager

```python
class ValidationManager:
    """Manages validation pipeline."""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
    
    async def validate(
        self,
        content: str,
        validators: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run validators on content.
        
        Args:
            content: Content to validate
            validators: List of validator names (None = use defaults)
            context: Validation context
        
        Returns:
            Aggregated validation results
        """
        if validators is None:
            validators = self.get_default_validators(context)
        
        results = {}
        overall_score = 0
        all_issues = []
        
        for validator_name in validators:
            validator = self.registry.get_validator(validator_name)
            if not validator:
                logger.warning(f"Validator '{validator_name}' not found")
                continue
            
            try:
                result = await validator.validate(content, context)
                results[validator_name] = {
                    "score": result.score,
                    "issues": [
                        {
                            "type": issue.type,
                            "severity": issue.severity.value,
                            "message": issue.message,
                            "line": issue.line,
                            "column": issue.column,
                            "suggestion": issue.suggestion
                        }
                        for issue in result.issues
                    ],
                    "metadata": result.metadata
                }
                overall_score += result.score
                all_issues.extend(result.issues)
            
            except Exception as e:
                logger.error(f"Validator '{validator_name}' failed: {e}")
                results[validator_name] = {
                    "error": str(e),
                    "score": 0,
                    "issues": []
                }
        
        # Calculate overall score
        if validators:
            overall_score /= len(validators)
        
        return {
            "overall_score": overall_score,
            "validators": results,
            "total_issues": len(all_issues),
            "issues_by_severity": self._group_by_severity(all_issues)
        }
    
    def get_default_validators(
        self, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Get default validators based on context."""
        # Base validators
        validators = ["readability", "structure"]
        
        if context:
            # Add context-specific validators
            material_type = context.get("material_type")
            if material_type == "quiz":
                validators.append("quiz_validator")
            elif material_type == "worksheet":
                validators.append("worksheet_validator")
            
            # Teaching style specific
            teaching_style = context.get("teaching_style")
            if teaching_style == "constructivist":
                validators.append("open_ended_validator")
        
        return validators
    
    def _group_by_severity(
        self, 
        issues: List[ValidationIssue]
    ) -> Dict[str, int]:
        """Group issues by severity."""
        counts = {"error": 0, "warning": 0, "info": 0}
        for issue in issues:
            counts[issue.severity.value] += 1
        return counts
```

### RemediationManager

```python
class RemediationManager:
    """Manages remediation pipeline."""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
    
    async def remediate(
        self,
        content: str,
        issues: List[ValidationIssue],
        remediators: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply remediators to fix issues.
        
        Args:
            content: Content to remediate
            issues: Validation issues to fix
            remediators: List of remediator names
            context: Remediation context
        
        Returns:
            Remediation results
        """
        if remediators is None:
            remediators = self.suggest_remediators(issues)
        
        current_content = content
        all_changes = []
        applied_remediators = []
        
        for remediator_name in remediators:
            remediator = self.registry.get_remediator(remediator_name)
            if not remediator:
                logger.warning(f"Remediator '{remediator_name}' not found")
                continue
            
            # Filter issues this remediator can handle
            applicable_issues = [
                issue for issue in issues 
                if remediator.can_handle(issue)
            ]
            
            if not applicable_issues:
                continue
            
            try:
                result = await remediator.remediate(
                    current_content, 
                    applicable_issues, 
                    context
                )
                
                if result.success:
                    current_content = result.content
                    all_changes.extend(result.changes_made)
                    applied_remediators.append({
                        "name": remediator_name,
                        "changes": len(result.changes_made),
                        "metadata": result.metadata
                    })
                else:
                    logger.warning(
                        f"Remediator '{remediator_name}' failed: {result.error}"
                    )
            
            except Exception as e:
                logger.error(f"Remediator '{remediator_name}' error: {e}")
        
        return {
            "original_content": content,
            "remediated_content": current_content,
            "changes_made": all_changes,
            "applied_remediators": applied_remediators,
            "content_changed": content != current_content
        }
    
    def suggest_remediators(
        self, 
        issues: List[ValidationIssue]
    ) -> List[str]:
        """
        Suggest remediators based on issues.
        
        Args:
            issues: List of validation issues
        
        Returns:
            Ordered list of suggested remediator names
        """
        suggestions = []
        issue_types = {issue.type for issue in issues}
        
        # Map issue types to remediators
        remediator_map = {
            "long_sentence": "sentence_splitter",
            "passive_voice": "active_voice_converter",
            "heading_hierarchy": "heading_hierarchy_fixer",
            "missing_structure": "structure_enhancer",
            "low_readability": "readability_improver"
        }
        
        for issue_type in issue_types:
            if issue_type in remediator_map:
                remediator = remediator_map[issue_type]
                if remediator not in suggestions:
                    suggestions.append(remediator)
        
        return suggestions
```

## Best Practices

### Plugin Development Guidelines

1. **Clear Metadata**
   - Use descriptive names
   - Follow semantic versioning
   - Include comprehensive tags

2. **Error Handling**
   - Never let exceptions escape
   - Log errors appropriately
   - Return partial results when possible

3. **Performance**
   - Use async for I/O operations
   - Cache expensive computations
   - Process in chunks for large content

4. **Configuration**
   - Document all config options
   - Provide sensible defaults
   - Validate configuration

5. **Testing**
   - Unit test all methods
   - Test edge cases
   - Include integration tests

### Example Plugin Test

```python
import pytest
from plugins.validators.custom import URLValidator

@pytest.mark.asyncio
async def test_url_validator():
    validator = URLValidator({
        "require_educational": True
    })
    
    content = """
    Check out this resource: https://example.edu/course
    And this one: https://random-site.com/page
    Invalid URL: htp://broken.com
    """
    
    result = await validator.validate(content)
    
    assert result.score < 100
    assert len(result.issues) == 2
    
    # Check for invalid URL
    invalid_issues = [
        i for i in result.issues 
        if i.type == "invalid_url"
    ]
    assert len(invalid_issues) == 1
    
    # Check for non-educational URL
    edu_issues = [
        i for i in result.issues 
        if i.type == "non_educational_url"
    ]
    assert len(edu_issues) == 1
```