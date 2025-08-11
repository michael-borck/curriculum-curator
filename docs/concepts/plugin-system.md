# Plugin System

The plugin system provides extensibility for content validation and remediation. It allows power users to add custom validators and remediators without modifying core code.

## Architecture

```
plugins/
├── __init__.py
├── base.py                 # Base classes and interfaces
├── validators/
│   ├── __init__.py
│   ├── base.py            # BaseValidator class
│   ├── quality/
│   │   ├── readability.py
│   │   └── structure.py
│   ├── language/
│   │   └── grammar.py
│   └── alignment/
│       └── objectives.py
└── remediators/
    ├── __init__.py
    ├── base.py            # BaseRemediator class
    ├── autofix/
    │   └── sentence_splitter.py
    └── rewrite/
        └── style_adjuster.py
```

## Core Components

### Base Plugin Class
```python
class BasePlugin(ABC):
    metadata: PluginMetadata = None
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
```

### Plugin Metadata
```python
@dataclass
class PluginMetadata:
    name: str              # Unique identifier
    version: str           # Semantic version
    description: str       # Human-readable description
    author: str           # Plugin author
    category: str         # Plugin category
    tags: List[str]       # Searchable tags
```

### Plugin Registry
- Central registry for all plugins
- Auto-discovery at startup
- Lazy loading for performance
- Type-safe plugin retrieval

## Validators

### Purpose
Validators analyze content and identify issues without modifying it.

### Base Validator
```python
class BaseValidator(BasePlugin):
    @abstractmethod
    async def validate(
        self, 
        content: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate content and return issues."""
        pass
```

### Validation Result
```python
@dataclass
class ValidationResult:
    issues: List[ValidationIssue]
    score: float  # 0-100 quality score
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Validation Issue
```python
@dataclass
class ValidationIssue:
    type: str                    # Issue type identifier
    severity: Severity           # ERROR, WARNING, INFO
    message: str                 # Human-readable message
    line: Optional[int] = None   # Line number if applicable
    column: Optional[int] = None # Column number
    suggestion: Optional[str] = None  # Fix suggestion
```

### Example Validator
```python
class ReadabilityValidator(BaseValidator):
    metadata = PluginMetadata(
        name="readability",
        version="1.0.0",
        description="Checks content readability metrics",
        author="Curriculum Curator Team",
        category="quality",
        tags=["readability", "complexity", "education"]
    )
    
    async def validate(self, content: str, context=None):
        issues = []
        
        # Check Flesch Reading Ease
        score = textstat.flesch_reading_ease(content)
        if score < 30:
            issues.append(ValidationIssue(
                type="low_readability",
                severity=Severity.WARNING,
                message=f"Content is very difficult to read (score: {score})"
            ))
        
        # Check sentence length
        sentences = sent_tokenize(content)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        
        for sentence in long_sentences:
            issues.append(ValidationIssue(
                type="long_sentence",
                severity=Severity.INFO,
                message="Sentence is too long",
                suggestion="Consider breaking into shorter sentences"
            ))
        
        return ValidationResult(
            issues=issues,
            score=max(0, score)
        )
```

## Remediators

### Purpose
Remediators fix issues identified by validators or proactively improve content.

### Base Remediator
```python
class BaseRemediator(BasePlugin):
    @abstractmethod
    async def remediate(
        self,
        content: str,
        issues: Optional[List[ValidationIssue]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RemediationResult:
        """Remediate content based on issues."""
        pass
```

### Remediation Result
```python
@dataclass
class RemediationResult:
    content: str              # Modified content
    changes_made: List[str]   # Description of changes
    success: bool            # Whether remediation succeeded
    error: Optional[str] = None  # Error message if failed
```

### Example Remediator
```python
class SentenceSplitter(BaseRemediator):
    metadata = PluginMetadata(
        name="sentence_splitter",
        version="1.0.0",
        description="Splits long sentences for better readability",
        author="Curriculum Curator Team",
        category="autofix",
        tags=["readability", "sentences"]
    )
    
    async def remediate(self, content: str, issues=None, context=None):
        changes = []
        modified = content
        
        # Find long sentences
        sentences = sent_tokenize(content)
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 25:
                # Simple split at conjunctions
                parts = re.split(r'\s+(and|but|or)\s+', sentence)
                if len(parts) > 1:
                    new_sentences = '. '.join(parts) + '.'
                    modified = modified.replace(sentence, new_sentences)
                    changes.append(f"Split long sentence ({len(words)} words)")
        
        return RemediationResult(
            content=modified,
            changes_made=changes,
            success=True
        )
```

## Plugin Discovery

### Automatic Discovery
```python
def discover_plugins(plugin_type: str) -> int:
    """Discover and register plugins of given type."""
    plugin_dir = Path(__file__).parent / plugin_type
    count = 0
    
    for file in plugin_dir.rglob("*.py"):
        if file.name.startswith("_"):
            continue
            
        module_path = file.relative_to(plugin_dir.parent)
        module_name = str(module_path).replace("/", ".")[:-3]
        
        try:
            module = importlib.import_module(f"plugins.{module_name}")
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BasePlugin):
                    if hasattr(obj, 'metadata') and obj.metadata:
                        register_plugin(obj)
                        count += 1
                        
        except Exception as e:
            logger.error(f"Failed to load plugin {module_name}: {e}")
    
    return count
```

### Manual Registration
```python
# For external plugins
from my_custom_plugin import CustomValidator

registry = PluginRegistry()
registry.register_validator("custom", CustomValidator)
```

## Plugin Manager

### Validation Manager
```python
class ValidationManager:
    async def validate(
        self,
        content: str,
        validators: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run specified validators on content."""
        
        if validators is None:
            validators = self.get_default_validators()
        
        results = []
        for validator_name in validators:
            validator = self.get_validator(validator_name)
            if validator:
                result = await validator.validate(content, context)
                results.append({
                    "validator": validator_name,
                    "result": result
                })
        
        return self.aggregate_results(results)
```

### Remediation Manager
```python
class RemediationManager:
    async def remediate(
        self,
        content: str,
        issues: List[ValidationIssue],
        remediators: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Apply remediators to fix issues."""
        
        if remediators is None:
            remediators = self.suggest_remediators(issues)
        
        current_content = content
        all_changes = []
        
        for remediator_name in remediators:
            remediator = self.get_remediator(remediator_name)
            if remediator:
                result = await remediator.remediate(
                    current_content, issues, context
                )
                if result.success:
                    current_content = result.content
                    all_changes.extend(result.changes_made)
        
        return {
            "final_content": current_content,
            "changes": all_changes,
            "remediators_applied": remediators
        }
```

## Configuration

### Plugin Selection
```yaml
# config.yaml
validation:
  default_validators:
    - readability
    - structure
    - grammar
  
  validator_config:
    readability:
      target_grade_level: 12
      max_sentence_length: 25

remediation:
  auto_remediate: true
  default_remediators:
    - sentence_splitter
    - format_corrector
  
  remediator_config:
    sentence_splitter:
      max_length: 20
      preserve_style: true
```

### Teaching Style Integration
```python
def get_validators_for_style(teaching_style: TeachingStyle) -> List[str]:
    """Get appropriate validators for teaching style."""
    
    if teaching_style == TeachingStyle.TRADITIONAL_LECTURE:
        return ["structure", "completeness", "clarity"]
    elif teaching_style == TeachingStyle.CONSTRUCTIVIST:
        return ["openness", "reflection_prompts", "diversity"]
    # ... etc
```

## Creating Custom Plugins

### Step 1: Create Plugin Class
```python
# plugins/validators/custom/my_validator.py
from plugins.validators.base import BaseValidator, ValidationResult, ValidationIssue
from plugins.base import PluginMetadata

class MyCustomValidator(BaseValidator):
    metadata = PluginMetadata(
        name="my_custom",
        version="1.0.0",
        description="My custom validator",
        author="Your Name",
        category="custom",
        tags=["custom", "example"]
    )
    
    async def validate(self, content: str, context=None):
        issues = []
        
        # Your validation logic here
        if "bad phrase" in content.lower():
            issues.append(ValidationIssue(
                type="inappropriate_phrase",
                severity=Severity.WARNING,
                message="Found inappropriate phrase"
            ))
        
        return ValidationResult(
            issues=issues,
            score=100 - len(issues) * 10
        )
```

### Step 2: Place in Plugin Directory
```
plugins/
└── validators/
    └── custom/
        └── my_validator.py
```

### Step 3: Use in Application
```python
# The plugin is auto-discovered on startup
validators = validation_manager.get_available_validators()
# "my_custom" will be in the list

# Use it
result = await validation_manager.validate(
    content, 
    validators=["my_custom"]
)
```

## Best Practices

### 1. Single Responsibility
- Each plugin should focus on one aspect
- Don't combine validation and remediation
- Keep plugins small and focused

### 2. Configuration
- Make plugins configurable
- Use sensible defaults
- Document configuration options

### 3. Performance
- Use async methods for I/O operations
- Cache expensive computations
- Minimize external dependencies

### 4. Error Handling
- Handle errors gracefully
- Return partial results when possible
- Log errors for debugging

### 5. Testing
- Write unit tests for plugins
- Test with various content types
- Include edge cases

## Future Enhancements

### Planned Features
- Plugin marketplace
- Plugin dependencies
- Plugin composition
- Performance profiling
- A/B testing framework

### External Plugin Support
- pip-installable plugins
- Plugin namespacing
- Version compatibility
- Security sandboxing