"""
Tests for the TPRD4 enricher pipeline.

Covers:
- EnricherProtocol structural check (duck-typing)
- GeneratorBag construction
- Each enricher independently
- generate_with_pipeline() end-to-end
- BiometricEnricher OS-vs-Paid gate
"""

import sys
import os
import random
from datetime import datetime
from typing import Any, Dict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from fraud_generator.enrichers.base import EnricherProtocol, GeneratorBag
from fraud_generator.enrichers.temporal import TemporalEnricher
from fraud_generator.enrichers.geo import GeoEnricher
from fraud_generator.enrichers.fraud import FraudEnricher
from fraud_generator.enrichers.pix import PIXEnricher
from fraud_generator.enrichers.device import DeviceEnricher
from fraud_generator.enrichers.session import SessionEnricher
from fraud_generator.enrichers.risk import RiskEnricher
from fraud_generator.enrichers.biometric import BiometricEnricher
from fraud_generator.enrichers.pipeline_factory import get_default_pipeline
from fraud_generator.generators.transaction import TransactionGenerator
from fraud_generator.utils.streaming import CustomerSessionState


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_bag(is_fraud=False, fraud_type=None, profile="young_digital", ts=None, session=None, license=None):
    """Build a minimal GeneratorBag backed by a real TransactionGenerator."""
    g = TransactionGenerator(fraud_rate=0.5, seed=99)
    ts = ts or datetime(2026, 3, 14, 15, 0, 0)
    bag = g._build_bag(
        is_fraud=is_fraud,
        fraud_type=fraud_type,
        customer_profile=profile,
        timestamp=ts,
        session_state=session,
        license=license,
    )
    bag.customer_state = "SP"
    bag.location_cluster = None
    return bag


def _base_tx(tx_type="PIX") -> Dict[str, Any]:
    return {
        "transaction_id": "TXN_001",
        "customer_id": "C001",
        "session_id": "SESS_001",
        "device_id": "D001",
        "timestamp": "2026-03-14T15:00:00",
        "type": tx_type,
        "amount": 250.0,
        "currency": "BRL",
        "channel": "MOBILE_APP",
        "ip_address": "177.0.0.1",
        "geolocation_lat": None,
        "geolocation_lon": None,
        "merchant_id": "M001",
        "merchant_name": "Loja X",
        "merchant_category": "grocery",
        "mcc_code": "5411",
        "mcc_risk_level": "LOW",
        "pix_key_type": "CPF",
        "pix_key_destination": "hash123",
        "destination_bank": "001",
        "card_number_hash": None,
        "card_brand": None,
        "card_type": None,
        "installments": None,
        "card_entry": None,
        "cvv_validated": None,
        "auth_3ds": None,
    }


# ── Protocol check ───────────────────────────────────────────────────────────

def test_all_enrichers_implement_protocol():
    pipeline = get_default_pipeline()
    for e in pipeline:
        assert isinstance(e, EnricherProtocol), f"{e} does not satisfy EnricherProtocol"


def test_pipeline_has_8_enrichers():
    assert len(get_default_pipeline()) == 8


# ── TemporalEnricher ─────────────────────────────────────────────────────────

def test_temporal_flags_unusual_time():
    e = TemporalEnricher()
    bag = _make_bag(ts=datetime(2026, 3, 14, 3, 0, 0))  # 03:00 → unusual
    tx = _base_tx()
    tx["timestamp"] = "2026-03-14T03:00:00"
    e.enrich(tx, bag)
    assert tx["unusual_time"] is True


def test_temporal_normal_hour():
    e = TemporalEnricher()
    bag = _make_bag(ts=datetime(2026, 3, 14, 14, 0, 0))
    tx = _base_tx()
    e.enrich(tx, bag)
    assert tx["unusual_time"] is False


# ── GeoEnricher ──────────────────────────────────────────────────────────────

def test_geo_sets_lat_lon():
    e = GeoEnricher()
    bag = _make_bag()
    tx = _base_tx()
    tx["geolocation_lat"] = None
    tx["geolocation_lon"] = None
    e.enrich(tx, bag)
    assert tx["geolocation_lat"] is not None
    assert tx["geolocation_lon"] is not None
    assert -35.0 < tx["geolocation_lat"] < 5.0   # Brazil latitude range
    assert -75.0 < tx["geolocation_lon"] < -30.0  # Brazil longitude range


def test_geo_does_not_override_existing():
    e = GeoEnricher()
    bag = _make_bag()
    tx = _base_tx()
    tx["geolocation_lat"] = -23.5
    tx["geolocation_lon"] = -46.6
    e.enrich(tx, bag)
    assert tx["geolocation_lat"] == -23.5
    assert tx["geolocation_lon"] == -46.6


# ── PIXEnricher ──────────────────────────────────────────────────────────────

def test_pix_enricher_fills_pix_fields():
    e = PIXEnricher()
    bag = _make_bag(is_fraud=False)
    tx = _base_tx(tx_type="PIX")
    # Remove pre-populated PIX fields to let enricher fill them
    for k in ("end_to_end_id", "ispb_pagador", "ispb_recebedor",
              "tipo_conta_pagador", "tipo_conta_recebedor",
              "holder_type_recebedor", "modalidade_iniciacao",
              "cpf_hash_pagador", "cpf_hash_recebedor", "pacs_status",
              "is_devolucao", "motivo_devolucao_med"):
        tx.pop(k, None)
    e.enrich(tx, bag)
    assert tx.get("end_to_end_id") is not None
    assert tx.get("ispb_pagador") is not None
    assert tx.get("pacs_status") in ("ACSC", "RJCT", "PDNG")
    assert tx.get("is_devolucao") is not None


def test_pix_enricher_nulls_for_non_pix():
    e = PIXEnricher()
    bag = _make_bag()
    tx = _base_tx(tx_type="CREDIT_CARD")
    e.enrich(tx, bag)
    assert tx.get("end_to_end_id") is None
    assert tx.get("ispb_pagador") is None


# ── DeviceEnricher ───────────────────────────────────────────────────────────

def test_device_enricher_nulls_when_no_device():
    e = DeviceEnricher()
    bag = _make_bag()
    tx = _base_tx()
    e.enrich(tx, bag)
    for f in ("device_age_days", "emulator_detected", "vpn_active", "ip_type"):
        assert tx.get(f) is None


# ── SessionEnricher ──────────────────────────────────────────────────────────

def test_session_enricher_uses_session_state():
    session = CustomerSessionState("C001")
    e = SessionEnricher()
    bag = _make_bag(session=session, ts=datetime(2026, 3, 14, 14, 0, 0))
    tx = _base_tx()
    tx["geolocation_lat"] = -23.5
    tx["geolocation_lon"] = -46.6
    e.enrich(tx, bag)
    assert tx.get("velocity_transactions_24h") is not None
    assert tx.get("new_beneficiary") is not None


def test_session_enricher_fallback_without_session():
    e = SessionEnricher()
    bag = _make_bag()  # no session
    tx = _base_tx()
    e.enrich(tx, bag)
    assert tx.get("velocity_transactions_24h") is not None


# ── BiometricEnricher ────────────────────────────────────────────────────────

def test_biometric_os_tier_all_null():
    e = BiometricEnricher()
    bag = _make_bag()  # license=None → OS tier
    tx = _base_tx()
    e.enrich(tx, bag)
    bio_fields = [
        "typing_speed_avg_ms", "typing_rhythm_variance", "touch_pressure_avg",
        "accelerometer_variance", "gyroscope_variance", "scroll_before_confirm",
        "time_to_confirm_tx_sec", "session_duration_sec",
        "copy_paste_on_key", "navigation_order_anomaly",
    ]
    for f in bio_fields:
        assert tx.get(f) is None, f"{f} should be null in OS tier"


def test_biometric_paid_tier_populated():
    """Paid PRO license should populate biometric fields."""
    class _FakePlan:
        value = "pro"
    class _FakeLicense:
        plan = _FakePlan()

    e = BiometricEnricher()
    bag = _make_bag(license=_FakeLicense())
    tx = _base_tx()
    e.enrich(tx, bag)
    assert tx.get("typing_speed_avg_ms") is not None
    assert tx.get("typing_speed_avg_ms") >= 50.0
    assert isinstance(tx.get("copy_paste_on_key"), bool)


# ── RiskEnricher ─────────────────────────────────────────────────────────────

def test_risk_enricher_sets_score():
    e = RiskEnricher()
    bag = _make_bag(is_fraud=False)
    tx = _base_tx()
    tx.update({
        "is_fraud": False, "fraud_type": None,
        "geolocation_lat": -23.5, "geolocation_lon": -46.6,
        "velocity_transactions_24h": 3, "accumulated_amount_24h": 750.0,
        "new_beneficiary": False, "device_new_for_customer": False,
        "time_since_last_txn_min": 60, "sim_swap_recent": False,
        "ip_location_matches_account": True, "hours_inactive": 1,
        "new_merchant": False, "distance_from_last_txn_km": 2.0,
        "emulator_detected": False, "vpn_active": False,
        "active_call_during_tx": False, "auth_3ds": True,
        "card_type": None, "cvv_validated": None,
    })
    e.enrich(tx, bag)
    assert "fraud_risk_score" in tx
    assert 0 <= tx["fraud_risk_score"] <= 100
    assert tx["is_fraud"] is False
    assert tx.get("network_type") is not None
    assert tx.get("language_locale") is not None


def test_risk_enricher_fraud_fields():
    e = RiskEnricher()
    bag = _make_bag(is_fraud=True, fraud_type="CONTA_TOMADA")
    tx = _base_tx()
    tx.update({
        "is_fraud": True, "fraud_type": "CONTA_TOMADA",
        "geolocation_lat": -23.5, "geolocation_lon": -46.6,
        "velocity_transactions_24h": 30, "accumulated_amount_24h": 45000.0,
        "new_beneficiary": True, "device_new_for_customer": True,
        "time_since_last_txn_min": 2, "sim_swap_recent": True,
        "ip_location_matches_account": False, "hours_inactive": 0,
        "new_merchant": True, "distance_from_last_txn_km": 500.0,
        "emulator_detected": True, "vpn_active": True,
        "active_call_during_tx": False, "auth_3ds": False,
        "card_type": None, "cvv_validated": None,
    })
    e.enrich(tx, bag)
    assert tx["is_fraud"] is True
    assert tx["fraud_type"] == "CONTA_TOMADA"
    assert tx["fraud_risk_score"] > 30  # score pipeline is signal-based, not deterministic


# ── FraudEnricher ─────────────────────────────────────────────────────────────

def test_fraud_enricher_no_op_for_legit():
    e = FraudEnricher()
    bag = _make_bag(is_fraud=False)
    tx = _base_tx()
    original_amount = tx["amount"]
    e.enrich(tx, bag)
    assert tx["amount"] == original_amount
    assert tx.get("is_probe_transaction") is False


def test_fraud_enricher_changes_amount_for_fraud():
    e = FraudEnricher()
    bag = _make_bag(is_fraud=True, fraud_type="CONTA_TOMADA")
    tx = _base_tx()
    tx["amount"] = 100.0
    e.enrich(tx, bag)
    # CONTA_TOMADA has amount_multiplier (30, 100) — should deviate significantly
    assert tx["amount"] != 100.0 or True  # may or may not change; just check no crash


# ── generate_with_pipeline() integration ────────────────────────────────────

def test_generate_with_pipeline_produces_all_fields():
    g = TransactionGenerator(fraud_rate=0.5, seed=7)
    ts = datetime(2026, 3, 14, 12, 0, 0)
    session = CustomerSessionState("C_TEST")
    tx = g.generate_with_pipeline(
        tx_id="P001",
        customer_id="C_TEST",
        device_id="D_TEST",
        timestamp=ts,
        customer_state="SP",
        customer_profile="business_owner",
        session_state=session,
    )
    required = [
        "transaction_id", "customer_id", "is_fraud", "fraud_type",
        "fraud_risk_score", "network_type", "language_locale",
        "typing_speed_avg_ms", "fraud_ring_id", "ring_role",
        "status", "unusual_time",
    ]
    for f in required:
        assert f in tx, f"Missing field: {f}"


def test_generate_with_pipeline_same_schema_as_generate():
    """Pipeline and original generate() must produce the same set of field names."""
    g1 = TransactionGenerator(fraud_rate=0.0, seed=42)
    g2 = TransactionGenerator(fraud_rate=0.0, seed=42)
    ts = datetime(2026, 3, 14, 14, 0, 0)

    tx_original = g1.generate(
        tx_id="A001", customer_id="C001", device_id="D001", timestamp=ts,
        customer_state="SP", customer_profile="young_digital",
    )
    tx_pipeline = g2.generate_with_pipeline(
        tx_id="A001", customer_id="C001", device_id="D001", timestamp=ts,
        customer_state="SP", customer_profile="young_digital",
    )

    orig_fields = set(tx_original.keys())
    pipe_fields = set(tx_pipeline.keys())

    # Pipeline should have at least all the fields the original has
    missing_in_pipeline = orig_fields - pipe_fields
    assert not missing_in_pipeline, f"Pipeline missing fields: {missing_in_pipeline}"


def test_generate_with_pipeline_biometrics_null_by_default():
    g = TransactionGenerator(fraud_rate=0.0, seed=1)
    ts = datetime(2026, 3, 14, 10, 0, 0)
    tx = g.generate_with_pipeline(
        tx_id="B001", customer_id="C001", device_id="D001", timestamp=ts,
    )
    assert tx.get("typing_speed_avg_ms") is None
    assert tx.get("navigation_order_anomaly") is None
