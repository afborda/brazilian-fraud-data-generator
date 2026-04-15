"""
Fraud rule correlation engine.

Matches a GenerationContext against 4 known fraud behavioral patterns and
sets ctx.matched_rule to the first matching rule name, or None.

Rules (priority order — most specific first):
    1. MALWARE_ATS   – robô automático no dispositivo da vítima
    2. ATO           – Account Takeover (dispositivo novo + IP diferente)
    3. FALSA_CENTRAL – golpe da falsa central (ligação ativa)
    4. CONTA_LARANJA – mula de dinheiro (conta recém-criada)

The matched rule is used by score.py to apply bonus weights, and by
generators/transaction.py to annotate the transaction's fraud_type field.
"""

from __future__ import annotations

from typing import Optional

from .session_context import GenerationContext


# ── Individual rule predicates ────────────────────────────────────────────────

def _matches_malware_ats(ctx: GenerationContext) -> bool:
    """
    Automated Transfer System malware running on victim's device.
    Signature: emulator + rooted + zero typing delay + zero accel + zero pressure.
    """
    return (
        ctx.is_emulator
        and ctx.is_rooted
        and ctx.typing_interval_ms <= 15
        and ctx.touch_pressure == 0.0
        and ctx.accel_magnitude == 0.0
    )


def _matches_ato(ctx: GenerationContext) -> bool:
    """
    Account Takeover: attacker on a device the victim has never used.
    Signature: new device + IP mismatch + short session + long inactivity.
    """
    return (
        ctx.new_device
        and ctx.ip_mismatch
        and 5 <= ctx.session_duration_s <= 20
        and ctx.hours_inactive >= 168   # ≥ 1 week without activity
    )


def _matches_falsa_central(ctx: GenerationContext) -> bool:
    """
    Golpe da falsa central: victim is on a call with attacker who instructs them.
    Signature: active call + high touch pressure (coerced) + brand-new dest account.
    """
    return (
        ctx.active_call
        and 0.75 <= ctx.touch_pressure <= 0.90
        and ctx.dest_account_age_days <= 7
    )


def _matches_conta_laranja(ctx: GenerationContext) -> bool:
    """
    Money mule: recently-opened account used as pass-through.
    Signature: multiple accounts + recent account (0-2h since login) + new dest account.
    """
    return (
        ctx.multiple_accounts
        and ctx.hours_inactive <= 2
        and ctx.dest_account_age_days <= 14
    )


# ── Public interface ──────────────────────────────────────────────────────────

# Ordered list of (rule_name, predicate) — most specific first.
_RULES: list[tuple[str, object]] = [
    ("MALWARE_ATS",   _matches_malware_ats),
    ("ATO",           _matches_ato),
    ("FALSA_CENTRAL", _matches_falsa_central),
    ("CONTA_LARANJA", _matches_conta_laranja),
]


def match_fraud_rule(ctx: GenerationContext) -> Optional[str]:
    """
    Evaluate all rules against *ctx* and return the first matching rule name.

    Returns None when no rule fires (legitimate or unknown pattern).
    Sets ctx.matched_rule as a side-effect so downstream components
    can read it without calling this function again.
    """
    for rule_name, predicate in _RULES:
        if predicate(ctx):
            ctx.matched_rule = rule_name
            return rule_name
    ctx.matched_rule = None
    return None


class FraudRuleMatcher:
    """
    Stateless, reusable wrapper around the rule evaluation pipeline.

    Prefer using module-level ``match_fraud_rule()`` for simple call sites.
    Use this class when you need to inject custom rules or mock during tests.
    """

    def __init__(self, rules: Optional[list[tuple[str, object]]] = None) -> None:
        self._rules = rules if rules is not None else _RULES

    def match(self, ctx: GenerationContext) -> Optional[str]:
        """Return the first matching rule name, or None."""
        for rule_name, predicate in self._rules:
            if predicate(ctx):
                ctx.matched_rule = rule_name
                return rule_name
        ctx.matched_rule = None
        return None

    def match_all(self, ctx: GenerationContext) -> list[str]:
        """Return all matching rule names (used in tests / analysis)."""
        return [name for name, pred in self._rules if pred(ctx)]
