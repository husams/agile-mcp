## **Tech Stack**

This table defines the specific technologies and versions that will be used to build the service.

| Category | Technology | Version | Purpose | Rationale |
| :---- | :---- | :---- | :---- | :---- |
| **Language** | Python | \~3.11 | Primary development language | A robust, widely-used language with excellent support for web services and data handling. |
| **Data Validation** | Pydantic | Latest | Data validation and serialization | Ensures data consistency and provides automatic serialization to and from JSON, which is critical for reliable API responses. |
| **MCP SDK** | FastMCP | Latest | Handles MCP communication, tool definition, and the web server. | The official SDK for building MCP servers in Python. It simplifies development by handling protocol specifics automatically. |
| **Database** | SQLite | \~3.37+ | Local, file-based relational database | The simplest and most effective solution for a locally hosted service. No separate server process needed. |
| **ORM / DB Client** | SQLAlchemy | \~2.0 | Database toolkit and ORM | The de-facto standard for ORMs in Python, providing a powerful and flexible way to interact with the database. |
| **Testing** | Pytest | \~8.2.2 | Testing framework | A powerful and easy-to-use testing framework for Python, ideal for unit and integration tests. |
