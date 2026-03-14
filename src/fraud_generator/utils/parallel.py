"""
Parallel streaming engine - multiprocessing bypass for the Python GIL.

Spawns N worker processes, each with its own TransactionGenerator or
RideGenerator loop. Workers push BATCHES of generated events into a shared
multiprocessing.Queue which the main process drains and forwards to
the streaming connection (Kafka / webhook / stdout).

Batch queuing: Workers generate BATCH_SIZE events in memory, then
serialize the whole list as a single pickle.  This amortises ~1 ms of
pickle/unpickle overhead across many events instead of paying it per event.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import random
import sys
import time
from datetime import datetime
from multiprocessing import Event, Process, Queue
from typing import Any, Dict, List, Optional, Tuple

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# Events per batch pushed to queue.  Higher = less pickle overhead.
BATCH_SIZE = 200


def _tx_worker(
    worker_id: int,
    customer_tuples: List[tuple],
    device_tuples: List[tuple],
    fraud_rate: float,
    use_profiles: bool,
    seed: Optional[int],
    output_queue: Queue,
    stop_event: Event,
    base_tx_id: int,
) -> None:
    """Transaction generation worker (child process, batch queuing)."""
    import traceback
    try:
        from fraud_generator.generators import TransactionGenerator
        from fraud_generator.utils.streaming import CustomerSessionState
        from fraud_generator.utils import CustomerIndex, DeviceIndex

        worker_seed = (seed + worker_id * 7919) if seed is not None else None
        if worker_seed is not None:
            random.seed(worker_seed)

        customers = [CustomerIndex(*c) for c in customer_tuples]
        devices = [DeviceIndex(*d) for d in device_tuples]

        cust_dev_map: Dict[str, list] = {}
        for d in devices:
            cust_dev_map.setdefault(d.customer_id, []).append(d)

        pairs: List[Tuple] = []
        for c in customers:
            for d in cust_dev_map.get(c.customer_id, []):
                pairs.append((c, d))
        if not pairs:
            pairs = [(customers[0], devices[0])]

        tx_gen = TransactionGenerator(
            fraud_rate=fraud_rate,
            use_profiles=use_profiles,
            seed=worker_seed,
        )
        sessions: Dict[str, CustomerSessionState] = {}
        counter = 0

        while not stop_event.is_set():
            batch: List[Dict[str, Any]] = []
            for _ in range(BATCH_SIZE):
                if stop_event.is_set():
                    break
                customer, device = random.choice(pairs)
                timestamp = datetime.now()
                unique_tx_id = f"{base_tx_id}_w{worker_id}_{counter:08d}"

                session = sessions.get(customer.customer_id)
                if session is None:
                    session = CustomerSessionState(customer.customer_id)
                    sessions[customer.customer_id] = session

                tx = tx_gen.generate(
                    tx_id=unique_tx_id,
                    customer_id=customer.customer_id,
                    device_id=device.device_id,
                    timestamp=timestamp,
                    customer_state=customer.state,
                    customer_profile=customer.profile,
                    session_state=session,
                )
                session.add_transaction(tx, timestamp)
                batch.append(tx)
                counter += 1

            if batch:
                while not stop_event.is_set():
                    try:
                        output_queue.put(batch, timeout=0.1)
                        break
                    except Exception:
                        continue
    except Exception:
        traceback.print_exc()
    finally:
        try:
            output_queue.put(None, timeout=5.0)
        except Exception:
            pass


def _ride_worker(
    worker_id: int,
    customer_tuples: List[tuple],
    driver_tuples: List[tuple],
    fraud_rate: float,
    use_profiles: bool,
    seed: Optional[int],
    output_queue: Queue,
    stop_event: Event,
    base_ride_id: int,
) -> None:
    """Ride generation worker (child process, batch queuing)."""
    import traceback
    try:
        from fraud_generator.generators import RideGenerator
        from fraud_generator.utils import CustomerIndex, DriverIndex

        worker_seed = (seed + worker_id * 7919) if seed is not None else None
        if worker_seed is not None:
            random.seed(worker_seed)

        customers = [CustomerIndex(*c) for c in customer_tuples]
        drivers = [DriverIndex(*d) for d in driver_tuples]

        ride_gen = RideGenerator(
            fraud_rate=fraud_rate,
            use_profiles=use_profiles,
            seed=worker_seed,
        )
        counter = 0

        while not stop_event.is_set():
            batch: List[Dict[str, Any]] = []
            for _ in range(BATCH_SIZE):
                if stop_event.is_set():
                    break
                customer = random.choice(customers)
                driver = random.choice(drivers)
                timestamp = datetime.now()
                ride_id = f"RIDE_{base_ride_id}_w{worker_id}_{counter:08d}"

                ride = ride_gen.generate(
                    ride_id=ride_id,
                    driver_id=driver.driver_id,
                    passenger_id=customer.customer_id,
                    timestamp=timestamp,
                    passenger_state=customer.state,
                    passenger_profile=customer.profile,
                )
                batch.append(ride)
                counter += 1

            if batch:
                while not stop_event.is_set():
                    try:
                        output_queue.put(batch, timeout=0.1)
                        break
                    except Exception:
                        continue
    except Exception:
        traceback.print_exc()
    finally:
        try:
            output_queue.put(None, timeout=5.0)
        except Exception:
            pass


class ParallelStreamManager:
    """Manages a pool of generator-worker processes for high-throughput streaming."""

    def __init__(self, num_workers: int, queue_size: int = 10_000):
        self.num_workers = num_workers
        # queue_size expressed in batches (not individual events)
        self.queue: Queue = Queue(maxsize=max(32, queue_size // BATCH_SIZE))
        self.stop_event: Event = Event()
        self.workers: List[Process] = []

    def start_tx_workers(
        self,
        customers,
        devices,
        fraud_rate: float,
        use_profiles: bool,
        seed: Optional[int],
    ) -> None:
        """Partition customers across workers and launch processes."""
        base_tx_id = int(time.time() * 1000)
        cust_tuples = [tuple(c) for c in customers]
        dev_tuples = [tuple(d) for d in devices]
        chunk = max(1, len(cust_tuples) // self.num_workers)

        for wid in range(self.num_workers):
            start = wid * chunk
            end = start + chunk if wid < self.num_workers - 1 else len(cust_tuples)
            cust_slice = cust_tuples[start:end]
            cust_ids = {c[0] for c in cust_slice}
            dev_slice = [d for d in dev_tuples if d[1] in cust_ids]
            if not dev_slice:
                dev_slice = dev_tuples

            p = Process(
                target=_tx_worker,
                args=(wid, cust_slice, dev_slice, fraud_rate, use_profiles, seed,
                      self.queue, self.stop_event, base_tx_id),
                daemon=True,
            )
            p.start()
            self.workers.append(p)

    def start_ride_workers(
        self,
        customers,
        drivers,
        fraud_rate: float,
        use_profiles: bool,
        seed: Optional[int],
    ) -> None:
        """Launch ride-generation workers."""
        base_ride_id = int(time.time() * 1000)
        cust_tuples = [tuple(c) for c in customers]
        drv_tuples = [tuple(d) for d in drivers]
        chunk = max(1, len(cust_tuples) // self.num_workers)

        for wid in range(self.num_workers):
            start = wid * chunk
            end = start + chunk if wid < self.num_workers - 1 else len(cust_tuples)
            cust_slice = cust_tuples[start:end]

            p = Process(
                target=_ride_worker,
                args=(wid, cust_slice, drv_tuples, fraud_rate, use_profiles, seed,
                      self.queue, self.stop_event, base_ride_id),
                daemon=True,
            )
            p.start()
            self.workers.append(p)

    def drain(self, max_events: Optional[int] = None, rate: float = 0.0,
              quiet: bool = False):
        """Yield individual events from batches in the shared queue.

        Workers push lists of events; this method unpacks them one by one.
        """
        delay = 1.0 / rate if rate > 0 else 0.0
        finished_workers = 0
        count = 0

        while finished_workers < self.num_workers:
            if max_events and count >= max_events:
                break

            try:
                item = self.queue.get(timeout=0.5)
            except Exception:
                continue

            if item is None:
                finished_workers += 1
                continue

            # item is a list (batch) of event dicts
            for event in item:
                yield event
                count += 1
                if max_events and count >= max_events:
                    break
                if delay > 0:
                    time.sleep(delay)

    def shutdown(self) -> None:
        """Signal all workers to stop and wait for them to exit."""
        self.stop_event.set()
        # Drain queue in a loop to unblock workers stuck on put()
        deadline = time.time() + 3.0
        alive = list(self.workers)
        while alive and time.time() < deadline:
            # Drain any pending items
            while True:
                try:
                    self.queue.get_nowait()
                except Exception:
                    break
            still_alive = []
            for p in alive:
                p.join(timeout=0.05)
                if p.is_alive():
                    still_alive.append(p)
            alive = still_alive
        for p in alive:
            p.terminate()
        self.workers.clear()
