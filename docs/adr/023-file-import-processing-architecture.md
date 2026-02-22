# 23. File Import and Processing Architecture

Date: 2025-12-03

## Status

Accepted

## Context

Educators often have existing course materials in various formats (PDF, Word documents, PowerPoint presentations, etc.) that they want to import into the Curriculum Curator. The system needs to:

1. **Support multiple file formats** commonly used in education
2. **Extract text content** from binary formats (PDF, DOCX, PPTX)
3. **Intelligently categorize content** based on file content and naming
4. **Handle bulk imports** (ZIP files with multiple documents)
5. **Detect organizational structure** (weeks, modules, content types)
6. **Maintain content quality** during format conversion

### Technical Challenges
- **Format diversity**: Academic materials come in many formats
- **Content extraction**: Binary formats need specialized libraries
- **Content intelligence**: Automatic categorization and organization
- **Performance**: Large file processing without blocking the UI
- **Error handling**: Graceful degradation when libraries are missing
- **Security**: Safe processing of uploaded files

## Decision

Implement a comprehensive **File Import and Processing Architecture** with the following components:

### 1. Multi-Format Support
- **Document formats**: PDF, DOCX, PPTX, MD, TXT, HTML
- **Archive formats**: ZIP files with multiple documents
- **Optional dependencies**: Libraries loaded dynamically with fallbacks

### 2. Intelligent Content Processing
- **Content type detection**: Regex patterns for automatic categorization
- **Week detection**: Filename patterns (Week_01, Lecture_1, etc.)
- **Metadata extraction**: Title, author, creation date from file properties
- **Content cleaning**: Remove formatting artifacts and normalize text

### 3. Bulk Import Capabilities
- **ZIP processing**: Extract and process multiple files
- **Structure analysis**: Detect folder organization and naming patterns
- **Batch operations**: Import multiple files with consistent categorization

### 4. Error Handling and Resilience
- **Graceful degradation**: Continue processing when optional libraries missing
- **Validation**: File size limits, type checking, content validation
- **Progress tracking**: Async processing with status updates

## Consequences

### Positive
- **Workflow integration**: Educators can import existing materials easily
- **Format compatibility**: Support for industry-standard document formats
- **Intelligence**: Automatic organization reduces manual work
- **Scalability**: Bulk import capabilities for large course migrations
- **Reliability**: Robust error handling and validation

### Negative
- **Dependency complexity**: Multiple optional libraries for different formats
- **Processing overhead**: Content extraction can be resource-intensive
- **Maintenance burden**: Keeping format support current with library updates
- **Security considerations**: File processing introduces security risks

### Neutral
- **Performance impact**: Async processing prevents UI blocking
- **Storage efficiency**: Extracted text reduces storage needs
- **Extensibility**: Easy addition of new format support

## Alternatives Considered

### Cloud Document Conversion Services
- **Rejected**: API costs, privacy concerns, dependency on external services
- **Why**: Self-hosted solution maintains privacy and reduces costs

### Browser-based Processing Only
- **Rejected**: Limited to formats browsers can handle natively
- **Why**: Need support for academic document formats (PDF, DOCX, PPTX)

### Simple Text Extraction Only
- **Rejected**: Would lose formatting and structure information
- **Why**: Content intelligence requires understanding document structure

## Implementation Notes

### Library Dependencies
```python
# Optional dependencies with fallbacks
PyPDF2      # PDF text extraction
python-docx # Word document processing
python-pptx # PowerPoint processing
markdown    # Markdown parsing
```

### Content Type Detection Patterns
- **Lectures**: Keywords like "lecture", "chapter", "module", "learning objectives"
- **Assessments**: "quiz", "test", "exam", "question", "multiple choice"
- **Worksheets**: "worksheet", "exercise", "practice", "homework"
- **Labs**: "laboratory", "experiment", "procedure", "materials"
- **Case Studies**: "case study", "scenario", "analysis", "discussion"

### Week Detection Logic
```python
patterns = [
    r"week[_-](\d+)",     # Week_01, week-1
    r"lecture[_-](\d+)",  # Lecture_1, lecture-01
    r"module[_-](\d+)",   # Module_1
    r"session[_-](\d+)",  # Session_1
    r"topic[_-](\d+)",    # Topic_1
]
```

### Security Measures
- **File type validation**: Check MIME types against allowed formats
- **Size limits**: Maximum file sizes to prevent abuse
- **Content scanning**: Basic checks for malicious content
- **Sandboxing**: Process files in isolated environment

### Performance Optimizations
- **Async processing**: Non-blocking file processing
- **Streaming**: Process large files without loading entirely in memory
- **Caching**: Cache extracted content to avoid reprocessing
- **Progress callbacks**: Real-time updates during bulk imports

## References

- [ADR-022: Content Type System Evolution](022-content-type-system-evolution.md) - Content types drive import categorization
- [ADR-017: FastAPI REST Backend](017-fastapi-rest-backend.md) - API endpoints for file upload
- [ADR-016: React TypeScript Frontend](016-react-typescript-frontend.md) - Frontend upload interfaces</content>
<parameter name="filePath">docs/adr/023-file-import-processing-architecture.md