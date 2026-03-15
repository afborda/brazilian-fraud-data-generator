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

from .base import EnricherProtocol, GeneratorBag
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
            tx["amount"] = round(base * random.uniform(lo_m, hi_m), 2)

        # ── New beneficiary ───────────────────────────────────────────────
        if characteristics.get("new_beneficiary", False):
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

        # ── Channel / PIX preference ──────────────────────────────────────
        if "channel_preference" in characteristics:
            preferred = characteristics["channel_preference"]
            tx["channel"] = random.choice(preferred)
            if "PIX" in preferred and tx["channel"] == "PIX":
                tx["type"] = "PIX"
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
            tx["new_beneficiary"] = True
        else:
            tx.setdefault("beneficiary_cpf_hash", None)

        # ── Fraud score override ──────────────────────────────────────────
        base_score = pattern.get("fraud_score_base", 0.5)
        tx["fraud_score"] = int(random.uniform(base_score * 100, 95))
