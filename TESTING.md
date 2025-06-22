# Curriculum Curator - Testing Guide

## Overview

This document provides comprehensive testing scenarios for the Curriculum Curator application. Use this to systematically verify functionality and track implementation progress.

**Last Updated:** 2025-01-19  
**Current Status:** Phase 1 - Comprehensive Testing & Documentation

## Test Environment Setup

### Prerequisites
- **Node.js 18+** with npm
- **Rust 1.70+** with cargo  
- **Tauri Dependencies** installed
- **Ollama** (for LLM testing): `ollama serve` + `ollama pull llama3.2:3b`

### Running Tests
```bash
# Start development environment
npm run dev

# Access application at http://localhost:5173/
# Or in Tauri desktop app window
```

## Test Categories

### 🎯 **UI/UX Testing** (Expected: PASS)

#### Navigation & Layout
- [ ] **App Mode Switching**
  - Switch between Wizard and Expert modes
  - Verify UI layout changes appropriately
  - Check responsive design on different window sizes
  
- [ ] **Header Navigation** 
  - All buttons in header toolbar functional
  - Settings panel opens/closes correctly
  - Preview panel toggles on/off
  - Session dropdown shows/hides

- [ ] **Wizard Mode Workflow**
  - Step progression works (1 of 6 → 2 of 6, etc.)
  - Form validation shows appropriate messages
  - Progress indicator updates correctly
  - Back/Next navigation functional

- [ ] **Expert Mode Interface**
  - Tab switching (Content Planner, Workflow, Batch)
  - Form controls respond to user input
  - Advanced options expand/collapse
  - Workflow step controls visible

#### Form Interactions
- [ ] **Input Validation**
  - Required fields show error states
  - Character limits enforced
  - Email format validation (if applicable)
  - Number input constraints work

- [ ] **Settings Management**
  - Settings panel opens without errors
  - User preferences can be modified
  - Changes persist after closing/reopening
  - Default values load correctly

### 🗄️ **Database Operations** (Expected: PASS)

#### Session Management
- [ ] **Create Sessions**
  - New sessions can be created with names
  - Session IDs are generated uniquely
  - Sessions appear in session browser
  
- [ ] **Save/Load Sessions**
  - Session data persists between app restarts
  - Session metadata (name, created date) accurate
  - Content associated with sessions correctly
  
- [ ] **Session Browser**
  - Sessions list displays correctly
  - Session selection switches active session
  - Session deletion removes from database
  - Search/filter functionality works

#### Data Persistence
- [ ] **Settings Persistence**
  - User preferences survive app restart
  - Content defaults maintained
  - UI preferences restored correctly

- [ ] **Content Storage**
  - Generated content saved to database
  - Content retrieval displays correctly
  - Content versioning (if implemented)

### 🤖 **LLM Integration** (Expected: PARTIAL)

#### Ollama Integration (Should PASS)
- [ ] **Connection Test**
  - App can connect to local Ollama
  - Model list retrieval works
  - Health check passes

- [ ] **Content Generation**
  - Basic prompt → response cycle works
  - Content appears in UI appropriately
  - Error handling for connection failures
  - Progress indicators during generation

#### External Providers (Expected: FAIL - Placeholder)
- [ ] **OpenAI Integration**
  - API key configuration
  - Model selection
  - Content generation
  - Error handling

- [ ] **Claude Integration**  
  - API key configuration
  - Model selection
  - Content generation
  - Error handling

- [ ] **Gemini Integration**
  - API key configuration
  - Model selection
  - Streaming support
  - Error handling

### 📁 **File Operations** (Expected: PARTIAL)

#### Import/Export
- [ ] **File Import**
  - File selection dialog opens
  - Supported formats recognized
  - Content parsed correctly
  - Error handling for invalid files

- [ ] **Export Functionality**
  - PowerPoint export works (Should PASS)
  - Markdown export (Needs testing)
  - PDF export (Needs testing)
  - Custom format options

- [ ] **Session Backup/Restore**
  - Manual backup creation
  - Backup file format valid
  - Restore from backup file
  - Backup management interface

### ⚙️ **Advanced Features** (Expected: FAIL - Placeholder)

#### Expert Mode Workflows
- [ ] **Step Execution**
  - "Run Step" buttons functional
  - Step progress tracking
  - Step result display
  - Error handling per step

#### Batch Processing
- [ ] **Batch Job Creation**
  - Multiple content generation
  - Job queue management
  - Progress monitoring
  - Completion notifications

#### Maintenance Operations
- [ ] **Storage Management**
  - Disk usage calculation
  - Content optimization
  - Duplicate detection
  - Cleanup operations

## Expected Test Results Matrix

| Feature Category | Current Status | Target Status |
|------------------|---------------|---------------|
| UI/UX Testing | ✅ PASS | ✅ PASS |
| Database Operations | ✅ PASS | ✅ PASS |
| Ollama LLM | ⚠️ PARTIAL | ✅ PASS |
| External LLMs | ❌ FAIL | ✅ PASS |
| Basic File Ops | ⚠️ PARTIAL | ✅ PASS |
| Expert Workflows | ❌ FAIL | ✅ PASS |
| Batch Processing | ❌ FAIL | ✅ PASS |
| Maintenance | ❌ FAIL | ✅ PASS |

## Test Execution Instructions

### 1. Run UI/UX Tests
Start with comprehensive UI testing to ensure all interfaces work:
```bash
# Test all navigation, forms, and layout changes
# Document any broken UI elements
```

### 2. Test Database Operations
Verify data persistence and session management:
```bash
# Create test sessions, restart app, verify persistence
# Test session browser and selection
```

### 3. Test LLM Integration
Start with Ollama, then external providers:
```bash
# Ensure Ollama is running: ollama serve
# Test content generation with different prompts
```

### 4. Test File Operations
Verify import/export and backup functionality:
```bash
# Test with sample files
# Verify export formats work correctly
```

### 5. Document Results
Update this file with actual test results:
- ✅ PASS: Works as expected
- ⚠️ PARTIAL: Works with limitations  
- ❌ FAIL: Broken or not implemented
- 🚧 BLOCKED: Cannot test due to dependencies

## Known Issues

### Console Errors (To Fix in Phase 1)
- `backupService` state not managed - needs Tauri service registration
- Missing API endpoints for backup operations
- Placeholder service calls returning errors

### Placeholder Functionality
- Expert Mode workflow steps are UI-only
- Batch processing has no backend implementation
- Advanced export formats are stubs
- Maintenance operations return mock data

## Next Steps

1. **Phase 1**: Complete systematic testing and document all results
2. **Phase 2**: Implement core LLM provider integrations
3. **Phase 3**: Add advanced features and polish

---

*Update this document as features are implemented and tested.*