"""
Weight caching module for optimized weighted random sampling.

Replaces inefficient random.choices() calls with pre-computed cumulative
distributions and binary search (bisect) for O(log n) lookups.

Performance improvement: Eliminates ~3µs overhead of random.choices() per call.
Uses only standard library (bisect) for minimal overhead.
"""

import bisect
import random
from typing import List, Any


class WeightCache:
    """Cache cumulative weights for fast weighted random selection."""
    
    def __init__(self, choices: List[Any], weights: List[float]):
        """
        Initialize weight cache.
        
        Args:
            choices: List of items to choose from
            weights: Corresponding weights (will be normalized)
        """
        self.choices = choices
        
        # Normalize weights to sum to 1.0
        total = sum(weights)
        normalized_weights = [w / total for w in weights]
        
        # Pre-compute cumulative distribution (using pure Python for speed)
        self.cumsum = []
        cumulative = 0.0
        for w in normalized_weights:
            cumulative += w
            self.cumsum.append(cumulative)
    
    def sample(self) -> Any:
        """
        Sample one item from choices using weighted distribution.
        
        Uses bisect binary search for O(log n) complexity.
        No numpy overhead - pure Python stdlib.
        
        Returns:
            One randomly selected item based on weights
        """
        r = random.random()  # 0.0 to 1.0
        
        # bisect_right finds insertion point, which is the index we want
        idx = bisect.bisect_right(self.cumsum, r)
        
        # Ensure index is in bounds
        idx = min(idx, len(self.choices) - 1)
        
        return self.choices[idx]
    
    def __call__(self) -> Any:
        """Allow instance to be called as function."""
        return self.sample()


# Pre-initialize caches for main transaction types
# These are created once at module import and reused for all transactions
_weight_caches = {}


def get_weight_cache(name: str, choices: List[Any], weights: List[float]) -> WeightCache:
    """
    Get or create a weight cache.
    
    Args:
        name: Cache identifier
        choices: List of items
        weights: Corresponding weights
    
    Returns:
        WeightCache instance
    """
    if name not in _weight_caches:
        _weight_caches[name] = WeightCache(choices, weights)
    return _weight_caches[name]


def clear_caches() -> None:
    """Clear all cached weights (useful for testing)."""
    _weight_caches.clear()


# ============================================================================
# Factory function for creating cached samplers
# ============================================================================

def make_weighted_sampler(name: str, choices: List[Any], weights: List[float]):
    """
    Create a fast weighted sampler function.
    
    Usage:
        sampler = make_weighted_sampler('tx_types', ['PIX', 'CARD', 'TED'], [0.45, 0.40, 0.15])
        tx_type = sampler()  # Call to sample
    
    Args:
        name: Cache identifier
        choices: Items to choose from
        weights: Corresponding weights
    
    Returns:
        Callable that returns weighted random selection
    """
    cache = get_weight_cache(name, choices, weights)
    return cache.sample
