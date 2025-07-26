# Epic 2: Artifact & Context Management

This epic enables agents to manage the artifacts they produce and retrieve granular context from both linked documents and the stories themselves.

## Story 2.1: Link Artifact to Story
**As an** AI Agent,
**I want** to link a generated artifact, such as a source file URI, to a user story,
**so that** there is a clear, traceable connection between my work and the requirement.

**Acceptance Criteria:**
1.  An `artifacts.linkToStory` tool is available.
2.  The tool accepts a story ID, an artifact URI, and a relation type (e.g., "implementation", "design", "test").
3.  The linkage is persisted correctly.
4.  An `artifacts.listForStory` tool is available to retrieve all artifacts linked to a story.

## Story 2.2: Retrieve a Specific Story Section
**As an** AI Agent,
**I want** to retrieve just a specific section of a story, like its Acceptance Criteria,
**so that** I can focus on the most relevant information for my current task without processing the entire story object.

**Acceptance Criteria:**
1.  A `backlog.getStorySection` tool is available.
2.  The tool accepts a story ID and a section name (e.g., "Acceptance Criteria", "Description").
3.  The tool returns the content of the requested section.
4.  The tool returns an appropriate error if the section does not exist.

---
