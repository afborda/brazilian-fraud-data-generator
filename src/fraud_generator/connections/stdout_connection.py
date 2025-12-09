"""
Stdout connection for debugging and testing.
"""

import json
import sys
from typing import Dict, Any, Optional

from .base import ConnectionProtocol


class StdoutConnection(ConnectionProtocol):
    """
    Connection that prints data to stdout (for debugging/testing).
    
    No dependencies required.
    
    Usage:
        conn = StdoutConnection()
        conn.connect(pretty=True)
        conn.send({'transaction_id': '123', 'valor': 100.0})
        conn.close()
    """
    
    name = "Standard Output"
    
    def __init__(self):
        self.pretty = False
        self.output = sys.stdout
        self._connected = False
        self._count = 0
    
    @classmethod
    def is_available(cls) -> bool:
        """Always available - no dependencies."""
        return True
    
    def connect(
        self,
        pretty: bool = False,
        output=None,
        **kwargs
    ) -> None:
        """
        Configure stdout output.
        
        Args:
            pretty: If True, pretty-print JSON with indentation
            output: Output stream (defaults to sys.stdout)
        """
        self.pretty = pretty
        self.output = output or sys.stdout
        self._connected = True
        self._count = 0
    
    def send(
        self,
        data: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Print a record to stdout.
        
        Args:
            data: Dictionary to print as JSON
        
        Returns:
            Always True
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            if self.pretty:
                output = json.dumps(data, indent=2, default=str, ensure_ascii=False)
            else:
                output = json.dumps(data, default=str, ensure_ascii=False)
            
            print(output, file=self.output)
            self._count += 1
            return True
        except Exception as e:
            print(f"❌ Stdout error: {e}", file=sys.stderr)
            return False
    
    def close(self) -> None:
        """Close the connection."""
        if self.output and self.output != sys.stdout:
            try:
                self.output.flush()
            except Exception:
                pass
        self._connected = False
    
    @property
    def count(self) -> int:
        """Number of records sent."""
        return self._count
