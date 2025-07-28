## **MCP Server Implementation Examples**

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
