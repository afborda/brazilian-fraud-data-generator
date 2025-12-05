"""
Parquet exporter for Brazilian Fraud Data Generator.

Requires pyarrow: pip install pyarrow
"""

from typing import List, Dict, Any, Iterator, Optional
from .base import ExporterProtocol

# Lazy import for optional dependency
_pyarrow_available = None
_pandas_available = None


def _check_pyarrow():
    """Check if pyarrow is available."""
    global _pyarrow_available
    if _pyarrow_available is None:
        try:
            import pyarrow
            _pyarrow_available = True
        except ImportError:
            _pyarrow_available = False
    return _pyarrow_available


def _check_pandas():
    """Check if pandas is available."""
    global _pandas_available
    if _pandas_available is None:
        try:
            import pandas
            _pandas_available = True
        except ImportError:
            _pandas_available = False
    return _pandas_available


class ParquetExporter(ExporterProtocol):
    """
    Export data to Apache Parquet format.
    
    Parquet is a columnar storage format ideal for:
    - Analytics workloads
    - Large datasets
    - Efficient compression
    - Schema preservation
    
    Requires: pip install pyarrow pandas
    """
    
    def __init__(
        self,
        compression: str = 'snappy',
        row_group_size: int = 100000
    ):
        """
        Initialize Parquet exporter.
        
        Args:
            compression: Compression codec ('snappy', 'gzip', 'brotli', 'zstd', None)
            row_group_size: Number of rows per row group
        """
        if not _check_pyarrow():
            raise ImportError(
                "pyarrow is required for Parquet export. "
                "Install with: pip install pyarrow"
            )
        if not _check_pandas():
            raise ImportError(
                "pandas is required for Parquet export. "
                "Install with: pip install pandas"
            )
        
        self.compression = compression
        self.row_group_size = row_group_size
    
    @property
    def extension(self) -> str:
        return '.parquet'
    
    @property
    def format_name(self) -> str:
        return 'Parquet'
    
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '_'
    ) -> Dict[str, Any]:
        """Flatten nested dictionary for Parquet (uses underscore separator)."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """Export records to Parquet file."""
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        self.ensure_directory(output_path)
        
        if not data:
            return 0
        
        # Flatten nested dictionaries
        flat_data = [self._flatten_dict(record) for record in data]
        
        # Create DataFrame
        df = pd.DataFrame(flat_data)
        
        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)
        
        if append:
            # For append, we need to read existing and concatenate
            try:
                existing_table = pq.read_table(output_path)
                table = pa.concat_tables([existing_table, table])
            except FileNotFoundError:
                pass  # File doesn't exist, will create new
        
        # Write Parquet file
        pq.write_table(
            table,
            output_path,
            compression=self.compression,
            row_group_size=self.row_group_size
        )
        
        return len(data)
    
    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 100000
    ) -> int:
        """Export iterator data to Parquet file using streaming."""
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        self.ensure_directory(output_path)
        
        total_count = 0
        writer = None
        schema = None
        
        try:
            batch = []
            for record in data_iterator:
                batch.append(self._flatten_dict(record))
                
                if len(batch) >= batch_size:
                    df = pd.DataFrame(batch)
                    table = pa.Table.from_pandas(df)
                    
                    if writer is None:
                        schema = table.schema
                        writer = pq.ParquetWriter(
                            output_path,
                            schema,
                            compression=self.compression
                        )
                    
                    writer.write_table(table)
                    total_count += len(batch)
                    batch = []
            
            # Write remaining records
            if batch:
                df = pd.DataFrame(batch)
                table = pa.Table.from_pandas(df)
                
                if writer is None:
                    schema = table.schema
                    writer = pq.ParquetWriter(
                        output_path,
                        schema,
                        compression=self.compression
                    )
                
                writer.write_table(table)
                total_count += len(batch)
        
        finally:
            if writer is not None:
                writer.close()
        
        return total_count


class ParquetPartitionedExporter(ParquetExporter):
    """
    Export data to partitioned Parquet dataset.
    
    Useful for very large datasets that benefit from
    partition-based querying (e.g., by date or estado).
    """
    
    def __init__(
        self,
        partition_cols: List[str] = None,
        compression: str = 'snappy'
    ):
        """
        Initialize partitioned Parquet exporter.
        
        Args:
            partition_cols: Columns to partition by (e.g., ['estado', 'date'])
            compression: Compression codec
        """
        super().__init__(compression=compression)
        self.partition_cols = partition_cols or []
    
    @property
    def format_name(self) -> str:
        return 'Partitioned Parquet'
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """Export records to partitioned Parquet dataset."""
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        self.ensure_directory(output_path)
        
        if not data:
            return 0
        
        # Flatten nested dictionaries
        flat_data = [self._flatten_dict(record) for record in data]
        
        # Create DataFrame
        df = pd.DataFrame(flat_data)
        
        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)
        
        # Write partitioned dataset
        pq.write_to_dataset(
            table,
            root_path=output_path,
            partition_cols=self.partition_cols if self.partition_cols else None,
            compression=self.compression,
            existing_data_behavior='overwrite_or_ignore' if append else 'delete_matching'
        )
        
        return len(data)
