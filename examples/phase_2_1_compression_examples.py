#!/usr/bin/env python3
"""
Example: Using Phase 2.1 Native Compression

Demonstrates how to use the new CompressionHandler
with different compression backends.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from fraud_generator.utils.compression import CompressionHandler, get_compressor


def example_basic_usage():
    """Example 1: Basic compression usage."""
    print("=" * 60)
    print("Example 1: Basic Compression Usage")
    print("=" * 60)
    
    data = b"Hello, World!" * 1000
    print(f"Original data: {len(data)} bytes")
    print()
    
    # Using gzip
    handler = CompressionHandler('gzip')
    compressed = handler.compress(data)
    decompressed = handler.decompress(compressed)
    
    print(f"gzip:")
    print(f"  Compressed: {len(compressed)} bytes ({len(compressed)/len(data)*100:.1f}%)")
    print(f"  Decompression OK: {decompressed == data}")
    print()


def example_algorithm_comparison():
    """Example 2: Compare different algorithms."""
    print("=" * 60)
    print("Example 2: Algorithm Comparison")
    print("=" * 60)
    
    data = b"Transaction data " * 1000
    algorithms = ['gzip', 'zstd', 'snappy', 'none']
    
    for algo in algorithms:
        try:
            handler = CompressionHandler(algo, verbose=False)
            compressed = handler.compress(data)
            ratio = (1 - len(compressed) / len(data)) * 100
            print(f"{algo:<10} → {len(compressed):>6} bytes ({ratio:>5.1f}% compression)")
        except Exception as e:
            print(f"{algo:<10} → Not available ({e})")
    
    print()


def example_with_json():
    """Example 3: Compress JSON data."""
    print("=" * 60)
    print("Example 3: Compress JSON Fraud Data")
    print("=" * 60)
    
    import json
    
    # Simulate fraud transaction data
    transactions = [
        {
            "id": f"txn_{i:06d}",
            "amount": 100.50,
            "type": "pix",
            "is_fraud": i % 100 == 0,
            "timestamp": "2024-01-15T12:30:00",
        }
        for i in range(1000)
    ]
    
    json_data = json.dumps(transactions).encode()
    print(f"JSON transactions: {len(json_data):,} bytes")
    print()
    
    # Try each compressor
    for algo in ['zstd', 'snappy', 'gzip']:
        try:
            handler = get_compressor(algo)
            compressed = handler.compress(json_data)
            ratio = (1 - len(compressed) / len(json_data)) * 100
            print(f"{algo:<10} → {len(compressed):>7,} bytes ({ratio:>5.1f}%)")
        except Exception as e:
            print(f"{algo:<10} → Error: {e}")
    
    print()


def example_fallback():
    """Example 4: Automatic fallback."""
    print("=" * 60)
    print("Example 4: Automatic Fallback")
    print("=" * 60)
    
    data = b"Test data" * 100
    
    # If zstd is not available, falls back to gzip automatically
    handler = CompressionHandler('zstd', verbose=True)
    print(f"Backend used: {handler.backend_name}")
    
    compressed = handler.compress(data)
    print(f"Compression works: {len(compressed) < len(data)}")
    print()


def example_integration_with_exporter():
    """Example 5: Integration pattern for exporters."""
    print("=" * 60)
    print("Example 5: Integration Pattern (Exporter Usage)")
    print("=" * 60)
    
    # This is how exporters would use the compression handler
    
    class ExporterWithCompression:
        """Example exporter using CompressionHandler."""
        
        def __init__(self, compression_algo='zstd'):
            self.compressor = CompressionHandler(compression_algo, verbose=False)
        
        def export_data(self, data: dict) -> bytes:
            """Export data with compression."""
            import json
            
            # Convert to JSON
            json_bytes = json.dumps(data).encode()
            
            # Compress
            compressed = self.compressor.compress(json_bytes)
            
            return compressed
    
    # Example usage
    exporter = ExporterWithCompression('zstd')
    data = {"customer": "John", "amount": 100.50, "fraud": False}
    
    result = exporter.export_data(data)
    print(f"Original JSON: ~{len(str(data))} bytes")
    print(f"Compressed: {len(result)} bytes")
    print(f"Using: {exporter.compressor.backend_name}")
    print()


if __name__ == '__main__':
    example_basic_usage()
    example_algorithm_comparison()
    example_with_json()
    example_fallback()
    example_integration_with_exporter()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
