# **Data Models**

This section defines the core data entities for the service.

## **Epic**

* **Purpose**: Represents a large body of work or a major feature. It acts as a container for related user stories.
* **Key Attributes**:
  * id: string - Unique identifier.
  * title: string - The name of the epic.
  * description: string - A detailed explanation of the epic's goal.
  * status: string - The current state of the epic (e.g., Draft, Ready, In Progress, Done).
* **Relationships**:
  * Has many Stories.

## **Story**

* **Purpose**: Represents a single unit of work, such as a feature, bug fix, or task, from a user's perspective.
* **Key Attributes**:
  * id: string - Unique identifier.
  * title: string - A short, descriptive title.
  * description: string - The full user story text.
  * acceptanceCriteria: string[] - A list of conditions that must be met for the story to be considered complete.
  * status: string - The current state of the story (e.g., ToDo, InProgress, Review, Done).
* **Relationships**:
  * Belongs to one Epic.
  * Has many Artifacts linked to it.
  * Can have dependencies on many other Stories (prerequisites).
  * Can be a dependency for many other Stories.

## **Artifact**

* **Purpose**: Represents a link to a resource generated or used during development, such as a source code file, a design document, or an API specification.
* **Key Attributes**:
  * id: string - Unique identifier.
  * uri: string - The Uniform Resource Identifier for the artifact (e.g., file:///path/to/code.js).
  * relation: string - Describes the artifact's relationship to the story (e.g., implementation, design, test).
* **Relationships**:
  * Belongs to one Story.
