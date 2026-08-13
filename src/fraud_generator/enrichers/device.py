"""
Device enricher — merges device-level fields (emulator_detected, vpn_active,
ip_type, device_age_days) into the transaction record.

In the current architecture device attributes live on the Device model
(devices.jsonl) and are already written to the device record.  This enricher
copies the relevant subset into the transaction so downstream ML features have
them in a single row — avoiding a join.

When the device object is not available (bag.device is None), the enricher
generates realistic fallback values based on the fraud context so device
fields are never null in output.
"""

import random
from typing import Any, Dict

from .base import EnricherProtocol, GeneratorBag
from ..utils.overlap import lognormal_days, two_class
from ..config.calibration import rate as _rate


def sample_device_age(is_fraud: bool) -> int:
    """Age in days of the device used, for either class.

    Median around seven months for an ordinary customer with a long tail
    (people keep phones for years), and around two months for fraud — but a
    third of fraud runs on an old, ordinary handset and a small share of
    legitimate traffic comes from a phone bought yesterday.
    """
    return two_class(
        is_fraud,
        legit=lambda: lognormal_days(median=210, sigma=1.15, lo=0, hi=2555),
        fraud=lambda: lognormal_days(median=60, sigma=1.05, lo=0, hi=2555),
        legit_contamination=_rate("device_age.legit_contamination"),
        fraud_contamination=_rate("device_age.fraud_contamination"),
    )


class DeviceEnricher:
    """
    Copies device-level signals into the transaction.

    Fields injected:
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
            # Generate realistic device fields when device object isn't available
            is_fraud = bag.is_fraud
            buf = bag.buf

            if tx.get("device_age_days") is None:
                # Was randint(0, 90) vs randint(30, 730): overlapping only in
                # [30, 90], so `device_age_days < 30` identified fraud with
                # 100.0000% precision and `> 90` identified legit with the same.
                # People replace phones and fraudsters reuse old ones.
                tx["device_age_days"] = sample_device_age(is_fraud)

            if tx.get("emulator_detected") is None:
                if is_fraud:
                    tx["emulator_detected"] = buf.next_float() < 0.08
                else:
                    tx["emulator_detected"] = buf.next_float() < 0.005

            if tx.get("vpn_active") is None:
                if is_fraud:
                    tx["vpn_active"] = buf.next_float() < 0.25
                else:
                    tx["vpn_active"] = buf.next_float() < 0.06

            if tx.get("ip_type") is None:
                if tx.get("vpn_active"):
                    tx["ip_type"] = buf.next_weighted(
                        "ip_type_vpn", ["VPN", "DATACENTER", "TOR"], [70, 25, 5]
                    )
                else:
                    tx["ip_type"] = buf.next_weighted(
                        "ip_type_normal", ["RESIDENTIAL", "DATACENTER"], [94, 6]
                    )
