"""
Base parser interface and data models for general document parsing.

This module provides infrastructure for parsing non-API documents like PDFs,
text files, Markdown, JSON, CSV, and DOCX files.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class DocumentType(Enum):
    """Supported general document types."""

    # API Specifications (for compatibility)
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    POSTMAN = "postman"

    # General Documents
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON_GENERIC = "json_generic"
    CSV = "csv"
    DOCX = "docx"
    HTML = "html"
    UNKNOWN = "unknown"


@dataclass
class DocumentChunk:
    """
    Represents a chunk of a document.
    Documents are split into chunks for embedding and vector storage.
    """

    content: str
    chunk_index: int  # Position in document (0-based)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional chunk-specific metadata
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None

    def to_vector_document(self, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert chunk to vector store document format.

        Args:
            base_metadata: Document-level metadata to merge with chunk metadata

        Returns:
            Dict with 'content' and 'metadata' keys
        """
        # Merge base metadata with chunk-specific metadata
        merged_metadata = {**base_metadata}

        # Add chunk-specific fields
        merged_metadata["chunk_index"] = self.chunk_index

        if self.page_number is not None:
            merged_metadata["page_number"] = self.page_number

        if self.section_title:
            merged_metadata["section_title"] = self.section_title

        if self.start_char is not None:
            merged_metadata["start_char"] = self.start_char

        if self.end_char is not None:
            merged_metadata["end_char"] = self.end_char

        # Add any additional chunk metadata
        merged_metadata.update(self.metadata)

        return {
            "content": self.content,
            "metadata": merged_metadata,
        }


@dataclass
class ParsedGenericDocument:
    """
    Represents a fully parsed general document.

    This is the counterpart to ParsedDocument (for API specs) but for
    general documents like PDFs, text files, etc.
    """

    title: str
    content: str  # Full document content
    chunks: List[DocumentChunk] = field(default_factory=list)
    document_type: DocumentType = DocumentType.UNKNOWN
    source_file: str = ""

    # Document metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Type-specific metadata (optional)
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    file_size: Optional[int] = None
    author: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    def get_base_metadata(self) -> Dict[str, Any]:
        """
        Generate base metadata that will be included in all chunks.

        Returns:
            Dict with document-level metadata
        """
        base = {
            "content_type": "general_document",
            "document_type": self.document_type.value,
            "title": self.title,
            "source_file": self.source_file,
            "chunk_count": len(self.chunks),
        }

        # Add optional metadata if available
        if self.page_count is not None:
            base["page_count"] = self.page_count

        if self.word_count is not None:
            base["word_count"] = self.word_count

        if self.author:
            base["author"] = self.author

        if self.created_date:
            base["created_date"] = self.created_date

        # Add any additional metadata
        base.update(self.metadata)

        return base

    def to_vector_documents(self) -> List[Dict[str, Any]]:
        """
        Convert document to vector store format.

        Returns:
            List of documents ready for vector store indexing
        """
        base_metadata = self.get_base_metadata()

        return [
            chunk.to_vector_document(base_metadata)
            for chunk in self.chunks
        ]

    def get_summary(self, max_length: int = 500) -> str:
        """
        Get a summary of the document.

        Args:
            max_length: Maximum summary length

        Returns:
            Document summary string
        """
        lines = [f"# {self.title}"]

        if self.document_type != DocumentType.UNKNOWN:
            lines.append(f"**Type**: {self.document_type.value}")

        if self.page_count is not None:
            lines.append(f"**Pages**: {self.page_count}")

        if self.word_count is not None:
            lines.append(f"**Words**: {self.word_count}")

        lines.append(f"**Chunks**: {len(self.chunks)}")

        # Add excerpt from first chunk
        if self.chunks:
            first_content = self.chunks[0].content
            excerpt = first_content[:max_length] + "..." if len(first_content) > max_length else first_content
            lines.append(f"\n**Excerpt**:\n{excerpt}")

        return "\n".join(lines)


class DocumentParser(ABC):
    """
    Abstract base class for general document parsers.

    This is separate from BaseParser (which is for API specs) and provides
    a similar interface for general documents.
    """

    @abstractmethod
    def parse(self, content: str, source_file: str = "") -> ParsedGenericDocument:
        """
        Parse document content.

        Args:
            content: Raw document content (text, binary encoded as string, etc.)
            source_file: Original file path/name for reference

        Returns:
            ParsedGenericDocument with content, chunks, and metadata
        """
        pass

    @abstractmethod
    def can_parse(self, content: str, filename: str = "") -> bool:
        """
        Check if this parser can handle the given content.

        Args:
            content: Raw content string or bytes
            filename: Optional filename for extension-based detection

        Returns:
            True if this parser can handle the content
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List of extensions (e.g., ['.pdf', '.txt'])
        """
        pass

    def parse_file(self, file_path: str) -> ParsedGenericDocument:
        """
        Parse a document file.

        Args:
            file_path: Path to the file

        Returns:
            ParsedGenericDocument with all extracted information
        """
        with open(file_path, "rb") as f:
            content = f.read()

        # Try to decode as string, or keep as bytes
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content.decode("latin-1")  # Fallback encoding

        return self.parse(content_str, source_file=file_path)

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 100,
        **kwargs
    ) -> List[DocumentChunk]:
        """
        Default text chunking strategy.

        Args:
            text: Text to chunk
            chunk_size: Target size for each chunk (characters)
            overlap: Overlap between chunks (characters)
            **kwargs: Additional metadata for chunks

        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary if possible
            if end < len(text):
                # Look for sentence endings
                sentence_end = max(
                    text.rfind(". ", start, end),
                    text.rfind("! ", start, end),
                    text.rfind("? ", start, end),
                    text.rfind("\n\n", start, end),
                )

                if sentence_end > start:
                    end = sentence_end + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata=kwargs,
                )
                chunks.append(chunk)
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - overlap if end < len(text) else end

        return chunks


# Utility functions for document parsing

def detect_encoding(content: bytes) -> str:
    """
    Detect text encoding using chardet.

    Args:
        content: Raw bytes

    Returns:
        Detected encoding name (e.g., 'utf-8', 'ascii')
    """
    try:
        import chardet
        result = chardet.detect(content)
        return result.get("encoding", "utf-8") or "utf-8"
    except ImportError:
        return "utf-8"


def count_words(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Input text

    Returns:
        Number of words
    """
    return len(text.split())


def extract_title_from_filename(filename: str) -> str:
    """
    Extract a readable title from filename.

    Args:
        filename: File name (with or without extension)

    Returns:
        Cleaned title
    """
    import os

    # Remove extension
    name = os.path.splitext(os.path.basename(filename))[0]

    # Replace underscores and hyphens with spaces
    name = name.replace("_", " ").replace("-", " ")

    # Capitalize words
    return name.title()
