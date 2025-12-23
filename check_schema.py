"""
Script para verificar schema do Parquet no MinIO
"""
import pyarrow.parquet as pq
from botocore.client import Config
import boto3
import io
import os

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', ''),
    config=Config(signature_version='s3v4')
)

response = s3.get_object(Bucket='fraud-data', Key='raw/batch/transactions_00000.parquet')
data = response['Body'].read()

pf = pq.ParquetFile(io.BytesIO(data))
print('=== SCHEMA DO PARQUET ===')
for field in pf.schema_arrow:
    print(f'{field.name}: {field.type}')
