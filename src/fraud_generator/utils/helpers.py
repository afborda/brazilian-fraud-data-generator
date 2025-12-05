"""
Utility functions for Brazilian Fraud Data Generator.
"""

import random
import hashlib
from typing import List


def generate_ip_brazil() -> str:
    """Generate a Brazilian IP address from common ISP ranges."""
    prefixes = [
        '177.', '187.', '189.', '191.', '200.', '201.',
        '179.', '186.', '188.', '190.', '170.',
        '138.', '143.', '152.', '168.',
    ]
    prefix = random.choice(prefixes)
    return prefix + '.'.join(str(random.randint(0, 255)) for _ in range(3))


def generate_hash(value: str, length: int = 32) -> str:
    """Generate a SHA256 hash of a value, truncated to length."""
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def generate_random_hash(length: int = 32) -> str:
    """Generate a random hash."""
    return hashlib.sha256(str(random.random()).encode()).hexdigest()[:length]


def weighted_choice(options: dict) -> str:
    """
    Select from options with weights.
    
    Args:
        options: Dictionary of {option: weight}
    
    Returns:
        Selected option
    """
    keys = list(options.keys())
    weights = list(options.values())
    return random.choices(keys, weights=weights)[0]


def parse_size(size_str: str) -> int:
    """
    Parse a size string to bytes.
    
    Args:
        size_str: Size string (e.g., '1GB', '500MB', '1TB')
    
    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }
    
    for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(unit):
            value = float(size_str[:-len(unit)])
            return int(value * multiplier)
    
    # Assume bytes if no unit
    return int(size_str)


def format_size(bytes_size: int) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
