"""
MinIO Parquet upload workers — ProcessPoolExecutor compatible.

Each function generates data in memory, serialises to a temporary Parquet
file and uploads to MinIO/S3 — entirely inside the child process (no
shared state with the parent).

IMPORTANT: Top-level functions only (pickling requirement).
"""
import gc
import os
import tempfile

import sys as _sys
_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _src not in _sys.path:
    _sys.path.insert(0, _src)

from fraud_generator.cli.workers.batch_gen import generate_transaction_batch, generate_ride_batch


def worker_upload_parquet_transactions(args: tuple) -> str:
    """
    Generate transactions → Parquet → upload to MinIO (child process).

    Args:
        args: (batch_id, num_transactions, customer_indexes, device_indexes,
               start_date, end_date, fraud_rate, use_profiles, seed,
               minio_endpoint, minio_access_key, minio_secret_key,
               bucket_name, object_prefix, compression)

    Returns:
        Object key (filename) of the uploaded file.
    """
    import pandas as pd

    (
        batch_id, num_transactions, customer_indexes, device_indexes,
        start_date, end_date, fraud_rate, use_profiles, seed,
        minio_endpoint, minio_access_key, minio_secret_key,
        bucket_name, object_prefix, compression,
    ) = args

    # Investigation-only fields are collected here and uploaded as a companion
    # object rather than travelling in the transaction record — see
    # utils/ground_truth.py. Same batch number, so the two join on
    # transaction_id.
    ground_truth: list = []
    transactions = generate_transaction_batch(
        batch_id=batch_id,
        num_transactions=num_transactions,
        customer_indexes=customer_indexes,
        device_indexes=device_indexes,
        start_date=start_date,
        end_date=end_date,
        fraud_rate=fraud_rate,
        use_profiles=use_profiles,
        seed=seed,
        ground_truth_sink=ground_truth,
    )

    flat_data = [_flatten(tx) for tx in transactions]
    df = pd.DataFrame(flat_data)

    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    local_path = tmpf.name
    tmpf.close()

    try:
        df.to_parquet(local_path, engine="pyarrow", compression=compression, index=False)
        object_key = _object_key(object_prefix, f"transactions_{batch_id:05d}.parquet")
        _upload(local_path, bucket_name, object_key, minio_endpoint,
                minio_access_key, minio_secret_key)

        if ground_truth:
            _upload_ground_truth(
                ground_truth, batch_id, compression, object_prefix, bucket_name,
                minio_endpoint, minio_access_key, minio_secret_key,
            )
        return f"transactions_{batch_id:05d}.parquet"
    finally:
        os.remove(local_path)
        del df, transactions, flat_data
        gc.collect()


def _upload_ground_truth(records, batch_id, compression, object_prefix, bucket_name,
                         minio_endpoint, minio_access_key, minio_secret_key) -> None:
    """Upload the companion ground-truth object for a transactions batch."""
    import pandas as pd  # imported lazily, like the callers do

    gt_df = pd.DataFrame(records)
    gt_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    gt_path = gt_tmp.name
    gt_tmp.close()
    try:
        gt_df.to_parquet(gt_path, engine="pyarrow", compression=compression, index=False)
        _upload(
            gt_path, bucket_name,
            _object_key(object_prefix, f"fraud_ground_truth_{batch_id:05d}.parquet"),
            minio_endpoint, minio_access_key, minio_secret_key,
        )
    finally:
        os.remove(gt_path)
        del gt_df


def worker_upload_parquet_rides(args: tuple) -> str:
    """
    Generate rides → Parquet → upload to MinIO (child process).

    Args — same shape as worker_upload_parquet_transactions but for rides.

    Returns:
        Object key of the uploaded file.
    """
    import pandas as pd

    (
        batch_id, num_rides, customer_indexes, driver_indexes,
        start_date, end_date, fraud_rate, use_profiles, seed,
        minio_endpoint, minio_access_key, minio_secret_key,
        bucket_name, object_prefix, compression,
    ) = args

    rides = generate_ride_batch(
        batch_id=batch_id,
        num_rides=num_rides,
        customer_indexes=customer_indexes,
        driver_indexes=driver_indexes,
        start_date=start_date,
        end_date=end_date,
        fraud_rate=fraud_rate,
        use_profiles=use_profiles,
        seed=seed,
    )

    flat_data = [_flatten(r) for r in rides]
    df = pd.DataFrame(flat_data)

    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    local_path = tmpf.name
    tmpf.close()

    try:
        df.to_parquet(local_path, engine="pyarrow", compression=compression, index=False)
        object_key = _object_key(object_prefix, f"rides_{batch_id:05d}.parquet")
        _upload(local_path, bucket_name, object_key, minio_endpoint,
                minio_access_key, minio_secret_key)
        return f"rides_{batch_id:05d}.parquet"
    finally:
        os.remove(local_path)
        del df, rides, flat_data
        gc.collect()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flatten(d: dict, parent_key: str = "", sep: str = "_") -> dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _object_key(prefix: str, filename: str) -> str:
    return f"{prefix}/{filename}" if prefix else filename


def _upload(
    local_path: str,
    bucket: str,
    key: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
) -> None:
    import boto3
    from botocore.config import Config

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    with open(local_path, "rb") as fh:
        s3.put_object(Bucket=bucket, Key=key, Body=fh.read(),
                      ContentType="application/octet-stream")
