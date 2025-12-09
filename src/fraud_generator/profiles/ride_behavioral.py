"""
Behavioral profiles for Rideshare in Brazilian Fraud Data Generator.

Profiles define realistic ride patterns for different passenger archetypes.
Each profile influences:
- Preferred apps and categories
- Ride frequency
- Time patterns
- POI types (pickup/dropoff)
- Price sensitivity
- Tip behavior
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
from enum import Enum


class RideProfileType(Enum):
    """Available ride behavioral profile types."""
    DAILY_COMMUTER = "daily_commuter"
    OCCASIONAL_USER = "occasional_user"
    FREQUENT_TRAVELER = "frequent_traveler"
    NIGHTLIFE = "nightlife"
    BUSINESS = "business"
    ECONOMY_FOCUSED = "economy_focused"
    RANDOM = "random"  # No profile (random behavior)


@dataclass
class RideBehavioralProfile:
    """
    Defines a behavioral profile for rideshare passengers.
    
    Each profile contains weighted preferences that influence
    how rides are generated for passengers with this profile.
    """
    name: str
    description: str
    
    # Preferred apps with weights
    preferred_apps: Dict[str, int]
    
    # Preferred categories with weights
    preferred_categories: Dict[str, int]
    
    # Rides per week range
    rides_per_week: Tuple[int, int]
    
    # Preferred hours for rides (24h format)
    preferred_hours: List[int]
    
    # Preferred days of week (0=Monday, 6=Sunday)
    preferred_days: List[int]
    
    # Preferred POI types for pickup
    preferred_pickup_pois: Dict[str, int]
    
    # Preferred POI types for dropoff
    preferred_dropoff_pois: Dict[str, int]
    
    # Maximum acceptable surge multiplier (will cancel if higher)
    max_acceptable_surge: float
    
    # Tip probability (0.0 to 1.0)
    tip_probability: float
    
    # Tip percentage range (of final fare)
    tip_percentage_range: Tuple[float, float]
    
    # Price sensitivity (higher = more likely to cancel on high prices)
    price_sensitivity: float = 1.0
    
    # Fraud susceptibility (higher = more likely target)
    fraud_susceptibility: float = 1.0


# =============================================================================
# RIDE PROFILE DEFINITIONS
# =============================================================================

RIDE_PROFILES: Dict[str, RideBehavioralProfile] = {
    RideProfileType.DAILY_COMMUTER.value: RideBehavioralProfile(
        name="daily_commuter",
        description="Commuter diário: 2x/dia em dias úteis, horários fixos, casa↔trabalho",
        preferred_apps={
            'UBER': 40,
            '99': 40,
            'CABIFY': 10,
            'INDRIVER': 10,
        },
        preferred_categories={
            'UberX': 35,
            'Pop': 35,
            'Lite': 15,
            'Economy': 15,
        },
        rides_per_week=(8, 12),  # ~2x per workday
        preferred_hours=[7, 8, 9, 17, 18, 19],  # Rush hours
        preferred_days=[0, 1, 2, 3, 4],  # Monday-Friday
        preferred_pickup_pois={
            'CENTRO_EMPRESARIAL': 40,
            'SHOPPING': 20,
            'UNIVERSIDADE': 20,
            'RODOVIARIA': 10,
            'HOSPITAL': 10,
        },
        preferred_dropoff_pois={
            'CENTRO_EMPRESARIAL': 40,
            'SHOPPING': 20,
            'UNIVERSIDADE': 15,
            'RODOVIARIA': 15,
            'HOSPITAL': 10,
        },
        max_acceptable_surge=1.8,
        tip_probability=0.10,
        tip_percentage_range=(0.05, 0.10),
        price_sensitivity=1.2,  # Somewhat price sensitive
        fraud_susceptibility=0.8,  # Low fraud risk
    ),
    
    RideProfileType.OCCASIONAL_USER.value: RideBehavioralProfile(
        name="occasional_user",
        description="Usuário ocasional: 2-4x/semana, shoppings, lazer, horários variados",
        preferred_apps={
            'UBER': 45,
            '99': 35,
            'CABIFY': 10,
            'INDRIVER': 10,
        },
        preferred_categories={
            'UberX': 40,
            'Pop': 35,
            'Comfort': 15,
            '99Comfort': 10,
        },
        rides_per_week=(2, 4),
        preferred_hours=[10, 11, 12, 14, 15, 16, 19, 20, 21],  # Variable
        preferred_days=[0, 1, 2, 3, 4, 5, 6],  # All days
        preferred_pickup_pois={
            'SHOPPING': 30,
            'PARQUE': 20,
            'CENTRO_HISTORICO': 15,
            'PRAIA': 15,
            'ESTADIO': 10,
            'FEIRA': 10,
        },
        preferred_dropoff_pois={
            'SHOPPING': 30,
            'PARQUE': 20,
            'CENTRO_HISTORICO': 15,
            'PRAIA': 15,
            'ESTADIO': 10,
            'MERCADO': 10,
        },
        max_acceptable_surge=2.0,
        tip_probability=0.15,
        tip_percentage_range=(0.10, 0.15),
        price_sensitivity=1.0,
        fraud_susceptibility=1.0,
    ),
    
    RideProfileType.FREQUENT_TRAVELER.value: RideBehavioralProfile(
        name="frequent_traveler",
        description="Viajante frequente: aeroportos, hotéis, categorias comfort+",
        preferred_apps={
            'UBER': 50,
            '99': 25,
            'CABIFY': 20,
            'INDRIVER': 5,
        },
        preferred_categories={
            'Comfort': 35,
            '99Comfort': 20,
            'Black': 25,
            'Cabify': 15,
            'Plus': 5,
        },
        rides_per_week=(4, 8),
        preferred_hours=[5, 6, 7, 8, 18, 19, 20, 21, 22],  # Flight times
        preferred_days=[0, 1, 2, 3, 4, 6],  # Mostly weekdays + Sunday
        preferred_pickup_pois={
            'AEROPORTO': 50,
            'HOTEL': 25,
            'CENTRO_EMPRESARIAL': 15,
            'RODOVIARIA': 10,
        },
        preferred_dropoff_pois={
            'AEROPORTO': 40,
            'HOTEL': 30,
            'CENTRO_EMPRESARIAL': 20,
            'SHOPPING': 10,
        },
        max_acceptable_surge=2.5,  # Will pay surge for flights
        tip_probability=0.30,
        tip_percentage_range=(0.15, 0.25),
        price_sensitivity=0.5,  # Less price sensitive
        fraud_susceptibility=1.2,  # Higher value target
    ),
    
    RideProfileType.NIGHTLIFE.value: RideBehavioralProfile(
        name="nightlife",
        description="Vida noturna: sex-dom 22h-04h, bares, baladas, aceita surge alto",
        preferred_apps={
            'UBER': 40,
            '99': 40,
            'INDRIVER': 15,
            'CABIFY': 5,
        },
        preferred_categories={
            'UberX': 40,
            'Pop': 40,
            'Economy': 15,
            'Lite': 5,
        },
        rides_per_week=(3, 6),
        preferred_hours=[22, 23, 0, 1, 2, 3, 4],  # Night hours
        preferred_days=[4, 5, 6],  # Friday, Saturday, Sunday
        preferred_pickup_pois={
            'SHOPPING': 20,
            'CENTRO_HISTORICO': 30,
            'PRAIA': 25,
            'ESTADIO': 15,
            'PARQUE': 10,
        },
        preferred_dropoff_pois={
            'SHOPPING': 15,
            'CENTRO_HISTORICO': 35,
            'PRAIA': 25,
            'ESTADIO': 15,
            'HOTEL': 10,
        },
        max_acceptable_surge=3.0,  # Will pay high surge at night
        tip_probability=0.20,
        tip_percentage_range=(0.10, 0.20),
        price_sensitivity=0.7,  # Less sensitive when partying
        fraud_susceptibility=1.5,  # Higher risk due to late hours
    ),
    
    RideProfileType.BUSINESS.value: RideBehavioralProfile(
        name="business",
        description="Executivo: horário comercial, categorias premium, gorjeta alta",
        preferred_apps={
            'UBER': 50,
            'CABIFY': 30,
            '99': 15,
            'INDRIVER': 5,
        },
        preferred_categories={
            'Black': 40,
            'Comfort': 30,
            'Plus': 15,
            'Cabify': 15,
        },
        rides_per_week=(6, 15),
        preferred_hours=[7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19],
        preferred_days=[0, 1, 2, 3, 4],  # Weekdays only
        preferred_pickup_pois={
            'CENTRO_EMPRESARIAL': 40,
            'AEROPORTO': 25,
            'HOTEL': 20,
            'SHOPPING': 10,
            'UNIVERSIDADE': 5,
        },
        preferred_dropoff_pois={
            'CENTRO_EMPRESARIAL': 40,
            'AEROPORTO': 25,
            'HOTEL': 15,
            'SHOPPING': 15,
            'RODOVIARIA': 5,
        },
        max_acceptable_surge=2.5,
        tip_probability=0.40,  # High tip rate
        tip_percentage_range=(0.15, 0.25),
        price_sensitivity=0.3,  # Not price sensitive
        fraud_susceptibility=1.3,  # High value target
    ),
    
    RideProfileType.ECONOMY_FOCUSED.value: RideBehavioralProfile(
        name="economy_focused",
        description="Econômico: sempre Pop/UberX, sensível a preço, sem gorjeta",
        preferred_apps={
            '99': 40,
            'INDRIVER': 30,  # Negotiable prices
            'UBER': 25,
            'CABIFY': 5,
        },
        preferred_categories={
            'Pop': 40,
            'Economy': 30,
            'UberX': 20,
            'Lite': 10,
        },
        rides_per_week=(2, 5),
        preferred_hours=[9, 10, 11, 14, 15, 16, 17],  # Avoid surge hours
        preferred_days=[0, 1, 2, 3, 4, 5, 6],
        preferred_pickup_pois={
            'TERMINAL_ONIBUS': 25,
            'RODOVIARIA': 20,
            'SHOPPING': 20,
            'MERCADO': 15,
            'FEIRA': 10,
            'HOSPITAL': 10,
        },
        preferred_dropoff_pois={
            'TERMINAL_ONIBUS': 25,
            'RODOVIARIA': 20,
            'SHOPPING': 20,
            'MERCADO': 15,
            'FEIRA': 10,
            'HOSPITAL': 10,
        },
        max_acceptable_surge=1.3,  # Will cancel on surge
        tip_probability=0.05,  # Rarely tips
        tip_percentage_range=(0.05, 0.10),
        price_sensitivity=2.0,  # Very price sensitive
        fraud_susceptibility=0.9,
    ),
}


# =============================================================================
# CUSTOMER PROFILE MAPPING
# =============================================================================

# Maps existing customer behavioral profiles to ride profiles
CUSTOMER_TO_RIDE_PROFILE: Dict[str, List[str]] = {
    'young_digital': [
        RideProfileType.NIGHTLIFE.value,
        RideProfileType.ECONOMY_FOCUSED.value,
    ],
    'high_spender': [
        RideProfileType.BUSINESS.value,
        RideProfileType.FREQUENT_TRAVELER.value,
    ],
    'business_owner': [
        RideProfileType.BUSINESS.value,
        RideProfileType.FREQUENT_TRAVELER.value,
    ],
    'traditional_senior': [
        RideProfileType.OCCASIONAL_USER.value,
    ],
    'family_provider': [
        RideProfileType.DAILY_COMMUTER.value,
        RideProfileType.OCCASIONAL_USER.value,
    ],
    'subscription_heavy': [
        RideProfileType.DAILY_COMMUTER.value,
        RideProfileType.ECONOMY_FOCUSED.value,
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_ride_profile(profile_name: str) -> Optional[RideBehavioralProfile]:
    """
    Get a ride profile by name.
    
    Args:
        profile_name: Profile name (e.g., 'daily_commuter')
    
    Returns:
        RideBehavioralProfile or None if not found
    """
    return RIDE_PROFILES.get(profile_name)


def get_ride_profile_for_customer(customer_profile: Optional[str]) -> RideProfileType:
    """
    Get a ride profile type based on customer's behavioral profile.
    
    If customer_profile is not mapped, returns a random ride profile.
    
    Args:
        customer_profile: Customer's behavioral profile name
    
    Returns:
        RideProfileType enum value
    """
    if customer_profile and customer_profile in CUSTOMER_TO_RIDE_PROFILE:
        # Get mapped ride profiles and choose one randomly
        ride_profiles = CUSTOMER_TO_RIDE_PROFILE[customer_profile]
        chosen = random.choice(ride_profiles)
        return RideProfileType(chosen)
    
    # No mapping found, return random
    return assign_random_ride_profile()


def assign_random_ride_profile() -> RideProfileType:
    """
    Assign a random ride profile with weighted distribution.
    
    Returns:
        RideProfileType enum value
    """
    profiles = [
        RideProfileType.DAILY_COMMUTER,
        RideProfileType.OCCASIONAL_USER,
        RideProfileType.FREQUENT_TRAVELER,
        RideProfileType.NIGHTLIFE,
        RideProfileType.BUSINESS,
        RideProfileType.ECONOMY_FOCUSED,
    ]
    
    # Weights based on expected population distribution
    weights = [
        25,  # DAILY_COMMUTER - common
        30,  # OCCASIONAL_USER - most common
        10,  # FREQUENT_TRAVELER - less common
        15,  # NIGHTLIFE - moderate
        10,  # BUSINESS - less common
        10,  # ECONOMY_FOCUSED - moderate
    ]
    
    return random.choices(profiles, weights=weights, k=1)[0]


def get_preferred_app_for_profile(profile_name: str) -> str:
    """
    Get a weighted random app for a ride profile.
    
    Args:
        profile_name: Profile name
    
    Returns:
        App name string
    """
    profile = RIDE_PROFILES.get(profile_name)
    if not profile:
        return 'UBER'
    
    apps = list(profile.preferred_apps.keys())
    weights = list(profile.preferred_apps.values())
    return random.choices(apps, weights=weights, k=1)[0]


def get_preferred_category_for_profile(profile_name: str) -> str:
    """
    Get a weighted random category for a ride profile.
    
    Args:
        profile_name: Profile name
    
    Returns:
        Category name string
    """
    profile = RIDE_PROFILES.get(profile_name)
    if not profile:
        return 'UberX'
    
    categories = list(profile.preferred_categories.keys())
    weights = list(profile.preferred_categories.values())
    return random.choices(categories, weights=weights, k=1)[0]


def get_preferred_hour_for_profile(profile_name: str) -> int:
    """
    Get a weighted random hour for a ride profile.
    
    Args:
        profile_name: Profile name
    
    Returns:
        Hour (0-23)
    """
    profile = RIDE_PROFILES.get(profile_name)
    if not profile or not profile.preferred_hours:
        return random.randint(6, 23)
    
    return random.choice(profile.preferred_hours)


def should_tip_for_profile(profile_name: str) -> bool:
    """
    Determine if passenger should tip based on profile.
    
    Args:
        profile_name: Profile name
    
    Returns:
        True if should tip
    """
    profile = RIDE_PROFILES.get(profile_name)
    if not profile:
        return random.random() < 0.15  # Default 15%
    
    return random.random() < profile.tip_probability


def get_tip_percentage_for_profile(profile_name: str) -> float:
    """
    Get tip percentage for a profile.
    
    Args:
        profile_name: Profile name
    
    Returns:
        Tip percentage (0.0 to 1.0)
    """
    profile = RIDE_PROFILES.get(profile_name)
    if not profile:
        return random.uniform(0.10, 0.15)
    
    return random.uniform(*profile.tip_percentage_range)


def should_accept_surge_for_profile(profile_name: str, surge: float) -> bool:
    """
    Determine if passenger would accept a given surge multiplier.
    
    Args:
        profile_name: Profile name
        surge: Surge multiplier
    
    Returns:
        True if would accept the surge
    """
    profile = RIDE_PROFILES.get(profile_name)
    if not profile:
        return surge <= 2.0  # Default max
    
    return surge <= profile.max_acceptable_surge
