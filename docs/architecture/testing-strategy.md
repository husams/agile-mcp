## **Testing Strategy**

To ensure the reliability and correctness of the Agile Lifecycle Management Service, a multi-layered testing approach will be implemented using the **Pytest** framework. The strategy is designed to validate the service at the unit, integration, and end-to-end levels, accounting for the specifics of the MCP protocol and its transports. All tests are executed automatically in the CI/CD pipeline, and a pull request cannot be merged unless all tests pass.

### **1. Unit Tests**

*   **Scope**: Focus on individual functions and classes within the **Service Layer** and **Repository Layer**.
*   **Goal**: Verify that the core business logic (e.g., dependency validation, status transitions) and data access functions work correctly in isolation.
*   **Methodology**:
    *   The API/Tool layer will be mocked to isolate the service logic.
    *   The database will be mocked or an in-memory SQLite database will be used for repository tests to ensure speed and isolation.
    *   Tests will be located in `tests/unit`.

### **2. Integration Tests**

*   **Scope**: Test the interaction between the **Service Layer** and the **Repository Layer**.
*   **Goal**: Ensure that the business logic correctly interacts with the database via the repository pattern.
*   **Methodology**:
    *   Tests will use a dedicated, temporary SQLite database file to test real database operations without mocking the ORM.
    *   Each test will run in a transaction that is rolled back after completion to maintain a clean state.
    *   Tests will be located in `tests/integration`.

### **3. End-to-End (E2E) Tests**

*   **Scope**: Test the entire application stack, from the MCP transport layer down to the database.
*   **Goal**: Validate that the service behaves correctly from the perspective of an AI agent (MCP client), ensuring that JSON-RPC requests are handled properly and produce the correct responses and side effects.
*   **Methodology**:
    *   E2E tests will simulate an MCP client interacting with the running service.
    *   For the MVP, testing will focus exclusively on the **`stdio` transport**, as this is the primary communication method for locally hosted MCP servers.
    *   A `pytest` fixture will launch the server as a `subprocess`.
    *   The test will write JSON-RPC request strings to the subprocess's `stdin`.
    *   It will read from `stdout` to capture the JSON-RPC response and from `stderr` to check for logs.
    *   Tests will assert that `stdout` contains *only* the valid JSON-RPC response and that any logging output is correctly directed to `stderr`.
    *   Tests will be located in `tests/e2e`.
