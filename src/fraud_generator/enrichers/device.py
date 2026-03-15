"""
Device enricher — merges device-level fields (emulator_detected, vpn_active,
ip_type, device_age_days) into the transaction record.

In the current architecture device attributes live on the Device model
(devices.jsonl) and are already written to the device record.  This enricher
copies the relevant subset into the transaction so downstream ML features have
them in a single row — avoiding a join.

If the device object is not available (bag.device is None) the fields default
to None so the schema stays stable.
"""

from typing import Any, Dict

from .base import EnricherProtocol, GeneratorBag


class DeviceEnricher:
    """
    Copies device-level signals into the transaction.

    Fields injected (all nullable):
      device_age_days, emulator_detected, vpn_active, ip_type
    """

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        device = getattr(bag, "device", None)

        if device is not None:
            tx.setdefault("device_age_days",     getattr(device, "device_age_days", None))
            tx.setdefault("emulator_detected",   getattr(device, "emulator_detected", None))
            tx.setdefault("vpn_active",          getattr(device, "vpn_active", None))
            tx.setdefault("ip_type",             getattr(device, "ip_type", None))
        else:
            tx.setdefault("device_age_days",   None)
            tx.setdefault("emulator_detected", None)
            tx.setdefault("vpn_active",        None)
            tx.setdefault("ip_type",           None)
