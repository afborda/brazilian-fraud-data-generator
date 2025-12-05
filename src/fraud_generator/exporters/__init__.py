"""
Exporters package for Brazilian Fraud Data Generator.

Provides multiple export formats using the Strategy pattern:
- JSON Lines (.jsonl) - Default, streaming-friendly
- JSON Array (.json) - Single file with array
- CSV (.csv) - Tabular format
- TSV (.tsv) - Tab-separated
- Parquet (.parquet) - Columnar format for analytics
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


__all__ = [
    'ExporterProtocol',
    'ExportStats',
    'JSONExporter',
    'JSONArrayExporter',
    'CSVExporter',
    'TSVExporter',
    'ParquetExporter',
    'ParquetPartitionedExporter',
    'get_exporter',
    'list_formats',
    'is_format_available',
    'PARQUET_AVAILABLE',
]
