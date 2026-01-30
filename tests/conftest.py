"""
Pytest configuration and shared fixtures.

Provides:
- Temporary directories for test outputs
- Mock data generators
- Common test parameters (seeds, sizes)
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix='test_output_')
    yield temp_dir
    # Cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_seed():
    """Return standard test seed for reproducibility."""
    return 42


@pytest.fixture
def small_batch_size():
    """Return small batch size for unit tests."""
    return 100


@pytest.fixture
def sample_customer_data():
    """Return sample customer data for fixtures."""
    return {
        "id": "cust_001",
        "cpf": "12345678909",
        "name": "Test Customer",
        "email": "test@example.com",
        "phone": "+5511999999999",
        "created_at": "2024-01-01T00:00:00",
        "profile": "young_digital"
    }


@pytest.fixture
def sample_transaction_data():
    """Return sample transaction data."""
    return {
        "id": "txn_001",
        "customer_id": "cust_001",
        "amount": 100.50,
        "currency": "BRL",
        "bank": "001",
        "type": "pix",
        "channel": "app",
        "is_fraud": False,
        "fraud_type": None,
        "timestamp": "2024-01-15T12:30:00"
    }


@pytest.fixture
def sample_ride_data():
    """Return sample ride-share data."""
    return {
        "id": "ride_001",
        "passenger_id": "cust_001",
        "driver_id": "driver_001",
        "distance_km": 5.2,
        "duration_minutes": 15,
        "fare_brl": 25.80,
        "app": "uber",
        "is_fraud": False,
        "fraud_type": None,
        "timestamp": "2024-01-15T12:30:00"
    }
