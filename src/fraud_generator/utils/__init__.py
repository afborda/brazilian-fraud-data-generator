"""
Utilities package for Brazilian Fraud Data Generator.
"""

from .streaming import (
    CustomerIndex,
    DeviceIndex,
    DriverIndex,
    RideIndex,
    CustomerSessionState,
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

from .redis_cache import (
    is_redis_available,
    get_redis_client,
    load_cached_indexes,
    save_cached_indexes,
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
    'CustomerSessionState',
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
    # Redis cache
    'is_redis_available',
    'get_redis_client',
    'load_cached_indexes',
    'save_cached_indexes',
]
