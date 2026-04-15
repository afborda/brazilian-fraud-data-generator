---
description: "Use when editing benchmark scripts, profiling code, or optimizing performance: WeightCache, streaming IO, batch chunking, memory management."
applyTo: "benchmarks/**"
---

# Performance Rules

## Benchmarking
- ALWAYS measure BEFORE and AFTER any optimization
- Use existing benchmarks: `benchmarks/comprehensive_benchmark.py`, `data_quality_benchmark.py`
- Report: records/sec, memory (RSS), AUC-ROC stability
- Minimum dataset: 10MB for profiling, 100MB for benchmarking

## Profiling Tools
- CPU: `python -m cProfile -s cumulative {script}`
- Memory: `python -m memory_profiler {script}` (requires `pip install memory_profiler`)
- RSS tracking: `/usr/bin/time -v python {script}`

## WeightCache Pattern
- Use `WeightCache` from `utils/weight_cache.py` for per-record weighted selections
- Initialize in `__init__`, NOT in generation loops
- Prefer `choose_batch(n)` over N single `choose()` calls
- Pre-caching requires weights sum = 1.0

## Streaming IO (P3 mitigation)
- Export in chunks via `export_batch()`, never accumulate full dataset in list
- CSV: write header once, append rows in chunks
- Parquet: use `ParquetWriter` with row groups
- Target: RSS < 500MB for 1GB datasets

## Known Performance Issues
| Issue | Priority | Mitigation |
|-------|----------|-----------|
| `random.choices()` per-record | P2 | WeightCache + binary search |
| CSV/Parquet OOM >1GB | P3 | Streaming `export_batch()` chunks |
| Customer/Device index growth | Low | LRU eviction or streaming index |

## Quality Guard
- NEVER sacrifice data quality for speed
- AUC-ROC must remain at 0.9991 after optimization
- Run `pytest tests/ -v` after every change
- Run `python benchmarks/data_quality_benchmark.py` to verify quality score
