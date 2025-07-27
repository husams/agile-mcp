# Sprint Change Proposal: Fix Missing MCP Server Example

## 1. Identified Issue Summary

**Problem:** The sharded architecture document, `docs/architecture/mcp-server-implementation-examples.md`, is incomplete. It is missing the detailed Python code example for implementing MCP Tools, Resources, and Prompts, which is present in the main `docs/architecture.md` source document.

**Trigger:** This was identified via user report during a review of the project documentation.

## 2. Epic & Artifact Impact

*   **Epic Impact:** This is a low-impact change to the overall epic structure. However, it directly affects the execution of the initial development stories within the current epic.
*   **Story Impact:** This defect critically impacts story `1.1.service-initialization.md`. The missing code example is essential guidance for the developer to correctly implement the MCP server according to the specified architecture. Failure to fix this could lead to incorrect implementation or development delays.
*   **Artifact Conflict:** There is a direct content conflict between `docs/architecture.md` (the source of truth) and the sharded file `docs/architecture/mcp-server-implementation-examples.md` (the outdated shard).

## 3. Recommended Path Forward

The recommended path is **Direct Adjustment**. This is a documentation defect that can be corrected by updating the sharded file to match the content of the main architecture document. No changes to scope, epics, or other stories are required.

## 4. Specific Proposed Edits

The following action should be taken:

**Action:** Overwrite the content of the file `docs/architecture/mcp-server-implementation-examples.md`.

**New Content:**
```markdown
# MCP Server Implementation Examples

The following examples demonstrate how each of the three MCP primitives (Tools, Resources, and Prompts) will be defined in the API/Tool layer using the FastMCP SDK.

```python
# In src/agile_mcp/main.py
from mcp.server.fastmcp import FastMCP
from mcp.exceptions import McpError
from .services.story_service import StoryService
from .services.exceptions import StoryNotFoundError

# Create an instance of the FastMCP server
mcp = FastMCP("agile-service")
story_service = StoryService()

# 1. Tool Example (Model-Controlled)
# Tools are functions for the AI agent to execute actions.
@mcp.tool()
def get_story(story_id: str) -> dict:
    """
    Retrieves the full details for a single story by its unique ID.

    Args:
        story_id: The unique identifier for the story to retrieve.

    Returns:
        A dictionary containing the story's details.
    """
    try:
        story = story_service.get_story(story_id)
        return story.to_dict() # Assumes a serialization method
    except StoryNotFoundError as e:
        # Translate the internal service exception to a standard MCP error
        raise McpError(code=-32001, message=str(e), data={"story_id": story_id})

# 2. Resource Example (Application-Controlled)
# Resources expose contextual data that the host application can provide to the model.
# They are defined with a URI template.
@mcp.resource("agile://backlog")
def get_backlog() -> list[dict]:
    """
    Provides the current state of the entire project backlog.

    Returns:
        A list of all stories in the backlog.
    """
    all_stories = story_service.get_all_stories()
    return [story.to_summary_dict() for story in all_stories]

# 3. Prompt Example (User-Controlled)
# Prompts are templates that a human user can invoke, often via a UI element like a slash command.
@mcp.prompt()
def create_story_from_title(epic_id: str, title: str) -> dict:
    """
    Creates a new story with a given title within a specified epic.
    This is a user-facing command to quickly add a story to the backlog.

    Args:
        epic_id: The ID of the parent epic for the new story.
        title: The title for the new story.

    Returns:
        The newly created story object.
    """
    new_story = story_service.create_story(
        epic_id=epic_id,
        title=title,
        description="[Generated from prompt]",
        acceptance_criteria=[]
    )
    return new_story.to_dict()

# The main entry point will run the mcp server
if __name__ == "__main__":
     mcp.run()
```
```

## 5. Agent Handoff Plan

No agent handoff is required. This is a direct documentation fix. Once this proposal is approved, the proposed edit can be implemented immediately.
