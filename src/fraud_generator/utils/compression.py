"""
Native compression handlers for Phase 2.1 optimization.

Supports multiple compression backends:
- zstandard (fast, good compression)
- snappy (ultra-fast, lighter compression)
- gzip (fallback, pure Python)

All backends gracefully degrade if native libraries unavailable.
"""

import gzip
import io
from typing import Literal
from abc import ABC, abstractmethod


class CompressionBackend(ABC):
    """Abstract base for compression backends."""
    
    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Compress bytes."""
        pass
    
    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Decompress bytes."""
        pass
    
    @property
    @abstractmethod
    def extension(self) -> str:
        """File extension for this compression."""
        pass


class GzipCompressor(CompressionBackend):
    """Pure Python gzip compression (fallback)."""
    
    def __init__(self, level: int = 9):
        self.level = level
    
    def compress(self, data: bytes) -> bytes:
        """Compress with gzip."""
        return gzip.compress(data, compresslevel=self.level)
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress with gzip."""
        return gzip.decompress(data)
    
    @property
    def extension(self) -> str:
        return '.gz'
    
    def __repr__(self) -> str:
        return f"GzipCompressor(level={self.level})"


class ZstdCompressor(CompressionBackend):
    """Native zstandard compression (C library)."""
    
    def __init__(self, level: int = 1):
        try:
            import zstandard
            self.zstd = zstandard
            self.level = level
        except ImportError:
            raise ImportError(
                "zstandard not installed. "
                "Install with: pip install zstandard"
            )
    
    def compress(self, data: bytes) -> bytes:
        """Compress with zstandard."""
        cctx = self.zstd.ZstdCompressor(level=self.level)
        return cctx.compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress with zstandard."""
        dctx = self.zstd.ZstdDecompressor()
        return dctx.decompress(data)
    
    @property
    def extension(self) -> str:
        return '.zstd'
    
    def __repr__(self) -> str:
        return f"ZstdCompressor(level={self.level})"


class SnappyCompressor(CompressionBackend):
    """Fast snappy compression (C library)."""
    
    def __init__(self):
        try:
            import snappy
            self.snappy = snappy
        except ImportError:
            raise ImportError(
                "python-snappy not installed. "
                "Install with: pip install python-snappy"
            )
    
    def compress(self, data: bytes) -> bytes:
        """Compress with snappy."""
        return self.snappy.compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress with snappy."""
        return self.snappy.decompress(data)
    
    @property
    def extension(self) -> str:
        return '.snappy'
    
    def __repr__(self) -> str:
        return "SnappyCompressor()"


class CompressionHandler:
    """
    Factory for compression handlers with graceful fallback.
    
    Automatically falls back to gzip if native libraries unavailable.
    
    Usage:
        handler = CompressionHandler('zstd')
        compressed = handler.compress(data)
        decompressed = handler.decompress(compressed)
    """
    
    def __init__(
        self,
        algorithm: Literal['zstd', 'snappy', 'gzip', 'none'] = 'gzip',
        level: int = 1,
        verbose: bool = True
    ):
        """
        Initialize compression handler.
        
        Args:
            algorithm: Compression algorithm ('zstd', 'snappy', 'gzip', 'none')
            level: Compression level (1-22 for zstd, 1-9 for gzip)
            verbose: Print warnings on fallback
        """
        self.algorithm = algorithm
        self.level = level
        self.verbose = verbose
        self._backend = self._get_backend()
    
    def _get_backend(self) -> CompressionBackend:
        """Get compression backend with fallback to gzip."""
        if self.algorithm == 'none':
            return NoOpCompressor()
        
        if self.algorithm == 'zstd':
            try:
                return ZstdCompressor(level=self.level)
            except ImportError as e:
                if self.verbose:
                    print(f"⚠️  {e}\n   Falling back to gzip")
                return GzipCompressor()
        
        elif self.algorithm == 'snappy':
            try:
                return SnappyCompressor()
            except ImportError as e:
                if self.verbose:
                    print(f"⚠️  {e}\n   Falling back to gzip")
                return GzipCompressor()
        
        elif self.algorithm == 'gzip':
            return GzipCompressor(level=self.level)
        
        else:
            raise ValueError(f"Unknown compression algorithm: {self.algorithm}")
    
    def compress(self, data: bytes) -> bytes:
        """Compress data."""
        if not isinstance(data, bytes):
            raise TypeError(f"Expected bytes, got {type(data).__name__}")
        return self._backend.compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress data."""
        if not isinstance(data, bytes):
            raise TypeError(f"Expected bytes, got {type(data).__name__}")
        return self._backend.decompress(data)
    
    @property
    def extension(self) -> str:
        """File extension for this compression."""
        return self._backend.extension
    
    @property
    def backend_name(self) -> str:
        """Name of active backend."""
        return self._backend.__class__.__name__
    
    def __repr__(self) -> str:
        return f"CompressionHandler(algorithm={self.algorithm}, backend={self.backend_name})"


class NoOpCompressor(CompressionBackend):
    """No-op compressor (pass-through)."""
    
    def compress(self, data: bytes) -> bytes:
        """Return data unchanged."""
        return data
    
    def decompress(self, data: bytes) -> bytes:
        """Return data unchanged."""
        return data
    
    @property
    def extension(self) -> str:
        return ''
    
    def __repr__(self) -> str:
        return "NoOpCompressor()"


def get_compressor(
    algorithm: Literal['zstd', 'snappy', 'gzip', 'none'] = 'gzip',
    **kwargs
) -> CompressionHandler:
    """
    Convenience function to create compressor.
    
    Args:
        algorithm: Compression algorithm
        **kwargs: Additional arguments to CompressionHandler
    
    Returns:
        CompressionHandler instance
    """
    return CompressionHandler(algorithm=algorithm, **kwargs)
