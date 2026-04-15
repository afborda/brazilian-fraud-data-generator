"""
CLI argument parser factory.

Single responsibility: build and return the ArgumentParser for generate.py.
No parsing logic, no business rules — just argument declaration.
"""
import argparse
from typing import List


def build_parser(available_formats: List[str]) -> argparse.ArgumentParser:
    """Return a fully configured ArgumentParser for the generator CLI."""
    parser = argparse.ArgumentParser(
        description="🇧🇷 synthfin-data v4.9.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --size 1GB --output ./data
  %(prog)s --size 1GB --type rides --output ./data
  %(prog)s --size 1GB --type all --output ./data
  %(prog)s --size 1GB --format csv --output ./data
  %(prog)s --size 1GB --format parquet --output ./data
  %(prog)s --size 1GB --no-profiles --output ./data
  %(prog)s --size 50GB --fraud-rate 0.01 --workers 8
  %(prog)s --size 1GB --seed 42 --output ./data

  # MinIO/S3 direct upload:
  %(prog)s --size 1GB --output minio://fraud-data/raw
  %(prog)s --size 1GB --output s3://fraud-data/raw --minio-endpoint http://minio:9000

  # Declarative JSON schema:
  %(prog)s --schema schemas/banking_full.json --count 5000 --output ./data

Available formats: """ + ", ".join(available_formats),
    )

    # ------------------------------------------------------------------ type
    parser.add_argument(
        "--type", "-t",
        default="transactions",
        choices=["transactions", "rides", "all"],
        help="Type of data to generate. Default: transactions",
    )

    # ------------------------------------------------------------------ size
    parser.add_argument(
        "--size", "-s",
        default="1GB",
        help="Target output size (e.g. 1GB, 500MB, 10GB). Default: 1GB",
    )

    # ---------------------------------------------------------------- output
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory or MinIO URL (minio://bucket/prefix). Default: ./output",
    )

    # ---------------------------------------------------------------- format
    parser.add_argument(
        "--format", "-f",
        default="jsonl",
        choices=available_formats,
        help="Export format. Default: jsonl",
    )

    # -------------------------------------------------------- jsonl-compress
    parser.add_argument(
        "--jsonl-compress",
        default="none",
        choices=["none", "gzip", "zstd", "snappy"],
        help="Inline compression for JSONL output. Default: none",
    )

    # ----------------------------------------------------------  fraud-rate
    parser.add_argument(
        "--fraud-rate", "-r",
        type=float,
        default=0.015,
        help="Fraud rate 0.0–1.0. Default: 0.015 (1.5%%)",
    )

    # ---------------------------------------------------------------- workers
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        help="Parallel worker count. Default: CPU count",
    )

    # ------------------------------------------------------------------ seed
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )

    # -------------------------------------------------------- parallel-mode
    parser.add_argument(
        "--parallel-mode",
        default="auto",
        choices=["auto", "thread", "process"],
        help="Parallel execution mode. Default: auto",
    )

    # ---------------------------------------------------------------- redis
    parser.add_argument("--redis-url", default=None,
                        help="Redis URL for index caching (e.g. redis://localhost:6379/0)")
    parser.add_argument("--redis-prefix", default="fraudgen",
                        help="Redis key prefix. Default: fraudgen")
    parser.add_argument("--redis-ttl", type=int, default=None,
                        help="Redis TTL in seconds for cached indexes")

    # ------------------------------------------------------------------- db
    parser.add_argument("--db-url", default=None,
                        help="Database URL for db format")
    parser.add_argument("--db-table", default="transactions",
                        help="Target table name. Default: transactions")

    # --------------------------------------------------------------- minio
    parser.add_argument("--minio-endpoint", default=None,
                        help="MinIO endpoint URL. Default: MINIO_ENDPOINT env")
    parser.add_argument("--minio-access-key", default=None,
                        help="MinIO access key. Default: MINIO_ROOT_USER env")
    parser.add_argument("--minio-secret-key", default=None,
                        help="MinIO secret key. Default: MINIO_ROOT_PASSWORD env")
    parser.add_argument("--no-date-partition", action="store_true",
                        help="Disable YYYY/MM/DD partitioning in MinIO")

    # --------------------------------------------------------- compression
    parser.add_argument(
        "--compression",
        default="zstd",
        choices=["snappy", "zstd", "gzip", "brotli", "none"],
        help="Parquet compression. Default: zstd",
    )

    # ------------------------------------------------------------- profiles
    parser.add_argument("--no-profiles", action="store_true",
                        help="Disable behavioural profiles (random generation)")

    # ------------------------------------------------------------- customers
    parser.add_argument(
        "--customers", "-c",
        type=int, default=None,
        help="Number of unique customers. Default: auto-calculated",
    )

    # --------------------------------------------------------------- dates
    parser.add_argument("--start-date", default=None,
                        help="Start date YYYY-MM-DD. Default: 1 year ago")
    parser.add_argument("--end-date", default=None,
                        help="End date YYYY-MM-DD. Default: today")

    # --------------------------------------------------------------- version
    parser.add_argument("--version", "-v", action="version", version="%(prog)s 4.1.0")

    # ------------------------------------------------------- schema mode
    parser.add_argument(
        "--schema",
        metavar="SCHEMA.json",
        default=None,
        help="Declarative JSON schema file. When set, bypasses --type/--format.",
    )
    parser.add_argument(
        "--count",
        type=int, default=None, metavar="N",
        help="Records to generate in schema mode. Default: 1000",
    )
    parser.add_argument(
        "--schema-no-ai",
        action="store_true", default=False,
        help="Disable AI schema correction (heuristics only).",
    )
    parser.add_argument(
        "--schema-ai-provider",
        default="openai",
        choices=["openai", "anthropic", "none"],
        help="LLM provider for schema correction. Default: openai",
    )

    return parser
