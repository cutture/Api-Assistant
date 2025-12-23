"""
Vector store service using ChromaDB for document storage and retrieval.
Provides semantic search capabilities for API documentation.
"""

import hashlib
from pathlib import Path
from typing import Any, Optional

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.core.embeddings import EmbeddingService, get_embedding_service

logger = structlog.get_logger(__name__)


class VectorStore:
    """
    ChromaDB-based vector store for API documentation.
    
    Features:
    - Persistent storage to disk
    - Metadata filtering
    - Semantic similarity search
    - Duplicate detection via content hashing
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection.
            persist_directory: Directory for persistent storage.
            embedding_service: Service for generating embeddings.
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.embedding_service = embedding_service or get_embedding_service()
        
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[chromadb.Collection] = None

    @property
    def client(self) -> chromadb.PersistentClient:
        """Get or create the ChromaDB client."""
        if self._client is None:
            # Ensure directory exists
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            logger.info("Initializing ChromaDB client", persist_dir=self.persist_directory)
            
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the collection."""
        if self._collection is None:
            logger.info("Getting/creating collection", name=self.collection_name)
            
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "API documentation chunks"},
            )
        return self._collection

    @staticmethod
    def _generate_content_hash(content: str) -> str:
        """Generate a hash for content deduplication."""
        return hashlib.md5(content.encode()).hexdigest()

    def add_document(
        self,
        content: str,
        metadata: dict[str, Any],
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Add a single document to the vector store.

        Args:
            content: The text content to store.
            metadata: Associated metadata (e.g., endpoint, method, source_file).
            doc_id: Optional document ID. Generated from content hash if not provided.

        Returns:
            The document ID.
        """
        if not content.strip():
            raise ValueError("Content cannot be empty")

        # Generate ID from content hash if not provided
        if doc_id is None:
            doc_id = self._generate_content_hash(content)

        # Check for duplicate
        existing = self.collection.get(ids=[doc_id])
        if existing["ids"]:
            logger.debug("Document already exists, skipping", doc_id=doc_id)
            return doc_id

        # Generate embedding
        embedding = self.embedding_service.embed_text(content)

        # Add to collection
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )

        logger.debug("Added document", doc_id=doc_id, metadata=metadata)
        return doc_id

    def add_documents(
        self,
        documents: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> list[str]:
        """
        Add multiple documents to the vector store.

        Args:
            documents: List of dicts with 'content' and 'metadata' keys.
            batch_size: Number of documents to process at once.

        Returns:
            List of document IDs.
        """
        if not documents:
            return []

        logger.info("Adding documents to vector store", count=len(documents))

        doc_ids = []
        contents = []
        metadatas = []

        for doc in documents:
            content = doc["content"]
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id") or self._generate_content_hash(content)

            doc_ids.append(doc_id)
            contents.append(content)
            metadatas.append(metadata)

        # Generate embeddings in batch
        embeddings = self.embedding_service.embed_texts(contents, batch_size=batch_size)

        # Filter out existing documents
        existing = self.collection.get(ids=doc_ids)
        existing_ids = set(existing["ids"])

        new_indices = [i for i, doc_id in enumerate(doc_ids) if doc_id not in existing_ids]
        
        if not new_indices:
            logger.info("All documents already exist, skipping")
            return doc_ids

        # Add only new documents
        new_ids = [doc_ids[i] for i in new_indices]
        new_embeddings = [embeddings[i] for i in new_indices]
        new_contents = [contents[i] for i in new_indices]
        new_metadatas = [metadatas[i] for i in new_indices]

        # Add in batches
        for i in range(0, len(new_ids), batch_size):
            batch_end = min(i + batch_size, len(new_ids))
            self.collection.add(
                ids=new_ids[i:batch_end],
                embeddings=new_embeddings[i:batch_end],
                documents=new_contents[i:batch_end],
                metadatas=new_metadatas[i:batch_end],
            )

        logger.info(
            "Documents added successfully",
            new_count=len(new_ids),
            skipped_count=len(doc_ids) - len(new_ids),
        )

        return doc_ids

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
        where_document: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: The search query.
            n_results: Maximum number of results to return.
            where: Metadata filter conditions.
            where_document: Document content filter conditions.

        Returns:
            List of search results with content, metadata, and similarity score.
        """
        logger.debug("Searching vector store", query=query[:50], n_results=n_results)

        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    # Convert distance to similarity score (1 - normalized distance)
                    "score": 1 - (results["distances"][0][i] / 2),
                })

        logger.debug("Search completed", result_count=len(formatted_results))
        return formatted_results

    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]:
        """
        Get a specific document by ID.

        Args:
            doc_id: The document ID.

        Returns:
            Document dict or None if not found.
        """
        result = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
        
        if result["ids"]:
            return {
                "id": result["ids"][0],
                "content": result["documents"][0],
                "metadata": result["metadatas"][0],
            }
        return None

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: The document ID.

        Returns:
            True if deleted, False if not found.
        """
        existing = self.collection.get(ids=[doc_id])
        if not existing["ids"]:
            return False

        self.collection.delete(ids=[doc_id])
        logger.debug("Deleted document", doc_id=doc_id)
        return True

    def clear(self) -> None:
        """Delete all documents from the collection."""
        logger.warning("Clearing all documents from collection", name=self.collection_name)
        self.client.delete_collection(self.collection_name)
        self._collection = None

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        return {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "persist_directory": self.persist_directory,
        }


# Convenience function
def get_vector_store() -> VectorStore:
    """Get a VectorStore instance with default settings."""
    return VectorStore()
