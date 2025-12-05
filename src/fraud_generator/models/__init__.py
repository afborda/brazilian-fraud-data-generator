"""
Models package for Brazilian Fraud Data Generator.
Contains data classes for Customer, Device, Transaction, and Ride entities.
"""

from .customer import Customer, Address, CustomerIndex
from .device import Device, DeviceIndex
from .transaction import Transaction
from .ride import (
    Location,
    Driver,
    Ride,
    DriverIndex,
    RideIndex,
    create_driver_index,
    create_ride_index,
)

__all__ = [
    # Customer
    'Customer',
    'Address',
    'CustomerIndex',
    # Device
    'Device',
    'DeviceIndex',
    # Transaction
    'Transaction',
    # Ride
    'Location',
    'Driver',
    'Ride',
    'DriverIndex',
    'RideIndex',
    'create_driver_index',
    'create_ride_index',
]
