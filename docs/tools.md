# Project Tools

This document provides a comprehensive overview of the tools available in the agile-mcp project.

## Table of Contents

- [Project Tools](#project-tools)
  - [Table of Contents](#table-of-contents)
  - [Tools](#tools)
    - [1. projects_create](#1-projects_create)
    - [2. projects_find](#2-projects_find)
    - [3. backlog_createEpic](#3-backlog_createepic)
    - [4. backlog_findEpics](#4-backlog_findepics)
    - [5. backlog_updateEpicStatus](#5-backlog_updateepicstatus)
    - [6. backlog_createStory](#6-backlog_createstory)
    - [7. backlog_getStory](#7-backlog_getstory)
    - [8. backlog_updateStory](#8-backlog_updatestory)
    - [9. backlog_updateStoryStatus](#9-backlog_updatestorystatus)
    - [10. backlog_executeStoryDodChecklist](#10-backlog_executestorydodchecklist)
    - [11. tasks_addToStory](#11-tasks_addtostory)
    - [12. tasks_updateTaskStatus](#12-tasks_updatetaskstatus)
    - [13. tasks_updateTaskDescription](#13-tasks_updatetaskdescription)
    - [14. tasks_reorderTasks](#14-tasks_reordertasks)
    - [15. acceptanceCriteria_addToStory](#15-acceptancecriteria_addtostory)
    - [16. acceptanceCriteria_updateStatus](#16-acceptancecriteria_updatestatus)
    - [17. acceptanceCriteria_updateDescription](#17-acceptancecriteria_updatedescription)
    - [18. acceptanceCriteria_reorderCriteria](#18-acceptancecriteria_reordercriteria)
    - [19. story_addComment](#19-story_addcomment)
    - [20. story_getComments](#20-story_getcomments)
    - [21. story_updateComment](#21-story_updatecomment)
    - [22. story_deleteComment](#22-story_deletecomment)
    - [23. artifacts_linkToStory](#23-artifacts_linktostory)
    - [24. artifacts_listForStory](#24-artifacts_listforstory)
    - [25. backlog_getStorySection](#25-backlog_getstorysection)
    - [26. backlog_addDependency](#26-backlog_adddependency)
    - [27. backlog_getNextReadyStory](#27-backlog_getnextreadystory)
    - [28. documents_ingest](#28-documents_ingest)
    - [29. documents_getSection](#29-documents_getsection)

## Tools

### 1. projects_create

Create a new project with the specified name and description.

**Parameters:**

-   `name` (string, required): The name of the project (max 200 characters).
-   `description` (string, required): A detailed explanation of the project's purpose (max 2000 characters).

### 2. projects_find

Retrieve a list of all existing projects.

### 3. backlog_createEpic

Create a new epic with the specified title and description.

**Parameters:**

-   `project_id` (string, required): The ID of the project this epic belongs to.
-   `title` (string, required): The name of the epic (max 200 characters).
-   `description` (string, required): A detailed explanation of the epic's goal (max 2000 characters).

### 4. backlog_findEpics

Retrieve a list of all existing epics.

### 5. backlog_updateEpicStatus

Update the status of an epic to reflect its current stage in the project plan.

**Parameters:**

-   `epic_id` (string, required): The unique identifier of the epic to update.
-   `status` (string, required): The new status value (must be one of: "Draft", "Ready", "In Progress", "Done", "On Hold").

### 6. backlog_createStory

Create a new user story within a specific epic.

**Parameters:**

-   `epic_id` (string, required): The unique identifier of the parent epic.
-   `title` (string, required): A short, descriptive title (max 200 characters).
-   `description` (string, required): The full user story text (max 2000 characters).
-   `acceptance_criteria` (array, required): A list of conditions that must be met for the story to be considered complete.
-   `tasks` (array, optional): Optional list of task dictionaries with id, description, completed, order.
-   `structured_acceptance_criteria` (array, optional): Optional list of structured AC dictionaries.
-   `comments` (array, optional): Optional list of comment dictionaries.
-   `dev_notes` (string, optional): Optional pre-compiled technical context and notes.
-   `priority` (integer, optional): Optional story priority.

### 7. backlog_getStory

Retrieve the full, self-contained details of a specified story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.

### 8. backlog_updateStory

Update a user story with partial field updates.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `title` (string, optional): Optional new title (max 200 characters).
-   `description` (string, optional): Optional new description (max 2000 characters).
-   `acceptance_criteria` (array, optional): Optional new acceptance criteria list.
-   `tasks` (array, optional): Optional list of task dictionaries with id, description, completed, order.
-   `structured_acceptance_criteria` (array, optional): Optional list of structured AC dictionaries.
-   `comments` (array, optional): Optional list of comment dictionaries.
-   `dev_notes` (string, optional): Optional pre-compiled technical context and notes.
-   `status` (string, optional): Optional new status ("ToDo", "InProgress", "Review", "Done").

### 9. backlog_updateStoryStatus

Update the status of a user story to reflect current work state.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `status` (string, required): The new status value ("ToDo", "InProgress", "Review", "Done").

### 10. backlog_executeStoryDodChecklist

Execute the Definition of Done (DoD) checklist for a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story to check.

### 11. tasks_addToStory

Add a new task to a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `description` (string, required): Description of the task.
-   `order` (integer, optional): Optional order for the task (auto-incremented if not provided).

### 12. tasks_updateTaskStatus

Update the completion status of a task within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `task_id` (string, required): The unique identifier of the task.
-   `completed` (boolean, required): New completion status.

### 13. tasks_updateTaskDescription

Update the description of a task within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `task_id` (string, required): The unique identifier of the task.
-   `description` (string, required): New task description.

### 14. tasks_reorderTasks

Reorder tasks within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `task_orders` (array, required): List of dicts with task_id and new order.

### 15. acceptanceCriteria_addToStory

Add a new acceptance criterion to a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `description` (string, required): Description of the acceptance criterion.
-   `order` (integer, optional): Optional order for the criterion (auto-incremented if not provided).

### 16. acceptanceCriteria_updateStatus

Update the met status of an acceptance criterion within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `criterion_id` (string, required): The unique identifier of the acceptance criterion.
-   `met` (boolean, required): New met status.

### 17. acceptanceCriteria_updateDescription

Update the description of an acceptance criterion within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `criterion_id` (string, required): The unique identifier of the acceptance criterion.
-   `description` (string, required): New criterion description.

### 18. acceptanceCriteria_reorderCriteria

Reorder acceptance criteria within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `criterion_orders` (array, required): List of dicts with criterion_id and new order.

### 19. story_addComment

Add a structured comment to a story with role and timestamp.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `author_role` (string, required): The role of the comment author (must be from predefined roles: 'Developer Agent', 'QA Agent', 'Scrum Master', 'Product Owner', 'Human Reviewer', 'System').
-   `content` (string, required): The comment text content.
-   `reply_to_id` (string, optional): Optional ID of comment this is replying to for threading.

### 20. story_getComments

Retrieve all comments for a story, ordered chronologically.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.

### 21. story_updateComment

Update the content of an existing comment.

**Parameters:**

-   `comment_id` (string, required): The unique identifier of the comment.
-   `content` (string, required): New comment content.

### 22. story_deleteComment

Delete a comment.

**Parameters:**

-   `comment_id` (string, required): The unique identifier of the comment.

### 23. artifacts_linkToStory

Links a generated artifact to a user story for traceability.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story to link the artifact to.
-   `uri` (string, required): The Uniform Resource Identifier for the artifact (e.g., file:///path/to/code.js).
-   `relation` (string, required): The relationship type between artifact and story ("implementation", "design", "test").

### 24. artifacts_listForStory

Retrieve all artifacts linked to a specific story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.

### 25. backlog_getStorySection

Retrieve a specific section from a story by its unique ID and section name.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `section_name` (string, required): The name of the section to extract (e.g., "Acceptance Criteria", "Story", "Tasks / Subtasks").

### 26. backlog_addDependency

Add a dependency relationship between two stories.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story that will have the dependency.
-   `depends_on_story_id` (string, required): The unique identifier of the story that must be completed first.

### 27. backlog_getNextReadyStory

Get the next story that is ready for implementation.

### 28. documents_ingest

Ingest a document by parsing its Markdown content into structured sections.

**Parameters:**

-   `project_id` (string, required): ID of the project to ingest document into.
-   `file_path` (string, required): Path to the original file.
-   `content` (string, required): Markdown content to parse and ingest.
-   `title` (string, optional): Optional custom title for the document.

### 29. documents_getSection

Retrieve document sections by ID or title.

**Parameters:**

-   `section_id` (string, optional): ID of the specific section to retrieve.
-   `title` (string, optional): Title to search for in sections (case-insensitive).
-   `document_id` (string, optional): ID of document to search within (optional).
-   `project_id` (string, optional): ID of project to search within (optional).
