"""
In-memory batch generators — produce full record lists for MinIO upload.

These functions are *not* ProcessPoolExecutor workers themselves; they are
helper functions called by minio_parquet.py workers or by MinIORunner for
JSONL/CSV formats.
"""
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import sys as _sys
import os as _os
_src = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "..", ".."))
if _src not in _sys.path:
    _sys.path.insert(0, _src)

from fraud_generator.generators import TransactionGenerator, RideGenerator
from fraud_generator.utils import CustomerIndex, DeviceIndex, DriverIndex, CustomerSessionState

_TX_HOUR_WEIGHTS = {
    0: 2, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2,
    6: 4, 7: 6, 8: 10, 9: 12, 10: 14, 11: 14,
    12: 15, 13: 14, 14: 13, 15: 12, 16: 12, 17: 13,
    18: 14, 19: 15, 20: 14, 21: 12, 22: 8, 23: 4,
}
_TX_HOURS = list(_TX_HOUR_WEIGHTS.keys())
_TX_W = list(_TX_HOUR_WEIGHTS.values())

_RIDE_HOUR_WEIGHTS = {
    0: 3, 1: 2, 2: 1, 3: 1, 4: 1, 5: 2,
    6: 5, 7: 8, 8: 12, 9: 10, 10: 8, 11: 8,
    12: 10, 13: 8, 14: 7, 15: 7, 16: 8, 17: 12,
    18: 14, 19: 12, 20: 10, 21: 8, 22: 8, 23: 5,
}
_RIDE_HOURS = list(_RIDE_HOUR_WEIGHTS.keys())
_RIDE_W = list(_RIDE_HOUR_WEIGHTS.values())


def generate_transaction_batch(
    batch_id: int,
    num_transactions: int,
    customer_indexes: List[tuple],
    device_indexes: List[tuple],
    start_date: datetime,
    end_date: datetime,
    fraud_rate: float,
    use_profiles: bool,
    seed: Optional[int],
) -> List[Dict[str, Any]]:
    """Return a list of transaction dicts generated in memory."""
    worker_seed = (seed + batch_id * 12_345) if seed is not None else (
        batch_id * 12_345 + int(time.time() * 1000) % 10_000
    )
    random.seed(worker_seed)

    customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
    device_idx_list = [DeviceIndex(*d) for d in device_indexes]

    cust_dev_map: Dict = {}
    for dev in device_idx_list:
        cust_dev_map.setdefault(dev.customer_id, []).append(dev)

    pairs = [
        (c, d)
        for c in customer_idx_list
        for d in cust_dev_map.get(c.customer_id, [])
    ]
    if not pairs:
        pairs = [(customer_idx_list[0], device_idx_list[0])]

    tx_gen = TransactionGenerator(fraud_rate=fraud_rate, use_profiles=use_profiles, seed=worker_seed)
    sessions: Dict[str, CustomerSessionState] = {}
    days_span = max(1, (end_date - start_date).days)
    start_id = batch_id * num_transactions

    result = []
    for i in range(num_transactions):
        cust, dev = random.choice(pairs)
        day = start_date + timedelta(days=random.randint(0, days_span))
        hour = random.choices(_TX_HOURS, weights=_TX_W)[0]
        ts = day.replace(hour=hour, minute=random.randint(0, 59),
                         second=random.randint(0, 59), microsecond=random.randint(0, 999_999))

        session = sessions.setdefault(cust.customer_id, CustomerSessionState(cust.customer_id))
        tx = tx_gen.generate(
            tx_id=f"{start_id + i:015d}",
            customer_id=cust.customer_id,
            device_id=dev.device_id,
            timestamp=ts,
            customer_state=cust.state,
            customer_profile=cust.profile,
            session_state=session,
        )
        session.add_transaction(tx, ts)
        result.append(tx)
    return result


def generate_ride_batch(
    batch_id: int,
    num_rides: int,
    customer_indexes: List[tuple],
    driver_indexes: List[tuple],
    start_date: datetime,
    end_date: datetime,
    fraud_rate: float,
    use_profiles: bool,
    seed: Optional[int],
) -> List[Dict[str, Any]]:
    """Return a list of ride dicts generated in memory."""
    worker_seed = (seed + batch_id * 54_321) if seed is not None else (
        batch_id * 54_321 + int(time.time() * 1000) % 10_000
    )
    random.seed(worker_seed)

    customer_idx_list = [CustomerIndex(*c) for c in customer_indexes]
    driver_idx_list = [DriverIndex(*d) for d in driver_indexes]

    drivers_by_state: Dict = {}
    for drv in driver_idx_list:
        drivers_by_state.setdefault(drv.operating_state, []).append(drv)

    ride_gen = RideGenerator(fraud_rate=fraud_rate, use_profiles=use_profiles, seed=worker_seed)
    days_span = max(1, (end_date - start_date).days)
    start_id = batch_id * num_rides

    result = []
    for i in range(num_rides):
        passenger = random.choice(customer_idx_list)
        state_drivers = drivers_by_state.get(passenger.state, [])
        driver = random.choice(state_drivers if state_drivers else driver_idx_list)

        day = start_date + timedelta(days=random.randint(0, days_span))
        hour = random.choices(_RIDE_HOURS, weights=_RIDE_W)[0]
        ts = day.replace(hour=hour, minute=random.randint(0, 59),
                         second=random.randint(0, 59), microsecond=random.randint(0, 999_999))

        ride = ride_gen.generate(
            ride_id=f"RIDE_{start_id + i:012d}",
            driver_id=driver.driver_id,
            passenger_id=passenger.customer_id,
            timestamp=ts,
            passenger_state=passenger.state,
            passenger_profile=passenger.profile,
        )
        result.append(ride)
    return result
