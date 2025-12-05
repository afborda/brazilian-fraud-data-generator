"""
🇧🇷 Brazilian Fraud Data Generator v3.2.0
==========================================
Generate realistic Brazilian financial transaction data for testing,
development, and machine learning model training.

Features:
- 100% Brazilian data (CPF válido, banks, PIX, addresses)
- Behavioral profiles for realistic patterns
- Multiple export formats (JSON, CSV, Parquet)
- Memory-efficient streaming for large datasets
- Configurable fraud patterns
- Parallel generation for high throughput
- Ride-share data generation (Uber, 99, Cabify, InDriver)
"""

__version__ = "3.2.0"
__author__ = "Abner Fonseca"

from .generators.customer import CustomerGenerator
from .generators.device import DeviceGenerator
from .generators.transaction import TransactionGenerator
from .generators.driver import DriverGenerator
from .generators.ride import RideGenerator
from .exporters import get_exporter
from .validators.cpf import generate_valid_cpf, validate_cpf

__all__ = [
    # Generators
    'CustomerGenerator',
    'DeviceGenerator', 
    'TransactionGenerator',
    'DriverGenerator',
    'RideGenerator',
    # Exporters
    'get_exporter',
    # Validators
    'generate_valid_cpf',
    'validate_cpf',
]
