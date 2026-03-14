"""
Session context generator.

Produces a unified GenerationContext per transaction that bundles:
  - Velocity/session state  (from utils/streaming.CustomerSessionState)
  - Device biometric signals (from profiles/device.sample_device_signals)
  - Account inactivity info
  - Derived flags: new_device, ip_mismatch, sim_swap, etc.

The context is consumed by generators/correlations.py (fraud rule matching)
and generators/score.py (fraud_risk_score computation).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import random

from ..profiles.device import (
    DeviceSignalProfile,
    get_device_profile,
    sample_device_signals,
)
from ..utils.streaming import CustomerSessionState


@dataclass
class GenerationContext:
    """
    Snapshot of all signals available at the moment a transaction is generated.

    Fields map 1-to-1 to the 17 signals used by score.py.
    """
    # ── Device signals (from profiles/device.py) ──────────────────────────
    touch_pressure: float = 0.5          # 0.0 = bot, 0.75-0.90 = coerced
    typing_interval_ms: int = 150        # <15 = bot/ATS
    accel_magnitude: float = 1.0         # 0.0 = emulator/fixed device
    session_duration_s: int = 120        # <5 = bot, 5-20 = ATO
    confirm_latency_s: int = 10          # <5 = scripted
    is_emulator: bool = False
    is_rooted: bool = False
    is_vpn: bool = False
    active_call: bool = False
    nav_anomaly: bool = False
    multiple_accounts: bool = False

    # ── Account state ─────────────────────────────────────────────────────
    hours_inactive: int = 0              # >168h = week inactive (ATO signal)
    new_device: bool = False             # device not seen before
    ip_mismatch: bool = False            # IP state != account state
    sim_swap_recent: bool = False        # SIM swap in last 7 days

    # ── Velocity (from CustomerSessionState) ──────────────────────────────
    velocity_transactions_24h: int = 1
    accumulated_amount_24h: float = 0.0
    time_since_last_txn_min: Optional[int] = None

    # ── Destination account ───────────────────────────────────────────────
    dest_account_age_days: int = 180     # <7 = brand-new mule account
    new_beneficiary: bool = False

    # ── Transaction values ─────────────────────────────────────────────────
    amount: float = 0.0
    typical_amount: float = 0.0         # customer's historical average

    # ── Push notification ─────────────────────────────────────────────────
    notification_ignored: bool = False   # customer ignored security notification

    # ── Matched fraud rule (populated by correlations.py) ─────────────────
    matched_rule: Optional[str] = None


class SessionContextGenerator:
    """
    Generates a GenerationContext for each transaction.

    Usage:
        ctx_gen = SessionContextGenerator()
        ctx = ctx_gen.build(
            fraud_type="CONTA_TOMADA",
            session_state=customer_session,
            current_time=timestamp,
            amount=1500.0,
            customer_typical_amount=200.0,
            customer_device_ids={"DEV_000001"},
            transaction_device_id="DEV_999999",  # new device → new_device=True
            customer_state="SP",
            tx_ip_state="RJ",
        )
    """

    def build(
        self,
        fraud_type: Optional[str],
        session_state: Optional[CustomerSessionState],
        current_time: datetime,
        amount: float,
        customer_typical_amount: float = 200.0,
        customer_device_ids: Optional[set] = None,
        transaction_device_id: Optional[str] = None,
        customer_state: Optional[str] = None,
        tx_ip_state: Optional[str] = None,
        last_login_dt: Optional[datetime] = None,
        rng=None,
    ) -> GenerationContext:
        """
        Build a GenerationContext for a single transaction.

        If fraud_type is supplied, signals are sampled from the matching
        DeviceSignalProfile (biased toward fraud detection).
        Otherwise, normal_human profile is used.
        """
        r = rng or random

        # 1. Device biometric signals
        profile: DeviceSignalProfile = get_device_profile(fraud_type)
        signals = sample_device_signals(profile, rng=r)

        # 2. Velocity from session state
        velocity = 1
        accumulated = 0.0
        time_since_last = None
        if session_state:
            velocity = session_state.get_velocity(current_time) + 1
            accumulated = session_state.get_accumulated_24h(current_time) + amount
            time_since_last = session_state.get_last_transaction_minutes_ago(current_time)

        # 3. Account inactivity
        hours_inactive = 0
        if last_login_dt:
            delta = current_time - last_login_dt
            hours_inactive = int(delta.total_seconds() / 3600)
        elif fraud_type in ("CONTA_TOMADA", "CARTAO_CLONADO"):
            # ATO patterns: long inactivity before takeover
            hours_inactive = r.randint(168, 720)  # 1–4 weeks

        # 4. New device detection
        is_new_device = False
        if customer_device_ids is not None and transaction_device_id:
            is_new_device = transaction_device_id not in customer_device_ids
        elif fraud_type in ("CONTA_TOMADA", "CARTAO_CLONADO"):
            is_new_device = r.random() < 0.80

        # 5. IP geolocation mismatch
        ip_mismatch = False
        if customer_state and tx_ip_state:
            ip_mismatch = customer_state != tx_ip_state
        elif fraud_type in ("CONTA_TOMADA", "CARTAO_CLONADO"):
            ip_mismatch = r.random() < 0.70
        elif fraud_type in ("BOT_ATS", "MICRO_BURST_VELOCITY"):
            ip_mismatch = r.random() < 0.60

        # 6. SIM swap
        sim_swap = False
        if fraud_type in ("CONTA_TOMADA", "ENGENHARIA_SOCIAL"):
            sim_swap = r.random() < 0.20

        # 7. Destination account
        dest_age = _sample_dest_account_age(fraud_type, r)
        new_beneficiary = dest_age < 30 or (fraud_type is not None and r.random() < 0.75)

        # 8. Notification ignored
        notification_ignored = False
        if fraud_type in ("CONTA_TOMADA", "PIX_GOLPE", "ENGENHARIA_SOCIAL"):
            notification_ignored = r.random() < 0.60

        return GenerationContext(
            # device signals
            touch_pressure=signals["touch_pressure"],
            typing_interval_ms=signals["typing_interval_ms"],
            accel_magnitude=signals["accel_magnitude"],
            session_duration_s=signals["session_duration_s"],
            confirm_latency_s=signals["confirm_latency_s"],
            is_emulator=signals["is_emulator"],
            is_rooted=signals["is_rooted"],
            is_vpn=signals["is_vpn"],
            active_call=signals["active_call"],
            nav_anomaly=signals["nav_anomaly"],
            multiple_accounts=signals["multiple_accounts"],
            # account state
            hours_inactive=hours_inactive,
            new_device=is_new_device,
            ip_mismatch=ip_mismatch,
            sim_swap_recent=sim_swap,
            # velocity
            velocity_transactions_24h=velocity,
            accumulated_amount_24h=round(accumulated, 2),
            time_since_last_txn_min=time_since_last,
            # destination
            dest_account_age_days=dest_age,
            new_beneficiary=new_beneficiary,
            # amount
            amount=amount,
            typical_amount=customer_typical_amount,
            # notification
            notification_ignored=notification_ignored,
        )

    def enrich_transaction(self, tx: Dict[str, Any], ctx: GenerationContext) -> Dict[str, Any]:
        """
        Merge GenerationContext signal fields into a transaction dict.
        Called after generate() to attach device/session signals to the record.
        """
        tx.update({
            # Biometric / device
            "touch_pressure":         ctx.touch_pressure,
            "typing_interval_ms":     ctx.typing_interval_ms,
            "accel_magnitude":        ctx.accel_magnitude,
            "session_duration_s":     ctx.session_duration_s,
            "confirm_latency_s":      ctx.confirm_latency_s,
            "is_emulator":            ctx.is_emulator,
            "rooted_or_jailbreak":    ctx.is_rooted,
            "is_vpn":                 ctx.is_vpn,
            "active_call":            ctx.active_call,
            "nav_anomaly":            ctx.nav_anomaly,
            "multiple_accounts":      ctx.multiple_accounts,
            # Account state
            "hours_inactive":         ctx.hours_inactive,
            "new_device":             ctx.new_device,
            "ip_mismatch":            ctx.ip_mismatch,
            "sim_swap_recent":        ctx.sim_swap_recent,
            # Velocity (override if set by context)
            "velocity_transactions_24h": ctx.velocity_transactions_24h,
            "accumulated_amount_24h":    ctx.accumulated_amount_24h,
            # Destination
            "dest_account_age_days":  ctx.dest_account_age_days,
            "new_beneficiary":        ctx.new_beneficiary,
            # Notification
            "notification_ignored":   ctx.notification_ignored,
        })
        return tx


def _sample_dest_account_age(fraud_type: Optional[str], rng) -> int:
    """Sample destination account age in days."""
    if fraud_type in ("PIX_GOLPE", "ENGENHARIA_SOCIAL", "LAVAGEM_DINHEIRO", "TRIANGULACAO"):
        return rng.randint(0, 7)       # brand-new mule account
    elif fraud_type in ("CONTA_TOMADA", "CARTAO_CLONADO"):
        return rng.randint(0, 30)      # recently opened mule account
    else:
        return rng.randint(30, 3650)   # established account
