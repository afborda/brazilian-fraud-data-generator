"""
Device & biometric behavioral profiles.

Each profile defines realistic device signal distributions that are fed into
generators/score.py to compute fraud_risk_score.

Signal taxonomy (from Master_Unificado research):
  - Biometric pressure:     0.0 (bot/ATS), 0.40-0.65 (normal), 0.75-0.90 (coerced)
  - Typing interval (ms):   0-15 (bot), 80-300 (normal human)
  - Accelerometer:          0.0 (device fixed/emulator), 0.1-2.5 (handheld)
  - Session duration (s):   <5 (bot), 10-30 (ATO), 60-600 (normal), >600 (suspeito-idle)
  - Confirmation time (s):  <5 (scripted), 5-30 (normal), >30 (coerced/pressured)
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import random


@dataclass
class DeviceSignalProfile:
    """
    Defines realistic distributions for device & biometric signals.
    Used by generators to produce correlated signals instead of random noise.
    """
    name: str
    description: str

    # Touch pressure: (min, max) — float 0.0-1.0
    pressure_range: Tuple[float, float]
    # Typing interval ms: (min, max)
    typing_interval_ms_range: Tuple[int, int]
    # Accelerometer magnitude: (min, max)
    accel_magnitude_range: Tuple[float, float]
    # Session duration seconds: (min, max)
    session_duration_s_range: Tuple[int, int]
    # Confirm click latency seconds: (min, max)
    confirm_latency_s_range: Tuple[int, int]
    # Probability of being emulator
    emulator_prob: float
    # Probability of rooted/jailbroken
    rooted_prob: float
    # Probability of VPN/datacenter IP
    vpn_prob: float
    # Probability of active call during transaction
    active_call_prob: float
    # Probability of navigation anomaly (skipped screens)
    nav_anomaly_prob: float
    # Probability of multiple accounts on same device
    multi_account_prob: float


# ─────────────────────────────────────────────────────────────────────────────
# Profile: Normal Human — typical legitimate user
# ─────────────────────────────────────────────────────────────────────────────
NORMAL_HUMAN = DeviceSignalProfile(
    name="normal_human",
    description="Legitimate user — handheld smartphone, natural biometrics",
    pressure_range=(0.40, 0.65),
    typing_interval_ms_range=(80, 350),
    accel_magnitude_range=(0.3, 2.5),
    session_duration_s_range=(60, 480),
    confirm_latency_s_range=(5, 30),
    emulator_prob=0.001,
    rooted_prob=0.02,
    vpn_prob=0.04,
    active_call_prob=0.02,
    nav_anomaly_prob=0.03,
    multi_account_prob=0.05,
)

# ─────────────────────────────────────────────────────────────────────────────
# Profile: Bot / ATS (Automated Transfer System)
# Fingerprint: emulator flag, zero pressure, typing < 15ms, accel = 0
# Maps to fraud rule: MALWARE_ATS
# ─────────────────────────────────────────────────────────────────────────────
BOT_ATS = DeviceSignalProfile(
    name="bot_ats",
    description="Malware ATS — scripted, no real user interaction",
    pressure_range=(0.0, 0.0),
    typing_interval_ms_range=(0, 15),
    accel_magnitude_range=(0.0, 0.0),
    session_duration_s_range=(1, 8),
    confirm_latency_s_range=(0, 4),
    emulator_prob=0.90,
    rooted_prob=0.80,
    vpn_prob=0.70,
    active_call_prob=0.0,
    nav_anomaly_prob=0.95,
    multi_account_prob=0.70,
)

# ─────────────────────────────────────────────────────────────────────────────
# Profile: Coerced / Falsa Central
# Fingerprint: device in hand (accel ok), pressure high (tense grip),
#              active call, long confirm latency (being instructed)
# Maps to fraud rule: FALSA_CENTRAL
# ─────────────────────────────────────────────────────────────────────────────
COERCED_USER = DeviceSignalProfile(
    name="coerced_user",
    description="Victim under phone coercion — natural device signals but high pressure/slow confirmation",
    pressure_range=(0.75, 0.92),
    typing_interval_ms_range=(150, 600),
    accel_magnitude_range=(0.5, 3.0),
    session_duration_s_range=(120, 900),
    confirm_latency_s_range=(15, 120),
    emulator_prob=0.0,
    rooted_prob=0.01,
    vpn_prob=0.02,
    active_call_prob=0.90,
    nav_anomaly_prob=0.10,
    multi_account_prob=0.05,
)

# ─────────────────────────────────────────────────────────────────────────────
# Profile: Account Takeover (ATO)
# Fingerprint: new device, fast session (attacker knows exactly what to do),
#              no active call, small accel
# Maps to fraud rule: ATO
# ─────────────────────────────────────────────────────────────────────────────
ACCOUNT_TAKEOVER = DeviceSignalProfile(
    name="account_takeover",
    description="Attacker who stole credentials — fast methodical navigation, new device",
    pressure_range=(0.30, 0.55),
    typing_interval_ms_range=(30, 80),
    accel_magnitude_range=(0.05, 0.30),
    session_duration_s_range=(8, 25),
    confirm_latency_s_range=(2, 8),
    emulator_prob=0.15,
    rooted_prob=0.20,
    vpn_prob=0.60,
    active_call_prob=0.01,
    nav_anomaly_prob=0.50,
    multi_account_prob=0.30,
)

# ─────────────────────────────────────────────────────────────────────────────
# Profile: Money Mule (Conta Laranja)
# Fingerprint: real device but brand new account/device, multiple accounts
# Maps to fraud rule: CONTA_LARANJA
# ─────────────────────────────────────────────────────────────────────────────
MONEY_MULE = DeviceSignalProfile(
    name="money_mule",
    description="Money mule — real person, new account, coached behavior",
    pressure_range=(0.35, 0.60),
    typing_interval_ms_range=(100, 400),
    accel_magnitude_range=(0.2, 2.0),
    session_duration_s_range=(20, 120),
    confirm_latency_s_range=(5, 40),
    emulator_prob=0.05,
    rooted_prob=0.10,
    vpn_prob=0.25,
    active_call_prob=0.30,
    nav_anomaly_prob=0.25,
    multi_account_prob=0.80,
)


# ─── Registry ─────────────────────────────────────────────────────────────────

ALL_PROFILES: dict = {
    "normal_human":      NORMAL_HUMAN,
    "bot_ats":           BOT_ATS,
    "coerced_user":      COERCED_USER,
    "account_takeover":  ACCOUNT_TAKEOVER,
    "money_mule":        MONEY_MULE,
}

# Maps transaction fraud_type → most likely device profile
FRAUD_TYPE_TO_DEVICE_PROFILE: dict = {
    "MALWARE_ATS":          "bot_ats",
    "CARD_TESTING":         "bot_ats",
    "MICRO_BURST_VELOCITY": "bot_ats",
    "DISTRIBUTED_VELOCITY": "bot_ats",
    "ENGENHARIA_SOCIAL":    "coerced_user",
    "PIX_GOLPE":            "coerced_user",
    "CONTA_TOMADA":         "account_takeover",
    "CARTAO_CLONADO":       "account_takeover",
    "LAVAGEM_DINHEIRO":     "money_mule",
    "TRIANGULACAO":         "money_mule",
}


def get_device_profile(fraud_type: Optional[str] = None) -> DeviceSignalProfile:
    """Return the appropriate device profile for a fraud type, or normal_human."""
    if fraud_type and fraud_type in FRAUD_TYPE_TO_DEVICE_PROFILE:
        return ALL_PROFILES[FRAUD_TYPE_TO_DEVICE_PROFILE[fraud_type]]
    return NORMAL_HUMAN


def sample_device_signals(profile: DeviceSignalProfile, rng=None) -> dict:
    """
    Sample concrete device signal values from a profile's distributions.

    Returns a dict with keys matching the 17-signal schema used by score.py.
    """
    r = rng or random
    pressure = round(r.uniform(*profile.pressure_range), 4)
    typing_ms = r.randint(*profile.typing_interval_ms_range)
    accel = round(r.uniform(*profile.accel_magnitude_range), 4)
    session_s = r.randint(*profile.session_duration_s_range)
    confirm_s = r.randint(*profile.confirm_latency_s_range)

    return {
        "touch_pressure":        pressure,
        "typing_interval_ms":    typing_ms,
        "accel_magnitude":       accel,
        "session_duration_s":    session_s,
        "confirm_latency_s":     confirm_s,
        "is_emulator":           r.random() < profile.emulator_prob,
        "is_rooted":             r.random() < profile.rooted_prob,
        "is_vpn":                r.random() < profile.vpn_prob,
        "active_call":           r.random() < profile.active_call_prob,
        "nav_anomaly":           r.random() < profile.nav_anomaly_prob,
        "multiple_accounts":     r.random() < profile.multi_account_prob,
    }
