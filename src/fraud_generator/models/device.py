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
        tipo: Device type (SMARTPHONE, DESKTOP, TABLET)
        fabricante: Device manufacturer
        modelo: Device model
        sistema_operacional: Operating system
        fingerprint: Device fingerprint hash
        primeiro_uso: First use date
        is_trusted: Whether device is trusted
        is_rooted_jailbroken: Whether device is rooted/jailbroken
    """
    device_id: str
    customer_id: str
    tipo: str
    fabricante: str
    modelo: str
    sistema_operacional: str
    fingerprint: str
    primeiro_uso: date
    is_trusted: bool = True
    is_rooted_jailbroken: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for JSON serialization."""
        return {
            'device_id': self.device_id,
            'customer_id': self.customer_id,
            'tipo': self.tipo,
            'fabricante': self.fabricante,
            'modelo': self.modelo,
            'sistema_operacional': self.sistema_operacional,
            'fingerprint': self.fingerprint,
            'primeiro_uso': self.primeiro_uso.isoformat() if isinstance(self.primeiro_uso, date) else self.primeiro_uso,
            'is_trusted': self.is_trusted,
            'is_rooted_jailbroken': self.is_rooted_jailbroken,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Device':
        """Create Device from dictionary."""
        primeiro_uso = data.get('primeiro_uso')
        if isinstance(primeiro_uso, str):
            primeiro_uso = date.fromisoformat(primeiro_uso)
        
        return cls(
            device_id=data['device_id'],
            customer_id=data['customer_id'],
            tipo=data['tipo'],
            fabricante=data['fabricante'],
            modelo=data['modelo'],
            sistema_operacional=data['sistema_operacional'],
            fingerprint=data['fingerprint'],
            primeiro_uso=primeiro_uso,
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
    tipo: str
    is_trusted: bool = True
