"""
Configuration module for rideshare data generation.
Contains apps, POIs, vehicles, rates, and fraud types for ride-sharing services.
"""

import random
from typing import Dict, List, Any, Optional

# =============================================================================
# RIDESHARE APPS
# =============================================================================

RIDESHARE_APPS = {
    'UBER': {
        'categories': ['UberX', 'Comfort', 'Black', 'Flash'],
        'weight': 45
    },
    '99': {
        'categories': ['Pop', '99Comfort', 'Black'],
        'weight': 35
    },
    'CABIFY': {
        'categories': ['Lite', 'Cabify', 'Plus'],
        'weight': 10
    },
    'INDRIVER': {
        'categories': ['Economy', 'Comfort'],
        'weight': 10
    },
}

APPS_LIST = list(RIDESHARE_APPS.keys())
APPS_WEIGHTS = [RIDESHARE_APPS[app]['weight'] for app in APPS_LIST]

# =============================================================================
# POIS POR CAPITAL (Simplified - Top 5 capitals with 6-8 POIs each)
# =============================================================================

POIS_POR_CAPITAL = {
    # São Paulo
    'SP': [
        {'name': 'Aeroporto de Congonhas', 'type': 'AIRPORT', 'lat': -23.6261, 'lon': -46.6564},
        {'name': 'Aeroporto de Guarulhos', 'type': 'AIRPORT', 'lat': -23.4356, 'lon': -46.4731},
        {'name': 'Shopping Ibirapuera', 'type': 'SHOPPING', 'lat': -23.6098, 'lon': -46.6653},
        {'name': 'Hospital das Clínicas', 'type': 'HOSPITAL', 'lat': -23.5558, 'lon': -46.6696},
        {'name': 'USP Cidade Universitária', 'type': 'UNIVERSITY', 'lat': -23.5587, 'lon': -46.7317},
        {'name': 'Estádio do Morumbi', 'type': 'STADIUM', 'lat': -23.6003, 'lon': -46.7222},
        {'name': 'Av. Paulista', 'type': 'BUSINESS_CENTER', 'lat': -23.5614, 'lon': -46.6558},
        {'name': 'Rodoviária do Tietê', 'type': 'BUS_STATION', 'lat': -23.5167, 'lon': -46.6250},
    ],
    # Rio de Janeiro
    'RJ': [
        {'name': 'Aeroporto Santos Dumont', 'type': 'AIRPORT', 'lat': -22.9104, 'lon': -43.1631},
        {'name': 'Aeroporto Galeão', 'type': 'AIRPORT', 'lat': -22.8089, 'lon': -43.2436},
        {'name': 'Shopping Rio Sul', 'type': 'SHOPPING', 'lat': -22.9511, 'lon': -43.1775},
        {'name': 'Maracanã', 'type': 'STADIUM', 'lat': -22.9121, 'lon': -43.2302},
        {'name': 'Praia de Copacabana', 'type': 'BEACH', 'lat': -22.9711, 'lon': -43.1822},
        {'name': 'Centro Histórico', 'type': 'HISTORIC_CENTER', 'lat': -22.9068, 'lon': -43.1729},
        {'name': 'Rodoviária Novo Rio', 'type': 'BUS_STATION', 'lat': -22.8986, 'lon': -43.2092},
        {'name': 'UFRJ', 'type': 'UNIVERSITY', 'lat': -22.8625, 'lon': -43.2236},
    ],
    # Minas Gerais (Belo Horizonte)
    'MG': [
        {'name': 'Aeroporto de Confins', 'type': 'AIRPORT', 'lat': -19.6244, 'lon': -43.9719},
        {'name': 'Shopping Diamond Mall', 'type': 'SHOPPING', 'lat': -19.9314, 'lon': -43.9342},
        {'name': 'Mineirão', 'type': 'STADIUM', 'lat': -19.8658, 'lon': -43.9708},
        {'name': 'UFMG', 'type': 'UNIVERSITY', 'lat': -19.8698, 'lon': -43.9644},
        {'name': 'Praça da Liberdade', 'type': 'HISTORIC_CENTER', 'lat': -19.9319, 'lon': -43.9381},
        {'name': 'Rodoviária de BH', 'type': 'BUS_STATION', 'lat': -19.9225, 'lon': -43.9306},
        {'name': 'Hospital Felício Rocho', 'type': 'HOSPITAL', 'lat': -19.9358, 'lon': -43.9356},
    ],
    # Bahia (Salvador)
    'BA': [
        {'name': 'Aeroporto de Salvador', 'type': 'AIRPORT', 'lat': -12.9086, 'lon': -38.3225},
        {'name': 'Shopping Barra', 'type': 'SHOPPING', 'lat': -13.0092, 'lon': -38.5311},
        {'name': 'Arena Fonte Nova', 'type': 'STADIUM', 'lat': -12.9786, 'lon': -38.5042},
        {'name': 'Pelourinho', 'type': 'HISTORIC_CENTER', 'lat': -12.9714, 'lon': -38.5103},
        {'name': 'Praia de Itapuã', 'type': 'BEACH', 'lat': -12.9394, 'lon': -38.3567},
        {'name': 'Rodoviária de Salvador', 'type': 'BUS_STATION', 'lat': -12.9558, 'lon': -38.4336},
        {'name': 'UFBA', 'type': 'UNIVERSITY', 'lat': -13.0019, 'lon': -38.5083},
    ],
    # Distrito Federal (Brasília)
    'DF': [
        {'name': 'Aeroporto JK', 'type': 'AIRPORT', 'lat': -15.8697, 'lon': -47.9172},
        {'name': 'Shopping Conjunto Nacional', 'type': 'SHOPPING', 'lat': -15.7900, 'lon': -47.8828},
        {'name': 'Estádio Mané Garrincha', 'type': 'STADIUM', 'lat': -15.7836, 'lon': -47.8989},
        {'name': 'UnB', 'type': 'UNIVERSITY', 'lat': -15.7631, 'lon': -47.8700},
        {'name': 'Esplanada dos Ministérios', 'type': 'BUSINESS_CENTER', 'lat': -15.7989, 'lon': -47.8644},
        {'name': 'Rodoviária do Plano Piloto', 'type': 'BUS_STATION', 'lat': -15.7942, 'lon': -47.8822},
        {'name': 'Parque da Cidade', 'type': 'PARK', 'lat': -15.8083, 'lon': -47.9017},
    ],
}

# Map state codes to their capital city names
CAPITAL_POR_ESTADO = {
    'SP': 'São Paulo',
    'RJ': 'Rio de Janeiro',
    'MG': 'Belo Horizonte',
    'BA': 'Salvador',
    'DF': 'Brasília',
}

POI_TYPES = [
    'AIRPORT', 'SHOPPING', 'BUS_STATION', 'HOSPITAL', 'UNIVERSITY',
    'STADIUM', 'BUSINESS_CENTER', 'BUS_TERMINAL', 'PARK',
    'BEACH', 'HISTORIC_CENTER', 'HOTEL', 'FAIR', 'MARKET'
]

# =============================================================================
# VEHICLES
# =============================================================================

VEHICLE_COLORS = [
    'White', 'Silver', 'Black', 'Gray', 'Red',
    'Blue', 'Brown', 'Beige', 'Green'
]

# Category hierarchy: Pop/UberX < Comfort < Black
VEICULOS_POPULARES = [
    # Economy (Pop, UberX, Lite, Economy)
    {'marca': 'Hyundai', 'modelo': 'HB20', 'categoria_min': 'economy'},
    {'marca': 'Chevrolet', 'modelo': 'Onix', 'categoria_min': 'economy'},
    {'marca': 'Fiat', 'modelo': 'Argo', 'categoria_min': 'economy'},
    {'marca': 'Fiat', 'modelo': 'Mobi', 'categoria_min': 'economy'},
    {'marca': 'Renault', 'modelo': 'Kwid', 'categoria_min': 'economy'},
    {'marca': 'Volkswagen', 'modelo': 'Gol', 'categoria_min': 'economy'},
    {'marca': 'Volkswagen', 'modelo': 'Polo', 'categoria_min': 'economy'},
    {'marca': 'Chevrolet', 'modelo': 'Onix Plus', 'categoria_min': 'economy'},
    # Comfort (Comfort, 99Comfort, Cabify)
    {'marca': 'Toyota', 'modelo': 'Corolla', 'categoria_min': 'comfort'},
    {'marca': 'Honda', 'modelo': 'Civic', 'categoria_min': 'comfort'},
    {'marca': 'Volkswagen', 'modelo': 'Virtus', 'categoria_min': 'comfort'},
    {'marca': 'Hyundai', 'modelo': 'HB20S', 'categoria_min': 'comfort'},
    {'marca': 'Nissan', 'modelo': 'Sentra', 'categoria_min': 'comfort'},
    # Black/Premium
    {'marca': 'Toyota', 'modelo': 'Corolla Cross', 'categoria_min': 'black'},
    {'marca': 'Jeep', 'modelo': 'Compass', 'categoria_min': 'black'},
    {'marca': 'Volkswagen', 'modelo': 'Tiguan', 'categoria_min': 'black'},
    {'marca': 'BMW', 'modelo': 'X1', 'categoria_min': 'black'},
    {'marca': 'Mercedes-Benz', 'modelo': 'Classe A', 'categoria_min': 'black'},
]

# Vehicle years range
VEHICLE_YEARS = list(range(2015, 2026))  # 2015 to 2025

# Category mapping for compatibility checking
CATEGORY_LEVELS = {
    # Economy categories
    'UberX': 'economy',
    'Pop': 'economy',
    'Lite': 'economy',
    'Economy': 'economy',
    'Flash': 'economy',
    # Comfort categories
    'Comfort': 'comfort',
    '99Comfort': 'comfort',
    'Cabify': 'comfort',
    # Black/Premium categories
    'Black': 'black',
    'Plus': 'black',
}

CATEGORY_HIERARCHY = ['economy', 'comfort', 'black']

# =============================================================================
# RATES AND PRICING
# =============================================================================

TAXAS_POR_CATEGORIA = {
    # Economy
    'UberX': {'base': 5.00, 'km': 1.20, 'min': 0.25},
    'Pop': {'base': 4.50, 'km': 1.10, 'min': 0.20},
    'Lite': {'base': 4.80, 'km': 1.15, 'min': 0.22},
    'Economy': {'base': 4.00, 'km': 1.00, 'min': 0.18},
    'Flash': {'base': 5.50, 'km': 1.25, 'min': 0.28},
    # Comfort
    'Comfort': {'base': 7.00, 'km': 1.80, 'min': 0.35},
    '99Comfort': {'base': 6.50, 'km': 1.70, 'min': 0.32},
    'Cabify': {'base': 6.80, 'km': 1.75, 'min': 0.33},
    # Black/Premium
    'Black': {'base': 10.00, 'km': 2.50, 'min': 0.50},
    'Plus': {'base': 9.50, 'km': 2.40, 'min': 0.48},
}

# Surge multipliers by hour of day
SURGE_POR_HORARIO = {
    # Early morning (00:00 - 05:59) - Low demand
    0: 1.0, 1: 1.0, 2: 1.2, 3: 1.3, 4: 1.2, 5: 1.0,
    # Morning rush (06:00 - 09:59)
    6: 1.2, 7: 1.5, 8: 1.8, 9: 1.4,
    # Mid-day (10:00 - 16:59) - Normal
    10: 1.0, 11: 1.0, 12: 1.1, 13: 1.0, 14: 1.0, 15: 1.0, 16: 1.1,
    # Evening rush (17:00 - 20:59)
    17: 1.4, 18: 1.8, 19: 1.6, 20: 1.3,
    # Night (21:00 - 23:59)
    21: 1.2, 22: 1.3, 23: 1.4,
}

# Platform fee percentage by app
PLATFORM_FEE_PERCENT = {
    'UBER': 0.25,
    '99': 0.20,
    'CABIFY': 0.22,
    'INDRIVER': 0.15,
}

# =============================================================================
# RIDE STATUS AND CANCELLATION
# =============================================================================

RIDE_STATUS = [
    'REQUESTED',
    'ACCEPTED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED_PASSENGER',
    'CANCELLED_DRIVER',
    'NO_DRIVER',
]

RIDE_STATUS_WEIGHTS = {
    'REQUESTED': 0,  # Transient state
    'ACCEPTED': 0,      # Transient state
    'IN_PROGRESS': 0, # Transient state
    'COMPLETED': 85,
    'CANCELLED_PASSENGER': 6,
    'CANCELLED_DRIVER': 4,
    'NO_DRIVER': 5,
}

FINAL_STATUS_LIST = ['COMPLETED', 'CANCELLED_PASSENGER', 'CANCELLED_DRIVER', 'NO_DRIVER']
FINAL_STATUS_WEIGHTS = [RIDE_STATUS_WEIGHTS[s] for s in FINAL_STATUS_LIST]

CANCELLATION_REASONS = {
    'PASSENGER': [
        'Wait time too long',
        'Change of plans',
        'Found another ride',
        'Price too high',
        'Request error',
        'Driver too far',
    ],
    'DRIVER': [
        'Passenger did not show up',
        'Unsafe location',
        'Destination too far',
        'Passenger cancelled at location',
        'Vehicle problem',
        'Personal emergency',
    ],
}

# =============================================================================
# FRAUD TYPES
# =============================================================================

RIDESHARE_FRAUD_TYPES = {
    'GHOST_RIDE': 15,              # Driver starts/finishes without passenger
    'GPS_SPOOFING': 20,            # Location manipulation
    'SURGE_ABUSE': 15,             # Creating artificial demand
    'MULTI_ACCOUNT_DRIVER': 12,    # Same driver, multiple accounts
    'PROMO_ABUSE': 18,             # Creating accounts for promotions
    'RATING_FRAUD': 10,            # Rating manipulation
    'SPLIT_FARE_FRAUD': 10,        # Fraud in shared rides
}

FRAUD_TYPES_LIST = list(RIDESHARE_FRAUD_TYPES.keys())
FRAUD_TYPES_WEIGHTS = list(RIDESHARE_FRAUD_TYPES.values())

# =============================================================================
# PAYMENT METHODS
# =============================================================================

PAYMENT_METHODS = {
    'PIX': 30,
    'CREDIT_CARD': 35,
    'DEBIT_CARD': 15,
    'CASH': 15,
    'CORPORATE_VOUCHER': 5,
}

PAYMENT_METHODS_LIST = list(PAYMENT_METHODS.keys())
PAYMENT_METHODS_WEIGHTS = list(PAYMENT_METHODS.values())

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_app_categories(app: str) -> List[str]:
    """Get available categories for a rideshare app."""
    if app in RIDESHARE_APPS:
        return RIDESHARE_APPS[app]['categories']
    return ['Economy']


def get_pois_for_state(state: str) -> List[Dict[str, Any]]:
    """
    Get POIs for a state. If state not in POIS_POR_CAPITAL,
    returns POIs from a random available state.
    """
    if state in POIS_POR_CAPITAL:
        return POIS_POR_CAPITAL[state]
    # Fallback to SP if state not available
    return POIS_POR_CAPITAL.get('SP', [])


def get_pois_for_city(state: str, city: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get POIs for a city. Currently only capitals are supported,
    so this just calls get_pois_for_state.
    """
    return get_pois_for_state(state)


def get_random_vehicle(category_min: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a random vehicle, optionally filtering by minimum category.
    
    Args:
        category_min: Minimum category level ('economy', 'comfort', 'black')
                     If None, returns any vehicle.
    
    Returns:
        Dict with marca, modelo, ano, cor, categoria_min
    """
    if category_min:
        min_level = CATEGORY_HIERARCHY.index(category_min) if category_min in CATEGORY_HIERARCHY else 0
        eligible = [v for v in VEICULOS_POPULARES 
                   if CATEGORY_HIERARCHY.index(v['categoria_min']) >= min_level]
    else:
        eligible = VEICULOS_POPULARES
    
    if not eligible:
        eligible = VEICULOS_POPULARES
    
    vehicle = random.choice(eligible)
    return {
        'marca': vehicle['marca'],
        'modelo': vehicle['modelo'],
        'ano': random.choice(VEHICLE_YEARS),
        'cor': random.choice(VEHICLE_COLORS),
        'categoria_min': vehicle['categoria_min'],
    }


def get_vehicle_for_category(category: str) -> Dict[str, Any]:
    """
    Get a random vehicle compatible with a specific ride category.
    
    Args:
        category: The ride category (e.g., 'UberX', 'Black', 'Comfort')
    
    Returns:
        Dict with vehicle details
    """
    category_level = CATEGORY_LEVELS.get(category, 'economy')
    return get_random_vehicle(category_min=category_level)


def get_surge_multiplier(hour: int) -> float:
    """Get surge multiplier for a given hour of day."""
    return SURGE_POR_HORARIO.get(hour % 24, 1.0)


def calculate_base_fare(category: str, distance_km: float, duration_min: float) -> Dict[str, float]:
    """
    Calculate fare breakdown for a ride.
    
    Returns:
        Dict with base, distance_fare, time_fare, total
    """
    rates = TAXAS_POR_CATEGORIA.get(category, TAXAS_POR_CATEGORIA['UberX'])
    
    base = rates['base']
    distance_fare = distance_km * rates['km']
    time_fare = duration_min * rates['min']
    total = base + distance_fare + time_fare
    
    return {
        'base': round(base, 2),
        'distance_fare': round(distance_fare, 2),
        'time_fare': round(time_fare, 2),
        'total': round(total, 2),
    }


def get_random_cancellation_reason(cancelled_by: str) -> str:
    """Get a random cancellation reason based on who cancelled."""
    reasons = CANCELLATION_REASONS.get(cancelled_by.upper(), CANCELLATION_REASONS['PASSENGER'])
    return random.choice(reasons)


def get_random_app() -> str:
    """Get a random rideshare app weighted by popularity."""
    return random.choices(APPS_LIST, weights=APPS_WEIGHTS, k=1)[0]


def get_random_category_for_app(app: str) -> str:
    """Get a random category for a given app."""
    categories = get_app_categories(app)
    return random.choice(categories)


def get_random_payment_method() -> str:
    """Get a random payment method weighted by popularity."""
    return random.choices(PAYMENT_METHODS_LIST, weights=PAYMENT_METHODS_WEIGHTS, k=1)[0]


def get_random_fraud_type() -> str:
    """Get a random fraud type weighted by occurrence."""
    return random.choices(FRAUD_TYPES_LIST, weights=FRAUD_TYPES_WEIGHTS, k=1)[0]


def get_random_final_status() -> str:
    """Get a random final ride status weighted by occurrence."""
    return random.choices(FINAL_STATUS_LIST, weights=FINAL_STATUS_WEIGHTS, k=1)[0]


def get_available_states() -> List[str]:
    """Get list of states with POI data available."""
    return list(POIS_POR_CAPITAL.keys())
