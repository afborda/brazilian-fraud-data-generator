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
from fraud_generator.cli.constants import STREAM_FLUSH_EVERY
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

    tx_generator = TransactionGenerator(
        fraud_rate=fraud_rate, use_profiles=use_profiles, seed=worker_seed
    )

    exporter_kwargs = {"skip_none": True} if format_name in ("jsonl", "json") else {}
    if format_name == "jsonl" and jsonl_compress != "none":
        exporter_kwargs["jsonl_compress"] = jsonl_compress
    exporter = get_exporter(format_name, **exporter_kwargs)

    output_path = os.path.join(output_dir, f"transactions_{batch_id:05d}{exporter.extension}")
    days_span = max(1, (end_date - start_date).days)
    sessions: Dict[str, CustomerSessionState] = {}

    # T1: pré-computa pesos de data (DOW × sazonalidade) UMA VEZ por batch
    # Em vez de chamar pick_weighted_date() 15× por tx, resolve em O(1) amortizado
    from fraud_generator.config.seasonality import _date_weight as _dw
    _date_list = [start_date.date() + timedelta(days=i) for i in range(days_span + 1)]
    _date_weights = [_dw(d) for d in _date_list]

    if format_name == "jsonl":
        with open(output_path, "wb") as fh:
            buffer = []
            for i in range(num_transactions):
                customer, device = random.choice(pairs)
                timestamp = _random_timestamp(_date_list, _date_weights)
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
                if i > 0 and i % STREAM_FLUSH_EVERY == 0:
                    fh.flush()
            if buffer:
                fh.writelines(buffer)
    else:
        transactions = []
        for i in range(num_transactions):
            customer, device = random.choice(pairs)
            timestamp = _random_timestamp(_date_list, _date_weights)
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
            transactions.append(tx)
        exporter.export_batch(transactions, output_path)

    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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
