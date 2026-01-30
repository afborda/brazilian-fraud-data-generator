# Phase 2 Optimization Roadmap

## Overview

Phase 1 delivered **7 optimizations** with cumulative gains of **+18.9% speed and -85.4% storage**.

Phase 2 focuses on **advanced performance improvements** targeting:
- Generation bottlenecks (Cython, Numba)
- Compression performance (native libraries)
- True parallelism (ProcessPoolExecutor)
- Storage formats (Arrow IPC, columnar)

---

## High-Priority Optimizations

### 2.1 Native Compression Libraries

**Expected Gain:** +15-25% compression speed  
**Effort:** Medium (3-5 days)  
**Dependencies:** zstandard-jni, snappy-c bindings

**Implementation Plan:**
```python
# Instead of pure Python gzip (22.9k rec/sec with gzip)
# Use zstandard C library (30-35k rec/sec)
import zstandard as zstd

# For JSONL gzip, use python-snappy (faster)
import snappy
```

**Benchmarking Strategy:**
- Compare zstd vs gzip vs brotli vs snappy
- Measure compression ratio AND speed
- Test with various compression levels
- Profile memory overhead

**Status:** Not started

---

### 2.2 Cython JIT for Transaction Generation

**Expected Gain:** +10-20% generation speed  
**Effort:** High (7-10 days)  
**Complexity:** Rewrite critical generation loops

**Candidates for JIT:**
1. `TransactionGenerator.generate()` - Main loop (60% of time)
2. Weighted random selection - O(log n) with WeightCache
3. Distance calculations (Haversine for rides)

**Implementation Plan:**
```cython
# fraud_generator/generators/transaction_cython.pyx
cdef class TransactionGeneratorCython:
    cdef object customer_index
    cdef object device_index
    cdef object tx_weights_cache
    
    def generate(self, ...):
        # C-level operations for hot loops
        # Avoid Python overhead
```

**Benchmarking Strategy:**
- Profile with cProfile before/after
- Measure per-operation time
- Test with various transaction counts
- Compare pure Python vs Cython + Python hybrid

**Status:** Not started

---

### 2.3 ProcessPoolExecutor True Parallelism

**Expected Gain:** +30-40% with 16 workers  
**Effort:** High (5-7 days)  
**Challenge:** Seed determinism, memory management

**Current Limitation:** ThreadPoolExecutor bound by GIL

**Implementation Plan:**
```python
# Replace ThreadPoolExecutor with ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor

# Challenges:
# 1. Each worker needs independent random seed
# 2. Shared indexes must be serialized (pickle overhead)
# 3. Memory scaling: 16 workers × 1GB cache = 16GB

# Solution:
# - Use mp.Manager() for shared state
# - Per-worker seed = base_seed + worker_id * 12345
# - Limit workers to CPU count / 2 (balanced I/O)
```

**Benchmarking Strategy:**
- Test with 1, 4, 8, 16 workers
- Measure speedup curve (should be linear until memory bound)
- Compare pickle overhead vs performance gain
- Profile memory scaling

**Status:** Not started

---

## Medium-Priority Optimizations

### 2.4 Numba JIT for Distance Calculations

**Expected Gain:** +5-10% for rides  
**Effort:** Low (2-3 days)  
**Focus:** Haversine distance calculation

**Implementation:**
```python
from numba import jit

@jit(nopython=True)
def haversine_distance_numba(lat1, lon1, lat2, lon2):
    # Pure math operations, no Python overhead
    # Expected: 10x+ faster than pure Python
```

**Test Cases:**
- 1M distance calculations
- Compare vs current implementation
- Verify accuracy to 6 decimals

**Status:** Not started

---

### 2.5 Batch CSV Writes

**Expected Gain:** +3-5% for CSV  
**Effort:** Low (1-2 days)  
**Current:** 65KB buffer per write

**Optimization:**
```python
# Increase buffer size or write frequency
# Current: 65KB chunks
# Target: 256KB or 512KB chunks

# Trade-off: Memory vs syscall reduction
# Measure: time per write vs peak memory
```

**Status:** Not started

---

### 2.6 Arrow IPC Format (Streaming)

**Expected Gain:** +20-30% for columnar workloads  
**Effort:** Medium (3-5 days)  
**Focus:** Zero-copy streaming to S3

**Implementation:**
```python
# Alternative to JSONL for downstream processing
import pyarrow as pa

# Columnar format advantages:
# - Better compression (30-50%)
# - Faster aggregation queries
# - Native Spark/Pandas support
```

**Status:** Not started

---

## Low-Priority Optimizations

### 2.7 Async Kafka/Webhook Streaming

**Expected Gain:** +10-20% for network I/O  
**Effort:** High (5-7 days)  
**Focus:** Non-blocking I/O for streaming mode

**Current:** Synchronous socket operations

**Implementation:**
```python
import asyncio
from aiokafka import AIOKafkaProducer

async def async_stream():
    # Non-blocking produce to Kafka
    # Batch multiple records before send
```

**Status:** Not started

---

### 2.8 Redis Caching for Generator State

**Expected Gain:** +5-10% for distributed generation  
**Effort:** High (5-7 days)  
**Use Case:** Multiple workers sharing customer/device cache

**Status:** Not started

---

### 2.9 Database Export Targets

**Expected Gain:** Direct database ingest  
**Effort:** High (10+ days)  
**Targets:** PostgreSQL, MongoDB, DuckDB

**Status:** Not started

---

## Recommended Execution Order

```
Phase 2 Timeline (12-16 weeks):

Month 1:
├─ Week 1-2: 2.1 Native Compression (zstd/snappy)
└─ Week 3-4: 2.5 Batch CSV Writes (quick win)

Month 2:
├─ Week 5-6: 2.2 Cython JIT Compilation
└─ Week 7-8: 2.4 Numba Distance Calculations

Month 3:
├─ Week 9-10: 2.3 ProcessPoolExecutor True Parallelism
└─ Week 11-12: 2.6 Arrow IPC Format

Month 4 (if time permits):
├─ Week 13: 2.7 Async Streaming
└─ Week 14-16: Documentation & Testing
```

---

## Performance Projection

If all Phase 2 optimizations are completed:

```
Current (Phase 1):
- Speed: 28,039 records/sec
- Storage (gzip): 30MB for 100MB dataset

Phase 2 Projection:
- Native Compression: 28,039 × 1.20 = 33,647 rec/sec (zstd faster than gzip)
- Cython JIT: 33,647 × 1.15 = 38,694 rec/sec
- ProcessPool (8x): 38,694 × 2.0 = 77,388 rec/sec
- Numba (rides): 77,388 × 1.05 = 81,257 rec/sec (rides only)

Estimated Phase 2 Gain: +180% overall
```

---

## Testing Strategy

### Benchmark Suite

```python
# benchmarks/phase_2_suite.py
class Phase2Benchmarks:
    def test_compression_speed(self):
        # Measure compression throughput
        # Compare: gzip vs zstd vs snappy vs brotli
        
    def test_cython_overhead(self):
        # Measure Cython import + compilation time
        # Compare pure Python vs Cython
        
    def test_parallelism_scaling(self):
        # Measure speedup with 1, 4, 8, 16 workers
        # Check memory scaling
        
    def test_distance_calculations(self):
        # Measure Numba vs pure Python
        # Verify accuracy
```

---

## Risk Assessment

| Optimization | Risk | Mitigation |
|--------------|------|-----------|
| 2.1 Compression | Library compatibility | Add feature flags, fallback |
| 2.2 Cython | Maintenance burden | Document, add type hints |
| 2.3 ProcessPool | Memory scaling | Limit workers, monitor heap |
| 2.4 Numba | Numerical accuracy | Verify vs baseline |

---

## Success Criteria

✅ **Phase 2 Complete When:**
- All benchmarks documented with seed=42
- Backward compatibility maintained
- Memory overhead < 10%
- No breaking API changes
- Documentation updated
- Tests passing

---

## Notes

- Start with **2.1 (compression)** - highest ROI, lowest risk
- **2.2 (Cython)** is high-impact but high-effort
- **2.3 (ProcessPool)** requires careful seed management
- **2.6 (Arrow)** opens new use cases but niche benefit
- **2.7-2.9** can be parallelized if additional team members available

---

*Generated: 2025-01-30*
*Based on Phase 1 completion (7 optimizations, +18.9% speed)*
