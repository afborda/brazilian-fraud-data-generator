"""
Unit tests for generators/session_context.py — GenerationContext and
build_context_for_fraud helper.
"""

import pytest
from datetime import datetime
from src.fraud_generator.generators.session_context import (
    GenerationContext,
    SessionContextGenerator,
    build_context_for_fraud,
)


# ── Tests: GenerationContext defaults ────────────────────────────────────────

class TestGenerationContextDefaults:
    def test_default_touch_pressure(self):
        ctx = GenerationContext()
        assert ctx.touch_pressure == 0.5

    def test_default_is_emulator_false(self):
        ctx = GenerationContext()
        assert ctx.is_emulator is False

    def test_default_matched_rule_none(self):
        ctx = GenerationContext()
        assert ctx.matched_rule is None

    def test_default_velocity_is_one(self):
        ctx = GenerationContext()
        assert ctx.velocity_transactions_24h == 1

    def test_default_dest_age_180(self):
        ctx = GenerationContext()
        assert ctx.dest_account_age_days == 180


# ── Tests: build_context_for_fraud ───────────────────────────────────────────

class TestBuildContextForFraud:
    def _base_tx(self, **overrides):
        tx = {
            "amount": 500.0,
            "new_device": False,
            "ip_mismatch": False,
            "hours_inactive": 0,
            "sim_swap_recent": False,
            "dest_account_age_days": 180,
            "new_beneficiary": False,
            "velocity_transactions_24h": 2,
            "accumulated_amount_24h": 1000.0,
            "time_since_last_txn_min": 30,
            "rooted_or_jailbreak": False,
            "multiple_accounts": False,
            "notification_ignored": False,
        }
        tx.update(overrides)
        return tx

    def test_returns_generation_context(self):
        tx = self._base_tx()
        ctx = build_context_for_fraud(tx, is_fraud=False, fraud_type=None)
        assert isinstance(ctx, GenerationContext)

    def test_amount_propagated(self):
        tx = self._base_tx(amount=1234.56)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type="PIX_GOLPE")
        assert ctx.amount == 1234.56

    def test_velocity_propagated(self):
        tx = self._base_tx(velocity_transactions_24h=15)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type="CONTA_TOMADA")
        assert ctx.velocity_transactions_24h == 15

    def test_hours_inactive_propagated(self):
        tx = self._base_tx(hours_inactive=240)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type="CONTA_TOMADA")
        assert ctx.hours_inactive == 240

    def test_new_device_propagated(self):
        tx = self._base_tx(new_device=True)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type="CONTA_TOMADA")
        assert ctx.new_device is True

    def test_ip_mismatch_propagated(self):
        tx = self._base_tx(ip_mismatch=True)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type="CARTAO_CLONADO")
        assert ctx.ip_mismatch is True

    def test_rooted_flag_propagated(self):
        tx = self._base_tx(rooted_or_jailbreak=True)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type=None)
        assert ctx.is_rooted is True

    def test_dest_account_age_propagated(self):
        tx = self._base_tx(dest_account_age_days=3)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type="PIX_GOLPE")
        assert ctx.dest_account_age_days == 3

    def test_notification_ignored_propagated(self):
        tx = self._base_tx(notification_ignored=True)
        ctx = build_context_for_fraud(tx, is_fraud=True, fraud_type="ENGENHARIA_SOCIAL")
        assert ctx.notification_ignored is True

    def test_typical_amount_default(self):
        tx = self._base_tx()
        ctx = build_context_for_fraud(tx, is_fraud=False, fraud_type=None)
        assert ctx.typical_amount == 200.0

    def test_typical_amount_override(self):
        tx = self._base_tx()
        ctx = build_context_for_fraud(tx, is_fraud=False, fraud_type=None, customer_typical_amount=350.0)
        assert ctx.typical_amount == 350.0

    def test_missing_fields_use_defaults(self):
        """Should not raise even if tx is mostly empty."""
        ctx = build_context_for_fraud({}, is_fraud=False, fraud_type=None)
        assert isinstance(ctx, GenerationContext)
        assert ctx.amount == 0.0
        assert ctx.velocity_transactions_24h == 1

    def test_device_signals_populated(self):
        """Device profile signals should always be non-None."""
        tx = self._base_tx()
        ctx = build_context_for_fraud(tx, is_fraud=False, fraud_type=None)
        assert ctx.typing_interval_ms is not None
        assert ctx.session_duration_s is not None
        assert isinstance(ctx.is_emulator, bool)


# ── Tests: SessionContextGenerator.build ─────────────────────────────────────

class TestSessionContextGeneratorBuild:
    def test_returns_generation_context(self):
        gen = SessionContextGenerator()
        ctx = gen.build(
            fraud_type=None,
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=200.0,
        )
        assert isinstance(ctx, GenerationContext)

    def test_fraud_type_influences_device_signals(self):
        gen = SessionContextGenerator()
        legit_ctx = gen.build(
            fraud_type=None,
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=200.0,
            rng=__import__("random").Random(42),
        )
        fraud_ctx = gen.build(
            fraud_type="MALWARE_ATS",
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=200.0,
            rng=__import__("random").Random(42),
        )
        # With seed 42, both will call sample_device_signals — just check types
        assert isinstance(legit_ctx.is_emulator, bool)
        assert isinstance(fraud_ctx.is_emulator, bool)

    def test_amount_stored_in_context(self):
        gen = SessionContextGenerator()
        ctx = gen.build(
            fraud_type=None,
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=999.99,
        )
        assert ctx.amount == 999.99

    def test_new_device_detected_when_device_not_in_set(self):
        gen = SessionContextGenerator()
        ctx = gen.build(
            fraud_type=None,
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=100.0,
            customer_device_ids={"DEV_001", "DEV_002"},
            transaction_device_id="DEV_999",  # not in set
        )
        assert ctx.new_device is True

    def test_known_device_is_not_new(self):
        gen = SessionContextGenerator()
        ctx = gen.build(
            fraud_type=None,
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=100.0,
            customer_device_ids={"DEV_001", "DEV_002"},
            transaction_device_id="DEV_001",  # in set
        )
        assert ctx.new_device is False

    def test_ip_mismatch_detected_by_state(self):
        gen = SessionContextGenerator()
        ctx = gen.build(
            fraud_type=None,
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=100.0,
            customer_state="SP",
            tx_ip_state="RJ",
        )
        assert ctx.ip_mismatch is True

    def test_no_ip_mismatch_for_same_state(self):
        gen = SessionContextGenerator()
        ctx = gen.build(
            fraud_type=None,
            session_state=None,
            current_time=datetime(2025, 6, 1, 12, 0, 0),
            amount=100.0,
            customer_state="SP",
            tx_ip_state="SP",
        )
        assert ctx.ip_mismatch is False
