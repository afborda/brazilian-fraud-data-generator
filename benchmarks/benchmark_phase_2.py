#!/usr/bin/env python3
"""
Performance benchmarking for Phase 2.2-2.9 optimizations.

Measures generation speed improvements across core scenarios.
"""

import sys
import time
import json
import statistics
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from fraud_generator.generators.transaction import TransactionGenerator
from fraud_generator.generators.ride import RideGenerator
from fraud_generator.utils.streaming import CustomerSessionState, haversine_distance
from fraud_generator.models.customer import Customer, Address
from fraud_generator.exporters.csv_exporter import CSVExporter


class BenchmarkRunner:
    """Run performance benchmarks for Phase 2.2-2.9 optimizations."""

    def __init__(self, output_dir: str = './benchmark_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: Dict[str, List[float]] = {}
        self.start_time = datetime.now().isoformat()

    def benchmark_haversine_calculation(self, iterations: int = 100000) -> float:
        """Benchmark Phase 2.4: Haversine distance calculation."""
        print(f"\n🔹 Benchmarking Haversine distance (100k iterations)...")
        
        coordinates = [
            (-23.5505, -46.6333),  # São Paulo
            (-22.9068, -43.1729),  # Rio de Janeiro
            (-23.2237, -49.6492),  # Londrina
            (-20.3155, -40.3128),  # Vitória
            (-19.9167, -43.9345),  # Belo Horizonte
        ]
        
        times = []
        for _ in range(3):
            start = time.perf_counter()
            for i in range(iterations):
                lat1, lon1 = coordinates[i % len(coordinates)]
                lat2, lon2 = coordinates[(i + 1) % len(coordinates)]
                haversine_distance(lat1, lon1, lat2, lon2)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        calls_per_sec = iterations / avg_time
        print(f"  ✓ Average: {avg_time:.4f}s ({calls_per_sec:,.0f} calls/sec)")
        self.results['haversine_distance'] = times
        return avg_time

    def benchmark_customer_session_state(self, num_transactions: int = 10000) -> float:
        """Benchmark Phase 2.2: CustomerSessionState (velocity, accumulation tracking)."""
        print(f"\n🔹 Benchmarking CustomerSessionState (10k transactions)...")
        
        session = CustomerSessionState("test_customer")
        base_time = datetime(2024, 1, 15, 12, 0, 0)
        
        times = []
        for _ in range(3):
            session = CustomerSessionState("test_customer")
            start = time.perf_counter()
            
            for i in range(num_transactions):
                tx = {
                    'transaction_id': f'tx_{i:06d}',
                    'timestamp': base_time + timedelta(minutes=i % 1440),
                    'amount': 100.0 + (i % 500),
                    'merchant_id': f'merc_{i % 100:03d}',
                    'geolocation_lat': -23.5505 + (i % 10) * 0.001,
                    'geolocation_lon': -46.6333 + (i % 10) * 0.001,
                    'device_id': f'dev_{i % 50:02d}'
                }
                session.add_transaction(tx, tx['timestamp'])
                
                if i % 100 == 0:
                    session.get_velocity(tx['timestamp'])
                    session.get_accumulated_24h(tx['timestamp'])
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        txns_per_sec = num_transactions / avg_time
        print(f"  ✓ Average: {avg_time:.4f}s ({txns_per_sec:,.0f} tx/sec)")
        self.results['customer_session_state'] = times
        return avg_time

    def benchmark_ride_generation(self, count: int = 5000) -> float:
        """Benchmark Phase 2.4: Ride generation with Haversine calculations."""
        print(f"\n🔹 Benchmarking Ride Generation (5k records)...")
        
        generator = RideGenerator()
        base_time = datetime(2024, 1, 15, 12, 0, 0)
        
        times = []
        for _ in range(3):
            start = time.perf_counter()
            
            for i in range(count):
                ride = generator.generate(
                    ride_id=f"ride_{i:06d}",
                    driver_id=f"drv_{i % 50:02d}",
                    passenger_id=f"pass_{i % 100:03d}",
                    timestamp=base_time,
                    passenger_state="SP"
                )
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        rides_per_sec = count / avg_time
        print(f"  ✓ Average: {avg_time:.4f}s ({rides_per_sec:,.0f} rides/sec)")
        self.results['ride_generation'] = times
        return avg_time

    def benchmark_csv_export(self, record_count: int = 50000) -> float:
        """Benchmark Phase 2.5: CSV export with optimized buffering."""
        print(f"\n🔹 Benchmarking CSV Export (50k records, optimized buffering)...")
        
        import tempfile
        
        records = [
            {
                'transaction_id': f'tx_{i:06d}',
                'customer_id': f'cust_{i % 1000:04d}',
                'amount': 100.0 + (i % 500),
                'timestamp': '2024-01-15T12:00:00',
                'merchant_id': f'merc_{i % 100:03d}',
                'fraud': i % 200 == 0
            }
            for i in range(record_count)
        ]
        
        exporter = CSVExporter()
        times = []
        
        for _ in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                output_path = f.name
            
            start = time.perf_counter()
            exporter.export_batch(records, output_path)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
            Path(output_path).unlink(missing_ok=True)
        
        avg_time = statistics.mean(times)
        records_per_sec = record_count / avg_time
        print(f"  ✓ Average: {avg_time:.4f}s ({records_per_sec:,.0f} records/sec)")
        self.results['csv_export_optimized'] = times
        return avg_time

    def benchmark_arrow_ipc_export(self, record_count: int = 50000) -> float:
        """Benchmark Phase 2.6: Arrow IPC export with compression."""
        try:
            from fraud_generator.exporters.arrow_ipc_exporter import ArrowIPCExporter
        except ImportError:
            print(f"\n🔹 Arrow IPC Export: SKIPPED (pyarrow not installed)")
            return None
        
        print(f"\n🔹 Benchmarking Arrow IPC Export (50k records)...")
        
        import tempfile
        
        records = [
            {
                'transaction_id': f'tx_{i:06d}',
                'customer_id': f'cust_{i % 1000:04d}',
                'amount': float(100.0 + (i % 500)),
                'timestamp': '2024-01-15T12:00:00',
                'merchant_id': f'merc_{i % 100:03d}',
                'fraud': bool(i % 200 == 0)
            }
            for i in range(record_count)
        ]
        
        exporter = ArrowIPCExporter(compression='lz4', batch_size=5000)
        times = []
        
        for _ in range(3):
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.arrow', delete=False) as f:
                output_path = f.name
            
            start = time.perf_counter()
            exporter.export_batch(records, output_path)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
            Path(output_path).unlink(missing_ok=True)
        
        avg_time = statistics.mean(times)
        records_per_sec = record_count / avg_time
        print(f"  ✓ Average: {avg_time:.4f}s ({records_per_sec:,.0f} records/sec)")
        self.results['arrow_ipc_export'] = times
        return avg_time

    def print_summary(self):
        """Print benchmark summary and comparisons."""
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY - Phase 2.2-2.9 Optimizations")
        print("="*70)
        
        print(f"\nTest Date: {self.start_time}")
        print(f"Results Directory: {self.output_dir}")
        
        # Haversine
        if 'haversine_distance' in self.results:
            avg = statistics.mean(self.results['haversine_distance'])
            print(f"\n📊 Phase 2.4 - Haversine Distance (100k calls)")
            print(f"  Average Time: {avg:.4f}s ({100000/avg:,.0f} calls/sec)")
        
        # Session state
        if 'customer_session_state' in self.results:
            avg = statistics.mean(self.results['customer_session_state'])
            print(f"\n📊 Phase 2.2 - CustomerSessionState (10k transactions)")
            print(f"  Average Time: {avg:.4f}s ({10000/avg:,.0f} tx/sec)")
        
        # Ride generation
        if 'ride_generation' in self.results:
            avg = statistics.mean(self.results['ride_generation'])
            print(f"\n📊 Phase 2.4 - Ride Generation (5k records)")
            print(f"  Average Time: {avg:.4f}s ({5000/avg:,.0f} rides/sec)")
        
        # CSV export
        if 'csv_export_optimized' in self.results:
            avg = statistics.mean(self.results['csv_export_optimized'])
            print(f"\n📊 Phase 2.5 - CSV Export (50k records, 256KB buffer)")
            print(f"  Average Time: {avg:.4f}s ({50000/avg:,.0f} records/sec)")
        
        # Arrow IPC
        if 'arrow_ipc_export' in self.results:
            avg = statistics.mean(self.results['arrow_ipc_export'])
            print(f"\n📊 Phase 2.6 - Arrow IPC Export (50k records, lz4)")
            print(f"  Average Time: {avg:.4f}s ({50000/avg:,.0f} records/sec)")

    def save_results(self):
        """Save benchmark results to JSON file."""
        results_file = self.output_dir / 'benchmark_results.json'
        
        data = {
            'timestamp': self.start_time,
            'results': {}
        }
        
        for key, times in self.results.items():
            data['results'][key] = {
                'values': times,
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'stdev': statistics.stdev(times) if len(times) > 1 else 0.0,
                'min': min(times),
                'max': max(times)
            }
        
        with open(results_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Results saved to {results_file}")


def main():
    """Run all benchmarks."""
    runner = BenchmarkRunner()
    
    print("\n" + "="*70)
    print("PERFORMANCE BENCHMARKS - Phase 2.2-2.9 Optimizations")
    print("="*70)
    
    try:
        runner.benchmark_haversine_calculation()
    except Exception as e:
        print(f"  ⚠ Haversine: {e}")
    
    try:
        runner.benchmark_customer_session_state()
    except Exception as e:
        print(f"  ⚠ Session State: {e}")
    
    try:
        runner.benchmark_ride_generation()
    except Exception as e:
        print(f"  ⚠ Ride Generation: {e}")
    
    try:
        runner.benchmark_csv_export()
    except Exception as e:
        print(f"  ⚠ CSV Export: {e}")
    
    try:
        runner.benchmark_arrow_ipc_export()
    except Exception as e:
        print(f"  ⚠ Arrow IPC: {e}")
    
    runner.print_summary()
    runner.save_results()


if __name__ == '__main__':
    main()
