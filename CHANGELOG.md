# Changelog

All notable changes to the Agile Management MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-08-01

### 🚨 BREAKING CHANGES

#### Tool Name Modernization
All MCP tool names have been updated to remove dots and use underscore-based naming for better protocol compliance and clarity. **This is a major breaking change that requires client updates.**

**All clients must update their tool references to use the new names.**

### Changed

#### Epic Management Tools
- `backlog.createEpic` → `create_epic`
- `backlog.findEpics` → `find_epics`
- `backlog.updateEpicStatus` → `update_epic_status`

#### Story Management Tools
- `backlog.createStory` → `create_story`
- `backlog.getStory` → `get_story`
- `backlog.updateStory` → `update_story`
- `backlog.updateStoryStatus` → `update_story_status`
- `backlog.executeStoryDodChecklist` → `execute_story_dod_checklist`
- `backlog.getStorySection` → `get_story_section`
- `backlog.addDependency` → `add_story_dependency`
- `backlog.getNextReadyStory` → `get_next_ready_story`

#### Task Management Tools
- `tasks.addToStory` → `add_task_to_story`
- `tasks.updateTaskStatus` → `update_task_status`
- `tasks.updateTaskDescription` → `update_task_description`
- `tasks.reorderTasks` → `reorder_story_tasks`

#### Acceptance Criteria Tools
- `acceptanceCriteria.addToStory` → `add_acceptance_criteria_to_story`
- `acceptanceCriteria.updateStatus` → `update_acceptance_criteria_status`
- `acceptanceCriteria.updateDescription` → `update_acceptance_criteria_description`
- `acceptanceCriteria.reorderCriteria` → `reorder_acceptance_criteria`

#### Comment Management Tools
- `story.addComment` → `add_story_comment`
- `story.getComments` → `get_story_comments`
- `story.updateComment` → `update_story_comment`
- `story.deleteComment` → `delete_story_comment`
- `comments.addToStory` → `add_comment_to_story`

#### Artifact Management Tools
- `artifacts.linkToStory` → `link_artifact_to_story`
- `artifacts.listForStory` → `list_story_artifacts`

#### Document Management Tools
- `documents.ingest` → `ingest_document`
- `documents.getSection` → `get_document_section`

#### Project Management Tools
- `projects.create` → `create_project`
- `projects.find` → `list_projects`

### Added
- **Migration Guide**: Comprehensive MIGRATION-GUIDE.md with complete tool name mappings and client migration examples
- **Version Management**: Added `__version__.py` for consistent version tracking
- **Breaking Change Documentation**: Clear documentation of all breaking changes

### Technical
- Updated all API endpoint decorators to use new tool names
- Updated all test files to reference new tool names
- Updated logging contexts to use new tool names
- Updated tools documentation with new naming
- Maintained 100% backward compatibility for all functionality (parameters, return values, behavior)
- All 681 unit tests and E2E tests pass with new tool names
- Pre-commit hooks updated and passing

### Migration
- See [MIGRATION-GUIDE.md](./MIGRATION-GUIDE.md) for complete migration instructions
- All functionality remains identical - only tool names have changed
- No changes to parameters, return values, or behavior
- Use provided mapping tables and scripts for automated migration

## [1.x.x] - Previous Versions

Previous versions used dotted tool names (e.g., `backlog.createEpic`) which have been deprecated in favor of underscore-based names for better MCP protocol compliance.

### Legacy Tool Names (Deprecated)
All tools with dotted names (`backlog.*`, `story.*`, `tasks.*`, `acceptanceCriteria.*`, `comments.*`, `artifacts.*`, `documents.*`, `projects.*`) are no longer supported as of version 2.0.0.

---

## Migration Support

For assistance with migrating from v1.x to v2.0:
1. Review the [Migration Guide](./MIGRATION-GUIDE.md)
2. Use the provided tool name mapping tables
3. Test individual tools before full migration
4. Open issues for migration-specific questions

## Version Support Policy

- **v2.x**: Current version with underscore-based tool names
- **v1.x**: Legacy version with dotted tool names (deprecated)

Only v2.x will receive ongoing support and updates.
