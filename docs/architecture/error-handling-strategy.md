## **Error Handling Strategy**

* **Custom Exceptions**: The Service Layer will define and use custom exceptions for specific business logic failures (e.g., StoryNotFoundError, CircularDependencyError).
* **Exception Translation**: The API/Tool Layer is responsible for catching these custom exceptions and translating them into standard MCP errors with appropriate codes (e.g., -32001) and messages before sending the response to the client. This keeps the core business logic clean and protocol-agnostic.
