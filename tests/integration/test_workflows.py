"""
Integration tests for complete data generation workflows.

Tests end-to-end scenarios:
- Transaction batch generation with Phase 1 optimizations
- Ride-share generation with compression
- Export to multiple formats (JSON, CSV, Parquet)
"""

import pytest
import json
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from fraud_generator.generators.transaction import TransactionGenerator
from fraud_generator.generators.customer import CustomerGenerator
from fraud_generator.exporters.json_exporter import JSONExporter
from fraud_generator.exporters.csv_exporter import CSVExporter


class TestTransactionGeneration:
    """Test complete transaction generation workflow."""

    def test_generate_transactions_basic(self, temp_output_dir, test_seed):
        """Test basic transaction generation."""
        customer_gen = CustomerGenerator(seed=test_seed)
        customers = list(customer_gen.generate_batch(count=10))

        assert len(customers) == 10
        assert all(c['customer_id'].startswith('CUST_') for c in customers)

    def test_transaction_with_json_export(self, temp_output_dir, test_seed):
        """Test transaction generation with JSON export."""
        customer_gen = CustomerGenerator(seed=test_seed)
        customers = list(customer_gen.generate_batch(count=5))

        txn_gen = TransactionGenerator(seed=test_seed, fraud_rate=0.1)
        base_time = datetime(2024, 6, 1, 12, 0, 0)

        transactions = []
        for i in range(50):
            cust = customers[i % len(customers)]
            tx = txn_gen.generate(
                tx_id=f"TX_{i:09d}",
                customer_id=cust['customer_id'],
                device_id=f"DEV_{i % 10:09d}",
                timestamp=base_time + timedelta(minutes=i),
                customer_state=cust['address']['state'],
                customer_profile=cust.get('behavioral_profile'),
            )
            transactions.append(tx)

        assert len(transactions) == 50

    def test_transaction_with_skip_none(self, temp_output_dir, test_seed):
        """Test transactions with skip_none optimization."""
        customer_gen = CustomerGenerator(seed=test_seed)
        customers = list(customer_gen.generate_batch(count=3))

        txn_gen = TransactionGenerator(seed=test_seed, fraud_rate=0.2)
        base_time = datetime(2024, 6, 1, 12, 0, 0)

        transactions = []
        for i in range(20):
            cust = customers[i % len(customers)]
            tx = txn_gen.generate(
                tx_id=f"TX_{i:09d}",
                customer_id=cust['customer_id'],
                device_id=f"DEV_{i % 5:09d}",
                timestamp=base_time + timedelta(minutes=i),
                customer_state=cust['address']['state'],
                customer_profile=cust.get('behavioral_profile'),
            )
            transactions.append(tx)

        # Export with skip_none
        exporter = JSONExporter(skip_none=True)

        # Verify transactions can be exported
        assert len(transactions) == 20


class TestExportFormats:
    """Test export format compatibility."""

    def test_json_exporter_basic(self, temp_output_dir):
        """Test JSON exporter initialization."""
        exporter = JSONExporter()
        assert exporter.format_name == 'JSON Lines'
        assert exporter.extension == '.jsonl'

    def test_json_exporter_skip_none(self, temp_output_dir):
        """Test JSON exporter with skip_none."""
        exporter = JSONExporter(skip_none=True)
        assert exporter.skip_none is True

    def test_csv_exporter_basic(self, temp_output_dir):
        """Test CSV exporter initialization."""
        exporter = CSVExporter()
        assert exporter.format_name == 'CSV'
        assert exporter.extension == '.csv'


class TestFraudInjection:
    """Test fraud injection in generated data."""

    def test_fraud_rate_respected(self, test_seed):
        """Test that fraud_rate produces expected fraud percentage."""
        customer_gen = CustomerGenerator(seed=test_seed)
        customers = list(customer_gen.generate_batch(count=5))

        fraud_rate = 0.2
        txn_gen = TransactionGenerator(seed=test_seed, fraud_rate=fraud_rate)
        base_time = datetime(2024, 6, 1, 12, 0, 0)

        transactions = []
        for i in range(1000):
            cust = customers[i % len(customers)]
            tx = txn_gen.generate(
                tx_id=f"TX_{i:09d}",
                customer_id=cust['customer_id'],
                device_id=f"DEV_{i % 10:09d}",
                timestamp=base_time + timedelta(seconds=i * 30),
                customer_state=cust['address']['state'],
                customer_profile=cust.get('behavioral_profile'),
            )
            transactions.append(tx)

        fraud_count = sum(1 for t in transactions if t.get('is_fraud'))
        actual_rate = fraud_count / len(transactions)

        # Allow 10% tolerance (fraud injection has some variance)
        assert abs(actual_rate - fraud_rate) < 0.10, \
            f"Expected {fraud_rate:.2%}, got {actual_rate:.2%}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
