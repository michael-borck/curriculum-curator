# ADR-0012: Framework Migration from FastHTML to NiceGUI

**Date**: 2025-08-03  
**Status**: Accepted  
**Deciders**: Development Team  
**Technical Story**: Framework selection for improved development velocity and user experience

## Context

The Curriculum Curator project was implemented using FastHTML framework, but several critical issues have emerged that significantly impact development velocity and user experience:

### Current FastHTML Implementation Issues

1. **Non-functional LLM Integration**: Despite significant development effort, the LLM connectivity remains broken with placeholder implementations throughout the codebase
2. **UI/UX Inconsistencies**: Constant wrestling with HTML/CSS styling, layout problems, and poor responsive design
3. **Development Velocity**: Slow progress due to framework limitations and manual styling requirements
4. **Technical Debt**: Extensive placeholder code and incomplete implementations across core features
5. **User Experience**: Poor interface consistency, layout issues (e.g., unwanted page titles), and suboptimal mobile support

### Framework Evaluation Context

The project requires:
- Rapid development of professional UI components
- Real-time user interface updates
- Consistent styling and responsive design
- Working LLM integration with progress indicators
- Admin dashboards with tabbed interfaces
- File upload with progress tracking
- Form validation and user feedback

## Decision

We will migrate from FastHTML to NiceGUI framework and start with a fresh implementation.

### Migration Approach: Fresh Start

Rather than attempting to port the existing incomplete FastHTML codebase, we will:

1. **Archive existing implementation** to `python-fasthtml` git branch and reference-implementations directory
2. **Start fresh** with NiceGUI while preserving:
   - Database schema and business logic concepts
   - Authentication patterns and security measures
   - Plugin system architecture
   - Teaching philosophy framework
   - All documentation and ADRs
3. **Focus on working functionality** over preserving incomplete code

## Decision Drivers

### Technical Drivers

- **Built-in UI Components**: NiceGUI provides professional Material Design components out of the box
- **Real-time Updates**: WebSocket-based architecture for immediate UI synchronization  
- **Framework Maturity**: Built on proven FastAPI foundation with established patterns
- **Development Speed**: Declarative UI components eliminate manual HTML/CSS work
- **Better Mobile Support**: Responsive design with Quasar/Vue components

### User Experience Drivers

- **Professional Interface**: Consistent Material Design eliminates styling inconsistencies
- **Interactive Elements**: Built-in progress indicators, dialogs, and notifications
- **Real-time Feedback**: Live updates for long-running operations (LLM generation)
- **Mobile Responsiveness**: Better mobile experience without custom CSS

### Development Process Drivers

- **Faster Iteration**: Component-based development with instant feedback
- **Less Debugging**: Framework handles styling and layout consistency
- **Better Testing**: NiceGUI testing framework for UI validation
- **Cleaner Code**: Less boilerplate HTML/CSS, more focus on business logic

## Consequences

### Positive

- **Immediate working LLM integration**: Start with functional foundations
- **Professional UI/UX**: Material Design components provide consistent experience
- **Faster development velocity**: Built-in components reduce development time
- **Better maintainability**: Cleaner architecture without technical debt
- **Improved testing**: Structured UI testing with NiceGUI test framework
- **Real-time features**: WebSocket updates for progress tracking and live data

### Negative

- **Development time investment**: 4-6 weeks for complete rewrite
- **Learning curve**: Team needs to learn NiceGUI patterns and components
- **Framework dependency**: Less control over HTML/CSS compared to FastHTML
- **Migration effort**: Need to rebuild all UI components and interactions

### Neutral

- **Business logic preservation**: Core concepts and patterns carry forward
- **Database compatibility**: Schema and data remain unchanged
- **Documentation relevance**: Most architectural decisions still apply
- **Feature parity timeline**: All planned features achievable within migration period

## Implementation Plan

### Phase 1: Foundation (Week 1)
- Archive FastHTML implementation to reference branch
- Set up NiceGUI project structure and dependencies
- Implement authentication and user management
- Create basic admin interface with working LLM integration

### Phase 2: Core Features (Weeks 2-3)  
- Build course management workflows
- Implement wizard and expert modes
- Add file upload and processing
- Integrate teaching philosophy system

### Phase 3: Advanced Features (Weeks 4-5)
- Plugin system integration
- Content enhancement and analysis
- Export functionality and reporting
- Testing and documentation updates

### Success Criteria

- ✅ Working LLM integration with all providers
- ✅ Professional, consistent UI/UX across all interfaces
- ✅ Complete feature parity with planned functionality
- ✅ Improved mobile responsiveness
- ✅ Real-time progress tracking and updates
- ✅ Comprehensive testing coverage

## Alternatives Considered

### Alternative 1: Fix FastHTML Implementation
**Rejected**: Too much technical debt and fundamental UI/UX issues. Estimated 8-12 weeks to resolve all issues vs 4-6 weeks for fresh start.

### Alternative 2: Gradual Migration
**Rejected**: Would require maintaining two codebases and complex integration between frameworks.

### Alternative 3: Different Framework (Streamlit, Gradio)
**Rejected**: Too specialized for data applications, insufficient customization for course management workflows.

### Alternative 4: Return to Tauri/Desktop
**Rejected**: Web-based deployment is preferred for institutional access and updates.

## Related Decisions

- **ADR-0002**: FastHTML Web Framework (superseded by this decision)
- **ADR-0003**: Plugin Architecture (preserved in new implementation)
- **ADR-0004**: Teaching Philosophy System (preserved in new implementation)
- **ADR-0005**: Hybrid Storage Approach (preserved in new implementation)

## References

- [NiceGUI Documentation](https://nicegui.io/)
- [FastHTML vs NiceGUI Comparison Research](../development/framework-comparison.md)
- [Migration Plan](../development/NICEGUI_MIGRATION_PLAN.md)
- [FastHTML Implementation Archive](../../reference-implementations/python-fasthtml-version/)

## Notes

This decision represents a significant but necessary pivot to ensure project success. The FastHTML implementation served as valuable learning experience and proof-of-concept for business logic and architecture patterns. The fresh start approach, while requiring initial investment, provides the best path forward for a professional, maintainable, and user-friendly application.

The archived FastHTML implementation will remain available for reference and pattern extraction during the NiceGUI development process.