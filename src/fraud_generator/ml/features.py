"""
Feature extraction for fraud ML models.

Reads raw transaction dicts and produces a clean DataFrame with exactly
FEATURE_NAMES columns. All missing values are filled with safe defaults
so models never receive NaN.

Design decisions:
- ip_type is ordinally encoded: RESIDENTIAL=0, MOBILE=1, CORPORATE=2,
  HOSTING=3, VPN=4, TOR=5, UNKNOWN=0 (same as residential — conservative)
- Velocity fields default to 0 (no prior transactions observed)
- Biometric fields default to -1 (distinguishable from a genuine zero)
- is_fraud / fraud_type are EXCLUDED (they are targets, not features)
- IDs (transaction_id, customer_id, device_id) are EXCLUDED (high cardinality)
- fraud_signals / fraud_labels are EXCLUDED (direct leakage)
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd

# ── Ordinal encoding for ip_type ─────────────────────────────────────────────
_IP_TYPE_ORD: dict[str, int] = {
    "RESIDENTIAL": 0,
    "MOBILE":      1,
    "CORPORATE":   2,
    "HOSTING":     3,
    "VPN":         4,
    "TOR":         5,
    "UNKNOWN":     0,
}

# ── Feature list (order matters — must match training) ────────────────────────
FEATURE_NAMES: list[str] = [
    # Risk signals (bool → int 0/1)
    "is_emulator",
    "rooted_or_jailbreak",
    "is_vpn",
    "active_call",
    "nav_anomaly",
    "multiple_accounts",
    "new_device",
    "ip_mismatch",
    "sim_swap_recent",
    "notification_ignored",
    "new_beneficiary",
    "unusual_time",
    # Velocity (float, default 0)
    "velocity_transactions_1h",
    "velocity_transactions_6h",
    "velocity_transactions_24h",
    "velocity_transactions_7d",
    "velocity_transactions_30d",
    "accumulated_amount_24h",
    "accumulated_amount_7d",
    # Transaction values
    "amount",
    "fraud_score",
    "fraud_risk_score",
    "bot_confidence_score",
    # Device / account state
    "device_age_days",
    "dest_account_age_days",
    "hours_inactive",
    # Biometric proxies (default -1)
    "touch_pressure",
    "typing_interval_ms",
    "session_duration_s",
    "confirm_latency_s",
    # Encoded categorical
    "ip_type_ord",
]

FEATURE_DTYPES: dict[str, str] = {
    # bools
    "is_emulator":          "int8",
    "rooted_or_jailbreak":  "int8",
    "is_vpn":               "int8",
    "active_call":          "int8",
    "nav_anomaly":          "int8",
    "multiple_accounts":    "int8",
    "new_device":           "int8",
    "ip_mismatch":          "int8",
    "sim_swap_recent":      "int8",
    "notification_ignored": "int8",
    "new_beneficiary":      "int8",
    "unusual_time":         "int8",
    # velocity
    "velocity_transactions_1h":  "float32",
    "velocity_transactions_6h":  "float32",
    "velocity_transactions_24h": "float32",
    "velocity_transactions_7d":  "float32",
    "velocity_transactions_30d": "float32",
    "accumulated_amount_24h":    "float32",
    "accumulated_amount_7d":     "float32",
    # values
    "amount":              "float32",
    "fraud_score":         "float32",
    "fraud_risk_score":    "float32",
    "bot_confidence_score":"float32",
    # device / account
    "device_age_days":     "float32",
    "dest_account_age_days": "float32",
    "hours_inactive":      "float32",
    # biometric
    "touch_pressure":      "float32",
    "typing_interval_ms":  "float32",
    "session_duration_s":  "float32",
    "confirm_latency_s":   "float32",
    # encoded
    "ip_type_ord":         "int8",
}

# Safe defaults when a field is missing/null
_DEFAULTS: dict[str, float] = {
    # bools → 0 (absent signal)
    "is_emulator": 0, "rooted_or_jailbreak": 0, "is_vpn": 0,
    "active_call": 0, "nav_anomaly": 0, "multiple_accounts": 0,
    "new_device": 0, "ip_mismatch": 0, "sim_swap_recent": 0,
    "notification_ignored": 0, "new_beneficiary": 0, "unusual_time": 0,
    # velocity → 0 (no history)
    "velocity_transactions_1h": 0.0, "velocity_transactions_6h": 0.0,
    "velocity_transactions_24h": 0.0, "velocity_transactions_7d": 0.0,
    "velocity_transactions_30d": 0.0, "accumulated_amount_24h": 0.0,
    "accumulated_amount_7d": 0.0,
    # values
    "amount": 0.0, "fraud_score": 50.0, "fraud_risk_score": 0.0,
    "bot_confidence_score": 0.0,
    # device / account
    "device_age_days": 365.0, "dest_account_age_days": 180.0, "hours_inactive": 0.0,
    # biometric → -1 (missing, distinguishable from genuine zero)
    "touch_pressure": -1.0, "typing_interval_ms": -1.0,
    "session_duration_s": -1.0, "confirm_latency_s": -1.0,
    # encoded
    "ip_type_ord": 0,
}


def _extract_one(rec: dict[str, Any]) -> dict[str, float]:
    row: dict[str, float] = {}

    for feat in FEATURE_NAMES:
        if feat == "ip_type_ord":
            raw = rec.get("ip_type") or "UNKNOWN"
            row["ip_type_ord"] = float(_IP_TYPE_ORD.get(str(raw).upper(), 0))
        else:
            val = rec.get(feat)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                row[feat] = _DEFAULTS[feat]
            else:
                try:
                    row[feat] = float(val)
                except (ValueError, TypeError):
                    row[feat] = _DEFAULTS[feat]

    return row


def extract_features(records: Sequence[dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of transaction dicts to a feature DataFrame.

    Returns a DataFrame with exactly len(FEATURE_NAMES) columns in the
    canonical order, with correct dtypes and no NaN values.
    """
    rows = [_extract_one(r) for r in records]
    df = pd.DataFrame(rows, columns=FEATURE_NAMES)

    for col, dtype in FEATURE_DTYPES.items():
        df[col] = df[col].astype(dtype)

    return df
