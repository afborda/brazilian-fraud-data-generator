"""
Fraud enricher — applies fraud-pattern-specific characteristics to a transaction.

Extracted from TransactionGenerator._apply_fraud_pattern.
Only runs when bag.is_fraud is True and bag.fraud_type is set.
"""

import random
import hashlib as _hl
import uuid as _uuid
from datetime import timedelta as _td
from typing import Any, Dict, Optional

from .base import EnricherProtocol, GeneratorBag, is_plan
from ..config.merchants import get_mcc_info
from ..config.geography import ESTADOS_BR, ESTADOS_LIST
from ..config.fraud_patterns import get_fraud_pattern, get_time_window_for_anomaly
from ..config.pix import (
    MODALIDADE_INICIACAO_LIST, MODALIDADE_INICIACAO_WEIGHTS,
    TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS,
    HOLDER_TYPE_LIST, HOLDER_TYPE_WEIGHTS,
    generate_end_to_end_id,
)
from ..utils.helpers import generate_random_hash
from ..profiles.behavioral import get_transaction_value_for_profile

# ── V6-M13: Demographic age multiplier (Artigo Fraudes Transacionais 2026) ──
# Ticket médio fraude: 18-24 R$964, 30-49 R$2.540, 60+ R$4.820
# Normalized to baseline 1.0 at 30-49 range
_PROFILE_AGE_GROUP: dict = {
    "young_digital":        "18-29",
    "subscription_heavy":   "22-45",
    "malware_ats_victim":   "18-45",
    "family_provider":      "30-55",
    "business_owner":       "30-55",
    "high_spender":         "30-60",
    "micro_empreendedor":   "25-55",
    "ato_victim":           "35-65",
    "traditional_senior":   "55-80",
    "falsa_central_victim": "55-85",
}

_AGE_GROUP_MULTIPLIER: dict = {
    "18-29": 0.38,   # R$964 / R$2.540
    "22-45": 0.70,   # blended
    "18-45": 0.65,   # blended
    "30-55": 1.0,    # baseline
    "30-60": 1.1,    # slightly above
    "25-55": 0.90,   # slightly below
    "35-65": 1.3,    # older skew
    "55-80": 1.90,   # R$4.820 / R$2.540
    "55-85": 1.90,   # seniors
}

# ── Fraud types that may produce impossible travel events (Pro+) ──────────────
_IMPOSSIBLE_TRAVEL_TYPES = frozenset({
    "CONTA_TOMADA", "SIM_SWAP", "MAO_FANTASMA", "CREDENTIAL_STUFFING",
    "CARTAO_CLONADO", "FRAUDE_APLICATIVO",
})

# ── Multi-label taxonomy: maps fraud_type → list of labels ───────────────────
_FRAUD_LABELS: dict = {
    "CONTA_TOMADA":          ["ATO", "CONTA_TOMADA"],
    "ENGENHARIA_SOCIAL":     ["ENGENHARIA_SOCIAL"],
    "PIX_GOLPE":             ["PIX_GOLPE", "ENGENHARIA_SOCIAL"],
    "CARTAO_CLONADO":        ["CARTAO_CLONADO"],
    "MULA_FINANCEIRA":       ["MULA_FINANCEIRA", "LAVAGEM_DINHEIRO"],
    "FRAUDE_APLICATIVO":     ["FRAUDE_APLICATIVO", "ATO"],
    "CARD_TESTING":          ["CARD_TESTING"],
    "COMPRA_TESTE":          ["CARD_TESTING"],
    "MICRO_BURST_VELOCITY":  ["MICRO_BURST_VELOCITY", "BOT"],
    "DISTRIBUTED_VELOCITY":  ["DISTRIBUTED_VELOCITY", "BOT"],
    "BOLETO_FALSO":          ["BOLETO_FALSO"],
    "MAO_FANTASMA":          ["RAT_FRAUD", "ATO", "MAO_FANTASMA"],
    "WHATSAPP_CLONE":        ["ENGENHARIA_SOCIAL", "WHATSAPP_CLONE", "IMPERSONATION"],
    "SIM_SWAP":              ["SIM_SWAP", "ATO"],
    "CREDENTIAL_STUFFING":   ["CREDENTIAL_STUFFING", "BOT", "ATO"],
    "SYNTHETIC_IDENTITY":    ["SYNTHETIC_IDENTITY", "IDENTITY_FRAUD"],
    "SEQUESTRO_RELAMPAGO":   ["SEQUESTRO_RELAMPAGO", "ENGENHARIA_SOCIAL"],
    # ── Novos tipos (pipeline RAG + notebooks) ────────────────────────
    "FALSA_CENTRAL_TELEFONICA": ["FALSA_CENTRAL", "ENGENHARIA_SOCIAL", "IMPERSONATION"],
    "PIX_AGENDADO_FRAUDE":   ["PIX_GOLPE", "ATO"],
    "FRAUDE_DELIVERY_APP":   ["CARTAO_CLONADO", "CARD_TESTING"],
    "EMPRESTIMO_FRAUDULENTO": ["IDENTITY_FRAUD", "SYNTHETIC_IDENTITY"],
    "DEEP_FAKE_BIOMETRIA":   ["IDENTITY_FRAUD", "DEEP_FAKE", "ATO"],
    "GOLPE_INVESTIMENTO":    ["ENGENHARIA_SOCIAL", "PIRAMIDE"],
    "FRAUDE_QR_CODE":        ["PIX_GOLPE", "ENGENHARIA_SOCIAL"],
    "PHISHING_BANCARIO":     ["PHISHING", "ATO", "CREDENTIAL_STUFFING"],
}

# ── Chain roles: position in the fraud chain ──────────────────────────────────
_FRAUD_CHAIN_ROLES: dict = {
    "MULA_FINANCEIRA":      "LAUNDERING",
    "DISTRIBUTED_VELOCITY": "TRANSFER",
    "MICRO_BURST_VELOCITY": "TRANSFER",
}
# All others default to "INITIATION"

# ── Detection latency ranges (days) if not in pattern config ─────────────────
_FRAUD_DETECTION_DELAY: dict = {
    "BOLETO_FALSO":        (2, 7),
    "CARTAO_CLONADO":      (1, 5),
    "CONTA_TOMADA":        (1, 3),
    "MULA_FINANCEIRA":     (7, 30),
    "ENGENHARIA_SOCIAL":   (1, 14),
    "PIX_GOLPE":           (1, 3),
    "SYNTHETIC_IDENTITY":  (30, 90),
    "WHATSAPP_CLONE":      (1, 7),
    "SEQUESTRO_RELAMPAGO": (1, 3),
    "SIM_SWAP":            (1, 5),
    "CREDENTIAL_STUFFING": (0, 2),
    "MAO_FANTASMA":        (1, 3),
    # ── Novos tipos ───────────────────────────────────────────────────
    "FALSA_CENTRAL_TELEFONICA": (1, 7),
    "PIX_AGENDADO_FRAUDE":     (1, 3),
    "FRAUDE_DELIVERY_APP":     (1, 5),
    "EMPRESTIMO_FRAUDULENTO":  (7, 30),
    "DEEP_FAKE_BIOMETRIA":     (3, 14),
    "GOLPE_INVESTIMENTO":      (14, 60),
    "FRAUDE_QR_CODE":          (1, 3),
    "PHISHING_BANCARIO":       (1, 5),
}

# ── Bot signature profiles ────────────────────────────────────────────────────
# Full-automation bots: toolkit or scripted injection
_BOT_FRAUD_TYPES_HIGH = frozenset({
    "MICRO_BURST_VELOCITY", "DISTRIBUTED_VELOCITY", "CREDENTIAL_STUFFING",
})
_BOT_FRAUD_TYPES_MED = frozenset({
    "CARD_TESTING", "COMPRA_TESTE",
})
# RAT/remote-access: scripted but victim device, partially human-looking
_RAT_FRAUD_TYPES = frozenset({
    "MAO_FANTASMA",
})
# Social-engineering: human victim operates own device → very low bot score
_SOCIAL_FRAUD_TYPES = frozenset({
    "ENGENHARIA_SOCIAL", "PIX_GOLPE", "FALSA_CENTRAL_TELEFONICA",
    "WHATSAPP_CLONE", "GOLPE_INVESTIMENTO", "EMPRESTIMO_FRAUDULENTO",
    "BOLETO_FALSO", "FRAUDE_QR_CODE", "FRAUDE_DELIVERY_APP",
    "SEQUESTRO_RELAMPAGO",
})
# ATO: attacker operates stolen session — moderate bot-like navigation speed
_ATO_FRAUD_TYPES = frozenset({
    "CONTA_TOMADA", "CARTAO_CLONADO", "FRAUDE_APLICATIVO", "SIM_SWAP",
    "PHISHING_BANCARIO", "DEEP_FAKE_BIOMETRIA", "SYNTHETIC_IDENTITY",
    "PIX_AGENDADO_FRAUDE",
})


def _get_bot_signature(fraud_type: str, buf) -> tuple:
    """Return (automation_signature: str, bot_confidence_score: float).

    Score calibration (RAG fraudflow + Febraban 2024):
      - Full-bot toolkit:   0.85-0.99
      - Card testing bots:  0.60-0.85
      - RAT (mão fantasma): 0.55-0.75  (partial automation on victim device)
      - ATO attacker:       0.15-0.40  (human but fast/anomalous)
      - Social engineering: 0.01-0.08  (real victim, human behaviour)
    """
    if fraud_type in _BOT_FRAUD_TYPES_HIGH:
        return "BOT_TOOLKIT", round(random.uniform(0.85, 0.99), 3)
    if fraud_type in _BOT_FRAUD_TYPES_MED:
        return "SCRIPTED", round(random.uniform(0.60, 0.85), 3)
    if fraud_type in _RAT_FRAUD_TYPES:
        return "SCRIPTED", round(random.uniform(0.55, 0.75), 3)
    if fraud_type in _ATO_FRAUD_TYPES:
        return "HUMAN", round(random.uniform(0.15, 0.40), 3)
    if fraud_type in _SOCIAL_FRAUD_TYPES:
        return "HUMAN", round(random.uniform(0.01, 0.08), 3)
    # Default: mildly anomalous human-like
    return "HUMAN", round(random.uniform(0.05, 0.25), 3)


# ── Fields that must be null on non-fraud records ────────────────────────────
_NEW_PRO_FIELDS_NULL = (
    "fraud_labels", "fraud_chain_id", "fraud_chain_role",
    "fraud_reported_days_after", "credential_breach_days_before",
    "is_impossible_travel", "min_travel_time_required_hours",
    "actual_gap_hours", "impossible_travel_group_id",
)


class FraudEnricher:
    """
    Applies fraud-specific overrides to amount, location, device, channel,
    MCC, timestamps, and velocity fields.

    Also handles:
    - T3: CARD_TESTING / MICRO_BURST_VELOCITY / DISTRIBUTED_VELOCITY
    - T7: micro-probe (PIX_GOLPE, CARTAO_CLONADO)
    - T7: ENGENHARIA_SOCIAL fixed beneficiaries
    """

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        if not bag.is_fraud or not bag.fraud_type:
            # Ensure probe fields exist on non-fraud records
            tx.setdefault("is_probe_transaction", False)
            tx.setdefault("probe_original_amount", None)
            tx.setdefault("beneficiary_cpf_hash", None)
            for _f in _NEW_PRO_FIELDS_NULL:
                tx.setdefault(_f, None)
            tx.setdefault("automation_signature", "HUMAN")
            tx.setdefault("bot_confidence_score", round(random.uniform(0.0, 0.05), 3))
            # V6-M14: PJ/PF destination defaults for legit transactions
            if random.random() < 0.15:  # 15% PJ in legit (vs 65% fraud)
                tx.setdefault("destination_account_type", "PJ")
                tx.setdefault("destination_company_age_days", random.randint(90, 3650))
                tx.setdefault("destination_account_age_days", random.randint(30, 1825))
            else:
                tx.setdefault("destination_account_type", "PF")
                tx.setdefault("destination_company_age_days", None)
                tx.setdefault("destination_account_age_days", random.randint(30, 3650))
            return

        fraud_type = bag.fraud_type
        customer_profile = bag.customer_profile
        timestamp = bag.timestamp
        buf = bag.buf
        use_profiles = bag.use_profiles

        pattern = get_fraud_pattern(fraud_type)
        characteristics = pattern["characteristics"]

        # ── Value anomaly ─────────────────────────────────────────────────
        if "amount_override" in characteristics:
            lo, hi = characteristics["amount_override"]
            tx["amount"] = round(random.uniform(lo, hi), 2)
        elif "amount_multiplier" in characteristics:
            lo_m, hi_m = characteristics["amount_multiplier"]
            base = (
                get_transaction_value_for_profile(customer_profile)
                if (use_profiles and customer_profile)
                else tx.get("amount", 100.0)
            )
            # V6-M13: modulate by victim age group (demographic factor)
            age_group = _PROFILE_AGE_GROUP.get(customer_profile)
            age_mult = _AGE_GROUP_MULTIPLIER.get(age_group, 1.0) if age_group else 1.0
            tx["amount"] = round(base * random.uniform(lo_m, hi_m) * age_mult, 2)

        # ── New beneficiary ───────────────────────────────────────────────
        new_ben_prob = characteristics.get("new_beneficiary_prob")
        if new_ben_prob is not None and random.random() < new_ben_prob:
            tx["new_beneficiary"] = True
            if tx.get("destination_bank"):
                tx["destination_bank"] = bag.bank_cache.sample()

        # ── Velocity ──────────────────────────────────────────────────────
        velocity = characteristics.get("velocity", "NONE")
        if velocity == "HIGH":
            burst_min, burst_max = characteristics.get("transaction_burst", (10, 30))
            tx["velocity_transactions_24h"] = random.randint(burst_min, burst_max)
            tx["accumulated_amount_24h"] = round(
                tx["amount"] * tx["velocity_transactions_24h"] * random.uniform(0.6, 0.9), 2
            )
        elif velocity == "MEDIUM":
            tx["velocity_transactions_24h"] = random.randint(5, 12)
            tx["accumulated_amount_24h"] = round(
                tx["amount"] * tx["velocity_transactions_24h"] * 0.7, 2
            )
        elif velocity == "LOW":
            # Fraud com velocity LOW ainda deve estar levemente acima da linha de base
            # para não ficar abaixo de clientes legítimos ativos (Bug #5)
            tx["velocity_transactions_24h"] = random.randint(3, 9)
            tx["accumulated_amount_24h"] = round(
                tx["amount"] * tx["velocity_transactions_24h"] * 0.5, 2
            )

        # ── Time anomaly ──────────────────────────────────────────────────
        time_anomaly = characteristics.get("time_anomaly", "NONE")
        if time_anomaly != "NONE":
            valid_hours = get_time_window_for_anomaly(time_anomaly)
            new_hour = random.choice(valid_hours)
            if timestamp is not None:
                new_timestamp = timestamp.replace(hour=new_hour, minute=random.randint(0, 59))
                tx["timestamp"] = new_timestamp.isoformat()
            tx["unusual_time"] = new_hour < 6 or new_hour > 22

        # ── Location anomaly ──────────────────────────────────────────────
        location_anomaly = characteristics.get("location_anomaly", "NONE")
        if location_anomaly == "HIGH":
            current_state = tx.get("customer_state", "SP")
            diff_state = random.choice([s for s in ESTADOS_LIST if s != current_state])
            info = ESTADOS_BR.get(diff_state, ESTADOS_BR["SP"])
            tx["geolocation_lat"] = round(info["lat"] + random.uniform(-0.5, 0.5), 6)
            tx["geolocation_lon"] = round(info["lon"] + random.uniform(-0.5, 0.5), 6)
        elif location_anomaly == "MEDIUM":
            tx["geolocation_lat"] = round((tx.get("geolocation_lat") or -15.0) + random.uniform(-2.0, 2.0), 6)
            tx["geolocation_lon"] = round((tx.get("geolocation_lon") or -47.0) + random.uniform(-2.0, 2.0), 6)
            tx["distance_from_last_txn_km"] = round(random.uniform(50, 200), 2)

        # ── Device anomaly ────────────────────────────────────────────────
        if characteristics.get("device_anomaly", "NONE") == "HIGH":
            tx["device_id"] = f"DEV_FRAUD_{random.randint(100000, 999999):06d}"

        # ── Channel preference (canal real: MOBILE_APP, WEB_BANKING, etc.) ─
        if "channel_preference" in characteristics:
            tx["channel"] = random.choice(characteristics["channel_preference"])

        # ── Type preference (tipo de pagamento: PIX, TED, CREDIT_CARD, etc.) ─
        if "type_preference" in characteristics:
            chosen_type = random.choice(characteristics["type_preference"])
            tx["type"] = chosen_type
            if chosen_type in ("CREDIT_CARD", "DEBIT_CARD"):
                # Garantir campos de cartão quando o tipo é forçado para cartão
                if not tx.get("card_brand"):
                    tx["card_brand"] = bag.brand_cache.sample()
                if not tx.get("card_type"):
                    tx["card_type"] = chosen_type
                tx.setdefault("card_number_hash", generate_random_hash(16))
                # Limpar campos PIX se existirem
                tx["pix_key_type"] = None
                tx["pix_key_destination"] = None
                tx["end_to_end_id"] = None
            elif chosen_type == "PIX":
                pix_key_type = random.choice(characteristics.get("pix_key_type", ["CPF", "PHONE", "EMAIL"]))
                tx["pix_key_type"] = pix_key_type
                tx["pix_key_destination"] = generate_random_hash(32)
                tx["destination_bank"] = bag.bank_cache.sample()
                tx["card_number_hash"] = None
                tx["card_brand"] = None
                tx["card_type"] = None
                # PIX/BACEN stubs — PIXEnricher will fill them properly
                if not tx.get("end_to_end_id"):
                    ispb_pag = buf.next_choice(bag.ispb_list)
                    ispb_rec = buf.next_choice(bag.ispb_list)
                    ts_str = str(tx.get("timestamp", ""))[:14].replace("-","").replace("T","").replace(":","")
                    seq = buf.next_hash16()[:10]
                    tx["end_to_end_id"] = generate_end_to_end_id(ispb_pag, ts_str, seq)
                    tx["ispb_pagador"] = ispb_pag
                    tx["ispb_recebedor"] = ispb_rec
                    tx["tipo_conta_pagador"] = buf.next_weighted("tipo_conta", TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS)
                    tx["tipo_conta_recebedor"] = buf.next_weighted("tipo_conta", TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS)
                    tx["holder_type_recebedor"] = buf.next_weighted("holder", HOLDER_TYPE_LIST, HOLDER_TYPE_WEIGHTS)
                    tx["modalidade_iniciacao"] = buf.next_weighted("modalidade", MODALIDADE_INICIACAO_LIST, MODALIDADE_INICIACAO_WEIGHTS)

        # ── MCC preference ────────────────────────────────────────────────
        if "mcc_preference" in characteristics:
            new_mcc = random.choice(characteristics["mcc_preference"])
            tx["mcc_code"] = new_mcc
            mcc_info = get_mcc_info(new_mcc)
            tx["merchant_category"] = mcc_info["category"]
            tx["mcc_risk_level"] = mcc_info["risk"]
            merchants = (bag.merchants_cache or {}).get(new_mcc, ["Suspicious Merchant"])
            tx["merchant_name"] = random.choice(merchants)

        # ── T3: Card Testing ──────────────────────────────────────────────
        if fraud_type == "CARD_TESTING":
            chars = characteristics
            if random.random() < 0.65:
                lo, hi = chars.get("card_test_phase_1_amount", (0.01, 1.00))
                tx["amount"] = round(random.uniform(lo, hi), 2)
                tx["card_test_phase"] = 1
                burst_min, burst_max = chars.get("transaction_burst", (3, 8))
                tx["velocity_transactions_24h"] = random.randint(burst_min, burst_max)
            else:
                lo, hi = chars.get("card_test_phase_3_amount", (3000.0, 15000.0))
                tx["amount"] = round(random.uniform(lo, hi), 2)
                tx["card_test_phase"] = 3
                tx["velocity_transactions_24h"] = random.randint(1, 2)

        # ── T3: Micro-Burst Velocity ──────────────────────────────────────
        elif fraud_type == "MICRO_BURST_VELOCITY":
            tx["velocity_burst_id"] = str(_uuid.uuid4())
            burst_min, burst_max = characteristics.get("transaction_burst", (10, 50))
            tx["velocity_transactions_24h"] = random.randint(burst_min, burst_max)
            window_min, window_max = characteristics.get("burst_window_minutes", (5, 15))
            window_s = random.randint(window_min, window_max) * 60
            if timestamp is not None:
                burst_ts = timestamp.replace(second=0, microsecond=0) + _td(seconds=random.randint(0, window_s))
                tx["timestamp"] = burst_ts.isoformat()
            tx["accumulated_amount_24h"] = round(
                tx["amount"] * tx["velocity_transactions_24h"] * random.uniform(0.7, 0.9), 2
            )

        # ── T3: Distributed Velocity ──────────────────────────────────────
        elif fraud_type == "DISTRIBUTED_VELOCITY":
            tx["distributed_attack_group"] = str(_uuid.uuid4())
            per_min, per_max = characteristics.get("transactions_per_device", (2, 3))
            tx["velocity_transactions_24h"] = random.randint(per_min, per_max)
            tx["device_id"] = f"DEV_DIST_{random.randint(100000, 999999):06d}"
            tx["ip_address"] = buf.next_ip()

        # ── T7: micro-probe (PIX_GOLPE, CARTAO_CLONADO) ──────────────────
        if fraud_type in ("PIX_GOLPE", "CARTAO_CLONADO") and random.random() < 0.40:
            tx["probe_original_amount"] = tx["amount"]
            tx["amount"] = round(random.uniform(1.0, 5.0), 2)
            tx["is_probe_transaction"] = True
        else:
            tx["is_probe_transaction"] = False
            tx.setdefault("probe_original_amount", None)

        # ── T7: ENGENHARIA_SOCIAL fixed beneficiaries ─────────────────────
        if fraud_type == "ENGENHARIA_SOCIAL":
            seed_bytes = (tx.get("customer_id", "") + fraud_type).encode()
            h = int(_hl.sha256(seed_bytes).hexdigest(), 16)
            beneficiary_idx = h % 3
            tx["beneficiary_cpf_hash"] = _hl.sha256(
                f"BENE_{tx.get('customer_id', '')}_{beneficiary_idx}".encode()
            ).hexdigest()
            # Usa a prob do padrão — não força 100% hardcoded
            if tx.get("new_beneficiary") is None:
                prob = characteristics.get("new_beneficiary_prob", 0.55)
                tx["new_beneficiary"] = random.random() < prob
        else:
            tx.setdefault("beneficiary_cpf_hash", None)

        # ── Fraud score com ruído pesado ─────────────────────────────────
        # Base do padrão + N(0,20) para forte sobreposição com legítimo.
        # RiskEnricher adicionará ruído extra — a soma produz overlap ~60%
        # entre classes, impedindo separação por score sozinho.
        base_score = pattern.get("fraud_score_base", 0.5)
        base_pts = int(base_score * 100)
        noise = int(random.gauss(0, 20))
        tx["fraud_score"] = max(5, min(95, base_pts + noise))

        # ── Pro+: multi-label fraud taxonomy ──────────────────────────────
        is_pro_plus = is_plan(bag.license, "pro", "team", "enterprise")
        if is_pro_plus:
            labels = _FRAUD_LABELS.get(fraud_type, [fraud_type])
            tx.setdefault("fraud_labels", labels)
            tx.setdefault("fraud_chain_id", str(_uuid.uuid4())[:18])
            tx.setdefault("fraud_chain_role", _FRAUD_CHAIN_ROLES.get(fraud_type, "INITIATION"))
            # Detection latency: how many days after fraud occurs until reported
            delay_lo, delay_hi = pattern.get(
                "detection_delay_days",
                _FRAUD_DETECTION_DELAY.get(fraud_type, (2, 14))
            )
            tx.setdefault("fraud_reported_days_after", random.randint(delay_lo, delay_hi))
            # Credential breach window: how long ago credentials were compromised
            breach_range = pattern.get("credential_breach_days_before")
            if breach_range:
                tx.setdefault("credential_breach_days_before", random.randint(*breach_range))
            else:
                tx.setdefault("credential_breach_days_before", None)
        else:
            tx.setdefault("fraud_labels", None)
            tx.setdefault("fraud_chain_id", None)
            tx.setdefault("fraud_chain_role", None)
            tx.setdefault("fraud_reported_days_after", None)
            tx.setdefault("credential_breach_days_before", None)

        # ── Pro+: impossible travel injection ─────────────────────────────
        if is_pro_plus and fraud_type in _IMPOSSIBLE_TRAVEL_TYPES:
            session_state = bag.session_state
            if session_state is not None and timestamp is not None:
                lat = tx.get("geolocation_lat")
                lon = tx.get("geolocation_lon")
                if lat is not None and lon is not None and random.random() < 0.08:
                    is_impossible, dist_km = session_state.check_impossible_travel(
                        lat, lon, timestamp
                    )
                    if is_impossible:
                        elapsed_h = (
                            (session_state.get_last_transaction_minutes_ago(timestamp) or 60)
                            / 60.0
                        )
                        min_travel_h = round(dist_km / 900.0, 2)
                        group_id = str(_uuid.uuid4())[:18]
                        tx["is_impossible_travel"] = True
                        tx.setdefault("min_travel_time_required_hours", min_travel_h)
                        tx.setdefault("actual_gap_hours", round(elapsed_h, 2))
                        tx.setdefault("impossible_travel_group_id", group_id)
                    else:
                        tx.setdefault("is_impossible_travel", False)
                        tx.setdefault("min_travel_time_required_hours", None)
                        tx.setdefault("actual_gap_hours", None)
                        tx.setdefault("impossible_travel_group_id", None)
                else:
                    tx.setdefault("is_impossible_travel", False)
                    tx.setdefault("min_travel_time_required_hours", None)
                    tx.setdefault("actual_gap_hours", None)
                    tx.setdefault("impossible_travel_group_id", None)
            else:
                tx.setdefault("is_impossible_travel", False)
                tx.setdefault("min_travel_time_required_hours", None)
                tx.setdefault("actual_gap_hours", None)
                tx.setdefault("impossible_travel_group_id", None)
        else:
            tx.setdefault("is_impossible_travel", False)
            tx.setdefault("min_travel_time_required_hours", None)
            tx.setdefault("actual_gap_hours", None)
            tx.setdefault("impossible_travel_group_id", None)

        # ── Bot / automation signature ─────────────────────────────────────
        # bot_confidence_score is ALWAYS populated for fraud transactions so
        # ML models can use it as a discriminative feature.
        # automation_signature is restricted to pro+ plans (schema field).
        sig, score = _get_bot_signature(fraud_type, buf)
        if is_pro_plus:
            tx.setdefault("automation_signature", sig)
        else:
            tx.setdefault("automation_signature", None)
        tx.setdefault("bot_confidence_score", score)

        # ── V6-M14: PJ/PF destination (Artigo Fraudes Transacionais 2026)
        # 65% dos golpes finalizam em contas PJ (vs 15% em legítimas)
        if random.random() < 0.65:
            tx["destination_account_type"] = "PJ"
            tx["destination_company_age_days"] = random.randint(1, 90)    # empresa recém-criada
            tx["destination_account_age_days"] = random.randint(1, 30)    # conta nova
        else:
            tx["destination_account_type"] = "PF"
            tx["destination_company_age_days"] = None
            tx["destination_account_age_days"] = random.randint(30, 1825)
