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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
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
    BatchGenerator, ProgressTracker,
)
from fraud_generator.validators import validate_cpf

# Configuration
TARGET_FILE_SIZE_MB = 128  # Each file will be ~128MB
# IMPORTANT: Real JSONL size is ~500 bytes per transaction after formatting
# Using 500 bytes ensures --size 10GB actually generates ~10GB of data
BYTES_PER_TRANSACTION = 500  # Adjusted from 1050 to match real output size
TRANSACTIONS_PER_FILE = (TARGET_FILE_SIZE_MB * 1024 * 1024) // BYTES_PER_TRANSACTION
BYTES_PER_RIDE = 600  # Adjusted from 1200 to match real output size
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
                    customer_state=customer.state,
                    customer_profile=customer.profile,
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
                customer_state=customer.state,
                customer_profile=customer.profile,
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
                state_drivers = drivers_by_state.get(passenger.state, [])
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
                    passenger_state=passenger.state,
                    passenger_profile=passenger.profile,
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
            state_drivers = drivers_by_state.get(passenger.state, [])
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
                passenger_state=passenger.state,
                passenger_profile=passenger.profile,
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
            state=customer['address']['state'],
            profile=customer.get('behavioral_profile'),
            bank_code=customer.get('bank_code'),
            risk_level=customer.get('risk_level'),
        )
        customer_indexes.append(tuple(customer_idx))
        
        # Generate devices for customer
        profile = customer.get('behavioral_profile')
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


# =============================================================================
# PROCESSPOOL WORKERS (Top-level functions for pickling)
# =============================================================================

def _worker_generate_and_upload_parquet_tx(args: tuple) -> str:
    """
    Standalone worker for ProcessPoolExecutor - generates transactions and uploads Parquet to MinIO.
    
    IMPORTANT: This must be a top-level function (not nested) to be picklable.
    Credentials are passed as arguments since child processes don't inherit os.environ reliably.
    Creates boto3 client inside the worker process.
    
    Args:
        args: Tuple containing all necessary parameters
        
    Returns:
        Filename of uploaded file
    """
    import pandas as pd
    import tempfile
    import gc
    
    (batch_id, num_transactions, customer_indexes, device_indexes,
     start_date, end_date, fraud_rate, use_profiles, seed,
     minio_endpoint, minio_access_key, minio_secret_key, 
     bucket_name, object_prefix, compression) = args
    
    # Generate transactions using existing function
    transactions = minio_generate_transaction_batch(
        batch_id=batch_id,
        num_transactions=num_transactions,
        customer_indexes=customer_indexes,
        device_indexes=device_indexes,
        start_date=start_date,
        end_date=end_date,
        fraud_rate=fraud_rate,
        use_profiles=use_profiles,
        seed=seed,
    )
    
    # Flatten nested dicts for DataFrame
    def flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    flat_data = [flatten_dict(tx) for tx in transactions]
    df = pd.DataFrame(flat_data)
    
    # Write to temp file with compression
    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    local_path = tmpf.name
    tmpf.close()
    
    try:
        # Write Parquet with specified compression (zstd default)
        df.to_parquet(local_path, engine='pyarrow', compression=compression, index=False)
        
        # Create boto3 client IN THE CHILD PROCESS
        import boto3
        from botocore.config import Config
        
        s3_client = boto3.client(
            's3',
            endpoint_url=minio_endpoint,
            aws_access_key_id=minio_access_key,
            aws_secret_access_key=minio_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
        )
        
        # Upload file
        object_key = f'{object_prefix}/transactions_{batch_id:05d}.parquet' if object_prefix else f'transactions_{batch_id:05d}.parquet'
        with open(local_path, 'rb') as f:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=f.read(),
                ContentType='application/octet-stream',
            )
        
        return f'transactions_{batch_id:05d}.parquet'
    finally:
        # Cleanup
        os.remove(local_path)
        del df, transactions, flat_data
        gc.collect()


def _worker_generate_and_upload_parquet_rides(args: tuple) -> str:
    """
    Standalone worker for ProcessPoolExecutor - generates rides and uploads Parquet to MinIO.
    
    IMPORTANT: This must be a top-level function (not nested) to be picklable.
    """
    import pandas as pd
    import tempfile
    import gc
    
    (batch_id, num_rides, customer_indexes, driver_indexes,
     start_date, end_date, fraud_rate, use_profiles, seed,
     minio_endpoint, minio_access_key, minio_secret_key,
     bucket_name, object_prefix, compression) = args
    
    # Generate rides using existing function
    rides = minio_generate_ride_batch(
        batch_id=batch_id,
        num_rides=num_rides,
        customer_indexes=customer_indexes,
        driver_indexes=driver_indexes,
        start_date=start_date,
        end_date=end_date,
        fraud_rate=fraud_rate,
        use_profiles=use_profiles,
        seed=seed,
    )
    
    # Flatten nested dicts for DataFrame
    def flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    flat_data = [flatten_dict(ride) for ride in rides]
    df = pd.DataFrame(flat_data)
    
    # Write to temp file
    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    local_path = tmpf.name
    tmpf.close()
    
    try:
        df.to_parquet(local_path, engine='pyarrow', compression=compression, index=False)
        
        # Create boto3 client IN THE CHILD PROCESS
        import boto3
        from botocore.config import Config
        
        s3_client = boto3.client(
            's3',
            endpoint_url=minio_endpoint,
            aws_access_key_id=minio_access_key,
            aws_secret_access_key=minio_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
        )
        
        # Upload file
        object_key = f'{object_prefix}/rides_{batch_id:05d}.parquet' if object_prefix else f'rides_{batch_id:05d}.parquet'
        with open(local_path, 'rb') as f:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=f.read(),
                ContentType='application/octet-stream',
            )
        
        return f'rides_{batch_id:05d}.parquet'
    finally:
        os.remove(local_path)
        del df, rides, flat_data
        gc.collect()


def minio_generate_transaction_batch(
    batch_id: int,
    num_transactions: int,
    customer_indexes: List[tuple],
    device_indexes: List[tuple],
    start_date: datetime,
    end_date: datetime,
    fraud_rate: float,
    use_profiles: bool,
    seed: Optional[int],
) -> List[Dict[str, Any]]:
    """
    Generate a batch of transactions in memory (for MinIO upload).
    
    Returns:
        List of transaction dictionaries
    """
    # Deterministic seed per batch
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
        
        # Generate timestamp with realistic distribution
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
            customer_state=customer.state,
            customer_profile=customer.profile,
        )
        transactions.append(tx)
    
    return transactions


def minio_generate_ride_batch(
    batch_id: int,
    num_rides: int,
    customer_indexes: List[tuple],
    driver_indexes: List[tuple],
    start_date: datetime,
    end_date: datetime,
    fraud_rate: float,
    use_profiles: bool,
    seed: Optional[int],
) -> List[Dict[str, Any]]:
    """
    Generate a batch of rides in memory (for MinIO upload).
    
    Returns:
        List of ride dictionaries
    """
    # Deterministic seed per batch
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
    
    rides = []
    start_ride_id = batch_id * num_rides
    
    for i in range(num_rides):
        # Select random passenger
        passenger = random.choice(customer_idx_list)
        
        # Select driver from same state if possible
        state_drivers = drivers_by_state.get(passenger.state, [])
        if state_drivers:
            driver = random.choice(state_drivers)
        else:
            driver = random.choice(driver_idx_list)
        
        # Generate timestamp with realistic distribution
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
            passenger_state=passenger.state,
            passenger_profile=passenger.profile,
        )
        rides.append(ride)
    
    return rides


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
        '--compression',
        type=str,
        default='zstd',
        choices=['snappy', 'zstd', 'gzip', 'brotli', 'none'],
        help='Compression for Parquet files. zstd offers best compression/speed ratio. Default: zstd'
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
    
    # Validate format for MinIO (supports jsonl, csv, parquet)
    if use_minio:
        supported_minio_formats = ('jsonl', 'csv', 'parquet')
        if args.format not in supported_minio_formats:
            print(f"⚠️  MinIO output supports: {', '.join(supported_minio_formats)}. Ignoring --format {args.format}")
            args.format = 'jsonl'
        # Check parquet dependencies for MinIO
        if args.format == 'parquet':
            try:
                import pyarrow
                import pandas
            except ImportError:
                print("❌ Parquet format requires pyarrow and pandas.")
                print("   Install with: pip install pyarrow pandas")
                sys.exit(1)
    
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
    
    # Compression (handle 'none' -> None)
    compression = args.compression if args.compression != 'none' else None
    
    # Setup output (local or MinIO)
    if use_minio:
        # MinIO output - create exporter
        minio_exporter = get_minio_exporter(
            minio_url=args.output,
            endpoint_url=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            partition_by_date=not args.no_date_partition,
            output_format=args.format,  # Pass the format to MinIO exporter
            compression=compression,  # Pass compression setting
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
    if args.format == 'parquet':
        print(f"🗜️  Compression: {args.compression.upper()}")
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
    print("\n" + "=" * 60)
    print("📋 FASE 1: Gerando clientes e dispositivos")
    print("=" * 60)
    
    output_display = args.output if not use_minio else f"{args.output} (MinIO)"
    progress_phase1 = ProgressTracker(
        total=num_customers,
        description="Gerando clientes e dispositivos",
        unit="clientes",
        output_path=output_display,
    )
    progress_phase1.start()
    
    phase1_start = time.time()
    
    customer_indexes, device_indexes, customer_data, device_data = generate_customers_and_devices(
        num_customers=num_customers,
        use_profiles=use_profiles,
        seed=args.seed
    )
    
    progress_phase1.current = num_customers
    progress_phase1._print_progress()
    progress_phase1.finish(show_summary=False)
    
    phase1_time = time.time() - phase1_start
    print(f"   ✅ Gerados {len(customer_data):,} clientes, {len(device_data):,} dispositivos")
    print(f"   ⏱️  Tempo: {format_duration(phase1_time)}")
    
    # Validate CPFs
    print("\n🔍 Validando CPFs...")
    valid_cpfs = sum(1 for c in customer_data if validate_cpf(c['cpf']))
    print(f"   ✅ {valid_cpfs:,}/{len(customer_data):,} CPFs válidos ({100*valid_cpfs/len(customer_data):.1f}%)")
    
    # Save customer and device data
    print("\n💾 Salvando dados de clientes e dispositivos...")
    if use_minio:
        # Upload to MinIO (exporter will handle correct extension)
        exporter.export_batch(customer_data, 'customers')
        exporter.export_batch(device_data, 'devices')
        print(f"   📤 Enviado: customers{exporter.extension} para MinIO")
        print(f"   📤 Enviado: devices{exporter.extension} para MinIO")
    else:
        # Save locally
        customers_path = os.path.join(args.output, f'customers{exporter.extension}')
        devices_path = os.path.join(args.output, f'devices{exporter.extension}')
        exporter.export_batch(customer_data, customers_path)
        exporter.export_batch(device_data, devices_path)
        print(f"   💾 Salvo: {customers_path}")
        print(f"   💾 Salvo: {devices_path}")
    
    tx_results = []
    ride_results = []
    
    # Phase 2: Generate transactions (if requested)
    if generate_transactions:
        print("\n" + "=" * 60)
        print("📋 FASE 2: Gerando transações")
        print("=" * 60)
        
        progress_tx = ProgressTracker(
            total=num_files,
            description="Gerando arquivos de transações",
            unit="arquivos",
            output_path=output_display,
        )
        progress_tx.start()
        
        phase2_start = time.time()
        
        if use_minio:
            # For MinIO + Parquet: use ProcessPoolExecutor (bypasses GIL for CPU-bound work)
            # For other formats: use ThreadPoolExecutor
            if args.format == 'parquet':
                # ProcessPoolExecutor for Parquet - TRUE parallelism!
                # Get MinIO credentials from exporter or environment
                minio_endpoint = exporter.endpoint_url
                minio_access_key = exporter.access_key
                minio_secret_key = exporter.secret_key
                bucket_name = exporter.bucket
                object_prefix = exporter.prefix
                parquet_compression = compression
                
                # Prepare worker arguments (must be picklable - no closures!)
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
                        args.seed,
                        minio_endpoint,
                        minio_access_key,
                        minio_secret_key,
                        bucket_name,
                        object_prefix,
                        parquet_compression,
                    )
                    worker_args.append(args_tuple)
                
                # Use ProcessPoolExecutor - bypasses GIL for real parallelism!
                # Limit to min(workers, num_files, cpu_count) for optimal performance
                max_process_workers = min(workers, num_files, mp.cpu_count())
                print(f"   🚀 Usando ProcessPoolExecutor com {max_process_workers} processos (bypass GIL)")
                
                with ProcessPoolExecutor(max_workers=max_process_workers) as executor:
                    futures = {executor.submit(_worker_generate_and_upload_parquet_tx, args): i 
                               for i, args in enumerate(worker_args)}
                    for future in as_completed(futures):
                        filename = future.result()
                        tx_results.append(filename)
                        progress_tx.update(1)
            else:
                # ThreadPoolExecutor for JSONL/CSV (I/O bound)
                def generate_and_upload_tx_batch(batch_id: int) -> str:
                    """Generate transactions and upload to MinIO."""
                    transactions = minio_generate_transaction_batch(
                        batch_id=batch_id,
                        num_transactions=TRANSACTIONS_PER_FILE,
                        customer_indexes=customer_indexes,
                        device_indexes=device_indexes,
                        start_date=start_date,
                        end_date=end_date,
                        fraud_rate=args.fraud_rate,
                        use_profiles=use_profiles,
                        seed=args.seed,
                    )
                    filename = f'transactions_{batch_id:05d}'
                    exporter.export_batch(transactions, filename)
                    return filename
                
                # Use ThreadPoolExecutor for parallel I/O
                max_workers = min(workers, num_files, 16)
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(generate_and_upload_tx_batch, i): i for i in range(num_files)}
                    for future in as_completed(futures):
                        filename = future.result()
                        tx_results.append(filename)
                        progress_tx.update(1)
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
                    progress_tx.update(1)
        
        progress_tx.finish()
        phase2_time = time.time() - phase2_start
        print(f"   💳 Total de transações: ~{total_transactions:,}")
    
    # Phase 3: Generate drivers (if rides requested)
    driver_indexes = []
    if generate_rides:
        print("\n" + "=" * 60)
        print("📋 FASE 3: Gerando motoristas")
        print("=" * 60)
        
        progress_drivers = ProgressTracker(
            total=num_drivers,
            description="Gerando motoristas",
            unit="motoristas",
            output_path=output_display,
        )
        progress_drivers.start()
        
        phase3_start = time.time()
        
        driver_indexes, driver_data = generate_drivers(
            num_drivers=num_drivers,
            seed=args.seed
        )
        
        progress_drivers.current = num_drivers
        progress_drivers._print_progress()
        progress_drivers.finish(show_summary=False)
        
        phase3_time = time.time() - phase3_start
        print(f"   ✅ Gerados {len(driver_data):,} motoristas")
        print(f"   ⏱️  Tempo: {format_duration(phase3_time)}")
        
        # Save driver data
        print("\n💾 Salvando dados de motoristas...")
        if use_minio:
            exporter.export_batch(driver_data, 'drivers')
            print(f"   📤 Enviado: drivers{exporter.extension} para MinIO")
        else:
            drivers_path = os.path.join(args.output, f'drivers{exporter.extension}')
            exporter.export_batch(driver_data, drivers_path)
            print(f"   💾 Salvo: {drivers_path}")
        
        # Validate driver CPFs
        print("\n🔍 Validando CPFs dos motoristas...")
        valid_driver_cpfs = sum(1 for d in driver_data if validate_cpf(d['cpf']))
        print(f"   ✅ {valid_driver_cpfs:,}/{len(driver_data):,} CPFs válidos ({100*valid_driver_cpfs/len(driver_data):.1f}%)")
    
    # Phase 4: Generate rides (if requested)
    if generate_rides:
        print("\n" + "=" * 60)
        print("📋 FASE 4: Gerando corridas")
        print("=" * 60)
        
        progress_rides = ProgressTracker(
            total=num_files,
            description="Gerando arquivos de corridas",
            unit="arquivos",
            output_path=output_display,
        )
        progress_rides.start()
        
        phase4_start = time.time()
        
        if use_minio:
            # For MinIO + Parquet: use ProcessPoolExecutor (bypasses GIL for CPU-bound work)
            # For other formats: use ThreadPoolExecutor
            if args.format == 'parquet':
                # ProcessPoolExecutor for Parquet - TRUE parallelism!
                minio_endpoint = exporter.endpoint_url
                minio_access_key = exporter.access_key
                minio_secret_key = exporter.secret_key
                bucket_name = exporter.bucket
                object_prefix = exporter.prefix
                parquet_compression = compression
                
                # Prepare worker arguments
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
                        args.seed,
                        minio_endpoint,
                        minio_access_key,
                        minio_secret_key,
                        bucket_name,
                        object_prefix,
                        parquet_compression,
                    )
                    ride_worker_args.append(args_tuple)
                
                # Use ProcessPoolExecutor - bypasses GIL!
                max_process_workers = min(workers, num_files, mp.cpu_count())
                print(f"   🚀 Usando ProcessPoolExecutor com {max_process_workers} processos (bypass GIL)")
                
                with ProcessPoolExecutor(max_workers=max_process_workers) as executor:
                    futures = {executor.submit(_worker_generate_and_upload_parquet_rides, args): i 
                               for i, args in enumerate(ride_worker_args)}
                    for future in as_completed(futures):
                        filename = future.result()
                        ride_results.append(filename)
                        progress_rides.update(1)
            else:
                # ThreadPoolExecutor for JSONL/CSV (I/O bound)
                def generate_and_upload_ride_batch(batch_id: int) -> str:
                    """Generate rides and upload to MinIO."""
                    rides = minio_generate_ride_batch(
                        batch_id=batch_id,
                        num_rides=RIDES_PER_FILE,
                        customer_indexes=customer_indexes,
                        driver_indexes=driver_indexes,
                        start_date=start_date,
                        end_date=end_date,
                        fraud_rate=args.fraud_rate,
                        use_profiles=use_profiles,
                        seed=args.seed,
                    )
                    filename = f'rides_{batch_id:05d}'
                    exporter.export_batch(rides, filename)
                    return filename
                
                # Use ThreadPoolExecutor for parallel I/O
                max_workers = min(workers, num_files, 16)
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(generate_and_upload_ride_batch, i): i for i in range(num_files)}
                    for future in as_completed(futures):
                        filename = future.result()
                        ride_results.append(filename)
                        progress_rides.update(1)
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
                    progress_rides.update(1)
        
        progress_rides.finish()
        phase4_time = time.time() - phase4_start
        print(f"   🚗 Total de corridas: ~{total_rides:,}")
    
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
    print("✅ GERAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    if use_minio:
        print(f"📦 Tamanho estimado: ~{format_size(total_size)}")
    else:
        print(f"📦 Tamanho total: {format_size(total_size)}")
    print(f"📁 Arquivos criados: {total_files}")
    if generate_transactions:
        print(f"💳 Transações: ~{total_transactions:,}")
    if generate_rides:
        print(f"🚗 Corridas: ~{total_rides:,}")
    print(f"⏱️  Tempo total: {format_duration(total_time)}")
    
    total_records = total_transactions + total_rides
    if total_records > 0:
        print(f"⚡ Velocidade: {total_records / total_time:,.0f} registros/seg")
    
    if use_minio:
        print(f"📍 Destino: {args.output} (MinIO)")
    else:
        print(f"📍 Destino: {args.output}")
    print("=" * 60)
    print("\n🎉 Todos os dados foram gerados e salvos com sucesso!")


if __name__ == '__main__':
    main()
