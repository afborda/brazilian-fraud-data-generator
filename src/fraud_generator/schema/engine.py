"""
SchemaEngine: Orchestrates data generation according to a declarative JSON schema.

This is the top-level entry point for schema-driven generation.

Usage (from Python)::

    from fraud_generator.schema import SchemaEngine

    engine = SchemaEngine.from_file("my_schema.json")
    for record in engine.generate(count=1000):
        print(record)

Usage (CLI)::

    python generate.py --schema my_schema.json --count 10000 --output ./data

"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from .parser import SchemaParser
from .mapper import FieldMapper
from .ai_corrector import AISchemaCorrector


class SchemaEngine:
    """
    Generates records according to a user-defined declarative JSON schema.

    Internally it:
    1. Parses / validates the schema.
    2. Boots the appropriate generators (banking or ride_share).
    3. For each record, generates all required entities, then applies the
       FieldMapper to produce the user's desired structure.

    The engine is lazy — ``generate()`` is a generator (yields one record at
    a time), so it works well for large outputs without excess memory use.
    """

    def __init__(self, parsed_schema: Dict[str, Any]):
        """
        Construct from a dict already validated by SchemaParser.
        Use :meth:`from_file` or :meth:`from_string` instead most of the time.
        """
        self._schema = parsed_schema
        self._profile = parsed_schema["profile"]
        self._fraud_rate = parsed_schema.get("fraud_rate", 0.02)
        self._seed = parsed_schema.get("seed")
        self._output_template = parsed_schema["output"]
        self._mapper = FieldMapper()

        # Lazy-init generators
        self._customer_gen = None
        self._device_gen = None
        self._tx_gen = None
        self._driver_gen = None
        self._ride_gen = None

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_file(
        cls,
        path: Union[str, Path],
        *,
        strict: bool = False,
        auto_correct: bool = True,
        ai_api_key: Optional[str] = None,
        ai_provider: str = "openai",
    ) -> "SchemaEngine":
        """
        Load a schema from a JSON file.

        Args:
            path:         Path to the JSON schema file.
            strict:       If True, raise on unknown fields (instead of warning).
            auto_correct: If True, run AI/heuristic correction before parsing.
            ai_api_key:   Optional LLM API key for schema correction.
            ai_provider:  "openai" | "anthropic" | "none".
        """
        path = Path(path)
        raw_text = path.read_text(encoding="utf-8")
        return cls._from_text(
            raw_text,
            strict=strict,
            auto_correct=auto_correct,
            ai_api_key=ai_api_key,
            ai_provider=ai_provider,
        )

    @classmethod
    def from_string(
        cls,
        json_text: str,
        *,
        strict: bool = False,
        auto_correct: bool = True,
        ai_api_key: Optional[str] = None,
        ai_provider: str = "openai",
    ) -> "SchemaEngine":
        """
        Load a schema from a raw JSON string (e.g. pasted by a user or sent via API).
        """
        return cls._from_text(
            json_text,
            strict=strict,
            auto_correct=auto_correct,
            ai_api_key=ai_api_key,
            ai_provider=ai_provider,
        )

    @classmethod
    def _from_text(
        cls,
        text: str,
        *,
        strict: bool,
        auto_correct: bool,
        ai_api_key: Optional[str],
        ai_provider: str,
    ) -> "SchemaEngine":
        if auto_correct:
            corrector = AISchemaCorrector(
                api_key=ai_api_key,
                provider=ai_provider,
            )
            result = corrector.correct(text)
            if result.warnings:
                for w in result.warnings:
                    print(f"[schema] ⚠  {w}")
            if not result.success:
                print(f"[schema] ⚠  Correction failed: {result.explanation}")
            else:
                text = result.fixed_schema
                if result.used_ai:
                    print(f"[schema] ✅ AI correction applied ({ai_provider}).")
                elif result.explanation and "No issues" not in result.explanation:
                    print(f"[schema] ✅ Heuristic correction applied.")

        parser = SchemaParser(strict=strict)
        parsed = parser.from_string(text)
        if parser.warnings:
            for w in parser.warnings:
                print(f"[schema] ⚠  {w}")
        return cls(parsed)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(self, count: int = 100) -> Iterator[Dict[str, Any]]:
        """
        Yield ``count`` records shaped according to the loaded schema.

        Args:
            count: Number of records to generate.

        Yields:
            dict — one record per iteration, shaped as the schema's ``output`` block.
        """
        self._init_generators()

        if self._profile in ("banking", "all"):
            yield from self._generate_banking(count)
        elif self._profile == "ride_share":
            yield from self._generate_rides(count)

    def generate_list(self, count: int = 100) -> list[Dict[str, Any]]:
        """Convenience method — returns all records as a list (loads into memory)."""
        return list(self.generate(count))

    # ------------------------------------------------------------------
    # Private — generator boot
    # ------------------------------------------------------------------

    def _init_generators(self) -> None:
        """Lazily initialise the concrete generators."""
        if self._customer_gen is not None:
            return  # already initialised

        seed = self._seed

        from ..generators.customer import CustomerGenerator
        from ..generators.device import DeviceGenerator
        from ..generators.transaction import TransactionGenerator

        self._customer_gen = CustomerGenerator(seed=seed)
        self._device_gen = DeviceGenerator(seed=seed)
        self._tx_gen = TransactionGenerator(fraud_rate=self._fraud_rate, seed=seed)

        if self._profile in ("ride_share", "all"):
            from ..generators.driver import DriverGenerator
            from ..generators.ride import RideGenerator
            self._driver_gen = DriverGenerator(seed=seed)
            self._ride_gen = RideGenerator(fraud_rate=self._fraud_rate, seed=seed)

    # ------------------------------------------------------------------
    # Private — banking generation loop
    # ------------------------------------------------------------------

    def _generate_banking(self, count: int) -> Iterator[Dict[str, Any]]:
        import random as _random
        from datetime import datetime, timedelta

        # Pre-generate a pool of customers and devices (1 customer : ~10 tx)
        pool_size = max(10, count // 10)

        customers: list[dict] = []
        devices: list[dict] = []

        for i in range(pool_size):
            cid = f"CUST_{i:09d}"
            c_data = self._customer_gen.generate(cid)
            customers.append(c_data)

            did = f"DEV_{i:09d}"
            d_data = self._device_gen.generate(did, cid)
            devices.append(d_data)

        # Date range: last 365 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        total_seconds = int((end_date - start_date).total_seconds())

        for _ in range(count):
            customer = _random.choice(customers)
            device = _random.choice(devices)

            cid = customer.get("customer_id", "CUST_000000000")
            did = device.get("device_id", "DEV_000000000")
            profile = customer.get("behavioral_profile")
            state = customer.get("address", {}).get("state")

            ts = start_date + timedelta(seconds=_random.randint(0, total_seconds))

            tx_data = self._tx_gen.generate(
                tx_id=str(uuid.uuid4()),
                customer_id=cid,
                device_id=did,
                timestamp=ts,
                customer_state=state,
                customer_profile=profile,
            )

            # Flatten customer.address into direct fields for mapper access
            enriched_customer = _flatten_address(customer)

            record = self._mapper.resolve(
                self._output_template,
                transaction=_to_obj(tx_data),
                customer=_to_obj(enriched_customer),
                device=_to_obj(device),
            )
            yield record

    # ------------------------------------------------------------------
    # Private — ride-share generation loop
    # ------------------------------------------------------------------

    def _generate_rides(self, count: int) -> Iterator[Dict[str, Any]]:
        import random as _random
        from datetime import datetime, timedelta

        pool = max(10, count // 5)

        customers: list[dict] = []
        drivers: list[dict] = []

        for i in range(pool):
            cid = f"CUST_{i:09d}"
            c = self._customer_gen.generate(cid)
            customers.append(c)

            drv_id = f"DRV_{i:09d}"
            d = self._driver_gen.generate(drv_id)
            drivers.append(d)

        start_date = datetime(2024, 1, 1)
        total_seconds = int(timedelta(days=365).total_seconds())

        for _ in range(count):
            customer = _random.choice(customers)
            driver = _random.choice(drivers)

            cid = customer.get("customer_id", "CUST_000000000")
            drv_id = driver.get("driver_id", "DRV_000000000")

            # Extract passenger state from nested address dict
            address = customer.get("address", {})
            if isinstance(address, dict):
                passenger_state = address.get("state", "SP")
            else:
                passenger_state = getattr(address, "state", "SP") or "SP"

            passenger_profile = customer.get("behavioral_profile", None)
            ts = start_date + timedelta(seconds=_random.randint(0, total_seconds))

            # RideGenerator.generate(ride_id, driver_id, passenger_id, timestamp, passenger_state, ...)
            ride_data = self._ride_gen.generate(
                ride_id=str(uuid.uuid4()),
                driver_id=drv_id,
                passenger_id=cid,
                timestamp=ts,
                passenger_state=passenger_state,
                passenger_profile=passenger_profile,
            )

            enriched_customer = _flatten_address(customer)

            record = self._mapper.resolve(
                self._output_template,
                customer=_to_obj(enriched_customer),
                driver=_to_obj(driver),
                ride=_to_obj(ride_data),
            )
            yield record

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_id(obj: Any, field: str, default: str) -> str:
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)

    def summary(self) -> str:
        """Return a human-readable summary of the loaded schema."""
        parser = SchemaParser()
        return parser.summarize(self._schema)


# ---------------------------------------------------------------------------
# Internal helper: convert dict ↔ attribute-access object transparently
# ---------------------------------------------------------------------------

class _DictWrapper:
    """Wraps a plain dict so attribute access works (obj.field)."""
    def __init__(self, data: dict):
        self.__dict__.update(data)

    def __getattr__(self, name: str):
        return None  # unknown fields return None gracefully


def _to_obj(data: Any) -> Any:
    """If data is a plain dict, wrap it; otherwise return as-is."""
    if isinstance(data, dict):
        return _DictWrapper(data)
    return data


def _flatten_address(customer: dict) -> dict:
    """
    Make address sub-fields directly accessible on the customer dict.

    Converts:
        customer["address"]["city"]  →  customer["address.city"]

    so that mapper reference "customer.address.city" resolves correctly
    via nested attribute lookup on _DictWrapper.
    """
    result = dict(customer)
    address = customer.get("address", {})
    if isinstance(address, dict):
        # Keep original nested dict AND expose as address_obj with attrs
        result["address"] = _DictWrapper(address)
    return result
