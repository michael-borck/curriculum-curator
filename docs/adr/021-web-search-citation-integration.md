# 21. Web Search and Citation Integration

Date: 2025-12-03

## Status

Accepted (search provider strategy superseded by [ADR-039](039-tiered-research-architecture.md); citation management and research source library unchanged)

## Context

The Curriculum Curator enables educators to create course content, but often requires research and citation of academic sources. Educators currently need to:

1. **Manually search** for academic sources using external tools (Google Scholar, library databases, etc.)
2. **Switch contexts** between research tools and content creation
3. **Manually format citations** in various academic styles
4. **Track source usage** and maintain reference lists
5. **Synthesize information** from multiple sources

This creates friction in the content creation workflow and increases the cognitive load on educators. The system needs to integrate academic search and citation management directly into the content creation process.

### Requirements
- **Academic-focused search** with quality filtering
- **Citation management** in multiple academic styles (APA7, Harvard, MLA, etc.)
- **Source storage and organization** with metadata
- **Citation integration** into generated content
- **Multi-source synthesis** for comprehensive content creation
- **Privacy and cost considerations** for academic search

## Decision

Implement a comprehensive **Web Search and Citation Management System** with the following components:

### 1. Academic Search Integration
- **SearXNG Integration**: Self-hosted, privacy-focused search engine
- **Academic Source Scoring**: Prioritize .edu, .ac.uk, .gov, arxiv.org sources
- **Content Summarization**: AI-powered summarization for educational purposes
- **Search-and-Summarize Workflow**: Combined search and content extraction

### 2. Citation Management System
- **Research Source Model**: Comprehensive metadata storage (authors, DOI, publication details)
- **Citation Formatting Service**: Support for 6 academic styles (APA7, Harvard, MLA, Chicago, IEEE, Vancouver)
- **In-text and Reference Citations**: Automatic formatting and insertion
- **Source Usage Tracking**: Track which sources are used in which content

### 3. Content Integration
- **Save from Search**: Direct saving of sources from search results
- **Citation Panel**: UI for managing sources and generating citations
- **Multi-source Synthesis**: AI-powered content generation from multiple sources with proper citations
- **Citation Linking**: Track which citations are used in which content pieces

### 4. Technical Architecture
- **RESTful API**: Dedicated `/api/sources` and `/api/search` endpoints
- **Database Tables**: `research_sources` and `content_citations` tables
- **Service Layer**: `CitationService` and `WebSearchService` classes
- **Frontend Components**: `SearchPanel` and `ResearchPanel` components

## Consequences

### Positive
- **Streamlined Workflow**: Educators can research, cite, and create content in one system
- **Academic Quality**: Built-in academic source prioritization and quality filtering
- **Citation Accuracy**: Automated formatting reduces citation errors
- **Source Organization**: Centralized source library with tagging and search
- **AI-Enhanced Research**: Multi-source synthesis capabilities
- **Privacy-Focused**: Self-hosted SearXNG avoids data sharing with commercial search providers

### Negative
- **External Dependency**: Requires SearXNG instance setup and maintenance
- **API Rate Limits**: Search functionality depends on external service availability
- **Citation Complexity**: Supporting multiple citation styles increases code complexity
- **Storage Requirements**: Source metadata and summaries increase database size
- **Learning Curve**: Educators need to learn new citation management interface

### Neutral
- **Cost**: SearXNG is free and self-hosted, no API costs
- **Scalability**: Search results cached for performance
- **Extensibility**: Citation service can support additional styles
- **Integration**: Works with existing LLM content generation

## Alternatives Considered

### Commercial Search APIs (Google, Bing, etc.)
- **Rejected**: Privacy concerns, API costs, commercial data collection policies
- **Why**: Academic context requires privacy and cost predictability

### Browser Extensions (Zotero, Mendeley)
- **Rejected**: Requires context switching and manual data entry
- **Why**: Goal is integrated workflow, not external tool integration

### Citation-only Service (no search)
- **Rejected**: Would still require external search, defeating workflow integration
- **Why**: Complete research-to-citation workflow is the core value proposition

### Built-in Search Engine
- **Rejected**: Would require significant infrastructure and maintenance
- **Why**: SearXNG provides excellent privacy-focused search without custom development

## Implementation Notes

### SearXNG Setup
- Deploy SearXNG on Tailscale network for privacy
- Configure academic source prioritization
- Set up caching for performance
- Monitor rate limits and availability

### Citation Styles
- APA7 as default (most common in education)
- Support additional styles via community contribution
- Citation validation against style guides
- Handle edge cases (multiple authors, missing data)

### Database Design
- `research_sources` table with comprehensive metadata
- `content_citations` junction table for many-to-many relationships
- JSON fields for flexible author and tag storage
- Indexing on user_id and unit_id for performance

### API Design
- RESTful endpoints following existing patterns
- Proper error handling for external service failures
- Pagination for large source libraries
- Authentication required for all operations

## References

- [SearXNG Documentation](https://docs.searxng.org/)
- [Citation Style Language](https://citationstyles.org/)
- [ADR 0014: LiteLLM Unified LLM Abstraction](014-litellm-unified-llm-abstraction.md)
- [ADR 0016: React TypeScript Frontend](016-react-typescript-frontend.md)
- [ADR 0017: FastAPI REST Backend](017-fastapi-rest-backend.md)</content>
<parameter name="filePath">docs/adr/021-web-search-citation-integration.md