"""
Data models for Ride-Share entities: Location, Driver, Ride.
Uses dataclasses following the pattern of models/customer.py.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Optional, Dict, Any, List, NamedTuple, Tuple
import json


# =============================================================================
# LOCATION
# =============================================================================

@dataclass
class Location:
    """
    Geographic location with POI (Point of Interest) information.
    
    Attributes:
        lat: Latitude coordinate
        lon: Longitude coordinate
        name: Name of the location/POI
        poi_type: Type of POI (AEROPORTO, SHOPPING, HOSPITAL, etc.)
        city: City name
        state: State code (e.g., 'SP', 'RJ')
    """
    lat: float
    lon: float
    name: str
    poi_type: str
    city: str
    state: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'lat': self.lat,
            'lon': self.lon,
            'name': self.name,
            'poi_type': self.poi_type,
            'city': self.city,
            'state': self.state,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Location':
        """Create Location from dictionary."""
        return cls(
            lat=data['lat'],
            lon=data['lon'],
            name=data['name'],
            poi_type=data['poi_type'],
            city=data['city'],
            state=data['state'],
        )


# =============================================================================
# DRIVER
# =============================================================================

@dataclass
class Driver:
    """
    Rideshare driver data model.
    
    Attributes:
        driver_id: Unique identifier for the driver
        name: Full name
        cpf: CPF number (valid)
        cnh_number: CNH (driver's license) number - 11 digits
        cnh_category: CNH category (B, AB, C, D, E)
        cnh_expiration: CNH expiration date
        phone: Phone number
        email: Email address
        vehicle_plate: Vehicle license plate (Mercosul or old format)
        vehicle_brand: Vehicle brand (e.g., 'Hyundai', 'Chevrolet')
        vehicle_model: Vehicle model (e.g., 'HB20', 'Onix')
        vehicle_year: Vehicle year (2015-2025)
        vehicle_color: Vehicle color
        rating: Driver rating (1.0 to 5.0)
        trips_completed: Total number of trips completed
        registration_date: Date when driver registered
        active_apps: List of apps the driver is active on
        operating_city: City where driver operates
        operating_state: State where driver operates
        categories_enabled: List of enabled ride categories
        is_active: Whether driver is currently active
    """
    driver_id: str
    name: str  # nome
    cpf: str
    cnh_number: str  # cnh_numero
    cnh_category: str  # cnh_categoria
    cnh_expiration: date  # cnh_validade
    phone: str  # telefone
    email: str
    vehicle_plate: str
    vehicle_brand: str
    vehicle_model: str
    vehicle_year: int
    vehicle_color: str
    rating: float
    trips_completed: int
    registration_date: datetime
    active_apps: List[str]
    operating_city: str
    operating_state: str
    categories_enabled: List[str]
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        return {
            'driver_id': self.driver_id,
            'name': self.name,
            'cpf': self.cpf,
            'cnh_number': self.cnh_number,
            'cnh_category': self.cnh_category,
            'cnh_expiration': self.cnh_expiration.isoformat() if isinstance(self.cnh_expiration, date) else self.cnh_expiration,
            'phone': self.phone,
            'email': self.email,
            'vehicle_plate': self.vehicle_plate,
            'vehicle_brand': self.vehicle_brand,
            'vehicle_model': self.vehicle_model,
            'vehicle_year': self.vehicle_year,
            'vehicle_color': self.vehicle_color,
            'rating': round(self.rating, 2),
            'trips_completed': self.trips_completed,
            'registration_date': self.registration_date.isoformat() if isinstance(self.registration_date, datetime) else self.registration_date,
            'active_apps': self.active_apps,
            'operating_city': self.operating_city,
            'operating_state': self.operating_state,
            'categories_enabled': self.categories_enabled,
            'is_active': self.is_active,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Driver':
        """Create Driver from dictionary."""
        # Handle date conversions
        cnh_expiration = data.get('cnh_expiration')
        if isinstance(cnh_expiration, str):
            cnh_expiration = date.fromisoformat(cnh_expiration)
        
        registration_date = data.get('registration_date')
        if isinstance(registration_date, str):
            registration_date = datetime.fromisoformat(registration_date)
        
        return cls(
            driver_id=data['driver_id'],
            name=data['name'],
            cpf=data['cpf'],
            cnh_number=data['cnh_number'],
            cnh_category=data['cnh_category'],
            cnh_expiration=cnh_expiration,
            phone=data['phone'],
            email=data['email'],
            vehicle_plate=data['vehicle_plate'],
            vehicle_brand=data['vehicle_brand'],
            vehicle_model=data['vehicle_model'],
            vehicle_year=data['vehicle_year'],
            vehicle_color=data['vehicle_color'],
            rating=data['rating'],
            trips_completed=data['trips_completed'],
            registration_date=registration_date,
            active_apps=data['active_apps'],
            operating_city=data['operating_city'],
            operating_state=data['operating_state'],
            categories_enabled=data['categories_enabled'],
            is_active=data.get('is_active', True),
        )


# =============================================================================
# RIDE
# =============================================================================

@dataclass
class Ride:
    """
    Rideshare ride/trip data model.
    
    Attributes:
        ride_id: Unique identifier for the ride
        timestamp: Event timestamp
        app: Rideshare app (UBER, 99, CABIFY, INDRIVER)
        category: Ride category (UberX, Pop, Black, etc.)
        driver_id: ID of the driver
        passenger_id: ID of the passenger (customer_id)
        pickup_location: Pickup location with POI info
        dropoff_location: Dropoff location with POI info
        request_datetime: When ride was requested
        accept_datetime: When driver accepted (None if not accepted)
        pickup_datetime: When passenger was picked up (None if not picked up)
        dropoff_datetime: When ride ended (None if not completed)
        distance_km: Distance traveled in kilometers
        duration_minutes: Ride duration in minutes
        wait_time_minutes: Time passenger waited for driver
        base_fare: Base fare before surge
        surge_multiplier: Surge pricing multiplier
        final_fare: Final fare paid
        driver_pay: Amount driver receives
        platform_fee: Platform commission
        tip: Tip amount
        payment_method: Payment method used
        status: Ride status
        driver_rating: Rating given to driver (1-5, None if not rated)
        passenger_rating: Rating given to passenger (1-5, None if not rated)
        cancellation_reason: Reason for cancellation (None if completed)
        weather_condition: Weather during ride
        temperature: Temperature in Celsius
        is_fraud: Whether ride is fraudulent
        fraud_type: Type of fraud (None if legitimate)
    """
    ride_id: str
    timestamp: datetime
    app: str
    category: str
    driver_id: str
    passenger_id: str
    pickup_location: Location
    dropoff_location: Location
    request_datetime: datetime
    accept_datetime: Optional[datetime]
    pickup_datetime: Optional[datetime]
    dropoff_datetime: Optional[datetime]
    distance_km: float
    duration_minutes: int
    wait_time_minutes: int
    base_fare: float
    surge_multiplier: float
    final_fare: float
    driver_pay: float
    platform_fee: float
    tip: float
    payment_method: str
    status: str
    driver_rating: Optional[int]
    passenger_rating: Optional[int]
    cancellation_reason: Optional[str]
    weather_condition: str
    temperature: float
    is_fraud: bool
    fraud_type: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        def format_datetime(dt: Optional[datetime]) -> Optional[str]:
            if dt is None:
                return None
            return dt.isoformat() if isinstance(dt, datetime) else dt
        
        return {
            'ride_id': self.ride_id,
            'timestamp': format_datetime(self.timestamp),
            'app': self.app,
            'category': self.category,
            'driver_id': self.driver_id,
            'passenger_id': self.passenger_id,
            'pickup_location': self.pickup_location.to_dict() if isinstance(self.pickup_location, Location) else self.pickup_location,
            'dropoff_location': self.dropoff_location.to_dict() if isinstance(self.dropoff_location, Location) else self.dropoff_location,
            'request_datetime': format_datetime(self.request_datetime),
            'accept_datetime': format_datetime(self.accept_datetime),
            'pickup_datetime': format_datetime(self.pickup_datetime),
            'dropoff_datetime': format_datetime(self.dropoff_datetime),
            'distance_km': round(self.distance_km, 2),
            'duration_minutes': self.duration_minutes,
            'wait_time_minutes': self.wait_time_minutes,
            'base_fare': round(self.base_fare, 2),
            'surge_multiplier': round(self.surge_multiplier, 2),
            'final_fare': round(self.final_fare, 2),
            'driver_pay': round(self.driver_pay, 2),
            'platform_fee': round(self.platform_fee, 2),
            'tip': round(self.tip, 2),
            'payment_method': self.payment_method,
            'status': self.status,
            'driver_rating': self.driver_rating,
            'passenger_rating': self.passenger_rating,
            'cancellation_reason': self.cancellation_reason,
            'weather_condition': self.weather_condition,
            'temperature': round(self.temperature, 1),
            'is_fraud': self.is_fraud,
            'fraud_type': self.fraud_type,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ride':
        """Create Ride from dictionary."""
        def parse_datetime(value: Optional[str]) -> Optional[datetime]:
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            return datetime.fromisoformat(value)
        
        # Handle nested Location objects
        pickup_data = data.get('pickup_location', {})
        if isinstance(pickup_data, dict):
            pickup_location = Location.from_dict(pickup_data)
        else:
            pickup_location = pickup_data
        
        dropoff_data = data.get('dropoff_location', {})
        if isinstance(dropoff_data, dict):
            dropoff_location = Location.from_dict(dropoff_data)
        else:
            dropoff_location = dropoff_data
        
        return cls(
            ride_id=data['ride_id'],
            timestamp=parse_datetime(data['timestamp']),
            app=data['app'],
            category=data['category'],
            driver_id=data['driver_id'],
            passenger_id=data['passenger_id'],
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            request_datetime=parse_datetime(data['request_datetime']),
            accept_datetime=parse_datetime(data.get('accept_datetime')),
            pickup_datetime=parse_datetime(data.get('pickup_datetime')),
            dropoff_datetime=parse_datetime(data.get('dropoff_datetime')),
            distance_km=data['distance_km'],
            duration_minutes=data['duration_minutes'],
            wait_time_minutes=data['wait_time_minutes'],
            base_fare=data['base_fare'],
            surge_multiplier=data['surge_multiplier'],
            final_fare=data['final_fare'],
            driver_pay=data['driver_pay'],
            platform_fee=data['platform_fee'],
            tip=data['tip'],
            payment_method=data['payment_method'],
            status=data['status'],
            driver_rating=data.get('driver_rating'),
            passenger_rating=data.get('passenger_rating'),
            cancellation_reason=data.get('cancellation_reason'),
            weather_condition=data['weather_condition'],
            temperature=data['temperature'],
            is_fraud=data['is_fraud'],
            fraud_type=data.get('fraud_type'),
        )


# =============================================================================
# INDEX CLASSES (Lightweight references for memory efficiency)
# =============================================================================

class DriverIndex(NamedTuple):
    """
    Lightweight driver index for memory-efficient processing.
    Uses NamedTuple for immutability and hashability.
    
    Memory usage: ~100-150 bytes vs ~500+ bytes for full Driver
    """
    driver_id: str
    operating_state: str
    operating_city: str
    active_apps: Tuple[str, ...]  # Tuple for hashability
    
    def __repr__(self) -> str:
        return f"DriverIndex({self.driver_id}, {self.operating_state}, {self.operating_city})"


class RideIndex(NamedTuple):
    """
    Lightweight ride index for memory-efficient processing.
    Uses NamedTuple for immutability and hashability.
    """
    ride_id: str
    driver_id: str
    passenger_id: str
    app: str
    city: str
    
    def __repr__(self) -> str:
        return f"RideIndex({self.ride_id}, {self.driver_id}, {self.passenger_id})"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_driver_index(driver_dict: Dict[str, Any]) -> DriverIndex:
    """
    Create a DriverIndex from a driver dictionary.
    
    Args:
        driver_dict: Dictionary containing driver data
    
    Returns:
        DriverIndex with essential fields
    """
    active_apps = driver_dict.get('active_apps', [])
    if isinstance(active_apps, list):
        active_apps = tuple(active_apps)
    
    return DriverIndex(
        driver_id=driver_dict['driver_id'],
        operating_state=driver_dict['operating_state'],
        operating_city=driver_dict['operating_city'],
        active_apps=active_apps,
    )


def create_ride_index(ride_dict: Dict[str, Any]) -> RideIndex:
    """
    Create a RideIndex from a ride dictionary.
    
    Args:
        ride_dict: Dictionary containing ride data
    
    Returns:
        RideIndex with essential fields
    """
    # Get city from pickup location
    pickup = ride_dict.get('pickup_location', {})
    city = pickup.get('city', '') if isinstance(pickup, dict) else ''
    
    return RideIndex(
        ride_id=ride_dict['ride_id'],
        driver_id=ride_dict['driver_id'],
        passenger_id=ride_dict['passenger_id'],
        app=ride_dict['app'],
        city=city,
    )
