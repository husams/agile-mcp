# Epic 9: Agent Workflow & Model Enhancements

This document outlines the epics and stories required to implement the improved agent workflows and enhanced data models as described in `docs/improved_flow.md` and `docs/improved_model.md`.

---

## Epic 9.1: Foundational Data Model Refactor

This epic focuses on restructuring the core data model to be project-centric and support the ingestion of structured documents. This is the foundation for creating self-sufficient stories.

### Story 9.1.1: Implement Project Entity
**As a** System,
**I want** to introduce a top-level `Project` entity that contains all associated Epics, Stories, and Documents,
**so that** all project artifacts are organized under a single, queryable root.

**Acceptance Criteria:**
1.  A `Project` data model is created with attributes for `id`, `name`, and `description`.
2.  Existing `Epic` models are updated to include a foreign key relationship to a `Project`.
3.  A `projects.create` tool is created to initialize a new project.
4.  A `projects.find` tool is created to list all existing projects.

### Story 9.1.2: Implement Structured Document Storage
**As an** Analyst Agent,
**I want** to ingest documents into a structured database model, broken down by sections,
**so that** other agents can query for specific, granular context without loading entire files.

**Acceptance Criteria:**
1.  A `Document` data model is created, linked to a `Project`.
2.  A `DocumentSection` data model is created, linked to a `Document`, containing `title` (from Markdown heading) and `content`.
3.  An `documents.ingest` tool is created that accepts a file's content, parses it into sections based on Markdown headings, and saves it to the database.
4.  A `documents.getSection` tool is created to retrieve the content of a specific section by its title or ID.

---

## Epic 9.2: Implement Self-Sufficient Story Model

This epic focuses on redesigning the `Story` model to be a self-contained packet of information, enabling the Developer Agent to work with maximum efficiency.

### Story 9.2.1: Redesign Story Data Model
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

### Story 9.2.2: Implement Unified Commenting System
**As a** QA Agent,
**I want** to add a structured comment to a story, with my role and a timestamp,
**so that** I can provide clear, auditable feedback to the Developer Agent.

**Acceptance Criteria:**
1.  A `Comment` data model is created with `author_role`, `content`, `timestamp`, and an optional `reply_to_id`.
2.  The `author_role` field MUST be an enumeration of predefined roles (e.g., `Developer Agent`, `QA Agent`, `Scrum Master`, `Product Owner`, `Human Reviewer`).
3.  A `story.addComment` tool is created that accepts a `story_id` and a `Comment` object, validating the `author_role` against the predefined list.
4.  The `backlog.getStory` tool is updated to include the full list of comments, ordered chronologically.

---

## Epic 9.3: Adapt Agent Workflows & Existing Tools

This epic ensures that the existing agent workflows are updated to leverage the new, richer data models, delivering the intended efficiency gains.

### Story 9.3.1: Update Story Creation Workflow
**As a** Scrum Master Agent,
**I want** to use the `documents.getSection` tool to gather context and compile it into the `dev_notes` of a new story,
**so that** I can create a self-sufficient, ready-to-code story for the Developer Agent.

**Acceptance Criteria:**
1.  The `backlog.createStory` tool is updated to accept the new `dev_notes`, `tasks`, and other fields.
2.  The tool correctly persists this new structured data when creating a story.
3.  The workflow for the Scrum Master agent is documented, detailing the process of fetching sections and creating the story.

### Story 9.3.2: Update `getNextReadyStory` Workflow
**As a** Developer Agent,
**I want** the `backlog.getNextReadyStory` tool to return the full, self-sufficient story object,
**so that** I can immediately begin work with all necessary context.

**Acceptance Criteria:**
1.  The `backlog.getNextReadyStory` tool's return payload is updated to the new, rich `Story` model.
2.  The tool's logic remains the same (respecting dependencies and status), but the data it returns is now comprehensive.
3.  The performance of the tool is not significantly degraded by the larger payload.
