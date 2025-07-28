## Testing Architecture Guidelines

### E2E Testing Requirements (**MANDATORY**)

**Core Principle**: All End-to-End (E2E) tests **MUST** use isolated test data and environments.

**Enforcement Rules:**
1. **Isolated Data**: E2E tests shall use dedicated, isolated test data, not shared production data.
2. **Isolated Environment**: All E2E tests must connect to and execute against an isolated test server environment, not the release server.
3. **No Production Data**: Tests must not validate against actual production data structures or content.
4. **Test Environment Mirroring**: The E2E testing environment should mirror production configuration as closely as possible, but with isolated data.
5. **Test Isolation**: E2E tests must operate on an isolated data state, ensuring no side effects on other tests or production data.

**Rationale:**
- Prevents data corruption in production environments.
- Ensures test repeatability and reliability by eliminating dependencies on external data changes.
- Facilitates parallel test execution without conflicts.
- Provides a safe environment for testing destructive operations.
- Aligns with best practices for robust automated testing.

**Implementation Requirements:**
- E2E test configuration must specify isolated test server endpoints.
- Database connections for E2E tests must target isolated test databases.
- Authentication and authorization must use test credentials.
- API calls must target isolated MCP server instances.
- Response validation must account for expected test data variations.

**Non-Compliance Consequences:**
- E2E tests using shared production databases are **prohibited**.
- E2E tests with dependencies on production data are **invalid**.
- Test results from non-isolated environments are **inadmissible**.
- Development practices violating this principle require architectural review.
