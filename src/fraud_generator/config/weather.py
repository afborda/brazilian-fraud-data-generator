"""
Configuration module for weather simulation.
Contains regions, weather conditions, temperatures, and rain probabilities.
"""

import random
from datetime import datetime
from typing import Dict, Any, Optional

# =============================================================================
# BRAZILIAN REGIONS
# =============================================================================

REGIOES = {
    'NORTE': ['AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO'],
    'NORDESTE': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'CENTRO_OESTE': ['DF', 'GO', 'MT', 'MS'],
    'SUDESTE': ['ES', 'MG', 'RJ', 'SP'],
    'SUL': ['PR', 'RS', 'SC'],
}

# Reverse mapping: state -> region
STATE_TO_REGION = {}
for region, states in REGIOES.items():
    for state in states:
        STATE_TO_REGION[state] = region

# =============================================================================
# WEATHER CONDITIONS
# =============================================================================

WEATHER_CONDITIONS = {
    'CLEAR': {
        'surge_impact': 1.0,
        'desc': 'Tempo limpo',
        'desc_en': 'Clear sky',
    },
    'CLOUDY': {
        'surge_impact': 1.0,
        'desc': 'Nublado',
        'desc_en': 'Cloudy',
    },
    'LIGHT_RAIN': {
        'surge_impact': 1.3,
        'desc': 'Garoa',
        'desc_en': 'Light rain',
    },
    'RAIN': {
        'surge_impact': 1.6,
        'desc': 'Chuva',
        'desc_en': 'Rain',
    },
    'HEAVY_RAIN': {
        'surge_impact': 2.0,
        'desc': 'Chuva forte',
        'desc_en': 'Heavy rain',
    },
    'STORM': {
        'surge_impact': 2.5,
        'desc': 'Tempestade',
        'desc_en': 'Storm',
    },
}

WEATHER_CONDITIONS_LIST = list(WEATHER_CONDITIONS.keys())

# =============================================================================
# TEMPERATURE BY REGION AND SEASON
# =============================================================================

# Temperatures in Celsius (min, max) by region and season
# Brazil: Summer = Dec-Feb, Autumn = Mar-May, Winter = Jun-Aug, Spring = Sep-Nov
TEMP_POR_REGIAO = {
    'NORTE': {
        'verao': (26, 34),    # Hot and humid year-round
        'outono': (25, 33),
        'inverno': (24, 32),
        'primavera': (26, 35),
    },
    'NORDESTE': {
        'verao': (26, 35),    # Hot, coastal areas slightly cooler
        'outono': (24, 32),
        'inverno': (22, 30),
        'primavera': (25, 34),
    },
    'CENTRO_OESTE': {
        'verao': (22, 35),    # Hot summers, dry winters
        'outono': (20, 32),
        'inverno': (15, 30),
        'primavera': (22, 36),
    },
    'SUDESTE': {
        'verao': (22, 35),    # Variable, coastal vs inland
        'outono': (18, 28),
        'inverno': (12, 25),
        'primavera': (18, 30),
    },
    'SUL': {
        'verao': (20, 32),    # Four distinct seasons
        'outono': (14, 25),
        'inverno': (5, 18),
        'primavera': (14, 26),
    },
}

# =============================================================================
# RAIN PROBABILITY BY MONTH AND REGION
# =============================================================================

# Probability of rain (0.0 to 1.0) by month (1-12) and region
# Based on typical Brazilian climate patterns
PROB_CHUVA_POR_MES = {
    'NORTE': {
        # Rainy season: Dec-May, Dry: Jun-Nov
        1: 0.70, 2: 0.75, 3: 0.80, 4: 0.75, 5: 0.60, 6: 0.30,
        7: 0.20, 8: 0.15, 9: 0.20, 10: 0.30, 11: 0.45, 12: 0.60,
    },
    'NORDESTE': {
        # Varies by sub-region, using coastal averages
        1: 0.25, 2: 0.30, 3: 0.45, 4: 0.55, 5: 0.60, 6: 0.55,
        7: 0.50, 8: 0.35, 9: 0.20, 10: 0.15, 11: 0.15, 12: 0.20,
    },
    'CENTRO_OESTE': {
        # Rainy season: Oct-Mar, Dry: Apr-Sep
        1: 0.65, 2: 0.60, 3: 0.55, 4: 0.30, 5: 0.15, 6: 0.05,
        7: 0.05, 8: 0.10, 9: 0.25, 10: 0.45, 11: 0.55, 12: 0.60,
    },
    'SUDESTE': {
        # Rainy summer, dry winter
        1: 0.60, 2: 0.55, 3: 0.50, 4: 0.35, 5: 0.25, 6: 0.15,
        7: 0.15, 8: 0.15, 9: 0.25, 10: 0.40, 11: 0.50, 12: 0.55,
    },
    'SUL': {
        # Rain distributed throughout the year
        1: 0.45, 2: 0.45, 3: 0.40, 4: 0.40, 5: 0.40, 6: 0.40,
        7: 0.45, 8: 0.45, 9: 0.50, 10: 0.50, 11: 0.45, 12: 0.45,
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_region_for_state(state: str) -> str:
    """
    Get the Brazilian region for a given state code.
    
    Args:
        state: Two-letter state code (e.g., 'SP', 'RJ')
    
    Returns:
        Region name (NORTE, NORDESTE, CENTRO_OESTE, SUDESTE, SUL)
        Defaults to SUDESTE if state not found.
    """
    return STATE_TO_REGION.get(state.upper(), 'SUDESTE')


def get_season(month: int) -> str:
    """
    Get the season for a given month (Brazilian seasons).
    
    In Brazil (Southern Hemisphere):
    - Summer (Verão): December, January, February
    - Autumn (Outono): March, April, May
    - Winter (Inverno): June, July, August
    - Spring (Primavera): September, October, November
    
    Args:
        month: Month number (1-12)
    
    Returns:
        Season name in Portuguese (verao, outono, inverno, primavera)
    """
    month = month % 12 or 12  # Handle 0 as December
    
    if month in (12, 1, 2):
        return 'verao'
    elif month in (3, 4, 5):
        return 'outono'
    elif month in (6, 7, 8):
        return 'inverno'
    else:  # 9, 10, 11
        return 'primavera'


def _get_weather_condition(rain_probability: float) -> str:
    """
    Determine weather condition based on rain probability.
    
    Args:
        rain_probability: Base probability of rain for region/month (0.0 to 1.0)
    
    Returns:
        Weather condition string
    """
    roll = random.random()
    
    # Adjust thresholds based on rain probability
    if roll > rain_probability:
        # No rain
        return random.choice(['CLEAR', 'CLOUDY'])
    else:
        # Some form of rain
        rain_intensity = random.random()
        if rain_intensity < 0.50:
            return 'LIGHT_RAIN'
        elif rain_intensity < 0.80:
            return 'RAIN'
        elif rain_intensity < 0.95:
            return 'HEAVY_RAIN'
        else:
            return 'STORM'


def generate_weather(state: str, dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Generate realistic weather conditions for a state and datetime.
    
    Args:
        state: Two-letter state code (e.g., 'SP', 'RJ')
        dt: Datetime for weather generation. If None, uses current time.
    
    Returns:
        Dict with:
            - condition: Weather condition string (CLEAR, RAIN, etc.)
            - condition_desc: Description in Portuguese
            - temperature: Temperature in Celsius
            - surge_impact: Surge multiplier for rideshare pricing
            - region: Brazilian region
            - season: Current season
    """
    if dt is None:
        dt = datetime.now()
    
    # Get region and season
    region = get_region_for_state(state)
    season = get_season(dt.month)
    
    # Get rain probability for region/month
    rain_prob = PROB_CHUVA_POR_MES.get(region, PROB_CHUVA_POR_MES['SUDESTE']).get(dt.month, 0.3)
    
    # Adjust rain probability by time of day (afternoon storms are common)
    hour = dt.hour
    if 14 <= hour <= 18:
        rain_prob = min(1.0, rain_prob * 1.3)  # 30% more likely in afternoon
    elif 0 <= hour <= 6:
        rain_prob = rain_prob * 0.7  # 30% less likely at night
    
    # Generate condition
    condition = _get_weather_condition(rain_prob)
    
    # Get temperature range for region/season
    temp_range = TEMP_POR_REGIAO.get(region, TEMP_POR_REGIAO['SUDESTE']).get(season, (20, 30))
    
    # Adjust temperature by time of day
    base_temp = random.uniform(temp_range[0], temp_range[1])
    if 6 <= hour <= 9:
        # Morning - cooler
        temperature = base_temp * 0.9
    elif 12 <= hour <= 16:
        # Afternoon - hottest
        temperature = base_temp * 1.05
    elif 18 <= hour <= 22:
        # Evening - cooling down
        temperature = base_temp * 0.95
    else:
        # Night - coolest
        temperature = base_temp * 0.85
    
    # Clamp temperature to reasonable range
    temperature = max(temp_range[0] - 5, min(temp_range[1] + 5, temperature))
    
    # Reduce temperature if raining
    if condition in ('RAIN', 'HEAVY_RAIN', 'STORM'):
        temperature -= random.uniform(2, 5)
    
    # Get surge impact
    weather_info = WEATHER_CONDITIONS.get(condition, WEATHER_CONDITIONS['CLEAR'])
    surge_impact = weather_info['surge_impact']
    
    return {
        'condition': condition,
        'condition_desc': weather_info['desc'],
        'temperature': round(temperature, 1),
        'surge_impact': surge_impact,
        'region': region,
        'season': season,
    }


def get_surge_impact(condition: str) -> float:
    """
    Get the surge impact multiplier for a weather condition.
    
    Args:
        condition: Weather condition string
    
    Returns:
        Surge multiplier (1.0 to 2.5)
    """
    weather_info = WEATHER_CONDITIONS.get(condition, WEATHER_CONDITIONS['CLEAR'])
    return weather_info['surge_impact']


def get_weather_description(condition: str, portuguese: bool = True) -> str:
    """
    Get the description for a weather condition.
    
    Args:
        condition: Weather condition string
        portuguese: If True, return Portuguese description
    
    Returns:
        Weather description string
    """
    weather_info = WEATHER_CONDITIONS.get(condition, WEATHER_CONDITIONS['CLEAR'])
    return weather_info['desc'] if portuguese else weather_info['desc_en']
