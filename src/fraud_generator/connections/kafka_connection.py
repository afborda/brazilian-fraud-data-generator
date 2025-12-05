"""
Kafka connection for streaming transactions.
"""

import json
from typing import Dict, Any, Optional

from .base import ConnectionProtocol


class KafkaConnection(ConnectionProtocol):
    """
    Connection for streaming data to Apache Kafka.
    
    Requires: pip install kafka-python
    
    Usage:
        conn = KafkaConnection()
        conn.connect(bootstrap_servers='localhost:9092', topic='transactions')
        conn.send({'transaction_id': '123', 'valor': 100.0})
        conn.close()
    """
    
    name = "Apache Kafka"
    
    def __init__(self):
        self.producer = None
        self.default_topic = None
        self._connected = False
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if kafka-python is installed."""
        try:
            import kafka
            return True
        except ImportError:
            return False
    
    def connect(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'transactions',
        **kwargs
    ) -> None:
        """
        Connect to Kafka broker.
        
        Args:
            bootstrap_servers: Kafka broker address(es)
            topic: Default topic to send messages to
            **kwargs: Additional KafkaProducer configuration
        """
        if not self.is_available():
            raise ImportError(
                "kafka-python is not installed. "
                "Install with: pip install kafka-python"
            )
        
        from kafka import KafkaProducer
        
        self.default_topic = topic
        
        # Default configuration
        producer_config = {
            'bootstrap_servers': bootstrap_servers,
            'value_serializer': lambda v: json.dumps(v, default=str).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            'acks': 'all',
            'retries': 3,
        }
        
        # Override with user config
        producer_config.update(kwargs)
        
        self.producer = KafkaProducer(**producer_config)
        self._connected = True
    
    def send(
        self,
        data: Dict[str, Any],
        topic: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send a record to Kafka.
        
        Args:
            data: Dictionary to send as JSON
            topic: Topic to send to (uses default if not specified)
            key: Message key (optional)
        
        Returns:
            True if message was sent successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        target_topic = topic or self.default_topic
        
        try:
            future = self.producer.send(
                target_topic,
                value=data,
                key=key
            )
            # Wait for send to complete (with timeout)
            future.get(timeout=10)
            return True
        except Exception as e:
            print(f"❌ Kafka send error: {e}")
            return False
    
    def flush(self) -> None:
        """Flush pending messages."""
        if self.producer:
            self.producer.flush()
    
    def close(self) -> None:
        """Close the Kafka producer."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            self._connected = False
