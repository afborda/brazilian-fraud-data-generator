"""
BatchRunner — local disk and database generation pipeline.

Orchestrates 4 phases:
  1. Generate customers + devices (index_builder)
  2. Generate transaction files  (workers/tx_worker via ProcessPoolExecutor)
  3. Generate drivers            (index_builder)
  4. Generate ride files         (workers/ride_worker via ProcessPoolExecutor)

Open/Closed: add new output sub-types by extending this class or
composing a new runner — without touching MinIORunner or SchemaRunner.
"""
import argparse
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Optional

from fraud_generator.cli.runners.base import BaseRunner
from fraud_generator.cli.constants import (
    TARGET_FILE_SIZE_MB,
    TRANSACTIONS_PER_FILE,
    RIDES_PER_FILE,
    RIDES_PER_DRIVER,
)
from fraud_generator.cli.index_builder import generate_customers_and_devices, generate_drivers
from fraud_generator.cli.workers.tx_worker import worker_generate_batch
from fraud_generator.cli.workers.ride_worker import worker_generate_rides_batch
from fraud_generator.cli.workers.batch_gen import generate_transaction_batch, generate_ride_batch
from fraud_generator.exporters import get_exporter
from fraud_generator.utils import (
    parse_size, format_size, format_duration,
    ProgressTracker,
    is_redis_available, get_redis_client,
    load_cached_indexes, save_cached_indexes,
)
from fraud_generator.validators import validate_cpf


class BatchRunner(BaseRunner):
    """Run the full batch pipeline writing to local disk or a database."""

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

        is_db = args.format in ("db", "database")
        db_tables = self._db_tables(args) if is_db else None

        # --- build exporter ------------------------------------------------
        if is_db:
            exporter = get_exporter(args.format, db_url=args.db_url, table_name=args.db_table)
            output_dir = None
        else:
            os.makedirs(args.output, exist_ok=True)
            output_dir = args.output
            exporter_kwargs = {"skip_none": True} if args.format in ("jsonl", "json") else {}
            if args.format == "jsonl" and args.jsonl_compress != "none":
                exporter_kwargs["jsonl_compress"] = args.jsonl_compress
            exporter = get_exporter(args.format, **exporter_kwargs)

        # --- header --------------------------------------------------------
        self._print_header(args, target_bytes, num_customers, total_tx,
                           total_rides, num_drivers, num_files, workers,
                           start_date, end_date, use_profiles)

        start_time = time.time()

        # -------------------------------------------------------------------
        # Phase 1: customers + devices
        # -------------------------------------------------------------------
        output_display = args.output
        redis_client = self._connect_redis(args)

        print("\n" + "=" * 60)
        print("📋 FASE 1: Gerando clientes e dispositivos")
        print("=" * 60)

        ph1 = ProgressTracker(num_customers, "Gerando clientes e dispositivos",
                               "clientes", output_display)
        ph1.start()
        ph1_t0 = time.time()

        customer_indexes, device_indexes, customer_data, device_data = \
            self._load_or_build_customers(redis_client, args, num_customers, use_profiles)

        ph1.current = num_customers
        ph1._print_progress()
        ph1.finish(show_summary=False)

        print(f"   ✅ {len(customer_data):,} clientes, {len(device_data):,} dispositivos")
        print(f"   ⏱️  {format_duration(time.time() - ph1_t0)}")

        print("\n🔍 Validando CPFs...")
        valid = sum(1 for c in customer_data if validate_cpf(c["cpf"]))
        print(f"   ✅ {valid:,}/{len(customer_data):,} CPFs válidos "
              f"({100 * valid / len(customer_data):.1f}%)")

        print("\n💾 Salvando clientes e dispositivos...")
        self._save(exporter, customer_data, "customers", args, output_dir, is_db, db_tables)
        self._save(exporter, device_data, "devices", args, output_dir, is_db, db_tables)

        tx_results: List[str] = []
        ride_results: List[str] = []

        # -------------------------------------------------------------------
        # Phase 2: transactions
        # -------------------------------------------------------------------
        if generate_tx:
            print("\n" + "=" * 60)
            print("📋 FASE 2: Gerando transações")
            print("=" * 60)

            ph2 = ProgressTracker(num_files, "Gerando arquivos de transações",
                                   "arquivos", output_display)
            ph2.start()
            ph2_t0 = time.time()

            if is_db:
                for bid in range(num_files):
                    txs = generate_transaction_batch(
                        batch_id=bid, num_transactions=TRANSACTIONS_PER_FILE,
                        customer_indexes=customer_indexes, device_indexes=device_indexes,
                        start_date=start_date, end_date=end_date,
                        fraud_rate=args.fraud_rate, use_profiles=use_profiles, seed=args.seed,
                    )
                    exporter.export_batch(txs, args.db_url, append=bid > 0)
                    tx_results.append(f"db_batch_{bid:05d}")
                    ph2.update(1)
            else:
                tx_results = self._run_local_workers(
                    worker_fn=worker_generate_batch,
                    build_args=lambda bid: (
                        bid, TRANSACTIONS_PER_FILE,
                        customer_indexes, device_indexes,
                        start_date, end_date,
                        args.fraud_rate, use_profiles,
                        args.output, args.format, args.seed, args.jsonl_compress,
                    ),
                    num_files=num_files, workers=workers,
                    parallel_mode=args.parallel_mode, progress=ph2,
                )

            ph2.finish()
            print(f"   💳 ~{total_tx:,} transações  ⏱️  {format_duration(time.time() - ph2_t0)}")

        driver_indexes: List[tuple] = []

        # -------------------------------------------------------------------
        # Phase 3: drivers
        # -------------------------------------------------------------------
        if generate_rides:
            print("\n" + "=" * 60)
            print("📋 FASE 3: Gerando motoristas")
            print("=" * 60)

            ph3 = ProgressTracker(num_drivers, "Gerando motoristas",
                                   "motoristas", output_display)
            ph3.start()
            ph3_t0 = time.time()

            driver_indexes, driver_data = self._load_or_build_drivers(
                redis_client, args, num_drivers, customer_indexes, device_indexes
            )

            ph3.current = num_drivers
            ph3._print_progress()
            ph3.finish(show_summary=False)
            print(f"   ✅ {len(driver_data):,} motoristas  ⏱️  {format_duration(time.time() - ph3_t0)}")

            print("\n💾 Salvando motoristas...")
            self._save(exporter, driver_data, "drivers", args, output_dir, is_db, db_tables)

            print("\n🔍 Validando CPFs dos motoristas...")
            valid_d = sum(1 for d in driver_data if validate_cpf(d["cpf"]))
            print(f"   ✅ {valid_d:,}/{len(driver_data):,} CPFs válidos")

        # -------------------------------------------------------------------
        # Phase 4: rides
        # -------------------------------------------------------------------
        if generate_rides:
            print("\n" + "=" * 60)
            print("📋 FASE 4: Gerando corridas")
            print("=" * 60)

            ph4 = ProgressTracker(num_files, "Gerando arquivos de corridas",
                                   "arquivos", output_display)
            ph4.start()
            ph4_t0 = time.time()

            if is_db:
                rides_exp = get_exporter(args.format, db_url=args.db_url,
                                         table_name=db_tables["rides"])
                for bid in range(num_files):
                    rides = generate_ride_batch(
                        batch_id=bid, num_rides=RIDES_PER_FILE,
                        customer_indexes=customer_indexes, driver_indexes=driver_indexes,
                        start_date=start_date, end_date=end_date,
                        fraud_rate=args.fraud_rate, use_profiles=use_profiles, seed=args.seed,
                    )
                    rides_exp.export_batch(rides, args.db_url, append=bid > 0)
                    ride_results.append(f"db_batch_{bid:05d}")
                    ph4.update(1)
            else:
                ride_results = self._run_local_workers(
                    worker_fn=worker_generate_rides_batch,
                    build_args=lambda bid: (
                        bid, RIDES_PER_FILE,
                        customer_indexes, driver_indexes,
                        start_date, end_date,
                        args.fraud_rate, use_profiles,
                        args.output, args.format, args.seed, args.jsonl_compress,
                    ),
                    num_files=num_files, workers=workers,
                    parallel_mode=args.parallel_mode, progress=ph4,
                )

            ph4.finish()
            print(f"   🚗 ~{total_rides:,} corridas  ⏱️  {format_duration(time.time() - ph4_t0)}")

        # -------------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------------
        self._print_summary(
            args, start_time, total_tx, total_rides,
            len(tx_results) + len(ride_results) + 2 + (1 if generate_rides else 0),
        )

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
    def _db_tables(args) -> dict:
        return {
            "customers": "customers",
            "devices": "devices",
            "drivers": "drivers",
            "transactions": args.db_table,
            "rides": f"{args.db_table}_rides",
        }

    @staticmethod
    def _connect_redis(args):
        if not args.redis_url:
            return None
        if not is_redis_available():
            print("⚠️  Redis não disponível. Instale com: pip install redis")
            return None
        try:
            client = get_redis_client(args.redis_url)
            print(f"🧠 Redis cache: {args.redis_url} (prefix={args.redis_prefix})")
            return client
        except Exception as exc:
            print(f"⚠️  Falha ao conectar ao Redis: {exc}")
            return None

    @staticmethod
    def _load_or_build_customers(redis_client, args, num_customers, use_profiles):
        if redis_client:
            cached = load_cached_indexes(redis_client, prefix=args.redis_prefix,
                                         include_drivers=False)
            ci, di, cd, dd, _, _ = cached
            if ci and di:
                print(f"✅ Cache Redis: {len(ci)} customers, {len(di)} devices")
                return ci, di, cd or [], dd or []

        ci, di, cd, dd = generate_customers_and_devices(num_customers, use_profiles, args.seed)

        if redis_client:
            save_cached_indexes(redis_client, prefix=args.redis_prefix,
                                customer_indexes=ci, device_indexes=di,
                                customer_data=cd, device_data=dd,
                                ttl_seconds=args.redis_ttl)
        return ci, di, cd, dd

    @staticmethod
    def _load_or_build_drivers(redis_client, args, num_drivers,
                                customer_indexes, device_indexes):
        if redis_client:
            cached = load_cached_indexes(redis_client, prefix=args.redis_prefix,
                                         include_drivers=True)
            _, _, _, _, drv_idx, drv_data = cached
            if drv_idx:
                print(f"✅ Cache Redis: {len(drv_idx)} drivers")
                if drv_data:
                    return drv_idx, drv_data

        drv_idx, drv_data = generate_drivers(num_drivers, args.seed)

        if redis_client:
            save_cached_indexes(redis_client, prefix=args.redis_prefix,
                                customer_indexes=customer_indexes,
                                device_indexes=device_indexes,
                                driver_indexes=drv_idx, driver_data=drv_data,
                                ttl_seconds=args.redis_ttl)
        return drv_idx, drv_data

    @staticmethod
    def _save(exporter, data, name, args, output_dir, is_db, db_tables):
        if is_db:
            tbl_exp = get_exporter(args.format, db_url=args.db_url,
                                   table_name=db_tables[name])
            tbl_exp.export_batch(data, args.db_url, append=False)
            print(f"   🗄️  Inserido: {db_tables[name]}")
        else:
            path = os.path.join(output_dir, f"{name}{exporter.extension}")
            exporter.export_batch(data, path)
            print(f"   💾 Salvo: {path}")

    @staticmethod
    def _run_local_workers(worker_fn, build_args, num_files, workers,
                            parallel_mode, progress) -> List[str]:
        """Dispatch worker_fn via ThreadPool or ProcessPool depending on mode."""
        worker_args = [build_args(bid) for bid in range(num_files)]
        results: List[str] = []

        if parallel_mode == "thread":
            max_w = min(workers, num_files, 16)
            with ThreadPoolExecutor(max_workers=max_w) as ex:
                futures = {ex.submit(worker_fn, a): i for i, a in enumerate(worker_args)}
                for fut in as_completed(futures):
                    results.append(fut.result())
                    progress.update(1)
        else:
            max_w = min(workers, num_files, mp.cpu_count())
            print(f"   🚀 ProcessPoolExecutor — {max_w} processos (bypass GIL)")
            with ProcessPoolExecutor(max_workers=max_w) as ex:
                futures = {ex.submit(worker_fn, a): i for i, a in enumerate(worker_args)}
                for fut in as_completed(futures):
                    results.append(fut.result())
                    progress.update(1)

        return results

    @staticmethod
    def _print_header(args, target_bytes, num_customers, total_tx, total_rides,
                       num_drivers, num_files, workers, start_date, end_date, use_profiles):
        print("=" * 60)
        print("🇧🇷 BRAZILIAN FRAUD DATA GENERATOR v4.9.0")
        print("=" * 60)
        print(f"📦 Target size: {format_size(target_bytes)}")
        if args.format in ("db", "database"):
            print(f"🗄️  Output: {args.db_url} (DB) — table: {args.db_table}")
        else:
            print(f"📁 Output: {args.output}")
        print(f"📄 Format: {args.format.upper()}")
        if args.format == "parquet":
            print(f"🗜️  Compression: {args.compression.upper()}")
        elif args.format == "jsonl" and args.jsonl_compress != "none":
            print(f"🗜️  Compression: {args.jsonl_compress.upper()}")
        print(f"🎯 Type: {args.type.upper()}")
        print(f"👥 Customers: {num_customers:,}")
        if total_tx:
            print(f"💳 Transactions: ~{total_tx:,}")
        if total_rides:
            print(f"🚗 Drivers: {num_drivers:,}  Rides: ~{total_rides:,}")
        print(f"📊 Files: {num_files}  🎭 Fraud: {args.fraud_rate * 100:.1f}%")
        print(f"🧠 Profiles: {'✅' if use_profiles else '❌'}  ⚡ Workers: {workers}")
        print(f"📅 {start_date.date()} → {end_date.date()}")
        if args.seed:
            print(f"🎲 Seed: {args.seed}")
        print("=" * 60)

    @staticmethod
    def _print_summary(args, start_time, total_tx, total_rides, total_files):
        total_time = time.time() - start_time
        total_size = sum(
            os.path.getsize(os.path.join(args.output, f))
            for f in os.listdir(args.output)
            if os.path.isfile(os.path.join(args.output, f))
        ) if os.path.isdir(args.output) else 0

        print("\n" + "=" * 60)
        print("✅ GERAÇÃO CONCLUÍDA!")
        print("=" * 60)
        print(f"📦 Tamanho total: {format_size(total_size)}")
        print(f"📁 Arquivos: {total_files}")
        if total_tx:
            print(f"💳 Transações: ~{total_tx:,}")
        if total_rides:
            print(f"🚗 Corridas: ~{total_rides:,}")
        print(f"⏱️  {format_duration(total_time)}")
        total_records = total_tx + total_rides
        if total_records and total_time:
            print(f"⚡ {total_records / total_time:,.0f} rec/s")
        print(f"📍 {args.output}")
        print("=" * 60)
