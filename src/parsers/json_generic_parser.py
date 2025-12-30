"""
Generic JSON document parser.

Handles JSON files that are not API specifications (OpenAPI, Postman).
This includes data files, configuration files, and other JSON documents.
"""

import json
from typing import List, Any, Dict

from src.parsers.document_parser import (
    DocumentParser,
    ParsedGenericDocument,
    DocumentChunk,
    DocumentType,
    extract_title_from_filename,
)


class JSONGenericParser(DocumentParser):
    """
    Parser for generic JSON documents.

    Handles any valid JSON file that is not an API specification.

    Chunking strategy:
    - For flat JSON: Chunk by top-level keys
    - For nested JSON: Chunk by major sections
    - For arrays: Chunk by array elements (grouped)
    """

    def parse(self, content: str, source_file: str = "") -> ParsedGenericDocument:
        """
        Parse generic JSON content.

        Args:
            content: JSON string content
            source_file: Original filename

        Returns:
            ParsedGenericDocument with chunks
        """
        # Parse JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

        # Extract title
        title = self._extract_title(data, source_file)

        # Chunk the JSON
        chunks = self._chunk_json(data)

        return ParsedGenericDocument(
            title=title,
            content=content,
            chunks=chunks,
            document_type=DocumentType.JSON_GENERIC,
            source_file=source_file,
            metadata={
                "json_type": self._get_json_type(data),
                "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
            },
        )

    def can_parse(self, content: str, filename: str = "") -> bool:
        """Check if this parser can handle the content."""
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return [".json"]

    def _extract_title(self, data: Any, filename: str) -> str:
        """Extract title from JSON data or filename."""
        # Try common title fields
        if isinstance(data, dict):
            title_fields = ["title", "name", "label", "id", "key"]
            for field in title_fields:
                if field in data and isinstance(data[field], str):
                    return data[field]

        # Fall back to filename
        if filename:
            return extract_title_from_filename(filename)

        return "JSON Document"

    def _get_json_type(self, data: Any) -> str:
        """Determine the type of JSON structure."""
        if isinstance(data, dict):
            return "object"
        elif isinstance(data, list):
            return "array"
        else:
            return "primitive"

    def _chunk_json(self, data: Any) -> List[DocumentChunk]:
        """
        Chunk JSON data intelligently.

        Strategy depends on JSON structure:
        - Object: Chunk by top-level keys
        - Array: Chunk by elements (grouped)
        - Nested: Recursively chunk large sections
        """
        chunks = []

        if isinstance(data, dict):
            chunks = self._chunk_object(data)
        elif isinstance(data, list):
            chunks = self._chunk_array(data)
        else:
            # Single primitive value - create one chunk
            chunks = [
                DocumentChunk(
                    content=json.dumps(data, indent=2),
                    chunk_index=0,
                    metadata={"json_type": "primitive"},
                )
            ]

        return chunks

    def _chunk_object(self, obj: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk a JSON object by top-level keys."""
        chunks = []
        chunk_index = 0

        for key, value in obj.items():
            # Create a chunk for this key-value pair
            chunk_data = {key: value}
            chunk_json = json.dumps(chunk_data, indent=2)

            # If this chunk is too large, try to sub-chunk it
            if len(chunk_json) > 2000 and isinstance(value, (dict, list)):
                # Recursively chunk the value
                sub_chunks = self._chunk_json(value)
                for sub_chunk in sub_chunks:
                    # Prepend the key context
                    sub_chunk.content = f"Key: {key}\n\n{sub_chunk.content}"
                    sub_chunk.chunk_index = chunk_index
                    sub_chunk.metadata["parent_key"] = key
                    chunks.append(sub_chunk)
                    chunk_index += 1
            else:
                # Keep as single chunk
                chunk = DocumentChunk(
                    content=chunk_json,
                    chunk_index=chunk_index,
                    metadata={
                        "key": key,
                        "value_type": type(value).__name__,
                    },
                )
                chunks.append(chunk)
                chunk_index += 1

        return chunks

    def _chunk_array(self, arr: List[Any]) -> List[DocumentChunk]:
        """Chunk a JSON array by grouping elements."""
        chunks = []
        chunk_index = 0

        # Group array elements into chunks of ~10 items or ~1000 chars
        current_group = []
        current_size = 0

        for item in arr:
            item_json = json.dumps(item, indent=2)
            item_size = len(item_json)

            # Check if adding this item would exceed limits
            if current_group and (
                len(current_group) >= 10 or current_size + item_size > 1000
            ):
                # Save current group as chunk
                chunk_content = json.dumps(current_group, indent=2)
                chunk = DocumentChunk(
                    content=f"Array elements {chunk_index * 10} to {chunk_index * 10 + len(current_group) - 1}:\n\n{chunk_content}",
                    chunk_index=chunk_index,
                    metadata={
                        "array_start_index": chunk_index * 10,
                        "array_element_count": len(current_group),
                    },
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new group
                current_group = [item]
                current_size = item_size
            else:
                current_group.append(item)
                current_size += item_size

        # Don't forget last group
        if current_group:
            chunk_content = json.dumps(current_group, indent=2)
            chunk = DocumentChunk(
                content=f"Array elements {chunk_index * 10} to {chunk_index * 10 + len(current_group) - 1}:\n\n{chunk_content}",
                chunk_index=chunk_index,
                metadata={
                    "array_start_index": chunk_index * 10,
                    "array_element_count": len(current_group),
                },
            )
            chunks.append(chunk)

        return chunks
