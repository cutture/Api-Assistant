"""
Text and Markdown document parser.

Handles plain text (.txt) and Markdown (.md) files, chunking them appropriately
for vector storage and search.
"""

import re
from typing import List

from src.parsers.document_parser import (
    DocumentParser,
    ParsedGenericDocument,
    DocumentChunk,
    DocumentType,
    extract_title_from_filename,
    count_words,
)


class TextParser(DocumentParser):
    """
    Parser for plain text and Markdown documents.

    Handles:
    - Plain text files (.txt)
    - Markdown files (.md, .markdown)

    Chunking strategy:
    - For Markdown: Split by headers (##, ###, etc.)
    - For plain text: Split by paragraphs or fixed size
    """

    def parse(self, content: str, source_file: str = "") -> ParsedGenericDocument:
        """
        Parse text or markdown content.

        Args:
            content: Text content
            source_file: Original filename

        Returns:
            ParsedGenericDocument with chunks
        """
        # Detect if it's Markdown or plain text
        is_markdown = self._is_markdown(content)
        doc_type = DocumentType.MARKDOWN if is_markdown else DocumentType.TEXT

        # Extract title
        title = self._extract_title(content, source_file, is_markdown)

        # Chunk the content
        if is_markdown:
            chunks = self._chunk_markdown(content)
        else:
            chunks = self._chunk_plain_text(content)

        # Calculate statistics
        word_count = count_words(content)
        char_count = len(content)

        return ParsedGenericDocument(
            title=title,
            content=content,
            chunks=chunks,
            document_type=doc_type,
            source_file=source_file,
            word_count=word_count,
            character_count=char_count,
        )

    def can_parse(self, content: str, filename: str = "") -> bool:
        """Check if this parser can handle the content."""
        if filename:
            ext = filename.lower()
            if ext.endswith((".txt", ".text", ".md", ".markdown")):
                return True

        # Check if it's readable text
        try:
            # If it can be read as text and has reasonable printable ratio
            printable_ratio = sum(c.isprintable() or c in "\n\r\t" for c in content[:1000]) / min(len(content), 1000)
            return printable_ratio > 0.8
        except:
            return False

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return [".txt", ".text", ".md", ".markdown"]

    def _is_markdown(self, content: str) -> bool:
        """Check if content appears to be Markdown."""
        markdown_patterns = [
            r"^#{1,6}\s",  # Headers
            r"\[.*\]\(.*\)",  # Links
            r"^\*\s",  # Unordered lists
            r"^\d+\.\s",  # Ordered lists
            r"```",  # Code blocks
            r"^\>",  # Blockquotes
            r"\*\*.*\*\*",  # Bold
            r"__.*__",  # Bold
            r"\*.*\*",  # Italic
        ]

        matches = sum(
            1 for pattern in markdown_patterns
            if re.search(pattern, content, re.MULTILINE)
        )

        return matches >= 2

    def _extract_title(self, content: str, filename: str, is_markdown: bool) -> str:
        """Extract title from content or filename."""
        if is_markdown:
            # Try to find first H1 header
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        # Fall back to filename
        if filename:
            return extract_title_from_filename(filename)

        # Last resort: use first line or "Untitled"
        first_line = content.split("\n")[0].strip()
        if first_line and len(first_line) < 100:
            return first_line

        return "Untitled Document"

    def _chunk_markdown(self, content: str) -> List[DocumentChunk]:
        """
        Chunk Markdown content by sections (headers).

        Strategy:
        - Split by headers (##, ###, etc.)
        - Keep header with its content
        - If section is too large, sub-chunk it
        """
        chunks = []
        chunk_index = 0

        # Split by headers (## or ###)
        sections = re.split(r"(^#{2,6}\s+.+$)", content, flags=re.MULTILINE)

        current_section = ""
        current_header = None

        for i, section in enumerate(sections):
            # Check if this is a header
            header_match = re.match(r"^(#{2,6})\s+(.+)$", section)

            if header_match:
                # Save previous section if exists
                if current_section.strip():
                    chunks.extend(
                        self._create_chunks_from_section(
                            current_section,
                            chunk_index,
                            current_header
                        )
                    )
                    chunk_index += len(chunks)

                # Start new section
                current_header = header_match.group(2).strip()
                current_section = section + "\n"
            else:
                # Add to current section
                current_section += section

        # Don't forget the last section
        if current_section.strip():
            chunks.extend(
                self._create_chunks_from_section(
                    current_section,
                    chunk_index,
                    current_header
                )
            )

        # If no chunks were created (no headers), chunk the whole content
        if not chunks:
            chunks = self.chunk_text(content, chunk_size=1000, overlap=100)

        return chunks

    def _create_chunks_from_section(
        self,
        section: str,
        start_index: int,
        header: str = None
    ) -> List[DocumentChunk]:
        """Create chunks from a markdown section."""
        # If section is small enough, keep as one chunk
        if len(section) <= 1500:
            return [
                DocumentChunk(
                    content=section.strip(),
                    chunk_index=start_index,
                    section_title=header,
                    metadata={"section": header} if header else {},
                )
            ]

        # Otherwise, split into smaller chunks
        sub_chunks = self.chunk_text(
            section,
            chunk_size=1000,
            overlap=100,
            section_title=header
        )

        # Update chunk indices
        for i, chunk in enumerate(sub_chunks):
            chunk.chunk_index = start_index + i

        return sub_chunks

    def _chunk_plain_text(self, content: str) -> List[DocumentChunk]:
        """
        Chunk plain text content.

        Strategy:
        - Split by paragraphs (double newline)
        - Group paragraphs into chunks of ~1000 chars
        - Maintain some overlap for context
        """
        # Try to split by paragraphs first
        paragraphs = re.split(r"\n\s*\n", content)

        if len(paragraphs) > 1:
            # Group paragraphs into chunks
            chunks = []
            current_chunk = ""
            chunk_index = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # If adding this paragraph exceeds limit, save current chunk
                if current_chunk and len(current_chunk) + len(para) > 1000:
                    chunks.append(
                        DocumentChunk(
                            content=current_chunk.strip(),
                            chunk_index=chunk_index,
                        )
                    )
                    chunk_index += 1

                    # Start new chunk with overlap (last sentence of previous)
                    sentences = current_chunk.split(". ")
                    if len(sentences) > 1:
                        current_chunk = sentences[-1] + ". " + para
                    else:
                        current_chunk = para
                else:
                    # Add paragraph to current chunk
                    current_chunk += "\n\n" + para if current_chunk else para

            # Don't forget last chunk
            if current_chunk.strip():
                chunks.append(
                    DocumentChunk(
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                    )
                )

            return chunks
        else:
            # No clear paragraphs, use fixed-size chunking
            return self.chunk_text(content, chunk_size=1000, overlap=100)
