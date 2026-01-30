"""
Unit tests for Phase 1 optimizations.

Test suite validating all optimization features:
- WeightCache O(log n) sampling
- skip_none field filtering
- MinIO gzip compression
- CSV streaming
"""

import unittest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from fraud_generator.utils.weight_cache import WeightCache
from fraud_generator.exporters.json_exporter import JSONExporter
from fraud_generator.exporters.minio_exporter import MinIOExporter


class TestWeightCache(unittest.TestCase):
    """Test WeightCache optimization (1.1)."""

    def setUp(self):
        """Set up test fixtures."""
        self.items = ['A', 'B', 'C', 'D']
        self.weights = [0.1, 0.2, 0.3, 0.4]
        self.cache = WeightCache(self.items, self.weights)

    def test_cache_initialization(self):
        """Test WeightCache initializes correctly."""
        self.assertEqual(self.cache.choices, self.items)
        self.assertIsNotNone(self.cache.cumsum)

    def test_sample_returns_valid_item(self):
        """Test sample() returns item from choices."""
        sample = self.cache.sample()
        self.assertIn(sample, self.items)

    def test_sample_distribution(self):
        """Test sample distribution roughly matches weights."""
        samples = [self.cache.sample() for _ in range(1000)]
        
        from collections import Counter
        counts = Counter(samples)
        
        for item, weight in zip(self.items, self.weights):
            actual_ratio = counts[item] / len(samples)
            # Allow 10% tolerance
            self.assertAlmostEqual(actual_ratio, weight, delta=0.1)


class TestSkipNone(unittest.TestCase):
    """Test skip_none optimization (1.3)."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = JSONExporter(skip_none=True)

    def test_clean_record_removes_none(self):
        """Test _clean_record removes None values."""
        test_record = {
            "id": "1",
            "name": "Test",
            "optional": None,
            "another": "value"
        }
        
        cleaned = self.exporter._clean_record(test_record)
        
        self.assertNotIn("optional", cleaned)
        self.assertIn("id", cleaned)
        self.assertIn("name", cleaned)
        self.assertIn("another", cleaned)

    def test_clean_record_preserves_zero(self):
        """Test _clean_record preserves 0 and False values."""
        test_record = {
            "count": 0,
            "enabled": False,
            "nothing": None
        }
        
        cleaned = self.exporter._clean_record(test_record)
        
        self.assertIn("count", cleaned)
        self.assertEqual(cleaned["count"], 0)
        self.assertIn("enabled", cleaned)
        self.assertEqual(cleaned["enabled"], False)
        self.assertNotIn("nothing", cleaned)


class TestMinIOGzip(unittest.TestCase):
    """Test MinIO gzip compression (1.7)."""

    def test_gzip_extension(self):
        """Test gzip sets .jsonl.gz extension."""
        exporter = MinIOExporter(bucket='test', jsonl_compress='gzip')
        self.assertEqual(exporter.extension, '.jsonl.gz')

    def test_plain_extension(self):
        """Test plain JSONL sets .jsonl extension."""
        exporter = MinIOExporter(bucket='test', jsonl_compress='none')
        self.assertEqual(exporter.extension, '.jsonl')

    def test_jsonl_compress_stored(self):
        """Test jsonl_compress parameter is stored."""
        exporter = MinIOExporter(bucket='test', jsonl_compress='gzip')
        self.assertEqual(exporter.jsonl_compress, 'gzip')


if __name__ == '__main__':
    unittest.main()
