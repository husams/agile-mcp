# Sprint Change Proposal - Epic 6 Implementation Gap & Project Scope Corrections

**Date:** 2025-07-30
**Status:** Approved
**Change Type:** Implementation Gap Resolution & Scope Correction

## Analysis Summary

### Identified Issues

**Primary Issue:** Epic 6 (Agent Workflow & Model Enhancements) incorrectly marked as "Done" when critical functionality is missing, specifically:
- Missing document management tools (`documents.ingest`, `documents.getSection`)
- Missing Project entity implementation
- Incomplete service layer methods (`StoryService.update_story()`)
- Missing MCP tools (`backlog.updateStory`)

**Secondary Issue:** Epic 7 (Role-Based Access Control) is discarded and no longer needed in project scope.

**Root Cause:** Status tracking does not reflect actual implementation state. Epic 6 shows as complete but lacks core requirements per detailed analysis in `docs/missing-functionality.md`.

### Impact Assessment
- **Epic 6 Status:** Partially Complete - data models exist, but service layer and document management tools missing
- **Epic 7 (RBAC):** Removed from project scope entirely
- **Future Epics:** No blocking impact - Epic 6 completion enables planned functionality
- **MVP Scope:** Maintained for Epic 6, reduced by Epic 7 removal
- **Timeline:** Moderate implementation effort for Epic 6 completion

### Path Forward Rationale
**Direct Adjustment approach selected** - implement all missing Epic 6 functionality using existing architectural foundation. Requirements are clearly defined, architecture is sound, and Epic 6 is foundational for agent workflow efficiency.

## Specific Proposed Implementation

### Epic 6 Completion Requirements

**Missing Service Layer Methods:**
- Enhanced `StoryService.create_story()` with structured field support
- New `StoryService.update_story()` method for partial updates
- Repository layer `update_story()` support

**Missing MCP Tools:**
- `backlog.updateStory` tool (completely missing)
- Enhanced `backlog.createStory` with structured fields

**Missing Document Management (Stories 6.1-6.2):**
```sql
PROJECT (id, name, description)
DOCUMENT (id, project_id, title, type)
DOCUMENT_SECTION (id, document_id, title, content)
```

**Missing Project Tools:**
- `projects.create` - Initialize new project
- `projects.find` - List all projects
- `documents.ingest` - Parse and store document sections
- `documents.getSection` - Retrieve specific document section

### Epic 7 Scope Removal

**Action Required:** Remove Epic 7 (Role-Based Access Control) from project documentation:
- Archive Epic 7 PRD files
- Update main PRD to remove Epic 7 references
- Remove Epic 7 from epic list and project roadmap
- Update any architecture references to RBAC functionality

### Implementation Sequence

**Phase 1: Service Layer Completion (Critical)**
1. Enhance `StoryService.create_story()` with structured field support
2. Implement missing `StoryService.update_story()` method
3. Add repository layer `update_story()` support

**Phase 2: Missing MCP Tools (High Priority)**
4. Implement `backlog.updateStory` tool
5. Enhance `backlog.createStory` with structured field parameters

**Phase 3: Document Management (Stories 6.1-6.2)**
6. Implement Project entity and tools (`projects.*`)
7. Implement Document/DocumentSection models and tools (`documents.*`)

**Phase 4: Integration Testing (Critical)**
8. Fix all failing integration tests in `test_story_structured_fields_flow.py`
9. Validate Epic 6 acceptance criteria compliance

## PRD MVP Impact
**Epic 6:** Scope maintained - remains in MVP with corrected "Partially Complete" status
**Epic 7:** Removed from MVP and project scope entirely

## Next Steps

### Immediate Actions (Epic 6 Completion)
1. **Fix Service Layer:** Implement missing `StoryService.update_story()` and enhance `create_story()`
2. **Fix MCP Tools:** Implement `backlog.updateStory` and enhance `backlog.createStory`
3. **Fix Integration Tests:** Resolve 5 failing tests in `test_story_structured_fields_flow.py`

### Documentation Updates (Epic 7 Removal)
4. **Archive Epic 7 Files:** Move RBAC documentation to archived folder
5. **Update PRD:** Remove Epic 7 references from main PRD documents
6. **Update Epic Lists:** Remove Epic 7 from project roadmap documentation

### Document Management Implementation
7. **Project Entity:** Implement PROJECT data model and `projects.*` tools
8. **Document Management:** Implement DOCUMENT models and `documents.*` tools

## Success Criteria
- [ ] All 5 failing Epic 6 integration tests pass
- [ ] Epic 6 service layer methods fully implemented
- [ ] Epic 6 MCP tools complete and functional
- [ ] Epic 7 documentation cleanly removed from project
- [ ] Document management capabilities available
- [ ] Epic 6 status correctly reflects "Complete" when all AC met

---
**Approval:** ✅ **Approved** - Ready for implementation
