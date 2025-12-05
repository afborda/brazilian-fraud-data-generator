"""
Driver generator for Brazilian Rideshare Fraud Data Generator.
"""

import random
import string
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List, Iterator
from faker import Faker

from ..models.ride import DriverIndex
from ..validators.cpf import generate_valid_cpf
from ..config.geography import (
    ESTADOS_LIST,
    ESTADOS_WEIGHTS,
    CIDADES_POR_ESTADO,
)
from ..config.rideshare import (
    RIDESHARE_APPS,
    APPS_LIST,
    VEICULOS_POPULARES,
    VEHICLE_YEARS,
    CORES_VEICULOS,
    CATEGORY_HIERARCHY,
    get_app_categories,
    get_available_states,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_cnh() -> Dict[str, Any]:
    """
    Generate a valid Brazilian CNH (Carteira Nacional de Habilitação).
    
    Returns:
        Dict with:
            - numero: 11-digit CNH number
            - categoria: Category (B, AB, C, D, E)
            - validade: Expiration date (1-5 years from now)
    """
    # CNH number: 11 random digits
    numero = ''.join(random.choices(string.digits, k=11))
    
    # Category distribution (most drivers have B or AB)
    categoria = random.choices(
        ['B', 'AB', 'C', 'D', 'E'],
        weights=[60, 25, 8, 5, 2],
        k=1
    )[0]
    
    # Expiration date: 1-5 years from now
    years_until_expiry = random.randint(1, 5)
    validade = date.today() + timedelta(days=years_until_expiry * 365)
    
    return {
        'numero': numero,
        'categoria': categoria,
        'validade': validade,
    }


def generate_vehicle_plate(use_mercosul: Optional[bool] = None) -> str:
    """
    Generate a Brazilian vehicle license plate.
    
    Args:
        use_mercosul: If True, use Mercosul format (ABC1D23).
                     If False, use old format (ABC-1234).
                     If None, randomly choose (70% Mercosul, 30% old).
    
    Returns:
        License plate string
    """
    if use_mercosul is None:
        use_mercosul = random.random() < 0.70
    
    # First 3 characters are always letters
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    
    if use_mercosul:
        # Mercosul format: ABC1D23 (letter, digit, letter, digit, digit)
        digit1 = random.choice(string.digits)
        letter4 = random.choice(string.ascii_uppercase)
        digits_end = ''.join(random.choices(string.digits, k=2))
        return f"{letters}{digit1}{letter4}{digits_end}"
    else:
        # Old format: ABC-1234
        digits = ''.join(random.choices(string.digits, k=4))
        return f"{letters}-{digits}"


def select_vehicle_for_categories(categories: List[str]) -> Dict[str, Any]:
    """
    Select a vehicle compatible with the given categories.
    
    The vehicle's categoria_min must be able to serve all requested categories.
    
    Args:
        categories: List of enabled categories (e.g., ['UberX', 'Comfort'])
    
    Returns:
        Dict with marca, modelo, ano, cor, categoria_min
    """
    # Determine the minimum category level needed
    # If driver has 'Black' category, they need a 'black' level vehicle
    # If only 'UberX'/'Pop', an 'economy' vehicle is fine
    
    min_level_needed = 'economy'
    
    for cat in categories:
        # Map category names to levels
        if cat in ['Black', 'Plus']:
            min_level_needed = 'black'
            break  # Black is the highest
        elif cat in ['Comfort', '99Comfort', 'Cabify']:
            if min_level_needed != 'black':
                min_level_needed = 'comfort'
    
    # Filter vehicles by minimum category
    level_index = CATEGORY_HIERARCHY.index(min_level_needed)
    eligible_vehicles = [
        v for v in VEICULOS_POPULARES
        if CATEGORY_HIERARCHY.index(v['categoria_min']) >= level_index
    ]
    
    if not eligible_vehicles:
        eligible_vehicles = VEICULOS_POPULARES
    
    vehicle = random.choice(eligible_vehicles)
    
    return {
        'marca': vehicle['marca'],
        'modelo': vehicle['modelo'],
        'ano': random.choice(VEHICLE_YEARS),
        'cor': random.choice(CORES_VEICULOS),
        'categoria_min': vehicle['categoria_min'],
    }


def get_categories_for_vehicle(vehicle_categoria_min: str, apps: List[str]) -> List[str]:
    """
    Get all categories a vehicle can serve based on its minimum category level.
    
    Args:
        vehicle_categoria_min: The vehicle's minimum category ('economy', 'comfort', 'black')
        apps: List of apps the driver is registered with
    
    Returns:
        List of category names the driver can enable
    """
    categories = []
    vehicle_level = CATEGORY_HIERARCHY.index(vehicle_categoria_min)
    
    for app in apps:
        app_categories = get_app_categories(app)
        for cat in app_categories:
            # Map category to level
            if cat in ['UberX', 'Pop', 'Lite', 'Economy', 'Flash']:
                cat_level = 0  # economy
            elif cat in ['Comfort', '99Comfort', 'Cabify']:
                cat_level = 1  # comfort
            else:  # Black, Plus
                cat_level = 2  # black
            
            # Vehicle can serve this category if its level is >= category level
            if vehicle_level >= cat_level and cat not in categories:
                categories.append(cat)
    
    return categories


# =============================================================================
# DRIVER GENERATOR CLASS
# =============================================================================

class DriverGenerator:
    """
    Generator for realistic Brazilian rideshare driver data.
    
    Features:
    - Valid CPF with check digits
    - Valid CNH with realistic category distribution
    - Mercosul or old format license plates
    - Vehicle selection based on enabled categories
    - Realistic rating distribution
    - Multiple app registration
    """
    
    def __init__(
        self,
        locale: str = 'pt_BR',
        seed: Optional[int] = None
    ):
        """
        Initialize driver generator.
        
        Args:
            locale: Faker locale (default: pt_BR)
            seed: Random seed for reproducibility
        """
        self.fake = Faker(locale)
        
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        
        # Get available states (those with POI data)
        self.available_states = get_available_states()
    
    def generate(
        self,
        driver_id: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a single driver.
        
        Args:
            driver_id: Unique identifier for the driver
            state: Operating state code (e.g., 'SP'). If None, randomly selected.
        
        Returns:
            Driver data as dictionary
        """
        # Select operating state (prefer states with POI data)
        if state and state in self.available_states:
            operating_state = state
        elif state:
            # State provided but not in available, use random from available
            operating_state = random.choice(self.available_states)
        else:
            # Weight selection towards available states
            operating_state = random.choices(
                self.available_states,
                weights=[ESTADOS_WEIGHTS[ESTADOS_LIST.index(s)] if s in ESTADOS_LIST else 1 
                        for s in self.available_states],
                k=1
            )[0]
        
        # Select operating city (capital)
        cities = CIDADES_POR_ESTADO.get(operating_state, ['Capital'])
        operating_city = cities[0]  # Usually the capital/main city
        
        # Generate personal info
        nome = self.fake.name()
        cpf = generate_valid_cpf(formatted=True)
        cnh_data = generate_cnh()
        
        # Contact info
        telefone = self.fake.phone_number()
        email = self.fake.email()
        
        # Active apps (1-3 apps)
        num_apps = random.choices([1, 2, 3], weights=[40, 40, 20], k=1)[0]
        active_apps = random.sample(APPS_LIST, k=min(num_apps, len(APPS_LIST)))
        
        # Determine available categories from apps
        all_categories = []
        for app in active_apps:
            all_categories.extend(get_app_categories(app))
        all_categories = list(set(all_categories))
        
        # Randomly select which categories the driver enables (based on vehicle)
        # Most drivers stick to economy, some do comfort, few do black
        category_preference = random.choices(
            ['economy', 'comfort', 'black'],
            weights=[70, 25, 5],
            k=1
        )[0]
        
        # Select vehicle based on category preference
        vehicle = select_vehicle_for_categories([category_preference])
        
        # Get actual enabled categories based on vehicle capability
        categories_enabled = get_categories_for_vehicle(
            vehicle['categoria_min'],
            active_apps
        )
        
        # Vehicle plate
        vehicle_plate = generate_vehicle_plate()
        
        # Rating: Normal distribution centered at 4.7
        rating = random.gauss(4.7, 0.2)
        rating = max(4.0, min(5.0, rating))  # Clamp between 4.0 and 5.0
        
        # Trips completed: Realistic distribution
        # Most drivers: 100-1000, some: 1000-5000, few: 5000+
        trip_tier = random.choices(
            ['new', 'regular', 'experienced', 'veteran'],
            weights=[15, 50, 25, 10],
            k=1
        )[0]
        
        if trip_tier == 'new':
            trips_completed = random.randint(10, 100)
        elif trip_tier == 'regular':
            trips_completed = random.randint(100, 1000)
        elif trip_tier == 'experienced':
            trips_completed = random.randint(1000, 5000)
        else:  # veteran
            trips_completed = random.randint(5000, 15000)
        
        # Registration date based on trips
        if trips_completed < 100:
            registration_date = self.fake.date_time_between(start_date='-6m', end_date='-1m')
        elif trips_completed < 1000:
            registration_date = self.fake.date_time_between(start_date='-2y', end_date='-6m')
        else:
            registration_date = self.fake.date_time_between(start_date='-5y', end_date='-2y')
        
        # Active status (most are active)
        is_active = random.random() < 0.95
        
        return {
            'driver_id': driver_id,
            'nome': nome,
            'cpf': cpf,
            'cnh_numero': cnh_data['numero'],
            'cnh_categoria': cnh_data['categoria'],
            'cnh_validade': cnh_data['validade'].isoformat(),
            'telefone': telefone,
            'email': email,
            'vehicle_plate': vehicle_plate,
            'vehicle_brand': vehicle['marca'],
            'vehicle_model': vehicle['modelo'],
            'vehicle_year': vehicle['ano'],
            'vehicle_color': vehicle['cor'],
            'rating': round(rating, 2),
            'trips_completed': trips_completed,
            'registration_date': registration_date.isoformat(),
            'active_apps': active_apps,
            'operating_city': operating_city,
            'operating_state': operating_state,
            'categories_enabled': categories_enabled,
            'is_active': is_active,
        }
    
    def generate_batch(
        self,
        count: int,
        start_id: int = 1
    ) -> Iterator[Dict[str, Any]]:
        """
        Generate multiple drivers.
        
        Args:
            count: Number of drivers to generate
            start_id: Starting ID number
        
        Yields:
            Driver data dictionaries
        """
        for i in range(count):
            driver_id = f"DRV_{start_id + i:012d}"
            yield self.generate(driver_id)
    
    def generate_index(self, driver_data: Dict[str, Any]) -> DriverIndex:
        """
        Create a lightweight index from driver data.
        
        Args:
            driver_data: Full driver dictionary
        
        Returns:
            DriverIndex with essential fields for lookups
        """
        active_apps = driver_data.get('active_apps', [])
        if isinstance(active_apps, list):
            active_apps = tuple(active_apps)
        
        return DriverIndex(
            driver_id=driver_data['driver_id'],
            operating_state=driver_data['operating_state'],
            operating_city=driver_data['operating_city'],
            active_apps=active_apps,
        )
