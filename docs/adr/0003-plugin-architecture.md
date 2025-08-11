# 3. Plugin Architecture for Validators and Remediators

Date: 2025-08-01

## Status

Accepted

## Context

The Python-Electron version had a comprehensive plugin system for validators and remediators. While that implementation was overly complex for our needs, the core concept of modular validators and remediators is valuable. We need a plugin system that:
- Allows easy addition of new validators and remediators
- Supports both built-in and potentially external plugins
- Maintains clear separation of concerns
- Is simple to understand and use

## Decision

We will implement a simplified plugin architecture with:

1. **Base Classes**: Abstract base classes for validators and remediators
2. **Auto-discovery**: Automatic plugin discovery in designated directories
3. **Registry Pattern**: Central registry for managing plugins
4. **Metadata**: Each plugin declares its metadata (name, version, description)
5. **Simple Interface**: Clear, minimal interfaces for plugin implementation

The architecture follows these principles:
- Validators only detect issues, they don't modify content
- Remediators fix specific types of issues
- Clear separation between detection and remediation
- Configuration-driven plugin selection

## Consequences

### Positive
- Easy to add new validators and remediators
- Clear separation of concerns
- Power users can extend functionality
- Modular testing of individual plugins
- Flexible validation and remediation strategies

### Negative
- Additional complexity compared to hardcoded validators
- Need to maintain plugin interfaces
- Performance overhead of dynamic loading
- More complex error handling

### Neutral
- Requires documentation for plugin developers
- Need to decide on external plugin support later
- Plugin versioning considerations

## Alternatives Considered

### Hardcoded Validators
- All validation logic built into core
- Rejected as too inflexible for power users

### Full Plugin System with External Loading
- Support for pip-installable plugins
- Rejected as overly complex for initial version

### Function-Based System
- Simple functions instead of classes
- Rejected as it lacks structure for metadata and configuration

## Implementation Notes

```python
# Example validator structure
class ReadabilityValidator(BaseValidator):
    metadata = PluginMetadata(
        name="readability",
        version="1.0.0",
        description="Checks content readability"
    )
    
    async def validate(self, content: str, context: dict) -> ValidationResult:
        # Implementation
        pass
```

- Plugins discovered at startup from `plugins/validators/` and `plugins/remediators/`
- Use async methods for future LLM integration
- Provide helpful base classes with common functionality
- Include example plugins (readability, structure, sentence_splitter)

## References

- [Python-Electron Plugin Design](../../reference-implementations/python-electron-version/docs/adr/0002-validation-remediation-design.md)
- [ADR-0004](0004-teaching-philosophy-system.md) - How teaching styles influence validation