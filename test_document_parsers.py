#!/usr/bin/env python3
"""
Quick test script to verify document parsers work correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.text_parser import TextParser
from src.parsers.json_generic_parser import JSONGenericParser
from src.parsers.format_handler import UnifiedFormatHandler, FormatDetector


def test_text_parser():
    """Test TextParser with sample text file."""
    print("\n=== Testing TextParser ===")
    with open("examples/sample-text.txt", "r") as f:
        content = f.read()

    parser = TextParser()
    result = parser.parse(content, "sample-text.txt")

    print(f"Title: {result.title}")
    print(f"Document Type: {result.document_type}")
    print(f"Number of chunks: {len(result.chunks)}")
    print(f"Word count: {result.word_count}")
    print(f"Character count: {result.character_count}")

    print("\nFirst chunk:")
    print(result.chunks[0].content[:200] + "...")

    return result


def test_markdown_parser():
    """Test TextParser with sample markdown file."""
    print("\n=== Testing Markdown Parser ===")
    with open("examples/sample-markdown.md", "r") as f:
        content = f.read()

    parser = TextParser()
    result = parser.parse(content, "sample-markdown.md")

    print(f"Title: {result.title}")
    print(f"Document Type: {result.document_type}")
    print(f"Number of chunks: {len(result.chunks)}")

    print("\nChunks with section titles:")
    for i, chunk in enumerate(result.chunks[:3]):
        title = chunk.section_title or "No section"
        print(f"  Chunk {i}: {title}")

    return result


def test_json_parser():
    """Test JSONGenericParser with sample JSON file."""
    print("\n=== Testing JSONGenericParser ===")
    with open("examples/sample-data.json", "r") as f:
        content = f.read()

    parser = JSONGenericParser()
    result = parser.parse(content, "sample-data.json")

    print(f"Title: {result.title}")
    print(f"Document Type: {result.document_type}")
    print(f"Number of chunks: {len(result.chunks)}")
    print(f"Metadata: {result.metadata}")

    print("\nFirst chunk:")
    print(result.chunks[0].content[:200] + "...")

    return result


def test_format_detection():
    """Test FormatDetector."""
    print("\n=== Testing FormatDetector ===")

    detector = FormatDetector()

    # Test text file
    with open("examples/sample-text.txt", "r") as f:
        content = f.read()
    doc_type = detector.detect_document_type(content, "sample-text.txt")
    print(f"sample-text.txt detected as: {doc_type}")

    # Test markdown file
    with open("examples/sample-markdown.md", "r") as f:
        content = f.read()
    doc_type = detector.detect_document_type(content, "sample-markdown.md")
    print(f"sample-markdown.md detected as: {doc_type}")

    # Test JSON file
    with open("examples/sample-data.json", "r") as f:
        content = f.read()
    doc_type = detector.detect_document_type(content, "sample-data.json")
    print(f"sample-data.json detected as: {doc_type}")

    # Test OpenAPI file
    with open("examples/sample-openapi.json", "r") as f:
        content = f.read()
    doc_type = detector.detect_document_type(content, "sample-openapi.json")
    print(f"sample-openapi.json detected as: {doc_type}")


def test_unified_handler():
    """Test UnifiedFormatHandler with parse_document."""
    print("\n=== Testing UnifiedFormatHandler ===")

    handler = UnifiedFormatHandler()

    # Test text document
    with open("examples/sample-text.txt", "r") as f:
        content = f.read()
    result = handler.parse_document(content, filename="sample-text.txt")
    print(f"\nText document: {len(result['documents'])} chunks created")

    # Test markdown document
    with open("examples/sample-markdown.md", "r") as f:
        content = f.read()
    result = handler.parse_document(content, filename="sample-markdown.md")
    print(f"Markdown document: {len(result['documents'])} chunks created")

    # Test JSON document
    with open("examples/sample-data.json", "r") as f:
        content = f.read()
    result = handler.parse_document(content, filename="sample-data.json")
    print(f"JSON document: {len(result['documents'])} chunks created")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Document Parser Test Suite")
    print("=" * 60)

    try:
        test_format_detection()
        test_text_parser()
        test_markdown_parser()
        test_json_parser()
        test_unified_handler()

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
