#!/usr/bin/env python3
"""
Benchmark: multiprocessing GIL bypass for streaming.

Compares single-process baseline vs N parallel workers using
ParallelStreamManager with batch queuing (BATCH_SIZE=200).

Usage:
    python3 benchmarks/multiprocessing_benchmark.py
    python3 benchmarks/multiprocessing_benchmark.py --events 200000 --workers 1,2,4,8,16
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fraud_generator.generators import (
    CustomerGenerator,
    DeviceGenerator,
    DriverGenerator,
    RideGenerator,
    TransactionGenerator,
)
from fraud_generator.utils import CustomerIndex, DeviceIndex, DriverIndex
from fraud_generator.utils.parallel import BATCH_SIZE, ParallelStreamManager
from fraud_generator.utils.streaming import CustomerSessionState


def setup_data(num_customers=1000, num_drivers=100, seed=42):
    """Generate base customer/device/driver data."""
    random.seed(seed)
    cg = CustomerGenerator(use_profiles=True, seed=seed)
    dg = DeviceGenerator(seed=seed)
    drg = DriverGenerator(seed=seed)

    custs, devs, drivers = [], [], []
    dc = 1
    for i in range(num_customers):
        cid = f"CUST_{i+1:012d}"
        c = cg.generate(cid)
        custs.append(
            CustomerIndex(
                c["customer_id"],
                c["address"]["state"],
                c.get("behavioral_profile"),
                c.get("bank_code"),
                c.get("risk_level"),
            )
        )
        for d in dg.generate_for_customer(
            cid, c.get("behavioral_profile"), start_device_id=dc
        ):
            devs.append(DeviceIndex(d["device_id"], d["customer_id"]))
            dc += 1

    for i in range(num_drivers):
        did = f"DRV_{i+1:012d}"
        d = drg.generate(did)
        drivers.append(
            DriverIndex(
                d["driver_id"],
                d["operating_state"],
                d.get("operating_city", ""),
                d.get("active_apps", []),
            )
        )

    return custs, devs, drivers


def baseline_transactions(custs, devs, max_events, seed=42):
    """Single-process transaction generation (no queue overhead)."""
    cust_dev_map = {}
    for d in devs:
        cust_dev_map.setdefault(d.customer_id, []).append(d)
    pairs = [(c, d) for c in custs for d in cust_dev_map.get(c.customer_id, [])]

    tx_gen = TransactionGenerator(fraud_rate=0.02, use_profiles=True, seed=seed)
    sessions = {}
    random.seed(seed)

    t0 = time.time()
    for i in range(max_events):
        c, d = random.choice(pairs)
        s = sessions.setdefault(c.customer_id, CustomerSessionState(c.customer_id))
        tx = tx_gen.generate(
            tx_id=f"TX_{i}",
            customer_id=c.customer_id,
            device_id=d.device_id,
            timestamp=datetime.now(),
            customer_state=c.state,
            customer_profile=c.profile,
            session_state=s,
        )
        s.add_transaction(tx, datetime.now())
    return time.time() - t0


def baseline_rides(custs, drivers, max_events, seed=42):
    """Single-process ride generation (no queue overhead)."""
    rg = RideGenerator(fraud_rate=0.02, use_profiles=True, seed=seed)
    random.seed(seed)

    t0 = time.time()
    for i in range(max_events):
        c = random.choice(custs)
        d = random.choice(drivers)
        rg.generate(
            ride_id=f"R_{i}",
            driver_id=d.driver_id,
            passenger_id=c.customer_id,
            timestamp=datetime.now(),
            passenger_state=c.state,
            passenger_profile=c.profile,
        )
    return time.time() - t0


def parallel_test(custs, devs, drivers, num_workers, max_events, is_rides, seed=42):
    """Parallel generation through ParallelStreamManager."""
    mgr = ParallelStreamManager(num_workers=num_workers, queue_size=max(50000, max_events * 2))

    if is_rides:
        mgr.start_ride_workers(custs, drivers, 0.02, True, seed)
    else:
        mgr.start_tx_workers(custs, devs, 0.02, True, seed)

    cnt = 0
    t0 = time.time()
    t_first = None
    for evt in mgr.drain(max_events=max_events, rate=0):
        if t_first is None:
            t_first = time.time()
        cnt += 1

    t_drain = time.time()
    gen_elapsed = t_drain - (t_first or t0)
    startup = (t_first or t0) - t0

    mgr.shutdown()
    shutdown_time = time.time() - t_drain

    return {
        "events": cnt,
        "gen_elapsed": gen_elapsed,
        "startup": startup,
        "shutdown": shutdown_time,
        "evt_per_sec": cnt / gen_elapsed if gen_elapsed > 0 else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Multiprocessing GIL bypass benchmark")
    parser.add_argument("--events", type=int, default=100000, help="Events to generate per test")
    parser.add_argument("--workers", type=str, default="1,2,4,8", help="Comma-separated worker counts")
    parser.add_argument("--customers", type=int, default=1000)
    parser.add_argument("--drivers", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    worker_counts = [int(w) for w in args.workers.split(",")]

    print("=" * 70)
    print("BENCHMARK: Multiprocessing GIL Bypass — Streaming Mode")
    print("=" * 70)
    print(f"  Events per test:  {args.events:,}")
    print(f"  Customers:        {args.customers:,}")
    print(f"  Batch size:       {BATCH_SIZE}")
    print(f"  Worker counts:    {worker_counts}")
    print(f"  Python:           {sys.version.split()[0]}")
    print(f"  CPU cores:        {os.cpu_count()}")
    print()

    print("Setting up base data…", flush=True)
    custs, devs, drivers = setup_data(args.customers, args.drivers, args.seed)
    print(f"  {len(custs)} customers, {len(devs)} devices, {len(drivers)} drivers")

    results = {"meta": {
        "events": args.events,
        "customers": args.customers,
        "batch_size": BATCH_SIZE,
        "python": sys.version.split()[0],
        "cpu_cores": os.cpu_count(),
    }, "transactions": {}, "rides": {}}

    # ── Transactions ─────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("TRANSACTIONS")
    print("─" * 70)

    print(f"\n  Baseline (single-process, no queue)…", end=" ", flush=True)
    bl_tx = baseline_transactions(custs, devs, args.events, args.seed)
    bl_tx_rate = args.events / bl_tx
    print(f"{bl_tx_rate:,.0f} evt/s  ({bl_tx:.3f}s)")
    results["transactions"]["baseline"] = {"evt_per_sec": bl_tx_rate, "elapsed": bl_tx}

    for nw in worker_counts:
        print(f"\n  {nw} worker(s)…", end=" ", flush=True)
        r = parallel_test(custs, devs, drivers, nw, args.events, is_rides=False, seed=args.seed)
        speedup = r["evt_per_sec"] / bl_tx_rate
        print(f"{r['evt_per_sec']:,.0f} evt/s  ({r['gen_elapsed']:.3f}s)  "
              f"[{speedup:.2f}x baseline]  startup={r['startup']:.3f}s  shutdown={r['shutdown']:.1f}s")
        results["transactions"][f"{nw}_workers"] = {
            "evt_per_sec": r["evt_per_sec"],
            "elapsed": r["gen_elapsed"],
            "speedup": speedup,
            "startup": r["startup"],
            "shutdown": r["shutdown"],
        }

    # ── Rides ────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("RIDES")
    print("─" * 70)

    print(f"\n  Baseline (single-process, no queue)…", end=" ", flush=True)
    bl_r = baseline_rides(custs, drivers, args.events, args.seed)
    bl_r_rate = args.events / bl_r
    print(f"{bl_r_rate:,.0f} evt/s  ({bl_r:.3f}s)")
    results["rides"]["baseline"] = {"evt_per_sec": bl_r_rate, "elapsed": bl_r}

    for nw in worker_counts:
        print(f"\n  {nw} worker(s)…", end=" ", flush=True)
        r = parallel_test(custs, devs, drivers, nw, args.events, is_rides=True, seed=args.seed)
        speedup = r["evt_per_sec"] / bl_r_rate
        print(f"{r['evt_per_sec']:,.0f} evt/s  ({r['gen_elapsed']:.3f}s)  "
              f"[{speedup:.2f}x baseline]  startup={r['startup']:.3f}s  shutdown={r['shutdown']:.1f}s")
        results["rides"][f"{nw}_workers"] = {
            "evt_per_sec": r["evt_per_sec"],
            "elapsed": r["gen_elapsed"],
            "speedup": speedup,
            "startup": r["startup"],
            "shutdown": r["shutdown"],
        }

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"\n{'Workers':<10} {'TX evt/s':>12} {'TX speedup':>12} {'Rides evt/s':>12} {'Rides speedup':>14}")
    print("-" * 62)
    print(f"{'baseline':<10} {bl_tx_rate:>12,.0f} {'1.00x':>12} {bl_r_rate:>12,.0f} {'1.00x':>14}")
    for nw in worker_counts:
        tx_r = results["transactions"][f"{nw}_workers"]["evt_per_sec"]
        tx_s = results["transactions"][f"{nw}_workers"]["speedup"]
        rd_r = results["rides"][f"{nw}_workers"]["evt_per_sec"]
        rd_s = results["rides"][f"{nw}_workers"]["speedup"]
        print(f"{nw:<10} {tx_r:>12,.0f} {tx_s:>11.2f}x {rd_r:>12,.0f} {rd_s:>13.2f}x")

    if args.json:
        outpath = os.path.join(os.path.dirname(__file__), "multiprocessing_results.json")
        with open(outpath, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to {outpath}")

    print()


if __name__ == "__main__":
    main()
