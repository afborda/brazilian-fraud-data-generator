"""
Biometric enricher — fills the 10 biometric fields.

OS tier:  all fields are null (the default today).
Paid tier (PRO / ENTERPRISE / TEAM):  fields are populated with realistic
         distributions based on fraud_type and behavioral profile.

The tier gate uses `bag.license` (a License dataclass).  If no license is
present the enricher behaves as OS tier (null fields) — this is the correct
default for the open-source build.

Field list (10):
  typing_speed_avg_ms, typing_rhythm_variance, touch_pressure_avg,
  accelerometer_variance, gyroscope_variance, scroll_before_confirm,
  time_to_confirm_tx_sec, session_duration_sec,
  copy_paste_on_key, navigation_order_anomaly
"""

import random
from typing import Any, Dict, Optional

from .base import EnricherProtocol, GeneratorBag

# Plans that unlock biometric enrichment
_PAID_PLANS = frozenset({"pro", "team", "enterprise"})

_BIOMETRIC_NULL = {
    "typing_speed_avg_ms":      None,
    "typing_rhythm_variance":   None,
    "touch_pressure_avg":       None,
    "accelerometer_variance":   None,
    "gyroscope_variance":       None,
    "scroll_before_confirm":    None,
    "time_to_confirm_tx_sec":   None,
    "session_duration_sec":     None,
    "copy_paste_on_key":        None,
    "navigation_order_anomaly": None,
}


def _is_paid_tier(license_obj: Any) -> bool:
    """Return True when the license grants biometric data."""
    if license_obj is None:
        return False
    plan_value = getattr(getattr(license_obj, "plan", None), "value", None) or str(
        getattr(license_obj, "plan", "")
    ).lower()
    return plan_value in _PAID_PLANS


class BiometricEnricher:
    """
    Fills biometric fields.  Output is null for OS / FREE / STARTER tier.
    Paid tiers (PRO+) receive realistic behavioural biometrics.
    """

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        if not _is_paid_tier(bag.license):
            tx.update(_BIOMETRIC_NULL)
            return

        # ── Paid tier: generate realistic biometrics ──────────────────────
        is_fraud = bag.is_fraud
        fraud_type = bag.fraud_type
        buf = bag.buf
        rng: random.Random = buf._rng

        # Fraudsters tend to act faster, copy-paste more, higher variance
        if is_fraud:
            typing_speed = round(rng.gauss(180, 40), 1)      # ms / keystroke
            typing_var   = round(abs(rng.gauss(0.6, 0.3)), 3)
            touch_pres   = round(rng.gauss(0.3, 0.15), 3)    # normalised 0-1
            accel_var    = round(abs(rng.gauss(1.2, 0.5)), 3)
            gyro_var     = round(abs(rng.gauss(0.9, 0.4)), 3)
            scroll_pre   = bool(rng.random() < 0.25)          # less scrolling
            confirm_sec  = round(rng.gauss(4, 2), 2)          # faster confirm
            session_sec  = round(rng.gauss(90, 45), 1)        # shorter session
            copy_paste   = bool(rng.random() < 0.55)          # higher copy-paste
            nav_anomaly  = bool(rng.random() < 0.45)          # skip screens
        else:
            typing_speed = round(rng.gauss(280, 60), 1)
            typing_var   = round(abs(rng.gauss(0.2, 0.1)), 3)
            touch_pres   = round(rng.gauss(0.55, 0.1), 3)
            accel_var    = round(abs(rng.gauss(0.4, 0.15)), 3)
            gyro_var     = round(abs(rng.gauss(0.3, 0.1)), 3)
            scroll_pre   = bool(rng.random() < 0.78)
            confirm_sec  = round(rng.gauss(12, 4), 2)
            session_sec  = round(rng.gauss(220, 80), 1)
            copy_paste   = bool(rng.random() < 0.08)
            nav_anomaly  = bool(rng.random() < 0.05)

        tx.update({
            "typing_speed_avg_ms":      max(typing_speed, 50.0),
            "typing_rhythm_variance":   min(max(typing_var, 0.0), 1.0),
            "touch_pressure_avg":       min(max(touch_pres, 0.0), 1.0),
            "accelerometer_variance":   max(accel_var, 0.0),
            "gyroscope_variance":       max(gyro_var, 0.0),
            "scroll_before_confirm":    scroll_pre,
            "time_to_confirm_tx_sec":   max(confirm_sec, 0.5),
            "session_duration_sec":     max(session_sec, 5.0),
            "copy_paste_on_key":        copy_paste,
            "navigation_order_anomaly": nav_anomaly,
        })
