"""
Device generator for Brazilian Fraud Data Generator.
"""

import random
import hashlib
from datetime import date
from typing import Dict, Any, Optional, Iterator
from faker import Faker

from ..models.device import Device, DeviceIndex
from ..config.devices import (
    DEVICE_TYPES_LIST,
    DEVICE_TYPES_WEIGHTS,
    get_manufacturers_for_device_type,
    get_models_for_manufacturer,
    get_os_for_device_type,
    get_device_category,
)


class DeviceGenerator:
    """
    Generator for realistic device data.
    
    Generates devices with appropriate manufacturers, models,
    and OS versions based on device type.
    """
    
    def __init__(
        self,
        locale: str = 'pt_BR',
        seed: Optional[int] = None
    ):
        """
        Initialize device generator.
        
        Args:
            locale: Faker locale
            seed: Random seed for reproducibility
        """
        self.fake = Faker(locale)
        
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
    
    def generate(
        self,
        device_id: str,
        customer_id: str,
        preferred_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a single device.
        
        Args:
            device_id: Unique identifier for the device
            customer_id: Associated customer ID
            preferred_type: Preferred device type (optional)
        
        Returns:
            Device data as dictionary
        """
        # Select device type
        if preferred_type and preferred_type in DEVICE_TYPES_LIST:
            device_type = preferred_type
        else:
            device_type = random.choices(
                DEVICE_TYPES_LIST,
                weights=DEVICE_TYPES_WEIGHTS
            )[0]
        
        # Get manufacturer and model
        manufacturers = get_manufacturers_for_device_type(device_type)
        manufacturer = random.choice(manufacturers)
        
        models = get_models_for_manufacturer(manufacturer)
        model = random.choice(models)
        
        # Get OS
        os_options = get_os_for_device_type(device_type)
        os_name = random.choice(os_options)
        
        # Generate fingerprint
        fingerprint = hashlib.sha256(
            f"{device_id}{random.random()}".encode()
        ).hexdigest()[:32]
        
        # First use date
        first_use = self.fake.date_between(start_date='-2y', end_date='today')
        
        # Trust and security status
        is_trusted = random.choices([True, False], weights=[85, 15])[0]
        is_rooted = random.choices([False, True], weights=[97, 3])[0]
        
        return {
            'device_id': device_id,
            'customer_id': customer_id,
            'type': get_device_category(device_type),
            'manufacturer': manufacturer,
            'model': model,
            'operating_system': os_name,
            'fingerprint': fingerprint,
            'first_use': first_use.isoformat(),
            'is_trusted': is_trusted,
            'is_rooted_jailbroken': is_rooted,
        }
    
    def generate_for_customer(
        self,
        customer_id: str,
        customer_profile: Optional[str] = None,
        start_device_id: int = 1,
        min_devices: int = 1,
        max_devices: int = 3
    ) -> Iterator[Dict[str, Any]]:
        """
        Generate devices for a customer.
        
        Args:
            customer_id: Customer identifier
            customer_profile: Customer's behavioral profile
            start_device_id: Starting device ID number
            min_devices: Minimum devices per customer
            max_devices: Maximum devices per customer
        
        Yields:
            Device data dictionaries
        """
        # Number of devices based on profile
        if customer_profile in ['young_digital', 'subscription_heavy']:
            num_devices = random.randint(2, max_devices)
        elif customer_profile == 'traditional_senior':
            num_devices = random.randint(1, 2)
        else:
            num_devices = random.randint(min_devices, max_devices)
        
        # Determine preferred device types based on profile
        preferred_types = self._get_preferred_types(customer_profile)
        
        for i in range(num_devices):
            device_id = f"DEV_{start_device_id + i:012d}"
            
            # First device is usually the most used type for profile
            if i == 0 and preferred_types:
                preferred = preferred_types[0]
            elif preferred_types:
                preferred = random.choice(preferred_types)
            else:
                preferred = None
            
            yield self.generate(device_id, customer_id, preferred_type=preferred)
    
    def generate_index(self, device_data: Dict[str, Any]) -> DeviceIndex:
        """Create a lightweight index from device data."""
        return DeviceIndex(
            device_id=device_data['device_id'],
            customer_id=device_data['customer_id'],
        )
    
    def _get_preferred_types(self, profile: Optional[str]) -> list:
        """Get preferred device types for a profile."""
        profile_preferences = {
            'young_digital': ['SMARTPHONE_ANDROID', 'SMARTPHONE_IOS'],
            'traditional_senior': ['SMARTPHONE_ANDROID', 'DESKTOP_WINDOWS'],
            'business_owner': ['SMARTPHONE_IOS', 'DESKTOP_WINDOWS', 'DESKTOP_MAC'],
            'high_spender': ['SMARTPHONE_IOS', 'DESKTOP_MAC'],
            'subscription_heavy': ['SMARTPHONE_ANDROID', 'SMARTPHONE_IOS', 'TABLET_ANDROID'],
            'family_provider': ['SMARTPHONE_ANDROID', 'DESKTOP_WINDOWS'],
        }
        return profile_preferences.get(profile, [])
