"""
Pipeline factory — builds and returns the default enricher chain.

The canonical pipeline order is:
  1. TemporalEnricher   — unusual_time flag
  2. GeoEnricher        — lat/lon (before fraud can override)
  3. FraudEnricher      — pattern overrides (amount, location, device, channel)
  4. PIXEnricher        — BACEN pacs.008 fields
  5. DeviceEnricher     — device-level signals
  6. SessionEnricher    — velocity, merchant novelty, impossible-travel
  7. RiskEnricher       — score pipeline, ring assignment, TPRD2 fields
  8. BiometricEnricher  — biometric fields (null OS, real Paid)

Order rationale:
- Temporal before Fraud so FraudEnricher can read the hour when applying
  time_anomaly overrides.
- Geo before Fraud so FraudEnricher can override with HIGH/MEDIUM anomaly.
- PIX after Fraud so the type='PIX' upgrade from channel_preference is visible.
- Session after DeviceEnricher so device_new_for_customer sees the final device_id.
- Risk last before Biometric because it needs all other fields settled.
"""

from typing import List

from .base import EnricherProtocol
from .temporal import TemporalEnricher
from .geo import GeoEnricher
from .fraud import FraudEnricher
from .pix import PIXEnricher
from .device import DeviceEnricher
from .session import SessionEnricher
from .risk import RiskEnricher
from .biometric import BiometricEnricher


def get_default_pipeline() -> List[EnricherProtocol]:
    """Return a fresh list of enricher instances in the correct execution order."""
    return [
        TemporalEnricher(),
        GeoEnricher(),
        FraudEnricher(),
        PIXEnricher(),
        DeviceEnricher(),
        SessionEnricher(),
        RiskEnricher(),
        BiometricEnricher(),
    ]
