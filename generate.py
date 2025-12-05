#!/usr/bin/env python3
"""
🇧🇷 BRAZILIAN FRAUD DATA GENERATOR v3.0
=======================================
Generate realistic Brazilian financial transaction data for testing,
development, and machine learning model training.

Features:
- 100% Brazilian data (CPF válido, banks, PIX, addresses)
- Behavioral profiles for realistic patterns (default)
- Multiple export formats (JSON, CSV, Parquet)
- Memory-efficient streaming for large datasets
- Configurable fraud patterns
- Parallel generation for high throughput
- Reproducible data with seed support

Usage:
    # Basic usage with profiles (default)
    python3 generate.py --size 1GB --output ./output
    
    # Specify export format
    python3 generate.py --size 1GB --format csv --output ./output
    python3 generate.py --size 1GB --format parquet --output ./output
    
    # Disable profiles (random transactions)
    python3 generate.py --size 1GB --no-profiles --output ./output
    
    # Custom fraud rate and workers
    python3 generate.py --size 50GB --fraud-rate 0.01 --workers 8
    
    # Reproducible data
    python3 generate.py --size 1GB --seed 42 --output ./output
"""

__version__ = "3.0.0"

import argparse
import json
import os
import sys
import time
import random
import multiprocessing as mp
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from functools import partial

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fraud_generator.generators import CustomerGenerator, DeviceGenerator, TransactionGenerator
from fraud_generator.exporters import get_exporter, list_formats, is_format_available
from fraud_generator.utils import (
    CustomerIndex, DeviceIndex,
    parse_size, format_size, format_duration,
    BatchGenerator,
)
from fraud_generator.validators import validate_cpf

# Configuration
TARGET_FILE_SIZE_MB = 128  # Each file will be ~128MB
BYTES_PER_TRANSACTION = 1050  # ~1KB per JSON transaction
TRANSACTIONS_PER_FILE = (TARGET_FILE_SIZE_MB * 1024 * 1024) // BYTES_PER_TRANSACTION


def worker_generate_batch(args: tuple) -> str:
    """
    Worker that generates a batch file with transactions.
    
    Args:
        args: Tuple of (batch_id, num_transactions, customer_indexes, device_indexes,
              start_date, end_date, fraud_rate, use_profiles, output_dir, format_name, seed)
    
    Returns:
        Path to generated file
    """
    (batch_id, num_transactions, customer_indexes, device_indexes,
     start_date, end_date, fraud_rate, use_profiles, output_dir, format_name, seed) = args
    
    # Deterministic seed per worker
    if seed is not None:
        worker_seed = seed + batch_id * 12345
    else:
        worker_seed = batch_id * 12345 + int(time.time() * 1000) % 10000
    
    random.seed(worker_seed)
    
    # Reconstruct indexes
    customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
    device_idx_list = [DeviceIndex(*d) for d in device_indexes]
    
    # Build customer-device pairs
    customer_device_map = {}
    for device in device_idx_list:
        if device.customer_id not in customer_device_map:
            customer_device_map[device.customer_id] = []
        customer_device_map[device.customer_id].append(device)
    
    pairs = []
    for customer in customer_idx_list:
        devices = customer_device_map.get(customer.customer_id, [])
        if devices:
            for device in devices:
                pairs.append((customer, device))
    
    if not pairs:
        # Fallback
        pairs = [(customer_idx_list[0], device_idx_list[0])]
    
    # Generate transactions
    tx_generator = TransactionGenerator(
        fraud_rate=fraud_rate,
        use_profiles=use_profiles,
        seed=worker_seed
    )
    
    transactions = []
    start_tx_id = batch_id * num_transactions
    
    for i in range(num_transactions):
        customer, device = random.choice(pairs)
        
        # Generate timestamp
        days_between = (end_date - start_date).days
        random_day = start_date + timedelta(days=random.randint(0, max(1, days_between)))
        
        hour_weights = {
            0: 2, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2,
            6: 4, 7: 6, 8: 10, 9: 12, 10: 14, 11: 14,
            12: 15, 13: 14, 14: 13, 15: 12, 16: 12, 17: 13,
            18: 14, 19: 15, 20: 14, 21: 12, 22: 8, 23: 4
        }
        hour = random.choices(list(hour_weights.keys()), weights=list(hour_weights.values()))[0]
        timestamp = random_day.replace(
            hour=hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=random.randint(0, 999999)
        )
        
        tx = tx_generator.generate(
            tx_id=f"{start_tx_id + i:015d}",
            customer_id=customer.customer_id,
            device_id=device.device_id,
            timestamp=timestamp,
            customer_state=customer.estado,
            customer_profile=customer.perfil,
        )
        transactions.append(tx)
    
    # Export
    exporter = get_exporter(format_name)
    output_path = os.path.join(output_dir, f'transactions_{batch_id:05d}{exporter.extension}')
    exporter.export_batch(transactions, output_path)
    
    return output_path


def generate_customers_and_devices(
    num_customers: int,
    use_profiles: bool,
    seed: Optional[int]
) -> Tuple[List[tuple], List[tuple], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate customers and their devices.
    
    Returns:
        Tuple of (customer_indexes, device_indexes, customer_data, device_data)
    """
    if seed is not None:
        random.seed(seed)
    
    customer_gen = CustomerGenerator(use_profiles=use_profiles, seed=seed)
    device_gen = DeviceGenerator(seed=seed)
    
    customer_indexes = []
    device_indexes = []
    customer_data = []
    device_data = []
    
    device_counter = 1
    
    for i in range(num_customers):
        customer_id = f"CUST_{i+1:012d}"
        customer = customer_gen.generate(customer_id)
        customer_data.append(customer)
        
        # Create index (for pickling to workers)
        customer_idx = CustomerIndex(
            customer_id=customer['customer_id'],
            estado=customer['endereco']['estado'],
            perfil=customer.get('perfil_comportamental'),
            banco_codigo=customer.get('banco_codigo'),
            nivel_risco=customer.get('nivel_risco'),
        )
        customer_indexes.append(tuple(customer_idx))
        
        # Generate devices for customer
        profile = customer.get('perfil_comportamental')
        for device in device_gen.generate_for_customer(
            customer_id,
            profile,
            start_device_id=device_counter
        ):
            device_data.append(device)
            device_idx = DeviceIndex(
                device_id=device['device_id'],
                customer_id=device['customer_id'],
            )
            device_indexes.append(tuple(device_idx))
            device_counter += 1
    
    return customer_indexes, device_indexes, customer_data, device_data


def main():
    parser = argparse.ArgumentParser(
        description="🇧🇷 Brazilian Fraud Data Generator v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --size 1GB --output ./data
  %(prog)s --size 1GB --format csv --output ./data
  %(prog)s --size 1GB --format parquet --output ./data
  %(prog)s --size 1GB --no-profiles --output ./data
  %(prog)s --size 50GB --fraud-rate 0.01 --workers 8
  %(prog)s --size 1GB --seed 42 --output ./data

Available formats: """ + ", ".join(list_formats())
    )
    
    parser.add_argument(
        '--size', '-s',
        type=str,
        default='1GB',
        help='Target size (e.g., 1GB, 500MB, 10GB). Default: 1GB'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./output',
        help='Output directory. Default: ./output'
    )
    
    parser.add_argument(
        '--format', '-f',
        type=str,
        default='jsonl',
        choices=list_formats(),
        help='Export format. Default: jsonl (JSON Lines)'
    )
    
    parser.add_argument(
        '--fraud-rate', '-r',
        type=float,
        default=0.02,
        help='Fraud rate (0.0-1.0). Default: 0.02 (2%%)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=None,
        help='Number of parallel workers. Default: CPU count'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    
    parser.add_argument(
        '--no-profiles',
        action='store_true',
        help='Disable behavioral profiles (random transactions)'
    )
    
    parser.add_argument(
        '--customers', '-c',
        type=int,
        default=None,
        help='Number of unique customers. Default: auto-calculated'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Start date (YYYY-MM-DD). Default: 1 year ago'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date (YYYY-MM-DD). Default: today'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    # Validate format
    if not is_format_available(args.format):
        print(f"❌ Format '{args.format}' is not available.")
        print("   Install dependencies: pip install pyarrow pandas")
        sys.exit(1)
    
    # Parse size
    target_bytes = parse_size(args.size)
    
    # Calculate number of files and transactions
    num_files = max(1, target_bytes // (TARGET_FILE_SIZE_MB * 1024 * 1024))
    total_transactions = num_files * TRANSACTIONS_PER_FILE
    
    # Calculate customers
    if args.customers:
        num_customers = args.customers
    else:
        # ~100 transactions per customer on average
        num_customers = max(1000, total_transactions // 100)
    
    # Date range
    end_date = datetime.now()
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    start_date = end_date - timedelta(days=365)
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    
    # Workers
    workers = args.workers or mp.cpu_count()
    
    # Use profiles (default: True)
    use_profiles = not args.no_profiles
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Print configuration
    print("=" * 60)
    print("🇧🇷 BRAZILIAN FRAUD DATA GENERATOR v3.0")
    print("=" * 60)
    print(f"📦 Target size: {format_size(target_bytes)}")
    print(f"📁 Output: {args.output}")
    print(f"📄 Format: {args.format.upper()}")
    print(f"👥 Customers: {num_customers:,}")
    print(f"💳 Transactions: ~{total_transactions:,}")
    print(f"📊 Files: {num_files}")
    print(f"🎭 Fraud rate: {args.fraud_rate * 100:.1f}%")
    print(f"🧠 Behavioral profiles: {'✅ Enabled' if use_profiles else '❌ Disabled'}")
    print(f"⚡ Workers: {workers}")
    print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
    if args.seed:
        print(f"🎲 Seed: {args.seed}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Phase 1: Generate customers and devices
    print("\n📋 Phase 1: Generating customers and devices...")
    phase1_start = time.time()
    
    customer_indexes, device_indexes, customer_data, device_data = generate_customers_and_devices(
        num_customers=num_customers,
        use_profiles=use_profiles,
        seed=args.seed
    )
    
    phase1_time = time.time() - phase1_start
    print(f"   ✅ Generated {len(customer_data):,} customers, {len(device_data):,} devices")
    print(f"   ⏱️  Time: {format_duration(phase1_time)}")
    
    # Validate CPFs
    print("\n🔍 Validating CPFs...")
    valid_cpfs = sum(1 for c in customer_data if validate_cpf(c['cpf']))
    print(f"   ✅ {valid_cpfs:,}/{len(customer_data):,} CPFs valid ({100*valid_cpfs/len(customer_data):.1f}%)")
    
    # Save customer and device data
    exporter = get_exporter(args.format)
    
    customers_path = os.path.join(args.output, f'customers{exporter.extension}')
    devices_path = os.path.join(args.output, f'devices{exporter.extension}')
    
    exporter.export_batch(customer_data, customers_path)
    exporter.export_batch(device_data, devices_path)
    print(f"   💾 Saved: {customers_path}")
    print(f"   💾 Saved: {devices_path}")
    
    # Phase 2: Generate transactions
    print(f"\n📋 Phase 2: Generating transactions ({num_files} files)...")
    phase2_start = time.time()
    
    # Prepare worker arguments
    worker_args = []
    for batch_id in range(num_files):
        args_tuple = (
            batch_id,
            TRANSACTIONS_PER_FILE,
            customer_indexes,
            device_indexes,
            start_date,
            end_date,
            args.fraud_rate,
            use_profiles,
            args.output,
            args.format,
            args.seed,
        )
        worker_args.append(args_tuple)
    
    # Generate in parallel
    with mp.Pool(workers) as pool:
        results = []
        for i, result in enumerate(pool.imap_unordered(worker_generate_batch, worker_args)):
            results.append(result)
            progress = (i + 1) / num_files * 100
            print(f"\r   Progress: {progress:.1f}% ({i + 1}/{num_files} files)", end='', flush=True)
    
    print()  # New line after progress
    
    phase2_time = time.time() - phase2_start
    
    # Summary
    total_time = time.time() - start_time
    
    # Calculate actual size
    total_size = 0
    for f in os.listdir(args.output):
        fpath = os.path.join(args.output, f)
        if os.path.isfile(fpath):
            total_size += os.path.getsize(fpath)
    
    print("\n" + "=" * 60)
    print("✅ GENERATION COMPLETE")
    print("=" * 60)
    print(f"📦 Total size: {format_size(total_size)}")
    print(f"📁 Files created: {len(results) + 2} (transactions + customers + devices)")
    print(f"💳 Transactions: ~{total_transactions:,}")
    print(f"⏱️  Total time: {format_duration(total_time)}")
    print(f"⚡ Throughput: {total_transactions / total_time:,.0f} tx/sec")
    print(f"📍 Output: {args.output}")
    print("=" * 60)


if __name__ == '__main__':
    main()
