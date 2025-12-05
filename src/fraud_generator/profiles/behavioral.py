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
        description="Jovem digital: 18-30 anos, muito ativo em apps, streaming, delivery",
        age_range=(18, 30),
        income_multiplier=(0.5, 1.5),
        transaction_types={
            'PIX': 60,
            'CARTAO_CREDITO': 25,
            'CARTAO_DEBITO': 10,
            'DEBITO_AUTOMATICO': 5,
        },
        preferred_mccs={
            '5812': 20,       # Restaurantes/Delivery
            '5812_delivery': 25,  # Apps de delivery
            '5815': 20,       # Streaming/Digital
            '7941': 10,       # Academias
            '4121': 15,       # Uber/99
            '5814': 10,       # Fast Food
        },
        channel_preferences={
            'APP_MOBILE': 85,
            'WEB_BANKING': 10,
            'WHATSAPP_PAY': 5,
        },
        monthly_tx_frequency=(40, 100),
        typical_value_range=(15, 300),
        preferred_hours=[10, 11, 12, 13, 14, 18, 19, 20, 21, 22, 23],
        weekend_multiplier=1.3,
        fraud_susceptibility=1.2,  # More susceptible to phishing/social engineering
    ),
    
    ProfileType.TRADITIONAL_SENIOR.value: BehavioralProfile(
        name="traditional_senior",
        description="Sênior tradicional: 55+ anos, prefere agência/ATM, cauteloso",
        age_range=(55, 80),
        income_multiplier=(1.0, 3.0),  # Often retired with savings
        transaction_types={
            'PIX': 25,
            'CARTAO_CREDITO': 15,
            'CARTAO_DEBITO': 25,
            'BOLETO': 15,
            'SAQUE': 10,
            'TED': 10,
        },
        preferred_mccs={
            '5411': 25,       # Supermercados
            '5912': 15,       # Farmácias
            '8011': 10,       # Médicos
            '4900': 15,       # Utilidades
            '4814': 10,       # Telecom
            '5499': 10,       # Conveniência
            '6011': 15,       # Saque/ATM
        },
        channel_preferences={
            'APP_MOBILE': 30,
            'WEB_BANKING': 20,
            'ATM': 30,
            'AGENCIA': 20,
        },
        monthly_tx_frequency=(15, 40),
        typical_value_range=(50, 800),
        preferred_hours=[8, 9, 10, 11, 14, 15, 16, 17],
        weekend_multiplier=0.6,  # Less active on weekends
        fraud_susceptibility=1.5,  # More susceptible to phone scams
    ),
    
    ProfileType.BUSINESS_OWNER.value: BehavioralProfile(
        name="business_owner",
        description="Empreendedor: 30-55 anos, alto volume, fornecedores e serviços",
        age_range=(30, 55),
        income_multiplier=(2.0, 8.0),
        transaction_types={
            'PIX': 45,
            'TED': 20,
            'BOLETO': 15,
            'CARTAO_CREDITO': 15,
            'CARTAO_DEBITO': 5,
        },
        preferred_mccs={
            '5411': 10,       # Supermercados
            '5541': 15,       # Combustível
            '7011': 8,        # Hotéis
            '4511': 8,        # Aéreo
            '5732': 10,       # Eletrônicos
            '4814': 10,       # Telecom
            '8299': 10,       # Educação/Cursos
            '5812': 15,       # Restaurantes
            '4121': 14,       # Transporte
        },
        channel_preferences={
            'APP_MOBILE': 60,
            'WEB_BANKING': 35,
            'ATM': 3,
            'AGENCIA': 2,
        },
        monthly_tx_frequency=(50, 150),
        typical_value_range=(100, 5000),
        preferred_hours=[8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20],
        weekend_multiplier=0.4,  # Less business activity on weekends
        fraud_susceptibility=1.3,  # Targeted by business fraud
    ),
    
    ProfileType.HIGH_SPENDER.value: BehavioralProfile(
        name="high_spender",
        description="Alto poder aquisitivo: 30-60 anos, luxo, viagens, alto ticket médio",
        age_range=(30, 60),
        income_multiplier=(5.0, 15.0),
        transaction_types={
            'CARTAO_CREDITO': 50,
            'PIX': 30,
            'CARTAO_DEBITO': 10,
            'TED': 10,
        },
        preferred_mccs={
            '5944': 10,       # Joalherias
            '5651': 15,       # Vestuário luxo
            '7011': 15,       # Hotéis
            '4511': 15,       # Aéreo
            '5812': 15,       # Restaurantes
            '5977': 10,       # Cosméticos
            '5732': 10,       # Eletrônicos
            '5311': 10,       # Lojas
        },
        channel_preferences={
            'APP_MOBILE': 70,
            'WEB_BANKING': 25,
            'ATM': 3,
            'AGENCIA': 2,
        },
        monthly_tx_frequency=(30, 80),
        typical_value_range=(200, 10000),
        preferred_hours=[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
        weekend_multiplier=1.5,  # More leisure spending on weekends
        fraud_susceptibility=1.4,  # High value target
    ),
    
    ProfileType.SUBSCRIPTION_HEAVY.value: BehavioralProfile(
        name="subscription_heavy",
        description="Assinante digital: 22-45 anos, muitas assinaturas recorrentes",
        age_range=(22, 45),
        income_multiplier=(1.0, 3.0),
        transaction_types={
            'DEBITO_AUTOMATICO': 35,
            'PIX': 35,
            'CARTAO_CREDITO': 25,
            'CARTAO_DEBITO': 5,
        },
        preferred_mccs={
            '5815': 35,       # Streaming/Digital
            '7941': 15,       # Academia
            '4814': 15,       # Telecom
            '5812': 15,       # Delivery
            '8299': 10,       # Cursos online
            '5411': 10,       # Supermercados
        },
        channel_preferences={
            'APP_MOBILE': 75,
            'WEB_BANKING': 20,
            'WHATSAPP_PAY': 5,
        },
        monthly_tx_frequency=(35, 70),
        typical_value_range=(10, 500),
        preferred_hours=[6, 7, 8, 18, 19, 20, 21, 22, 23],
        weekend_multiplier=1.2,
        fraud_susceptibility=1.1,
    ),
    
    ProfileType.FAMILY_PROVIDER.value: BehavioralProfile(
        name="family_provider",
        description="Provedor familiar: 30-55 anos, supermercado, farmácia, educação",
        age_range=(30, 55),
        income_multiplier=(1.5, 4.0),
        transaction_types={
            'PIX': 40,
            'CARTAO_CREDITO': 30,
            'CARTAO_DEBITO': 15,
            'BOLETO': 10,
            'DEBITO_AUTOMATICO': 5,
        },
        preferred_mccs={
            '5411': 25,       # Supermercados
            '5912': 10,       # Farmácias
            '5995': 5,        # Pet Shop
            '8299': 10,       # Educação
            '4900': 10,       # Utilidades
            '5541': 10,       # Combustível
            '5651': 10,       # Vestuário
            '5814': 10,       # Fast Food
            '5499': 10,       # Conveniência
        },
        channel_preferences={
            'APP_MOBILE': 65,
            'WEB_BANKING': 25,
            'ATM': 7,
            'AGENCIA': 3,
        },
        monthly_tx_frequency=(60, 120),
        typical_value_range=(30, 1500),
        preferred_hours=[7, 8, 9, 12, 13, 17, 18, 19, 20, 21],
        weekend_multiplier=1.4,  # More family activity on weekends
        fraud_susceptibility=1.0,
    ),
}


# Profile distribution weights for automatic assignment
PROFILE_DISTRIBUTION = {
    ProfileType.YOUNG_DIGITAL.value: 25,
    ProfileType.TRADITIONAL_SENIOR.value: 15,
    ProfileType.BUSINESS_OWNER.value: 10,
    ProfileType.HIGH_SPENDER.value: 8,
    ProfileType.SUBSCRIPTION_HEAVY.value: 20,
    ProfileType.FAMILY_PROVIDER.value: 22,
}

PROFILE_LIST = list(PROFILE_DISTRIBUTION.keys())
PROFILE_WEIGHTS = list(PROFILE_DISTRIBUTION.values())


def get_profile(profile_name: str) -> Optional[BehavioralProfile]:
    """Get a behavioral profile by name."""
    return PROFILES.get(profile_name)


def assign_random_profile() -> str:
    """Assign a random profile based on distribution weights."""
    return random.choices(PROFILE_LIST, weights=PROFILE_WEIGHTS)[0]


def get_transaction_type_for_profile(profile_name: str) -> str:
    """Get a weighted random transaction type for a profile."""
    profile = PROFILES.get(profile_name)
    if not profile:
        # Fallback to default distribution
        from ..config.transactions import TX_TYPES_LIST, TX_TYPES_WEIGHTS
        return random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)[0]
    
    types = list(profile.transaction_types.keys())
    weights = list(profile.transaction_types.values())
    return random.choices(types, weights=weights)[0]


def get_mcc_for_profile(profile_name: str) -> str:
    """Get a weighted random MCC for a profile."""
    profile = PROFILES.get(profile_name)
    if not profile:
        # Fallback to default distribution
        from ..config.merchants import MCC_LIST, MCC_WEIGHTS
        return random.choices(MCC_LIST, weights=MCC_WEIGHTS)[0]
    
    mccs = list(profile.preferred_mccs.keys())
    weights = list(profile.preferred_mccs.values())
    return random.choices(mccs, weights=weights)[0]


def get_channel_for_profile(profile_name: str) -> str:
    """Get a weighted random channel for a profile."""
    profile = PROFILES.get(profile_name)
    if not profile:
        from ..config.transactions import CHANNELS_LIST, CHANNELS_WEIGHTS
        return random.choices(CHANNELS_LIST, weights=CHANNELS_WEIGHTS)[0]
    
    channels = list(profile.channel_preferences.keys())
    weights = list(profile.channel_preferences.values())
    return random.choices(channels, weights=weights)[0]


def get_transaction_hour_for_profile(profile_name: str, is_weekend: bool = False) -> int:
    """Get a realistic transaction hour for a profile."""
    profile = PROFILES.get(profile_name)
    
    if not profile:
        # Default hour distribution
        hour_weights = {
            0: 2, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2,
            6: 4, 7: 6, 8: 10, 9: 12, 10: 14, 11: 14,
            12: 15, 13: 14, 14: 13, 15: 12, 16: 12, 17: 13,
            18: 14, 19: 15, 20: 14, 21: 12, 22: 8, 23: 4
        }
        hours = list(hour_weights.keys())
        weights = list(hour_weights.values())
        return random.choices(hours, weights=weights)[0]
    
    # Prefer profile's preferred hours
    preferred = profile.preferred_hours
    other_hours = [h for h in range(24) if h not in preferred]
    
    # 70% chance of preferred hour, 30% other
    if random.random() < 0.7 and preferred:
        hour = random.choice(preferred)
    else:
        hour = random.choice(other_hours) if other_hours else random.choice(preferred)
    
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
        # Use MCC range directly
        valor_min, valor_max = mcc_value_range
        mean = (valor_min + valor_max) / 3
        return round(min(max(random.gauss(mean, mean/2), valor_min), valor_max), 2)
    
    # Blend profile and MCC ranges
    profile_min, profile_max = profile.typical_value_range
    mcc_min, mcc_max = mcc_value_range
    
    # Use overlapping range or profile range
    final_min = max(profile_min, mcc_min * 0.5)
    final_max = min(profile_max, mcc_max * 1.5)
    
    if final_min >= final_max:
        final_min, final_max = mcc_value_range
    
    # Log-normal distribution for more realistic values
    mean = (final_min + final_max) / 3
    value = random.gauss(mean, mean / 2)
    return round(min(max(value, final_min), final_max), 2)


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
