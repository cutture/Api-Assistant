#!/usr/bin/env python3
"""
Quick test runner to verify critical UI tests without pytest.

This script runs the most important UI tests to verify the fixes
for the icon and column mocking issues.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.chat import get_agent_icon, render_sources_section


def test_agent_icons():
    """Test that all agent icons are correct."""
    print("Testing agent icon mapping...")

    tests = [
        ("query_analyzer", "🔍"),
        ("rag_agent", "📚"),
        ("code_generator", "💻"),
        ("doc_analyzer", "📝"),
        ("unknown_agent", "🤖"),
    ]

    passed = 0
    failed = 0

    for agent_name, expected_icon in tests:
        icon = get_agent_icon(agent_name)
        if icon == expected_icon:
            print(f"  ✅ {agent_name}: {icon}")
            passed += 1
        else:
            print(f"  ❌ {agent_name}: expected {expected_icon}, got {icon}")
            failed += 1

    return passed, failed


def test_source_key_uniqueness():
    """Test that source keys are unique across messages."""
    print("\nTesting source widget key uniqueness...")

    sources = [
        {"content": "Test1", "metadata": {"endpoint": "/test1", "method": "GET"}, "score": 0.9},
        {"content": "Test2", "metadata": {"endpoint": "/test2", "method": "POST"}, "score": 0.8},
    ]

    all_keys = []

    try:
        # Test rendering for 3 different messages
        for msg_idx in range(3):
            with patch('streamlit.expander'), \
                 patch('streamlit.markdown'), \
                 patch('streamlit.columns') as mock_columns, \
                 patch('streamlit.metric'), \
                 patch('streamlit.text_area') as mock_text_area, \
                 patch('streamlit.divider'):

                # Mock columns to return 2 column objects
                col1, col2 = MagicMock(), MagicMock()
                mock_columns.return_value = [col1, col2]

                render_sources_section(sources, message_index=msg_idx)

                # Collect keys
                for call in mock_text_area.call_args_list:
                    key = call.kwargs.get('key')
                    if key:
                        all_keys.append(key)

        # Verify uniqueness
        if len(all_keys) == len(set(all_keys)):
            print(f"  ✅ All {len(all_keys)} keys are unique")
            print(f"     Keys: {all_keys}")
            return 1, 0
        else:
            print(f"  ❌ Duplicate keys found!")
            print(f"     Keys: {all_keys}")
            return 0, 1

    except Exception as e:
        print(f"  ❌ Error during test: {e}")
        return 0, 1


def main():
    """Run all tests."""
    print("=" * 70)
    print("API Integration Assistant - Quick UI Test Suite")
    print("=" * 70)
    print()

    total_passed = 0
    total_failed = 0

    # Test 1: Agent icons
    passed, failed = test_agent_icons()
    total_passed += passed
    total_failed += failed

    # Test 2: Key uniqueness
    passed, failed = test_source_key_uniqueness()
    total_passed += passed
    total_failed += failed

    # Summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print()

    if total_failed == 0:
        print("✅ All critical UI tests passed!")
        print()
        print("The fixes are working correctly:")
        print("  1. Agent icon for doc_analyzer is now '📝' (not '📋')")
        print("  2. Source widget keys are unique across messages")
        print()
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        print()
        return 1


if __name__ == '__main__':
    exit(main())
