"""
🇧🇷 Brazilian Fraud Data Generator v3.0
=======================================
Generate realistic Brazilian financial transaction data for testing,
development, and machine learning model training.

Features:
- 100% Brazilian data (CPF válido, banks, PIX, addresses)
- Behavioral profiles for realistic patterns
- Multiple export formats (JSON, CSV, Parquet)
- Memory-efficient streaming for large datasets
- Configurable fraud patterns
- Parallel generation for high throughput
"""

__version__ = "3.0.0"
__author__ = "Abner Fonseca"

from .generators.customer import CustomerGenerator
from .generators.device import DeviceGenerator
from .generators.transaction import TransactionGenerator
from .exporters import get_exporter
from .validators.cpf import generate_valid_cpf, validate_cpf

__all__ = [
    'CustomerGenerator',
    'DeviceGenerator', 
    'TransactionGenerator',
    'get_exporter',
    'generate_valid_cpf',
    'validate_cpf',
]
