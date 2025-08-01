# Epic 6: Agent Workflow & Model Enhancements

This epic focuses on implementing the project-centric data model, structured document ingestion, and the self-sufficient story model to dramatically improve agent autonomy and efficiency.

## Story 6.1: Implement Project Entity
**As a** System,
**I want** to introduce a top-level `Project` entity that contains all associated Epics, Stories, and Documents,
**so that** all project artifacts are organized under a single, queryable root.

**Acceptance Criteria:**
1.  A `Project` data model is created with attributes for `id`, `name`, and `description`.
2.  Existing `Epic` models are updated to include a foreign key relationship to a `Project`.
3.  A `projects.create` tool is created to initialize a new project.
4.  A `projects.find` tool is created to list all existing projects.

## Story 6.2: Implement Structured Document Storage
**As an** Analyst Agent,
**I want** to ingest documents into a structured database model, broken down by sections,
**so that** other agents can query for specific, granular context without loading entire files.

**Acceptance Criteria:**
1.  A `Document` data model is created, linked to a `Project`.
2.  A `DocumentSection` data model is created, linked to a `Document`, containing `title` (from Markdown heading) and `content`.
3.  An `documents.ingest` tool is created that accepts a file's content, parses it into sections based on Markdown headings, and saves it to the database.
4.  A `documents.getSection` tool is created to retrieve the content of a specific section by its title or ID.

## Story 6.3: Redesign Story Data Model
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

## Story 6.4: Implement Unified Commenting System
**As a** QA Agent,
**I want** to add a structured comment to a story, with my role and a timestamp,
**so that** I can provide clear, auditable feedback to the Developer Agent.

**Acceptance Criteria:**
1.  A `Comment` data model is created with `author_role`, `content`, `timestamp`, and an optional `reply_to_id`.
2.  The `author_role` field MUST be an enumeration of predefined roles (e.g., `Developer Agent`, `QA Agent`, `Scrum Master`, `Product Owner`, `Human Reviewer`).
3.  A `story.addComment` tool is created that accepts a `story_id` and a `Comment` object, validating the `author_role` against the predefined list.
4.  The `backlog.getStory` tool is updated to include the full list of comments, ordered chronologically.

## Story 6.5: Update Story Creation Workflow
**As a** Scrum Master Agent,
**I want** to use the `documents.getSection` tool to gather context and compile it into the `dev_notes` of a new story,
**so that** I can create a self-sufficient, ready-to-code story for the Developer Agent.

**Acceptance Criteria:**
1.  The `backlog.createStory` tool is updated to accept the new `dev_notes`, `tasks`, and other fields.
2.  The tool correctly persists this new structured data when creating a story.
3.  The workflow for the Scrum Master agent is documented, detailing the process of fetching sections and creating the story.

## Story 6.6: Update `getNextReadyStory` Workflow
**As a** Developer Agent,
**I want** the `backlog.getNextReadyStory` tool to return the full, self-sufficient story object,
**so that** I can immediately begin work with all necessary context.

**Acceptance Criteria:**
1.  The `backlog.getNextReadyStory` tool's return payload is updated to the new, rich `Story` model.
2.  The tool's logic remains the same (respecting dependencies and status), but the data it returns is now comprehensive.
3.  The performance of the tool is not significantly degraded by the larger payload.

## Implementation Overview

### Epic Goals
This epic transforms the agent workflow from a query-dependent model to a self-sufficient, context-rich system that maximizes agent autonomy and efficiency. The implementation creates a hierarchical data structure (Project → Epic → Story → Document/Comments) that provides comprehensive context without requiring additional lookups.

### Story Dependencies & Implementation Sequence

**Phase 1: Core Data Models (Foundation)**
- **Story 6.1**: Project Entity - Establishes organizational hierarchy
- **Story 6.2**: Structured Document Storage - Enables context ingestion
- **Story 6.3**: Story Data Model - Creates rich, self-sufficient stories

**Phase 2: Communication System**
- **Story 6.4**: Unified Commenting System - Enables agent collaboration

**Phase 3: Agent Workflow Integration**
- **Story 6.5**: Enhanced Story Creation - Scrum Master creates context-rich stories
- **Story 6.6**: Enhanced Story Retrieval - Developer gets complete context

### Key Architectural Decisions

1. **Project-Centric Organization**: All artifacts organized under Projects for better context management
2. **Structured Document Ingestion**: Documents parsed into queryable sections for targeted context retrieval
3. **Self-Sufficient Story Model**: Stories contain all necessary implementation context (dev_notes, tasks, comments)
4. **Role-Based Comment System**: Structured communication between different agent types
5. **Backward Compatibility**: All enhancements maintain compatibility with existing workflows

### Expected Benefits

- **Reduced Agent Query Overhead**: Self-sufficient stories eliminate additional context queries
- **Improved Development Velocity**: Developers receive comprehensive context immediately
- **Enhanced Agent Collaboration**: Structured commenting enables clear agent-to-agent communication
- **Better Context Management**: Document sections provide targeted, relevant context
- **Scalable Architecture**: Project-centric model supports multiple concurrent projects

### Implementation Status
- **Stories Defined**: 6/6 Complete ✅
- **Story Validation**: Complete ✅
- **Implementation Sequence**: Validated ✅
- **Ready for Development**: Yes ✅

---
