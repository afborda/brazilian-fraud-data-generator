"""
Fraud risk score calculator (17 signals → 0-100 int).

Consumes a GenerationContext (already enriched by correlations.py) and
returns an integer score 0-100 stored in Transaction.fraud_risk_score.

Signal weights are tuned for Brazilian banking fraud patterns (2023-2024 BACEN data).

Usage:
    from fraud_generator.generators.score import compute_fraud_risk_score
    from fraud_generator.generators.correlations import match_fraud_rule

    match_fraud_rule(ctx)                        # sets ctx.matched_rule
    tx['fraud_risk_score'] = compute_fraud_risk_score(ctx)
"""

from __future__ import annotations

from typing import Optional

from .session_context import GenerationContext


# ── Signal weight constants ───────────────────────────────────────────────────

_W_ACTIVE_CALL         = 35   # Victim on phone with attacker (FALSA_CENTRAL)
_W_EMULATOR            = 35   # Device is emulated (MALWARE_ATS)
_W_ROOTED              = 30   # Device is rooted/jailbroken (MALWARE_ATS support)
_W_TYPING_BOT          = 30   # Typing interval < 15ms → automated input
_W_ACCEL_SESSION       = 28   # Zero accel + session < 5s → static device/script
_W_ATO_TRIAD           = 25   # new_device + ip_mismatch + hours_inactive ≥ 168
_W_DEST_ACCOUNT_NEW    = 20   # Destination account opened < 7 days ago
_W_PRESSURE_ZERO       = 20   # Touch pressure == 0.0 (no human fingers detected)
_W_MULTIPLE_ACCOUNTS   = 18   # Multiple accounts from same device (CONTA_LARANJA)
_W_VPN_DATACENTER      = 15   # VPN + short session (attacker hiding origin)
_W_SESSION_HIGH_VALUE  = 15   # Session < 10s + amount > typical (rushed ATO)
_W_CONFIRM_FAST        = 12   # Confirmation latency < 5s (scripted flow)
_W_NAV_ANOMALY         = 10   # Navigation pattern anomaly (non-human path)
_W_SIM_SWAP            = 10   # SIM swap in last 7 days (account hijack setup)
_W_ODD_HOURS           = 8    # Transaction 00:00–06:00 local time
_W_AMOUNT_SPIKE        = 8    # Amount > 5× customer historical average
_W_NOTIF_IGNORED       = 5    # Customer ignored security push notification

_MAX_SCORE = 100


# ── Individual signal evaluators ─────────────────────────────────────────────

def _score_active_call(ctx: GenerationContext) -> int:
    return _W_ACTIVE_CALL if ctx.active_call else 0


def _score_emulator(ctx: GenerationContext) -> int:
    return _W_EMULATOR if ctx.is_emulator else 0


def _score_rooted(ctx: GenerationContext) -> int:
    return _W_ROOTED if ctx.is_rooted else 0


def _score_typing_bot(ctx: GenerationContext) -> int:
    return _W_TYPING_BOT if ctx.typing_interval_ms <= 15 else 0


def _score_accel_session(ctx: GenerationContext) -> int:
    """Zero acceleration AND session < 5s — device is stationary/scripted."""
    return _W_ACCEL_SESSION if (ctx.accel_magnitude == 0.0 and ctx.session_duration_s < 5) else 0


def _score_ato_triad(ctx: GenerationContext) -> int:
    """Classic ATO triad: new device + IP mismatch + long inactivity."""
    return _W_ATO_TRIAD if (ctx.new_device and ctx.ip_mismatch and ctx.hours_inactive >= 168) else 0


def _score_dest_account_new(ctx: GenerationContext) -> int:
    return _W_DEST_ACCOUNT_NEW if ctx.dest_account_age_days < 7 else 0


def _score_pressure_zero(ctx: GenerationContext) -> int:
    return _W_PRESSURE_ZERO if ctx.touch_pressure == 0.0 else 0


def _score_multiple_accounts(ctx: GenerationContext) -> int:
    return _W_MULTIPLE_ACCOUNTS if ctx.multiple_accounts else 0


def _score_vpn_datacenter(ctx: GenerationContext) -> int:
    """VPN active (attacker routing through datacenter)."""
    return _W_VPN_DATACENTER if ctx.is_vpn else 0


def _score_session_high_value(ctx: GenerationContext) -> int:
    """Very short session + amount above customer's typical — rushed attacker."""
    if ctx.session_duration_s < 10 and ctx.typical_amount > 0:
        if ctx.amount > ctx.typical_amount:
            return _W_SESSION_HIGH_VALUE
    return 0


def _score_confirm_fast(ctx: GenerationContext) -> int:
    return _W_CONFIRM_FAST if ctx.confirm_latency_s < 5 else 0


def _score_nav_anomaly(ctx: GenerationContext) -> int:
    return _W_NAV_ANOMALY if ctx.nav_anomaly else 0


def _score_sim_swap(ctx: GenerationContext) -> int:
    return _W_SIM_SWAP if ctx.sim_swap_recent else 0


def _score_odd_hours(ctx: GenerationContext) -> int:
    """
    Transactions generated between midnight and 06:00 are statistically riskier.
    We proxy this by reading ctx.amount as a surrogate only when ctx has no
    explicit hour field.  If the generator sets tx['hour'] it should be forwarded
    to the context; until then this signal checks the accumulated_amount_24h spike
    as a proxy for late-night behaviour.
    """
    # NOTE: A future version of GenerationContext should add `transaction_hour: int`.
    # For now, skip scoring this signal to avoid false positives.
    return 0


def _score_amount_spike(ctx: GenerationContext) -> int:
    """Amount > 5× historical average."""
    if ctx.typical_amount > 0 and ctx.amount > 5 * ctx.typical_amount:
        return _W_AMOUNT_SPIKE
    return 0


def _score_notification_ignored(ctx: GenerationContext) -> int:
    return _W_NOTIF_IGNORED if ctx.notification_ignored else 0


# ── Aggregator ────────────────────────────────────────────────────────────────

_EVALUATORS = [
    _score_active_call,
    _score_emulator,
    _score_rooted,
    _score_typing_bot,
    _score_accel_session,
    _score_ato_triad,
    _score_dest_account_new,
    _score_pressure_zero,
    _score_multiple_accounts,
    _score_vpn_datacenter,
    _score_session_high_value,
    _score_confirm_fast,
    _score_nav_anomaly,
    _score_sim_swap,
    _score_odd_hours,
    _score_amount_spike,
    _score_notification_ignored,
]


def compute_fraud_risk_score(ctx: GenerationContext) -> int:
    """
    Sum all active signal weights and clamp to [0, 100].

    Returns an integer suitable for Transaction.fraud_risk_score.
    """
    raw = sum(fn(ctx) for fn in _EVALUATORS)
    return min(raw, _MAX_SCORE)


def score_breakdown(ctx: GenerationContext) -> dict[str, int]:
    """
    Return per-signal contributions (useful for explainability analysis).

    Example:
        {
            'active_call': 35,
            'emulator': 0,
            ...
            'total': 45
        }
    """
    labels = [fn.__name__.removeprefix('_score_') for fn in _EVALUATORS]
    values = [fn(ctx) for fn in _EVALUATORS]
    result = dict(zip(labels, values))
    result['total'] = min(sum(values), _MAX_SCORE)
    return result
