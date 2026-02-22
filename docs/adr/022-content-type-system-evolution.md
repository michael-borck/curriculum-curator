# 22. Content Type System Evolution

Date: 2025-12-03

## Status

Accepted

## Context

The Curriculum Curator manages various types of educational content, from traditional lectures to modern multimedia resources. The initial content type system was limited and didn't adequately support the breadth of materials that educators work with, particularly when integrating with academic search systems.

### Initial Limitations
The original content type system included basic types but had several issues:

1. **"Reading" was too narrow**: Only covered traditional text-based reading materials
2. **Missing multimedia support**: No explicit support for videos, podcasts, or interactive media
3. **Limited assessment types**: Only basic quiz support
4. **No tutorial content**: Missing step-by-step instructional guides
5. **Academic search mismatch**: Search results include videos and multimedia that couldn't be properly categorized

### Requirements for Evolution
- **Multimedia content support**: Videos, podcasts, and interactive media from academic sources
- **Comprehensive assessment types**: Support for various testing and evaluation methods
- **Academic resource categorization**: Better alignment with search result types
- **Workflow flexibility**: Support for different pedagogical approaches
- **Future extensibility**: Easy addition of new content types

## Decision

Evolve the content type system to be more comprehensive and multimedia-aware:

### Core Content Types
- **Administrative**: `syllabus`, `schedule`
- **Instructional Delivery**: `lecture`, `module`, `tutorial`
- **Learning Resources**: `resource`, `video`, `podcast` (renamed from "reading")
- **Practice & Engagement**: `worksheet`, `faq`, `interactive`, `case_study`
- **Assessment**: `quiz`, `short_answer`, `matching`, `assessment`
- **Projects & Assignments**: `assignment`, `project`

### Key Changes Made

#### 1. Renamed "Reading" → "Resource"
- **Old**: `reading` - implied only text-based materials
- **New**: `resource` - encompasses articles, websites, datasets, multimedia
- **Rationale**: Better reflects academic search results and modern learning materials

#### 2. Added Multimedia Types
- **Video**: Explicit support for video content (lectures, tutorials, demonstrations)
- **Podcast**: Audio content support (interviews, discussions, lectures)
- **Tutorial**: Step-by-step instructional guides and walkthroughs

#### 3. Enhanced Assessment Types
- **Short Answer**: Open-ended written responses
- **Matching**: Matching exercises and associations
- **Assessment**: Formal assessments and tests (broader than just quizzes)

#### 4. Improved Categorization
- **Interactive**: Interactive elements and simulations
- **Case Study**: Real-world case analysis and studies
- **FAQ**: Frequently asked questions and Q&A formats

## Consequences

### Positive
- **Better Search Integration**: Academic search results can be properly categorized
- **Multimedia Support**: Videos and podcasts from research can be saved and referenced
- **Assessment Flexibility**: More assessment types support diverse evaluation methods
- **User Experience**: Clearer content type selection and organization
- **Future-Proof**: Extensible system for new content types

### Negative
- **Migration Complexity**: Existing content needs type updates
- **UI Complexity**: More content types in selection interfaces
- **Training Requirements**: Educators need to understand new type distinctions

### Neutral
- **Database Impact**: Content type field remains a string, no schema changes needed
- **Backward Compatibility**: Old types can be mapped to new equivalents
- **API Compatibility**: Existing endpoints work with new types

## Alternatives Considered

### Keep Original Types
- **Rejected**: Too limiting for modern educational content and search integration
- **Why**: Would prevent proper categorization of multimedia and diverse assessment types

### Hierarchical Type System
- **Rejected**: Would add complexity without clear benefits
- **Why**: Flat type system is simpler to understand and implement

### User-Defined Types
- **Rejected**: Would lead to inconsistency and maintenance issues
- **Why**: Standardized types ensure consistency and interoperability

## Implementation Notes

### Database Migration
- Content type field remains `String(20)` - no schema changes required
- Existing content automatically works with new type names
- Type validation updated in both backend and frontend

### Frontend Updates
- Updated `ContentType` TypeScript type definition
- Modified content type labels and icons in UI components
- Updated content creation and editing interfaces

### Backward Compatibility
- Old type names gracefully handled (e.g., "reading" → "resource")
- API responses include both old and new type names during transition
- Import/export functions handle type mapping

### Content Type Guidelines
- **Resource**: Any learning material that can be consumed (read, watched, listened to)
- **Video**: Moving visual content with audio
- **Podcast**: Audio-only content
- **Tutorial**: Step-by-step instructional content
- **Interactive**: Content requiring user interaction
- **Assessment**: Content designed to evaluate learning

## References

- [ADR-021: Web Search and Citation Integration](021-web-search-citation-integration.md) - Search integration drove content type expansion
- [ADR-016: React TypeScript Frontend](016-react-typescript-frontend.md) - Frontend type system updates
- [ADR-017: FastAPI REST Backend](017-fastapi-rest-backend.md) - Backend API compatibility</content>
<parameter name="filePath">docs/adr/022-content-type-system-evolution.md