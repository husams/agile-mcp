# Migration Guide: Tool Name Changes

## Overview

This guide covers the breaking changes introduced in version 2.0.0, where all MCP tool names have been updated to remove dots and use underscore-based naming for better protocol compliance and clarity.

## Why This Change?

1. **MCP Protocol Compliance**: Dots in tool names are not valid according to the MCP protocol specification
2. **Improved Clarity**: Underscore-based names are more descriptive and readable
3. **Consistency**: Uniform naming convention across all tools

## Complete Tool Name Mapping

### Epic Management Tools
| Old Name | New Name |
|----------|----------|
| `backlog.createEpic` | `create_epic` |
| `backlog.findEpics` | `find_epics` |
| `backlog.updateEpicStatus` | `update_epic_status` |

### Story Management Tools
| Old Name | New Name |
|----------|----------|
| `backlog.createStory` | `create_story` |
| `backlog.getStory` | `get_story` |
| `backlog.updateStory` | `update_story` |
| `backlog.updateStoryStatus` | `update_story_status` |
| `backlog.executeStoryDodChecklist` | `execute_story_dod_checklist` |
| `backlog.getStorySection` | `get_story_section` |
| `backlog.addDependency` | `add_story_dependency` |
| `backlog.getNextReadyStory` | `get_next_ready_story` |

### Task Management Tools
| Old Name | New Name |
|----------|----------|
| `tasks.addToStory` | `add_task_to_story` |
| `tasks.updateTaskStatus` | `update_task_status` |
| `tasks.updateTaskDescription` | `update_task_description` |
| `tasks.reorderTasks` | `reorder_story_tasks` |

### Acceptance Criteria Tools
| Old Name | New Name |
|----------|----------|
| `acceptanceCriteria.addToStory` | `add_acceptance_criteria_to_story` |
| `acceptanceCriteria.updateStatus` | `update_acceptance_criteria_status` |
| `acceptanceCriteria.updateDescription` | `update_acceptance_criteria_description` |
| `acceptanceCriteria.reorderCriteria` | `reorder_acceptance_criteria` |

### Comment Management Tools
| Old Name | New Name |
|----------|----------|
| `story.addComment` | `add_story_comment` |
| `story.getComments` | `get_story_comments` |
| `story.updateComment` | `update_story_comment` |
| `story.deleteComment` | `delete_story_comment` |
| `comments.addToStory` | `add_comment_to_story` |

### Artifact Management Tools
| Old Name | New Name |
|----------|----------|
| `artifacts.linkToStory` | `link_artifact_to_story` |
| `artifacts.listForStory` | `list_story_artifacts` |

### Document Management Tools
| Old Name | New Name |
|----------|----------|
| `documents.ingest` | `ingest_document` |
| `documents.getSection` | `get_document_section` |

### Project Management Tools
| Old Name | New Name |
|----------|----------|
| `projects.create` | `create_project` |
| `projects.find` | `list_projects` |

## Migration Examples

### Before (v1.x)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "backlog.createEpic",
    "arguments": {
      "title": "User Authentication System",
      "description": "Implement complete user auth flow",
      "project_id": "proj-123"
    }
  }
}
```

### After (v2.0+)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_epic",
    "arguments": {
      "title": "User Authentication System",
      "description": "Implement complete user auth flow",
      "project_id": "proj-123"
    }
  }
}
```

## Migration Checklist

- [ ] **Update tool calls** in your MCP client code to use new names
- [ ] **Update any hardcoded tool names** in configuration files
- [ ] **Review integration tests** that reference tool names
- [ ] **Update documentation** that mentions specific tool names
- [ ] **Verify tool discovery** works with new names in your MCP client
- [ ] **Test end-to-end workflows** to ensure no missed references

## Migration Scripts

### Python MCP Client
```python
# Tool name mapping for automated migration
TOOL_NAME_MAPPING = {
    "backlog.createEpic": "create_epic",
    "backlog.findEpics": "find_epics",
    "backlog.updateEpicStatus": "update_epic_status",
    "backlog.createStory": "create_story",
    "backlog.getStory": "get_story",
    "backlog.updateStory": "update_story",
    "backlog.updateStoryStatus": "update_story_status",
    "backlog.executeStoryDodChecklist": "execute_story_dod_checklist",
    "backlog.getStorySection": "get_story_section",
    "backlog.addDependency": "add_story_dependency",
    "backlog.getNextReadyStory": "get_next_ready_story",
    "tasks.addToStory": "add_task_to_story",
    "tasks.updateTaskStatus": "update_task_status",
    "tasks.updateTaskDescription": "update_task_description",
    "tasks.reorderTasks": "reorder_story_tasks",
    "acceptanceCriteria.addToStory": "add_acceptance_criteria_to_story",
    "acceptanceCriteria.updateStatus": "update_acceptance_criteria_status",
    "acceptanceCriteria.updateDescription": "update_acceptance_criteria_description",
    "acceptanceCriteria.reorderCriteria": "reorder_acceptance_criteria",
    "story.addComment": "add_story_comment",
    "story.getComments": "get_story_comments",
    "story.updateComment": "update_story_comment",
    "story.deleteComment": "delete_story_comment",
    "comments.addToStory": "add_comment_to_story",
    "artifacts.linkToStory": "link_artifact_to_story",
    "artifacts.listForStory": "list_story_artifacts",
    "documents.ingest": "ingest_document",
    "documents.getSection": "get_document_section",
    "projects.create": "create_project",
    "projects.find": "list_projects"
}

def migrate_tool_name(old_name: str) -> str:
    """Convert old tool name to new format."""
    return TOOL_NAME_MAPPING.get(old_name, old_name)
```

### JavaScript/TypeScript
```typescript
const TOOL_NAME_MAPPING: Record<string, string> = {
  "backlog.createEpic": "create_epic",
  "backlog.findEpics": "find_epics",
  "backlog.updateEpicStatus": "update_epic_status",
  // ... add all mappings
};

function migrateToolName(oldName: string): string {
  return TOOL_NAME_MAPPING[oldName] || oldName;
}
```

## Breaking Change Timeline

- **v1.x**: Legacy dotted tool names (deprecated)
- **v2.0.0**: New underscore-based tool names (current)
- **Future**: Legacy names will not be supported

## Support

If you encounter issues during migration:

1. **Check the mapping table** above for correct new names
2. **Review your MCP client** tool discovery implementation
3. **Test with individual tools** before full migration
4. **File issues** in our GitHub repository if you find problems

For questions about specific migration scenarios, please open an issue with:
- Your current tool usage patterns
- MCP client type and version
- Specific error messages encountered

## Functional Changes

**Important**: Only tool names have changed. All functionality, parameters, return values, and behaviors remain exactly the same. This is purely a naming/interface change for protocol compliance.
