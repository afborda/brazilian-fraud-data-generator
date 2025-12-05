"""
Models package for Brazilian Fraud Data Generator.
Contains data classes for Customer, Device, and Transaction entities.
"""

from .customer import Customer, Address, CustomerIndex
from .device import Device, DeviceIndex
from .transaction import Transaction

__all__ = [
    'Customer',
    'Address',
    'CustomerIndex',
    'Device',
    'DeviceIndex',
    'Transaction',
]
