#!/usr/bin/env python3
"""
Phase 2.1 Compression Benchmark

Compares compression algorithms on realistic fraud data.
Shows compression speed, ratio, and memory usage.

Usage:
    python benchmarks/phase_2_1_compression_benchmark.py
"""

import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from fraud_generator.utils.compression import CompressionHandler


def generate_sample_transactions(count: int) -> bytes:
    """Generate sample transaction data (JSON)."""
    transactions = [
        {
            "id": f"txn_{i:06d}",
            "customer_id": f"cust_{i % 1000:04d}",
            "amount": 100.50 + (i % 50),
            "currency": "BRL",
            "bank": f"{(i % 100):03d}",
            "type": ["pix", "card", "debit", "credit"][i % 4],
            "channel": ["app", "web", "atm", "branch"][i % 4],
            "is_fraud": i % 100 == 0,
            "fraud_type": "card_takeover" if i % 100 == 0 else None,
            "timestamp": f"2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00",
        }
        for i in range(count)
    ]
    return json.dumps(transactions).encode()


def benchmark_algorithm(algorithm: str, data: bytes, iterations: int = 3) -> dict:
    """Benchmark a single compression algorithm."""
    try:
        handler = CompressionHandler(algorithm, verbose=False)
    except (ImportError, ValueError) as e:
        return {
            'algorithm': algorithm,
            'status': 'UNAVAILABLE',
            'error': str(e),
        }
    
    # Warmup
    handler.compress(data[:1000])
    
    # Benchmark compression
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        compressed = handler.compress(data)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    original_size = len(data)
    compressed_size = len(compressed)
    ratio = (1 - compressed_size / original_size) * 100
    throughput = original_size / avg_time / 1e6  # MB/sec
    
    # Verify decompression works
    try:
        decompressed = handler.decompress(compressed)
        assert decompressed == data, "Decompression mismatch!"
    except Exception as e:
        return {
            'algorithm': algorithm,
            'status': 'DECOMPRESSION_ERROR',
            'error': str(e),
        }
    
    return {
        'algorithm': algorithm,
        'status': 'OK',
        'original_size_mb': original_size / 1e6,
        'compressed_size_mb': compressed_size / 1e6,
        'compression_ratio': f"{ratio:.1f}%",
        'time_ms': avg_time * 1000,
        'throughput_mbps': throughput,
        'backend': handler.backend_name,
    }


def main():
    """Run benchmarks."""
    print("=" * 80)
    print("Phase 2.1 Compression Benchmark")
    print("=" * 80)
    print()
    
    # Generate test data
    print("Generating test data...")
    data_sizes = {
        '10K records': 10_000,
        '100K records': 100_000,
    }
    
    algorithms = ['gzip', 'zstd', 'snappy', 'none']
    
    for size_name, count in data_sizes.items():
        print(f"\n{'─' * 80}")
        print(f"Test: {size_name}")
        print(f"{'─' * 80}")
        
        data = generate_sample_transactions(count)
        print(f"Data size: {len(data) / 1e6:.2f} MB ({count:,} records)")
        print()
        
        # Benchmark each algorithm
        results = []
        for algo in algorithms:
            result = benchmark_algorithm(algo, data)
            results.append(result)
        
        # Print results table
        print(f"{'Algorithm':<15} {'Status':<20} {'Compressed':<12} {'Ratio':<10} {'Speed':<12} {'Throughput':<15}")
        print("─" * 90)
        
        for result in results:
            if result['status'] == 'OK':
                print(
                    f"{result['algorithm']:<15} "
                    f"{result['status']:<20} "
                    f"{result['compressed_size_mb']:>6.2f} MB   "
                    f"{result['compression_ratio']:>9} "
                    f"{result['time_ms']:>6.2f} ms   "
                    f"{result['throughput_mbps']:>10.1f} MB/s"
                )
            elif result['status'] == 'UNAVAILABLE':
                print(
                    f"{result['algorithm']:<15} "
                    f"⚠️  {result['status']:<17} "
                    f"(install {result['algorithm']})"
                )
            else:
                print(
                    f"{result['algorithm']:<15} "
                    f"❌ {result['status']:<17} "
                    f"({result['error']})"
                )
    
    print()
    print("=" * 80)
    print("Summary:")
    print("  • zstd: Best compression ratio, fast C backend")
    print("  • snappy: Ultra-fast, lighter compression")
    print("  • gzip: Baseline, pure Python fallback")
    print("  • none: No compression (for comparison)")
    print("=" * 80)


if __name__ == '__main__':
    main()
