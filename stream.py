#!/usr/bin/env python3
"""
🇧🇷 BRAZILIAN FRAUD DATA GENERATOR - STREAMING MODE
====================================================
Stream realistic Brazilian financial transaction data in real-time
to Kafka, webhooks, or stdout.

Usage:
    # Stream to stdout (debug)
    python3 stream.py --target stdout --rate 5
    
    # Stream to Kafka
    python3 stream.py --target kafka --kafka-server localhost:9092 --kafka-topic transactions --rate 100
    
    # Stream to webhook/REST API
    python3 stream.py --target webhook --webhook-url http://api:8080/ingest --rate 50
    
    # Limit number of events
    python3 stream.py --target stdout --rate 10 --max-events 100
"""

__version__ = "3.1.0"

import argparse
import os
import sys
import time
import random
import signal
from datetime import datetime
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fraud_generator.generators import CustomerGenerator, DeviceGenerator, TransactionGenerator
from fraud_generator.connections import get_connection, list_targets, is_target_available
from fraud_generator.utils import CustomerIndex, DeviceIndex

# Global flag for graceful shutdown
_running = True


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    global _running
    print("\n\n⏹️  Stopping stream...")
    _running = False


def generate_base_data(num_customers: int, use_profiles: bool, seed: Optional[int]):
    """Generate customers and devices for streaming."""
    if seed is not None:
        random.seed(seed)
    
    customer_gen = CustomerGenerator(use_profiles=use_profiles, seed=seed)
    device_gen = DeviceGenerator(seed=seed)
    
    customers = []
    devices = []
    device_counter = 1
    
    print(f"   Generating {num_customers} customers...")
    
    for i in range(num_customers):
        customer_id = f"CUST_{i+1:012d}"
        customer = customer_gen.generate(customer_id)
        
        customer_idx = CustomerIndex(
            customer_id=customer['customer_id'],
            estado=customer['endereco']['estado'],
            perfil=customer.get('perfil_comportamental'),
            banco_codigo=customer.get('banco_codigo'),
            nivel_risco=customer.get('nivel_risco'),
        )
        customers.append(customer_idx)
        
        profile = customer.get('perfil_comportamental')
        for device in device_gen.generate_for_customer(
            customer_id,
            profile,
            start_device_id=device_counter
        ):
            device_idx = DeviceIndex(
                device_id=device['device_id'],
                customer_id=device['customer_id'],
            )
            devices.append(device_idx)
            device_counter += 1
    
    return customers, devices


def run_streaming(
    connection,
    customers,
    devices,
    tx_generator,
    rate: float,
    max_events: Optional[int],
    quiet: bool
):
    """Main streaming loop."""
    global _running
    
    # Build customer-device pairs
    customer_device_map = {}
    for device in devices:
        if device.customer_id not in customer_device_map:
            customer_device_map[device.customer_id] = []
        customer_device_map[device.customer_id].append(device)
    
    pairs = []
    for customer in customers:
        customer_devices = customer_device_map.get(customer.customer_id, [])
        if customer_devices:
            for device in customer_devices:
                pairs.append((customer, device))
    
    if not pairs:
        pairs = [(customers[0], devices[0])]
    
    # Calculate delay between events
    delay = 1.0 / rate if rate > 0 else 0
    
    event_count = 0
    error_count = 0
    start_time = time.time()
    
    while _running:
        # Check max events
        if max_events and event_count >= max_events:
            break
        
        # Select random customer/device
        customer, device = random.choice(pairs)
        
        # Generate transaction with current timestamp
        timestamp = datetime.now()
        
        tx = tx_generator.generate(
            tx_id=f"{event_count:015d}",
            customer_id=customer.customer_id,
            device_id=device.device_id,
            timestamp=timestamp,
            customer_state=customer.estado,
            customer_profile=customer.perfil,
        )
        
        # Send to target
        success = connection.send(tx)
        
        if success:
            event_count += 1
        else:
            error_count += 1
        
        # Progress output
        if not quiet and event_count % 100 == 0:
            elapsed = time.time() - start_time
            actual_rate = event_count / elapsed if elapsed > 0 else 0
            print(f"\r   📊 Events: {event_count:,} | Rate: {actual_rate:.1f}/s | Errors: {error_count}", end='', flush=True)
        
        # Rate limiting
        if delay > 0:
            time.sleep(delay)
    
    return event_count, error_count, time.time() - start_time


def main():
    parser = argparse.ArgumentParser(
        description="🇧🇷 Brazilian Fraud Data Generator - Streaming Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Debug mode (print to terminal)
  %(prog)s --target stdout --rate 5
  
  # Stream to Kafka
  %(prog)s --target kafka --kafka-server localhost:9092 --kafka-topic transactions --rate 100
  
  # Stream to REST API
  %(prog)s --target webhook --webhook-url http://api:8080/ingest --rate 50
  
  # Limited events
  %(prog)s --target stdout --rate 10 --max-events 1000

Available targets: """ + ", ".join(list_targets())
    )
    
    # Target selection
    parser.add_argument(
        '--target', '-t',
        type=str,
        required=True,
        choices=list_targets(),
        help='Streaming target (kafka, webhook, stdout)'
    )
    
    # Rate control
    parser.add_argument(
        '--rate', '-r',
        type=float,
        default=10.0,
        help='Events per second. Default: 10'
    )
    
    parser.add_argument(
        '--max-events', '-n',
        type=int,
        default=None,
        help='Maximum events to generate (infinite if not set)'
    )
    
    # Kafka options
    parser.add_argument(
        '--kafka-server',
        type=str,
        default='localhost:9092',
        help='Kafka bootstrap server. Default: localhost:9092'
    )
    
    parser.add_argument(
        '--kafka-topic',
        type=str,
        default='transactions',
        help='Kafka topic. Default: transactions'
    )
    
    # Webhook options
    parser.add_argument(
        '--webhook-url',
        type=str,
        default=None,
        help='Webhook URL for HTTP target'
    )
    
    parser.add_argument(
        '--webhook-method',
        type=str,
        default='POST',
        choices=['POST', 'PUT', 'PATCH'],
        help='HTTP method. Default: POST'
    )
    
    # Data options
    parser.add_argument(
        '--customers', '-c',
        type=int,
        default=1000,
        help='Number of customers to simulate. Default: 1000'
    )
    
    parser.add_argument(
        '--fraud-rate',
        type=float,
        default=0.02,
        help='Fraud rate (0.0-1.0). Default: 0.02 (2%%)'
    )
    
    parser.add_argument(
        '--no-profiles',
        action='store_true',
        help='Disable behavioral profiles'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    
    # Output options
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON (stdout only)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    # Validate target availability
    if not is_target_available(args.target):
        print(f"❌ Target '{args.target}' is not available.")
        if args.target == 'kafka':
            print("   Install with: pip install kafka-python")
        elif args.target == 'webhook':
            print("   Install with: pip install requests")
        sys.exit(1)
    
    # Validate webhook URL
    if args.target == 'webhook' and not args.webhook_url:
        print("❌ --webhook-url is required for webhook target")
        sys.exit(1)
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Print header
    print("=" * 60)
    print("🇧🇷 BRAZILIAN FRAUD DATA GENERATOR - STREAMING")
    print("=" * 60)
    print(f"🎯 Target: {args.target.upper()}")
    print(f"⚡ Rate: {args.rate} events/second")
    if args.max_events:
        print(f"📊 Max events: {args.max_events:,}")
    else:
        print(f"📊 Max events: ∞ (Ctrl+C to stop)")
    print(f"🎭 Fraud rate: {args.fraud_rate * 100:.1f}%")
    print(f"👥 Customers: {args.customers:,}")
    print(f"🧠 Profiles: {'❌ Disabled' if args.no_profiles else '✅ Enabled'}")
    
    if args.target == 'kafka':
        print(f"📡 Kafka: {args.kafka_server} → {args.kafka_topic}")
    elif args.target == 'webhook':
        print(f"🌐 Webhook: {args.webhook_method} {args.webhook_url}")
    
    print("=" * 60)
    
    # Phase 1: Generate base data
    print("\n📋 Phase 1: Initializing...")
    use_profiles = not args.no_profiles
    
    customers, devices = generate_base_data(
        num_customers=args.customers,
        use_profiles=use_profiles,
        seed=args.seed
    )
    
    print(f"   ✅ Ready: {len(customers)} customers, {len(devices)} devices")
    
    # Phase 2: Setup connection
    print(f"\n📋 Phase 2: Connecting to {args.target}...")
    
    connection = get_connection(args.target)
    
    if args.target == 'kafka':
        connection.connect(
            bootstrap_servers=args.kafka_server,
            topic=args.kafka_topic
        )
        print(f"   ✅ Connected to Kafka")
    
    elif args.target == 'webhook':
        connection.connect(
            url=args.webhook_url,
            method=args.webhook_method
        )
        print(f"   ✅ Webhook configured")
    
    elif args.target == 'stdout':
        connection.connect(pretty=args.pretty)
        print(f"   ✅ Stdout ready")
    
    # Phase 3: Start streaming
    print(f"\n📋 Phase 3: Streaming started...")
    print("   Press Ctrl+C to stop\n")
    
    tx_generator = TransactionGenerator(
        fraud_rate=args.fraud_rate,
        use_profiles=use_profiles,
        seed=args.seed
    )
    
    try:
        event_count, error_count, elapsed = run_streaming(
            connection=connection,
            customers=customers,
            devices=devices,
            tx_generator=tx_generator,
            rate=args.rate,
            max_events=args.max_events,
            quiet=args.quiet
        )
    finally:
        connection.close()
    
    # Summary
    print("\n\n" + "=" * 60)
    print("✅ STREAMING COMPLETE")
    print("=" * 60)
    print(f"📊 Total events: {event_count:,}")
    print(f"❌ Errors: {error_count:,}")
    print(f"⏱️  Duration: {elapsed:.1f}s")
    print(f"⚡ Actual rate: {event_count / elapsed:.1f} events/sec")
    print("=" * 60)


if __name__ == '__main__':
    main()
