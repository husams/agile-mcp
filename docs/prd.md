# Agile Lifecycle Management Service Product Requirements Document (PRD)

## Goals and Background Context

### Goals
* **Empower AI Agents**: To provide a robust set of tools for Generative AI agents to autonomously manage the agile software development lifecycle.
* **Streamline Development**: To enable agents to efficiently manage backlogs, retrieve task-relevant information, and track generated artifacts.
* **Standardize Interaction**: To implement the Model Context Protocol (MCP) as the standard for all agent-service communication, ensuring predictable and secure interactions.
* **Support Complex Workflows**: To facilitate advanced agile practices like story dependencies and prioritized task queuing for developer agents.

### Background Context
The modern software development process, especially when augmented by AI, requires a new layer of tooling. AI agents need a structured way to interact with project management systems that is more granular and context-aware than traditional user-facing UIs.

This service will act as a specialized **MCP Server**, designed from the ground up to be used by AI agents as a primary tool. It will leverage the client-host-server architecture defined in the MCP specification, where the agent (client) communicates through a host application to our service. This ensures that the agent operates within secure, well-defined boundaries, only accessing the project information it is permitted to, without having visibility into the entire conversation or other servers. The service will be composable and easy to build upon, adhering to MCP's core design principles.

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-07-26 | 1.0 | Initial PRD draft | John (PM) |
| 2025-07-26 | 1.1 | Added requirement and story for retrieving story sections. | John (PM) |
| 2025-07-26 | 1.2 | Added formal lifecycles for Epics and Stories. | John (PM) |

---

## Requirements

### Functional
1.  **FR1**: The service MUST provide tools for agents to create, retrieve, update, and manage Epics and Stories.
2.  **FR2**: The service MUST allow agents to link generated artifacts (e.g., file URIs) to specific stories.
3.  **FR3**: The service MUST provide a tool for a Developer Agent to retrieve the next "ready" story from the backlog, respecting dependencies.
4.  **FR4**: The service MUST allow a Product Owner Agent to define dependencies between user stories.
5.  **FR5**: The service MUST allow agents to query and retrieve specific sections of documents linked as artifacts.
6.  **FR6**: All agent interactions with the service MUST conform to the Model Context Protocol (MCP) specification.
7.  **FR7**: Stories retrieved from the service MUST be self-sufficient, containing all necessary information for a developer agent to begin implementation.
8.  **FR8**: The service MUST provide a tool for an agent to retrieve a specific section of a story (e.g., "Acceptance Criteria", "Description").
9.  **FR9**: The service MUST provide tools for agents to manage the lifecycle state of Epics and Stories.

### Non Functional
1.  **NFR1**: The service architecture SHOULD be highly composable, allowing new tools and capabilities to be added progressively without impacting existing functionality, as per MCP design principles.
2.  **NFR2**: The service MUST enforce strict security boundaries, ensuring an agent can only access data and tools relevant to its session and permissions, as per MCP design principles.
3.  **NFR3**: The service MUST be designed for high availability to support continuous operation by autonomous agents.
4.  **NFR4**: The service's API response times for common operations (e.g., getting a story) SHOULD be under 200ms to ensure agent efficiency.

---

## Work Item Lifecycles

### Epic Lifecycle
* **Draft**: The epic is being defined and is not yet ready for development.
* **Ready**: The epic has been approved and its stories can be prioritized for development.
* **In Progress**: At least one story within the epic is being actively worked on.
* **Done**: All stories within the epic are complete.
* **On Hold**: The epic is temporarily paused.

### Story Lifecycle
* **ToDo**: The story is approved and waiting in the backlog.
* **InProgress**: The story is actively being worked on by a developer agent in a feature branch.
* **In Review**: The work is complete, and a pull request has been created and is pending review.
* **Done**: The pull request has been approved, passed all CI checks (linting, mypy, and all tests), and merged into the main branch.

---

## Technical Assumptions

* **Repository Structure**: A **Monorepo** structure is recommended to manage the service's packages and potentially shared types with future client implementations.
* **Service Architecture**: A **Monolithic Service** approach is recommended. This aligns with the architecture document and prioritizes simplicity for a locally hosted service.
* **Testing Requirements**: A comprehensive testing strategy is required, as formally defined in the "Testing Strategy" section of the **Architecture Document**. This includes Unit, Integration, and End-to-End tests to ensure the reliability of the tools provided to the agents.

---

## Epic List

Here is the proposed high-level list of epics to build the service. Please review the overall structure.

* **Epic 1: Core Service & Backlog Management**: Establish the foundational MCP server, implement core data models, and provide basic tools for managing epics and stories, including their lifecycles.
* **Epic 2: Artifact & Context Management**: Implement functionality for agents to link and retrieve artifacts, including the ability to query specific sections of documents and stories.
* **Epic 3: Advanced Story Workflow**: Introduce story dependencies and the intelligent "next ready story" tool for developer agents.
* **Epic 4: DevOps & Observability**: Establish a CI/CD pipeline for automated testing and implement structured logging for service monitoring.

---

## Epic 1: Core Service & Backlog Management

This epic focuses on establishing the basic service and implementing the primary tools for backlog management. It delivers the initial, core value of the system.

### Story 1.0: Project Scaffolding
**As a** Developer Agent,
**I want** to set up the initial project structure and install core dependencies,
**so that** I have a clean, consistent foundation to start building the service.

**Acceptance Criteria:**
1.  A directory structure that aligns with the 3-Layer Architecture (api, services, data) is created.
2.  A `pyproject.toml` file is created with the specified dependencies (FastMCP, SQLAlchemy, Pytest).
3.  Core dependencies are installed into the local environment.
4.  An initial, empty SQLite database file is created.

### Story 1.1: Service Initialization
**As a** Host Application,
**I want** to initialize a stateful session with the Agile Management Service using MCP,
**so that** I can enable an AI agent to interact with it.

**Acceptance Criteria:**
1.  The service correctly handles an `initialize` request from an MCP client.
2.  The service responds with its capabilities, declaring support for `tools`.
3.  A successful session is established and maintained.
4.  The service adheres to the JSON-RPC 2.0 specification for all communications.

### Story 1.2: Create and Retrieve Epics
**As an** AI Agent,
**I want** to create new epics and retrieve a list of existing epics,
**so that** I can structure the project's high-level goals.

**Acceptance Criteria:**
1.  A `backlog.createEpic` tool is available and functional.
2.  A `backlog.findEpics` tool is available and returns a list of all epics.
3.  Created epics are persisted correctly in the database with a default status of "Draft".
4.  The tools handle invalid parameters gracefully with appropriate JSON-RPC errors.

### Story 1.3: Create and Retrieve Stories
**As an** AI Agent,
**I want** to create a new user story within a specific epic and retrieve its details,
**so that** I can define and access the requirements for a unit of work.

**Acceptance Criteria:**
1.  A `backlog.createStory` tool is available and correctly associates the story with the specified epic.
2.  The tool accepts a title, description, and a list of acceptance criteria.
3.  A `backlog.getStory` tool is available and returns the full, self-contained details of a specified story.
4.  The story is created with a default status of "ToDo".

### Story 1.4: Update Story Status
**As an** AI Agent,
**I want** to update the status of a user story,
**so that** I can reflect the current state of my work (e.g., "InProgress", "Done").

**Acceptance Criteria:**
1.  A `backlog.updateStoryStatus` tool is available.
2.  The tool correctly updates the status of the specified story.
3.  The tool validates that the provided status is one of the allowed values ("ToDo", "InProgress", "Review", "Done").
4.  The change in status is reflected in subsequent calls to `backlog.getStory`.

### Story 1.5: Manage Epic Lifecycle State
**As a** Product Owner Agent,
**I want** to update the status of an epic,
**so that** I can reflect its current stage in the overall project plan.

**Acceptance Criteria:**
1. A `backlog.updateEpicStatus` tool is available.
2. The tool correctly updates the status of the specified epic.
3. The tool validates that the provided status is one of the allowed values (`Draft`, `Ready`, `In Progress`, `Done`, `On Hold`).
4. The change in status is reflected in subsequent calls to `backlog.findEpics`.

---

## Epic 2: Artifact & Context Management

This epic enables agents to manage the artifacts they produce and retrieve granular context from both linked documents and the stories themselves.

### Story 2.1: Link Artifact to Story
**As an** AI Agent,
**I want** to link a generated artifact, such as a source file URI, to a user story,
**so that** there is a clear, traceable connection between my work and the requirement.

**Acceptance Criteria:**
1.  An `artifacts.linkToStory` tool is available.
2.  The tool accepts a story ID, an artifact URI, and a relation type (e.g., "implementation", "design", "test").
3.  The linkage is persisted correctly.
4.  An `artifacts.listForStory` tool is available to retrieve all artifacts linked to a story.

### Story 2.2: Retrieve a Specific Story Section
**As an** AI Agent,
**I want** to retrieve just a specific section of a story, like its Acceptance Criteria,
**so that** I can focus on the most relevant information for my current task without processing the entire story object.

**Acceptance Criteria:**
1.  A `backlog.getStorySection` tool is available.
2.  The tool accepts a story ID and a section name (e.g., "Acceptance Criteria", "Description").
3.  The tool returns the content of the requested section.
4.  The tool returns an appropriate error if the section does not exist.

---

## Epic 3: Advanced Story Workflow

This epic introduces sophisticated workflow management, allowing for dependencies between stories and enabling developer agents to pull work from an intelligent queue.

### Story 3.1: Define Story Dependencies
**As a** Product Owner Agent,
**I want** to define a dependency between two stories, where one must be completed before the other can be started,
**so that** I can ensure a logical and technically sound order of implementation.

**Acceptance Criteria:**
1.  A `backlog.addDependency` tool is available.
2.  The tool accepts a story ID and the ID of the story it depends on.
3.  The dependency is persisted correctly.
4.  The tool prevents the creation of circular dependencies (e.g., Story A depends on B, and B depends on A).

### Story 3.2: Get Next Ready Story
**As a** Developer Agent,
**I want** to request the next story that is ready for implementation,
**so that** I can work on the highest-priority task that is not blocked by any dependencies.

**Acceptance Criteria:**
1.  A `backlog.getNextReadyStory` tool is available.
2.  The tool returns the highest-priority story with a "ToDo" status that has no incomplete dependencies.
3.  If multiple stories are ready, the one with the earliest creation date is returned.
4.  If no stories are ready, the tool returns a null or empty response.
5.  When a story is retrieved via this tool, its status is automatically updated to "InProgress".

---

## Epic 4: DevOps & Observability

This epic focuses on ensuring the project is maintainable and deployable by establishing a CI/CD pipeline and implementing basic monitoring.

### Story 4.1: Setup CI/CD Pipeline
**As a** Developer Agent,
**I want** to set up a basic CI/CD pipeline using GitHub Actions,
**so that** all tests are automatically run on every push to the main branch.

**Acceptance Criteria:**
1.  A GitHub Actions workflow file is created in `.github/workflows/`.
2.  The workflow triggers on every `push` event to the `main` branch.
3.  The workflow installs Python and all project dependencies.
4.  The workflow executes the entire `pytest` suite.
5.  The build fails if any of the tests fail.

### Story 4.2: Implement Structured Logging
**As a** Developer Agent,
**I want** to implement structured logging throughout the service,
**so that** I can easily parse and analyze log output for debugging and monitoring.

**Acceptance Criteria:**
1.  A logging library that supports structured output (e.g., JSON) is added to the project.
2.  The application is configured to output logs in a structured format.
3.  Key events in the service layer (e.g., story creation, status updates) are logged with relevant context (e.g., story ID).
4.  Errors in the API/Tool layer are logged with their associated request ID and error details.

---

## Epic List

Here is the proposed high-level list of epics to build the service. Please review the overall structure.

*   **Epic 1: Core Service & Backlog Management**: Establish the foundational MCP server, implement core data models, and provide basic tools for managing epics and stories, including their lifecycles.
*   **Epic 2: Artifact & Context Management**: Implement functionality for agents to link and retrieve artifacts, including the ability to query specific sections of documents and stories.
*   **Epic 3: Advanced Story Workflow**: Introduce story dependencies and the intelligent "next ready story" tool for developer agents.
*   **Epic 4: DevOps & Observability**: Establish a CI/CD pipeline for automated testing and implement structured logging for service monitoring.
*   **Epic 5: Enhanced Database Abstraction**: Decouple the application from SQLite, allowing for different database backends (e.g., PostgreSQL, Document, Graph).
*   **Epic 6: Agent Workflow & Model Enhancements**: Implement the project-centric data model, structured document ingestion, and the self-sufficient story model to dramatically improve agent autonomy and efficiency.
*   **Epic 7: Role-Based Access Control (RBAC)**: Implement user roles (Scrum Master, Product Owner, etc.) and permissions to control access to tools and data.

---

## Epic 5: Enhanced Database Abstraction

This epic focuses on decoupling the application from SQLite, allowing for support of various database backends, including relational, document-based, and graph databases.

### Story 5.1: Database Abstraction Layer

**As a** Developer Agent,
**I want** the database interactions to be abstracted,
**so that** the service can support different database technologies without significant code changes.

**Acceptance Criteria:**
1.  A clear abstraction layer is defined for database operations.
2.  Existing data models and repository methods are adapted to use this abstraction.
3.  The service can still function with SQLite using the new abstraction.

### Story 5.2: PostgreSQL Database Integration

**As a** Developer Agent,
**I want** the service to support PostgreSQL as a database backend,
**so that** the service can handle larger datasets and more complex queries.

**Acceptance Criteria:**
1.  The service can connect to and use a PostgreSQL database.
2.  All existing data (Epics, Stories, Artifacts, Dependencies) can be persisted and retrieved from PostgreSQL.
3.  Database migrations for PostgreSQL are defined and executable.

### Story 5.3: Document Database Integration (e.g., MongoDB)

**As a** Developer Agent,
**I want** the service to support a document-based database (e.g., MongoDB) as a backend,
**so that** the service can store and retrieve unstructured or semi-structured data more flexibly.

**Acceptance Criteria:**
1.  The service can connect to and use a document database.
2.  Epics and Stories can be stored and retrieved as documents.
3.  A clear strategy for mapping relational concepts to document models is implemented.

### Story 5.4: Graph Database Integration (e.g., Neo4j)

**As a** Developer Agent,
**I want** the service to support a graph database (e.g., Neo4j) as a backend,
**so that** the service can efficiently manage and query complex relationships between entities like stories and artifacts.

**Acceptance Criteria:**
1.  The service can connect to and use a graph database.
2.  Dependencies between stories and links to artifacts are represented as graph relationships.
3.  Queries for `getNextReadyStory` and `listForStory` leverage graph traversal capabilities.

---

## Epic 6: Agent Workflow & Model Enhancements

This epic focuses on implementing the project-centric data model, structured document ingestion, and the self-sufficient story model to dramatically improve agent autonomy and efficiency.

### Story 6.1: Implement Project Entity
**As a** System,
**I want** to introduce a top-level `Project` entity that contains all associated Epics, Stories, and Documents,
**so that** all project artifacts are organized under a single, queryable root.

**Acceptance Criteria:**
1.  A `Project` data model is created with attributes for `id`, `name`, and `description`.
2.  Existing `Epic` models are updated to include a foreign key relationship to a `Project`.
3.  A `projects.create` tool is created to initialize a new project.
4.  A `projects.find` tool is created to list all existing projects.

### Story 6.2: Implement Structured Document Storage
**As an** Analyst Agent,
**I want** to ingest documents into a structured database model, broken down by sections,
**so that** other agents can query for specific, granular context without loading entire files.

**Acceptance Criteria:**
1.  A `Document` data model is created, linked to a `Project`.
2.  A `DocumentSection` data model is created, linked to a `Document`, containing `title` (from Markdown heading) and `content`.
3.  An `documents.ingest` tool is created that accepts a file's content, parses it into sections based on Markdown headings, and saves it to the database.
4.  A `documents.getSection` tool is created to retrieve the content of a specific section by its title or ID.

### Story 6.3: Redesign Story Data Model
**As a** Developer Agent,
**I want** the `Story` object I receive to be a rich, self-sufficient model,
**so that** I have all the necessary context to begin implementation without further queries.

**Acceptance Criteria:**
1.  The `Story` data model is extended to include:
    *   `dev_notes`: A structured text field (e.g., JSON or Markdown) to hold pre-compiled architectural and technical context.
    *   `tasks`: A list of structured task objects (e.g., `{"description": "...", "completed": false}`).
    *   `comments`: A list of structured comment objects.
2.  The database schema is updated to reflect these changes.
3.  Existing story creation logic is updated to handle these new, optional fields.

### Story 6.4: Implement Unified Commenting System
**As a** QA Agent,
**I want** to add a structured comment to a story, with my role and a timestamp,
**so that** I can provide clear, auditable feedback to the Developer Agent.

**Acceptance Criteria:**
1.  A `Comment` data model is created with `author_role`, `content`, `timestamp`, and an optional `reply_to_id`.
2.  The `author_role` field MUST be an enumeration of predefined roles (e.g., `Developer Agent`, `QA Agent`, `Scrum Master`, `Product Owner`, `Human Reviewer`).
3.  A `story.addComment` tool is created that accepts a `story_id` and a `Comment` object, validating the `author_role` against the predefined list.
4.  The `backlog.getStory` tool is updated to include the full list of comments, ordered chronologically.

### Story 6.5: Update Story Creation Workflow
**As a** Scrum Master Agent,
**I want** to use the `documents.getSection` tool to gather context and compile it into the `dev_notes` of a new story,
**so that** I can create a self-sufficient, ready-to-code story for the Developer Agent.

**Acceptance Criteria:**
1.  The `backlog.createStory` tool is updated to accept the new `dev_notes`, `tasks`, and other fields.
2.  The tool correctly persists this new structured data when creating a story.
3.  The workflow for the Scrum Master agent is documented, detailing the process of fetching sections and creating the story.

### Story 6.6: Update `getNextReadyStory` Workflow
**As a** Developer Agent,
**I want** the `backlog.getNextReadyStory` tool to return the full, self-sufficient story object,
**so that** I can immediately begin work with all necessary context.

**Acceptance Criteria:**
1.  The `backlog.getNextReadyStory` tool's return payload is updated to the new, rich `Story` model.
2.  The tool's logic remains the same (respecting dependencies and status), but the data it returns is now comprehensive.
3.  The performance of the tool is not significantly degraded by the larger payload.

---

## Epic 7: Role-Based Access Control (RBAC)

This epic focuses on implementing user roles and permissions to control access to tools and data within the Agile MCP Server, ensuring secure and appropriate interactions for different types of AI agents.

### Story 7.1: User and Role Management

**As an** Administrator Agent,
**I want** to create and manage users and assign them specific roles (e.g., Scrum Master, Product Owner, Developer),
**so that** I can define different levels of access within the system.

**Acceptance Criteria:**
1.  Tools are available to create, retrieve, update, and delete users.
2.  Tools are available to define and assign roles to users.
3.  Predefined roles (Scrum Master, Product Owner, Developer, QA, Architect, Analyst, Orchestrator) are available.

### Story 7.2: Define and Enforce Permissions

**As an** Administrator Agent,
**I want** to define granular permissions for each role, specifying which tools and data they can access or modify,
**so that** I can enforce security boundaries and ensure agents only perform authorized actions.

**Acceptance Criteria:**
1.  A permission model is implemented that maps roles to specific tool access and data modification rights.
2.  The API layer enforces these permissions for every incoming MCP request.
3.  Unauthorized access attempts result in appropriate JSON-RPC error responses.

### Story 7.3: Integrate RBAC with Existing Tools

**As a** Developer Agent,
**I want** existing tools (e.g., `backlog.createStory`, `artifacts.linkToStory`) to respect the new RBAC system,
**so that** only authorized agents can perform specific actions.

**Acceptance Criteria:**
1.  All existing MCP tools are integrated with the RBAC system.
2.  A Product Owner Agent can only use tools designated for POs (e.g., `backlog.addDependency`).
3.  A Developer Agent can only use tools designated for Developers (e.g., `backlog.getNextReadyStory`).

---
