#!/usr/bin/env python3
"""
Validate test structure and count tests.

This script validates that all test files are properly structured
and reports the number of test functions found.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def count_tests_in_file(file_path: Path) -> Tuple[int, int]:
    """
    Count test functions and classes in a Python file.

    Args:
        file_path: Path to the test file

    Returns:
        Tuple of (number of test classes, number of test functions)
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Count test classes
    test_classes = len(re.findall(r'class Test\w+:', content))

    # Count test functions (including methods)
    test_functions = len(re.findall(r'def test_\w+\(', content))

    return test_classes, test_functions


def find_test_files(directory: Path) -> List[Path]:
    """Find all test files in a directory."""
    test_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .pytest_cache
        dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__'))]

        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(Path(root) / file)

    return sorted(test_files)


def validate_test_structure(file_path: Path) -> List[str]:
    """
    Validate test file structure.

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    with open(file_path, 'r') as f:
        content = f.read()

    # Check for docstring
    if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
        issues.append(f"Missing module docstring: {file_path}")

    # Check for pytest import
    if 'import pytest' not in content and 'from pytest' not in content:
        if 'def test_' in content:  # Has tests but no pytest import
            issues.append(f"Missing pytest import: {file_path}")

    # Check for proper test naming
    if 'def test' in content.lower():
        invalid_tests = re.findall(r'def (test\w+)\(', content)
        for test_name in invalid_tests:
            if not test_name.startswith('test_') and test_name != 'test':
                issues.append(f"Invalid test name '{test_name}': {file_path}")

    return issues


def main():
    """Main validation function."""
    tests_dir = Path(__file__).parent

    print("=" * 70)
    print("API Integration Assistant - Test Validation")
    print("=" * 70)
    print()

    # Find all test files
    test_files = find_test_files(tests_dir)

    if not test_files:
        print("❌ No test files found!")
        return 1

    # Collect statistics
    total_classes = 0
    total_functions = 0
    total_issues = []
    results_by_dir: Dict[str, Dict] = {}

    print(f"Found {len(test_files)} test files:\n")

    for test_file in test_files:
        # Get relative path
        rel_path = test_file.relative_to(tests_dir)
        dir_name = str(rel_path.parent) if str(rel_path.parent) != '.' else 'root'

        # Count tests
        classes, functions = count_tests_in_file(test_file)
        total_classes += classes
        total_functions += functions

        # Validate structure
        issues = validate_test_structure(test_file)
        total_issues.extend(issues)

        # Track by directory
        if dir_name not in results_by_dir:
            results_by_dir[dir_name] = {'files': 0, 'classes': 0, 'functions': 0}

        results_by_dir[dir_name]['files'] += 1
        results_by_dir[dir_name]['classes'] += classes
        results_by_dir[dir_name]['functions'] += functions

        # Print file results
        status = "✅" if not issues else "⚠️"
        print(f"  {status} {rel_path}")
        print(f"     - {classes} test classes, {functions} test functions")
        if issues:
            for issue in issues:
                print(f"     - ⚠️  {issue}")

    print()
    print("=" * 70)
    print("Summary by Directory:")
    print("=" * 70)

    for dir_name, stats in sorted(results_by_dir.items()):
        print(f"\n{dir_name}/")
        print(f"  Files:     {stats['files']}")
        print(f"  Classes:   {stats['classes']}")
        print(f"  Functions: {stats['functions']}")

    print()
    print("=" * 70)
    print("Overall Statistics:")
    print("=" * 70)
    print(f"  Total test files:      {len(test_files)}")
    print(f"  Total test classes:    {total_classes}")
    print(f"  Total test functions:  {total_functions}")
    print(f"  Structure issues:      {len(total_issues)}")
    print()

    if total_issues:
        print("=" * 70)
        print("Validation Issues:")
        print("=" * 70)
        for issue in total_issues:
            print(f"  ⚠️  {issue}")
        print()
        return 1
    else:
        print("✅ All tests validated successfully!")
        print()
        print("To run the tests:")
        print("  pip install pytest pytest-asyncio")
        print("  pytest -v")
        print()
        return 0


if __name__ == '__main__':
    exit(main())
