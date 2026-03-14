"""
Unit tests for generators/score.py — 17-signal fraud_risk_score calculator.
"""

import pytest
from src.fraud_generator.generators.session_context import GenerationContext
from src.fraud_generator.generators.score import compute_fraud_risk_score, score_breakdown


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def zero_ctx():
    """All signals off — should produce score 0."""
    return GenerationContext(
        touch_pressure=0.5,
        typing_interval_ms=150,
        accel_magnitude=1.0,
        session_duration_s=120,
        confirm_latency_s=10,
        is_emulator=False,
        is_rooted=False,
        is_vpn=False,
        active_call=False,
        nav_anomaly=False,
        multiple_accounts=False,
        hours_inactive=0,
        new_device=False,
        ip_mismatch=False,
        sim_swap_recent=False,
        dest_account_age_days=365,
        new_beneficiary=False,
        amount=100.0,
        typical_amount=150.0,
        notification_ignored=False,
    )


@pytest.fixture
def max_ctx():
    """All high-weight signals active — should produce score 100 (capped)."""
    return GenerationContext(
        touch_pressure=0.0,       # _W_PRESSURE_ZERO = 20
        typing_interval_ms=5,     # _W_TYPING_BOT = 30
        accel_magnitude=0.0,      # part of _W_ACCEL_SESSION with session_duration_s<5
        session_duration_s=2,     # _W_ACCEL_SESSION = 28  |  _W_SESSION_HIGH_VALUE = 15
        confirm_latency_s=2,      # _W_CONFIRM_FAST = 12
        is_emulator=True,         # _W_EMULATOR = 35
        is_rooted=True,           # _W_ROOTED = 30
        is_vpn=True,              # _W_VPN_DATACENTER = 15
        active_call=True,         # _W_ACTIVE_CALL = 35
        nav_anomaly=True,         # _W_NAV_ANOMALY = 10
        multiple_accounts=True,   # _W_MULTIPLE_ACCOUNTS = 18
        hours_inactive=200,       # part of ATO triad
        new_device=True,          # part of ATO triad  _W_ATO_TRIAD = 25
        ip_mismatch=True,         # part of ATO triad
        sim_swap_recent=True,     # _W_SIM_SWAP = 10
        dest_account_age_days=3,  # _W_DEST_ACCOUNT_NEW = 20
        new_beneficiary=True,
        amount=10000.0,           # >> 5× typical → _W_AMOUNT_SPIKE = 8
        typical_amount=100.0,
        notification_ignored=True,  # _W_NOTIF_IGNORED = 5
    )


# ── Tests: basic bounds ───────────────────────────────────────────────────────

class TestScoreBounds:
    def test_minimum_score_is_zero(self, zero_ctx):
        score = compute_fraud_risk_score(zero_ctx)
        assert score == 0

    def test_score_never_exceeds_100(self, max_ctx):
        score = compute_fraud_risk_score(max_ctx)
        assert score == 100

    def test_score_is_integer(self, zero_ctx):
        score = compute_fraud_risk_score(zero_ctx)
        assert isinstance(score, int)

    def test_score_is_integer_for_fraud(self, max_ctx):
        score = compute_fraud_risk_score(max_ctx)
        assert isinstance(score, int)


# ── Tests: individual signals ────────────────────────────────────────────────

class TestIndividualSignals:
    def test_active_call_adds_weight(self, zero_ctx):
        zero_ctx.active_call = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_emulator_adds_weight(self, zero_ctx):
        zero_ctx.is_emulator = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_rooted_adds_weight(self, zero_ctx):
        zero_ctx.is_rooted = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_typing_bot_adds_weight(self, zero_ctx):
        zero_ctx.typing_interval_ms = 5
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_typing_16ms_does_not_fire(self, zero_ctx):
        zero_ctx.typing_interval_ms = 16  # just above threshold
        score = compute_fraud_risk_score(zero_ctx)
        assert score == 0

    def test_accel_session_signal(self, zero_ctx):
        zero_ctx.accel_magnitude = 0.0
        zero_ctx.session_duration_s = 3  # <5s
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_accel_session_no_fire_if_session_long(self, zero_ctx):
        zero_ctx.accel_magnitude = 0.0
        zero_ctx.session_duration_s = 10  # >=5s → signal should not fire
        score = compute_fraud_risk_score(zero_ctx)
        assert score == 0

    def test_ato_triad_adds_weight(self, zero_ctx):
        zero_ctx.new_device = True
        zero_ctx.ip_mismatch = True
        zero_ctx.hours_inactive = 200  # >=168h
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_ato_triad_no_fire_if_not_inactive_enough(self, zero_ctx):
        zero_ctx.new_device = True
        zero_ctx.ip_mismatch = True
        zero_ctx.hours_inactive = 100  # <168h
        score = compute_fraud_risk_score(zero_ctx)
        assert score == 0

    def test_dest_account_new_adds_weight(self, zero_ctx):
        zero_ctx.dest_account_age_days = 3  # <7 days
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_dest_account_7_days_no_fire(self, zero_ctx):
        zero_ctx.dest_account_age_days = 7  # boundary: not strictly less
        score = compute_fraud_risk_score(zero_ctx)
        assert score == 0

    def test_pressure_zero_adds_weight(self, zero_ctx):
        zero_ctx.touch_pressure = 0.0
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_vpn_adds_weight(self, zero_ctx):
        zero_ctx.is_vpn = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_session_high_value_adds_weight(self, zero_ctx):
        zero_ctx.session_duration_s = 5   # <10s
        zero_ctx.amount = 5000.0
        zero_ctx.typical_amount = 100.0   # amount >> typical
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_confirm_fast_adds_weight(self, zero_ctx):
        zero_ctx.confirm_latency_s = 2  # <5s
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_nav_anomaly_adds_weight(self, zero_ctx):
        zero_ctx.nav_anomaly = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_sim_swap_adds_weight(self, zero_ctx):
        zero_ctx.sim_swap_recent = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_amount_spike_adds_weight(self, zero_ctx):
        zero_ctx.amount = 1001.0
        zero_ctx.typical_amount = 100.0   # 10× > 5×
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_amount_spike_no_fire_below_5x(self, zero_ctx):
        zero_ctx.amount = 400.0
        zero_ctx.typical_amount = 100.0   # 4× < 5×
        score = compute_fraud_risk_score(zero_ctx)
        assert score == 0

    def test_notification_ignored_adds_weight(self, zero_ctx):
        zero_ctx.notification_ignored = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0

    def test_multiple_accounts_adds_weight(self, zero_ctx):
        zero_ctx.multiple_accounts = True
        score = compute_fraud_risk_score(zero_ctx)
        assert score > 0


# ── Tests: score_breakdown ────────────────────────────────────────────────────

class TestScoreBreakdown:
    def test_breakdown_contains_total(self, zero_ctx):
        bd = score_breakdown(zero_ctx)
        assert "total" in bd

    def test_breakdown_total_matches_compute(self, max_ctx):
        bd = score_breakdown(max_ctx)
        assert bd["total"] == compute_fraud_risk_score(max_ctx)

    def test_breakdown_all_values_non_negative(self, max_ctx):
        bd = score_breakdown(max_ctx)
        for k, v in bd.items():
            assert v >= 0, f"Signal {k} has negative value {v}"

    def test_breakdown_zero_ctx_all_zeros(self, zero_ctx):
        bd = score_breakdown(zero_ctx)
        signals = {k: v for k, v in bd.items() if k != "total"}
        assert all(v == 0 for v in signals.values())

    def test_breakdown_total_is_capped_at_100(self, max_ctx):
        bd = score_breakdown(max_ctx)
        assert bd["total"] <= 100


# ── Tests: score ordering ─────────────────────────────────────────────────────

class TestScoreOrdering:
    def test_fraud_profile_scores_higher_than_legitimate(self, zero_ctx, max_ctx):
        legit_score = compute_fraud_risk_score(zero_ctx)
        fraud_score = compute_fraud_risk_score(max_ctx)
        assert fraud_score > legit_score

    def test_emulator_scores_higher_than_no_emulator(self, zero_ctx):
        base = compute_fraud_risk_score(zero_ctx)
        zero_ctx.is_emulator = True
        with_emulator = compute_fraud_risk_score(zero_ctx)
        assert with_emulator > base
