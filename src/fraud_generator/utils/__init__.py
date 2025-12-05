"""
Utilities package for Brazilian Fraud Data Generator.
"""

from .streaming import (
    CustomerIndex,
    DeviceIndex,
    create_customer_index,
    create_device_index,
    BatchGenerator,
    batch_iterator,
    chunked_range,
    estimate_memory_usage,
    ProgressTracker,
)

from .helpers import (
    generate_ip_brazil,
    generate_hash,
    generate_random_hash,
    weighted_choice,
    parse_size,
    format_size,
    format_duration,
)

__all__ = [
    # Streaming
    'CustomerIndex',
    'DeviceIndex',
    'create_customer_index',
    'create_device_index',
    'BatchGenerator',
    'batch_iterator',
    'chunked_range',
    'estimate_memory_usage',
    'ProgressTracker',
    # Helpers
    'generate_ip_brazil',
    'generate_hash',
    'generate_random_hash',
    'weighted_choice',
    'parse_size',
    'format_size',
    'format_duration',
]
