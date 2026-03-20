"""
Behavioral profiles for Brazilian Fraud Data Generator.

Profiles define realistic spending patterns for different customer archetypes.
Each profile influences:
- Preferred transaction types
- Typical merchants/MCCs
- Transaction frequency
- Value ranges
- Time patterns
- Channel preferences
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
from enum import Enum


class ProfileType(Enum):
    """Available behavioral profile types."""
    YOUNG_DIGITAL = "young_digital"
    TRADITIONAL_SENIOR = "traditional_senior"
    BUSINESS_OWNER = "business_owner"
    HIGH_SPENDER = "high_spender"
    SUBSCRIPTION_HEAVY = "subscription_heavy"
    FAMILY_PROVIDER = "family_provider"
    RANDOM = "random"  # No profile (random behavior)


@dataclass
class BehavioralProfile:
    """
    Defines a behavioral profile for a customer archetype.
    
    Each profile contains weighted preferences that influence
    how transactions are generated for customers with this profile.
    """
    name: str
    description: str
    
    # Age range (for customer generation)
    age_range: Tuple[int, int]
    
    # Income multiplier (relative to base income)
    income_multiplier: Tuple[float, float]
    
    # Preferred transaction types with weights
    transaction_types: Dict[str, int]
    
    # Preferred MCCs with weights
    preferred_mccs: Dict[str, int]
    
    # Channel preferences with weights
    channel_preferences: Dict[str, int]
    
    # Typical transaction frequency (transactions per month)
    monthly_tx_frequency: Tuple[int, int]
    
    # Typical transaction value range (BRL)
    typical_value_range: Tuple[float, float]
    
    # Preferred hours for transactions (24h format)
    preferred_hours: List[int]
    
    # Weekend activity multiplier (1.0 = same as weekday)
    weekend_multiplier: float = 1.0
    
    # Fraud susceptibility (higher = more likely target)
    fraud_susceptibility: float = 1.0


# Profile definitions
PROFILES: Dict[str, BehavioralProfile] = {
    ProfileType.YOUNG_DIGITAL.value: BehavioralProfile(
        name="young_digital",
        description="Young digital native: 18-30 years, very active on apps, streaming, delivery",
        age_range=(18, 30),
        income_multiplier=(0.5, 1.5),
        transaction_types={
            'PIX': 60,
            'CREDIT_CARD': 25,
            'DEBIT_CARD': 10,
            'AUTO_DEBIT': 5,
        },
        preferred_mccs={
            '5812': 20,       # Restaurants/Delivery
            '5812_delivery': 25,  # Delivery apps
            '5815': 20,       # Streaming/Digital
            '7941': 10,       # Gyms
            '4121': 15,       # Uber/99
            '5814': 10,       # Fast Food
        },
        channel_preferences={
            'MOBILE_APP': 85,
            'WEB_BANKING': 10,
            'WHATSAPP_PAY': 5,
        },
        monthly_tx_frequency=(40, 100),
        typical_value_range=(15, 300),
        # T1: janela estreita (3-5h) → picos mais nítidos + menor entropia
        preferred_hours=[12, 13, 19, 21, 22],
        weekend_multiplier=1.3,
        fraud_susceptibility=1.2,  # More susceptible to phishing/social engineering
    ),
    
    ProfileType.TRADITIONAL_SENIOR.value: BehavioralProfile(
        name="traditional_senior",
        description="Traditional senior: 55+ years, prefers branch/ATM, cautious",
        age_range=(55, 80),
        income_multiplier=(1.0, 3.0),  # Often retired with savings
        transaction_types={
            'PIX': 25,
            'CREDIT_CARD': 15,
            'DEBIT_CARD': 25,
            'BOLETO': 15,
            'WITHDRAWAL': 10,
            'TED': 10,
        },
        preferred_mccs={
            '5411': 25,       # Supermarkets
            '5912': 15,       # Pharmacies
            '8011': 10,       # Doctors
            '4900': 15,       # Utilities
            '4814': 10,       # Telecom
            '5499': 10,       # Convenience
            '6011': 15,       # Cash/ATM
        },
        channel_preferences={
            'MOBILE_APP': 30,
            'WEB_BANKING': 20,
            'ATM': 30,
            'BRANCH': 20,
        },
        monthly_tx_frequency=(15, 40),
        typical_value_range=(50, 800),
        # T1: matinal e pós-almoço (sênior não usa noite)
        preferred_hours=[9, 10, 15, 16],
        weekend_multiplier=0.6,  # Less active on weekends
        fraud_susceptibility=1.5,  # More susceptible to phone scams
    ),
    
    ProfileType.BUSINESS_OWNER.value: BehavioralProfile(
        name="business_owner",
        description="Business owner: 30-55 years, high volume, suppliers and services",
        age_range=(30, 55),
        income_multiplier=(2.0, 8.0),
        transaction_types={
            'PIX': 45,
            'TED': 20,
            'BOLETO': 15,
            'CREDIT_CARD': 15,
            'DEBIT_CARD': 5,
        },
        preferred_mccs={
            '5411': 10,       # Supermarkets
            '5541': 15,       # Gas
            '7011': 8,        # Hotels
            '4511': 8,        # Airlines
            '5732': 10,       # Electronics
            '4814': 10,       # Telecom
            '8299': 10,       # Education/Courses
            '5812': 15,       # Restaurants
            '4121': 14,       # Transport
        },
        channel_preferences={
            'MOBILE_APP': 60,
            'WEB_BANKING': 35,
            'ATM': 3,
            'BRANCH': 2,
        },
        monthly_tx_frequency=(50, 150),
        typical_value_range=(100, 5000),
        # T1: almoço comercial + fim do expediente
        preferred_hours=[12, 13, 18, 19],
        weekend_multiplier=0.4,  # Less business activity on weekends
        fraud_susceptibility=1.3,  # Targeted by business fraud
    ),
    
    ProfileType.HIGH_SPENDER.value: BehavioralProfile(
        name="high_spender",
        description="High net worth: 30-60 years, luxury, travel, high average ticket",
        age_range=(30, 60),
        income_multiplier=(5.0, 15.0),
        transaction_types={
            'CREDIT_CARD': 50,
            'PIX': 30,
            'DEBIT_CARD': 10,
            'TED': 10,
        },
        preferred_mccs={
            '5944': 10,       # Jewelry
            '5651': 15,       # Luxury clothing
            '7011': 15,       # Hotels
            '4511': 15,       # Airlines
            '5812': 15,       # Restaurants
            '5977': 10,       # Cosmetics
            '5732': 10,       # Electronics
            '5311': 10,       # Stores
        },
        channel_preferences={
            'MOBILE_APP': 70,
            'WEB_BANKING': 25,
            'ATM': 3,
            'BRANCH': 2,
        },
        monthly_tx_frequency=(30, 80),
        typical_value_range=(200, 10000),
        # T1: tarde/noite — compras de luxo e lazer
        preferred_hours=[15, 19, 20, 21],
        weekend_multiplier=1.5,  # More leisure spending on weekends
        fraud_susceptibility=1.4,  # High value target
    ),
    
    ProfileType.SUBSCRIPTION_HEAVY.value: BehavioralProfile(
        name="subscription_heavy",
        description="Digital subscriber: 22-45 years, many recurring subscriptions",
        age_range=(22, 45),
        income_multiplier=(1.0, 3.0),
        transaction_types={
            'AUTO_DEBIT': 35,
            'PIX': 35,
            'CREDIT_CARD': 25,
            'DEBIT_CARD': 5,
        },
        preferred_mccs={
            '5815': 35,       # Streaming/Digital
            '7941': 15,       # Gym
            '4814': 15,       # Telecom
            '5812': 15,       # Delivery
            '8299': 10,       # Online courses
            '5411': 10,       # Supermarkets
        },
        channel_preferences={
            'MOBILE_APP': 75,
            'WEB_BANKING': 20,
            'WHATSAPP_PAY': 5,
        },
        monthly_tx_frequency=(35, 70),
        typical_value_range=(10, 500),
        # T1: noite — streaming e assinaturas digitais
        preferred_hours=[20, 21, 22],
        weekend_multiplier=1.2,
        fraud_susceptibility=1.1,
    ),
    
    ProfileType.FAMILY_PROVIDER.value: BehavioralProfile(
        name="family_provider",
        description="Family provider: 30-55 years, supermarket, pharmacy, education",
        age_range=(30, 55),
        income_multiplier=(1.5, 4.0),
        transaction_types={
            'PIX': 40,
            'CREDIT_CARD': 30,
            'DEBIT_CARD': 15,
            'BOLETO': 10,
            'AUTO_DEBIT': 5,
        },
        preferred_mccs={
            '5411': 25,       # Supermarkets
            '5912': 10,       # Pharmacies
            '5995': 5,        # Pet Shop
            '8299': 10,       # Education
            '4900': 10,       # Utilities
            '5541': 10,       # Gas
            '5651': 10,       # Clothing
            '5814': 10,       # Fast Food
            '5499': 10,       # Convenience
        },
        channel_preferences={
            'MOBILE_APP': 65,
            'WEB_BANKING': 25,
            'ATM': 7,
            'BRANCH': 3,
        },
        monthly_tx_frequency=(60, 120),
        typical_value_range=(30, 1500),
        # T1: almoço em família + jantar/noite
        preferred_hours=[12, 18, 19, 20],
        weekend_multiplier=1.4,  # More family activity on weekends
        fraud_susceptibility=1.0,
    ),

    # ── Fraud victim archetypes (used by correlations/score pipeline) ──────

    "ato_victim": BehavioralProfile(
        name="ato_victim",
        description=(
            "Account Takeover victim: 35-65 years, light mobile users with dormant "
            "periods, passwords reused across services, account inactive for 1+ weeks"
        ),
        age_range=(35, 65),
        income_multiplier=(1.0, 3.0),
        transaction_types={
            'PIX': 35,
            'DEBIT_CARD': 30,
            'CREDIT_CARD': 20,
            'BOLETO': 10,
            'WITHDRAWAL': 5,
        },
        preferred_mccs={
            '5411': 30,   # Supermarkets
            '5912': 15,   # Pharmacies
            '4900': 15,   # Utilities
            '5814': 10,   # Fast Food
            '5541': 10,   # Gas
            '8011': 10,   # Health/doctors
            '6011': 10,   # ATM/withdrawals
        },
        channel_preferences={
            'MOBILE_APP': 40,
            'WEB_BANKING': 25,
            'ATM': 20,
            'BRANCH': 15,
        },
        monthly_tx_frequency=(10, 30),   # low frequency → dormant account pattern
        typical_value_range=(30, 600),
        preferred_hours=[9, 10, 15, 16, 18],
        weekend_multiplier=0.7,
        fraud_susceptibility=2.0,        # prime ATO target
    ),

    "falsa_central_victim": BehavioralProfile(
        name="falsa_central_victim",
        description=(
            "Golpe da falsa central victim: 55+ years, low digital literacy, "
            "trusts phone calls from 'bank employees', high susceptibility to social engineering"
        ),
        age_range=(55, 85),
        income_multiplier=(1.0, 4.0),   # often retirees with savings
        transaction_types={
            'PIX': 20,
            'TED': 15,
            'DEBIT_CARD': 30,
            'BOLETO': 15,
            'WITHDRAWAL': 15,
            'CREDIT_CARD': 5,
        },
        preferred_mccs={
            '5411': 30,   # Supermarkets
            '5912': 20,   # Pharmacies
            '8011': 15,   # Doctors
            '4900': 15,   # Utilities
            '6011': 15,   # ATM
            '5499': 5,    # Convenience
        },
        channel_preferences={
            'MOBILE_APP': 20,
            'WEB_BANKING': 15,
            'ATM': 35,
            'BRANCH': 30,
        },
        monthly_tx_frequency=(8, 25),
        typical_value_range=(50, 1000),
        preferred_hours=[9, 10, 11, 14, 15, 16],
        weekend_multiplier=0.5,
        fraud_susceptibility=2.5,        # highest susceptibility — prime falsa central target
    ),

    "malware_ats_victim": BehavioralProfile(
        name="malware_ats_victim",
        description=(
            "Malware/ATS victim: 18-45 years, high-risk app installer, "
            "rooted Android device, APK from untrusted sources, high digital activity"
        ),
        age_range=(18, 45),
        income_multiplier=(0.5, 2.5),
        transaction_types={
            'PIX': 65,
            'CREDIT_CARD': 20,
            'DEBIT_CARD': 10,
            'AUTO_DEBIT': 5,
        },
        preferred_mccs={
            '5812': 15,       # Delivery
            '5815': 20,       # Streaming
            '4121': 15,       # Rideshare
            '5814': 10,       # Fast food
            '7941': 10,       # Gyms
            '5732': 15,       # Electronics/apps
            '8299': 15,       # Online courses
        },
        channel_preferences={
            'MOBILE_APP': 95,   # exclusively mobile — device compromise is effective
            'WEB_BANKING': 4,
            'WHATSAPP_PAY': 1,
        },
        monthly_tx_frequency=(50, 120),  # high digital activity = more exposure
        typical_value_range=(10, 500),
        preferred_hours=[19, 20, 21, 22, 23],  # evening sideload sessions
        weekend_multiplier=1.4,
        fraud_susceptibility=1.8,
    ),
}


# Profile distribution weights for automatic assignment
# Fraud victim archetypes receive low weights — they exist for targeted fraud injection,
# not for the general population baseline.
PROFILE_DISTRIBUTION = {
    ProfileType.YOUNG_DIGITAL.value: 25,
    ProfileType.TRADITIONAL_SENIOR.value: 15,
    ProfileType.BUSINESS_OWNER.value: 10,
    ProfileType.HIGH_SPENDER.value: 8,
    ProfileType.SUBSCRIPTION_HEAVY.value: 20,
    ProfileType.FAMILY_PROVIDER.value: 22,
    # Fraud victim archetypes (low base weight; boosted by fraud injection logic)
    "ato_victim": 0,
    "falsa_central_victim": 0,
    "malware_ats_victim": 0,
}

PROFILE_LIST = list(PROFILE_DISTRIBUTION.keys())
PROFILE_WEIGHTS = list(PROFILE_DISTRIBUTION.values())


# ── Pre-built WeightCaches for profile distributions ────────────
# Eliminates repeated list() + random.choices() overhead per call.
from ..utils.weight_cache import WeightCache

_profile_tx_type_caches: Dict[str, WeightCache] = {}
_profile_mcc_caches: Dict[str, WeightCache] = {}
_profile_channel_caches: Dict[str, WeightCache] = {}

for _pname, _prof in PROFILES.items():
    _profile_tx_type_caches[_pname] = WeightCache(
        list(_prof.transaction_types.keys()),
        list(_prof.transaction_types.values()),
    )
    _profile_mcc_caches[_pname] = WeightCache(
        list(_prof.preferred_mccs.keys()),
        list(_prof.preferred_mccs.values()),
    )
    _profile_channel_caches[_pname] = WeightCache(
        list(_prof.channel_preferences.keys()),
        list(_prof.channel_preferences.values()),
    )

_profile_assign_cache = WeightCache(PROFILE_LIST, PROFILE_WEIGHTS)


def get_profile(profile_name: str) -> Optional[BehavioralProfile]:
    """Get a behavioral profile by name."""
    return PROFILES.get(profile_name)


def assign_random_profile() -> str:
    """Assign a random profile based on distribution weights."""
    return _profile_assign_cache.sample()


def get_transaction_type_for_profile(profile_name: str) -> str:
    """Get a weighted random transaction type for a profile."""
    cache = _profile_tx_type_caches.get(profile_name)
    if cache:
        return cache.sample()
    # Fallback to default distribution
    from ..config.transactions import TX_TYPES_LIST, TX_TYPES_WEIGHTS
    return random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)[0]


def get_mcc_for_profile(profile_name: str) -> str:
    """Get a weighted random MCC for a profile."""
    cache = _profile_mcc_caches.get(profile_name)
    if cache:
        return cache.sample()
    # Fallback to default distribution
    from ..config.merchants import MCC_LIST, MCC_WEIGHTS
    return random.choices(MCC_LIST, weights=MCC_WEIGHTS)[0]


def get_channel_for_profile(profile_name: str) -> str:
    """Get a weighted random channel for a profile."""
    cache = _profile_channel_caches.get(profile_name)
    if cache:
        return cache.sample()
    from ..config.transactions import CHANNELS_LIST, CHANNELS_WEIGHTS
    return random.choices(CHANNELS_LIST, weights=CHANNELS_WEIGHTS)[0]


def get_transaction_hour_for_profile(profile_name: str, is_weekend: bool = False) -> int:
    """Get a realistic transaction hour for a profile.

    T1: fallback usa distribui\u00e7\u00e3o trimodal (picos 12h, 18h, 21h) em vez de uniforme.
    """
    from ..config.seasonality import pick_hour, HORA_WEIGHTS_PADRAO

    profile = PROFILES.get(profile_name)

    if not profile:
        # T1: distribui\u00e7\u00e3o trimodal realista (Br 2024)
        return pick_hour(HORA_WEIGHTS_PADRAO)

    # T1: usa HORA_WEIGHTS_PADRAO para ponderar mesmo dentro das horas preferenciais
    # (antes: random.choice(preferred) distribuía uniformemente → alta entropia)
    preferred = profile.preferred_hours
    w_preferred = [HORA_WEIGHTS_PADRAO[h] for h in preferred]

    # 70% dentro das horas preferenciais (ponderadas por trimodal), 30% trimodal livre
    if random.random() < 0.7 and preferred:
        hour = random.choices(preferred, weights=w_preferred, k=1)[0]
    else:
        # T1: sempre usa distribuição trimodal mesmo fora do horário preferido
        hour = pick_hour(HORA_WEIGHTS_PADRAO)

    return hour


def get_transaction_value_for_profile(
    profile_name: str,
    mcc_value_range: Tuple[float, float] = (10, 1000)
) -> float:
    """
    Get a realistic transaction value for a profile.
    
    Considers both profile preferences and MCC typical values.
    """
    profile = PROFILES.get(profile_name)
    
    if not profile:
        # Log-normal calibrado pelo range MCC (sem pile-up nos limites)
        valor_min, valor_max = mcc_value_range
        mu = (math.log(max(valor_min, 0.01)) + math.log(valor_max)) / 2
        sigma = max((math.log(valor_max) - math.log(max(valor_min, 0.01))) / 4, 0.30)
        value = math.exp(random.gauss(mu, sigma))
        return round(max(valor_min, min(value, valor_max * 2.0)), 2)

    # Blend profile and MCC ranges
    profile_min, profile_max = profile.typical_value_range
    mcc_min, mcc_max = mcc_value_range

    final_min = max(profile_min, mcc_min * 0.5)
    final_max = min(profile_max, mcc_max * 1.5)

    if final_min >= final_max:
        final_min, final_max = mcc_value_range

    # Log-normal calibrado pelo range combinado perfil × MCC
    mu = (math.log(max(final_min, 0.01)) + math.log(final_max)) / 2
    sigma = max((math.log(final_max) - math.log(max(final_min, 0.01))) / 4, 0.30)
    value = math.exp(random.gauss(mu, sigma))
    return round(max(final_min, min(value, final_max * 2.0)), 2)


def get_monthly_transactions_for_profile(profile_name: str) -> int:
    """Get expected monthly transaction count for a profile."""
    profile = PROFILES.get(profile_name)
    if not profile:
        return random.randint(20, 60)
    
    min_tx, max_tx = profile.monthly_tx_frequency
    return random.randint(min_tx, max_tx)


def should_transact_on_weekend(profile_name: str) -> bool:
    """Determine if a transaction should happen on weekend based on profile."""
    profile = PROFILES.get(profile_name)
    if not profile:
        return random.random() < 0.5
    
    # Higher multiplier = more weekend activity
    return random.random() < (profile.weekend_multiplier / 2)
