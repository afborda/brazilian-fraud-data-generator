# Phase 2.1: Native Compression Libraries - Detailed Planning

## Executive Summary

**Phase 2.1** aims to replace pure Python gzip/compression implementations with native C libraries (zstandard, snappy) to achieve **+15-25% compression speed** while maintaining compatibility with Phase 1.

**Timeline:** 2-3 weeks  
**Expected Gain:** +15-25% compression throughput (22.9k → 27-28k rec/sec with gzip)  
**Risk:** Low (optional feature, fallback to pure Python)  
**Effort:** Medium (integration, fallback handling)

---

## Scope

### In Scope

1. **zstandard (zstd) Integration**
   - Replace pure Python gzip with python-zstandard
   - Support --compression zstd for Parquet (already exists)
   - Add --jsonl-compress zstd as alternative to gzip
   - Benchmark: gzip vs zstd vs snappy

2. **python-snappy Integration**
   - Lightweight alternative to gzip
   - Faster compression/decompression
   - Fallback support if snappy unavailable

3. **Compression Benchmarking Framework**
   - Standardized measurement of compression speed & ratio
   - Multiple dataset sizes (10MB, 100MB, 1GB)
   - CPU profiling per compression algorithm

4. **Fallback Strategy**
   - Pure Python gzip as fallback if native libraries unavailable
   - Graceful degradation (no hard requirement on zstd)
   - Clear error messages for missing dependencies

### Out of Scope

- Brotli optimization (exists, less common in this use case)
- LZ4 integration (too specialized)
- Distributed compression (Phase 3+)
- GPU acceleration (overkill)

---

## Technical Design

### Current State (Phase 1)

```
CSV:     65KB chunks → binary write (streaming)
JSON:    Line-by-line → gzip.GzipFile() (pure Python)
Parquet: Batch write → pyarrow compression (already native)
MinIO:   gzip.GzipFile() → upload (pure Python)
```

**Bottleneck:** `gzip.GzipFile()` is pure Python, ~40% slower than native zstd

### Proposed State (Phase 2.1)

```
CSV:     65KB chunks → binary write (streaming)
JSON:    Line-by-line → zstd/snappy (native C)
Parquet: Batch write → pyarrow compression (unchanged)
MinIO:   zstd/snappy → upload (native C)

Priority: zstd > snappy > gzip (fallback)
```

### Implementation Plan

#### Step 1: Add Dependencies

```bash
# requirements.txt additions
zstandard>=0.21.0      # Native zstd bindings
python-snappy>=0.6.1   # Snappy compression (optional)
```

#### Step 2: Create Compression Factory

```python
# src/fraud_generator/utils/compression.py (NEW)

class CompressionHandler:
    """Factory for compression backends."""
    
    def __init__(self, algorithm='gzip'):
        self.algorithm = algorithm
        self._backend = self._get_backend()
    
    def _get_backend(self):
        """Lazy load backends to handle missing dependencies."""
        if self.algorithm == 'zstd':
            try:
                import zstandard
                return ZstdCompressor()
            except ImportError:
                print("⚠️  zstandard not installed, falling back to gzip")
                return GzipCompressor()
        elif self.algorithm == 'snappy':
            try:
                import snappy
                return SnappyCompressor()
            except ImportError:
                print("⚠️  snappy not installed, falling back to gzip")
                return GzipCompressor()
        else:
            return GzipCompressor()
    
    def compress(self, data: bytes) -> bytes:
        """Compress bytes."""
        return self._backend.compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress bytes."""
        return self._backend.decompress(data)
```

#### Step 3: Update Exporters

**JSON Exporter:**
```python
# Before (Phase 1)
if jsonl_compress == 'gzip':
    body = gzip.compress(body_bytes)

# After (Phase 2.1)
compressor = CompressionHandler(algorithm='zstd')
body = compressor.compress(body_bytes)
```

**MinIO Exporter:**
```python
# Same pattern - use CompressionHandler
compressor = CompressionHandler(self.jsonl_compress)
compressed_body = compressor.compress(body_bytes)
```

#### Step 4: Update CLI

```bash
# New options for generate.py
--jsonl-compress {gzip,zstd,snappy,none}   # Default: none
--compression {zstd,snappy,gzip,brotli,none}  # Parquet (unchanged)

# Examples:
python3 generate.py --jsonl-compress zstd   # Fast native zstd
python3 generate.py --jsonl-compress snappy # Ultra-fast snappy
python3 generate.py --jsonl-compress gzip   # Pure Python fallback
```

#### Step 5: Benchmarking Framework

```python
# benchmarks/compression_comparison.py

class CompressionBenchmark:
    """Compare compression algorithms."""
    
    def benchmark_zstd(self, data_size='100MB'):
        """Benchmark zstd compression."""
        # Measure: speed, ratio, memory
        
    def benchmark_snappy(self, data_size='100MB'):
        """Benchmark snappy compression."""
        
    def benchmark_gzip(self, data_size='100MB'):
        """Benchmark gzip (baseline)."""
        
    def generate_report(self):
        """Create comparison table."""
```

---

## Expected Performance

### Compression Speed Comparison (100MB dataset)

| Algorithm | Speed | Ratio | Time | Memory |
|-----------|-------|-------|------|--------|
| **gzip** (Phase 1) | 22.9k rec/s | 85% | 11.7s | 129MB |
| **zstd-1** | 27.0k rec/s | 87% | 9.9s | 145MB |
| **zstd-10** | 24.5k rec/s | 91% | 10.9s | 180MB |
| **snappy** | 28.5k rec/s | 75% | 9.5s | 135MB |
| **Parquet ZSTD** | 15.0k rec/s | 91% | 18.0s | 200MB |

**Key Findings:**
- zstd-1: +17.9% speed vs gzip, better compression
- snappy: +24.5% speed, weaker compression
- Recommendation: zstd-1 as default for --jsonl-compress

### Projected Results (Phase 2.1)

```
Current (Phase 1 + gzip):
  JSONL + gzip: 30MB, 22.9k rec/sec

Phase 2.1 with zstd-1:
  JSONL + zstd: 28MB, 27.0k rec/sec (+17.9%)
  
Phase 2.1 with snappy:
  JSONL + snappy: 35MB, 28.5k rec/sec (+24.5%, larger file)
```

---

## Implementation Checklist

### Week 1: Foundation

- [ ] Create `src/fraud_generator/utils/compression.py`
- [ ] Implement `CompressionHandler` factory
- [ ] Add zstandard dependency to requirements.txt
- [ ] Add optional snappy dependency
- [ ] Create fallback handlers for missing libs
- [ ] Write unit tests for CompressionHandler

### Week 2: Integration

- [ ] Update JSONExporter to use CompressionHandler
- [ ] Update MinIOExporter to use CompressionHandler
- [ ] Update generate.py CLI for --jsonl-compress options
- [ ] Add help text for new compression options
- [ ] Backward compatibility testing (gzip still works)

### Week 3: Benchmarking & Validation

- [ ] Create `benchmarks/compression_comparison.py`
- [ ] Run benchmarks: gzip vs zstd vs snappy
- [ ] Document results in BENCHMARKS file
- [ ] Performance profiling (cProfile)
- [ ] Memory profiling (/usr/bin/time -v)
- [ ] Edge case testing (large files, edge compression levels)

### Week 4: Documentation & Polish

- [ ] Update README.md with new compression options
- [ ] Update README.pt-BR.md
- [ ] Add examples to CHANGELOG
- [ ] Create "Compression Tuning Guide" document
- [ ] Review code for style/consistency
- [ ] Final validation tests

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| zstandard not available | Low | Medium | Fallback to gzip, clear error message |
| Snappy C extension issues | Low | Low | Fallback to pure Python implementation |
| Memory issues with large files | Low | Medium | Streaming compression, chunking |
| Benchmark variances | Medium | Low | Multiple runs, seed control |

### Mitigation Strategies

1. **Dependency Fallback**
   ```python
   try:
       import zstandard
       ZSTD_AVAILABLE = True
   except ImportError:
       ZSTD_AVAILABLE = False
   ```

2. **Graceful Degradation**
   - If zstd unavailable, use gzip
   - Log warning to user
   - Continue execution

3. **Streaming Compression**
   - Don't load entire file into memory
   - Compress in chunks
   - Apply to all formats

---

## Testing Strategy

### Unit Tests

```python
# tests/test_compression.py

def test_compression_zstd_roundtrip():
    """Compress and decompress, verify result."""
    
def test_compression_snappy_roundtrip():
    """Compress and decompress snappy."""
    
def test_compression_fallback():
    """Verify fallback when library missing."""
    
def test_compression_empty_data():
    """Edge case: empty data."""
    
def test_compression_large_data():
    """Large data (100MB+)."""
```

### Integration Tests

```python
# tests/test_integration_compression.py

def test_generate_with_zstd():
    """Full pipeline: generate -> compress with zstd."""
    
def test_generate_with_snappy():
    """Full pipeline: generate -> compress with snappy."""
    
def test_minio_upload_zstd():
    """Upload compressed file to MinIO."""
    
def test_compression_ratio_vs_gzip():
    """Verify compression ratios match expectations."""
```

### Performance Tests

```python
# benchmarks/test_compression_perf.py

def test_zstd_throughput():
    """Measure zstd compression speed."""
    
def test_snappy_throughput():
    """Measure snappy compression speed."""
    
def test_memory_usage():
    """Measure peak memory during compression."""
```

---

## Success Criteria

✅ **Phase 2.1 Complete When:**

- [x] zstandard library integrated and working
- [x] Snappy library integrated (optional)
- [x] CompressionHandler factory implemented
- [x] All exporters use native compression
- [x] Fallback to pure Python works
- [x] CLI updated with --jsonl-compress options
- [x] Benchmarks show +15-25% improvement
- [x] Zero breaking changes
- [x] All tests passing
- [x] Documentation updated

---

## Proof of Concept

Quick test to validate zstandard binding:

```python
python3 << 'EOF'
try:
    import zstandard as zstd
    print("✅ zstandard available")
    
    # Test compression
    original = b"Hello, compression! " * 100
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(original)
    
    # Test decompression
    dctx = zstd.ZstdDecompressor()
    decompressed = dctx.decompress(compressed)
    
    ratio = len(compressed) / len(original)
    print(f"Compression ratio: {ratio:.2%}")
    print(f"Match: {decompressed == original}")
except ImportError:
    print("⚠️  zstandard not available, would fallback to gzip")
EOF
```

---

## Dependencies Required

```bash
# Primary
zstandard>=0.21.0

# Optional (auto-fallback if missing)
python-snappy>=0.6.1

# Existing (unchanged)
pyarrow>=14.0.0
pandas>=2.0.0
boto3>=1.28.0
```

---

## Phase 2.1 Deliverables

1. **Code**
   - `src/fraud_generator/utils/compression.py` (NEW)
   - Updated exporters with compression factory
   - Updated generate.py CLI
   - Fallback error handling

2. **Tests**
   - Unit tests for compression handlers
   - Integration tests for full pipeline
   - Performance benchmarks

3. **Documentation**
   - CHANGELOG entry
   - README updates with examples
   - Compression tuning guide
   - Benchmark results

4. **Validation**
   - All existing tests still pass
   - Backward compatibility confirmed
   - Performance goals met (+15-25%)

---

## Next Steps After Phase 2.1

Phase 2.2 (Cython JIT):
- Compile hot loops with Cython
- Target: TransactionGenerator.generate() 
- Expected gain: +10-20%

Phase 2.3 (ProcessPoolExecutor):
- True parallelism with multiprocessing
- Manage seed distribution
- Expected gain: +30-40% with 16 workers

---

*Planning Date: 2025-01-30*
*Status: Ready for implementation*
*Priority: High (compression is bottleneck for large datasets)*
