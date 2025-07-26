# Contributing to Agile Management MCP Server

Thank you for your interest in contributing to the Agile Management MCP Server! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic understanding of MCP (Model Context Protocol)
- Familiarity with agile development concepts

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/agile-mcp.git
   cd agile-mcp
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

5. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/feature-name` - Individual feature branches
- `bugfix/bug-description` - Bug fix branches
- `hotfix/critical-fix` - Critical production fixes

### Making Changes

1. Create a new branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards
3. Write or update tests for your changes
4. Run the test suite to ensure everything passes
5. Commit your changes with descriptive messages

### Testing

Run all tests before submitting:

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# End-to-end tests
python -m pytest tests/e2e/

# All tests with coverage
python -m pytest tests/ --cov=src/agile_mcp
```

### Code Quality

We maintain high code quality standards:

- **Linting**: Use `flake8` for code linting
- **Type Checking**: Use `mypy` for static type checking
- **Formatting**: Use `black` for code formatting
- **Security**: Use `bandit` for security scanning

Run quality checks:
```bash
# Linting
flake8 src/ tests/

# Type checking
mypy src/agile_mcp

# Formatting
black src/ tests/

# Security scan
bandit -r src/
```

## Coding Standards

### Python Style Guide

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public functions and classes
- Maximum line length: 88 characters (black default)

### Code Organization

- **Services**: Business logic and core functionality
- **Repositories**: Data access and persistence logic
- **API**: MCP protocol handlers and tool definitions
- **Tests**: Comprehensive test coverage for all components

### Documentation

- Update documentation for any new features
- Include docstrings with examples for complex functions
- Update README.md if changing installation or usage
- Add or update architectural documentation for significant changes

## Submitting Changes

### Pull Request Process

1. Ensure your branch is up to date with `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout your-feature-branch
   git rebase develop
   ```

2. Push your changes:
   ```bash
   git push origin your-feature-branch
   ```

3. Create a Pull Request on GitHub with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Link to any related issues
   - Screenshots or examples if applicable

### Pull Request Requirements

- [ ] All tests pass
- [ ] Code coverage maintained or improved
- [ ] Documentation updated if needed
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Security scan passes
- [ ] Commit messages are clear and descriptive

## Issue Reporting

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Log output if applicable

### Feature Requests

Include:
- Clear description of the proposed feature
- Use case and business justification
- Possible implementation approach
- Any related issues or discussions

## Code Review Guidelines

### For Authors

- Keep PRs focused and reasonably sized
- Respond promptly to review feedback
- Be open to suggestions and improvements
- Ensure CI passes before requesting review

### For Reviewers

- Be constructive and specific in feedback
- Consider both functionality and maintainability
- Test the changes if possible
- Approve only when confident in the quality

## Development Tools

### Recommended Extensions (VS Code)

- Python
- Pylance
- Black Formatter
- GitLens
- pytest

### Useful Commands

```bash
# Run server in development mode
python src/agile_mcp/main.py

# Run tests with file watching
pytest-watch

# Generate coverage report
pytest tests/ --cov=src/agile_mcp --cov-report=html

# Check all quality metrics
make lint test security  # If Makefile exists
```

## Community

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Follow our Code of Conduct

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Reach out to maintainers for guidance

Thank you for contributing! 🚀
