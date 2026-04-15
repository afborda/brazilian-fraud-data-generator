"""
Risk enricher — fills the fraud_risk_score and supporting risk indicators.

Extracted from TransactionGenerator._add_risk_indicators (risk/score block):
- status, refusal_reason, fraud_score, is_fraud, fraud_type
- sim_swap_recent, ip_location_matches_account, hours_inactive, new_merchant
- fraud_risk_score, fraud_signals (17-signal pipeline)
- T6: fraud_ring_id, ring_role, recipient_is_mule
- TPRD2: active_call_during_tx, network_type, language_locale
"""

from typing import Any, Dict

from .base import EnricherProtocol, GeneratorBag, is_plan
from ..config.transactions import REFUSAL_REASONS
from ..generators.session_context import build_context_for_fraud
from ..generators.correlations import match_fraud_rule
from ..generators.score import compute_fraud_risk_score, score_breakdown


class RiskEnricher:
    """Fills status, fraud_risk_score, signals, ring fields and TPRD2 fields."""

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        buf = bag.buf
        is_fraud = bag.is_fraud
        fraud_type = bag.fraud_type

        # ── Status & base fraud_score ─────────────────────────────────────
        if not tx.get("status"):
            if is_fraud:
                status = buf.next_weighted(
                    "status_fraud",
                    ["APPROVED", "DECLINED", "PENDING", "BLOCKED"],
                    [60, 25, 10, 5],
                )
                # fraud_score com ruído pesado: usa base do FraudEnricher + N(0,25)
                # para que distribuições fraud/legit se sobreponham fortemente,
                # evitando que o score seja feature discriminadora perfeita.
                raw = tx.get("fraud_score")
                if raw is None:
                    raw = int(buf.next_uniform(25, 75))
                noise = int(buf.next_gauss(0, 25))
                fraud_score = max(0, min(100, raw + noise))
            else:
                status = buf.next_weighted(
                    "status_normal",
                    ["APPROVED", "DECLINED", "PENDING"],
                    [96, 3, 1],
                )
                # Distribuição legítima com sobreposição significativa:
                # 70%: score baixo (0-35)
                # 20%: borderline (35-60) — falsos positivos realistas
                #  8%: alto risco legítimo (60-80) — compra incomum, viagem
                #  2%: muito alto (80-95) — atividade atípica mas legítima
                r = buf.next_float()
                if r < 0.70:
                    fraud_score = int(buf.next_uniform(0, 35))
                elif r < 0.90:
                    fraud_score = int(buf.next_uniform(35, 60))
                elif r < 0.98:
                    fraud_score = int(buf.next_uniform(60, 80))
                else:
                    fraud_score = int(buf.next_uniform(80, 95))

            tx["status"] = status
            tx["fraud_score"] = fraud_score

        tx.setdefault("refusal_reason",
            buf.next_choice(REFUSAL_REASONS) if tx.get("status") == "DECLINED" else None
        )
        tx["is_fraud"] = is_fraud
        tx["fraud_type"] = fraud_type

        # ── sim_swap_recent ───────────────────────────────────────────────
        if tx.get("sim_swap_recent") is None:
            if is_fraud and fraud_type in ("CONTA_TOMADA", "SIM_SWAP", "ATO"):
                tx["sim_swap_recent"] = buf.next_float() < 0.65
            elif is_fraud:
                tx["sim_swap_recent"] = buf.next_float() < 0.10
            else:
                tx["sim_swap_recent"] = buf.next_float() < 0.01

        # ── ip_location_matches_account ───────────────────────────────────
        if tx.get("ip_location_matches_account") is None:
            tx["ip_location_matches_account"] = buf.next_float() < (0.35 if is_fraud else 0.94)

        # ── hours_inactive (coarse proxy for time_since_last_txn_min) ─────
        _tslt = tx.get("time_since_last_txn_min")
        tx["hours_inactive"] = int(_tslt / 60) if _tslt is not None else 0

        # ── new_merchant mirrors new_beneficiary ──────────────────────────
        if tx.get("new_merchant") is None:
            tx["new_merchant"] = tx.get("new_beneficiary")

        # ── 17-signal fraud_risk_score pipeline ──────────────────────────
        ctx = build_context_for_fraud(tx, is_fraud, fraud_type, rng=buf._rng)
        match_fraud_rule(ctx)
        tx["fraud_risk_score"] = compute_fraud_risk_score(ctx)

        breakdown = score_breakdown(ctx)
        tx["fraud_signals"] = [
            sig for sig, val in breakdown.items() if sig != "total" and val > 0
        ] or None

        # ── TPRD2: active_call_during_tx ─────────────────────────────────
        tx["active_call_during_tx"] = ctx.active_call

        # ── TPRD2: network_type ───────────────────────────────────────────
        _net_vals = ["WIFI", "4G", "5G", "3G", "UNKNOWN"]
        _net_w = [25, 40, 15, 15, 5] if is_fraud else [55, 25, 12, 5, 3]
        tx["network_type"] = buf.next_weighted("network_type", _net_vals, _net_w)

        # ── TPRD2: language_locale ────────────────────────────────────────
        if is_fraud and fraud_type in ("CONTA_TOMADA", "PIRÂMIDE_FINANCEIRA"):
            _loc_vals = ["pt-BR", "en-US", "es-ES", "zh-CN", "ru-RU"]
            _loc_w    = [50, 25, 10, 10, 5]
        else:
            _loc_vals = ["pt-BR", "pt-PT", "en-US", "es-ES"]
            _loc_w    = [92, 3, 3, 2]
        tx["language_locale"] = buf.next_weighted("language_locale", _loc_vals, _loc_w)

        # ── T6: Fraud ring assignment ─────────────────────────────────────
        ring_registry = bag.ring_registry
        if ring_registry is not None:
            ring_id, ring_role = ring_registry.get_or_assign(
                tx.get("customer_id", ""),
                is_fraud,
                fraud_type,
                buf._rng,
            )
        else:
            ring_id, ring_role = None, None

        tx["fraud_ring_id"] = ring_id
        tx["ring_role"] = ring_role
        tx["recipient_is_mule"] = (
            ring_role in ("orchestrator", "recruiter")
            and tx.get("type") in ("PIX", "TED")
            and is_fraud
        ) if ring_id else False

        # ── Team+: enhanced mule graph structure ──────────────────────────
        is_team_plus = is_plan(bag.license, "team", "enterprise")
        if is_team_plus and ring_id and ring_role:
            # Mule tier: direct (1) or layered (2) — mulas may have sub-mulas
            if ring_role == "mule":
                tx["mule_tier"] = buf.next_weighted(
                    "mule_tier", [1, 2], [75, 25]
                )
            else:
                tx["mule_tier"] = None
            # Forward ratio: mulas keep 5-30% and forward the rest
            if ring_role == "mule":
                kept_pct = round(buf.next_uniform(0.05, 0.30), 3)
                tx["mule_forward_ratio"] = round(1.0 - kept_pct, 3)
            elif ring_role == "orchestrator":
                tx["mule_forward_ratio"] = 0.0   # retains all
            else:
                tx["mule_forward_ratio"] = None
            # Network size estimate (how many accounts in this ring)
            tx["mule_network_size"] = buf.next_int(4, 18)
        else:
            tx.setdefault("mule_tier", None)
            tx.setdefault("mule_forward_ratio", None)
            tx.setdefault("mule_network_size", None)
