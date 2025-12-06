"""
Data model for Device entity using dataclasses.
"""

from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional, Dict, Any
import json


@dataclass
class Device:
    """
    Device data model for Brazilian financial transactions.
    
    Represents a device used to perform financial transactions.
    
    Attributes:
        device_id: Unique identifier for the device
        customer_id: Associated customer ID
        type: Device type (SMARTPHONE, DESKTOP, TABLET)
        manufacturer: Device manufacturer
        model: Device model
        operating_system: Operating system
        fingerprint: Device fingerprint hash
        first_use: First use date
        is_trusted: Whether device is trusted
        is_rooted_jailbroken: Whether device is rooted/jailbroken
    """
    device_id: str
    customer_id: str
    type: str  # tipo
    manufacturer: str  # fabricante
    model: str  # modelo
    operating_system: str  # sistema_operacional
    fingerprint: str
    first_use: date  # primeiro_uso
    is_trusted: bool = True
    is_rooted_jailbroken: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        return {
            'device_id': self.device_id,
            'customer_id': self.customer_id,
            'type': self.type,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'operating_system': self.operating_system,
            'fingerprint': self.fingerprint,
            'first_use': self.first_use.isoformat() if isinstance(self.first_use, date) else self.first_use,
            'is_trusted': self.is_trusted,
            'is_rooted_jailbroken': self.is_rooted_jailbroken,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Device':
        """Create Device from dictionary."""
        first_use = data.get('first_use')
        if isinstance(first_use, str):
            first_use = date.fromisoformat(first_use)
        
        return cls(
            device_id=data['device_id'],
            customer_id=data['customer_id'],
            type=data['type'],
            manufacturer=data['manufacturer'],
            model=data['model'],
            operating_system=data['operating_system'],
            fingerprint=data['fingerprint'],
            first_use=first_use,
            is_trusted=data.get('is_trusted', True),
            is_rooted_jailbroken=data.get('is_rooted_jailbroken', False),
        )


@dataclass
class DeviceIndex:
    """
    Lightweight device index for memory-efficient processing.
    """
    device_id: str
    customer_id: str
    type: str  # tipo
    is_trusted: bool = True
