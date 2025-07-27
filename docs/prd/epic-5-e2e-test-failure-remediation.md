# Epic 5: E2E Test Failure Remediation

This epic addresses the critical E2E test failures affecting the Agile MCP Server's test suite. The focus is on achieving full compliance with the "Into Wind Testing Guideline" by ensuring all E2E tests use real servers and production data, implementing proper response validation, and establishing robust quality assurance processes.

## Overview

The E2E test suite currently has 31 failing tests due to various issues including inconsistent response formats, mocked components that don't reflect real server behavior, and inadequate response validation. This epic systematically addresses these failures while establishing long-term test reliability and architectural compliance.

## Story 5.1: Integrate Pydantic for API Responses
**As a** developer,
**I want** to properly integrate existing Pydantic response models into all API tool functions for consistent JSON serialization,
**so that** E2E test failures caused by inconsistent response formats and non-serializable objects are resolved and the API returns reliable JSON responses.

**Status:** Done

## Story 5.2: Fix Artifact Tools E2E Tests
**As a** developer,
**I want** to fix the failing E2E tests in `test_artifact_tools_e2e.py` by implementing proper JSON-RPC communication and response validation,
**so that** artifact management functionality is thoroughly validated in a production-like environment.

**Status:** ToDo

## Story 5.3: Fix Story Tools E2E Tests
**As a** developer,
**I want** to fix the failing E2E tests in `test_story_tools_e2e.py` by implementing proper server communication and response validation,
**so that** story management functionality is thoroughly validated against a real MCP server.

**Status:** ToDo

## Story 5.4: Fix Dependency Tools E2E Tests
**As a** developer,
**I want** to fix the failing E2E tests in `test_dependency_tools_e2e.py` by implementing proper JSON-RPC communication and validation,
**so that** story dependency management functionality works reliably in production environments.

**Status:** ToDo

## Story 5.5: Isolate E2E Test Database
**As a** developer,
**I want** to implement proper database isolation for E2E tests using the production server with dedicated test data,
**so that** tests run reliably without interfering with each other while maintaining architectural compliance.

**Status:** ToDo

## Story 5.6: Enhance E2E Test Validation
**As a** developer,
**I want** to implement comprehensive E2E test validation utilities for consistent response validation across all test suites,
**so that** test failures are caught early with clear diagnostic information and tests reliably validate production server responses.

**Status:** ToDo

## Story 5.7: Implement Proactive Quality Checks
**As a** developer,
**I want** to implement proactive quality checks including pre-commit hooks and enhanced CI validation,
**so that** code quality issues and test failures are prevented before they reach the main branch.

**Status:** ToDo

## Story 5.8: Refactor Mocked E2E Test to Use Real Server and Database
**As a** developer,
**I want** to refactor the `test_get_next_ready_story_e2e.py` test suite to interact with a real MCP server and production database via JSON-RPC,
**so that** our E2E tests fully comply with the "Into Wind Testing Guideline" by validating against the actual production environment with real data.

**Status:** ToDo

## Epic Goals

**Primary Objectives:**
- Achieve 100% E2E test pass rate
- Full compliance with "Into Wind Testing Guideline" architecture requirements
- Establish robust test validation framework for long-term reliability
- Implement proactive quality measures to prevent future test failures

**Success Criteria:**
- All 31 failing E2E tests are resolved and consistently passing
- E2E tests use real MCP server processes with production data access
- Comprehensive response validation utilities are in place
- Proactive quality checks prevent regression of test failures
- CI/CD pipeline reliably validates all changes before merge

**Technical Standards:**
- All E2E tests must use `mcp_server_process` fixture with real server interaction
- Production database connection required (no isolated/mocked databases)
- JSON-RPC communication over stdin/stdout for all server interactions
- Pydantic response models for consistent API response formatting
- Comprehensive validation utilities for robust test assertions

## Dependencies

**Architectural Compliance:**
- Must adhere to E2E Testing Requirements in `docs/architecture/tech-stack.md`
- Production-first testing philosophy with real data validation
- No mocked components or isolated test environments for E2E tests

**Technical Dependencies:**
- Python ~3.11 with Pytest ~8.2.2 testing framework
- SQLAlchemy ~2.0 ORM for production database access
- Pydantic for response model validation and serialization
- FastMCP SDK for MCP server communication and tool definition

**Infrastructure Requirements:**
- Production database access for E2E test execution
- CI/CD pipeline integration for automated test validation
- Pre-commit hooks for proactive quality enforcement