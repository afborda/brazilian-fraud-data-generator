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



# Probabilidade de a transação sair de outro estado, por tipo de fraude.
# Ver o comentário em _pick_location para o porquê de não ser uniforme.
_GEO_ANOMALY_PROB: dict = {
    # Vítima operando o próprio aparelho, na própria cidade: sem deslocamento.
    "PIX_GOLPE": 0.02,
    "ENGENHARIA_SOCIAL": 0.02,
    "FALSA_CENTRAL_TELEFONICA": 0.02,
    "WHATSAPP_CLONE": 0.03,
    "GOLPE_INVESTIMENTO": 0.03,
    "BOLETO_FALSO": 0.03,
    "FRAUDE_QR_CODE": 0.04,
    "SEQUESTRO_RELAMPAGO": 0.02,
    "EMPRESTIMO_FRAUDULENTO": 0.05,
    # Atacante remoto, mas boa parte usa proxy residencial na cidade da vítima
    # para não disparar a regra de geolocalização.
    "CONTA_TOMADA": 0.22,
    "CREDENTIAL_STUFFING": 0.28,
    "CARTAO_CLONADO": 0.20,
    "FRAUDE_APLICATIVO": 0.18,
    "SIM_SWAP": 0.15,
    "MAO_FANTASMA": 0.06,   # RAT no aparelho da própria vítima
    "PHISHING_BANCARIO": 0.20,
    # Operações distribuídas de propósito.
    "DISTRIBUTED_VELOCITY": 0.40,
    "CARD_TESTING": 0.35,
    "COMPRA_TESTE": 0.35,
    "MULA_FINANCEIRA": 0.12,
}

_GEO_ANOMALY_DEFAULT = 0.10


class GeoEnricher:
    """
    Fills geolocation_lat, geolocation_lon, codigo_ibge_municipio and
    municipio_nome using real IBGE municipality centroids.

    Logic:
    - Fraud with a location anomaly (probability per fraud type — see
      _GEO_ANOMALY_PROB): random different state, municipality selected by
      population weight within that state.
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

        # Anomalia geográfica: só faz sentido quando o atacante opera de outro
        # lugar. Isto valia para 30% de TODA fraude, independente do tipo, e o
        # efeito era grande: `distance_from_last_km` saía com mediana de 15 km
        # no legítimo contra 337 km na fraude — 22× — e virava a feature mais
        # importante do benchmark, com 31,7% da importância.
        #
        # Golpe do PIX, falsa central, WhatsApp clonado e engenharia social em
        # geral têm a VÍTIMA fazendo a transferência, do celular dela, em casa.
        # Não há salto geográfico nenhum. Quem se desloca é ATO, credential
        # stuffing e clonagem de cartão, onde o atacante está de fato noutro
        # lugar — e mesmo aí, boa parte usa proxy residencial na cidade da
        # vítima justamente para não disparar a regra de geolocalização.
        fraud_type = getattr(bag, "fraud_type", None)
        anomaly_prob = _GEO_ANOMALY_PROB.get(fraud_type, _GEO_ANOMALY_DEFAULT)
        if is_fraud and buf.next_float() < anomaly_prob:
            diff_state = estado_cache.sample()
            municipio  = pick_municipio(diff_state, rng)
            lat = round(municipio.lat + buf.next_uniform(-0.05, 0.05), 6)
            lon = round(municipio.lon + buf.next_uniform(-0.05, 0.05), 6)
            return lat, lon, municipio

        # Cluster-based placement (normal path)
        if location_cluster:
            wts = [p[2] for p in location_cluster]
            idx = random.choices(range(len(location_cluster)), weights=wts, k=1)[0]
            lat = round(location_cluster[idx][0] + buf.next_uniform(-0.01, 0.01), 6)
            lon = round(location_cluster[idx][1] + buf.next_uniform(-0.01, 0.01), 6)
            # This branch used to return municipio=None, which had two effects:
            # codigo_ibge_municipio and municipio_nome came out null on 100% of
            # legitimate records, and the only rows carrying them were the 30%
            # of fraud that takes the location-anomaly path above — so
            # `municipio_nome IS NOT NULL` was a fraud marker. Resolving the
            # municipality here fills the schema field for both classes.
            estado_cluster = (
                customer_state
                if (customer_state and customer_state in ESTADOS_BR)
                else estado_cache.sample()
            )
            return lat, lon, pick_municipio(estado_cluster, rng)

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
