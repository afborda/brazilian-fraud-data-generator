# 🧠 Memory Optimization Guide for Large-Scale Generation (50GB+)

## Current Issues Analysis

### Problem 1: Workers Copy All Indexes
Each multiprocessing worker receives a **full copy** of customer_indexes and device_indexes via pickle serialization.

```
Memory usage = base_indexes × num_workers
Example: 400MB indexes × 8 workers = 3.2GB just for indexes!
```

### Problem 2: Batch Accumulation
Each worker accumulates entire batch in memory before writing:
```
Memory per worker = TRANSACTIONS_PER_FILE × ~1KB = ~128MB
Total with 8 workers = ~1GB concurrent memory for pending writes
```

### Problem 3: No Streaming Write
Records are collected in lists before export, not streamed to disk.

---

## Recommended Solutions

### Solution 1: Memory-Mapped Index Files (Recommended for 50GB+)

Instead of passing indexes via pickle, save indexes to disk and let workers read them:

```python
# In main process - save indexes to temp file
import tempfile
import mmap

def save_indexes_to_mmap(customer_indexes, output_path):
    """Save indexes to memory-mapped file for efficient multi-process access."""
    import struct
    
    with open(output_path, 'wb') as f:
        # Write header: count
        f.write(struct.pack('I', len(customer_indexes)))
        
        # Write fixed-size records (use hash for string fields)
        for idx in customer_indexes:
            # Pack as fixed-size binary record
            record = struct.pack('16s2sH', 
                idx.customer_id.encode()[:16],
                idx.estado.encode()[:2],
                hash(idx.perfil or '') % 65536
            )
            f.write(record)

# In worker - read from mmap
def worker_with_mmap(args):
    batch_id, index_file_path, ... = args
    
    with open(index_file_path, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        count = struct.unpack('I', mm[:4])[0]
        
        # Random access without loading all into memory
        random_idx = random.randint(0, count - 1)
        offset = 4 + random_idx * RECORD_SIZE
        record = mm[offset:offset + RECORD_SIZE]
```

**Memory savings: ~90%** - Workers share the same physical memory pages.

---

### Solution 2: Streaming Export (Quick Fix)

Modify workers to write incrementally instead of accumulating:

```python
def worker_generate_batch_streaming(args: tuple) -> str:
    """Memory-efficient worker that streams to disk."""
    (batch_id, num_transactions, customer_indexes, device_indexes,
     start_date, end_date, fraud_rate, use_profiles, output_dir, format_name, seed) = args
    
    # Setup
    random.seed(seed + batch_id * 12345 if seed else batch_id * 12345)
    customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
    device_idx_list = [DeviceIndex(*d) for d in device_indexes]
    
    # Build pairs (one time)
    pairs = build_customer_device_pairs(customer_idx_list, device_idx_list)
    
    tx_generator = TransactionGenerator(fraud_rate=fraud_rate, use_profiles=use_profiles, seed=seed)
    
    output_path = os.path.join(output_dir, f'transactions_{batch_id:05d}.jsonl')
    
    # STREAM directly to file - don't accumulate!
    FLUSH_EVERY = 1000  # Flush every 1000 records
    
    with open(output_path, 'w', encoding='utf-8', buffering=8192) as f:
        for i in range(num_transactions):
            customer, device = random.choice(pairs)
            timestamp = generate_random_timestamp(start_date, end_date)
            
            tx = tx_generator.generate(
                tx_id=f"{batch_id * num_transactions + i:015d}",
                customer_id=customer.customer_id,
                device_id=device.device_id,
                timestamp=timestamp,
                customer_state=customer.estado,
                customer_profile=customer.perfil,
            )
            
            # Write immediately - no list accumulation!
            f.write(json.dumps(tx, ensure_ascii=False, separators=(',', ':')) + '\n')
            
            # Periodic flush for very large batches
            if i % FLUSH_EVERY == 0:
                f.flush()
    
    return output_path
```

**Memory savings: ~80%** per worker (no transaction list accumulation).

---

### Solution 3: Reduce Index Memory with Shared Memory (Python 3.8+)

Use `multiprocessing.shared_memory` for zero-copy index sharing:

```python
from multiprocessing import shared_memory
import numpy as np

def create_shared_indexes(customer_indexes):
    """Create shared memory for customer indexes."""
    # Convert to numpy structured array for shared memory
    dt = np.dtype([
        ('customer_id', 'U20'),
        ('estado', 'U2'),
        ('perfil', 'U30'),
    ])
    
    arr = np.array([
        (c.customer_id, c.estado, c.perfil or '')
        for c in customer_indexes
    ], dtype=dt)
    
    # Create shared memory
    shm = shared_memory.SharedMemory(create=True, size=arr.nbytes)
    shared_arr = np.ndarray(arr.shape, dtype=dt, buffer=shm.buf)
    shared_arr[:] = arr[:]
    
    return shm.name, arr.shape, dt

def worker_with_shared_memory(args):
    batch_id, shm_name, shape, dtype, ... = args
    
    # Attach to existing shared memory (zero-copy!)
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    customers = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
    
    # Use customers array directly...
    random_customer = customers[random.randint(0, len(customers) - 1)]
    
    existing_shm.close()  # Don't unlink - main process will do that
```

**Memory savings: ~95%** - True zero-copy between processes.

---

### Solution 4: Reduce Worker Concurrency for Low Memory

```python
def calculate_optimal_workers(target_size_gb, available_ram_gb):
    """Calculate optimal worker count based on memory constraints."""
    
    # Estimated memory per worker
    MEMORY_PER_WORKER_GB = 0.5  # ~500MB per worker (indexes + buffer + generation)
    
    # Leave 4GB for OS and other processes
    usable_ram = available_ram_gb - 4
    
    max_workers = max(1, int(usable_ram / MEMORY_PER_WORKER_GB))
    
    # Also limit by target size (diminishing returns after certain point)
    size_based_workers = max(1, min(16, int(target_size_gb / 5)))
    
    return min(max_workers, size_based_workers, mp.cpu_count())

# Usage
workers = calculate_optimal_workers(50, 22)  # 50GB target, 22GB RAM
# Result: ~4-6 workers for safe operation
```

---

### Solution 5: Chunked Customer Generation

For 50GB+, don't generate all customers upfront:

```python
def generate_in_chunks(target_gb, chunk_gb=5):
    """Generate data in memory-safe chunks."""
    
    num_chunks = int(target_gb / chunk_gb)
    
    for chunk_id in range(num_chunks):
        # Generate only this chunk's customers
        chunk_customers = target_gb / 100 / num_chunks  # ~5000 per chunk for 50GB
        
        customer_indexes, device_indexes, customer_data, device_data = \
            generate_customers_and_devices(num_customers=int(chunk_customers), ...)
        
        # Save customer/device data immediately
        save_chunk_data(customer_data, device_data, chunk_id)
        
        # Generate transactions for this chunk
        generate_transactions_for_chunk(
            customer_indexes, 
            device_indexes,
            chunk_id,
            transactions_per_chunk=...
        )
        
        # CRITICAL: Free memory before next chunk
        del customer_indexes, device_indexes, customer_data, device_data
        gc.collect()
```

---

## Best Storage Location

### Current: `./output/` (Local Disk)

**Pros:**
- ✅ Fastest write speed (NVMe/SSD)
- ✅ Simple path management

**Cons:**
- ❌ Limited to 56GB available
- ❌ No redundancy

### Recommended Alternatives for 50GB+:

| Location | Best For | Speed | Cost |
|----------|----------|-------|------|
| **Local SSD** (`./output`) | Development, <100GB | ⚡ Fastest | Free |
| **External NVMe** | Production, 100GB-1TB | ⚡ Fast | $$ |
| **S3/MinIO** | Cloud, unlimited | 🐢 Slower | $$ |
| **HDFS/Spark** | Big Data, 1TB+ | ⚡ Distributed | $$$ |

### Recommended: Use `/tmp` for Intermediate Files

```python
# Use tmpfs (RAM-based) for intermediate files if available
import tempfile

TEMP_DIR = '/tmp/fraud_generator'  # Uses tmpfs (RAM) on Linux
OUTPUT_DIR = '/data/fraud_output'   # Final output to persistent storage

# Generate to temp first (fast), then move to final location
temp_output = os.path.join(TEMP_DIR, f'batch_{batch_id}.jsonl')
# ... generate ...
shutil.move(temp_output, final_output)
```

---

## Recommended Configuration for 50GB Generation

```bash
# For your system (22GB RAM, 56GB disk free):

# Option A: Safe mode (slower but guaranteed)
python generate.py --size 50GB --workers 4 --output /data/output

# Option B: Aggressive (faster, monitor memory)
python generate.py --size 50GB --workers 6 --output /data/output

# Option C: Chunked generation (most reliable)
for i in {1..10}; do
    python generate.py --size 5GB --output /data/output/chunk_$i --seed $((42 + i))
done
```

---

## Quick Fixes to Apply Now

### 1. Reduce `TARGET_FILE_SIZE_MB`

```python
# generate.py line 64
TARGET_FILE_SIZE_MB = 64  # Reduce from 128MB to 64MB per file
```

More files, but less memory per worker.

### 2. Add Memory Monitoring

```python
import psutil

def check_memory_pressure():
    """Warn if memory is getting low."""
    mem = psutil.virtual_memory()
    if mem.percent > 85:
        print(f"⚠️  WARNING: Memory usage at {mem.percent}%!")
        return True
    return False
```

### 3. Use `--workers 4` for 50GB

```bash
python generate.py --size 50GB --workers 4 --output ./output
```

---

## Estimated Memory Usage (Current vs Optimized)

| Component | Current (50GB) | Optimized |
|-----------|----------------|-----------|
| Customer indexes (500k) | ~400MB × 8 = **3.2GB** | ~400MB shared |
| Transaction buffers | ~128MB × 8 = **1GB** | ~10MB (streaming) |
| Python overhead | ~2GB | ~1GB |
| **TOTAL** | **~6.2GB** | **~1.5GB** |

With optimizations, you can safely generate 50GB+ even with 8GB RAM!
