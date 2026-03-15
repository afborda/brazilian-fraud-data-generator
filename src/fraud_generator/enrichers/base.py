"""
Base types for the enricher pipeline.

EnricherProtocol: every enricher must implement `enrich(tx, bag)`.
GeneratorBag: lightweight container that gives enrichers read-only access
              to the shared generator state (caches, RNG buffers, config).
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field


@runtime_checkable
class EnricherProtocol(Protocol):
    """Protocol that all enrichers must satisfy."""

    def enrich(self, tx: Dict[str, Any], bag: "GeneratorBag") -> None:
        """Mutate *tx* in-place to add or override fields."""
        ...


@dataclass
class GeneratorBag:
    """
    Shared generator state passed to every enricher.

    This dataclass replaces the tight coupling between TransactionGenerator
    methods and its instance variables. Enrichers read from `bag` but
    must not write back to it — all mutations go into `tx`.
    """
    # ── Core generation context ───────────────────────────────────────────
    is_fraud:         bool
    fraud_type:       Optional[str]
    customer_profile: Optional[str]
    timestamp: Any = None   # datetime

    # ── Pre-compute buffers (PrecomputeBuffers) ───────────────────────────
    buf: Any = None

    # ── WeightCache objects ───────────────────────────────────────────────
    tx_type_cache:   Any = None
    fraud_type_cache: Any = None
    mcc_cache:       Any = None
    channel_cache:   Any = None
    bank_cache:      Any = None
    estado_cache:    Any = None
    brand_cache:     Any = None
    installment_cache: Any = None
    card_entry_cache:  Any = None
    pix_type_cache:    Any = None
    ispb_list:         Any = None

    # ── Merchant lookup ───────────────────────────────────────────────────
    merchants_cache: Any = None   # dict: mcc_code → list of merchant names

    # ── Fraud patterns ────────────────────────────────────────────────────
    fraud_patterns: Any = None    # dict from config.fraud_patterns

    # ── Flags ─────────────────────────────────────────────────────────────
    use_profiles: bool = True

    # ── Ring registry (T6) ───────────────────────────────────────────────
    ring_registry: Any = None

    # ── Session state (CustomerSessionState | None) ───────────────────────
    session_state: Any = None

    # ── License (optional — gates biometric tier) ─────────────────────────
    license: Any = None           # fraud_generator.licensing.license.License | None
