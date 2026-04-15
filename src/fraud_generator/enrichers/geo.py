"""
Geo enricher — sets geolocation_lat / geolocation_lon on the transaction.

This is a thin wrapper around the existing geolocation logic in
TransactionGenerator._get_geolocation.  It is called *before* FraudEnricher
so that the fraud pattern can override the location when needed.

Fields added here (all tiers):
  geolocation_lat, geolocation_lon, codigo_ibge_municipio, municipio_nome

Pro+ fields added here:
  distance_from_home_km, is_known_location, location_cluster_id,
  first_time_at_this_location
"""

import random
from typing import Any, Dict, Optional, Tuple

from .base import EnricherProtocol, GeneratorBag, is_plan
from ..config.geography import ESTADOS_BR
from ..config.municipios import Municipio, pick_municipio
from ..utils.streaming import haversine_distance

# Cluster slot names — index matches location_cluster tuple order
_CLUSTER_NAMES = ("HOME", "WORK", "SHOPPING", "OTHER", "OCCASIONAL")
# Distance threshold (km) within which a location is considered "known"
_KNOWN_LOCATION_KM = 2.0


class GeoEnricher:
    """
    Fills geolocation_lat, geolocation_lon, codigo_ibge_municipio and
    municipio_nome using real IBGE municipality centroids.

    Logic:
    - Fraud with HIGH location anomaly (30% chance): random different state,
      municipality selected by population weight within that state.
    - Legitimate (or fraud without anomaly) + location_cluster: cluster-weighted.
    - Normal path: municipality centroid (±0.05°) from customer's state.

    Pro+ also fills: distance_from_home_km, is_known_location,
    location_cluster_id, first_time_at_this_location.
    """

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        already_set = (
            tx.get("geolocation_lat") is not None
            and tx.get("geolocation_lon") is not None
        )
        if not already_set:
            lat, lon, municipio = self._pick_location(bag)
            tx["geolocation_lat"]       = lat
            tx["geolocation_lon"]       = lon
            tx["codigo_ibge_municipio"] = municipio.ibge if municipio else None
            tx["municipio_nome"]        = municipio.name if municipio else None
        else:
            lat = tx["geolocation_lat"]
            lon = tx["geolocation_lon"]
            tx.setdefault("codigo_ibge_municipio", None)
            tx.setdefault("municipio_nome",        None)

        # ── Pro+: geo clustering metadata ─────────────────────────────────
        is_pro_plus = is_plan(bag.license, "pro", "team", "enterprise")
        location_cluster = getattr(bag, "location_cluster", None)

        if is_pro_plus and location_cluster:
            self._fill_cluster_metadata(tx, lat, lon, location_cluster)
        else:
            tx.setdefault("distance_from_home_km",      None)
            tx.setdefault("is_known_location",          None)
            tx.setdefault("location_cluster_id",        None)
            tx.setdefault("first_time_at_this_location",None)

    def _pick_location(
        self, bag: GeneratorBag
    ) -> Tuple[float, float, Optional[Municipio]]:
        buf    = bag.buf
        rng: random.Random = buf._rng
        is_fraud     = bag.is_fraud
        customer_state: Optional[str] = getattr(bag, "customer_state", None)
        location_cluster = getattr(bag, "location_cluster", None)
        estado_cache = bag.estado_cache

        # Fraud: HIGH location anomaly → completely different state
        if is_fraud and buf.next_float() < 0.3:
            diff_state = estado_cache.sample()
            municipio  = pick_municipio(diff_state, rng)
            lat = round(municipio.lat + buf.next_uniform(-0.05, 0.05), 6)
            lon = round(municipio.lon + buf.next_uniform(-0.05, 0.05), 6)
            return lat, lon, municipio

        # Cluster-based placement (normal path — no municipio override)
        if location_cluster:
            wts = [p[2] for p in location_cluster]
            idx = random.choices(range(len(location_cluster)), weights=wts, k=1)[0]
            lat = round(location_cluster[idx][0] + buf.next_uniform(-0.01, 0.01), 6)
            lon = round(location_cluster[idx][1] + buf.next_uniform(-0.01, 0.01), 6)
            return lat, lon, None

        # Normal path: use real municipality centroid from customer's state
        estado    = customer_state if (customer_state and customer_state in ESTADOS_BR) else estado_cache.sample()
        municipio = pick_municipio(estado, rng)
        lat = round(municipio.lat + buf.next_uniform(-0.05, 0.05), 6)
        lon = round(municipio.lon + buf.next_uniform(-0.05, 0.05), 6)
        return lat, lon, municipio

    def _fill_cluster_metadata(
        self,
        tx: Dict[str, Any],
        lat: float,
        lon: float,
        location_cluster: tuple,
    ) -> None:
        """Fill Pro+ geo clustering fields on the transaction dict."""
        # Distance from home (index 0)
        home_lat, home_lon, _ = location_cluster[0]
        dist_home = haversine_distance(lat, lon, home_lat, home_lon)
        tx.setdefault("distance_from_home_km", round(dist_home, 2))

        # Find nearest cluster point
        min_dist    = float("inf")
        nearest_idx = 0
        for i, (clat, clon, _) in enumerate(location_cluster):
            d = haversine_distance(lat, lon, clat, clon)
            if d < min_dist:
                min_dist    = d
                nearest_idx = i

        is_known     = min_dist < _KNOWN_LOCATION_KM
        cluster_name = _CLUSTER_NAMES[nearest_idx] if nearest_idx < len(_CLUSTER_NAMES) else "OTHER"

        tx.setdefault("is_known_location",           is_known)
        tx.setdefault("location_cluster_id",         cluster_name if is_known else "UNKNOWN")
        tx.setdefault("first_time_at_this_location", not is_known)
