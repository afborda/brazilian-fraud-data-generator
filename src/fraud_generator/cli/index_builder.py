"""
Index builder — Phase 1 and Phase 3 of the generation pipeline.

Single responsibility: generate Customer/Device/Driver entities and
return lightweight index tuples that can be pickled to worker processes.
"""
import random
from typing import Dict, Any, List, Optional, Tuple

from fraud_generator.generators import CustomerGenerator, DeviceGenerator, DriverGenerator
from fraud_generator.utils import CustomerIndex, DeviceIndex, DriverIndex
from fraud_generator.config.geography import ESTADOS_BR


def _generate_location_cluster(state: str) -> tuple:
    """Generate 3-5 habitual location points for a customer in the given state.

    Returns a tuple of (lat, lon, weight) tuples representing:
    home (55%), work (20%), shopping (15%), other (10%).
    Each point is a small random offset from the state capital (~60 km max).
    """
    info = ESTADOS_BR.get(state, ESTADOS_BR['SP'])
    base_lat, base_lon = info['lat'], info['lon']
    home_lat   = base_lat + random.uniform(-0.25, 0.25)
    home_lon   = base_lon + random.uniform(-0.25, 0.25)
    work_lat   = home_lat + random.uniform(-0.20, 0.20)
    work_lon   = home_lon + random.uniform(-0.20, 0.20)
    shop_lat   = home_lat + random.uniform(-0.30, 0.30)
    shop_lon   = home_lon + random.uniform(-0.30, 0.30)
    other_lat  = base_lat + random.uniform(-0.40, 0.40)
    other_lon  = base_lon + random.uniform(-0.40, 0.40)
    return (
        (round(home_lat, 6),  round(home_lon, 6),  0.55),
        (round(work_lat, 6),  round(work_lon, 6),  0.20),
        (round(shop_lat, 6),  round(shop_lon, 6),  0.15),
        (round(other_lat, 6), round(other_lon, 6), 0.10),
    )


def generate_customers_and_devices(
    num_customers: int,
    use_profiles: bool,
    seed: Optional[int],
) -> Tuple[List[tuple], List[tuple], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate *num_customers* customers and their associated devices.

    Returns:
        (customer_indexes, device_indexes, customer_data, device_data)
        where *_indexes are lists of plain tuples (picklable for workers).
    """
    if seed is not None:
        random.seed(seed)

    customer_gen = CustomerGenerator(use_profiles=use_profiles, seed=seed)
    device_gen = DeviceGenerator(seed=seed)

    customer_indexes: List[tuple] = []
    device_indexes: List[tuple] = []
    customer_data: List[Dict[str, Any]] = []
    device_data: List[Dict[str, Any]] = []

    device_counter = 1

    for i in range(num_customers):
        customer_id = f"CUST_{i + 1:012d}"
        customer = customer_gen.generate(customer_id)
        customer_data.append(customer)

        _state = customer["address"]["state"]
        customer_idx = CustomerIndex(
            customer_id=customer["customer_id"],
            state=_state,
            profile=customer.get("behavioral_profile"),
            bank_code=customer.get("bank_code"),
            risk_level=customer.get("risk_level"),
            location_cluster=_generate_location_cluster(_state),
        )
        customer_indexes.append(tuple(customer_idx))

        profile = customer.get("behavioral_profile")
        for device in device_gen.generate_for_customer(
            customer_id, profile, start_device_id=device_counter
        ):
            device_data.append(device)
            device_idx = DeviceIndex(
                device_id=device["device_id"],
                customer_id=device["customer_id"],
                device_age_days=device.get("device_age_days", 365),
                emulator_detected=device.get("emulator_detected", False),
                vpn_active=device.get("vpn_active", False),
                ip_type=device.get("ip_type", "RESIDENTIAL"),
            )
            device_indexes.append(tuple(device_idx))
            device_counter += 1

    return customer_indexes, device_indexes, customer_data, device_data


def generate_drivers(
    num_drivers: int,
    seed: Optional[int],
) -> Tuple[List[tuple], List[Dict[str, Any]]]:
    """
    Generate *num_drivers* ride-share drivers.

    Returns:
        (driver_indexes, driver_data)
    """
    if seed is not None:
        random.seed(seed)

    driver_gen = DriverGenerator(seed=seed)

    driver_indexes: List[tuple] = []
    driver_data: List[Dict[str, Any]] = []

    for i in range(num_drivers):
        driver_id = f"DRV_{i + 1:010d}"
        driver = driver_gen.generate(driver_id)
        driver_data.append(driver)

        driver_idx = DriverIndex(
            driver_id=driver["driver_id"],
            operating_state=driver.get("operating_state", "SP"),
            operating_city=driver.get("operating_city", "São Paulo"),
            active_apps=tuple(driver.get("active_apps", [])),
        )
        driver_indexes.append(tuple(driver_idx))

    return driver_indexes, driver_data
