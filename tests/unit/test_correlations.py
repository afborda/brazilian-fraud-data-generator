"""
Unit tests for generators/correlations.py — 4 fraud rule predicates.
"""

import pytest
from src.fraud_generator.generators.session_context import GenerationContext
from src.fraud_generator.generators.correlations import match_fraud_rule, FraudRuleMatcher


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_ctx():
    """Baseline legitimate context — no rule should fire."""
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
    )


@pytest.fixture
def malware_ats_ctx():
    """Context that matches the MALWARE_ATS rule exactly."""
    return GenerationContext(
        touch_pressure=0.0,       # bot: zero pressure
        typing_interval_ms=5,     # bot: <15ms
        accel_magnitude=0.0,      # emulator: no movement
        session_duration_s=3,
        confirm_latency_s=1,
        is_emulator=True,
        is_rooted=True,
        is_vpn=False,
        active_call=False,
        nav_anomaly=False,
        multiple_accounts=False,
        hours_inactive=0,
        new_device=False,
        ip_mismatch=False,
        sim_swap_recent=False,
        dest_account_age_days=180,
        new_beneficiary=False,
    )


@pytest.fixture
def ato_ctx():
    """Context that matches the ATO rule exactly."""
    return GenerationContext(
        touch_pressure=0.5,
        typing_interval_ms=80,
        accel_magnitude=0.8,
        session_duration_s=10,    # 5-20s
        confirm_latency_s=6,
        is_emulator=False,
        is_rooted=False,
        is_vpn=False,
        active_call=False,
        nav_anomaly=False,
        multiple_accounts=False,
        hours_inactive=200,       # >168h (over 1 week)
        new_device=True,
        ip_mismatch=True,
        sim_swap_recent=False,
        dest_account_age_days=180,
        new_beneficiary=False,
    )


@pytest.fixture
def falsa_central_ctx():
    """Context that matches the FALSA_CENTRAL rule exactly."""
    return GenerationContext(
        touch_pressure=0.80,      # coerced: 0.75-0.90
        typing_interval_ms=120,
        accel_magnitude=0.9,
        session_duration_s=300,
        confirm_latency_s=8,
        is_emulator=False,
        is_rooted=False,
        is_vpn=False,
        active_call=True,         # on the phone with attacker
        nav_anomaly=False,
        multiple_accounts=False,
        hours_inactive=5,
        new_device=False,
        ip_mismatch=False,
        sim_swap_recent=False,
        dest_account_age_days=3,  # brand-new mule account (<=7)
        new_beneficiary=True,
    )


@pytest.fixture
def conta_laranja_ctx():
    """Context that matches the CONTA_LARANJA rule exactly."""
    return GenerationContext(
        touch_pressure=0.5,
        typing_interval_ms=100,
        accel_magnitude=0.7,
        session_duration_s=60,
        confirm_latency_s=8,
        is_emulator=False,
        is_rooted=False,
        is_vpn=False,
        active_call=False,
        nav_anomaly=False,
        multiple_accounts=True,   # mule: multiple accounts on device
        hours_inactive=1,         # recently active (<=2h)
        new_device=False,
        ip_mismatch=False,
        sim_swap_recent=False,
        dest_account_age_days=10, # recently-opened mule (<=14)
        new_beneficiary=True,
    )


# ── Tests: individual rules fire ─────────────────────────────────────────────

class TestMalwareAtsRule:
    def test_matches_when_all_signals_set(self, malware_ats_ctx):
        result = match_fraud_rule(malware_ats_ctx)
        assert result == "MALWARE_ATS"

    def test_sets_matched_rule_on_ctx(self, malware_ats_ctx):
        match_fraud_rule(malware_ats_ctx)
        assert malware_ats_ctx.matched_rule == "MALWARE_ATS"

    def test_no_match_when_not_emulator(self, malware_ats_ctx):
        malware_ats_ctx.is_emulator = False
        result = match_fraud_rule(malware_ats_ctx)
        assert result != "MALWARE_ATS"

    def test_no_match_when_not_rooted(self, malware_ats_ctx):
        malware_ats_ctx.is_rooted = False
        result = match_fraud_rule(malware_ats_ctx)
        assert result != "MALWARE_ATS"

    def test_no_match_when_typing_too_slow(self, malware_ats_ctx):
        malware_ats_ctx.typing_interval_ms = 16  # just above threshold
        result = match_fraud_rule(malware_ats_ctx)
        assert result != "MALWARE_ATS"

    def test_no_match_when_pressure_nonzero(self, malware_ats_ctx):
        malware_ats_ctx.touch_pressure = 0.1
        result = match_fraud_rule(malware_ats_ctx)
        assert result != "MALWARE_ATS"


class TestAtoRule:
    def test_matches_when_all_signals_set(self, ato_ctx):
        result = match_fraud_rule(ato_ctx)
        assert result == "ATO"

    def test_sets_matched_rule_on_ctx(self, ato_ctx):
        match_fraud_rule(ato_ctx)
        assert ato_ctx.matched_rule == "ATO"

    def test_no_match_when_known_device(self, ato_ctx):
        ato_ctx.new_device = False
        result = match_fraud_rule(ato_ctx)
        assert result != "ATO"

    def test_no_match_when_no_ip_mismatch(self, ato_ctx):
        ato_ctx.ip_mismatch = False
        result = match_fraud_rule(ato_ctx)
        assert result != "ATO"

    def test_no_match_when_session_too_long(self, ato_ctx):
        ato_ctx.session_duration_s = 300  # outside 5-20s window
        result = match_fraud_rule(ato_ctx)
        assert result != "ATO"

    def test_no_match_when_session_too_short(self, ato_ctx):
        ato_ctx.session_duration_s = 3  # below 5s
        result = match_fraud_rule(ato_ctx)
        assert result != "ATO"

    def test_no_match_when_recently_active(self, ato_ctx):
        ato_ctx.hours_inactive = 100  # < 168h
        result = match_fraud_rule(ato_ctx)
        assert result != "ATO"


class TestFalsaCentralRule:
    def test_matches_when_all_signals_set(self, falsa_central_ctx):
        result = match_fraud_rule(falsa_central_ctx)
        assert result == "FALSA_CENTRAL"

    def test_no_match_when_not_on_call(self, falsa_central_ctx):
        falsa_central_ctx.active_call = False
        result = match_fraud_rule(falsa_central_ctx)
        assert result != "FALSA_CENTRAL"

    def test_no_match_when_pressure_too_low(self, falsa_central_ctx):
        falsa_central_ctx.touch_pressure = 0.50  # below coerced range
        result = match_fraud_rule(falsa_central_ctx)
        assert result != "FALSA_CENTRAL"

    def test_no_match_when_dest_account_old(self, falsa_central_ctx):
        falsa_central_ctx.dest_account_age_days = 30  # > 7 days
        result = match_fraud_rule(falsa_central_ctx)
        assert result != "FALSA_CENTRAL"

    def test_boundary_pressure_0_75(self, falsa_central_ctx):
        falsa_central_ctx.touch_pressure = 0.75  # lower boundary
        result = match_fraud_rule(falsa_central_ctx)
        assert result == "FALSA_CENTRAL"

    def test_boundary_pressure_0_90(self, falsa_central_ctx):
        falsa_central_ctx.touch_pressure = 0.90  # upper boundary
        result = match_fraud_rule(falsa_central_ctx)
        assert result == "FALSA_CENTRAL"


class TestContaLaranjaRule:
    def test_matches_when_all_signals_set(self, conta_laranja_ctx):
        result = match_fraud_rule(conta_laranja_ctx)
        assert result == "CONTA_LARANJA"

    def test_no_match_when_single_account(self, conta_laranja_ctx):
        conta_laranja_ctx.multiple_accounts = False
        result = match_fraud_rule(conta_laranja_ctx)
        assert result != "CONTA_LARANJA"

    def test_no_match_when_inactive_too_long(self, conta_laranja_ctx):
        conta_laranja_ctx.hours_inactive = 5  # > 2h
        result = match_fraud_rule(conta_laranja_ctx)
        assert result != "CONTA_LARANJA"

    def test_no_match_when_dest_account_established(self, conta_laranja_ctx):
        conta_laranja_ctx.dest_account_age_days = 30  # > 14
        result = match_fraud_rule(conta_laranja_ctx)
        assert result != "CONTA_LARANJA"


# ── Tests: clean context fires nothing ───────────────────────────────────────

class TestCleanContext:
    def test_no_rule_fires_for_legitimate_transaction(self, clean_ctx):
        result = match_fraud_rule(clean_ctx)
        assert result is None

    def test_matched_rule_is_none_for_legitimate(self, clean_ctx):
        match_fraud_rule(clean_ctx)
        assert clean_ctx.matched_rule is None


# ── Tests: FraudRuleMatcher class ────────────────────────────────────────────

class TestFraudRuleMatcher:
    def test_default_rules_fire(self, ato_ctx):
        matcher = FraudRuleMatcher()
        result = matcher.match(ato_ctx)
        assert result == "ATO"

    def test_custom_rules_can_be_injected(self, clean_ctx):
        custom_rule = lambda ctx: True  # always fires
        matcher = FraudRuleMatcher(rules=[("MY_RULE", custom_rule)])
        result = matcher.match(clean_ctx)
        assert result == "MY_RULE"

    def test_empty_rules_returns_none(self, clean_ctx):
        matcher = FraudRuleMatcher(rules=[])
        result = matcher.match(clean_ctx)
        assert result is None
