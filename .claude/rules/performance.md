---
description: Benchmarking, profiling, WeightCache, streaming IO, memory management
paths:
  - "benchmarks/**"
  - "src/fraud_generator/utils/weight_cache.py"
  - "src/fraud_generator/utils/streaming.py"
---

# Performance Rules

## Benchmarking
- ALWAYS measure BEFORE and AFTER changes
- Use: `benchmarks/comprehensive_benchmark.py`, `data_quality_benchmark.py`
- Minimum: 10MB for profiling, 100MB for benchmarks

## WeightCache
- Use `WeightCache` for per-record weighted selections
- Initialize in `__init__`, NOT in loops
- Prefer `choose_batch(n)` over N `choose()` calls
- Pre-caching requires weights sum = 1.0

## Streaming IO (P3)
- Export in chunks via `export_batch()`, never accumulate full list
- Target: RSS < 500MB for 1GB datasets

## Quality Guard
- AUC-ROC must remain 0.9991 after optimization
- Run `pytest tests/ -v` after every performance change
