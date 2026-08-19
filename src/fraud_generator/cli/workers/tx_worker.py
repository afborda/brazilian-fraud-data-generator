"""
Transaction batch worker — runs inside a ProcessPoolExecutor child process.

IMPORTANT: This function must stay at the module top-level (never nested)
so that Python's pickle protocol can resolve it by fully-qualified name
``fraud_generator.cli.workers.tx_worker.worker_generate_batch``.
"""
import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict

# Guard: ensure src/ is discoverable in spawn-based multiprocessing (macOS/Windows)
import sys as _sys
_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _src not in _sys.path:
    _sys.path.insert(0, _src)

from fraud_generator.generators import TransactionGenerator
from fraud_generator.exporters import get_exporter
from fraud_generator.utils import CustomerIndex, DeviceIndex, CustomerSessionState
from fraud_generator.utils.ground_truth import ground_truth_path
from fraud_generator.cli.constants import STREAM_FLUSH_EVERY
from fraud_generator.profiles.behavioral import PROFILES
# T1: usa pesos trimodais do módulo de sazonalidade
from fraud_generator.config.seasonality import (
    HORA_WEIGHTS_PADRAO,
    pick_hour,
)


def worker_generate_batch(args: tuple) -> str:
    """
    Generate a batch of transactions and write to a file.

    Uses streaming writes (line-by-line) for JSONL to keep memory usage O(1).
    Accumulates to a list for CSV/Parquet (required by those formats).

    Args:
        args: Packed tuple —
            (batch_id, num_transactions, customer_indexes, device_indexes,
             start_date, end_date, fraud_rate, use_profiles,
             output_dir, format_name, seed, jsonl_compress)

    Returns:
        Absolute path to the generated file.
    """
    (
        batch_id, num_transactions, customer_indexes, device_indexes,
        start_date, end_date, fraud_rate, use_profiles,
        output_dir, format_name, seed, jsonl_compress,
    ) = args

    session_start_ms = int(time.time() * 1000)

    # Deterministic per-worker seed
    worker_seed = (seed + batch_id * 12_345) if seed is not None else (
        batch_id * 12_345 + int(time.time() * 1000) % 10_000
    )
    random.seed(worker_seed)

    # Rebuild lightweight indexes
    customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
    device_idx_list = [DeviceIndex(*d) for d in device_indexes]

    # Map customer → devices
    customer_device_map: Dict = {}
    for device in device_idx_list:
        customer_device_map.setdefault(device.customer_id, []).append(device)

    pairs = [
        (cust, dev)
        for cust in customer_idx_list
        for dev in customer_device_map.get(cust.customer_id, [])
    ]
    if not pairs:
        pairs = [(customer_idx_list[0], device_idx_list[0])]

    # Activity weights — how often each customer shows up in the stream.
    #
    # Picking uniformly gave every customer the same expected volume, so the
    # per-customer count came out near-binomial (measured: min 27, max 181 over
    # a year). Real activity is heavily heterogeneous: most correntistas make a
    # handful of PIX a month while MEIs and heavy users make hundreds. Without
    # that tail, "high velocity" is never legitimate behaviour, so
    # `velocity_transactions_24h > 8` separated fraud with 100% precision — and
    # a model trained on it floods production with false positives on the very
    # customers who transact most.
    #
    # BehavioralProfile.monthly_tx_frequency already carries the per-profile
    # rate (8-25 for falsa_central_victim up to 60-200 for micro_empreendedor)
    # and was never read by any generator. The lognormal factor adds
    # within-profile spread.
    _pair_weights = [
        _activity_weight(cust) for cust, _dev in pairs
    ]

    tx_generator = TransactionGenerator(
        fraud_rate=fraud_rate, use_profiles=use_profiles, seed=worker_seed
    )

    exporter_kwargs = {"skip_none": True} if format_name in ("jsonl", "json") else {}
    if format_name == "jsonl" and jsonl_compress != "none":
        exporter_kwargs["jsonl_compress"] = jsonl_compress
    exporter = get_exporter(format_name, **exporter_kwargs)

    output_path = os.path.join(output_dir, f"transactions_{batch_id:05d}{exporter.extension}")
    gt_path = ground_truth_path(output_path)
    days_span = max(1, (end_date - start_date).days)
    sessions: Dict[str, CustomerSessionState] = {}

    # T1: pré-computa pesos de data (DOW × sazonalidade) UMA VEZ por batch
    # Em vez de chamar pick_weighted_date() 15× por tx, resolve em O(1) amortizado
    from fraud_generator.config.seasonality import _date_weight as _dw
    _date_list = [start_date.date() + timedelta(days=i) for i in range(days_span + 1)]
    _date_weights = [_dw(d) for d in _date_list]

    # Sessions need transactions in chronological order — see _sorted_timestamps.
    _timestamps = _sorted_timestamps(num_transactions, _date_list, _date_weights)

    if format_name == "jsonl":
        with open(output_path, "wb") as fh, open(gt_path, "wb") as gt_fh:
            buffer = []
            gt_buffer = []
            for i in range(num_transactions):
                customer, device = random.choices(pairs, weights=_pair_weights, k=1)[0]
                timestamp = _timestamps[i]
                unique_tx_id = f"{session_start_ms}_{batch_id:04d}_{i:06d}"

                session = sessions.setdefault(
                    customer.customer_id, CustomerSessionState(customer.customer_id)
                )
                tx = tx_generator.generate(
                    tx_id=unique_tx_id,
                    customer_id=customer.customer_id,
                    device_id=device.device_id,
                    timestamp=timestamp,
                    customer_state=customer.state,
                    customer_profile=customer.profile,
                    session_state=session,
                    location_cluster=customer.location_cluster,
                )
                # Impossible travel check
                _is_imp, _dist = session.check_impossible_travel(
                    tx.get('geolocation_lat'), tx.get('geolocation_lon'), timestamp
                )
                tx['is_impossible_travel'] = _is_imp
                tx['distance_from_last_km'] = _dist
                session.add_transaction(tx, timestamp)

                # Ground truth (multiclass label, chain linkage, report delay,
                # card-test phase, attack-cluster id) rides in a companion
                # file — see utils/ground_truth.py — not in the main record.
                ground_truth = tx.pop("_ground_truth", None)
                if ground_truth is not None:
                    gt_buffer.append((
                        json.dumps(_clean_ground_truth(ground_truth), ensure_ascii=False, separators=(",", ":")) + "\n"
                    ).encode("utf-8"))

                record = exporter._clean_record(tx) if hasattr(exporter, "_clean_record") else tx
                line_bytes = (
                    json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
                ).encode("utf-8")

                if hasattr(exporter, "_compressor") and exporter._compressor is not None:
                    line_bytes = exporter._compressor.compress(line_bytes)

                buffer.append(line_bytes)
                if len(buffer) >= 1_000:
                    fh.writelines(buffer)
                    buffer.clear()
                if len(gt_buffer) >= 1_000:
                    gt_fh.writelines(gt_buffer)
                    gt_buffer.clear()
                if i > 0 and i % STREAM_FLUSH_EVERY == 0:
                    fh.flush()
            if buffer:
                fh.writelines(buffer)
            if gt_buffer:
                gt_fh.writelines(gt_buffer)
    else:
        transactions = []
        ground_truths = []
        for i in range(num_transactions):
            customer, device = random.choices(pairs, weights=_pair_weights, k=1)[0]
            timestamp = _timestamps[i]
            unique_tx_id = f"{session_start_ms}_{batch_id:04d}_{i:06d}"

            session = sessions.setdefault(
                customer.customer_id, CustomerSessionState(customer.customer_id)
            )
            tx = tx_generator.generate(
                tx_id=unique_tx_id,
                customer_id=customer.customer_id,
                device_id=device.device_id,
                timestamp=timestamp,
                customer_state=customer.state,
                customer_profile=customer.profile,
                session_state=session,
                location_cluster=customer.location_cluster,
            )
            # Impossible travel check
            _is_imp, _dist = session.check_impossible_travel(
                tx.get('geolocation_lat'), tx.get('geolocation_lon'), timestamp
            )
            tx['is_impossible_travel'] = _is_imp
            tx['distance_from_last_km'] = _dist
            session.add_transaction(tx, timestamp)
            ground_truth = tx.pop("_ground_truth", None)
            if ground_truth is not None:
                ground_truths.append(ground_truth)
            transactions.append(tx)
        exporter.export_batch(transactions, output_path)
        with open(gt_path, "w", encoding="utf-8") as gt_fh:
            for ground_truth in ground_truths:
                gt_fh.write(
                    json.dumps(_clean_ground_truth(ground_truth), ensure_ascii=False, separators=(",", ":")) + "\n"
                )

    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _activity_weight(customer) -> float:
    """Relative frequency with which *customer* appears in the transaction stream.

    Combines the profile's declared monthly rate with a lognormal factor for
    within-profile spread, so the per-customer volume distribution acquires the
    long right tail that real banking traffic has. See the comment at the call
    site for why a uniform pick made high velocity a perfect fraud predictor.
    """
    profile = getattr(customer, "profile", None)
    cfg = PROFILES.get(profile) if profile else None
    if cfg is not None:
        lo, hi = cfg.monthly_tx_frequency
        base = (lo + hi) / 2
    else:
        base = 40.0
    return max(0.05, base * random.lognormvariate(0.0, 0.6))


_GT_KEEP_ALWAYS = frozenset({"transaction_id", "is_fraud"})


def _clean_ground_truth(record: Dict) -> Dict:
    """Drop None-valued keys except the join/label anchors.

    ~98% of records carry no forensic detail (the fields only fire for a
    handful of fraud sub-types), so writing every key on every line would
    roughly double the companion file's size for no informational gain.
    `transaction_id` and `is_fraud` stay even when falsy so every row is
    still joinable and evaluable.
    """
    return {k: v for k, v in record.items() if v is not None or k in _GT_KEEP_ALWAYS}


def _sorted_timestamps(n: int, date_list, date_weights) -> list:
    """Draw *n* timestamps from the same distribution, returned in chronological order.

    `CustomerSessionState._prune_old` evicts from the left of a deque while the
    head is older than the cutoff, which only yields a correct sliding window if
    transactions arrive in time order. Feeding it independently-drawn timestamps
    made the "last 24h" window retain up to a full year of history, inflating
    every velocity feature (measured: mean velocity_transactions_24h of 30.96
    against a real-world ~1.7-3/day) and making time_since_last_txn_min and
    distance_from_last_km compare against a "previous" transaction that had in
    fact happened months later.

    Sorting here is cheap and bounded: batches cap at TRANSACTIONS_PER_FILE, so
    this list costs ~12 MB regardless of total dataset size.

    Note: this consumes RNG draws in a different order than the previous
    per-iteration sampling, so output for a given --seed changes from v4.18.0.
    The marginal distribution of timestamps is unchanged.
    """
    stamps = [_random_timestamp(date_list, date_weights) for _ in range(n)]
    stamps.sort()
    return stamps


def _random_timestamp(date_list, date_weights) -> datetime:
    # T1: dia ponderado por DOW × sazonalidade (pré-computado); hora trimodal (12h, 18h, 21h)
    day = random.choices(date_list, weights=date_weights, k=1)[0]
    hour = pick_hour(HORA_WEIGHTS_PADRAO)
    return datetime(
        day.year, day.month, day.day,
        hour,
        random.randint(0, 59),
        random.randint(0, 59),
        random.randint(0, 999_999),
    )
