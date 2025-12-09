"""
Webhook/HTTP connection for streaming transactions.
"""

import json
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import ConnectionProtocol


class WebhookConnection(ConnectionProtocol):
    """
    Connection for streaming data to HTTP endpoints (webhooks/REST APIs).
    
    Requires: pip install requests
    
    Usage:
        conn = WebhookConnection()
        conn.connect(url='http://api.example.com/transactions', method='POST')
        conn.send({'transaction_id': '123', 'valor': 100.0})
        conn.close()
    """
    
    name = "HTTP Webhook"
    
    def __init__(self):
        self.session = None
        self.url = None
        self.method = 'POST'
        self.headers = {}
        self.timeout = 30
        self.max_workers = 10
        self._executor = None
        self._connected = False
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if requests is installed."""
        try:
            import requests
            return True
        except ImportError:
            return False
    
    def connect(
        self,
        url: str,
        method: str = 'POST',
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        max_workers: int = 10,
        **kwargs
    ) -> None:
        """
        Configure the webhook connection.
        
        Args:
            url: Target URL for the webhook
            method: HTTP method (POST, PUT, PATCH)
            headers: HTTP headers to include
            timeout: Request timeout in seconds
            max_workers: Max concurrent requests
        """
        if not self.is_available():
            raise ImportError(
                "requests is not installed. "
                "Install with: pip install requests"
            )
        
        import requests
        
        self.url = url
        self.method = method.upper()
        self.timeout = timeout
        self.max_workers = max_workers
        
        # Default headers
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'BrazilianFraudGenerator/3.0',
        }
        if headers:
            self.headers.update(headers)
        
        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Thread pool for async requests
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._connected = True
    
    def send(
        self,
        data: Dict[str, Any],
        url: Optional[str] = None,
        async_mode: bool = False,
        **kwargs
    ) -> bool:
        """
        Send a record via HTTP.
        
        Args:
            data: Dictionary to send as JSON
            url: Override URL (uses default if not specified)
            async_mode: If True, don't wait for response
        
        Returns:
            True if request was successful (2xx status)
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        target_url = url or self.url
        
        try:
            response = self.session.request(
                method=self.method,
                url=target_url,
                json=data,
                timeout=self.timeout
            )
            return 200 <= response.status_code < 300
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return False
    
    def send_batch(
        self,
        records: List[Dict[str, Any]],
        **kwargs
    ) -> int:
        """
        Send multiple records concurrently.
        
        Args:
            records: List of dictionaries to send
        
        Returns:
            Number of successful requests
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        futures = []
        for record in records:
            future = self._executor.submit(self.send, record)
            futures.append(future)
        
        success_count = 0
        for future in as_completed(futures):
            try:
                if future.result():
                    success_count += 1
            except Exception:
                pass
        
        return success_count
    
    def close(self) -> None:
        """Close the HTTP session and thread pool."""
        if self._executor:
            self._executor.shutdown(wait=True)
        if self.session:
            self.session.close()
        self._connected = False
