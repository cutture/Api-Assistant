"""
Vector store service using ChromaDB for document storage and retrieval.
Provides semantic search capabilities for API documentation.
Includes performance monitoring and hybrid search (BM25 + Vector).
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.core.advanced_filtering import (
    FacetResult,
    FacetedSearch,
    Filter,
)
from src.core.cross_encoder import CrossEncoderReranker
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
    - Cross-encoder re-ranking for improved accuracy
    - Duplicate detection via content hashing
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
        enable_hybrid_search: bool = True,
        enable_reranker: bool = False,
        reranker_model: str = "ms-marco-mini-lm-6",
    ):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection.
            persist_directory: Directory for persistent storage.
            embedding_service: Service for generating embeddings.
            enable_hybrid_search: Enable BM25 + Vector hybrid search (default: True).
            enable_reranker: Enable cross-encoder re-ranking (default: False, lazy loaded).
            reranker_model: Cross-encoder model to use for re-ranking.
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.embedding_service = embedding_service or get_embedding_service()
        self.enable_hybrid_search = enable_hybrid_search
        self.enable_reranker = enable_reranker
        self.reranker_model = reranker_model

        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[chromadb.Collection] = None
        self._bm25: Optional[BM25] = None  # BM25 index for keyword search
        self._hybrid_search: Optional[HybridSearch] = None  # Hybrid search strategy
        self._reranker: Optional[CrossEncoderReranker] = None  # Cross-encoder re-ranker
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
    ) -> dict[str, Any]:
        """
        Add multiple documents to the vector store with performance monitoring.

        Args:
            documents: List of dicts with 'content' and 'metadata' keys.
            batch_size: Number of documents to process at once.

        Returns:
            Dictionary with document_ids (all IDs), new_count, and skipped_count.
        """
        if not documents:
            return {"document_ids": [], "new_count": 0, "skipped_count": 0}

        logger.info("Adding documents to vector store", count=len(documents))

        doc_ids = []
        contents = []
        metadatas = []
        seen_ids = set()  # Track IDs in current batch to avoid duplicates
        batch_duplicates = 0

        for doc in documents:
            content = doc["content"]
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id") or self._generate_content_hash(content)

            # Skip if this ID already exists in the current batch
            if doc_id in seen_ids:
                batch_duplicates += 1
                logger.debug("Skipping duplicate ID in batch", doc_id=doc_id)
                continue

            seen_ids.add(doc_id)
            doc_ids.append(doc_id)
            contents.append(content)
            metadatas.append(metadata)

        if batch_duplicates > 0:
            logger.info(
                "Removed duplicate IDs from batch",
                duplicates=batch_duplicates,
                unique_documents=len(doc_ids)
            )

        # Generate embeddings in batch
        embeddings = self.embedding_service.embed_texts(contents, batch_size=batch_size)

        # Filter out existing documents
        existing = self.collection.get(ids=doc_ids)
        existing_ids = set(existing["ids"])

        new_indices = [i for i, doc_id in enumerate(doc_ids) if doc_id not in existing_ids]

        if not new_indices:
            logger.info("All documents already exist, skipping")
            return {
                "document_ids": doc_ids,
                "new_count": 0,
                "skipped_count": len(doc_ids) + batch_duplicates,
            }

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

        # Calculate total skipped: existing docs + batch duplicates
        total_skipped = (len(doc_ids) - len(new_ids)) + batch_duplicates

        logger.info(
            "Documents added successfully",
            new_count=len(new_ids),
            skipped_existing=len(doc_ids) - len(new_ids),
            skipped_batch_duplicates=batch_duplicates,
            total_skipped=total_skipped,
        )

        # Rebuild BM25 index if hybrid search is enabled
        if self.enable_hybrid_search:
            self._rebuild_bm25_index()

        return {
            "document_ids": doc_ids,
            "new_count": len(new_ids),
            "skipped_count": total_skipped,
        }

    @monitor_performance("vector_store_search")
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Union[dict[str, Any], Filter]] = None,
        where_document: Optional[dict[str, Any]] = None,
        use_hybrid: bool = True,
        use_reranker: bool = False,
        rerank_top_k: Optional[int] = None,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents with performance monitoring.

        Supports multiple search modes:
        1. Vector-only search (use_hybrid=False)
        2. Hybrid search (use_hybrid=True) - BM25 + Vector with RRF
        3. Re-ranked search (use_reranker=True) - Cross-encoder re-ranking

        Search pipeline:
        - If use_reranker=True: Retrieve candidates → Re-rank with cross-encoder
        - If use_hybrid=True: BM25 + Vector with RRF fusion
        - Otherwise: Pure vector search
        - Filter results by minimum score threshold

        Args:
            query: The search query.
            n_results: Maximum number of results to return.
            where: Metadata filter conditions (dict or Filter object).
            where_document: Document content filter conditions.
            use_hybrid: Use hybrid search if available (default: True).
            use_reranker: Use cross-encoder re-ranking (default: False).
            rerank_top_k: Number of candidates to retrieve before re-ranking (default: n_results * 3).
            min_score: Minimum relevance score threshold (0.0-1.0). Results below this are filtered out (default: 0.0 - disabled).

        Returns:
            List of search results with content, metadata, and similarity score (filtered by min_score).
        """
        # Store original filter object for client-side filtering if needed
        original_filter = where if isinstance(where, Filter) else None

        # Convert Filter object to dict if needed
        where_dict, where_doc_dict = self._process_filters(where, where_document)

        # Determine if we should use re-ranking
        use_reranker_mode = use_reranker and self.enable_reranker

        if use_reranker_mode:
            # Re-ranking pipeline: retrieve more candidates, then re-rank
            if rerank_top_k is None:
                rerank_top_k = max(n_results * 3, 20)  # Retrieve 3x candidates by default

            # Retrieve candidates using hybrid or vector search
            use_hybrid_mode = use_hybrid and self.enable_hybrid_search and self._bm25 is not None

            if use_hybrid_mode:
                candidates = self._hybrid_search_impl(query, rerank_top_k, where_dict, where_doc_dict)
            else:
                candidates = self._vector_search_impl(query, rerank_top_k, where_dict, where_doc_dict)

            # Apply client-side filtering if we have an original filter
            # This catches filters that couldn't be converted to ChromaDB format
            # (e.g., CONTAINS, REGEX, etc.) even if some parts were converted
            if original_filter:
                from src.core.advanced_filtering import FacetedSearch
                candidates = FacetedSearch.apply_client_side_filter(candidates, original_filter)

            # Re-rank with cross-encoder
            results = self._rerank_results(query, candidates, n_results)

            # Filter by minimum score threshold
            filtered_results = [r for r in results if r.get("score", 0) >= min_score]
            logger.debug(
                "Score filtering applied",
                original_count=len(results),
                filtered_count=len(filtered_results),
                min_score=min_score
            )
            return filtered_results
        else:
            # Standard search without re-ranking
            use_hybrid_mode = use_hybrid and self.enable_hybrid_search and self._bm25 is not None

            if use_hybrid_mode:
                results = self._hybrid_search_impl(query, n_results, where_dict, where_doc_dict)
            else:
                results = self._vector_search_impl(query, n_results, where_dict, where_doc_dict)

            # Apply client-side filtering if we have an original filter
            # This catches filters that couldn't be converted to ChromaDB format
            # (e.g., CONTAINS, REGEX, etc.) even if some parts were converted
            if original_filter:
                from src.core.advanced_filtering import FacetedSearch
                results = FacetedSearch.apply_client_side_filter(results, original_filter)

            # Filter by minimum score threshold
            filtered_results = [r for r in results if r.get("score", 0) >= min_score]
            logger.debug(
                "Score filtering applied",
                original_count=len(results),
                filtered_count=len(filtered_results),
                min_score=min_score
            )
            return filtered_results

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

            # Apply client-side filtering to BM25 results if filters are specified
            if where or where_document:
                from src.core.advanced_filtering import FacetedSearch, FilterBuilder

                filtered_bm25 = []
                for doc_id, score in bm25_raw:
                    # Get document metadata and content
                    doc = next((d for d in self._documents_cache if d["id"] == doc_id), None)
                    if doc:
                        # Apply metadata filter
                        if where:
                            # Convert ChromaDB where clause to filter matches
                            if not self._matches_where_clause(doc["metadata"], where):
                                continue

                        # Apply document filter
                        if where_document:
                            if not self._matches_where_document_clause(doc["content"], where_document):
                                continue

                        filtered_bm25.append((doc_id, score))

                bm25_results = filtered_bm25
            else:
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

    def _rerank_results(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results using cross-encoder.

        Args:
            query: Search query
            candidates: List of candidate results
            top_k: Number of top results to return

        Returns:
            Re-ranked results
        """
        if not candidates:
            return []

        # Lazy load cross-encoder
        if self._reranker is None:
            logger.info(
                "Initializing cross-encoder re-ranker",
                model=self.reranker_model,
            )
            self._reranker = CrossEncoderReranker(
                model_name=self.reranker_model,
                use_cache=True,
            )

        # Re-rank
        rerank_results = self._reranker.rerank(query, candidates, top_k)

        # Convert to dict format
        formatted_results = []
        for result in rerank_results:
            formatted_results.append({
                "id": result.doc_id,
                "content": result.content,
                "metadata": result.metadata,
                "score": result.rerank_score,
                "original_score": result.original_score,
                "original_rank": result.original_rank,
                "method": "reranked",
            })

        return formatted_results

    def _process_filters(
        self,
        where: Optional[Union[dict[str, Any], Filter]],
        where_document: Optional[dict[str, Any]],
    ) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]]]:
        """
        Process filter parameters.

        Converts Filter objects to ChromaDB filter dicts.

        Args:
            where: Metadata filter (dict or Filter object)
            where_document: Document content filter (dict)

        Returns:
            Tuple of (where_dict, where_document_dict)
        """
        where_dict = None
        where_doc_dict = where_document

        # Process where parameter
        if where is not None:
            if isinstance(where, Filter):
                # Convert Filter to ChromaDB format
                where_dict = where.to_chroma_where()
                # Also get document filter if any
                filter_doc = where.to_chroma_where_document()
                if filter_doc and not where_doc_dict:
                    where_doc_dict = filter_doc
            else:
                # Already a dict
                where_dict = where

        return where_dict, where_doc_dict

    def _matches_where_clause(
        self,
        metadata: Dict[str, Any],
        where: Dict[str, Any],
    ) -> bool:
        """
        Check if metadata matches a ChromaDB where clause.

        Args:
            metadata: Document metadata
            where: ChromaDB where clause

        Returns:
            True if metadata matches the where clause
        """
        for field, condition in where.items():
            # Handle logical operators
            if field == "$and":
                return all(self._matches_where_clause(metadata, c) for c in condition)
            elif field == "$or":
                return any(self._matches_where_clause(metadata, c) for c in condition)
            elif field == "$not":
                return not self._matches_where_clause(metadata, condition)

            # Handle field conditions
            if field not in metadata:
                return False

            field_value = metadata[field]

            if isinstance(condition, dict):
                # Operator-based condition
                for op, value in condition.items():
                    if op == "$eq":
                        if field_value != value:
                            return False
                    elif op == "$ne":
                        if field_value == value:
                            return False
                    elif op == "$gt":
                        if not (field_value > value):
                            return False
                    elif op == "$gte":
                        if not (field_value >= value):
                            return False
                    elif op == "$lt":
                        if not (field_value < value):
                            return False
                    elif op == "$lte":
                        if not (field_value <= value):
                            return False
                    elif op == "$in":
                        if field_value not in value:
                            return False
                    elif op == "$nin":
                        if field_value in value:
                            return False
                    elif op == "$contains":
                        if value not in str(field_value):
                            return False
                    elif op == "$not_contains":
                        if value in str(field_value):
                            return False
            else:
                # Direct equality
                if field_value != condition:
                    return False

        return True

    def _matches_where_document_clause(
        self,
        content: str,
        where_document: Dict[str, Any],
    ) -> bool:
        """
        Check if document content matches a where_document clause.

        Args:
            content: Document content
            where_document: ChromaDB where_document clause

        Returns:
            True if content matches the where_document clause
        """
        for op, value in where_document.items():
            if op == "$contains":
                if value not in content:
                    return False
            elif op == "$not_contains":
                if value in content:
                    return False
            elif op == "$and":
                return all(self._matches_where_document_clause(content, c) for c in value)
            elif op == "$or":
                return any(self._matches_where_document_clause(content, c) for c in value)
            elif op == "$not":
                return not self._matches_where_document_clause(content, value)

        return True

    def search_with_facets(
        self,
        query: str,
        facet_fields: List[str],
        n_results: int = 20,
        where: Optional[Union[dict[str, Any], Filter]] = None,
        where_document: Optional[dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> tuple[list[dict[str, Any]], Dict[str, FacetResult]]:
        """
        Search with faceted aggregation.

        Performs search and computes facet counts for specified fields.
        Useful for building filtered search UIs with category counts.

        Args:
            query: Search query
            facet_fields: List of metadata fields to compute facets for
            n_results: Number of results to return
            where: Metadata filter (dict or Filter object)
            where_document: Document content filter
            use_hybrid: Use hybrid search if available

        Returns:
            Tuple of (search_results, facets_dict)
                - search_results: List of search results
                - facets_dict: Map of field names to FacetResult objects

        Example:
            >>> results, facets = store.search_with_facets(
            ...     "authentication",
            ...     facet_fields=["method", "category"],
            ...     n_results=20
            ... )
            >>> print(f"Found {len(results)} results")
            >>> for field, facet in facets.items():
            ...     print(f"{field}: {facet.get_top_values(5)}")
        """
        # Perform search
        results = self.search(
            query=query,
            n_results=n_results,
            where=where,
            where_document=where_document,
            use_hybrid=use_hybrid,
            use_reranker=False,  # Don't use reranker for faceted search
        )

        # Compute facets
        facets = FacetedSearch.compute_facets(results, facet_fields)

        logger.debug(
            "Faceted search completed",
            query=query[:50],
            result_count=len(results),
            facet_fields=facet_fields,
        )

        return results, facets

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

    def get_all_documents(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Get all documents from the collection.

        Args:
            limit: Maximum number of documents to return (None for all).

        Returns:
            List of documents with id, content, and metadata.
        """
        result = self.collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )

        documents = []
        for i in range(len(result["ids"])):
            documents.append({
                "id": result["ids"][i],
                "content": result["documents"][i],
                "metadata": result["metadatas"][i],
            })

        logger.debug("Retrieved documents", count=len(documents))
        return documents

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
            "reranker_enabled": self.enable_reranker,
        }

        if self.enable_hybrid_search and self._bm25:
            stats["bm25_indexed_documents"] = len(self._documents_cache)

        if self.enable_reranker:
            stats["reranker_model"] = self.reranker_model
            if self._reranker:
                stats["reranker_loaded"] = True
                cache_stats = self._reranker.get_cache_stats()
                if cache_stats:
                    stats["reranker_cache"] = cache_stats

        return stats


# Convenience function
def get_vector_store(
    enable_hybrid_search: bool = True,
    enable_reranker: bool = False,
) -> VectorStore:
    """
    Get a VectorStore instance with default settings.

    Args:
        enable_hybrid_search: Enable BM25 + Vector hybrid search (default: True).
        enable_reranker: Enable cross-encoder re-ranking (default: False).

    Returns:
        VectorStore instance.
    """
    return VectorStore(
        enable_hybrid_search=enable_hybrid_search,
        enable_reranker=enable_reranker,
    )
