"""
MinIORunner — generation pipeline writing directly to MinIO / S3.

Mirrors BatchRunner's 4-phase structure but dispatches to MinIO-aware
workers for upload.  Parquet format uses ProcessPoolExecutor (true
parallelism); JSONL/CSV use ThreadPoolExecutor (I/O bound).
"""
import argparse
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List

from fraud_generator.cli.runners.base import BaseRunner
from fraud_generator.cli.constants import (
    TARGET_FILE_SIZE_MB,
    TRANSACTIONS_PER_FILE,
    RIDES_PER_FILE,
    RIDES_PER_DRIVER,
)
from fraud_generator.cli.index_builder import generate_customers_and_devices, generate_drivers
from fraud_generator.cli.workers.batch_gen import generate_transaction_batch, generate_ride_batch
from fraud_generator.cli.workers.minio_parquet import (
    worker_upload_parquet_transactions,
    worker_upload_parquet_rides,
)
from fraud_generator.exporters import get_minio_exporter
from fraud_generator.utils import (
    parse_size, format_size, format_duration,
    ProgressTracker,
    is_redis_available, get_redis_client,
    load_cached_indexes, save_cached_indexes,
)
from fraud_generator.validators import validate_cpf


class MinIORunner(BaseRunner):
    """Run the batch pipeline with MinIO as the output target."""

    def run(self, args: argparse.Namespace) -> None:
        target_bytes = parse_size(args.size)
        generate_tx = args.type in ("transactions", "all")
        generate_rides = args.type in ("rides", "all")

        num_files = max(1, target_bytes // (TARGET_FILE_SIZE_MB * 1024 * 1024))
        total_tx = num_files * TRANSACTIONS_PER_FILE if generate_tx else 0
        total_rides = num_files * RIDES_PER_FILE if generate_rides else 0
        num_drivers = max(100, total_rides // RIDES_PER_DRIVER) if generate_rides else 0
        num_customers = self._calc_customers(args, generate_tx, generate_rides,
                                              total_tx, total_rides)
        start_date, end_date = self._parse_dates(args)
        workers = args.workers or mp.cpu_count()
        use_profiles = not args.no_profiles
        compression = args.compression if args.compression != "none" else None

        exporter = get_minio_exporter(
            minio_url=args.output,
            endpoint_url=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            partition_by_date=not args.no_date_partition,
            output_format=args.format,
            compression=compression,
            jsonl_compress=args.jsonl_compress,
        )

        print("=" * 60)
        print("🇧🇷 BRAZILIAN FRAUD DATA GENERATOR v4.1.0 — MinIO")
        print("=" * 60)
        print(f"☁️  Output: {args.output}")
        if args.minio_endpoint:
            print(f"   Endpoint: {args.minio_endpoint}")
        print(f"📦 {format_size(target_bytes)}  📄 {args.format.upper()}  "
              f"🎯 {args.type.upper()}")
        print(f"👥 Customers: {num_customers:,}  ⚡ Workers: {workers}")
        if args.seed:
            print(f"🎲 Seed: {args.seed}")
        print("=" * 60)

        start_time = time.time()
        output_display = f"{args.output} (MinIO)"

        redis_client = self._connect_redis(args)

        # Phase 1 -----------------------------------------------------------
        print("\n📋 FASE 1: Gerando clientes e dispositivos")
        ph1 = ProgressTracker(num_customers, "Gerando clientes e dispositivos",
                               "clientes", output_display)
        ph1.start()
        ph1_t0 = time.time()

        customer_indexes, device_indexes, customer_data, device_data = \
            self._load_or_build_customers(redis_client, args, num_customers, use_profiles)

        ph1.current = num_customers
        ph1._print_progress()
        ph1.finish(show_summary=False)
        print(f"   ✅ {len(customer_data):,} clientes OK  ⏱️  {format_duration(time.time() - ph1_t0)}")

        exporter.export_batch(customer_data, "customers")
        exporter.export_batch(device_data, "devices")
        print(f"   📤 customers{exporter.extension} + devices{exporter.extension} → MinIO")

        tx_results: List[str] = []

        # Phase 2 -----------------------------------------------------------
        if generate_tx:
            print("\n📋 FASE 2: Gerando transações → MinIO")
            ph2 = ProgressTracker(num_files, "Gerando transações", "arquivos", output_display)
            ph2.start()
            ph2_t0 = time.time()

            if args.format == "parquet":
                tx_results = self._run_parquet_workers(
                    worker_fn=worker_upload_parquet_transactions,
                    build_args=lambda bid: (
                        bid, TRANSACTIONS_PER_FILE,
                        customer_indexes, device_indexes,
                        start_date, end_date,
                        args.fraud_rate, use_profiles, args.seed,
                        exporter.endpoint_url, exporter.access_key, exporter.secret_key,
                        exporter.bucket, exporter.prefix, compression,
                    ),
                    num_files=num_files, workers=workers, progress=ph2,
                )
            else:
                tx_results = self._run_thread_workers(
                    num_files=num_files, workers=workers, progress=ph2,
                    generate_fn=generate_transaction_batch,
                    upload_name="transactions",
                    common_kwargs=dict(
                        customer_indexes=customer_indexes,
                        device_indexes=device_indexes,
                        start_date=start_date, end_date=end_date,
                        fraud_rate=args.fraud_rate, use_profiles=use_profiles,
                        seed=args.seed,
                    ),
                    batch_size=TRANSACTIONS_PER_FILE,
                    exporter=exporter,
                )

            ph2.finish()
            print(f"   💳 ~{total_tx:,}  ⏱️  {format_duration(time.time() - ph2_t0)}")

        driver_indexes: List[tuple] = []

        # Phase 3 -----------------------------------------------------------
        if generate_rides:
            print("\n📋 FASE 3: Gerando motoristas")
            driver_indexes, driver_data = generate_drivers(num_drivers, args.seed)
            exporter.export_batch(driver_data, "drivers")
            print(f"   ✅ {len(driver_data):,} motoristas → MinIO")

        ride_results: List[str] = []

        # Phase 4 -----------------------------------------------------------
        if generate_rides:
            print("\n📋 FASE 4: Gerando corridas → MinIO")
            ph4 = ProgressTracker(num_files, "Gerando corridas", "arquivos", output_display)
            ph4.start()
            ph4_t0 = time.time()

            if args.format == "parquet":
                ride_results = self._run_parquet_workers(
                    worker_fn=worker_upload_parquet_rides,
                    build_args=lambda bid: (
                        bid, RIDES_PER_FILE,
                        customer_indexes, driver_indexes,
                        start_date, end_date,
                        args.fraud_rate, use_profiles, args.seed,
                        exporter.endpoint_url, exporter.access_key, exporter.secret_key,
                        exporter.bucket, exporter.prefix, compression,
                    ),
                    num_files=num_files, workers=workers, progress=ph4,
                )
            else:
                ride_results = self._run_thread_workers(
                    num_files=num_files, workers=workers, progress=ph4,
                    generate_fn=generate_ride_batch,
                    upload_name="rides",
                    common_kwargs=dict(
                        customer_indexes=customer_indexes,
                        driver_indexes=driver_indexes,
                        start_date=start_date, end_date=end_date,
                        fraud_rate=args.fraud_rate, use_profiles=use_profiles,
                        seed=args.seed,
                    ),
                    batch_size=RIDES_PER_FILE,
                    exporter=exporter,
                )

            ph4.finish()
            print(f"   🚗 ~{total_rides:,}  ⏱️  {format_duration(time.time() - ph4_t0)}")

        # Summary -----------------------------------------------------------
        total_time = time.time() - start_time
        total_size = (total_tx * 500) + (total_rides * 800) + \
                     (len(customer_data) * 400) + (len(device_data) * 300)
        total_files = len(tx_results) + len(ride_results) + 2 + (1 if generate_rides else 0)

        print("\n" + "=" * 60)
        print("✅ GERAÇÃO CONCLUÍDA!")
        print("=" * 60)
        print(f"☁️  Destino: {args.output} (MinIO)")
        print(f"📦 ~{format_size(total_size)}  📁 {total_files} arquivos")
        if total_tx:
            print(f"💳 ~{total_tx:,} transações")
        if total_rides:
            print(f"🚗 ~{total_rides:,} corridas")
        total_records = total_tx + total_rides
        if total_records and total_time:
            print(f"⚡ {total_records / total_time:,.0f} rec/s  ⏱️  {format_duration(total_time)}")
        print("=" * 60)

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _calc_customers(args, gen_tx, gen_rides, total_tx, total_rides) -> int:
        if args.customers:
            return args.customers
        if gen_tx and gen_rides:
            return max(1_000, (total_tx + total_rides) // 100)
        if gen_tx:
            return max(1_000, total_tx // 100)
        return max(1_000, total_rides // 50)

    @staticmethod
    def _parse_dates(args):
        end_date = datetime.now()
        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=365)
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        return start_date, end_date

    @staticmethod
    def _connect_redis(args):
        if not args.redis_url:
            return None
        if not is_redis_available():
            return None
        try:
            return get_redis_client(args.redis_url)
        except Exception:
            return None

    @staticmethod
    def _load_or_build_customers(redis_client, args, num_customers, use_profiles):
        if redis_client:
            ci, di, cd, dd, _, _ = load_cached_indexes(
                redis_client, prefix=args.redis_prefix, include_drivers=False
            )
            if ci and di:
                return ci, di, cd or [], dd or []
        ci, di, cd, dd = generate_customers_and_devices(num_customers, use_profiles, args.seed)
        if redis_client:
            save_cached_indexes(redis_client, prefix=args.redis_prefix,
                                customer_indexes=ci, device_indexes=di,
                                customer_data=cd, device_data=dd,
                                ttl_seconds=args.redis_ttl)
        return ci, di, cd, dd

    @staticmethod
    def _run_parquet_workers(worker_fn, build_args, num_files, workers, progress) -> List[str]:
        max_w = min(workers, num_files, mp.cpu_count())
        print(f"   🚀 ProcessPoolExecutor — {max_w} processos")
        results: List[str] = []
        with ProcessPoolExecutor(max_workers=max_w) as ex:
            futures = {ex.submit(worker_fn, build_args(bid)): bid for bid in range(num_files)}
            for fut in as_completed(futures):
                results.append(fut.result())
                progress.update(1)
        return results

    @staticmethod
    def _run_thread_workers(num_files, workers, progress,
                             generate_fn, upload_name, common_kwargs,
                             batch_size, exporter) -> List[str]:
        max_w = min(workers, num_files, 16)
        results: List[str] = []

        def _upload(bid):
            records = generate_fn(
                batch_id=bid, **{("num_transactions" if upload_name == "transactions"
                                  else "num_rides"): batch_size},
                **common_kwargs,
            )
            fname = f"{upload_name}_{bid:05d}"
            exporter.export_batch(records, fname)
            return fname

        with ThreadPoolExecutor(max_workers=max_w) as ex:
            futures = {ex.submit(_upload, bid): bid for bid in range(num_files)}
            for fut in as_completed(futures):
                results.append(fut.result())
                progress.update(1)
        return results
