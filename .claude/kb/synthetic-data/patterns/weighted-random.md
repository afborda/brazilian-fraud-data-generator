# Weighted Random Selection

> Performance-critical pattern for probabilistic field generation.

## The Problem (P2)

`random.choices(population, weights)` is called per-record for many fields:
- Transaction type, channel, MCC, bank, state, hour, card brand, etc.
- At ~25% overhead on large datasets, this is a significant bottleneck

## Solution: WeightCache

```python
# src/fraud_generator/utils/weight_cache.py

class WeightCache:
    """Pre-computes cumulative weights for O(log n) selection."""
    
    def __init__(self, population, weights):
        # Normalize weights, build cumulative distribution
        self._cumulative = ...
        self._population = population
    
    def choose(self) -> Any:
        # Binary search on cumulative distribution
        # ~3x faster than random.choices() for repeated calls
        return self._population[bisect(self._cumulative, random.random())]
    
    def choose_batch(self, n: int) -> List[Any]:
        # Vectorized batch selection
        # ~10x faster than n × random.choices()
        return [self._population[bisect(self._cumulative, r)] 
                for r in [random.random() for _ in range(n)]]
```

## Usage Pattern

```python
# In generator __init__ (ONE TIME)
self._tx_type_cache = WeightCache(TX_TYPES_LIST, TX_TYPE_WEIGHTS)
self._bank_cache = WeightCache(BANK_CODES, BANK_WEIGHTS)

# In generator loop (PER RECORD — fast)
tx_type = self._tx_type_cache.choose()
bank = self._bank_cache.choose()
```

## PrecomputeBuffers

For even higher performance (`src/fraud_generator/utils/precompute.py`):

```python
class PrecomputeBuffers:
    """Pre-generates N values at once, serves from buffer."""
    
    def __init__(self, cache: WeightCache, buffer_size: int = 10000):
        self._buffer = cache.choose_batch(buffer_size)
        self._index = 0
    
    def next(self) -> Any:
        if self._index >= len(self._buffer):
            self._refill()
        value = self._buffer[self._index]
        self._index += 1
        return value
```

## Rules

1. **Always cache**: If a `random.choices()` call happens per-record, wrap in WeightCache
2. **Init once**: Build caches in `__init__`, not in the generate loop
3. **Weights normalization**: WeightCache normalizes internally — raw weights OK
4. **Seed compatibility**: WeightCache uses `random.random()` — respects `random.seed()`
5. **Profile-specific**: Create separate caches per profile if weights differ by profile

## Anti-Patterns

- **Per-record random.choices()**: Direct stdlib call in hot loop — use WeightCache
- **Numpy in hot path**: numpy has import/setup overhead; WeightCache is faster for single picks
- **Global caches**: Cache should be per-generator-instance for thread safety
