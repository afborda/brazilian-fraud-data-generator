"""
Session enricher — fills velocity, merchant novelty, and travel fields
from `CustomerSessionState`.

Extracted from TransactionGenerator._add_risk_indicators (session_state block).

Note: `is_impossible_travel` and `distance_from_last_km` are intentionally NOT
set here — those come from `session.check_impossible_travel()` which the caller
(tx_worker / batch_gen) invokes *after* generate() returns, and then sets the
fields directly on the tx dict.  The enricher only fills the fields that the
existing `generate()` method already fills.

Pro+ extended velocity windows (1h/6h/7d/30d) and geo clustering fields are
gated behind the license plan check.
"""

from typing import Any, Dict

from .base import EnricherProtocol, GeneratorBag, is_plan

# Profile velocity baselines (mean txns/24h, std)
_PROFILE_VELOCITY_BASELINE: dict = {
    "high_spender":         (15, 5.0),
    "business_owner":       (20, 7.0),
    "subscription_heavy":   (8,  3.0),
    "young_digital":        (10, 4.0),
    "traditional_senior":   (5,  2.0),
    "family_provider":      (7,  2.5),
    "ato_victim":           (8,  3.5),
    "falsa_central_victim": (6,  2.5),
    "malware_ats_victim":   (9,  3.5),
}
_PROFILE_VELOCITY_DEFAULT = (8, 3.0)

# Extended velocity window fields (Pro+) — set to None for lower plans
_VELOCITY_WINDOW_FIELDS = (
    "velocity_transactions_1h",
    "velocity_transactions_6h",
    "velocity_transactions_7d",
    "velocity_transactions_30d",
    "accumulated_amount_1h",
    "accumulated_amount_6h",
    "accumulated_amount_7d",
    "accumulated_amount_30d",
    "velocity_unique_merchants_7d",
    "velocity_unique_devices_7d",
)

# Geo clustering fields (Pro+) — set to None for lower plans
_GEO_CLUSTER_FIELDS = (
    "distance_from_home_km",
    "is_known_location",
    "location_cluster_id",
    "first_time_at_this_location",
    "merchant_visit_count",
    "days_since_first_merchant_visit",
    "new_merchant_flag",
)


class SessionEnricher:
    """
    Enriches the transaction with session-state derived fields.

    When `bag.session_state` is available (the standard path in tx_worker):
    - velocity_transactions_24h
    - accumulated_amount_24h
    - new_beneficiary / new_merchant
    - customer_velocity_z_score
    - device_new_for_customer
    - time_since_last_txn_min
    - distance_from_last_txn_km

    Pro+ additional fields (gated by license):
    - velocity_transactions_1h/6h/7d/30d
    - accumulated_amount_1h/6h/7d/30d
    - velocity_unique_merchants_7d, velocity_unique_devices_7d
    - distance_from_home_km, is_known_location, location_cluster_id
    - first_time_at_this_location, merchant_visit_count, new_merchant_flag

    Falls back to random values when session_state is None.
    """

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        buf = bag.buf
        session_state = bag.session_state
        timestamp = bag.timestamp
        customer_profile = bag.customer_profile
        is_fraud = bag.is_fraud
        # V6-M1: velocity windows always enabled (was gated by is_plan Pro+)
        is_pro_plus = True

        if is_fraud:
            default_transactions_24h = buf.next_int(5, 50)
            default_accumulated_amount = round(buf.next_uniform(2000, 50000), 2)
        else:
            default_transactions_24h = buf.next_int(1, 15)
            default_accumulated_amount = round(buf.next_uniform(50, 5000), 2)

        if session_state:
            if tx.get("velocity_transactions_24h") is None:
                tx["velocity_transactions_24h"] = session_state.get_velocity(timestamp) + 1
            if tx.get("accumulated_amount_24h") is None:
                tx["accumulated_amount_24h"] = round(
                    session_state.get_accumulated_24h(timestamp) + float(tx.get("amount", 0.0)),
                    2,
                )
            if tx.get("new_beneficiary") is None:
                tx["new_beneficiary"] = session_state.is_new_merchant(tx.get("merchant_id"))

            # T4: velocity z-score
            current_v = tx.get("velocity_transactions_24h") or 0
            v_mean, v_std = _PROFILE_VELOCITY_BASELINE.get(
                customer_profile, _PROFILE_VELOCITY_DEFAULT
            )
            tx["customer_velocity_z_score"] = round((current_v - v_mean) / max(v_std, 0.1), 2)

            # T4: device novelty
            if tx.get("device_new_for_customer") is None:
                tx["device_new_for_customer"] = session_state.is_new_device(tx.get("device_id"))

            if tx.get("time_since_last_txn_min") is None:
                tx["time_since_last_txn_min"] = session_state.get_last_transaction_minutes_ago(timestamp)

            if tx.get("distance_from_last_txn_km") is None:
                tx["distance_from_last_txn_km"] = session_state.get_distance_from_last_txn_km(
                    tx.get("geolocation_lat"),
                    tx.get("geolocation_lon"),
                )

            # ── Pro+: extended velocity windows ───────────────────────────
            if is_pro_plus:
                tx.setdefault("velocity_transactions_1h",
                    session_state.get_velocity_window(timestamp, 1))
                tx.setdefault("velocity_transactions_6h",
                    session_state.get_velocity_window(timestamp, 6))
                tx.setdefault("velocity_transactions_7d",
                    session_state.get_velocity_window(timestamp, 168))
                tx.setdefault("velocity_transactions_30d",
                    session_state.get_velocity_window(timestamp, 720))
                tx.setdefault("accumulated_amount_1h",
                    session_state.get_accumulated_window(timestamp, 1))
                tx.setdefault("accumulated_amount_6h",
                    session_state.get_accumulated_window(timestamp, 6))
                tx.setdefault("accumulated_amount_7d",
                    session_state.get_accumulated_window(timestamp, 168))
                tx.setdefault("accumulated_amount_30d",
                    session_state.get_accumulated_window(timestamp, 720))
                tx.setdefault("velocity_unique_merchants_7d",
                    session_state.get_unique_merchants_window(timestamp, 168))
                tx.setdefault("velocity_unique_devices_7d",
                    session_state.get_unique_devices_window(timestamp, 168))
            else:
                for f in _VELOCITY_WINDOW_FIELDS:
                    tx.setdefault(f, None)

        else:
            if tx.get("distance_from_last_txn_km") is None:
                tx["distance_from_last_txn_km"] = (
                    round(buf.next_uniform(0, 100), 2) if buf.next_float() > 0.5 else None
                )
            if tx.get("time_since_last_txn_min") is None:
                tx["time_since_last_txn_min"] = (
                    buf.next_int(1, 1440) if buf.next_float() > 0.3 else None
                )
            if tx.get("velocity_transactions_24h") is None:
                tx["velocity_transactions_24h"] = default_transactions_24h
            if tx.get("accumulated_amount_24h") is None:
                tx["accumulated_amount_24h"] = default_accumulated_amount
            if tx.get("new_beneficiary") is None:
                tx["new_beneficiary"] = buf.next_float() < (0.45 if is_fraud else 0.20)
            # No session state — all extended fields null
            for f in _VELOCITY_WINDOW_FIELDS:
                tx.setdefault(f, None)

