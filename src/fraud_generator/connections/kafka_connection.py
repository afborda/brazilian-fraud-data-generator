"""
Kafka connection for streaming transactions.
"""

import json
import time
import random
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
        max_retries: int = 30,
        initial_backoff: float = 1.0,
        max_backoff: float = 10.0,
        **kwargs
    ) -> None:
        """
        Connect to Kafka broker with exponential backoff retry.
        
        This method implements automatic retry with exponential backoff and jitter,
        which is crucial for Docker Compose environments where Kafka may still be
        initializing when the client attempts connection.
        
        Args:
            bootstrap_servers: Kafka broker address(es) - e.g., 'kafka:9092' or 'localhost:9092,localhost:9093'
            topic: Default topic to send messages to
            max_retries: Maximum number of connection attempts (default: 30 = ~5 minutes total wait)
            initial_backoff: Initial wait time in seconds (default: 1s, doubles each retry)
            max_backoff: Maximum wait time in seconds (default: 10s, prevents infinite doubling)
            **kwargs: Additional KafkaProducer configuration
        
        Raises:
            ImportError: If kafka-python is not installed
            ConnectionError: If unable to connect after max_retries attempts
            
        Note:
            This implements the exponential backoff pattern recommended by AWS and used
            by major projects like Spring Kafka, confluent-kafka, etc.
            See: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
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
        
        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                if attempt == 1:
                    print(f"📡 Connecting to Kafka ({bootstrap_servers})...", end=" ", flush=True)
                else:
                    print(f"   Retry {attempt}/{max_retries}...", end=" ", flush=True)
                
                self.producer = KafkaProducer(**producer_config)
                self._connected = True
                print("✅ Connected!")
                return
                
            except Exception as e:
                last_error = e
                
                if attempt == max_retries:
                    print(f"❌ Failed after {max_retries} attempts")
                    break
                
                # Calculate exponential backoff with jitter
                # Formula: min(initial_backoff * 2^(attempt-1), max_backoff) + random_jitter
                backoff = min(
                    initial_backoff * (2 ** (attempt - 1)),
                    max_backoff
                )
                jitter = random.uniform(0, backoff * 0.1)  # Add up to 10% jitter
                wait_time = backoff + jitter
                
                error_name = type(e).__name__
                print(f"retrying in {wait_time:.1f}s ({error_name})")
                time.sleep(wait_time)
        
        # If we got here, all retries failed
        error_msg = (
            f"Failed to connect to Kafka at '{bootstrap_servers}' "
            f"after {max_retries} attempts (waited ~{int(initial_backoff * (2**max_retries - 1))}s total). "
            f"Last error: {type(last_error).__name__}: {last_error}\n\n"
            f"Troubleshooting:\n"
            f"  1. Verify Kafka is running: docker ps | grep kafka\n"
            f"  2. Check Kafka logs: docker logs fraud_kafka\n"
            f"  3. Verify bootstrap_servers is correct (got: '{bootstrap_servers}')\n"
            f"  4. Check network connectivity: docker exec -it fraud_generator nc -zv kafka 9092\n"
            f"  5. For Docker Compose: ensure 'depends_on' is defined\n"
            f"  6. For Kubernetes: ensure Kafka service is accessible"
        )
        raise ConnectionError(error_msg)
    
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
