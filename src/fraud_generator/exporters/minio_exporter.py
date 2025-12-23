"""
MinIO Exporter for Brazilian Fraud Data Generator.

Uploads data directly to MinIO/S3-compatible storage.
Supports JSONL, CSV, and Parquet formats.
"""

import csv
import io
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Iterator, Optional, Literal
from urllib.parse import urlparse

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Optional dependencies for additional formats
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from .base import ExporterProtocol


def is_minio_available() -> bool:
    """Check if MinIO/S3 dependencies are available."""
    return BOTO3_AVAILABLE


def is_minio_parquet_available() -> bool:
    """Check if MinIO Parquet export is available."""
    return BOTO3_AVAILABLE and PYARROW_AVAILABLE and PANDAS_AVAILABLE


def parse_minio_url(url: str) -> tuple:
    """
    Parse MinIO URL into bucket and prefix.
    
    Args:
        url: URL in format minio://bucket/path/to/data or s3://bucket/path
        
    Returns:
        Tuple of (bucket, prefix)
    """
    parsed = urlparse(url)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip('/')
    return bucket, prefix


class MinIOExporter(ExporterProtocol):
    """
    Export data directly to MinIO/S3-compatible storage.
    
    Supports:
    - Direct upload to MinIO buckets
    - Partitioning by date (YYYY/MM/DD)
    - Automatic bucket creation
    - Multiple formats: JSONL, CSV, Parquet
    """
    
    SUPPORTED_FORMATS = ('jsonl', 'csv', 'parquet')
    SUPPORTED_COMPRESSIONS = ('zstd', 'snappy', 'gzip', 'brotli', 'none')
    
    def __init__(
        self,
        endpoint_url: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket: str = "fraud-data",
        prefix: str = "raw",
        partition_by_date: bool = True,
        region: str = "us-east-1",
        secure: bool = False,
        output_format: str = "jsonl",
        compression: str = "zstd",
    ):
        """
        Initialize MinIO exporter.
        
        Args:
            endpoint_url: MinIO endpoint (e.g., http://localhost:9000)
            access_key: MinIO access key (or AWS_ACCESS_KEY_ID)
            secret_key: MinIO secret key (or AWS_SECRET_ACCESS_KEY)
            bucket: Target bucket name
            prefix: Path prefix inside bucket (e.g., "raw/transactions")
            partition_by_date: If True, adds YYYY/MM/DD to path
            region: AWS region (ignored by MinIO but required)
            secure: Use HTTPS
            output_format: Output format ('jsonl', 'csv', 'parquet')
            compression: Compression for Parquet ('zstd', 'snappy', 'gzip', 'brotli', 'none')
        """
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for MinIO export. "
                "Install it with: pip install boto3"
            )
        
        # Validate format
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {output_format}. Supported: {self.SUPPORTED_FORMATS}")
        
        # Check Parquet dependencies
        if output_format == 'parquet' and not is_minio_parquet_available():
            raise ImportError(
                "pyarrow and pandas are required for Parquet export. "
                "Install with: pip install pyarrow pandas"
            )
        
        self._output_format = output_format
        self.compression = compression if compression != 'none' else None
        self.endpoint_url = endpoint_url or os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ROOT_USER") or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_ROOT_PASSWORD") or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = bucket
        self.prefix = prefix.strip('/')
        self.partition_by_date = partition_by_date
        self.region = region
        
        # Handle secure URL
        if self.endpoint_url.startswith("https://"):
            secure = True
        
        # Initialize S3 client
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name=self.region,
        )
        
        # Track if bucket was verified
        self._bucket_verified = False
    
    @property
    def extension(self) -> str:
        extensions = {'jsonl': '.jsonl', 'csv': '.csv', 'parquet': '.parquet'}
        return extensions[self._output_format]
    
    @property
    def format_name(self) -> str:
        names = {'jsonl': 'MinIO (JSONL)', 'csv': 'MinIO (CSV)', 'parquet': 'MinIO (Parquet)'}
        return names[self._output_format]
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        if self._bucket_verified:
            return
        
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ('404', 'NoSuchBucket'):
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    print(f"   📦 Created bucket: {self.bucket}")
                except ClientError as create_error:
                    # Bucket might have been created by another process
                    if 'BucketAlreadyOwnedByYou' not in str(create_error):
                        raise
            else:
                raise
        
        self._bucket_verified = True
    
    def _get_object_key(self, filename: str) -> str:
        """
        Build full object key with optional date partitioning.
        
        Args:
            filename: Base filename (e.g., "transactions_00001.jsonl")
            
        Returns:
            Full object key (e.g., "raw/transactions/2025/12/05/transactions_00001.jsonl")
        """
        parts = [self.prefix] if self.prefix else []
        
        if self.partition_by_date:
            date_path = datetime.now().strftime("%Y/%m/%d")
            parts.append(date_path)
        
        parts.append(filename)
        
        return '/'.join(parts)
    
    def ensure_directory(self, output_path: str) -> None:
        """For MinIO, just ensure bucket exists."""
        self._ensure_bucket()
    
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '_'
    ) -> Dict[str, Any]:
        """Flatten nested dictionary for CSV/Parquet formats."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _export_jsonl(self, data: List[Dict[str, Any]], object_key: str, append: bool = False) -> int:
        """Export data as JSONL format."""
        if append:
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=object_key)
                existing_content = response['Body'].read().decode('utf-8')
                existing_lines = existing_content.strip().split('\n') if existing_content.strip() else []
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    existing_lines = []
                else:
                    raise
            
            new_lines = [json.dumps(record, ensure_ascii=False, separators=(',', ':')) for record in data]
            all_lines = existing_lines + new_lines
            body = '\n'.join(all_lines) + '\n'
        else:
            lines = [json.dumps(record, ensure_ascii=False, separators=(',', ':'), default=str) for record in data]
            body = '\n'.join(lines) + '\n'
        
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=body.encode('utf-8'),
            ContentType='application/x-ndjson',
        )
        return len(data)
    
    def _export_csv(self, data: List[Dict[str, Any]], object_key: str, append: bool = False) -> int:
        """Export data as CSV format."""
        if not data:
            return 0
        
        # Flatten nested dicts
        flat_data = [self._flatten_dict(record) for record in data]
        
        # Get all columns
        all_columns = set()
        for record in flat_data:
            all_columns.update(record.keys())
        columns = sorted(all_columns)
        
        # Write to buffer
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction='ignore')
        
        if not append:
            writer.writeheader()
        
        for record in flat_data:
            writer.writerow(record)
        
        # Convert to bytes and use streaming upload (avoids memory copy)
        csv_bytes = io.BytesIO(buffer.getvalue().encode('utf-8'))
        csv_bytes.seek(0)
        
        self.client.upload_fileobj(
            csv_bytes,
            self.bucket,
            object_key,
            ExtraArgs={'ContentType': 'text/csv'},
        )
        return len(data)
    
    def _export_parquet(self, data: List[Dict[str, Any]], object_key: str, append: bool = False) -> int:
        """Export data as Parquet format."""
        if not data:
            return 0
        
        # Flatten nested dicts
        flat_data = [self._flatten_dict(record) for record in data]
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(flat_data)
        
        # IMPORTANTE: Manter timestamp como STRING para compatibilidade com Spark
        # NÃO converter para datetime porque isso causa inconsistência de schema entre partições
        # Spark pode ter problemas quando alguns arquivos têm timestamp como string e outros como INT64
        # A conversão para timestamp será feita na camada Bronze do pipeline
        
        # Garantir que colunas timestamp sejam SEMPRE strings (formato ISO8601)
        for col in df.columns:
            if 'timestamp' in col.lower() or 'date' in col.lower() or col.endswith('_at'):
                # Converter para string se for datetime, manter como string se já for
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
                else:
                    # Já é string, garantir formato consistente
                    df[col] = df[col].astype(str)
        
        # Convert to PyArrow Table - todas as colunas timestamp são strings
        table = pa.Table.from_pandas(df, preserve_index=False)
        
        # Write to buffer with Spark-compatible settings
        buffer = io.BytesIO()
        pq.write_table(
            table,
            buffer,
            compression=getattr(self, 'compression', 'snappy') or 'snappy',
            use_dictionary=False,  # Evita PlainLongDictionary issues
            write_statistics=False,
            version='2.4',  # Formato compatível com Spark 3.x
        )
        buffer.seek(0)
        
        # Use streaming upload (avoids memory copy from buffer.getvalue())
        self.client.upload_fileobj(
            buffer,
            self.bucket,
            object_key,
            ExtraArgs={'ContentType': 'application/octet-stream'},
        )
        return len(data)
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """
        Export a batch of records to MinIO.
        
        Args:
            data: List of records to export
            output_path: Object key or full path
            append: If True, download existing and append (expensive, JSONL only)
            
        Returns:
            Number of records exported
        """
        self._ensure_bucket()
        
        # Extract filename from path if full path provided
        if '/' in output_path:
            filename = os.path.basename(output_path)
        else:
            filename = output_path
        
        # Ensure correct extension
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        filename = f"{base_name}{self.extension}"
        
        object_key = self._get_object_key(filename)
        
        # Export based on format
        if self._output_format == 'jsonl':
            return self._export_jsonl(data, object_key, append)
        elif self._output_format == 'csv':
            return self._export_csv(data, object_key, append)
        elif self._output_format == 'parquet':
            return self._export_parquet(data, object_key, append)
        else:
            raise ValueError(f"Unsupported format: {self._output_format}")
    
    def export_stream(
        self,
        data_iterator: Iterator[Dict[str, Any]],
        output_path: str,
        batch_size: int = 10000
    ) -> int:
        """
        Export data from iterator to MinIO in batches.
        
        For very large datasets, this uploads in chunks to avoid memory issues.
        Each chunk becomes a separate file.
        """
        self._ensure_bucket()
        
        filename_base = os.path.basename(output_path).rsplit('.', 1)[0]
        total_count = 0
        batch_num = 0
        batch = []
        
        for record in data_iterator:
            batch.append(record)
            
            if len(batch) >= batch_size:
                chunk_filename = f"{filename_base}_{batch_num:05d}.jsonl"
                self.export_batch(batch, chunk_filename)
                total_count += len(batch)
                batch = []
                batch_num += 1
        
        # Write remaining records
        if batch:
            if batch_num == 0:
                chunk_filename = f"{filename_base}.jsonl"
            else:
                chunk_filename = f"{filename_base}_{batch_num:05d}.jsonl"
            self.export_batch(batch, chunk_filename)
            total_count += len(batch)
        
        return total_count
    
    def export_single(self, record: Dict[str, Any], output_path: str, append: bool = True) -> None:
        """Export a single record to MinIO."""
        self.export_batch([record], output_path, append=append)
    
    def get_full_path(self, filename: str) -> str:
        """Get full S3/MinIO URL for a file."""
        object_key = self._get_object_key(filename)
        return f"s3://{self.bucket}/{object_key}"
    
    def list_objects(self, prefix: str = None) -> List[str]:
        """List objects in bucket with optional prefix."""
        self._ensure_bucket()
        
        search_prefix = prefix or self.prefix
        
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=search_prefix,
        )
        
        return [obj['Key'] for obj in response.get('Contents', [])]


class MinIOStreamWriter:
    """
    Memory-efficient writer that streams directly to MinIO.
    
    Use this when generating large files to avoid memory accumulation.
    """
    
    def __init__(
        self,
        exporter: MinIOExporter,
        filename: str,
        buffer_size: int = 1000,
    ):
        """
        Initialize streaming writer.
        
        Args:
            exporter: MinIO exporter instance
            filename: Target filename
            buffer_size: Records to buffer before upload
        """
        self.exporter = exporter
        self.filename = filename
        self.buffer_size = buffer_size
        self._buffer = []
        self._part_num = 0
        self._total_written = 0
    
    def write(self, record: Dict[str, Any]) -> None:
        """Add record to buffer, flush if needed."""
        self._buffer.append(record)
        
        if len(self._buffer) >= self.buffer_size:
            self._flush_buffer()
    
    def _flush_buffer(self) -> None:
        """Upload buffer to MinIO as a part file."""
        if not self._buffer:
            return
        
        part_filename = f"{self.filename.rsplit('.', 1)[0]}_part{self._part_num:05d}.jsonl"
        self.exporter.export_batch(self._buffer, part_filename)
        
        self._total_written += len(self._buffer)
        self._buffer = []
        self._part_num += 1
    
    def close(self) -> int:
        """Flush remaining buffer and return total records written."""
        self._flush_buffer()
        return self._total_written
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
