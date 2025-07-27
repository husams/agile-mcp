# **Tech Stack**

This table defines the specific technologies and versions that will be used to build the service.

| Category | Technology | Version | Purpose | Rationale |
| :---- | :---- | :---- | :---- | :---- |
| **Language** | Python | \~3.11 | Primary development language | A robust, widely-used language with excellent support for web services and data handling. |
| **Data Validation** | Pydantic | Latest | Data validation and serialization | Ensures data consistency and provides automatic serialization to and from JSON, which is critical for reliable API responses. |
| **MCP SDK** | FastMCP | Latest | Handles MCP communication, tool definition, and the web server. | The official SDK for building MCP servers in Python. It simplifies development by handling protocol specifics automatically. |
| **Database** | SQLite | \~3.37+ | Local, file-based relational database | The simplest and most effective solution for a locally hosted service. No separate server process needed. |
| **ORM / DB Client** | SQLAlchemy | \~2.0 | Database toolkit and ORM | The de-facto standard for ORMs in Python, providing a powerful and flexible way to interact with the database. |
| **Testing** | Pytest | \~8.2.2 | Testing framework | A powerful and easy-to-use testing framework for Python, ideal for unit and integration tests. |
| **E2E Testing** | Release Server | Production | End-to-end testing environment | **MANDATORY**: All E2E tests MUST use the release server with real production data. No mocked data or isolated environments for E2E testing. |

## Testing Architecture Guidelines

### E2E Testing Requirements (**MANDATORY**)

**Core Principle**: All End-to-End (E2E) tests **MUST** use the release server with real production data.

**Enforcement Rules:**
1. **No Mocked Data**: E2E tests shall not use mocked, stubbed, or fabricated data
2. **Release Server Only**: All E2E tests must connect to and execute against the release server environment
3. **Real Data Validation**: Tests must validate against actual production data structures and content
4. **Production Environment**: E2E testing environment must mirror production configuration exactly
5. **No Test Isolation**: E2E tests operate on shared production data state

**Rationale:**
- Ensures tests validate real-world scenarios and data conditions
- Prevents false positives from idealized test data
- Validates complete system integration including data layer
- Maintains confidence in production deployment readiness
- Aligns with production-first testing philosophy

**Implementation Requirements:**
- E2E test configuration must specify production server endpoints
- Database connections for E2E tests must target production database
- Authentication and authorization must use production credentials
- API calls must target production MCP server instances
- Response validation must account for real production data variations

**Non-Compliance Consequences:**
- E2E tests using isolated databases are **prohibited**
- E2E tests with mocked responses are **invalid**
- Test results from non-production environments are **inadmissible**
- Development practices violating this principle require architectural review
