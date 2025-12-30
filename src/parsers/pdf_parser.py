"""
PDF document parser.

Handles PDF files (.pdf), extracting text and chunking by pages or paragraphs.
"""

import re
from typing import List
from io import BytesIO

from src.parsers.document_parser import (
    DocumentParser,
    ParsedGenericDocument,
    DocumentChunk,
    DocumentType,
    extract_title_from_filename,
    count_words,
)


class PDFParser(DocumentParser):
    """
    Parser for PDF documents.

    Handles:
    - PDF files (.pdf)
    - Text extraction from pages
    - Metadata extraction (title, author, etc.)

    Chunking strategy:
    - Page-based chunking (default)
    - Paragraph-based chunking for large pages
    - Preserves page numbers for reference
    """

    def parse(self, content: str, source_file: str = "") -> ParsedGenericDocument:
        """
        Parse PDF content.

        Args:
            content: PDF content (can be string or bytes encoded as string)
            source_file: Original filename

        Returns:
            ParsedGenericDocument with chunks
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError(
                "pypdf is required for PDF parsing. "
                "Install it with: pip install pypdf>=4.0.0"
            )

        # Convert content to bytes if needed
        if isinstance(content, str):
            # If it's a string, it might be base64 or latin-1 encoded
            try:
                content_bytes = content.encode("latin-1")
            except:
                content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        # Create PDF reader
        try:
            pdf_file = BytesIO(content_bytes)
            reader = PdfReader(pdf_file)
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {str(e)}")

        # Extract metadata
        metadata = self._extract_metadata(reader)
        title = metadata.get("title") or extract_title_from_filename(source_file)
        author = metadata.get("author")
        page_count = len(reader.pages)

        # Extract text from all pages
        pages_text = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()
                pages_text.append({
                    "page_number": page_num,
                    "text": text,
                })
            except Exception as e:
                # If text extraction fails for a page, log and continue
                pages_text.append({
                    "page_number": page_num,
                    "text": f"[Error extracting text from page {page_num}: {str(e)}]",
                })

        # Combine all text
        full_text = "\n\n".join(
            f"[Page {p['page_number']}]\n{p['text']}"
            for p in pages_text
        )

        # Chunk the PDF
        chunks = self._chunk_pdf(pages_text)

        # Calculate statistics
        word_count = count_words(full_text)

        return ParsedGenericDocument(
            title=title,
            content=full_text,
            chunks=chunks,
            document_type=DocumentType.PDF,
            source_file=source_file,
            page_count=page_count,
            word_count=word_count,
            character_count=len(full_text),
            author=author,
            metadata=metadata,
        )

    def can_parse(self, content: str, filename: str = "") -> bool:
        """Check if this parser can handle the content."""
        # Check filename extension
        if filename and filename.lower().endswith(".pdf"):
            return True

        # Check for PDF magic bytes
        if isinstance(content, str):
            return content.startswith("%PDF")
        elif isinstance(content, bytes):
            return content.startswith(b"%PDF")

        return False

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return [".pdf"]

    def _extract_metadata(self, reader) -> dict:
        """Extract metadata from PDF."""
        metadata = {}

        try:
            if reader.metadata:
                # Extract common metadata fields
                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title

                if reader.metadata.author:
                    metadata["author"] = reader.metadata.author

                if reader.metadata.subject:
                    metadata["subject"] = reader.metadata.subject

                if reader.metadata.creator:
                    metadata["creator"] = reader.metadata.creator

                if reader.metadata.producer:
                    metadata["producer"] = reader.metadata.producer

                if reader.metadata.creation_date:
                    metadata["created_date"] = str(reader.metadata.creation_date)

                if reader.metadata.modification_date:
                    metadata["modified_date"] = str(reader.metadata.modification_date)
        except:
            pass

        return metadata

    def _chunk_pdf(self, pages_text: List[dict]) -> List[DocumentChunk]:
        """
        Chunk PDF content.

        Strategy:
        - Default: One chunk per page
        - For large pages (>2000 chars): Split into paragraphs
        - Preserve page numbers in metadata
        """
        chunks = []
        chunk_index = 0

        for page_data in pages_text:
            page_num = page_data["page_number"]
            text = page_data["text"].strip()

            if not text:
                continue

            # If page is small enough, keep as one chunk
            if len(text) <= 2000:
                chunk = DocumentChunk(
                    content=text,
                    chunk_index=chunk_index,
                    page_number=page_num,
                    metadata={"page_number": page_num},
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # Page is too large - split by paragraphs
                paragraphs = re.split(r"\n\s*\n", text)
                current_chunk_text = ""

                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue

                    # If adding this paragraph exceeds limit, save current chunk
                    if current_chunk_text and len(current_chunk_text) + len(para) > 1500:
                        chunk = DocumentChunk(
                            content=current_chunk_text.strip(),
                            chunk_index=chunk_index,
                            page_number=page_num,
                            metadata={"page_number": page_num},
                        )
                        chunks.append(chunk)
                        chunk_index += 1

                        # Start new chunk
                        current_chunk_text = para
                    else:
                        # Add paragraph to current chunk
                        current_chunk_text += "\n\n" + para if current_chunk_text else para

                # Don't forget last chunk from this page
                if current_chunk_text.strip():
                    chunk = DocumentChunk(
                        content=current_chunk_text.strip(),
                        chunk_index=chunk_index,
                        page_number=page_num,
                        metadata={"page_number": page_num},
                    )
                    chunks.append(chunk)
                    chunk_index += 1

        return chunks
