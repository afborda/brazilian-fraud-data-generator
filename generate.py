#!/usr/bin/env python3
"""
🇧🇷 BRAZILIAN FRAUD DATA GENERATOR v3.2.0
=========================================
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
- Ride-share data generation (Uber, 99, Cabify, InDriver)

Usage:
    # Basic usage with profiles (default) - transactions only
    python3 generate.py --size 1GB --output ./output
    
    # Generate ride-share data
    python3 generate.py --size 1GB --type rides --output ./output
    
    # Generate both transactions and rides
    python3 generate.py --size 1GB --type all --output ./output
    
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

__version__ = "3.2.0"

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

from fraud_generator.generators import (
    CustomerGenerator, DeviceGenerator, TransactionGenerator,
    DriverGenerator, RideGenerator,
)
from fraud_generator.exporters import (
    get_exporter, list_formats, is_format_available,
    get_minio_exporter, is_minio_url, MINIO_AVAILABLE,
)
from fraud_generator.utils import (
    CustomerIndex, DeviceIndex, DriverIndex,
    parse_size, format_size, format_duration,
    BatchGenerator,
)
from fraud_generator.validators import validate_cpf

# Configuration
TARGET_FILE_SIZE_MB = 128  # Each file will be ~128MB
BYTES_PER_TRANSACTION = 1050  # ~1KB per JSON transaction
TRANSACTIONS_PER_FILE = (TARGET_FILE_SIZE_MB * 1024 * 1024) // BYTES_PER_TRANSACTION
BYTES_PER_RIDE = 1200  # ~1.2KB per JSON ride
RIDES_PER_FILE = (TARGET_FILE_SIZE_MB * 1024 * 1024) // BYTES_PER_RIDE
RIDES_PER_DRIVER = 50  # Average rides per driver
STREAM_FLUSH_EVERY = 5000  # Flush to disk every N records (memory optimization)


def worker_generate_batch(args: tuple) -> str:
    """
    Worker that generates a batch file with transactions.
    Uses streaming write for memory efficiency - doesn't accumulate all records in memory.
    
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
    
    # Determine output format
    exporter = get_exporter(format_name)
    output_path = os.path.join(output_dir, f'transactions_{batch_id:05d}{exporter.extension}')
    
    start_tx_id = batch_id * num_transactions
    
    # For JSONL format: stream directly to file (memory efficient)
    # For other formats: accumulate (required by format)
    if format_name == 'jsonl':
        # STREAMING MODE - write directly to file, don't accumulate in memory
        with open(output_path, 'w', encoding='utf-8', buffering=65536) as f:
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
                
                # Write directly to file - no memory accumulation!
                f.write(json.dumps(tx, ensure_ascii=False, separators=(',', ':')) + '\n')
                
                # Periodic flush for very large batches
                if i > 0 and i % STREAM_FLUSH_EVERY == 0:
                    f.flush()
    else:
        # BATCH MODE - required for CSV/Parquet formats
        transactions = []
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
        
        # Export batch
        exporter.export_batch(transactions, output_path)
    
    return output_path


def worker_generate_rides_batch(args: tuple) -> str:
    """
    Worker that generates a batch file with rides.
    Uses streaming write for memory efficiency - doesn't accumulate all records in memory.
    
    Args:
        args: Tuple of (batch_id, num_rides, customer_indexes, driver_indexes,
              start_date, end_date, fraud_rate, use_profiles, output_dir, format_name, seed)
    
    Returns:
        Path to generated file
    """
    (batch_id, num_rides, customer_indexes, driver_indexes,
     start_date, end_date, fraud_rate, use_profiles, output_dir, format_name, seed) = args
    
    # Deterministic seed per worker
    if seed is not None:
        worker_seed = seed + batch_id * 54321
    else:
        worker_seed = batch_id * 54321 + int(time.time() * 1000) % 10000
    
    random.seed(worker_seed)
    
    # Reconstruct indexes
    customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
    driver_idx_list = [DriverIndex(*d) for d in driver_indexes]
    
    # Build state-based driver lookup
    drivers_by_state = {}
    for driver in driver_idx_list:
        state = driver.operating_state
        if state not in drivers_by_state:
            drivers_by_state[state] = []
        drivers_by_state[state].append(driver)
    
    # Generate rides
    ride_generator = RideGenerator(
        fraud_rate=fraud_rate,
        use_profiles=use_profiles,
        seed=worker_seed
    )
    
    # Determine output format
    exporter = get_exporter(format_name)
    output_path = os.path.join(output_dir, f'rides_{batch_id:05d}{exporter.extension}')
    
    start_ride_id = batch_id * num_rides
    
    # For JSONL format: stream directly to file (memory efficient)
    # For other formats: accumulate (required by format)
    if format_name == 'jsonl':
        # STREAMING MODE - write directly to file, don't accumulate in memory
        with open(output_path, 'w', encoding='utf-8', buffering=65536) as f:
            for i in range(num_rides):
                # Select random passenger (customer)
                passenger = random.choice(customer_idx_list)
                
                # Select driver from same state if possible
                state_drivers = drivers_by_state.get(passenger.estado, [])
                if state_drivers:
                    driver = random.choice(state_drivers)
                else:
                    driver = random.choice(driver_idx_list)
                
                # Generate timestamp
                days_between = (end_date - start_date).days
                random_day = start_date + timedelta(days=random.randint(0, max(1, days_between)))
                
                hour_weights = {
                    0: 3, 1: 2, 2: 1, 3: 1, 4: 1, 5: 2,
                    6: 5, 7: 8, 8: 12, 9: 10, 10: 8, 11: 8,
                    12: 10, 13: 8, 14: 7, 15: 7, 16: 8, 17: 12,
                    18: 14, 19: 12, 20: 10, 21: 8, 22: 8, 23: 5
                }
                hour = random.choices(list(hour_weights.keys()), weights=list(hour_weights.values()))[0]
                timestamp = random_day.replace(
                    hour=hour,
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                    microsecond=random.randint(0, 999999)
                )
                
                ride = ride_generator.generate(
                    ride_id=f"RIDE_{start_ride_id + i:012d}",
                    driver_id=driver.driver_id,
                    passenger_id=passenger.customer_id,
                    timestamp=timestamp,
                    passenger_state=passenger.estado,
                    passenger_profile=passenger.perfil,
                )
                
                # Write directly to file - no memory accumulation!
                f.write(json.dumps(ride, ensure_ascii=False, separators=(',', ':')) + '\n')
                
                # Periodic flush for very large batches
                if i > 0 and i % STREAM_FLUSH_EVERY == 0:
                    f.flush()
    else:
        # BATCH MODE - required for CSV/Parquet formats
        rides = []
        for i in range(num_rides):
            # Select random passenger (customer)
            passenger = random.choice(customer_idx_list)
            
            # Select driver from same state if possible
            state_drivers = drivers_by_state.get(passenger.estado, [])
            if state_drivers:
                driver = random.choice(state_drivers)
            else:
                driver = random.choice(driver_idx_list)
            
            # Generate timestamp
            days_between = (end_date - start_date).days
            random_day = start_date + timedelta(days=random.randint(0, max(1, days_between)))
            
            hour_weights = {
                0: 3, 1: 2, 2: 1, 3: 1, 4: 1, 5: 2,
                6: 5, 7: 8, 8: 12, 9: 10, 10: 8, 11: 8,
                12: 10, 13: 8, 14: 7, 15: 7, 16: 8, 17: 12,
                18: 14, 19: 12, 20: 10, 21: 8, 22: 8, 23: 5
            }
            hour = random.choices(list(hour_weights.keys()), weights=list(hour_weights.values()))[0]
            timestamp = random_day.replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=random.randint(0, 999999)
            )
            
            ride = ride_generator.generate(
                ride_id=f"RIDE_{start_ride_id + i:012d}",
                driver_id=driver.driver_id,
                passenger_id=passenger.customer_id,
                timestamp=timestamp,
                passenger_state=passenger.estado,
                passenger_profile=passenger.perfil,
            )
            rides.append(ride)
        
        # Export batch
        exporter.export_batch(rides, output_path)
    
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


def generate_drivers(
    num_drivers: int,
    seed: Optional[int]
) -> Tuple[List[tuple], List[Dict[str, Any]]]:
    """
    Generate drivers for ride-share.
    
    Returns:
        Tuple of (driver_indexes, driver_data)
    """
    if seed is not None:
        random.seed(seed)
    
    driver_gen = DriverGenerator(seed=seed)
    
    driver_indexes = []
    driver_data = []
    
    for i in range(num_drivers):
        driver_id = f"DRV_{i+1:010d}"
        driver = driver_gen.generate(driver_id)
        driver_data.append(driver)
        
        # Create index (for pickling to workers)
        driver_idx = DriverIndex(
            driver_id=driver['driver_id'],
            operating_state=driver.get('operating_state', 'SP'),
            operating_city=driver.get('operating_city', 'São Paulo'),
            active_apps=tuple(driver.get('active_apps', [])),
        )
        driver_indexes.append(tuple(driver_idx))
    
    return driver_indexes, driver_data


def main():
    parser = argparse.ArgumentParser(
        description="🇧🇷 Brazilian Fraud Data Generator v3.2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --size 1GB --output ./data
  %(prog)s --size 1GB --type rides --output ./data
  %(prog)s --size 1GB --type all --output ./data
  %(prog)s --size 1GB --format csv --output ./data
  %(prog)s --size 1GB --format parquet --output ./data
  %(prog)s --size 1GB --no-profiles --output ./data
  %(prog)s --size 50GB --fraud-rate 0.01 --workers 8
  %(prog)s --size 1GB --seed 42 --output ./data
  
  # MinIO/S3 direct upload:
  %(prog)s --size 1GB --output minio://fraud-data/raw
  %(prog)s --size 1GB --output s3://fraud-data/raw --minio-endpoint http://minio:9000

Available formats: """ + ", ".join(list_formats())
    )
    
    parser.add_argument(
        '--type', '-t',
        type=str,
        default='transactions',
        choices=['transactions', 'rides', 'all'],
        help='Type of data to generate: transactions, rides, or all. Default: transactions'
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
        help='Output directory or MinIO URL (minio://bucket/prefix). Default: ./output'
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
    
    # MinIO arguments
    parser.add_argument(
        '--minio-endpoint',
        type=str,
        default=None,
        help='MinIO endpoint URL (e.g., http://minio:9000). Default: MINIO_ENDPOINT env'
    )
    
    parser.add_argument(
        '--minio-access-key',
        type=str,
        default=None,
        help='MinIO access key. Default: MINIO_ROOT_USER env'
    )
    
    parser.add_argument(
        '--minio-secret-key',
        type=str,
        default=None,
        help='MinIO secret key. Default: MINIO_ROOT_PASSWORD env'
    )
    
    parser.add_argument(
        '--no-date-partition',
        action='store_true',
        help='Disable date partitioning in MinIO (YYYY/MM/DD)'
    )
    
    parser.add_argument(
        '--no-profiles',
        action='store_true',
        help='Disable behavioral profiles (random transactions/rides)'
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
    
    # Check if output is MinIO URL
    use_minio = is_minio_url(args.output)
    
    # Validate MinIO availability
    if use_minio and not MINIO_AVAILABLE:
        print("❌ MinIO output requires boto3.")
        print("   Install with: pip install boto3")
        sys.exit(1)
    
    # Validate format (MinIO only supports jsonl)
    if use_minio and args.format != 'jsonl':
        print(f"⚠️  MinIO output only supports JSONL format. Ignoring --format {args.format}")
        args.format = 'jsonl'
    
    # Validate format
    if not use_minio and not is_format_available(args.format):
        print(f"❌ Format '{args.format}' is not available.")
        print("   Install dependencies: pip install pyarrow pandas")
        sys.exit(1)
    
    # Parse size
    target_bytes = parse_size(args.size)
    
    # Determine what to generate
    generate_transactions = args.type in ('transactions', 'all')
    generate_rides = args.type in ('rides', 'all')
    
    # Calculate number of files
    num_files = max(1, target_bytes // (TARGET_FILE_SIZE_MB * 1024 * 1024))
    
    # Calculate totals based on type
    if generate_transactions:
        total_transactions = num_files * TRANSACTIONS_PER_FILE
    else:
        total_transactions = 0
    
    if generate_rides:
        total_rides = num_files * RIDES_PER_FILE
        num_drivers = max(100, total_rides // RIDES_PER_DRIVER)
    else:
        total_rides = 0
        num_drivers = 0
    
    # Calculate customers
    if args.customers:
        num_customers = args.customers
    else:
        # Auto-calculate based on type
        if generate_transactions and generate_rides:
            num_customers = max(1000, (total_transactions + total_rides) // 100)
        elif generate_transactions:
            num_customers = max(1000, total_transactions // 100)
        else:
            num_customers = max(1000, total_rides // 50)  # ~50 rides per passenger
    
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
    
    # Setup output (local or MinIO)
    if use_minio:
        # MinIO output - create exporter
        minio_exporter = get_minio_exporter(
            minio_url=args.output,
            endpoint_url=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            partition_by_date=not args.no_date_partition,
        )
        output_dir = None  # Not used for MinIO
        exporter = minio_exporter
    else:
        # Local output - create directory
        os.makedirs(args.output, exist_ok=True)
        output_dir = args.output
        exporter = get_exporter(args.format)
        minio_exporter = None
    
    # Print configuration
    print("=" * 60)
    print("🇧🇷 BRAZILIAN FRAUD DATA GENERATOR v3.2.0")
    print("=" * 60)
    print(f"📦 Target size: {format_size(target_bytes)}")
    if use_minio:
        print(f"☁️  Output: {args.output} (MinIO)")
        if args.minio_endpoint:
            print(f"   Endpoint: {args.minio_endpoint}")
    else:
        print(f"📁 Output: {args.output}")
    print(f"📄 Format: {args.format.upper()}")
    print(f"🎯 Type: {args.type.upper()}")
    print(f"👥 Customers: {num_customers:,}")
    if generate_transactions:
        print(f"💳 Transactions: ~{total_transactions:,}")
    if generate_rides:
        print(f"🚗 Drivers: {num_drivers:,}")
        print(f"🚗 Rides: ~{total_rides:,}")
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
    if use_minio:
        # Upload to MinIO
        exporter.export_batch(customer_data, 'customers.jsonl')
        exporter.export_batch(device_data, 'devices.jsonl')
        print(f"   💾 Uploaded: customers.jsonl to MinIO")
        print(f"   💾 Uploaded: devices.jsonl to MinIO")
    else:
        # Save locally
        customers_path = os.path.join(args.output, f'customers{exporter.extension}')
        devices_path = os.path.join(args.output, f'devices{exporter.extension}')
        exporter.export_batch(customer_data, customers_path)
        exporter.export_batch(device_data, devices_path)
        print(f"   💾 Saved: {customers_path}")
        print(f"   💾 Saved: {devices_path}")
    
    tx_results = []
    ride_results = []
    
    # Phase 2: Generate transactions (if requested)
    if generate_transactions:
        print(f"\n📋 Phase 2: Generating transactions ({num_files} files)...")
        phase2_start = time.time()
        
        if use_minio:
            # For MinIO, generate and upload directly (no multiprocessing for now)
            # TODO: Add multiprocessing support for MinIO
            for batch_id in range(num_files):
                # Generate in memory
                tx_generator = TransactionGenerator(
                    fraud_rate=args.fraud_rate,
                    use_profiles=use_profiles,
                    seed=args.seed + batch_id * 12345 if args.seed else None
                )
                
                customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
                device_idx_list = [DeviceIndex(*d) for d in device_indexes]
                
                # Build pairs
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
                    pairs = [(customer_idx_list[0], device_idx_list[0])]
                
                transactions = []
                start_tx_id = batch_id * TRANSACTIONS_PER_FILE
                
                for i in range(TRANSACTIONS_PER_FILE):
                    customer, device = random.choice(pairs)
                    days_between = (end_date - start_date).days
                    random_day = start_date + timedelta(days=random.randint(0, max(1, days_between)))
                    timestamp = random_day.replace(
                        hour=random.randint(6, 23),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
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
                
                # Upload to MinIO
                filename = f'transactions_{batch_id:05d}.jsonl'
                exporter.export_batch(transactions, filename)
                tx_results.append(filename)
                
                progress = (batch_id + 1) / num_files * 100
                print(f"\r   Progress: {progress:.1f}% ({batch_id + 1}/{num_files} files)", end='', flush=True)
            
            print()
        else:
            # Local: use multiprocessing
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
            for i, result in enumerate(pool.imap_unordered(worker_generate_batch, worker_args)):
                tx_results.append(result)
                progress = (i + 1) / num_files * 100
                print(f"\r   Progress: {progress:.1f}% ({i + 1}/{num_files} files)", end='', flush=True)
        
        print()  # New line after progress
        phase2_time = time.time() - phase2_start
        print(f"   ⏱️  Time: {format_duration(phase2_time)}")
    
    # Phase 3: Generate drivers (if rides requested)
    driver_indexes = []
    if generate_rides:
        print(f"\n📋 Phase 3: Generating drivers ({num_drivers:,})...")
        phase3_start = time.time()
        
        driver_indexes, driver_data = generate_drivers(
            num_drivers=num_drivers,
            seed=args.seed
        )
        
        phase3_time = time.time() - phase3_start
        print(f"   ✅ Generated {len(driver_data):,} drivers")
        print(f"   ⏱️  Time: {format_duration(phase3_time)}")
        
        # Save driver data
        if use_minio:
            exporter.export_batch(driver_data, 'drivers.jsonl')
            print(f"   💾 Uploaded: drivers.jsonl to MinIO")
        else:
            drivers_path = os.path.join(args.output, f'drivers{exporter.extension}')
            exporter.export_batch(driver_data, drivers_path)
            print(f"   💾 Saved: {drivers_path}")
        
        # Validate driver CPFs
        print("\n🔍 Validating driver CPFs...")
        valid_driver_cpfs = sum(1 for d in driver_data if validate_cpf(d['cpf']))
        print(f"   ✅ {valid_driver_cpfs:,}/{len(driver_data):,} CPFs valid ({100*valid_driver_cpfs/len(driver_data):.1f}%)")
    
    # Phase 4: Generate rides (if requested)
    if generate_rides:
        print(f"\n📋 Phase 4: Generating rides ({num_files} files)...")
        phase4_start = time.time()
        
        if use_minio:
            # For MinIO, generate and upload directly (no multiprocessing)
            from src.fraud_generator.generators.transaction import RideGenerator
            
            for batch_id in range(num_files):
                ride_generator = RideGenerator(
                    fraud_rate=args.fraud_rate,
                    use_profiles=use_profiles,
                    seed=args.seed + batch_id * 54321 if args.seed else None
                )
                
                customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
                driver_idx_list = [DriverIndex(*d) for d in driver_indexes]
                
                # Build pairs
                pairs = [(c, d) for c in customer_idx_list for d in driver_idx_list[:10]]
                if not pairs:
                    pairs = [(customer_idx_list[0], driver_idx_list[0])]
                
                rides = []
                start_ride_id = batch_id * RIDES_PER_FILE
                
                for i in range(RIDES_PER_FILE):
                    customer, driver = random.choice(pairs)
                    days_between = (end_date - start_date).days
                    random_day = start_date + timedelta(days=random.randint(0, max(1, days_between)))
                    timestamp = random_day.replace(
                        hour=random.randint(6, 23),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )
                    
                    ride = ride_generator.generate(
                        ride_id=f"R{start_ride_id + i:015d}",
                        customer_id=customer.customer_id,
                        driver_id=driver.driver_id,
                        timestamp=timestamp,
                        customer_state=customer.estado,
                        customer_profile=customer.perfil,
                    )
                    rides.append(ride)
                
                # Upload to MinIO
                filename = f'rides_{batch_id:05d}.jsonl'
                exporter.export_batch(rides, filename)
                ride_results.append(filename)
                
                progress = (batch_id + 1) / num_files * 100
                print(f"\r   Progress: {progress:.1f}% ({batch_id + 1}/{num_files} files)", end='', flush=True)
            
            print()
        else:
            # Local: use multiprocessing
            # Prepare worker arguments for rides
            ride_worker_args = []
            for batch_id in range(num_files):
                args_tuple = (
                    batch_id,
                    RIDES_PER_FILE,
                    customer_indexes,
                    driver_indexes,
                    start_date,
                    end_date,
                    args.fraud_rate,
                    use_profiles,
                    args.output,
                    args.format,
                    args.seed,
                )
                ride_worker_args.append(args_tuple)
            
            # Generate in parallel
            with mp.Pool(workers) as pool:
                for i, result in enumerate(pool.imap_unordered(worker_generate_rides_batch, ride_worker_args)):
                    ride_results.append(result)
                    progress = (i + 1) / num_files * 100
                    print(f"\r   Progress: {progress:.1f}% ({i + 1}/{num_files} files)", end='', flush=True)
            
            print()  # New line after progress
        
        phase4_time = time.time() - phase4_start
        print(f"   ⏱️  Time: {format_duration(phase4_time)}")
    
    # Summary
    total_time = time.time() - start_time
    
    # Calculate actual size
    total_size = 0
    if use_minio:
        # For MinIO, estimate based on records (actual size tracking would require API calls)
        # Approximate: ~500 bytes per transaction, ~800 bytes per ride
        total_size = (total_transactions * 500) + (total_rides * 800) + (num_customers * 400) + (len(device_data) * 300)
        if generate_rides:
            total_size += num_drivers * 350
    else:
        for f in os.listdir(args.output):
            fpath = os.path.join(args.output, f)
            if os.path.isfile(fpath):
                total_size += os.path.getsize(fpath)
    
    # Count files
    base_files = 2  # customers + devices
    if generate_rides:
        base_files += 1  # drivers
    total_files = base_files + len(tx_results) + len(ride_results)
    
    print("\n" + "=" * 60)
    print("✅ GENERATION COMPLETE")
    print("=" * 60)
    if use_minio:
        print(f"📦 Estimated size: ~{format_size(total_size)}")
    else:
        print(f"📦 Total size: {format_size(total_size)}")
    print(f"📁 Files created: {total_files}")
    if generate_transactions:
        print(f"💳 Transactions: ~{total_transactions:,}")
    if generate_rides:
        print(f"🚗 Rides: ~{total_rides:,}")
    print(f"⏱️  Total time: {format_duration(total_time)}")
    
    total_records = total_transactions + total_rides
    if total_records > 0:
        print(f"⚡ Throughput: {total_records / total_time:,.0f} records/sec")
    
    if use_minio:
        print(f"📍 Output: {args.output} (MinIO)")
    else:
        print(f"📍 Output: {args.output}")
    print("=" * 60)


if __name__ == '__main__':
    main()
