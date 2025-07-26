# Sprint Change Proposal: Project Structure Refactoring

## 1. Identified Issue Summary

The current project structure is flat, with the main application logic (`main.py`) and source directories (`api/`, `services/`, etc.) located in the root of the repository. This was a result of the default behavior of the `uv` packaging tool. This structure is not scalable, makes import management difficult, and does not follow standard Python project layout conventions, which can hinder long-term maintainability and onboarding of new developers.

## 2. Epic Impact Summary

This change is primarily a technical refactoring and does not directly alter the functionality or scope of any existing or future epics. However, it will touch almost all existing code and tests due to file movement and necessary import path adjustments.

- **Current & Future Epics:** No epics need to be abandoned, redefined, or re-prioritized. The core goals remain the same.
- **Story Impact:** All subsequent stories will need to be implemented within the new project structure. Existing stories that have been implemented will need their code moved and imports updated.

## 3. Artifact Adjustment Needs

The following artifacts will be impacted and require updates:

- **All Python Source Code:** All files within `main.py`, `api/`, `services/`, and `repositories/` will be moved. Their import statements will need to be updated to be relative to the new `src` root.
- **All Test Files:** Test files in `tests/` will need their import paths updated to reflect the new location of the source code (e.g., `from agile_mcp.services import...` instead of `from services import...`).
- **`requirements.txt`:** May need the addition of `.` to the python path for local development.
- **`.vscode/settings.json`:** The Python path for tooling like linters and formatters will need to be updated to include the `src` directory.
- **CI/CD & Build Scripts (if any):** Any scripts that run, test, or build the project will need to be updated to account for the new directory structure.

## 4. Recommended Path Forward

The recommended path is a **Direct Adjustment**. We will refactor the project structure immediately. Deferring this "technical debt" will only make future development more complex and costly.

### Visual Structure Comparison

Here is a visual representation of the proposed change:

**Before (Current Structure):**
```
.
├── main.py
├── api/
├── services/
├── repositories/
└── tests/
```

**After (Proposed Structure):**
```
.
├── src/
│   └── agile_mcp/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       ├── services/
│       └── repositories/
└── tests/
```

**Rationale:**
- **Adherence to Standards:** Aligns the project with best practices for Python development.
- **Improved Maintainability:** Simplifies import logic and makes the project easier to navigate.
- **Scalability:** Provides a robust foundation for adding new features and modules.
- **Minimal Functional Risk:** The change is purely structural and, if done carefully, will not alter the application's behavior.

## 5. High-Level Action Plan

1.  **Create the new directory structure:**
    -   Create `src/agile_mcp/`.
2.  **Move existing source code:**
    -   Move `main.py`, `api/`, `services/`, and `repositories/` into `src/agile_mcp/`.
3.  **Create a package:**
    -   Add an `__init__.py` file to `src/agile_mcp/` to mark it as a Python package.
4.  **Update Import Paths:**
    -   Review all moved source files and all test files, updating Python import statements to be absolute from the `src` directory (e.g., `from agile_mcp.services.some_service import ...`).
5.  **Update Development Environment Configuration:**
    -   Modify `.vscode/settings.json` to ensure linters and other tools are aware of the new source path.
6.  **Test:**
    -   Run all existing tests to confirm that the refactoring was successful and did not introduce regressions.

## 6. Agent Handoff Plan

This plan can be executed by the **Developer Agent (`*dev`)**. The PO's role is to approve this proposal and ensure a new story is created to track this refactoring work.
