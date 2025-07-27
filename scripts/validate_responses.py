#!/usr/bin/env python3
"""Pre-commit hook to validate MCP tool response formats"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, List, Optional


def has_tool_decorator(node: ast.FunctionDef) -> bool:
    """Check if function has @mcp.tool decorator"""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "tool":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "tool":
            return True
    return False


def extract_return_statements(node: ast.FunctionDef) -> List[ast.Return]:
    """Extract all return statements from a function"""
    returns = []
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            returns.append(child)
    return returns


def validates_json_return(node: ast.FunctionDef) -> bool:
    """Check if function returns valid JSON string"""
    returns = extract_return_statements(node)

    if not returns:
        return False

    for ret in returns:
        # Check if return value is a string that could be JSON
        if isinstance(ret.value, ast.Constant) and isinstance(ret.value.value, str):
            try:
                json.loads(ret.value.value)
                continue
            except json.JSONDecodeError:
                return False

        # Check for json.dumps() calls
        if isinstance(ret.value, ast.Call):
            if (
                isinstance(ret.value.func, ast.Attribute)
                and ret.value.func.attr == "dumps"
                and isinstance(ret.value.func.value, ast.Name)
                and ret.value.func.value.id == "json"
            ):
                continue

            # Check for mcp_response helper usage
            if isinstance(ret.value.func, ast.Name) and ret.value.func.id in [
                "mcp_response",
                "success_response",
                "error_response",
            ]:
                continue

        # Check for f-strings or string formatting that might produce JSON
        if isinstance(ret.value, ast.JoinedStr):
            # F-string - assume it's valid if it looks like JSON
            continue

        # If we can't verify it's JSON, flag as error
        return False

    return True


def check_pydantic_model_usage(node: ast.FunctionDef) -> List[str]:
    """Check if function properly uses Pydantic models for serialization"""
    errors = []

    # Look for model.model_dump_json() usage
    has_pydantic_serialization = False

    for child in ast.walk(node):
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "model_dump_json"
        ):
            has_pydantic_serialization = True
            break

    # If function has complex data structures but no Pydantic serialization,
    # it might need attention
    has_complex_data = False
    for child in ast.walk(node):
        if (
            isinstance(child, (ast.Dict, ast.List))
            and len(getattr(child, "keys", [])) > 3
        ):
            has_complex_data = True
            break

    if has_complex_data and not has_pydantic_serialization:
        errors.append(
            f"Function '{node.name}' has complex data structures but no Pydantic serialization"
        )

    return errors


def validate_tool_functions(file_path: Path) -> List[str]:
    """Validate all tool functions return JSON strings"""
    errors = []

    if not file_path.exists():
        return [f"File not found: {file_path}"]

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        return [f"Failed to parse {file_path}: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and has_tool_decorator(node):
            # Validate function returns JSON string
            if not validates_json_return(node):
                errors.append(
                    f"{file_path}:{node.lineno} - "
                    f"Tool function '{node.name}' must return JSON string"
                )

            # Check Pydantic model usage
            pydantic_errors = check_pydantic_model_usage(node)
            for error in pydantic_errors:
                errors.append(f"{file_path}:{node.lineno} - {error}")

    return errors


def main():
    """Main entry point for pre-commit hook"""
    if len(sys.argv) < 2:
        print("Usage: validate_responses.py <file1> [file2] ...")
        sys.exit(1)

    all_errors = []

    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)
        errors = validate_tool_functions(file_path)
        all_errors.extend(errors)

    if all_errors:
        print("❌ JSON Response Format Validation Errors:")
        for error in all_errors:
            print(f"  {error}")
        print("\n💡 Fix suggestions:")
        print("  - Ensure all @mcp.tool functions return JSON strings")
        print("  - Use json.dumps() or mcp_response() helpers")
        print("  - Consider using Pydantic models with model_dump_json()")
        sys.exit(1)
    else:
        print("✅ All tool functions have valid JSON response formats")
        sys.exit(0)


if __name__ == "__main__":
    main()
