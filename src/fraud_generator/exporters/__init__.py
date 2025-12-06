"""
Exporters package for Brazilian Fraud Data Generator.

Provides multiple export formats using the Strategy pattern:
- JSON Lines (.jsonl) - Default, streaming-friendly
- JSON Array (.json) - Single file with array
- CSV (.csv) - Tabular format
- TSV (.tsv) - Tab-separated
- Parquet (.parquet) - Columnar format for analytics
- MinIO (s3://) - Direct upload to MinIO/S3
"""

from typing import Optional
from .base import ExporterProtocol, ExportStats
from .json_exporter import JSONExporter, JSONArrayExporter
from .csv_exporter import CSVExporter, TSVExporter

# Conditional import for Parquet
try:
    from .parquet_exporter import ParquetExporter, ParquetPartitionedExporter
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    ParquetExporter = None
    ParquetPartitionedExporter = None

# Conditional import for MinIO
try:
    from .minio_exporter import MinIOExporter, MinIOStreamWriter, is_minio_available, parse_minio_url
    MINIO_AVAILABLE = is_minio_available()
except ImportError:
    MINIO_AVAILABLE = False
    MinIOExporter = None
    MinIOStreamWriter = None
    parse_minio_url = None
    def is_minio_available():
        return False


# Format registry
EXPORTERS = {
    'jsonl': JSONExporter,
    'json': JSONArrayExporter,
    'csv': CSVExporter,
    'tsv': TSVExporter,
}

if PARQUET_AVAILABLE:
    EXPORTERS['parquet'] = ParquetExporter
    EXPORTERS['parquet_partitioned'] = ParquetPartitionedExporter


def get_exporter(format_name: str, **kwargs) -> ExporterProtocol:
    """
    Get an exporter instance by format name.
    
    Args:
        format_name: Format name ('jsonl', 'json', 'csv', 'tsv', 'parquet')
        **kwargs: Additional arguments for the exporter constructor
    
    Returns:
        Exporter instance
    
    Raises:
        ValueError: If format is not supported
        ImportError: If format requires missing dependencies
    
    Example:
        >>> exporter = get_exporter('csv')
        >>> exporter.export_batch(data, 'output.csv')
        
        >>> exporter = get_exporter('parquet', compression='gzip')
        >>> exporter.export_batch(data, 'output.parquet')
    """
    format_lower = format_name.lower()
    
    # Handle aliases
    aliases = {
        'json_lines': 'jsonl',
        'jsonlines': 'jsonl',
        'json-lines': 'jsonl',
        'json_array': 'json',
        'tab': 'tsv',
        'pq': 'parquet',
    }
    format_lower = aliases.get(format_lower, format_lower)
    
    if format_lower not in EXPORTERS:
        available = ', '.join(EXPORTERS.keys())
        raise ValueError(
            f"Unsupported format: {format_name}. "
            f"Available formats: {available}"
        )
    
    exporter_class = EXPORTERS[format_lower]
    
    if exporter_class is None:
        raise ImportError(
            f"Format '{format_name}' requires additional dependencies. "
            "Install with: pip install pyarrow pandas"
        )
    
    return exporter_class(**kwargs)


def list_formats() -> list:
    """Return list of available export formats."""
    return list(EXPORTERS.keys())


def is_format_available(format_name: str) -> bool:
    """Check if a format is available."""
    format_lower = format_name.lower()
    return format_lower in EXPORTERS and EXPORTERS.get(format_lower) is not None


def get_minio_exporter(
    minio_url: str,
    endpoint_url: str = None,
    access_key: str = None,
    secret_key: str = None,
    partition_by_date: bool = True,
    **kwargs
) -> 'MinIOExporter':
    """
    Get a MinIO exporter configured for a specific URL.
    
    Args:
        minio_url: URL in format minio://bucket/prefix or s3://bucket/prefix
        endpoint_url: MinIO endpoint (default: from MINIO_ENDPOINT env)
        access_key: MinIO access key (default: from MINIO_ROOT_USER env)
        secret_key: MinIO secret key (default: from MINIO_ROOT_PASSWORD env)
        partition_by_date: Add YYYY/MM/DD to path
        **kwargs: Additional arguments for MinIOExporter
    
    Returns:
        Configured MinIOExporter instance
    
    Example:
        >>> exporter = get_minio_exporter('minio://fraud-data/raw/transactions')
        >>> exporter.export_batch(data, 'transactions_00001.jsonl')
    """
    if not MINIO_AVAILABLE:
        raise ImportError(
            "MinIO export requires boto3. "
            "Install with: pip install boto3"
        )
    
    bucket, prefix = parse_minio_url(minio_url)
    
    return MinIOExporter(
        endpoint_url=endpoint_url,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        prefix=prefix,
        partition_by_date=partition_by_date,
        **kwargs
    )


def is_minio_url(path: str) -> bool:
    """Check if path is a MinIO/S3 URL."""
    return path.startswith('minio://') or path.startswith('s3://')


__all__ = [
    'ExporterProtocol',
    'ExportStats',
    'JSONExporter',
    'JSONArrayExporter',
    'CSVExporter',
    'TSVExporter',
    'ParquetExporter',
    'ParquetPartitionedExporter',
    'MinIOExporter',
    'MinIOStreamWriter',
    'get_exporter',
    'get_minio_exporter',
    'is_minio_url',
    'list_formats',
    'is_format_available',
    'is_minio_available',
    'parse_minio_url',
    'PARQUET_AVAILABLE',
    'MINIO_AVAILABLE',
]
