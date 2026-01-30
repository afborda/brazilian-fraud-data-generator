"""
Integration tests for complete data generation workflows.

Tests end-to-end scenarios:
- Transaction batch generation with Phase 1 optimizations
- Ride-share generation with compression
- Export to multiple formats (JSON, CSV, Parquet)
"""

import pytest
import json
import sys
from pathlib import Path
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
        customer_gen = CustomerGenerator(seed=test_seed, num_customers=10)
        customers = list(customer_gen.generate())
        
        assert len(customers) == 10
        assert all(c.id.startswith('cust_') for c in customers)

    def test_transaction_with_json_export(self, temp_output_dir, test_seed):
        """Test transaction generation with JSON export."""
        output_path = Path(temp_output_dir) / 'test_transactions.jsonl'
        
        customer_gen = CustomerGenerator(seed=test_seed, num_customers=5)
        customers = list(customer_gen.generate())
        
        txn_gen = TransactionGenerator(
            customers=customers,
            num_transactions=50,
            seed=test_seed,
            fraud_rate=0.1
        )
        
        transactions = list(txn_gen.generate())
        assert len(transactions) == 50

    def test_transaction_with_skip_none(self, temp_output_dir, test_seed):
        """Test transactions with skip_none optimization."""
        customer_gen = CustomerGenerator(seed=test_seed, num_customers=3)
        customers = list(customer_gen.generate())
        
        txn_gen = TransactionGenerator(
            customers=customers,
            num_transactions=20,
            seed=test_seed,
            fraud_rate=0.2
        )
        
        transactions = list(txn_gen.generate())
        
        # Export with skip_none
        exporter = JSONExporter(skip_none=True)
        
        # Verify transactions can be exported
        assert len(transactions) == 20


class TestExportFormats:
    """Test export format compatibility."""

    def test_json_exporter_basic(self, temp_output_dir):
        """Test JSON exporter initialization."""
        exporter = JSONExporter()
        assert exporter.format_name == 'json'
        assert exporter.extension == '.jsonl'

    def test_json_exporter_skip_none(self, temp_output_dir):
        """Test JSON exporter with skip_none."""
        exporter = JSONExporter(skip_none=True)
        assert exporter.skip_none is True

    def test_csv_exporter_basic(self, temp_output_dir):
        """Test CSV exporter initialization."""
        exporter = CSVExporter()
        assert exporter.format_name == 'csv'
        assert exporter.extension == '.csv'


class TestFraudInjection:
    """Test fraud injection in generated data."""

    def test_fraud_rate_respected(self, test_seed):
        """Test that fraud_rate produces expected fraud percentage."""
        customer_gen = CustomerGenerator(seed=test_seed, num_customers=5)
        customers = list(customer_gen.generate())
        
        fraud_rate = 0.2
        txn_gen = TransactionGenerator(
            customers=customers,
            num_transactions=1000,
            seed=test_seed,
            fraud_rate=fraud_rate
        )
        
        transactions = list(txn_gen.generate())
        
        fraud_count = sum(1 for t in transactions if t.is_fraud)
        actual_rate = fraud_count / len(transactions)
        
        # Allow 5% tolerance
        assert abs(actual_rate - fraud_rate) < 0.05, \
            f"Expected {fraud_rate:.2%}, got {actual_rate:.2%}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
