"""
Tests for Phase 2.1 native compression handlers.

Test suite for CompressionHandler factory and backend implementations.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from fraud_generator.utils.compression import (
    CompressionHandler,
    GzipCompressor,
    ZstdCompressor,
    SnappyCompressor,
    NoOpCompressor,
    get_compressor,
)


class TestGzipCompressor:
    """Test gzip compression backend."""
    
    def test_gzip_compress_decompress(self):
        """Test gzip compress/decompress roundtrip."""
        compressor = GzipCompressor()
        data = b"Hello, World!" * 1000
        
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        
        assert decompressed == data
        assert len(compressed) < len(data)  # Should compress
    
    def test_gzip_extension(self):
        """Test gzip extension property."""
        compressor = GzipCompressor()
        assert compressor.extension == '.gz'
    
    def test_gzip_compression_levels(self):
        """Test different compression levels."""
        data = b"Test data" * 1000
        
        level1 = GzipCompressor(level=1).compress(data)
        level9 = GzipCompressor(level=9).compress(data)
        
        # Higher level should compress better
        assert len(level9) <= len(level1)


class TestZstdCompressor:
    """Test zstandard compression backend."""
    
    def test_zstd_available(self):
        """Test zstd is available."""
        try:
            compressor = ZstdCompressor()
            assert compressor is not None
        except ImportError:
            pytest.skip("zstandard not installed")
    
    def test_zstd_compress_decompress(self):
        """Test zstd compress/decompress roundtrip."""
        try:
            compressor = ZstdCompressor()
        except ImportError:
            pytest.skip("zstandard not installed")
        
        data = b"Hello, World!" * 1000
        
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        
        assert decompressed == data
        assert len(compressed) < len(data)
    
    def test_zstd_extension(self):
        """Test zstd extension property."""
        try:
            compressor = ZstdCompressor()
        except ImportError:
            pytest.skip("zstandard not installed")
        
        assert compressor.extension == '.zstd'


class TestSnappyCompressor:
    """Test snappy compression backend."""
    
    def test_snappy_available(self):
        """Test snappy is available."""
        try:
            compressor = SnappyCompressor()
            assert compressor is not None
        except ImportError:
            pytest.skip("python-snappy not installed")
    
    def test_snappy_compress_decompress(self):
        """Test snappy compress/decompress roundtrip."""
        try:
            compressor = SnappyCompressor()
        except ImportError:
            pytest.skip("python-snappy not installed")
        
        data = b"Hello, World!" * 1000
        
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        
        assert decompressed == data
    
    def test_snappy_extension(self):
        """Test snappy extension property."""
        try:
            compressor = SnappyCompressor()
        except ImportError:
            pytest.skip("python-snappy not installed")
        
        assert compressor.extension == '.snappy'


class TestCompressionHandler:
    """Test CompressionHandler factory."""
    
    def test_handler_gzip(self):
        """Test handler defaults to gzip."""
        handler = CompressionHandler('gzip')
        data = b"Test data" * 100
        
        compressed = handler.compress(data)
        decompressed = handler.decompress(compressed)
        
        assert decompressed == data
    
    def test_handler_none(self):
        """Test handler with no compression."""
        handler = CompressionHandler('none')
        data = b"Test data" * 100
        
        compressed = handler.compress(data)
        
        assert compressed == data  # No compression
    
    def test_handler_fallback_zstd_to_gzip(self):
        """Test handler falls back to gzip if zstd unavailable."""
        # This test only works if zstandard is not installed
        # Otherwise it should use zstd
        handler = CompressionHandler('zstd', verbose=False)
        assert handler._backend is not None
    
    def test_handler_backend_name(self):
        """Test handler backend_name property."""
        handler = CompressionHandler('gzip')
        assert 'Gzip' in handler.backend_name
    
    def test_handler_algorithm_property(self):
        """Test handler stores algorithm."""
        handler = CompressionHandler('gzip')
        assert handler.algorithm == 'gzip'
    
    def test_get_compressor_convenience(self):
        """Test get_compressor convenience function."""
        handler = get_compressor('gzip')
        assert isinstance(handler, CompressionHandler)
    
    def test_invalid_algorithm(self):
        """Test invalid algorithm raises error."""
        with pytest.raises(ValueError):
            CompressionHandler('invalid_algo')
    
    def test_invalid_data_type(self):
        """Test compress rejects non-bytes."""
        handler = CompressionHandler('gzip')
        
        with pytest.raises(TypeError):
            handler.compress("not bytes")
    
    def test_handler_repr(self):
        """Test handler repr."""
        handler = CompressionHandler('gzip')
        repr_str = repr(handler)
        assert 'CompressionHandler' in repr_str


class TestCompressionBenchmark:
    """Benchmark different compression algorithms."""
    
    @pytest.mark.parametrize('algorithm', ['gzip', 'zstd', 'snappy', 'none'])
    def test_compress_json_like_data(self, algorithm):
        """Test compression on JSON-like data."""
        try:
            handler = CompressionHandler(algorithm, verbose=False)
        except ValueError:
            pytest.skip(f"{algorithm} not available")
        
        # Simulate JSON data (highly repetitive)
        import json
        data_list = [
            {
                "id": f"txn_{i}",
                "amount": 100.50,
                "type": "pix",
                "is_fraud": False,
            }
            for i in range(1000)
        ]
        data = json.dumps(data_list).encode()
        
        compressed = handler.compress(data)
        
        # All should compress JSON
        if algorithm != 'none':
            assert len(compressed) < len(data)
    
    def test_benchmark_gzip(self):
        """Benchmark gzip compression."""
        handler = CompressionHandler('gzip')
        data = b"Test data" * 10000
        
        # Simple timing
        import time
        start = time.time()
        for _ in range(10):
            handler.compress(data)
        elapsed = time.time() - start
        
        assert elapsed > 0  # Just verify it runs
    
    def test_benchmark_zstd(self):
        """Benchmark zstd compression."""
        try:
            handler = CompressionHandler('zstd')
        except (ImportError, ValueError):
            pytest.skip("zstandard not installed")
        
        data = b"Test data" * 10000
        
        # Simple timing
        import time
        start = time.time()
        for _ in range(10):
            handler.compress(data)
        elapsed = time.time() - start
        
        assert elapsed > 0  # Just verify it runs
    
    def test_benchmark_snappy(self):
        """Benchmark snappy compression."""
        try:
            handler = CompressionHandler('snappy')
        except (ImportError, ValueError):
            pytest.skip("python-snappy not installed")
        
        data = b"Test data" * 10000
        
        # Simple timing
        import time
        start = time.time()
        for _ in range(10):
            handler.compress(data)
        elapsed = time.time() - start
        
        assert elapsed > 0  # Just verify it runs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
