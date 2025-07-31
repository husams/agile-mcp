# Project Tools

This document provides a comprehensive overview of the tools available in the agile-mcp project.

## Table of Contents

- [Project Tools](#project-tools)
  - [Table of Contents](#table-of-contents)
  - [Tools](#tools)
    - [1. backlog\_createEpic](#1-backlog_createepic)
    - [2. backlog\_findEpics](#2-backlog_findepics)
    - [3. backlog\_updateEpicStatus](#3-backlog_updateepicstatus)
    - [4. backlog\_createStory](#4-backlog_createstory)
    - [5. backlog\_getStory](#5-backlog_getstory)
    - [6. backlog\_updateStory](#6-backlog_updatestory)
    - [7. backlog\_updateStoryStatus](#7-backlog_updatestorystatus)
    - [8. backlog\_executeStoryDodChecklist](#8-backlog_executestorydodchecklist)
    - [9. tasks\_addToStory](#9-tasks_addtostory)
    - [10. tasks\_updateTaskStatus](#10-tasks_updatetaskstatus)
    - [11. tasks\_updateTaskDescription](#11-tasks_updatetaskdescription)
    - [12. tasks\_reorderTasks](#12-tasks_reordertasks)
    - [13. acceptanceCriteria\_addToStory](#13-acceptancecriteria_addtostory)
    - [14. acceptanceCriteria\_updateStatus](#14-acceptancecriteria_updatestatus)
    - [15. acceptanceCriteria\_updateDescription](#15-acceptancecriteria_updatedescription)
    - [16. acceptanceCriteria\_reorderCriteria](#16-acceptancecriteria_reordercriteria)
    - [17. comments\_addToStory](#17-comments_addtostory)
    - [18. artifacts\_linkToStory](#18-artifacts_linktostory)
    - [19. artifacts\_listForStory](#19-artifacts_listforstory)
    - [20. backlog\_getStorySection](#20-backlog_getstorysection)
    - [21. backlog\_addDependency](#21-backlog_adddependency)
    - [22. backlog\_getNextReadyStory](#22-backlog_getnextreadystory)

## Tools

### 1. backlog_createEpic

Create a new epic with the specified title and description.

**Parameters:**

-   `title` (string, required): The name of the epic (max 200 characters).
-   `description` (string, required): A detailed explanation of the epic's goal (max 2000 characters).

### 2. backlog_findEpics

Retrieve a list of all existing epics.

### 3. backlog_updateEpicStatus

Update the status of an epic to reflect its current stage in the project plan.

**Parameters:**

-   `epic_id` (string, required): The unique identifier of the epic to update.
-   `status` (string, required): The new status value (must be one of: "Draft", "Ready", "In Progress", "Done", "On Hold").

### 4. backlog_createStory

Create a new user story within a specific epic.

**Parameters:**

-   `epic_id` (string, required): The unique identifier of the parent epic.
-   `title` (string, required): A short, descriptive title (max 200 characters).
-   `description` (string, required): The full user story text (max 2000 characters).
-   `acceptance_criteria` (array, required): A list of conditions that must be met for the story to be considered complete.
-   `tasks` (array, optional): Optional list of task dictionaries with id, description, completed, order.
-   `structured_acceptance_criteria` (array, optional): Optional list of structured AC dictionaries.
-   `comments` (array, optional): Optional list of comment dictionaries.
-   `priority` (integer, optional): Optional story priority.

### 5. backlog_getStory

Retrieve the full, self-contained details of a specified story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.

### 6. backlog_updateStory

Update a user story with partial field updates.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `title` (string, optional): Optional new title (max 200 characters).
-   `description` (string, optional): Optional new description (max 2000 characters).
-   `acceptance_criteria` (array, optional): Optional new acceptance criteria list.
-   `tasks` (array, optional): Optional list of task dictionaries with id, description, completed, order.
-   `structured_acceptance_criteria` (array, optional): Optional list of structured AC dictionaries.
-   `comments` (array, optional): Optional list of comment dictionaries.
-   `status` (string, optional): Optional new status ("ToDo", "InProgress", "Review", "Done").

### 7. backlog_updateStoryStatus

Update the status of a user story to reflect current work state.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `status` (string, required): The new status value ("ToDo", "InProgress", "Review", "Done").

### 8. backlog_executeStoryDodChecklist

Execute the Definition of Done (DoD) checklist for a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story to check.

### 9. tasks_addToStory

Add a new task to a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `description` (string, required): Description of the task.
-   `order` (integer, optional): Optional order for the task (auto-incremented if not provided).

### 10. tasks_updateTaskStatus

Update the completion status of a task within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `task_id` (string, required): The unique identifier of the task.
-   `completed` (boolean, required): New completion status.

### 11. tasks_updateTaskDescription

Update the description of a task within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `task_id` (string, required): The unique identifier of the task.
-   `description` (string, required): New task description.

### 12. tasks_reorderTasks

Reorder tasks within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `task_orders` (array, required): List of dicts with task_id and new order.

### 13. acceptanceCriteria_addToStory

Add a new acceptance criterion to a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `description` (string, required): Description of the acceptance criterion.
-   `order` (integer, optional): Optional order for the criterion (auto-incremented if not provided).

### 14. acceptanceCriteria_updateStatus

Update the met status of an acceptance criterion within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `criterion_id` (string, required): The unique identifier of the acceptance criterion.
-   `met` (boolean, required): New met status.

### 15. acceptanceCriteria_updateDescription

Update the description of an acceptance criterion within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `criterion_id` (string, required): The unique identifier of the acceptance criterion.
-   `description` (string, required): New criterion description.

### 16. acceptanceCriteria_reorderCriteria

Reorder acceptance criteria within a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `criterion_orders` (array, required): List of dicts with criterion_id and new order.

### 17. comments_addToStory

Add a new comment to a story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `author_role` (string, required): Role of commenter (e.g., 'Developer Agent', 'QA Agent', 'Human Reviewer').
-   `content` (string, required): The comment text content.
-   `reply_to_id` (string, optional): Optional ID of comment this is replying to for threading.

### 18. artifacts_linkToStory

Links a generated artifact to a user story for traceability.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story to link the artifact to.
-   `uri` (string, required): The Uniform Resource Identifier for the artifact (e.g., file:///path/to/code.js).
-   `relation` (string, required): The relationship type between artifact and story ("implementation", "design", "test").

### 19. artifacts_listForStory

Retrieve all artifacts linked to a specific story.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.

### 20. backlog_getStorySection

Retrieve a specific section from a story by its unique ID and section name.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story.
-   `section_name` (string, required): The name of the section to extract (e.g., "Acceptance Criteria", "Story", "Tasks / Subtasks").

### 21. backlog_addDependency

Add a dependency relationship between two stories.

**Parameters:**

-   `story_id` (string, required): The unique identifier of the story that will have the dependency.
-   `depends_on_story_id` (string, required): The unique identifier of the story that must be completed first.

### 22. backlog_getNextReadyStory

Get the next story that is ready for implementation.
