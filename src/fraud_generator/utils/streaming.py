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
    estado: str
    perfil: Optional[str]
    banco_codigo: Optional[str] = None
    nivel_risco: Optional[str] = None


class DeviceIndex(NamedTuple):
    """Lightweight device reference."""
    device_id: str
    customer_id: str


def create_customer_index(customer_dict: Dict[str, Any]) -> CustomerIndex:
    """Create a CustomerIndex from a customer dictionary."""
    return CustomerIndex(
        customer_id=customer_dict['customer_id'],
        estado=customer_dict.get('endereco', {}).get('estado', 'SP'),
        perfil=customer_dict.get('perfil_comportamental'),
        banco_codigo=customer_dict.get('banco_codigo'),
        nivel_risco=customer_dict.get('nivel_risco'),
    )


def create_device_index(device_dict: Dict[str, Any]) -> DeviceIndex:
    """Create a DeviceIndex from a device dictionary."""
    return DeviceIndex(
        device_id=device_dict['device_id'],
        customer_id=device_dict['customer_id'],
    )


class BatchGenerator:
    """
    Memory-efficient batch generator for large datasets.
    
    Generates data in batches, keeping only lightweight indexes
    in memory for customer/device references.
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
    
    def get_customers_by_state(self, estado: str) -> List[CustomerIndex]:
        """Get customers from a specific state."""
        return [c for c in self.customer_index if c.estado == estado]
    
    def get_customers_by_profile(self, profile: str) -> List[CustomerIndex]:
        """Get customers with a specific profile."""
        return [c for c in self.customer_index if c.perfil == profile]
    
    def clear(self) -> None:
        """Clear all indexes to free memory."""
        self.customer_index.clear()
        self.device_index.clear()


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
