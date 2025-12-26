"""
Tests for performance monitoring and caching systems.
"""

import time
from unittest.mock import MagicMock

import numpy as np
import pytest

from src.core.performance import (
    PerformanceMonitor,
    monitor_performance,
    monitor_performance_async,
    get_performance_report,
    get_slow_operations,
)
from src.core.cache import (
    LRUCache,
    EmbeddingCache,
    SemanticQueryCache,
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    def setup_method(self):
        """Reset monitor before each test."""
        PerformanceMonitor.reset()

    def test_record_operation(self):
        """Test recording operation metrics."""
        monitor = PerformanceMonitor.get_instance()

        monitor.record_operation("test_op", duration=1.5)
        monitor.record_operation("test_op", duration=2.0)
        monitor.record_operation("test_op", duration=1.0)

        report = monitor.get_report()
        operations = {op["operation"]: op for op in report["operations"]}

        assert "test_op" in operations
        assert operations["test_op"]["count"] == 3
        assert operations["test_op"]["min_time_ms"] == 1000
        assert operations["test_op"]["max_time_ms"] == 2000
        assert operations["test_op"]["avg_time_ms"] == 1500

    def test_record_operation_with_errors(self):
        """Test recording operation errors."""
        monitor = PerformanceMonitor.get_instance()

        monitor.record_operation("failing_op", duration=0.5, error=True)
        monitor.record_operation("failing_op", duration=0.6, error=True)
        monitor.record_operation("failing_op", duration=0.7, error=False)

        report = monitor.get_report()
        operations = {op["operation"]: op for op in report["operations"]}

        assert operations["failing_op"]["count"] == 3
        assert operations["failing_op"]["errors"] == 2
        assert operations["failing_op"]["error_rate"] == pytest.approx(66.67, rel=0.1)

    def test_cache_metrics(self):
        """Test cache hit/miss tracking."""
        monitor = PerformanceMonitor.get_instance()
        monitor.register_cache("test_cache", max_size=100)

        monitor.record_cache_hit("test_cache")
        monitor.record_cache_hit("test_cache")
        monitor.record_cache_miss("test_cache")

        report = monitor.get_report()
        caches = {c["cache"]: c for c in report["caches"]}

        assert "test_cache" in caches
        assert caches["test_cache"]["hits"] == 2
        assert caches["test_cache"]["misses"] == 1
        assert caches["test_cache"]["hit_rate"] == pytest.approx(66.67, rel=0.1)

    def test_slow_operations_detection(self):
        """Test detection of slow operations."""
        monitor = PerformanceMonitor.get_instance()

        monitor.record_operation("fast_op", duration=0.1)
        monitor.record_operation("slow_op", duration=2.5)
        monitor.record_operation("very_slow_op", duration=5.0)

        slow_ops = monitor.get_slow_operations(threshold_ms=1000)

        assert len(slow_ops) == 2
        slow_op_names = [op["operation"] for op in slow_ops]
        assert "slow_op" in slow_op_names
        assert "very_slow_op" in slow_op_names
        assert "fast_op" not in slow_op_names

    def test_get_report_summary(self):
        """Test performance report summary."""
        monitor = PerformanceMonitor.get_instance()

        monitor.record_operation("op1", duration=1.0)
        monitor.record_operation("op2", duration=2.0)
        monitor.record_operation("op3", duration=1.0, error=True)

        monitor.register_cache("cache1", max_size=100)
        monitor.record_cache_hit("cache1")
        monitor.record_cache_miss("cache1")

        report = monitor.get_report()

        assert report["summary"]["total_operations"] == 3
        assert report["summary"]["total_errors"] == 1
        assert report["summary"]["avg_cache_hit_rate"] == 50.0


class TestMonitorPerformanceDecorator:
    """Test performance monitoring decorators."""

    def setup_method(self):
        """Reset monitor before each test."""
        PerformanceMonitor.reset()

    def test_monitor_performance_decorator(self):
        """Test decorator monitors function execution."""

        @monitor_performance("test_function")
        def test_function(x):
            time.sleep(0.01)
            return x * 2

        result = test_function(5)
        assert result == 10

        monitor = PerformanceMonitor.get_instance()
        report = monitor.get_report()
        operations = {op["operation"]: op for op in report["operations"]}

        assert "test_function" in operations
        assert operations["test_function"]["count"] == 1
        assert operations["test_function"]["avg_time_ms"] >= 10

    def test_monitor_performance_with_exception(self):
        """Test decorator records errors."""

        @monitor_performance("failing_function")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        monitor = PerformanceMonitor.get_instance()
        report = monitor.get_report()
        operations = {op["operation"]: op for op in report["operations"]}

        assert operations["failing_function"]["errors"] == 1

    @pytest.mark.asyncio
    async def test_monitor_performance_async_decorator(self):
        """Test async decorator monitors execution."""
        import asyncio

        @monitor_performance_async("async_function")
        async def async_function(x):
            await asyncio.sleep(0.01)
            return x * 2

        result = await async_function(5)
        assert result == 10

        monitor = PerformanceMonitor.get_instance()
        report = monitor.get_report()
        operations = {op["operation"]: op for op in report["operations"]}

        assert "async_function" in operations
        assert operations["async_function"]["count"] == 1


class TestLRUCache:
    """Test LRU cache functionality."""

    def test_basic_get_put(self):
        """Test basic cache get/put operations."""
        cache = LRUCache(max_size=3, name="test_cache")

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") is None

    def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = LRUCache(max_size=3, name="test_cache")

        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        cache.put("key4", "value4")  # Should evict key1

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = LRUCache(max_size=10, ttl=0.1, name="test_cache")

        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"

        time.sleep(0.15)

        assert cache.get("key1") is None  # Expired

    def test_update_existing_key(self):
        """Test updating existing cache entry."""
        cache = LRUCache(max_size=3, name="test_cache")

        cache.put("key1", "value1")
        cache.put("key1", "value2")  # Update

        assert cache.get("key1") == "value2"
        assert cache.size() == 1

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=10, ttl=60, name="test_cache")

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        stats = cache.stats()
        assert stats["name"] == "test_cache"
        assert stats["size"] == 2
        assert stats["max_size"] == 10


class TestEmbeddingCache:
    """Test embedding cache functionality."""

    def test_basic_embedding_caching(self):
        """Test basic embedding caching."""
        cache = EmbeddingCache(max_size=10)
        embed_fn = MagicMock(return_value=np.array([1.0, 2.0, 3.0]))

        # First call - cache miss
        embedding1 = cache.get_embedding("test text", embed_fn)
        assert embed_fn.call_count == 1
        assert np.array_equal(embedding1, np.array([1.0, 2.0, 3.0]))

        # Second call - cache hit
        embedding2 = cache.get_embedding("test text", embed_fn)
        assert embed_fn.call_count == 1  # Not called again
        assert np.array_equal(embedding2, np.array([1.0, 2.0, 3.0]))

    def test_different_texts_different_embeddings(self):
        """Test different texts get different cache entries."""
        cache = EmbeddingCache(max_size=10)
        embed_fn = MagicMock(side_effect=[
            np.array([1.0, 2.0, 3.0]),
            np.array([4.0, 5.0, 6.0]),
        ])

        embedding1 = cache.get_embedding("text1", embed_fn)
        embedding2 = cache.get_embedding("text2", embed_fn)

        assert embed_fn.call_count == 2
        assert not np.array_equal(embedding1, embedding2)

    def test_batch_embedding_caching(self):
        """Test batch embedding with caching."""
        cache = EmbeddingCache(max_size=10)

        # Mock function that returns embeddings for uncached texts
        def mock_embed_batch(texts):
            return [np.array([float(i), float(i+1), float(i+2)]) for i in range(len(texts))]

        texts = ["text1", "text2", "text3"]

        # First call - all cache misses
        embeddings1 = cache.get_embeddings_batch(texts, mock_embed_batch)
        assert len(embeddings1) == 3

        # Second call - all cache hits
        # Mock function should not be called for cached texts
        mock_embed = MagicMock(return_value=[])
        embeddings2 = cache.get_embeddings_batch(texts, mock_embed)
        assert len(embeddings2) == 3
        assert mock_embed.call_count == 0

        # Check embeddings match
        for emb1, emb2 in zip(embeddings1, embeddings2):
            assert np.array_equal(emb1, emb2)


class TestSemanticQueryCache:
    """Test semantic query cache functionality."""

    def test_exact_match(self):
        """Test exact query match."""
        cache = SemanticQueryCache(max_size=10, similarity_threshold=0.95)

        query = "How do I authenticate?"
        embedding = np.array([1.0, 0.0, 0.0])
        result = {"answer": "Use API key"}

        cache.put(query, embedding, result)

        # Exact same query and embedding
        cached = cache.get(query, embedding)
        assert cached is not None
        assert cached["answer"] == "Use API key"

    def test_similar_query_match(self):
        """Test semantically similar query match."""
        cache = SemanticQueryCache(max_size=10, similarity_threshold=0.90)

        query1 = "How do I authenticate?"
        embedding1 = np.array([1.0, 0.0, 0.0])
        result1 = {"answer": "Use API key"}

        cache.put(query1, embedding1, result1)

        # Similar query (high cosine similarity)
        query2 = "How do I auth?"
        embedding2 = np.array([0.95, 0.05, 0.0])  # Very similar to embedding1

        cached = cache.get(query2, embedding2)
        assert cached is not None

    def test_dissimilar_query_miss(self):
        """Test dissimilar query returns cache miss."""
        cache = SemanticQueryCache(max_size=10, similarity_threshold=0.95)

        query1 = "How do I authenticate?"
        embedding1 = np.array([1.0, 0.0, 0.0])
        result1 = {"answer": "Use API key"}

        cache.put(query1, embedding1, result1)

        # Very different query
        query2 = "What endpoints are available?"
        embedding2 = np.array([0.0, 1.0, 0.0])  # Orthogonal to embedding1

        cached = cache.get(query2, embedding2)
        assert cached is None

    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = SemanticQueryCache(max_size=10, similarity_threshold=0.95, ttl=0.1)

        query = "test query"
        embedding = np.array([1.0, 0.0, 0.0])
        result = {"answer": "test"}

        cache.put(query, embedding, result)
        assert cache.get(query, embedding) is not None

        time.sleep(0.15)

        assert cache.get(query, embedding) is None


class TestPerformanceIntegration:
    """Integration tests for performance system."""

    def setup_method(self):
        """Reset monitor before each test."""
        PerformanceMonitor.reset()

    def test_full_caching_pipeline(self):
        """Test complete caching pipeline with monitoring."""
        embedding_cache = EmbeddingCache(max_size=100)

        # Mock embedding function
        call_count = {"count": 0}

        def mock_embed(text):
            call_count["count"] += 1
            return np.random.rand(384)

        # First embedding - cache miss
        emb1 = embedding_cache.get_embedding("test query", mock_embed)
        assert call_count["count"] == 1

        # Second embedding - cache hit
        emb2 = embedding_cache.get_embedding("test query", mock_embed)
        assert call_count["count"] == 1  # Not incremented
        assert np.array_equal(emb1, emb2)

        # Check performance monitoring
        monitor = PerformanceMonitor.get_instance()
        report = monitor.get_report()
        caches = {c["cache"]: c for c in report["caches"]}

        assert "embedding_cache" in caches
        assert caches["embedding_cache"]["hits"] >= 1
        assert caches["embedding_cache"]["hit_rate"] > 0

    def test_performance_report_generation(self):
        """Test generating complete performance report."""

        @monitor_performance("test_op")
        def test_operation():
            time.sleep(0.01)
            return "done"

        # Execute operations
        for _ in range(5):
            test_operation()

        # Get report
        report = get_performance_report()

        assert "operations" in report
        assert "caches" in report
        assert "summary" in report
        assert report["summary"]["total_operations"] == 5

    def test_slow_operation_identification(self):
        """Test identifying slow operations."""

        @monitor_performance("fast_op")
        def fast_operation():
            time.sleep(0.001)

        @monitor_performance("slow_op")
        def slow_operation():
            time.sleep(0.1)

        fast_operation()
        slow_operation()

        slow_ops = get_slow_operations(threshold_ms=50)
        assert len(slow_ops) == 1
        assert slow_ops[0]["operation"] == "slow_op"
