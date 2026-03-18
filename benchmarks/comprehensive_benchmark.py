#!/usr/bin/env python3
"""
SynthFin — Comprehensive Benchmark
====================================
Measures batch generation AND streaming performance across multiple
configurations. Outputs JSON + Markdown tables ready to paste into README.

Usage:
    python3 benchmarks/comprehensive_benchmark.py
    python3 benchmarks/comprehensive_benchmark.py --quick   # fewer combos
    python3 benchmarks/comprehensive_benchmark.py --out results/benchmark.json

Metrics collected per run:
    - total_time_s       : wall-clock seconds from start to last record
    - events_per_second  : throughput
    - mb_per_second      : data throughput (batch serialized size)
    - peak_memory_mb     : RSS peak during the run
    - bytes_per_event    : average serialized JSON size per record
    - cpu_user_s         : user CPU seconds consumed
    - workers            : number of parallel workers used
"""

import argparse
import gc
import json
import os
import platform
import resource
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

def _cpu_user() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_utime

def _machine_info() -> dict:
    try:
        cpu_count = os.cpu_count() or 1
        uname     = platform.uname()
        return {
            "os":         uname.system,
            "cpu":        uname.processor or uname.machine,
            "cpu_cores":  cpu_count,
            "python":     platform.python_version(),
            "timestamp":  datetime.now().isoformat() + "Z",
        }
    except Exception:
        return {}


# ─── In-process batch benchmark ───────────────────────────────────────────────

def _build_indexes(count: int, type_: str, seed: int):
    from fraud_generator.cli.index_builder import (
        generate_customers_and_devices,
        generate_drivers,
    )
    from fraud_generator.cli.constants import RIDES_PER_DRIVER

    num_customers = max(50, count // 10)
    customers, devices, _, _ = generate_customers_and_devices(num_customers, True, seed)

    if type_ in ("rides", "all"):
        num_drivers = max(20, count // 10)
        drivers, _ = generate_drivers(num_drivers, seed)
    else:
        drivers = []

    return customers, devices, drivers


def _batch_chunk(args_tuple):
    """Worker function: generate one chunk (pickleable top-level fn)."""
    batch_id, chunk_size, type_, customers, devices, drivers, seed, fraud_rate = args_tuple

    from fraud_generator.cli.workers.batch_gen import (
        generate_transaction_batch,
        generate_ride_batch,
    )
    start_dt = datetime(2024, 1, 1)
    end_dt   = datetime(2024, 12, 31)

    if type_ == "transactions":
        return generate_transaction_batch(
            batch_id, chunk_size, customers, devices,
            start_dt, end_dt, fraud_rate, True, seed + batch_id,
        )
    elif type_ == "rides":
        return generate_ride_batch(
            batch_id, chunk_size, customers, drivers,
            start_dt, end_dt, fraud_rate, True, seed + batch_id,
        )
    else:  # all
        txs = generate_transaction_batch(
            batch_id, chunk_size, customers, devices,
            start_dt, end_dt, fraud_rate, True, seed + batch_id,
        )
        rides = generate_ride_batch(
            batch_id, chunk_size, customers, drivers,
            start_dt, end_dt, fraud_rate, True, seed + batch_id,
        )
        return txs + rides


def run_batch(
    type_:      str,
    count:      int,
    workers:    int,
    seed:       int,
    fraud_rate: float = 0.03,
) -> dict:
    """Run in-process batch generation and collect metrics."""
    try:
        customers, devices, drivers = _build_indexes(count, type_, seed)
    except Exception as e:
        return {"error": f"index build failed: {e}", "config": {
            "type": type_, "count": count, "workers": workers,
        }}

    chunk_size = max(1000, count // max(1, workers))
    n_chunks   = max(1, count // chunk_size)
    tasks = [
        (i, chunk_size, type_, customers, devices, drivers, seed, fraud_rate)
        for i in range(n_chunks)
    ]

    cpu_before = _cpu_user()
    t0         = time.perf_counter()

    try:
        records = []
        if workers == 1:
            for task in tasks:
                records.extend(_batch_chunk(task))
        else:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                for chunk in pool.map(_batch_chunk, tasks):
                    records.extend(chunk)
    except Exception as e:
        return {"error": str(e), "config": {
            "type": type_, "count": count, "workers": workers,
        }}

    elapsed  = time.perf_counter() - t0
    cpu_used = _cpu_user() - cpu_before

    # Measure serialized size (JSON)
    sample = records[:min(200, len(records))]
    avg_bytes = sum(len(json.dumps(r, default=str)) for r in sample) / max(1, len(sample))
    total_bytes = avg_bytes * len(records)

    actual = len(records)
    eps  = actual / elapsed if elapsed > 0 else 0
    mbps = (total_bytes / 1_048_576) / elapsed if elapsed > 0 else 0

    return {
        "mode":              "batch",
        "type":              type_,
        "count":             actual,
        "workers":           workers,
        "seed":              seed,
        "fraud_rate":        fraud_rate,
        "total_time_s":      round(elapsed, 3),
        "events_per_second": round(eps),
        "mb_per_second":     round(mbps, 2),
        "bytes_per_event":   round(avg_bytes, 1),
        "cpu_user_s":        round(cpu_used, 2),
        "peak_memory_mb":    round(_rss_mb(), 1),
    }


# ─── Streaming benchmark ──────────────────────────────────────────────────────

def run_streaming(
    type_:     str,
    count:     int,
    rate:      int,
    seed:      int = 42,
) -> dict:
    """Benchmark streaming throughput with a token-bucket pacing loop."""
    import queue
    import threading

    try:
        customers, devices, drivers = _build_indexes(count, type_, seed)
    except Exception as e:
        return {"error": f"index build failed: {e}"}

    buf   = queue.Queue(maxsize=10_000)
    done  = threading.Event()
    stats = {"generated": 0, "errors": 0}

    chunk_size = min(500, max(100, rate // 4))
    start_dt   = datetime(2024, 1, 1)
    end_dt     = datetime(2024, 12, 31)

    def producer():
        from fraud_generator.cli.workers.batch_gen import (
            generate_transaction_batch,
            generate_ride_batch,
        )
        try:
            batch_id = 0
            while stats["generated"] < count:
                remaining = count - stats["generated"]
                n = min(chunk_size, remaining)
                if type_ == "transactions":
                    batch = generate_transaction_batch(
                        batch_id, n, customers, devices, start_dt, end_dt, 0.03, True, seed + batch_id
                    )
                elif type_ == "rides":
                    batch = generate_ride_batch(
                        batch_id, n, customers, drivers, start_dt, end_dt, 0.03, True, seed + batch_id
                    )
                else:
                    batch = generate_transaction_batch(
                        batch_id, n, customers, devices, start_dt, end_dt, 0.03, True, seed + batch_id
                    )
                for rec in batch:
                    buf.put(rec, timeout=5)
                    stats["generated"] += 1
                batch_id += 1
        except Exception:
            stats["errors"] += 1
        finally:
            done.set()

    token_interval = 1.0 / rate
    consumed       = 0

    cpu_before = _cpu_user()
    t0         = time.perf_counter()

    thread = threading.Thread(target=producer, daemon=True)
    thread.start()

    next_send = t0
    while consumed < count and not (done.is_set() and buf.empty()):
        now = time.perf_counter()
        if now < next_send:
            time.sleep(max(0, next_send - now))

        try:
            _ = buf.get_nowait()
            consumed  += 1
            next_send  = time.perf_counter() + token_interval
        except Exception:
            if done.is_set():
                break

    elapsed  = time.perf_counter() - t0
    cpu_used = _cpu_user() - cpu_before
    thread.join(timeout=5)

    actual_eps = consumed / elapsed if elapsed > 0 else 0

    return {
        "mode":              "streaming",
        "type":              type_,
        "count":             count,
        "target_rate_eps":   rate,
        "actual_rate_eps":   round(actual_eps),
        "rate_accuracy_pct": round(actual_eps / rate * 100, 1) if rate else 0,
        "events_sent":       consumed,
        "total_time_s":      round(elapsed, 3),
        "cpu_user_s":        round(cpu_used, 2),
        "peak_memory_mb":    round(_rss_mb(), 1),
    }


# ─── Markdown formatting ──────────────────────────────────────────────────────

def _md_batch_table(results: list[dict]) -> str:
    rows = [r for r in results if r.get("mode") == "batch" and "error" not in r]
    if not rows:
        return ""

    lines = [
        "### Batch Generation Performance",
        "",
        "| Type | Count | Workers | Time (s) | Events/s | MB/s | Bytes/evt | Mem (MB) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['type']:<12} "
            f"| {r['count']:>10,} "
            f"| {r['workers']:>7} "
            f"| {r['total_time_s']:>8.2f} "
            f"| {r['events_per_second']:>8,} "
            f"| {r['mb_per_second']:>4.1f} "
            f"| {r['bytes_per_event']:>9.0f} "
            f"| {r['peak_memory_mb']:>8.1f} |"
        )
    return "\n".join(lines)


def _md_streaming_table(results: list[dict]) -> str:
    rows = [r for r in results if r.get("mode") == "streaming" and "error" not in r]
    if not rows:
        return ""

    lines = [
        "### Streaming Performance",
        "",
        "| Type | Count | Target (evt/s) | Actual (evt/s) | Accuracy | Time (s) | Mem (MB) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['type']:<12} "
            f"| {r['count']:>10,} "
            f"| {r['target_rate_eps']:>14,} "
            f"| {r['actual_rate_eps']:>14,} "
            f"| {r['rate_accuracy_pct']:>7.1f}% "
            f"| {r['total_time_s']:>8.2f} "
            f"| {r['peak_memory_mb']:>8.1f} |"
        )
    return "\n".join(lines)


def _md_summary(results: list[dict], machine: dict) -> str:
    batch  = [r for r in results if r.get("mode") == "batch"      and "error" not in r]
    stream = [r for r in results if r.get("mode") == "streaming"  and "error" not in r]

    lines = ["## Benchmark Results", ""]

    if machine:
        lines += [
            f"**Machine**: {machine.get('cpu', 'unknown')} · "
            f"{machine.get('cpu_cores', '?')} cores · "
            f"{machine.get('os', '')} · "
            f"Python {machine.get('python', '')}",
            f"**Date**: {machine.get('timestamp', '')[:10]}",
            "",
        ]

    if batch:
        max_eps     = max(r["events_per_second"] for r in batch)
        max_workers = max(r["workers"]           for r in batch)
        lines += [
            f"**Batch peak throughput**: {max_eps:,} events/s ({max_workers} workers)",
        ]
    if stream:
        max_rate = max(r["actual_rate_eps"] for r in stream)
        lines += [f"**Streaming max rate**: {max_rate:,} events/s (token-bucket)"]

    lines += ["", _md_batch_table(results), "", _md_streaming_table(results)]
    return "\n".join(lines)


# ─── Matrices ─────────────────────────────────────────────────────────────────

BATCH_MATRIX = [
    # (type,          count,   workers, seed)
    ("transactions",  10_000,  1,       42),
    ("transactions",  10_000,  4,       42),
    ("transactions",  10_000,  8,       42),
    ("transactions",  50_000,  1,       42),
    ("transactions",  50_000,  4,       42),
    ("transactions",  50_000,  8,       42),
    ("transactions", 100_000,  4,       42),
    ("transactions", 100_000,  8,       42),
    ("rides",         10_000,  1,       42),
    ("rides",         50_000,  4,       42),
    ("all",           10_000,  4,       42),
    ("all",           50_000,  4,       42),
]

BATCH_MATRIX_QUICK = [
    ("transactions",  10_000,  1,  42),
    ("transactions",  10_000,  4,  42),
    ("transactions",  50_000,  4,  42),
    ("transactions",  50_000,  8,  42),
    ("rides",         10_000,  1,  42),
    ("all",           10_000,  4,  42),
]

STREAM_MATRIX = [
    # (type,          count,   rate_eps)
    ("transactions",  5_000,   10),
    ("transactions",  5_000,   50),
    ("transactions",  5_000,   100),
    ("transactions",  5_000,   500),
    ("transactions",  5_000,   1_000),
    ("transactions", 10_000,   2_000),
    ("rides",         5_000,   50),
    ("rides",         5_000,   500),
]

STREAM_MATRIX_QUICK = [
    ("transactions",  2_000,   10),
    ("transactions",  2_000,   100),
    ("transactions",  2_000,   500),
    ("rides",         2_000,   100),
]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick",     action="store_true", help="Run fewer combinations")
    parser.add_argument("--out",       default="",          help="JSON output path")
    parser.add_argument("--no-batch",  action="store_true")
    parser.add_argument("--no-stream", action="store_true")
    args = parser.parse_args()

    machine = _machine_info()
    results: list[dict] = []

    batch_matrix  = BATCH_MATRIX_QUICK  if args.quick else BATCH_MATRIX
    stream_matrix = STREAM_MATRIX_QUICK if args.quick else STREAM_MATRIX

    # ── Batch ──────────────────────────────────────────────────────────────────
    if not args.no_batch:
        print(f"\n{'='*60}")
        print(f"BATCH BENCHMARK  ({len(batch_matrix)} combinations)")
        print(f"{'='*60}")
        for i, (type_, count, workers, seed) in enumerate(batch_matrix, 1):
            print(f"[{i:2}/{len(batch_matrix)}] {type_:12} {count:>8,}  {workers}w ... ", end="", flush=True)
            r = run_batch(type_, count, workers, seed)
            results.append(r)
            if "error" in r:
                print(f"ERROR: {r['error'][:60]}")
            else:
                print(f"{r['events_per_second']:>8,} evt/s  {r['mb_per_second']:5.1f} MB/s  {r['total_time_s']:.2f}s")
            gc.collect()

    # ── Streaming ──────────────────────────────────────────────────────────────
    if not args.no_stream:
        print(f"\n{'='*60}")
        print(f"STREAMING BENCHMARK  ({len(stream_matrix)} combinations)")
        print(f"{'='*60}")
        for i, (type_, count, rate) in enumerate(stream_matrix, 1):
            print(f"[{i:2}/{len(stream_matrix)}] {type_:12} {count:>6,}  @ {rate:>6} evt/s ... ", end="", flush=True)
            r = run_streaming(type_, count, rate)
            results.append(r)
            if "error" in r:
                print(f"ERROR: {r['error']}")
            else:
                print(
                    f"actual {r['actual_rate_eps']:>6,} evt/s  "
                    f"({r['rate_accuracy_pct']:.0f}% accuracy)  "
                    f"{r['total_time_s']:.2f}s"
                )
            gc.collect()

    # ── Output ─────────────────────────────────────────────────────────────────
    output = {"machine": machine, "results": results}

    print("\n" + "="*60)
    print(_md_summary(results, machine))

    out_path = args.out or str(ROOT / "benchmarks" / "comprehensive_results.json")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✓ JSON saved to: {out_path}")

    md_path = out_path.replace(".json", ".md")
    with open(md_path, "w") as f:
        f.write(_md_summary(results, machine))
        f.write("\n\n")
        f.write("---\n")
        f.write(f"*Generated by `benchmarks/comprehensive_benchmark.py` on {machine.get('timestamp','')[:10]}*\n")
    print(f"✓ Markdown saved to: {md_path}")
    print(f"\nPaste the Markdown content into README.md → Performance Snapshot section.")


if __name__ == "__main__":
    main()
