"""
Ride batch worker — runs inside a ProcessPoolExecutor child process.

IMPORTANT: Must remain at module top-level for pickle compatibility.
"""
import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict

import sys as _sys
_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _src not in _sys.path:
    _sys.path.insert(0, _src)

from fraud_generator.generators import RideGenerator
from fraud_generator.exporters import get_exporter
from fraud_generator.utils import CustomerIndex, DriverIndex
from fraud_generator.cli.constants import STREAM_FLUSH_EVERY

_RIDE_HOUR_WEIGHTS = {
    0: 3, 1: 2, 2: 1, 3: 1, 4: 1, 5: 2,
    6: 5, 7: 8, 8: 12, 9: 10, 10: 8, 11: 8,
    12: 10, 13: 8, 14: 7, 15: 7, 16: 8, 17: 12,
    18: 14, 19: 12, 20: 10, 21: 8, 22: 8, 23: 5,
}
_RIDE_HOURS = list(_RIDE_HOUR_WEIGHTS.keys())
_RIDE_WEIGHTS = list(_RIDE_HOUR_WEIGHTS.values())


def worker_generate_rides_batch(args: tuple) -> str:
    """
    Generate a batch of rides and write to a file.

    Args:
        args: Packed tuple —
            (batch_id, num_rides, customer_indexes, driver_indexes,
             start_date, end_date, fraud_rate, use_profiles,
             output_dir, format_name, seed, jsonl_compress)

    Returns:
        Absolute path to the generated file.
    """
    (
        batch_id, num_rides, customer_indexes, driver_indexes,
        start_date, end_date, fraud_rate, use_profiles,
        output_dir, format_name, seed, jsonl_compress,
    ) = args

    worker_seed = (seed + batch_id * 54_321) if seed is not None else (
        batch_id * 54_321 + int(time.time() * 1000) % 10_000
    )
    random.seed(worker_seed)

    customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
    driver_idx_list = [DriverIndex(*d) for d in driver_indexes]

    # Group drivers by operating state for geo-aware selection
    drivers_by_state: Dict = {}
    for drv in driver_idx_list:
        drivers_by_state.setdefault(drv.operating_state, []).append(drv)

    ride_generator = RideGenerator(
        fraud_rate=fraud_rate, use_profiles=use_profiles, seed=worker_seed
    )

    exporter_kwargs = {"skip_none": True} if format_name in ("jsonl", "json") else {}
    if format_name == "jsonl" and jsonl_compress != "none":
        exporter_kwargs["jsonl_compress"] = jsonl_compress
    exporter = get_exporter(format_name, **exporter_kwargs)

    output_path = os.path.join(output_dir, f"rides_{batch_id:05d}{exporter.extension}")
    start_ride_id = batch_id * num_rides
    days_span = max(1, (end_date - start_date).days)

    if format_name == "jsonl":
        with open(output_path, "wb") as fh:
            buffer = []
            for i in range(num_rides):
                passenger, driver = _pick_pair(
                    customer_idx_list, driver_idx_list, drivers_by_state
                )
                timestamp = _random_timestamp(start_date, days_span)

                ride = ride_generator.generate(
                    ride_id=f"RIDE_{start_ride_id + i:012d}",
                    driver_id=driver.driver_id,
                    passenger_id=passenger.customer_id,
                    timestamp=timestamp,
                    passenger_state=passenger.state,
                    passenger_profile=passenger.profile,
                )

                record = exporter._clean_record(ride) if hasattr(exporter, "_clean_record") else ride
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
        rides = []
        for i in range(num_rides):
            passenger, driver = _pick_pair(
                customer_idx_list, driver_idx_list, drivers_by_state
            )
            timestamp = _random_timestamp(start_date, days_span)
            ride = ride_generator.generate(
                ride_id=f"RIDE_{start_ride_id + i:012d}",
                driver_id=driver.driver_id,
                passenger_id=passenger.customer_id,
                timestamp=timestamp,
                passenger_state=passenger.state,
                passenger_profile=passenger.profile,
            )
            rides.append(ride)
        exporter.export_batch(rides, output_path)

    return output_path


# ---------------------------------------------------------------------------

def _pick_pair(customers, drivers, drivers_by_state):
    passenger = random.choice(customers)
    state_drivers = drivers_by_state.get(passenger.state, [])
    driver = random.choice(state_drivers if state_drivers else drivers)
    return passenger, driver


def _random_timestamp(start: datetime, days_span: int) -> datetime:
    day = start + timedelta(days=random.randint(0, days_span))
    hour = random.choices(_RIDE_HOURS, weights=_RIDE_WEIGHTS)[0]
    return day.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=random.randint(0, 999_999),
    )
