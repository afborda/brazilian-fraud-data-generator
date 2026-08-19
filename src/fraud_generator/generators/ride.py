"""
Ride generator for Brazilian Rideshare Fraud Data Generator.
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Iterator, Tuple

try:
    from numba import jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def jit(*_args, **_kwargs):  # type: ignore
        def _wrap(func):
            return func
        return _wrap

from ..models.ride import RideIndex
from ..config.rideshare import (
    RIDESHARE_APPS,
    APPS_LIST,
    APPS_WEIGHTS,
    TAXAS_POR_CATEGORIA,
    SURGE_POR_HORARIO,
    PLATFORM_FEE_PERCENT,
    RIDESHARE_FRAUD_TYPES,
    FINAL_STATUS_LIST,
    FINAL_STATUS_WEIGHTS,
    CANCELLATION_REASONS,
    get_app_categories,
    get_pois_for_state,
    get_random_app,
    get_random_category_for_app,
    get_random_payment_method,
    get_random_fraud_type,
    get_random_final_status,
    get_random_cancellation_reason,
    CAPITAL_POR_ESTADO,
)
from ..config.weather import generate_weather, get_surge_impact
from ..config.geography import CIDADES_POR_ESTADO
from ..config.calibration import rate as _rate


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula.
    
    Args:
        lat1: Latitude of point 1 (degrees)
        lon1: Longitude of point 1 (degrees)
        lat2: Latitude of point 2 (degrees)
        lon2: Longitude of point 2 (degrees)
    
    Returns:
        Distance in kilometers
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


@jit(nopython=True, cache=True)
def haversine_distance_numba(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Numba-accelerated Haversine distance (if numba is available).
    """
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Select best available distance implementation
HAVERSINE_DISTANCE = haversine_distance_numba if NUMBA_AVAILABLE else haversine_distance


def calculate_surge(hour: int, weather_condition: str) -> float:
    """
    Calculate surge multiplier based on hour and weather.
    
    Args:
        hour: Hour of day (0-23)
        weather_condition: Weather condition string
    
    Returns:
        Surge multiplier (1.0 to ~3.0)
    """
    # Base surge from hour
    base_surge = SURGE_POR_HORARIO.get(hour, 1.0)

    # Weather impact
    weather_surge = get_surge_impact(weather_condition)

    # Combine (not simply multiply to avoid extreme values)
    # Use weighted combination
    combined = base_surge * 0.6 + weather_surge * 0.4 + (base_surge * weather_surge - 1) * 0.2

    # Clamp to reasonable range
    return max(1.0, min(3.0, combined))


def calculate_fare(
    distance_km: float,
    duration_min: float,
    category: str,
    surge: float,
    app: str
) -> Dict[str, float]:
    """
    Calculate fare breakdown for a ride.
    
    Args:
        distance_km: Distance in kilometers
        duration_min: Duration in minutes
        category: Ride category (e.g., 'UberX', 'Pop')
        surge: Surge multiplier
        app: App name (for platform fee)
    
    Returns:
        Dict with base_fare, final_fare, driver_pay, platform_fee
    """
    # Get rates for category (fallback to UberX if not found)
    rates = TAXAS_POR_CATEGORIA.get(category, TAXAS_POR_CATEGORIA.get('UberX', {
        'base': 5.0, 'km': 1.20, 'min': 0.25
    }))

    # Calculate base fare
    base = rates['base']
    distance_fare = distance_km * rates['km']
    time_fare = duration_min * rates['min']
    base_fare = base + distance_fare + time_fare

    # Apply surge
    final_fare = base_fare * surge

    # Minimum fare (at least R$8)
    final_fare = max(8.0, final_fare)

    # Platform fee
    platform_fee_pct = PLATFORM_FEE_PERCENT.get(app, 0.20)
    platform_fee = final_fare * platform_fee_pct

    # Driver pay
    driver_pay = final_fare - platform_fee

    return {
        'base_fare': round(base_fare, 2),
        'final_fare': round(final_fare, 2),
        'driver_pay': round(driver_pay, 2),
        'platform_fee': round(platform_fee, 2),
    }


def select_pois(state: str, city: Optional[str] = None) -> Tuple[Dict, Dict]:
    """
    Select two different POIs from the same city/state.
    
    Args:
        state: State code (e.g., 'SP')
        city: City name (optional, defaults to capital)
    
    Returns:
        Tuple of (pickup_poi, dropoff_poi) with different types
    """
    pois = get_pois_for_state(state)

    if len(pois) < 2:
        # Fallback: create synthetic POIs
        return (
            {'name': 'Origin', 'type': 'CENTER', 'lat': -23.55, 'lon': -46.64},
            {'name': 'Destination', 'type': 'SHOPPING', 'lat': -23.56, 'lon': -46.65},
        )

    # Select pickup POI
    pickup = random.choice(pois)

    # Select dropoff POI (different from pickup, preferably different type)
    available_dropoffs = [p for p in pois if p['name'] != pickup['name']]

    # Prefer different POI type
    different_type = [p for p in available_dropoffs if p['type'] != pickup['type']]
    if different_type:
        dropoff = random.choice(different_type)
    else:
        dropoff = random.choice(available_dropoffs) if available_dropoffs else pois[1]

    return pickup, dropoff


def get_average_speed(hour: int) -> float:
    """
    Get average urban speed based on hour of day.
    
    Args:
        hour: Hour of day (0-23)
    
    Returns:
        Average speed in km/h
    """
    # Rush hours: slower
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        return random.uniform(15, 25)
    # Night: faster
    elif 22 <= hour or hour <= 5:
        return random.uniform(35, 45)
    # Normal hours
    else:
        return random.uniform(25, 35)


# =============================================================================
# RIDE GENERATOR CLASS
# =============================================================================


def _promo_bucket_hash(bucket: int) -> str:
    """Stable 12-char id for a promotional campaign bucket.

    Legitimate campaigns and abuse rings share the same id namespace on
    purpose: the presence of a group id says a rider is in some campaign, not
    that they are defrauding it. What separates the two is the behaviour inside
    the group, which is what a detector should have to learn.
    """
    import hashlib as _hl

    return _hl.sha256(f"campaign::{bucket}".encode()).hexdigest()[:12]


class RideGenerator:
    """
    Generator for realistic Brazilian rideshare ride data.
    
    Features:
    - Multiple app support (Uber, 99, Cabify, InDriver)
    - Weather-aware surge pricing
    - Haversine distance calculation
    - Fraud type generation
    - Profile-aware generation (optional)
    """

    def __init__(
        self,
        fraud_rate: float = 0.008,
        use_profiles: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize ride generator.
        
        Args:
            fraud_rate: Fraction of rides that are fraudulent (0.0-1.0)
            use_profiles: If True, use behavioral profiles (future feature)
            seed: Random seed for reproducibility
        """
        self.fraud_rate = fraud_rate
        self.use_profiles = use_profiles

        if seed is not None:
            random.seed(seed)

    def generate(
        self,
        ride_id: str,
        driver_id: str,
        passenger_id: str,
        timestamp: datetime,
        passenger_state: str,
        passenger_profile: Optional[str] = None,
        force_fraud: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate a single ride.
        
        Args:
            ride_id: Ride identifier
            driver_id: Driver identifier
            passenger_id: Passenger (customer) identifier
            timestamp: Ride request timestamp
            passenger_state: Passenger's state (for POI selection)
            passenger_profile: Passenger's behavioral profile (optional)
            force_fraud: If set, override random fraud determination
        
        Returns:
            Ride data as dictionary
        """
        # Determine if fraud
        if force_fraud is not None:
            is_fraud = force_fraud
        else:
            is_fraud = random.random() < self.fraud_rate

        fraud_type = None
        if is_fraud:
            fraud_type = get_random_fraud_type()

        # Select app and category
        app = get_random_app()
        category = get_random_category_for_app(app)

        # Get weather for state and timestamp
        weather_data = generate_weather(passenger_state, timestamp)
        weather_condition = weather_data['condition']
        temperature = weather_data['temperature']

        # Select POIs
        pickup_poi, dropoff_poi = select_pois(passenger_state)

        # Get city name
        city = CAPITAL_POR_ESTADO.get(passenger_state, CIDADES_POR_ESTADO.get(passenger_state, ['Capital'])[0])

        # Build location dicts
        pickup_location = {
            'lat': pickup_poi['lat'],
            'lon': pickup_poi['lon'],
            'name': pickup_poi['name'],
            'poi_type': pickup_poi['type'],
            'city': city,
            'state': passenger_state,
        }

        dropoff_location = {
            'lat': dropoff_poi['lat'],
            'lon': dropoff_poi['lon'],
            'name': dropoff_poi['name'],
            'poi_type': dropoff_poi['type'],
            'city': city,
            'state': passenger_state,
        }

        # Calculate distance (Haversine * urban factor)
        straight_distance = HAVERSINE_DISTANCE(
            pickup_poi['lat'], pickup_poi['lon'],
            dropoff_poi['lat'], dropoff_poi['lon']
        )

        # Urban factor: roads are not straight
        urban_factor = random.uniform(1.3, 1.5)
        distance_km = straight_distance * urban_factor

        # Minimum distance
        distance_km = max(1.0, distance_km)

        # Calculate duration based on speed
        hour = timestamp.hour
        avg_speed = get_average_speed(hour)
        duration_minutes = int((distance_km / avg_speed) * 60)
        duration_minutes = max(5, duration_minutes)  # Minimum 5 minutes

        # Calculate surge
        surge_multiplier = calculate_surge(hour, weather_condition)

        # Calculate fare
        fare_data = calculate_fare(distance_km, duration_minutes, category, surge_multiplier, app)

        # Determine status
        status = get_random_final_status()

        # Timestamps based on status
        request_datetime = timestamp
        accept_datetime = None
        pickup_datetime = None
        dropoff_datetime = None
        wait_time_minutes = 0
        cancellation_reason = None
        driver_rating = None
        passenger_rating = None

        if status == 'COMPLETED':
            # Full ride flow
            wait_time_minutes = random.randint(2, 15)
            accept_datetime = request_datetime + timedelta(seconds=random.randint(10, 60))
            pickup_datetime = accept_datetime + timedelta(minutes=wait_time_minutes)
            dropoff_datetime = pickup_datetime + timedelta(minutes=duration_minutes)

            # Ratings (most give 5 stars)
            driver_rating = random.choices([5, 4, 3, 2, 1], weights=[70, 20, 5, 3, 2], k=1)[0]
            passenger_rating = random.choices([5, 4, 3, 2, 1], weights=[75, 18, 4, 2, 1], k=1)[0]

        elif status == 'CANCELLED_PASSENGER':
            accept_datetime = request_datetime + timedelta(seconds=random.randint(10, 60))
            wait_time_minutes = random.randint(1, 10)
            cancellation_reason = get_random_cancellation_reason('PASSENGER')
            # Zero fare for cancelled
            fare_data = {'base_fare': 0, 'final_fare': 0, 'driver_pay': 0, 'platform_fee': 0}

        elif status == 'CANCELLED_DRIVER':
            accept_datetime = request_datetime + timedelta(seconds=random.randint(10, 60))
            wait_time_minutes = random.randint(1, 5)
            cancellation_reason = get_random_cancellation_reason('DRIVER')
            fare_data = {'base_fare': 0, 'final_fare': 0, 'driver_pay': 0, 'platform_fee': 0}

        elif status == 'NO_DRIVER':
            wait_time_minutes = random.randint(5, 15)
            cancellation_reason = 'No driver available'
            fare_data = {'base_fare': 0, 'final_fare': 0, 'driver_pay': 0, 'platform_fee': 0}

        # Tip (only for completed rides, ~20% give tips)
        tip = 0.0
        if status == 'COMPLETED' and random.random() < 0.20:
            # Tip is typically 10-20% of fare
            tip = round(fare_data['final_fare'] * random.uniform(0.10, 0.25), 2)

        # Payment method
        payment_method = get_random_payment_method()

        ride = {
            'ride_id': ride_id,
            'timestamp': timestamp.isoformat(),
            'app': app,
            'category': category,
            'driver_id': driver_id,
            'passenger_id': passenger_id,
            'pickup_location': pickup_location,
            'dropoff_location': dropoff_location,
            'request_datetime': request_datetime.isoformat(),
            'accept_datetime': accept_datetime.isoformat() if accept_datetime else None,
            'pickup_datetime': pickup_datetime.isoformat() if pickup_datetime else None,
            'dropoff_datetime': dropoff_datetime.isoformat() if dropoff_datetime else None,
            'distance_km': round(distance_km, 2),
            'duration_minutes': duration_minutes,
            'wait_time_minutes': wait_time_minutes,
            'base_fare': fare_data['base_fare'],
            'surge_multiplier': round(surge_multiplier, 2),
            'final_fare': fare_data['final_fare'],
            'driver_pay': fare_data['driver_pay'],
            'platform_fee': fare_data['platform_fee'],
            'tip': tip,
            'payment_method': payment_method,
            'status': status,
            'driver_rating': driver_rating,
            'passenger_rating': passenger_rating,
            'cancellation_reason': cancellation_reason,
            'weather_condition': weather_condition,
            'temperature': temperature,
            'is_fraud': is_fraud,
            'fraud_type': fraud_type,
            # \u2500\u2500 T5: ride-share fraud fields \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n            # Estes cinco campos são preenchidos para AS DUAS classes logo
            # abaixo. Eram constantes fixas no ramo legítimo (None/0/False/0.0),
            # o que dava `nunique() == 1` e fazia qualquer desvio do default
            # significar fraude: medido em 223.696 corridas, a união de cinco
            # comparações triviais capturava 40,36% das fraudes com precisão
            # 100,0000%. Ver `_apply_legit_ride_fields`.
            'promo_abuse_group': None,
            'refund_count_30d': 0,
            'payment_dispute_flag': False,
            'route_deviation_km': 0.0,
            'new_device_first_ride': False,
        }

        # ── T5: populate fraud-specific field values ─────────────────────────
        if is_fraud and fraud_type:
            ride = self._apply_fraud_fields(ride, fraud_type, passenger_id)
        else:
            ride = self._apply_legit_ride_fields(ride, passenger_id)

        return ride

    def _apply_legit_ride_fields(self, ride: dict, passenger_id: str) -> dict:
        """Give an ordinary ride the same fields fraud carries, with real spread.

        Every value below happens to ordinary passengers:

        * reembolso — motorista não apareceu, corrida cancelada, cobrança em
          duplicidade. A maioria dos passageiros tem zero no mês, uma minoria
          tem um ou dois;
        * contestação de cartão — cobrança que o titular não reconhece, disputa
          familiar sobre o cartão, erro de tarifa dinâmica;
        * desvio de rota — trânsito, obra, bloqueio, motorista pegando atalho.
          Quase nunca é exatamente zero na prática;
        * primeiro uso de um aparelho — troca de celular, formatação, login no
          tablet;
        * grupo de promoção — campanhas legítimas agrupam passageiros de
          verdade (cupom de bairro, parceria com evento). Um `group_id` não
          nulo não pode significar abuso por si só.
        """
        rng = random

        # Poisson-ish: maioria em 0, cauda curta. Reembolso legítimo existe.
        r = rng.random()
        if r < _rate("ride.legit_refund_zero_share"):
            refunds = 0
        elif r < 0.985:
            refunds = 1
        else:
            refunds = rng.randint(2, 3)
        ride['refund_count_30d'] = refunds

        ride['payment_dispute_flag'] = rng.random() < _rate("ride.legit_dispute_prob")

        # Desvio quase sempre pequeno, mas raramente zero exato — o zero
        # cravado era o que tornava `> 0` um separador perfeito. Uma cauda rara
        # de desvio GRANDE também é real e faltava: obra, bloqueio de via ou
        # engarrafamento que força uma rota bem mais longa que a pedida — sem
        # ela, `route_deviation_km` do legítimo nunca passava de ~3,4 km e
        # qualquer corrida de DESTINATION_DISPARITY (ver `_apply_fraud_fields`)
        # ficava quase inteiramente fora desse alcance.
        if rng.random() < _rate("ride.legit_large_deviation_prob"):
            ride['route_deviation_km'] = round(abs(rng.gauss(6.0, 3.0)), 2)
        else:
            ride['route_deviation_km'] = round(abs(rng.gauss(0, 0.8)), 2)

        ride['new_device_first_ride'] = rng.random() < _rate("ride.legit_new_device_prob")

        # ~6% das corridas legítimas pertencem a alguma campanha promocional.
        if rng.random() < _rate("ride.legit_promo_group_share"):
            bucket = rng.randint(0, 40)
            ride['promo_abuse_group'] = f"PROMO_{_promo_bucket_hash(bucket)}"

        return ride

    def _apply_fraud_fields(
        self,
        ride: dict,
        fraud_type: str,
        passenger_id: str,
    ) -> dict:
        """T5: Populate ride-fraud-specific fields based on fraud type.

        Structure matters here. This used to write only the fields each pattern
        cared about, leaving the rest at their constant defaults — so a
        REFUND_ABUSE record carried `route_deviation_km = 0.0` exactly, and once
        the legitimate class stopped being constant that zero would have become
        a *fraud* marker. Every fraud record therefore starts from the same
        ordinary baseline as a legitimate one and only then receives its shift.

        The shifts are probabilistic and overlap the ordinary distribution:
        a pattern that always set the same combination of fields made
        `fraud_type` recoverable by table lookup, which is the multiclass
        version of the same defect.
        """
        import hashlib as _hl

        # Baseline: a fraudulent ride is an ordinary ride first.
        ride = self._apply_legit_ride_fields(ride, passenger_id)

        if fraud_type == 'PROMO_ABUSE':
            # Stable group_id derived from passenger so same account cluster appears together
            h = _hl.sha256(passenger_id.encode()).hexdigest()[:12]
            ride['promo_abuse_group'] = f"PROMO_{h}"
            # Conta usada 1-3 vezes e abandonada. Mantém o reembolso do
            # baseline: abusador de promoção às vezes também pede reembolso.

        elif fraud_type == 'REFUND_ABUSE':
            # Reclamação recorrente. O piso de 3 não se sustenta: um passageiro
            # legítimo azarado chega a 3, e um abusador cuidadoso fica em 2.
            ride['refund_count_30d'] = max(
                ride['refund_count_30d'], 1 + int(random.expovariate(1 / 3.2))
            )

        elif fraud_type == 'PAYMENT_CHARGEBACK':
            # Cartão roubado: a corrida completa e depois é contestada. Não é
            # certeza — parte dos chargebacks fraudulentos nunca é aberta pelo
            # titular, e o padrão só aparece na corrida seguinte.
            ride['payment_dispute_flag'] = random.random() < _rate("ride.chargeback_dispute_prob")

        elif fraud_type == 'DESTINATION_DISPARITY':
            # Rota realizada difere da pedida. A versão anterior multiplicava
            # distance_km por um fator sempre >= 0.35x, sempre acima da cauda
            # curta do baseline legítimo (abs(N(0, 0.8)), raramente > 3km) —
            # medido: 97,65% da fraude caía inteiramente fora do alcance
            # legítimo, quase um separador perfeito isolado (route_deviation_km
            # > 3.43 capturava 97,65% de DESTINATION_DISPARITY com 100% de
            # precisão num teste isolado do tipo). Uma fração agora fica com
            # desvio discreto — golpe morno ou tentativa abortada, ainda
            # dentro do que trânsito comum explicaria — simétrico à cauda
            # grande que _apply_legit_ride_fields ganhou para o lado legítimo.
            base_dist = ride.get('distance_km', 5.0)
            if random.random() < _rate("ride.destination_disparity_mild_share"):
                ride['route_deviation_km'] = round(
                    max(ride['route_deviation_km'], abs(random.gauss(0, 1.5))), 2
                )
            else:
                ride['route_deviation_km'] = round(
                    max(ride['route_deviation_km'], base_dist * random.uniform(0.35, 4.0)), 2
                )

        elif fraud_type == 'ACCOUNT_TAKEOVER_RIDE':
            # Aparelho novo na primeira corrida após a tomada de conta — comum,
            # não universal: parte dos ATO usa sessão já ativa no aparelho da
            # própria vítima.
            ride['new_device_first_ride'] = random.random() < _rate("ride.ato_new_device_prob")
            # Takeover followed immediately by ride — short acceptance window
            if ride.get('accept_datetime') and ride.get('request_datetime'):
                from datetime import timedelta as _td
                req_ts = ride['request_datetime']
                # Override to < 10 min from request (ATO attackers are fast)
                ride['wait_time_minutes'] = random.randint(1, 5)

        elif fraud_type == 'GPS_SPOOFING':
            # Coordenadas forjadas. Log-normal em vez de uniform(2, 15): o piso
            # de 2 km deixava a faixa [0, 2] exclusiva do legítimo, e o teto de
            # 15 deixava tudo acima exclusivo da fraude — dois cortes limpos.
            ride['route_deviation_km'] = round(
                max(ride['route_deviation_km'], random.lognormvariate(1.1, 0.9)), 2
            )

        elif fraud_type == 'GHOST_RIDE':
            # Sem passageiro real — o motorista simula a corrida.
            # `driver_rating = None` era exclusivo desta classe: corrida
            # legítima sem avaliação é comum (o passageiro simplesmente não
            # avalia), então a ausência sozinha não pode identificar fraude.
            if random.random() < _rate("ride.ghost_no_rating_prob"):
                ride['driver_rating'] = None
            # Nota 5 automática por script — mas passageiro real também dá 5.
            if random.random() < 0.85:
                ride['passenger_rating'] = 5

        return ride

    def generate_batch(
        self,
        count: int,
        drivers: List[Dict[str, Any]],
        passengers: List[Dict[str, Any]],
        start_id: int = 1,
        start_time: Optional[datetime] = None,
        time_span_hours: int = 24
    ) -> Iterator[Dict[str, Any]]:
        """
        Generate multiple rides.
        
        Args:
            count: Number of rides to generate
            drivers: List of driver dicts (need driver_id, operating_state)
            passengers: List of passenger dicts (need customer_id, endereco.estado, perfil_comportamental)
            start_id: Starting ID number
            start_time: Starting timestamp (defaults to now - time_span_hours)
            time_span_hours: Hours to spread rides over
        
        Yields:
            Ride data dictionaries
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=time_span_hours)

        if not drivers or not passengers:
            return

        for i in range(count):
            # Generate timestamp within time span
            offset_seconds = random.randint(0, time_span_hours * 3600)
            timestamp = start_time + timedelta(seconds=offset_seconds)

            # Select random driver and passenger
            driver = random.choice(drivers)
            passenger = random.choice(passengers)

            # Get passenger state
            passenger_state = passenger.get('endereco', {}).get('estado', 'SP')
            if isinstance(passenger_state, str) and len(passenger_state) != 2:
                # Try to extract from nested structure
                passenger_state = 'SP'

            passenger_profile = passenger.get('perfil_comportamental')

            ride_id = f"RIDE_{start_id + i:012d}"

            yield self.generate(
                ride_id=ride_id,
                driver_id=driver['driver_id'],
                passenger_id=passenger['customer_id'],
                timestamp=timestamp,
                passenger_state=passenger_state,
                passenger_profile=passenger_profile,
            )

    def generate_index(self, ride_data: Dict[str, Any]) -> RideIndex:
        """
        Create a lightweight index from ride data.
        
        Args:
            ride_data: Full ride dictionary
        
        Returns:
            RideIndex with essential fields for lookups
        """
        pickup = ride_data.get('pickup_location', {})
        city = pickup.get('city', '') if isinstance(pickup, dict) else ''

        return RideIndex(
            ride_id=ride_data['ride_id'],
            driver_id=ride_data['driver_id'],
            passenger_id=ride_data['passenger_id'],
            app=ride_data['app'],
            city=city,
        )
