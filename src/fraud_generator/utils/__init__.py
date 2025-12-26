"""
Utilities package for Brazilian Fraud Data Generator.
"""

from .streaming import (
    CustomerIndex,
    DeviceIndex,
    DriverIndex,
    RideIndex,
    create_customer_index,
    create_device_index,
    create_driver_index,
    create_ride_index,
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
    # Streaming - Customer/Device
    'CustomerIndex',
    'DeviceIndex',
    'create_customer_index',
    'create_device_index',
    # Streaming - Driver/Ride
    'DriverIndex',
    'RideIndex',
    'create_driver_index',
    'create_ride_index',
    # Streaming - Utils
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
