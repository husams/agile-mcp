#!/usr/bin/env python3
"""Validate MCP protocol compliance for tool functions."""

import ast
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def extract_tool_metadata(node: ast.FunctionDef) -> Optional[Dict[str, Any]]:
    """Extract tool metadata from @mcp.tool decorator."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            # @mcp.tool(name="...", description="...")
            if (
                isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "tool"
            ):

                metadata = {}
                for keyword in decorator.keywords:
                    if keyword.arg == "name" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        metadata["name"] = keyword.value.value
                    elif keyword.arg == "description" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        metadata["description"] = keyword.value.value

                return metadata

    return None


def validate_tool_name(name: str) -> List[str]:
    """Validate tool name follows MCP conventions."""
    errors = []

    if not name:
        errors.append("Tool name cannot be empty")
        return errors

    # Check name format (alphanumeric, underscores, hyphens)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        errors.append(
            f"Tool name '{name}' must start with letter and contain only "
            f"alphanumeric, underscore, or hyphen characters"
        )

    # Check length
    if len(name) > 64:
        errors.append(f"Tool name '{name}' exceeds 64 character limit")

    # Convention checks
    if name.startswith("_"):
        errors.append(f"Tool name '{name}' should not start with underscore")

    if "--" in name or "__" in name:
        errors.append(
            f"Tool name '{name}' should not contain consecutive hyphens or underscores"
        )

    return errors


def validate_tool_description(description: str) -> List[str]:
    """Validate tool description follows MCP conventions."""
    errors = []

    if not description:
        errors.append("Tool description cannot be empty")
        return errors

    if len(description) < 10:
        errors.append(
            f"Tool description too short: '{description}' (minimum 10 characters)"
        )

    if len(description) > 500:
        errors.append(
            f"Tool description too long: {len(description)} characters (maximum 500)"
        )

    if not description[0].isupper():
        errors.append(
            f"Tool description should start with capital letter: '{description}'"
        )

    if not description.endswith("."):
        errors.append(f"Tool description should end with period: '{description}'")

    return errors


def validate_function_parameters(node: ast.FunctionDef) -> List[str]:
    """Validate function parameters are properly typed."""
    errors = []

    for arg in node.args.args:
        if not arg.annotation:
            errors.append(f"Parameter '{arg.arg}' missing type annotation")

        # Check for proper parameter naming
        if not re.match(r"^[a-z][a-z0-9_]*$", arg.arg):
            errors.append(f"Parameter '{arg.arg}' should use snake_case naming")

    return errors


def check_return_type_annotation(node: ast.FunctionDef) -> List[str]:
    """Check if function has proper return type annotation."""
    errors = []

    if not node.returns:
        errors.append(f"Function '{node.name}' missing return type annotation")
    else:
        # Check if return type is str (for JSON responses)
        if isinstance(node.returns, ast.Name) and node.returns.id != "str":
            errors.append(f"Function '{node.name}' should return str (JSON string)")
        elif isinstance(node.returns, ast.Constant) and node.returns.value != str:
            errors.append(f"Function '{node.name}' should return str (JSON string)")

    return errors


def validate_docstring(node: ast.FunctionDef) -> List[str]:
    """Validate function has proper docstring."""
    errors = []

    docstring = ast.get_docstring(node)
    if not docstring:
        errors.append(f"Function '{node.name}' missing docstring")
        return errors

    if len(docstring.strip()) < 20:
        errors.append(f"Function '{node.name}' docstring too short")

    # Check for parameter documentation
    params = [arg.arg for arg in node.args.args]
    for param in params:
        if param not in docstring and param != "self":
            errors.append(
                f"Function '{node.name}' docstring missing parameter "
                f"'{param}' documentation"
            )

    return errors


def validate_mcp_compliance(file_path: Path) -> List[str]:
    """Validate MCP protocol compliance for tool functions."""
    errors = []

    if not file_path.exists():
        return [f"File not found: {file_path}"]

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        return [f"Failed to parse {file_path}: {e}"]

    tool_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if it's a tool function
            metadata = extract_tool_metadata(node)
            if metadata:
                tool_name = metadata.get("name", node.name)
                description = metadata.get("description", "")

                # Validate tool name uniqueness
                if tool_name in tool_names:
                    errors.append(
                        f"{file_path}:{node.lineno} - "
                        f"Duplicate tool name '{tool_name}'"
                    )
                tool_names.add(tool_name)

                # Validate tool name
                name_errors = validate_tool_name(tool_name)
                for error in name_errors:
                    errors.append(f"{file_path}:{node.lineno} - {error}")

                # Validate description
                desc_errors = validate_tool_description(description)
                for error in desc_errors:
                    errors.append(f"{file_path}:{node.lineno} - {error}")

                # Validate function parameters
                param_errors = validate_function_parameters(node)
                for error in param_errors:
                    errors.append(f"{file_path}:{node.lineno} - {error}")

                # Validate return type
                return_errors = check_return_type_annotation(node)
                for error in return_errors:
                    errors.append(f"{file_path}:{node.lineno} - {error}")

                # Validate docstring
                doc_errors = validate_docstring(node)
                for error in doc_errors:
                    errors.append(f"{file_path}:{node.lineno} - {error}")

    return errors


def main():
    """Run MCP protocol validation on specified files."""
    if len(sys.argv) < 2:
        print("Usage: validate_mcp_protocol.py <file1> [file2] ...")
        sys.exit(1)

    all_errors = []

    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)
        errors = validate_mcp_compliance(file_path)
        all_errors.extend(errors)

    if all_errors:
        print("❌ MCP Protocol Compliance Errors:")
        for error in all_errors:
            print(f"  {error}")
        print("\n💡 Fix suggestions:")
        print("  - Ensure tool names are unique and follow naming conventions")
        print("  - Add descriptive tool descriptions (10-500 characters)")
        print("  - Add type annotations to all parameters and return types")
        print("  - Include comprehensive docstrings with parameter documentation")
        print("  - Use snake_case for parameter names")
        sys.exit(1)
    else:
        print("✅ All tool functions comply with MCP protocol")
        sys.exit(0)


if __name__ == "__main__":
    main()
