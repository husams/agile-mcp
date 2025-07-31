# Scrum Master Agent Story Creation Workflow

This document outlines the enhanced workflow for Scrum Master Agents to create self-sufficient, ready-to-code stories using the updated `backlog.createStory` tool with `dev_notes` support.

## Overview

The enhanced story creation workflow enables Scrum Master Agents to compile technical context from various sources and embed it directly into story objects, creating self-sufficient stories that Developer Agents can implement without additional context queries.

## Workflow Steps

### 1. Identify Story Requirements

Begin by identifying the requirements for the new story:
- User story description
- Acceptance criteria
- Epic association
- Priority level

### 2. Gather Technical Context

Use the `documents.getSection` tool to gather relevant technical context from various sources:

#### Architecture Context
```typescript
// Fetch architectural patterns
const archContext = await documents.getSection({
  documentId: "architecture",
  sectionName: "Authentication"
});

// Fetch database design
const dbContext = await documents.getSection({
  documentId: "architecture",
  sectionName: "Database Design"
});
```

#### Technical Specifications
```typescript
// Fetch API specifications
const apiSpecs = await documents.getSection({
  documentId: "api-docs",
  sectionName: "User Management APIs"
});

// Fetch coding standards
const codingStandards = await documents.getSection({
  documentId: "standards",
  sectionName: "Python Coding Standards"
});
```

#### Related Stories Context
```typescript
// Fetch context from related completed stories
const relatedStory = await backlog.getStory({
  storyId: "user-auth-123"
});
```

### 3. Compile Context into dev_notes

Transform the gathered context into structured `dev_notes` that provide comprehensive technical guidance:

#### dev_notes Structure
```json
{
  "architecture": {
    "overview": "Use JWT tokens with Redis session storage",
    "patterns": ["Repository Pattern", "Service Layer"],
    "dependencies": ["redis", "pyjwt", "sqlalchemy"]
  },
  "implementation": {
    "files_to_modify": [
      "src/auth/auth_service.py",
      "src/models/user.py",
      "src/api/auth_endpoints.py"
    ],
    "key_methods": [
      "authenticate_user()",
      "generate_jwt_token()",
      "validate_session()"
    ]
  },
  "technical_constraints": [
    "Token expiry: 24 hours",
    "Session cleanup: Every 4 hours",
    "Password hashing: bcrypt with salt rounds=12"
  ],
  "related_stories": [
    {
      "id": "user-auth-123",
      "relevance": "Contains base authentication logic"
    }
  ],
  "testing_guidance": {
    "unit_tests": "Test authentication service methods",
    "integration_tests": "Test full auth flow with Redis",
    "e2e_tests": "Test login/logout user journey"
  }
}
```

#### Context Compilation Example
```typescript
function compileDevNotes(contexts) {
  const devNotes = {
    architecture: {
      overview: extractArchitecturalOverview(contexts.archContext),
      patterns: extractPatterns(contexts.archContext),
      dependencies: extractDependencies(contexts.archContext)
    },
    implementation: {
      files_to_modify: identifyFilesToModify(contexts.apiSpecs),
      key_methods: extractKeyMethods(contexts.apiSpecs)
    },
    technical_constraints: extractConstraints(contexts.codingStandards),
    related_stories: formatRelatedStories(contexts.relatedStories),
    testing_guidance: compileTestingGuidance(contexts.codingStandards)
  };

  return JSON.stringify(devNotes, null, 2);
}
```

### 4. Create Self-Sufficient Story

Use the enhanced `backlog.createStory` tool with the compiled `dev_notes`:

```typescript
const story = await backlog.createStory({
  epic_id: "epic-user-management",
  title: "Implement JWT Authentication Service",
  description: "As a user, I want to authenticate securely so that my session is protected",
  acceptance_criteria: [
    "User can login with email and password",
    "System generates JWT token on successful authentication",
    "Token expires after 24 hours",
    "Session is stored in Redis for quick validation"
  ],
  tasks: [
    {
      id: "task-1",
      description: "Create AuthService class with JWT token generation",
      completed: false,
      order: 1
    },
    {
      id: "task-2",
      description: "Implement Redis session storage",
      completed: false,
      order: 2
    },
    {
      id: "task-3",
      description: "Add authentication middleware",
      completed: false,
      order: 3
    }
  ],
  structured_acceptance_criteria: [
    {
      id: "ac-1",
      description: "User can login with email and password",
      met: false,
      order: 1
    },
    {
      id: "ac-2",
      description: "System generates JWT token on successful authentication",
      met: false,
      order: 2
    }
  ],
  dev_notes: compileDevNotes(gatheredContexts),
  priority: 8
});
```

### 5. Validate Self-Sufficiency

Ensure the created story meets self-sufficiency criteria:

#### Self-Sufficient Story Checklist
- [ ] **Complete Context**: Story contains all architectural context needed
- [ ] **Technical Specifications**: All API endpoints, data models, and business rules are specified
- [ ] **Implementation Guidance**: Clear guidance on files to modify and methods to implement
- [ ] **Dependency Information**: All required libraries and services are identified
- [ ] **Testing Strategy**: Comprehensive testing approach is outlined
- [ ] **Related Work**: References to related stories and existing implementations
- [ ] **Constraints**: All technical and business constraints are documented

## Best Practices

### Context Sources Priority
1. **Architecture Documentation** - High priority for structural decisions
2. **API Specifications** - High priority for interface contracts
3. **Related Stories** - Medium priority for implementation patterns
4. **Coding Standards** - Medium priority for style and quality
5. **Business Requirements** - Low priority (should be in acceptance criteria)

### dev_notes Content Guidelines
- **Be Specific**: Include exact file paths, method names, and configuration values
- **Be Actionable**: Every piece of information should guide implementation decisions
- **Be Current**: Only include up-to-date context; avoid deprecated patterns
- **Be Structured**: Use consistent JSON schema for easy parsing by Developer Agents

### Quality Validation
Before finalizing the story:
1. **Review Completeness**: Can a Developer Agent implement this without additional queries?
2. **Check Accuracy**: Is all technical information current and correct?
3. **Verify Relevance**: Does every piece of context directly support the story implementation?
4. **Test Accessibility**: Can the Developer Agent easily parse and use the dev_notes?

## Error Handling

### Missing Context
If required context cannot be retrieved:
```typescript
// Fallback strategy
if (!requiredContext) {
  devNotes.implementation.notes = [
    "ATTENTION: Missing context for [specific area]",
    "Developer Agent should consult [specific resource] before implementation"
  ];
}
```

### Context Conflicts
When different sources provide conflicting information:
```typescript
devNotes.conflicts = [
  {
    area: "authentication_method",
    sources: ["architecture.md", "api-spec.yaml"],
    resolution: "Use architecture.md approach (JWT) as it's more recent",
    date_resolved: "2025-07-31"
  }
];
```

## Integration with Developer Agent Workflow

The created self-sufficient story integrates seamlessly with the Developer Agent workflow:

1. **Story Retrieval**: Developer Agent calls `backlog.getNextReadyStory`
2. **Context Available**: All technical context is immediately available in `dev_notes`
3. **Implementation Begins**: No additional context queries needed
4. **Progress Tracking**: Developer Agent updates story status and task completion

## Example Complete Workflow

```typescript
async function createSelfSufficientStory(requirements) {
  // Step 1: Gather context
  const archContext = await documents.getSection({
    documentId: "architecture",
    sectionName: requirements.domain
  });

  const apiContext = await documents.getSection({
    documentId: "api-specs",
    sectionName: requirements.apiArea
  });

  // Step 2: Compile dev_notes
  const devNotes = compileDevNotes({
    architecture: archContext,
    api: apiContext
  });

  // Step 3: Create story
  const story = await backlog.createStory({
    epic_id: requirements.epicId,
    title: requirements.title,
    description: requirements.description,
    acceptance_criteria: requirements.acceptanceCriteria,
    dev_notes: devNotes,
    priority: requirements.priority
  });

  // Step 4: Validate self-sufficiency
  validateStoryCompleteness(story);

  return story;
}
```

This workflow ensures that Developer Agents receive comprehensive, actionable stories that can be implemented efficiently without requiring additional context gathering.
