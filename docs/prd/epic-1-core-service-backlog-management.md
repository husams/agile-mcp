# Epic 1: Core Service & Backlog Management

This epic focuses on establishing the basic service and implementing the primary tools for backlog management. It delivers the initial, core value of the system.

## Story 1.0: Project Scaffolding
**As a** Developer Agent,
**I want** to set up the initial project structure and install core dependencies,
**so that** I have a clean, consistent foundation to start building the service.

**Acceptance Criteria:**
1.  A directory structure that aligns with the 3-Layer Architecture (api, services, data) is created.
2.  A `pyproject.toml` file is created with the specified dependencies (FastMCP, SQLAlchemy, Pytest).
3.  Core dependencies are installed into the local environment.
4.  An initial, empty SQLite database file is created.

## Story 1.1: Service Initialization
**As a** Host Application,
**I want** to initialize a stateful session with the Agile Management Service using MCP,
**so that** I can enable an AI agent to interact with it.

**Acceptance Criteria:**
1.  The service correctly handles an `initialize` request from an MCP client.
2.  The service responds with its capabilities, declaring support for `tools`.
3.  A successful session is established and maintained.
4.  The service adheres to the JSON-RPC 2.0 specification for all communications.

## Story 1.2: Create and Retrieve Epics
**As an** AI Agent,
**I want** to create new epics and retrieve a list of existing epics,
**so that** I can structure the project's high-level goals.

**Acceptance Criteria:**
1.  A `backlog.createEpic` tool is available and functional.
2.  A `backlog.findEpics` tool is available and returns a list of all epics.
3.  Created epics are persisted correctly in the database with a default status of "Draft".
4.  The tools handle invalid parameters gracefully with appropriate JSON-RPC errors.

## Story 1.3: Create and Retrieve Stories
**As an** AI Agent,
**I want** to create a new user story within a specific epic and retrieve its details,
**so that** I can define and access the requirements for a unit of work.

**Acceptance Criteria:**
1.  A `backlog.createStory` tool is available and correctly associates the story with the specified epic.
2.  The tool accepts a title, description, and a list of acceptance criteria.
3.  A `backlog.getStory` tool is available and returns the full, self-contained details of a specified story.
4.  The story is created with a default status of "ToDo".

## Story 1.4: Update Story Status
**As an** AI Agent,
**I want** to update the status of a user story,
**so that** I can reflect the current state of my work (e.g., "InProgress", "Done").

**Acceptance Criteria:**
1.  A `backlog.updateStoryStatus` tool is available.
2.  The tool correctly updates the status of the specified story.
3.  The tool validates that the provided status is one of the allowed values ("ToDo", "InProgress", "Review", "Done").
4.  The change in status is reflected in subsequent calls to `backlog.getStory`.

## Story 1.5: Manage Epic Lifecycle State
**As a** Product Owner Agent,
**I want** to update the status of an epic,
**so that** I can reflect its current stage in the overall project plan.

**Acceptance Criteria:**
1. A `backlog.updateEpicStatus` tool is available.
2. The tool correctly updates the status of the specified epic.
3. The tool validates that the provided status is one of the allowed values (`Draft`, `Ready`, `In Progress`, `Done`, `On Hold`).
4. The change in status is reflected in subsequent calls to `backlog.findEpics`.

---
