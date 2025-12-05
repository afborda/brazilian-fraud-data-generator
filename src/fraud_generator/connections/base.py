"""
Base connection protocol for streaming targets.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ConnectionProtocol(ABC):
    """
    Abstract base class for all streaming connections.
    
    Implements the Strategy pattern for different output targets.
    All connections must implement connect, send, and close methods.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this connection."""
        pass
    
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if required dependencies are installed."""
        pass
    
    @abstractmethod
    def connect(self, **kwargs) -> None:
        """
        Establish connection to the target.
        
        Args:
            **kwargs: Connection-specific parameters
        """
        pass
    
    @abstractmethod
    def send(self, data: Dict[str, Any], **kwargs) -> bool:
        """
        Send a single record to the target.
        
        Args:
            data: Dictionary to send
            **kwargs: Additional parameters (topic, headers, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def send_batch(self, records: List[Dict[str, Any]], **kwargs) -> int:
        """
        Send multiple records to the target.
        
        Args:
            records: List of dictionaries to send
            **kwargs: Additional parameters
        
        Returns:
            Number of records successfully sent
        """
        success_count = 0
        for record in records:
            if self.send(record, **kwargs):
                success_count += 1
        return success_count
    
    @abstractmethod
    def close(self) -> None:
        """Close the connection and release resources."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
