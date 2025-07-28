#!/usr/bin/env python3
"""Pre-commit hook to run critical E2E tests against production server."""

import argparse
import os
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import List, Set


def get_changed_modules(file_paths: List[str]) -> Set[str]:
    """Determine which test modules to run based on changed files."""
    modules = set()

    for file_path in file_paths:
        path = Path(file_path)

        # Map source files to corresponding test modules
        if "api/" in str(path):
            if "artifact" in str(path):
                modules.add("test_artifact_tools_e2e")
            elif "backlog" in str(path):
                modules.add("test_backlog_section_tools_e2e")
            elif "epic" in str(path):
                modules.add("test_epic_tools_e2e")
            elif "story" in str(path):
                modules.add("test_story_tools_e2e")
                modules.add("test_get_next_ready_story_e2e")

        if "services/" in str(path):
            if "artifact" in str(path):
                modules.add("test_artifact_tools_e2e")
            elif "epic" in str(path):
                modules.add("test_epic_tools_e2e")
            elif "story" in str(path):
                modules.add("test_story_tools_e2e")
            elif "dependency" in str(path):
                modules.add("test_dependency_tools_e2e")

        if "models/" in str(path):
            # Model changes affect all tests
            modules.update(
                [
                    "test_artifact_tools_e2e",
                    "test_backlog_section_tools_e2e",
                    "test_epic_tools_e2e",
                    "test_story_tools_e2e",
                    "test_get_next_ready_story_e2e",
                    "test_dependency_tools_e2e",
                ]
            )

    # If no specific modules identified, run core tests
    if not modules:
        modules = {"test_story_tools_e2e", "test_epic_tools_e2e"}

    return modules


def run_test_module(module_name: str, production_server: bool = True) -> bool:
    """Run a specific test module."""
    test_file = f"tests/e2e/{module_name}.py"

    if not Path(test_file).exists():
        print(f"⚠️  Test file not found: {test_file}")
        return True  # Don't fail pre-commit for missing test files

    cmd = ["python", "-m", "pytest", test_file, "-v"]

    if production_server:
        # Set environment to use production server
        env = os.environ.copy()
        env["MCP_TEST_MODE"] = "production"
        env["MCP_SERVER_URL"] = "http://localhost:8000"  # Production server URL
    else:
        env = None

    try:
        result = subprocess.run(  # nosec B603
            cmd, capture_output=True, text=True, env=env, timeout=120
        )

        if result.returncode == 0:
            print(f"✅ {module_name}: PASSED")
            return True
        else:
            print(f"❌ {module_name}: FAILED")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {module_name}: TIMEOUT (120s)")
        return False
    except Exception as e:
        print(f"💥 {module_name}: ERROR - {e}")
        return False


def main():
    """Run critical E2E test runner."""
    parser = argparse.ArgumentParser(
        description="Run critical E2E tests for pre-commit"
    )
    parser.add_argument(
        "--production-server",
        action="store_true",
        help="Run tests against production server",
    )
    parser.add_argument("files", nargs="*", help="Changed files to analyze")

    args = parser.parse_args()

    if not args.files:
        print("No files provided, running core test suite...")
        modules = {"test_story_tools_e2e", "test_epic_tools_e2e"}
    else:
        modules = get_changed_modules(args.files)
        print(f"Running tests for modules: {', '.join(modules)}")

    if args.production_server:
        print("🌐 Running tests against production server...")
    else:
        print("🧪 Running tests against test environment...")

    all_passed = True

    for module in modules:
        passed = run_test_module(module, args.production_server)
        if not passed:
            all_passed = False

    if all_passed:
        print("✅ All critical E2E tests passed")
        sys.exit(0)
    else:
        print("❌ Some critical E2E tests failed")
        print("\n💡 Fix suggestions:")
        print("  - Check API response formats match expected JSON structure")
        print("  - Verify database operations are working correctly")
        print("  - Ensure production server is running and accessible")
        sys.exit(1)


if __name__ == "__main__":
    main()
