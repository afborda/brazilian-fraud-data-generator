"""
Connection module for streaming data to various targets.
"""

from .base import ConnectionProtocol
from .kafka_connection import KafkaConnection
from .webhook_connection import WebhookConnection
from .stdout_connection import StdoutConnection

# Registry of available connections
CONNECTIONS = {
    'kafka': KafkaConnection,
    'webhook': WebhookConnection,
    'stdout': StdoutConnection,
}


def get_connection(target: str) -> ConnectionProtocol:
    """Get a connection instance by target name."""
    if target not in CONNECTIONS:
        available = ', '.join(CONNECTIONS.keys())
        raise ValueError(f"Unknown target '{target}'. Available: {available}")
    return CONNECTIONS[target]()


def list_targets() -> list:
    """List available connection targets."""
    return list(CONNECTIONS.keys())


def is_target_available(target: str) -> bool:
    """Check if a target is available (dependencies installed)."""
    if target not in CONNECTIONS:
        return False
    return CONNECTIONS[target].is_available()


__all__ = [
    'ConnectionProtocol',
    'KafkaConnection',
    'WebhookConnection',
    'StdoutConnection',
    'get_connection',
    'list_targets',
    'is_target_available',
]
