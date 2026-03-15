"""
Geo enricher — sets geolocation_lat / geolocation_lon on the transaction.

This is a thin wrapper around the existing geolocation logic in
TransactionGenerator._get_geolocation.  It is called *before* FraudEnricher
so that the fraud pattern can override the location when needed.
"""

import random
from typing import Any, Dict, Optional, Tuple

from .base import EnricherProtocol, GeneratorBag
from ..config.geography import ESTADOS_BR


class GeoEnricher:
    """
    Fills geolocation_lat and geolocation_lon.

    Logic:
    - Fraud with HIGH location anomaly (30% chance): random different state.
    - Legitimate (or fraud without anomaly) + location_cluster: cluster-weighted.
    - Fallback: state-level random.

    This enricher only sets the fields when they are not already present,
    so FraudEnricher running *after* it can override with pattern-specific logic.
    """

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        if tx.get("geolocation_lat") is not None and tx.get("geolocation_lon") is not None:
            return  # already set (by a prior enricher or the base builder)

        lat, lon = self._pick_location(bag)
        tx["geolocation_lat"] = lat
        tx["geolocation_lon"] = lon

    def _pick_location(self, bag: GeneratorBag) -> Tuple[float, float]:
        buf = bag.buf
        is_fraud = bag.is_fraud
        customer_state: Optional[str] = getattr(bag, "customer_state", None)
        location_cluster = getattr(bag, "location_cluster", None)
        estado_cache = bag.estado_cache

        # Fraud: HIGH location anomaly → completely different state
        if is_fraud and buf.next_float() < 0.3:
            diff_state = estado_cache.sample()
            info = ESTADOS_BR[diff_state]
            lat = round(info["lat"] + buf.next_uniform(-0.5, 0.5), 6)
            lon = round(info["lon"] + buf.next_uniform(-0.5, 0.5), 6)
            return lat, lon

        # Cluster-based placement (normal path)
        if location_cluster:
            wts = [p[2] for p in location_cluster]
            idx = random.choices(range(len(location_cluster)), weights=wts, k=1)[0]
            lat = round(location_cluster[idx][0] + buf.next_uniform(-0.01, 0.01), 6)
            lon = round(location_cluster[idx][1] + buf.next_uniform(-0.01, 0.01), 6)
            return lat, lon

        # Fallback: state-level
        estado = customer_state if (customer_state and customer_state in ESTADOS_BR) else estado_cache.sample()
        info = ESTADOS_BR[estado]
        lat = round(info["lat"] + buf.next_uniform(-0.5, 0.5), 6)
        lon = round(info["lon"] + buf.next_uniform(-0.5, 0.5), 6)
        return lat, lon
