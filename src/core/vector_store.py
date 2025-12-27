"""
Vector store service using ChromaDB for document storage and retrieval.
Provides semantic search capabilities for API documentation.
Includes performance monitoring and hybrid search (BM25 + Vector).
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.core.embeddings import EmbeddingService, get_embedding_service
from src.core.hybrid_search import (
    BM25,
    HybridSearch,
    SearchResult,
    create_bm25_index,
    get_hybrid_search,
)
from src.core.performance import monitor_performance

logger = structlog.get_logger(__name__)


class VectorStore:
    """
    ChromaDB-based vector store for API documentation.

    Features:
    - Persistent storage to disk
    - Metadata filtering
    - Semantic similarity search (vector embeddings)
    - BM25 keyword search (traditional IR)
    - Hybrid search (BM25 + Vector with RRF fusion)
    - Duplicate detection via content hashing
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
        enable_hybrid_search: bool = True,
    ):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection.
            persist_directory: Directory for persistent storage.
            embedding_service: Service for generating embeddings.
            enable_hybrid_search: Enable BM25 + Vector hybrid search (default: True).
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.embedding_service = embedding_service or get_embedding_service()
        self.enable_hybrid_search = enable_hybrid_search

        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[chromadb.Collection] = None
        self._bm25: Optional[BM25] = None  # BM25 index for keyword search
        self._hybrid_search: Optional[HybridSearch] = None  # Hybrid search strategy
        self._documents_cache: List[Dict[str, Any]] = []  # Cache for BM25 indexing

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

    def _rebuild_bm25_index(self):
        """Rebuild BM25 index from all documents in the collection."""
        if not self.enable_hybrid_search:
            return

        logger.info("Rebuilding BM25 index")

        # Get all documents from ChromaDB
        all_docs = self.collection.get(include=["documents", "metadatas"])

        if not all_docs["ids"]:
            logger.warning("No documents found, BM25 index empty")
            self._bm25 = None
            self._documents_cache = []
            return

        # Build documents cache
        self._documents_cache = []
        for i, doc_id in enumerate(all_docs["ids"]):
            self._documents_cache.append({
                "id": doc_id,
                "content": all_docs["documents"][i],
                "metadata": all_docs["metadatas"][i],
            })

        # Create and fit BM25 index
        self._bm25 = create_bm25_index(self._documents_cache)
        self._hybrid_search = get_hybrid_search()

        logger.info("BM25 index rebuilt", document_count=len(self._documents_cache))

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

        # Rebuild BM25 index if hybrid search is enabled
        if self.enable_hybrid_search:
            self._rebuild_bm25_index()

        logger.debug("Added document", doc_id=doc_id, metadata=metadata)
        return doc_id

    @monitor_performance("vector_store_add_documents")
    def add_documents(
        self,
        documents: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> list[str]:
        """
        Add multiple documents to the vector store with performance monitoring.

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

        # Rebuild BM25 index if hybrid search is enabled
        if self.enable_hybrid_search:
            self._rebuild_bm25_index()

        return doc_ids

    @monitor_performance("vector_store_search")
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
        where_document: Optional[dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents with performance monitoring.

        Supports three search modes:
        1. Vector-only search (use_hybrid=False or hybrid disabled)
        2. Hybrid search (use_hybrid=True and hybrid enabled) - RECOMMENDED

        Args:
            query: The search query.
            n_results: Maximum number of results to return.
            where: Metadata filter conditions.
            where_document: Document content filter conditions.
            use_hybrid: Use hybrid search if available (default: True).

        Returns:
            List of search results with content, metadata, and similarity score.
        """
        # Determine search mode
        use_hybrid_mode = use_hybrid and self.enable_hybrid_search and self._bm25 is not None

        if use_hybrid_mode:
            return self._hybrid_search_impl(query, n_results, where, where_document)
        else:
            return self._vector_search_impl(query, n_results, where, where_document)

    def _vector_search_impl(
        self,
        query: str,
        n_results: int,
        where: Optional[dict[str, Any]] = None,
        where_document: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Pure vector similarity search."""
        logger.debug("Vector search", query=query[:50], n_results=n_results)

        # Generate query embedding (cached)
        query_embedding = self.embedding_service.embed_query(query)

        # Search ChromaDB
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
                    "method": "vector",
                })

        logger.debug("Vector search completed", result_count=len(formatted_results))
        return formatted_results

    def _hybrid_search_impl(
        self,
        query: str,
        n_results: int,
        where: Optional[dict[str, Any]] = None,
        where_document: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search combining BM25 keyword search and vector similarity search.

        Uses Reciprocal Rank Fusion (RRF) to merge results.
        """
        logger.debug("Hybrid search", query=query[:50], n_results=n_results)

        # 1. Get vector search results
        vector_results = self._vector_search_impl(
            query, n_results=n_results * 2, where=where, where_document=where_document
        )

        # Convert to SearchResult objects
        vector_search_results = [
            SearchResult(
                doc_id=r["id"],
                content=r["content"],
                metadata=r["metadata"],
                score=r["score"],
                method="vector",
            )
            for r in vector_results
        ]

        # 2. Get BM25 search results
        bm25_results = []
        if self._bm25:
            bm25_raw = self._bm25.search(query, top_k=n_results * 2)
            bm25_results = [(doc_id, score) for doc_id, score in bm25_raw]

        # 3. Merge using Reciprocal Rank Fusion
        if not self._hybrid_search:
            self._hybrid_search = get_hybrid_search()

        merged = self._hybrid_search.reciprocal_rank_fusion(
            bm25_results=bm25_results,
            vector_results=vector_search_results,
            k=60,
        )

        # 4. Format final results
        formatted_results = []
        doc_map = {r.doc_id: r for r in vector_search_results}

        # Add BM25-only results to map
        for doc_id, _ in bm25_results:
            if doc_id not in doc_map:
                # Get document from cache
                for cached_doc in self._documents_cache:
                    if cached_doc["id"] == doc_id:
                        doc_map[doc_id] = SearchResult(
                            doc_id=doc_id,
                            content=cached_doc["content"],
                            metadata=cached_doc["metadata"],
                            score=0.0,  # Will use RRF score
                            method="bm25",
                        )
                        break

        for doc_id, rrf_score in merged[:n_results]:
            if doc_id in doc_map:
                result = doc_map[doc_id]
                formatted_results.append({
                    "id": result.doc_id,
                    "content": result.content,
                    "metadata": result.metadata,
                    "score": rrf_score,  # Use RRF score
                    "method": "hybrid",
                    "original_method": result.method,
                })

        logger.debug(
            "Hybrid search completed",
            result_count=len(formatted_results),
            bm25_count=len(bm25_results),
            vector_count=len(vector_search_results),
        )

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

        # Rebuild BM25 index
        if self.enable_hybrid_search:
            self._rebuild_bm25_index()

        return True

    def clear(self) -> None:
        """Delete all documents from the collection."""
        logger.warning("Clearing all documents from collection", name=self.collection_name)
        self.client.delete_collection(self.collection_name)
        self._collection = None
        self._bm25 = None
        self._documents_cache = []

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        stats = {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "persist_directory": self.persist_directory,
            "hybrid_search_enabled": self.enable_hybrid_search,
        }

        if self.enable_hybrid_search and self._bm25:
            stats["bm25_indexed_documents"] = len(self._documents_cache)

        return stats


# Convenience function
def get_vector_store(enable_hybrid_search: bool = True) -> VectorStore:
    """
    Get a VectorStore instance with default settings.

    Args:
        enable_hybrid_search: Enable BM25 + Vector hybrid search (default: True).

    Returns:
        VectorStore instance.
    """
    return VectorStore(enable_hybrid_search=enable_hybrid_search)
