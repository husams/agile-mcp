## **Source Tree Structure**

This document outlines the project's directory structure and organization patterns to guide development decisions and file placement.

### **Root Directory Structure**

```
agile-mcp/
├── docs/                           # Documentation and specifications
│   ├── architecture/               # Technical architecture documents
│   ├── prd/                       # Product Requirements Documents (Epics)
│   ├── stories/                   # User stories and implementation specs
│   └── mcp/                       # MCP protocol documentation
├── src/                           # Application source code
│   └── agile_mcp/                 # Main package directory
├── tests/                         # Test suite organization
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
├── scripts/                       # Utility and automation scripts
└── requirements.txt               # Python dependencies
```

### **Application Source Structure (`src/agile_mcp/`)**

```
src/agile_mcp/
├── __init__.py                    # Package initialization
├── main.py                        # MCP server entry point
├── database.py                    # Database configuration and setup
├── api/                           # MCP tool definitions (API layer)
│   ├── __init__.py
│   ├── artifact_tools.py          # Artifact management tools
│   ├── backlog_tools.py           # Backlog and section retrieval tools
│   ├── epic_tools.py              # Epic management tools
│   └── story_tools.py             # Story management tools
├── models/                        # SQLAlchemy data models
│   ├── __init__.py
│   ├── artifact.py                # Artifact entity model
│   ├── epic.py                    # Epic entity model (Base)
│   ├── story.py                   # Story entity model
│   ├── story_dependency.py        # Story dependency relationships
│   └── response.py                # API response models
├── repositories/                  # Data access layer
│   ├── __init__.py
│   ├── artifact_repository.py     # Artifact data operations
│   ├── dependency_repository.py   # Story dependency operations
│   ├── epic_repository.py         # Epic data operations
│   └── story_repository.py        # Story data operations
├── services/                      # Business logic layer
│   ├── __init__.py
│   ├── artifact_service.py        # Artifact business logic
│   ├── dependency_service.py      # Dependency validation and management
│   ├── epic_service.py            # Epic business logic
│   ├── story_service.py           # Story business logic
│   └── exceptions.py              # Custom business exceptions
└── utils/                         # Shared utilities and helpers
    ├── __init__.py
    ├── logging_config.py          # Logging configuration
    ├── mcp_response.py             # MCP response formatting
    ├── story_parser.py             # Story content parsing utilities
    └── validators.py               # Data validation utilities
```

### **Test Structure (`tests/`)**

```
tests/
├── __init__.py
├── conftest.py                    # Shared test configuration
├── unit/                          # Unit tests (isolated components)
│   ├── test_*_model.py            # Model validation tests
│   ├── test_*_repository.py       # Repository layer tests
│   ├── test_*_service.py          # Service layer tests
│   └── test_*_tools.py            # Tool/API tests with mocks
├── integration/                   # Integration tests (service + repository)
│   └── test_*_flow.py             # Cross-layer workflow tests
├── e2e/                          # End-to-end tests (full MCP protocol)
│   ├── conftest.py                # E2E-specific test setup
│   ├── test_helpers.py            # E2E testing utilities
│   └── test_*_tools_e2e.py        # Full protocol integration tests
└── utils/                        # Test utilities and helpers
    ├── __init__.py
    ├── database_isolation_validator.py  # Database test isolation
    ├── test_data_factory.py       # Test data generation
    └── test_database_manager.py   # Test database management
```

### **File Naming Conventions**

| Component Type | Naming Pattern | Example |
|----------------|---------------|---------|
| **Models** | `{entity}.py` | `story.py`, `epic.py` |
| **Repositories** | `{entity}_repository.py` | `story_repository.py` |
| **Services** | `{entity}_service.py` | `story_service.py` |
| **API Tools** | `{domain}_tools.py` | `story_tools.py` |
| **Unit Tests** | `test_{component}.py` | `test_story_model.py` |
| **E2E Tests** | `test_{component}_e2e.py` | `test_story_tools_e2e.py` |

### **Development Guidelines**

#### **New Feature Implementation**
1. **Model Layer**: Add/modify entities in `src/agile_mcp/models/`
2. **Repository Layer**: Add data access in `src/agile_mcp/repositories/`
3. **Service Layer**: Add business logic in `src/agile_mcp/services/`
4. **API Layer**: Add MCP tools in `src/agile_mcp/api/`
5. **Testing**: Add comprehensive tests in `tests/unit/`, `tests/integration/`, `tests/e2e/`

#### **Testing File Location Strategy**
- **Unit Tests**: `tests/unit/test_{filename}.py` (mirrors source structure)
- **Integration Tests**: `tests/integration/test_{workflow_name}.py`
- **E2E Tests**: `tests/e2e/test_{api_component}_e2e.py`

#### **Architecture Layers**
The application follows a layered architecture:
1. **API Layer** (`api/`): MCP protocol interface
2. **Service Layer** (`services/`): Business logic and validation
3. **Repository Layer** (`repositories/`): Data access abstraction
4. **Model Layer** (`models/`): Data entities and relationships

Each layer should only depend on layers below it in the hierarchy.
