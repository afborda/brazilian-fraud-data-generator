#!/usr/bin/env python3
"""
SynthFin — Export Format Benchmark
====================================
Benchmarks every available export format (JSONL, JSON, CSV, TSV, Parquet,
Arrow IPC, Database) measuring write throughput, file size and memory usage.

Usage:
    python3 benchmarks/format_benchmark.py
    python3 benchmarks/format_benchmark.py --quick          # fewer records
    python3 benchmarks/format_benchmark.py --count 50000    # custom count
    python3 benchmarks/format_benchmark.py --out results/format_bench.json

Metrics per format:
    - write_time_s       : wall-clock seconds to export records
    - records_per_second : export throughput
    - mb_per_second      : data write speed
    - file_size_mb       : resulting file on disk
    - compression_ratio  : bytes_per_event_serialized / bytes_on_disk
    - peak_memory_mb     : RSS peak during the export
"""

import argparse
import gc
import json
import os
import platform
import resource
import shutil
import sys
import tempfile
import time
from datetime import datetime
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
        uname = platform.uname()
        return {
            "os": uname.system,
            "cpu": uname.processor or uname.machine,
            "cpu_cores": cpu_count,
            "python": platform.python_version(),
            "timestamp": datetime.now().isoformat() + "Z",
        }
    except Exception:
        return {}


def _file_size_mb(path: str) -> float:
    """Get file/directory size in MB."""
    p = Path(path)
    if p.is_file():
        return p.stat().st_size / 1_048_576
    elif p.is_dir():
        total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return total / 1_048_576
    return 0.0


# ─── Data Generation ─────────────────────────────────────────────────────────

def generate_test_data(count: int, type_: str, seed: int = 42) -> list[dict]:
    """Generate test data for benchmarking exports."""
    from fraud_generator.cli.index_builder import (
        generate_customers_and_devices,
        generate_drivers,
    )
    from fraud_generator.cli.workers.batch_gen import (
        generate_transaction_batch,
        generate_ride_batch,
    )

    num_customers = max(50, count // 10)
    customers, devices, _, _ = generate_customers_and_devices(num_customers, True, seed)

    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 12, 31)
    fraud_rate = 0.03

    if type_ == "transactions":
        return generate_transaction_batch(
            0, count, customers, devices,
            start_dt, end_dt, fraud_rate, True, seed,
        )
    elif type_ == "rides":
        drivers, _ = generate_drivers(max(20, count // 10), seed)
        return generate_ride_batch(
            0, count, customers, drivers,
            start_dt, end_dt, fraud_rate, True, seed,
        )
    else:
        drivers, _ = generate_drivers(max(20, count // 10), seed)
        txs = generate_transaction_batch(
            0, count // 2, customers, devices,
            start_dt, end_dt, fraud_rate, True, seed,
        )
        rides = generate_ride_batch(
            0, count // 2, customers, drivers,
            start_dt, end_dt, fraud_rate, True, seed + 1,
        )
        return txs + rides


# ─── Single Format Benchmark ─────────────────────────────────────────────────

def benchmark_format(
    format_name: str,
    data: list[dict],
    tmp_dir: str,
    **exporter_kwargs,
) -> dict:
    """Run export benchmark for a single format."""
    from fraud_generator.exporters import get_exporter, is_format_available

    if not is_format_available(format_name):
        return {
            "format": format_name,
            "status": "unavailable",
            "reason": "missing dependencies",
        }

    try:
        exporter = get_exporter(format_name, **exporter_kwargs)
    except (ValueError, ImportError) as e:
        return {
            "format": format_name,
            "status": "error",
            "reason": str(e),
        }

    output_path = os.path.join(tmp_dir, f"bench_output{exporter.extension}")

    # Force GC before measurement
    gc.collect()

    mem_before = _rss_mb()
    cpu_before = _cpu_user()
    t0 = time.perf_counter()

    try:
        # Database exporter can't store Python lists/dicts directly in SQLite.
        # Serialize complex types to JSON strings and use export_stream for
        # chunked writes (method='multi' hits param limits on large batches).
        if format_name in ("db", "database"):
            import copy
            flat_data = []
            for record in data:
                rec = copy.copy(record)
                for k, v in rec.items():
                    if isinstance(v, (list, dict, set, tuple)):
                        rec[k] = json.dumps(v, default=str)
                flat_data.append(rec)
            written = exporter.export_stream(iter(flat_data), output_path, batch_size=8)
        else:
            written = exporter.export_batch(data, output_path)
    except Exception as e:
        return {
            "format": format_name,
            "status": "error",
            "reason": str(e),
        }

    elapsed = time.perf_counter() - t0
    cpu_used = _cpu_user() - cpu_before
    mem_peak = _rss_mb()

    file_mb = _file_size_mb(output_path)

    # Compute reference serialized size (JSON)
    sample = data[:min(200, len(data))]
    avg_bytes = sum(len(json.dumps(r, default=str)) for r in sample) / max(1, len(sample))
    total_json_mb = (avg_bytes * len(data)) / 1_048_576

    rps = written / elapsed if elapsed > 0 else 0
    mbps = file_mb / elapsed if elapsed > 0 else 0
    compression = total_json_mb / file_mb if file_mb > 0 else 0

    return {
        "format": format_name,
        "status": "ok",
        "records_written": written,
        "write_time_s": round(elapsed, 4),
        "records_per_second": round(rps),
        "mb_per_second": round(mbps, 2),
        "file_size_mb": round(file_mb, 3),
        "json_equiv_mb": round(total_json_mb, 3),
        "compression_ratio": round(compression, 2),
        "bytes_per_record_disk": round((file_mb * 1_048_576) / max(1, written)),
        "cpu_user_s": round(cpu_used, 3),
        "peak_memory_mb": round(mem_peak, 1),
        "mem_delta_mb": round(mem_peak - mem_before, 1),
    }


def benchmark_export_stream(
    format_name: str,
    data: list[dict],
    tmp_dir: str,
    batch_size: int = 5000,
    **exporter_kwargs,
) -> dict:
    """Benchmark the export_stream method (iterator-based) for a format."""
    from fraud_generator.exporters import get_exporter, is_format_available

    if not is_format_available(format_name):
        return {
            "format": format_name,
            "method": "export_stream",
            "status": "unavailable",
        }

    try:
        exporter = get_exporter(format_name, **exporter_kwargs)
    except (ValueError, ImportError) as e:
        return {
            "format": format_name,
            "method": "export_stream",
            "status": "error",
            "reason": str(e),
        }

    output_path = os.path.join(tmp_dir, f"bench_stream{exporter.extension}")

    gc.collect()
    mem_before = _rss_mb()
    cpu_before = _cpu_user()
    t0 = time.perf_counter()

    try:
        written = exporter.export_stream(iter(data), output_path, batch_size=batch_size)
    except Exception as e:
        return {
            "format": format_name,
            "method": "export_stream",
            "status": "error",
            "reason": str(e),
        }

    elapsed = time.perf_counter() - t0
    cpu_used = _cpu_user() - cpu_before
    mem_peak = _rss_mb()
    file_mb = _file_size_mb(output_path)

    rps = written / elapsed if elapsed > 0 else 0
    mbps = file_mb / elapsed if elapsed > 0 else 0

    return {
        "format": format_name,
        "method": "export_stream",
        "status": "ok",
        "records_written": written,
        "write_time_s": round(elapsed, 4),
        "records_per_second": round(rps),
        "mb_per_second": round(mbps, 2),
        "file_size_mb": round(file_mb, 3),
        "cpu_user_s": round(cpu_used, 3),
        "peak_memory_mb": round(mem_peak, 1),
        "mem_delta_mb": round(mem_peak - mem_before, 1),
    }


# ─── Parquet Compression Variants ────────────────────────────────────────────

PARQUET_COMPRESSIONS = ["snappy", "zstd", "gzip", "none"]


def benchmark_parquet_compressions(data: list[dict], tmp_dir: str) -> list[dict]:
    """Benchmark parquet with different compression codecs."""
    from fraud_generator.exporters import is_format_available

    if not is_format_available("parquet"):
        return [{"format": "parquet", "status": "unavailable"}]

    results = []
    for codec in PARQUET_COMPRESSIONS:
        label = f"parquet ({codec})"
        sub_dir = os.path.join(tmp_dir, f"pq_{codec}")
        os.makedirs(sub_dir, exist_ok=True)

        r = benchmark_format("parquet", data, sub_dir, compression=codec)
        r["format"] = label
        r["compression_codec"] = codec
        results.append(r)
        gc.collect()

    return results


# ─── Markdown Report ─────────────────────────────────────────────────────────

def _md_format_table(results: list[dict], title: str = "Export Format Benchmark") -> str:
    ok_results = [r for r in results if r.get("status") == "ok"]
    if not ok_results:
        return f"### {title}\n\nNo successful results."

    lines = [
        f"### {title}",
        "",
        "| Format | Records | Write Time (s) | Records/s | MB/s | File Size (MB) | JSON Equiv (MB) | Ratio | Mem (MB) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for r in sorted(ok_results, key=lambda x: x.get("write_time_s", 999)):
        lines.append(
            f"| {r['format']:<22} "
            f"| {r.get('records_written', 0):>8,} "
            f"| {r.get('write_time_s', 0):>14.4f} "
            f"| {r.get('records_per_second', 0):>9,} "
            f"| {r.get('mb_per_second', 0):>4.2f} "
            f"| {r.get('file_size_mb', 0):>14.3f} "
            f"| {r.get('json_equiv_mb', 0):>15.3f} "
            f"| {r.get('compression_ratio', 0):>5.2f}x "
            f"| {r.get('peak_memory_mb', 0):>8.1f} |"
        )

    return "\n".join(lines)


def _md_stream_table(results: list[dict]) -> str:
    ok_results = [r for r in results if r.get("status") == "ok"]
    if not ok_results:
        return ""

    lines = [
        "### Iterator-Based Export (export_stream)",
        "",
        "| Format | Records | Write Time (s) | Records/s | MB/s | File Size (MB) | Mem (MB) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for r in sorted(ok_results, key=lambda x: x.get("write_time_s", 999)):
        lines.append(
            f"| {r['format']:<22} "
            f"| {r.get('records_written', 0):>8,} "
            f"| {r.get('write_time_s', 0):>14.4f} "
            f"| {r.get('records_per_second', 0):>9,} "
            f"| {r.get('mb_per_second', 0):>4.2f} "
            f"| {r.get('file_size_mb', 0):>14.3f} "
            f"| {r.get('peak_memory_mb', 0):>8.1f} |"
        )

    return "\n".join(lines)


def _md_summary(
    batch_results: list[dict],
    stream_results: list[dict],
    compression_results: list[dict],
    machine: dict,
    data_type: str,
    count: int,
) -> str:
    lines = [
        "## Export Format Benchmark Results",
        "",
    ]

    if machine:
        lines += [
            f"**Machine**: {machine.get('cpu', 'unknown')} · "
            f"{machine.get('cpu_cores', '?')} cores · "
            f"{machine.get('os', '')} · "
            f"Python {machine.get('python', '')}",
            f"**Date**: {machine.get('timestamp', '')[:10]}",
            f"**Data**: {count:,} {data_type} records",
            "",
        ]

    # Summary stats
    ok_batch = [r for r in batch_results if r.get("status") == "ok"]
    if ok_batch:
        fastest = min(ok_batch, key=lambda r: r["write_time_s"])
        smallest = min(ok_batch, key=lambda r: r["file_size_mb"])
        highest_rps = max(ok_batch, key=lambda r: r["records_per_second"])

        lines += [
            "### Key Findings",
            "",
            f"- **Fastest format**: {fastest['format']} ({fastest['records_per_second']:,} records/s, {fastest['write_time_s']:.4f}s)",
            f"- **Smallest output**: {smallest['format']} ({smallest['file_size_mb']:.3f} MB, {smallest.get('compression_ratio', 0):.2f}x compression)",
            f"- **Highest throughput**: {highest_rps['format']} ({highest_rps['records_per_second']:,} records/s, {highest_rps['mb_per_second']:.2f} MB/s)",
            "",
        ]

    lines.append(_md_format_table(batch_results, "Batch Export (export_batch)"))
    lines.append("")

    if stream_results:
        lines.append(_md_stream_table(stream_results))
        lines.append("")

    if compression_results:
        lines.append(_md_format_table(compression_results, "Parquet Compression Variants"))
        lines.append("")

    # Unavailable/errors
    errors = [r for r in batch_results if r.get("status") != "ok"]
    if errors:
        lines += ["### Unavailable/Error Formats", ""]
        for r in errors:
            lines.append(f"- **{r['format']}**: {r.get('status')} — {r.get('reason', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


# ─── Format Matrix ───────────────────────────────────────────────────────────

# Formats to test (excluding minio/s3 which need external services)
FORMATS_BATCH = [
    ("jsonl", {}),
    ("json", {}),
    ("csv", {}),
    ("tsv", {}),
    ("parquet", {}),
    ("parquet_partitioned", {}),
    ("arrow", {}),
    ("db", {"db_url": "sqlite:///bench_output.db"}),
]

FORMATS_STREAM = [
    ("jsonl", {}),
    ("json", {}),
    ("csv", {}),
    ("tsv", {}),
    ("parquet", {}),
    ("arrow", {}),
]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Benchmark all export formats")
    parser.add_argument("--quick", action="store_true", help="Use fewer records (5,000)")
    parser.add_argument("--count", type=int, default=0, help="Exact record count")
    parser.add_argument("--type", default="transactions", choices=["transactions", "rides", "all"])
    parser.add_argument("--out", default="", help="JSON output path")
    parser.add_argument("--no-stream", action="store_true", help="Skip export_stream tests")
    parser.add_argument("--no-compression", action="store_true", help="Skip parquet compression variants")
    args = parser.parse_args()

    if args.count:
        count = args.count
    elif args.quick:
        count = 5_000
    else:
        count = 20_000

    machine = _machine_info()

    print(f"\n{'='*70}")
    print(f"  EXPORT FORMAT BENCHMARK")
    print(f"  Records: {count:,} | Type: {args.type} | Formats: {len(FORMATS_BATCH)}")
    print(f"  Machine: {machine.get('cpu', '?')} · {machine.get('cpu_cores', '?')} cores")
    print(f"{'='*70}")

    # ── Generate data once ─────────────────────────────────────────────────────
    print(f"\n[1/4] Generating {count:,} {args.type} records ...", end=" ", flush=True)
    t0 = time.perf_counter()
    data = generate_test_data(count, args.type)
    gen_time = time.perf_counter() - t0
    print(f"done ({len(data):,} records in {gen_time:.2f}s)")

    # Reference JSON size
    sample = data[:min(200, len(data))]
    avg_bytes = sum(len(json.dumps(r, default=str)) for r in sample) / max(1, len(sample))
    total_json_mb = (avg_bytes * len(data)) / 1_048_576
    print(f"    Reference JSON size: {total_json_mb:.2f} MB ({avg_bytes:.0f} bytes/record)")

    # ── Batch export tests ─────────────────────────────────────────────────────
    print(f"\n[2/4] Batch export benchmark ({len(FORMATS_BATCH)} formats)")
    print(f"{'─'*70}")

    batch_results = []
    tmp_base = tempfile.mkdtemp(prefix="synthfin_bench_")

    try:
        for i, (fmt, kwargs) in enumerate(FORMATS_BATCH, 1):
            tmp_dir = os.path.join(tmp_base, f"batch_{fmt}")
            os.makedirs(tmp_dir, exist_ok=True)

            print(f"  [{i:2}/{len(FORMATS_BATCH)}] {fmt:<22} ... ", end="", flush=True)
            r = benchmark_format(fmt, data, tmp_dir, **kwargs)
            batch_results.append(r)

            if r["status"] == "ok":
                print(
                    f"{r['records_per_second']:>8,} rec/s  "
                    f"{r['file_size_mb']:>7.3f} MB  "
                    f"{r['compression_ratio']:.2f}x  "
                    f"{r['write_time_s']:.4f}s"
                )
            else:
                print(f"SKIP ({r.get('reason', r['status'])})")

            gc.collect()

        # ── Stream export tests ────────────────────────────────────────────────
        stream_results = []
        if not args.no_stream:
            print(f"\n[3/4] Stream export benchmark ({len(FORMATS_STREAM)} formats)")
            print(f"{'─'*70}")

            for i, (fmt, kwargs) in enumerate(FORMATS_STREAM, 1):
                tmp_dir = os.path.join(tmp_base, f"stream_{fmt}")
                os.makedirs(tmp_dir, exist_ok=True)

                print(f"  [{i:2}/{len(FORMATS_STREAM)}] {fmt:<22} ... ", end="", flush=True)
                r = benchmark_export_stream(fmt, data, tmp_dir, **kwargs)
                stream_results.append(r)

                if r["status"] == "ok":
                    print(
                        f"{r['records_per_second']:>8,} rec/s  "
                        f"{r['file_size_mb']:>7.3f} MB  "
                        f"{r['write_time_s']:.4f}s"
                    )
                else:
                    print(f"SKIP ({r.get('reason', r['status'])})")

                gc.collect()
        else:
            print(f"\n[3/4] Stream export benchmark ... SKIPPED")

        # ── Parquet compression tests ──────────────────────────────────────────
        compression_results = []
        if not args.no_compression:
            print(f"\n[4/4] Parquet compression variants ({len(PARQUET_COMPRESSIONS)} codecs)")
            print(f"{'─'*70}")

            compression_results = benchmark_parquet_compressions(data, tmp_base)
            for r in compression_results:
                if r.get("status") == "ok":
                    print(
                        f"  {r['format']:<22} "
                        f"{r['records_per_second']:>8,} rec/s  "
                        f"{r['file_size_mb']:>7.3f} MB  "
                        f"{r['compression_ratio']:.2f}x  "
                        f"{r['write_time_s']:.4f}s"
                    )
                else:
                    print(f"  {r.get('format', '?'):<22} SKIP")
        else:
            print(f"\n[4/4] Parquet compression variants ... SKIPPED")

    finally:
        # Cleanup temp files
        shutil.rmtree(tmp_base, ignore_errors=True)

    # ── Output ─────────────────────────────────────────────────────────────────
    all_results = {
        "machine": machine,
        "config": {
            "count": count,
            "type": args.type,
            "data_generation_time_s": round(gen_time, 3),
            "json_reference_size_mb": round(total_json_mb, 3),
        },
        "batch_export": batch_results,
        "stream_export": stream_results,
        "parquet_compression": compression_results,
    }

    md = _md_summary(batch_results, stream_results, compression_results, machine, args.type, count)

    print(f"\n{'='*70}")
    print(md)

    out_path = args.out or str(ROOT / "benchmarks" / "format_benchmark_results.json")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ JSON saved to: {out_path}")

    md_path = out_path.replace(".json", ".md")
    with open(md_path, "w") as f:
        f.write(md)
        f.write("\n\n---\n")
        f.write(
            f"*Generated by `benchmarks/format_benchmark.py` on "
            f"{machine.get('timestamp', '')[:10]}*\n"
        )
    print(f"✓ Markdown saved to: {md_path}")


if __name__ == "__main__":
    main()
