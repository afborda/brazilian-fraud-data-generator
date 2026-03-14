#!/usr/bin/env python3
"""
🇧🇷 Brazilian Fraud Data Generator v4.1.0
==========================================
Thin entrypoint — argument parsing + runner dispatch.

Execution modes (Open/Closed: add new modes without changing this file):
  --schema  →  SchemaRunner   declarative JSON schema output
  MinIO URL →  MinIORunner    writes directly to MinIO / S3
  (default) →  BatchRunner    writes to local disk or a database
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fraud_generator.cli.args import build_parser
from fraud_generator.cli.runners import BatchRunner, MinIORunner, SchemaRunner
from fraud_generator.exporters import is_minio_url, list_formats, MINIO_AVAILABLE, is_format_available
from fraud_generator.licensing.validator import validate_env, check_format_allowed, check_size_allowed
from fraud_generator.utils.helpers import parse_size


def main() -> None:
    # ── License validation (runs before anything else) ─────────────────────
    license = validate_env(phone_home=True)

    parser = build_parser(available_formats=list_formats())
    args = parser.parse_args()

    # ── License limit checks ───────────────────────────────────────────────
    try:
        if not args.schema:
            check_format_allowed(license, args.format)
        if hasattr(args, 'size') and args.size:
            check_size_allowed(license, parse_size(args.size))
    except Exception as e:
        print(f"\n  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    # ── Schema mode ────────────────────────────────────────────────────────
    if args.schema:
        SchemaRunner().run(args)
        return

    # ── MinIO mode ─────────────────────────────────────────────────────────
    if is_minio_url(args.output):
        if not MINIO_AVAILABLE:
            print("❌ MinIO requires boto3.  Install: pip install boto3")
            sys.exit(1)
        MinIORunner().run(args)
        return

    # ── Batch (local / DB) mode ────────────────────────────────────────────
    if not is_format_available(args.format):
        print(f"❌ Format '{args.format}' not available.")
        print("   Install: pip install pyarrow pandas")
        sys.exit(1)

    BatchRunner().run(args)


if __name__ == "__main__":
    main()
