"""
MinIO Exporter for Brazilian Fraud Data Generator.

Uploads data directly to MinIO/S3-compatible storage.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Iterator, Optional
from urllib.parse import urlparse

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .base import ExporterProtocol


def is_minio_available() -> bool:
    """Check if MinIO/S3 dependencies are available."""
    return BOTO3_AVAILABLE


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
    - JSONL format for Spark compatibility
    """
    
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
        """
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for MinIO export. "
                "Install it with: pip install boto3"
            )
        
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
        return '.jsonl'
    
    @property
    def format_name(self) -> str:
        return 'MinIO (JSONL)'
    
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
    
    def export_batch(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        append: bool = False
    ) -> int:
        """
        Export a batch of records to MinIO as JSONL.
        
        Args:
            data: List of records to export
            output_path: Object key or full path
            append: If True, download existing and append (expensive!)
            
        Returns:
            Number of records exported
        """
        self._ensure_bucket()
        
        # Extract filename from path if full path provided
        if '/' in output_path:
            filename = os.path.basename(output_path)
        else:
            filename = output_path
        
        # Ensure .jsonl extension
        if not filename.endswith('.jsonl'):
            filename = filename.rsplit('.', 1)[0] + '.jsonl'
        
        object_key = self._get_object_key(filename)
        
        # Handle append (download, merge, upload)
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
            
            # Merge
            new_lines = [json.dumps(record, ensure_ascii=False, separators=(',', ':')) for record in data]
            all_lines = existing_lines + new_lines
            body = '\n'.join(all_lines) + '\n'
        else:
            # Normal export
            lines = [json.dumps(record, ensure_ascii=False, separators=(',', ':'), default=str) for record in data]
            body = '\n'.join(lines) + '\n'
        
        # Upload to MinIO
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=body.encode('utf-8'),
            ContentType='application/x-ndjson',
        )
        
        return len(data)
    
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
