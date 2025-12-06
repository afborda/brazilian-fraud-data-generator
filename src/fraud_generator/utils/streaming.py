"""
Streaming utilities for memory-efficient data generation.
"""

from typing import NamedTuple, List, Iterator, Optional, Dict, Any, Callable
from collections import namedtuple
import random


class CustomerIndex(NamedTuple):
    """
    Lightweight customer reference for memory-efficient processing.
    
    Memory usage: ~50-80 bytes vs ~800+ bytes for full Customer object.
    """
    customer_id: str
    state: str
    profile: Optional[str]
    bank_code: Optional[str] = None
    risk_level: Optional[str] = None


class DeviceIndex(NamedTuple):
    """Lightweight device reference."""
    device_id: str
    customer_id: str


class DriverIndex(NamedTuple):
    """
    Lightweight driver reference for memory-efficient processing.
    
    Memory usage: ~60-90 bytes vs ~500+ bytes for full Driver object.
    """
    driver_id: str
    operating_state: str
    operating_city: str
    active_apps: tuple  # Tuple of app names


class RideIndex(NamedTuple):
    """Lightweight ride reference."""
    ride_id: str
    driver_id: str
    passenger_id: str
    app: str
    city: str


def create_customer_index(customer_dict: Dict[str, Any]) -> CustomerIndex:
    """Create a CustomerIndex from a customer dictionary."""
    return CustomerIndex(
        customer_id=customer_dict['customer_id'],
        state=customer_dict.get('address', {}).get('state', 'SP'),
        profile=customer_dict.get('behavioral_profile'),
        bank_code=customer_dict.get('bank_code'),
        risk_level=customer_dict.get('risk_level'),
    )


def create_device_index(device_dict: Dict[str, Any]) -> DeviceIndex:
    """Create a DeviceIndex from a device dictionary."""
    return DeviceIndex(
        device_id=device_dict['device_id'],
        customer_id=device_dict['customer_id'],
    )


def create_driver_index(driver_dict: Dict[str, Any]) -> DriverIndex:
    """Create a DriverIndex from a driver dictionary."""
    active_apps = driver_dict.get('active_apps', [])
    if isinstance(active_apps, list):
        active_apps = tuple(active_apps)
    
    return DriverIndex(
        driver_id=driver_dict['driver_id'],
        operating_state=driver_dict.get('operating_state', 'SP'),
        operating_city=driver_dict.get('operating_city', 'São Paulo'),
        active_apps=active_apps,
    )


def create_ride_index(ride_dict: Dict[str, Any]) -> RideIndex:
    """Create a RideIndex from a ride dictionary."""
    # Handle nested pickup_location
    pickup_location = ride_dict.get('pickup_location', {})
    city = pickup_location.get('city', '') if isinstance(pickup_location, dict) else ''
    
    return RideIndex(
        ride_id=ride_dict['ride_id'],
        driver_id=ride_dict.get('driver_id', ''),
        passenger_id=ride_dict.get('passenger_id', ''),
        app=ride_dict.get('app', ''),
        city=city,
    )


class BatchGenerator:
    """
    Memory-efficient batch generator for large datasets.
    
    Generates data in batches, keeping only lightweight indexes
    in memory for customer/device/driver references.
    """
    
    def __init__(
        self,
        batch_size: int = 10000,
        max_memory_items: int = 1000000
    ):
        """
        Initialize batch generator.
        
        Args:
            batch_size: Number of records per batch
            max_memory_items: Maximum items to keep in memory
        """
        self.batch_size = batch_size
        self.max_memory_items = max_memory_items
        self.customer_index: List[CustomerIndex] = []
        self.device_index: List[DeviceIndex] = []
        self.driver_index: List[DriverIndex] = []
    
    def add_customer_index(self, index: CustomerIndex) -> None:
        """Add a customer index to the reference list."""
        self.customer_index.append(index)
        
        # Memory management: if too many, sample down
        if len(self.customer_index) > self.max_memory_items:
            self.customer_index = random.sample(
                self.customer_index,
                self.max_memory_items // 2
            )
    
    def add_device_index(self, index: DeviceIndex) -> None:
        """Add a device index to the reference list."""
        self.device_index.append(index)
        
        if len(self.device_index) > self.max_memory_items:
            self.device_index = random.sample(
                self.device_index,
                self.max_memory_items // 2
            )
    
    def add_driver_index(self, index: DriverIndex) -> None:
        """Add a driver index to the reference list."""
        self.driver_index.append(index)
        
        if len(self.driver_index) > self.max_memory_items:
            self.driver_index = random.sample(
                self.driver_index,
                self.max_memory_items // 2
            )
    
    def get_random_customer(self) -> Optional[CustomerIndex]:
        """Get a random customer from the index."""
        if not self.customer_index:
            return None
        return random.choice(self.customer_index)
    
    def get_random_device(self, customer_id: Optional[str] = None) -> Optional[DeviceIndex]:
        """Get a random device, optionally for a specific customer."""
        if not self.device_index:
            return None
        
        if customer_id:
            customer_devices = [d for d in self.device_index if d.customer_id == customer_id]
            if customer_devices:
                return random.choice(customer_devices)
        
        return random.choice(self.device_index)
    
    def get_random_driver(
        self,
        state: Optional[str] = None,
        city: Optional[str] = None
    ) -> Optional[DriverIndex]:
        """
        Get a random driver, optionally filtered by state and/or city.
        
        Args:
            state: Filter by operating state
            city: Filter by operating city
        
        Returns:
            DriverIndex or None if no drivers match
        """
        if not self.driver_index:
            return None
        
        candidates = self.driver_index
        
        if state:
            candidates = [d for d in candidates if d.operating_state == state]
        
        if city and candidates:
            city_candidates = [d for d in candidates if d.operating_city == city]
            if city_candidates:
                candidates = city_candidates
        
        if not candidates:
            # Fallback to any driver
            return random.choice(self.driver_index)
        
        return random.choice(candidates)
    
    def get_drivers_by_state(self, state: str) -> List[DriverIndex]:
        """Get drivers from a specific state."""
        return [d for d in self.driver_index if d.operating_state == state]
    
    def get_drivers_by_app(self, app: str) -> List[DriverIndex]:
        """Get drivers who use a specific app."""
        return [d for d in self.driver_index if app in d.active_apps]
    
    def get_customers_by_state(self, state: str) -> List[CustomerIndex]:
        """Get customers from a specific state."""
        return [c for c in self.customer_index if c.state == state]
    
    def get_customers_by_profile(self, profile: str) -> List[CustomerIndex]:
        """Get customers with a specific profile."""
        return [c for c in self.customer_index if c.profile == profile]
    
    def clear(self) -> None:
        """Clear all indexes to free memory."""
        self.customer_index.clear()
        self.device_index.clear()
        self.driver_index.clear()


def batch_iterator(
    items: List[Any],
    batch_size: int
) -> Iterator[List[Any]]:
    """
    Iterate over items in batches.
    
    Args:
        items: List of items
        batch_size: Size of each batch
    
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def chunked_range(
    total: int,
    chunk_size: int
) -> Iterator[range]:
    """
    Generate range chunks.
    
    Args:
        total: Total number of items
        chunk_size: Size of each chunk
    
    Yields:
        Range objects for each chunk
    """
    for start in range(0, total, chunk_size):
        end = min(start + chunk_size, total)
        yield range(start, end)


def estimate_memory_usage(num_customers: int, num_devices_per_customer: float = 1.5) -> dict:
    """
    Estimate memory usage for different approaches.
    
    Args:
        num_customers: Number of customers
        num_devices_per_customer: Average devices per customer
    
    Returns:
        Dictionary with memory estimates in bytes and MB
    """
    # Full object sizes (approximate)
    FULL_CUSTOMER_SIZE = 800  # bytes
    FULL_DEVICE_SIZE = 300  # bytes
    
    # Index sizes
    INDEX_CUSTOMER_SIZE = 80  # bytes
    INDEX_DEVICE_SIZE = 50  # bytes
    
    num_devices = int(num_customers * num_devices_per_customer)
    
    full_memory = (
        num_customers * FULL_CUSTOMER_SIZE +
        num_devices * FULL_DEVICE_SIZE
    )
    
    index_memory = (
        num_customers * INDEX_CUSTOMER_SIZE +
        num_devices * INDEX_DEVICE_SIZE
    )
    
    return {
        'full_approach': {
            'bytes': full_memory,
            'mb': full_memory / (1024 * 1024),
        },
        'index_approach': {
            'bytes': index_memory,
            'mb': index_memory / (1024 * 1024),
        },
        'savings_percent': round((1 - index_memory / full_memory) * 100, 1),
    }


class ProgressTracker:
    """Track progress for long-running operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, n: int = 1) -> None:
        """Update progress by n items."""
        self.current += n
    
    @property
    def progress(self) -> float:
        """Get progress as percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100
    
    def __str__(self) -> str:
        return f"{self.description}: {self.current:,}/{self.total:,} ({self.progress:.1f}%)"
