# Architecture — synthfin-data

> **Version:** 4.17 — 2026-04-01  
> **Portuguese version:** [docs/ARQUITETURA.md](docs/ARQUITETURA.md)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [High-Level Structure](#2-high-level-structure)
3. [Entry Points](#3-entry-points)
4. [Execution Modes](#4-execution-modes)
   - 4.1 [Batch Mode](#41-batch-mode)
   - 4.2 [MinIO / S3 Mode](#42-minio--s3-mode)
   - 4.3 [Schema Mode](#43-schema-mode)
   - 4.4 [Streaming Mode](#44-streaming-mode)
5. [CLI Package (`src/fraud_generator/cli/`)](#5-cli-package)
   - 5.1 [args.py](#51-argspy)
   - 5.2 [constants.py](#52-constantspy)
   - 5.3 [index_builder.py](#53-index_builderpy)
   - 5.4 [Runners](#54-runners)
   - 5.5 [Workers](#55-workers)
6. [Generators](#6-generators)
7. [Behavioral Profiles](#7-behavioral-profiles)
8. [Exporters](#8-exporters)
9. [Connections (Streaming)](#9-connections-streaming)
10. [Schema System](#10-schema-system)
11. [Configuration Layer](#11-configuration-layer)
12. [Enricher Pipeline](#12-enricher-pipeline)
13. [Data Models & Indexes](#13-data-models--indexes)
14. [Utilities](#14-utilities)
15. [Validators](#15-validators)
16. [Licensing System](#16-licensing-system)
17. [Design Decisions](#17-design-decisions)
18. [Data Flow Diagrams](#18-data-flow-diagrams)
19. [Performance Characteristics](#19-performance-characteristics)
20. [Extension Guide](#20-extension-guide)
21. [Known Gaps & Limitations](#21-known-gaps--limitations)
22. [Environment & Dependencies](#22-environment--dependencies)
23. [SynthFin Ecosystem](#23-synthfin-ecosystem)

---

## 1. Project Overview

The **synthfin-data** produces synthetic banking and ride-share event datasets for ML model training, fraud detection research, and system integration testing. It can generate datasets ranging from kilobytes to terabytes in multiple output formats.

**Core capabilities:**

| Capability | Details |
|---|---|
| Data types | Banking transactions, ride-share rides |
| Output formats | JSONL, JSON Array, CSV, TSV, Parquet, Arrow IPC, MinIO/S3 |
| Compression | None, gzip, zstd, snappy (auto-detected) |
| Scale | MB → TB via streaming + multiprocessing |
| Fraud simulation | 25 banking fraud patterns (RAG-calibrated), 11 ride-share fraud types, configurable rate |
| Reproducibility | Deterministic seed support |
| Schema customisation | Declarative JSON schema files with optional AI correction |
| Streaming | Stdout, Apache Kafka, HTTP Webhook |

---

## 2. High-Level Structure

```
synthfin-data/
│
├── generate.py               Batch entry point (49 lines — thin dispatcher)
├── stream.py                 Streaming entry point (~904 lines)
├── check_schema.py           Output validation utility
│
├── schemas/                  Example declarative JSON schemas
│   ├── banking_minimal.json
│   ├── banking_full.json
│   ├── rideshare_full.json
│   └── custom_empresa.json
│
├── docs/                     Documentation (all .md files)
│
└── src/fraud_generator/      Core library
    ├── cli/                  SOLID CLI orchestration layer
    │   ├── args.py
    │   ├── constants.py
    │   ├── index_builder.py
    │   ├── runners/          Command objects (batch, minio, schema)
    │   └── workers/          Picklable worker functions
    ├── generators/           Entity generators (customer, device, driver, transaction, ride)
    ├── profiles/             Behavioural profile definitions
    ├── enrichers/            8-stage transaction enrichment pipeline
    ├── exporters/            Output format strategy implementations
    ├── connections/          Streaming target strategy implementations
    ├── schema/               Declarative schema parsing, mapping, AI correction
    ├── config/               Static configuration data (banks, merchants, geography, fraud patterns)
    ├── models/               Data structures and index types
    ├── utils/                Shared utilities (compression, weights, progress, streaming, parallel)
    ├── validators/           CPF validation algorithm
    ├── licensing/            HMAC-signed license system (5 plan tiers)
    └── email/                Transactional email via Resend API
```

---

## 3. Entry Points

### `generate.py` (49 lines)

Pure dispatcher — no business logic. Resolves which runner to invoke based on CLI flags:

```
parse args
    │
    ├─ --schema flag?  ──► SchemaRunner().run(args)
    │
    ├─ MinIO URL?      ──► MinIORunner().run(args)
    │
    └─ default         ──► BatchRunner().run(args)
```

### `stream.py` (~904 lines)

Standalone streaming mode. Handles continuous event emission to stdout, Kafka, or webhooks. Manages its own argument parsing, connection lifecycle, and graceful shutdown via `_running` flag (SIGINT/SIGTERM).

---

## 4. Execution Modes

### 4.1 Batch Mode

Generates data to local disk (or SQLite/PostgreSQL database).

**Pipeline:**

```
CLI args
  └─► index_builder.generate_customers_and_devices()
        └─► ProcessPoolExecutor (N workers)
              ├─ tx_worker.worker_generate_batch()   → transactions_00000.jsonl …
              └─ ride_worker.worker_generate_rides_batch() → rides_00000.jsonl …
```

**Parallelism model:** One Python subprocess per batch file. Seed per worker = `base_seed + batch_id × K`, guaranteeing that the combined dataset is reproducible regardless of the number of workers used.

### 4.2 MinIO / S3 Mode

Activated when `--output` is a URL matching `s3://bucket/path/prefix`.

- **Parquet**: `ProcessPoolExecutor` — generate in child process → write temp file → upload via `boto3`
- **JSONL / CSV**: `ThreadPoolExecutor` — generate in main process → stream bytes → upload

Credentials are read from environment variables `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`.

### 4.3 Schema Mode

Activated by `--schema path/to/schema.json`. Uses the declarative schema pipeline (see §10) to produce records whose field names and structure are fully user-defined.

### 4.4 Streaming Mode

Invoked via `stream.py`. The generator loops indefinitely, emitting one event per `--rate` interval to the chosen target connection. Graceful shutdown is handled by catching SIGINT/SIGTERM.

---

## 5. CLI Package

`src/fraud_generator/cli/` is the SOLID orchestration layer introduced in v4.1.0. It cleanly separates argument parsing, constants, index building, runner dispatch, and parallel worker functions.

### 5.1 `args.py`

Single function `build_parser(available_formats: list) -> ArgumentParser`. Declares all ~25 CLI arguments; never constructs any domain objects.

Key arguments:

| Argument | Values | Description |
|---|---|---|
| `--type` | `transactions`, `rides`, `all` | Entity type to generate |
| `--size` | e.g. `100MB`, `5GB` | Target output size |
| `--output` | directory path or `s3://…` | Destination |
| `--format` | `jsonl`, `csv`, `parquet`, … | Output format |
| `--fraud-rate` | `0.0 – 1.0` | Fraction of fraudulent records |
| `--workers` | integer | ProcessPoolExecutor parallelism |
| `--seed` | integer | RNG seed for reproducibility |
| `--schema` | JSON file path | Activate schema mode |
| `--compress` | `none`, `gzip`, `zstd`, `snappy` | Compression codec |
| `--profiles` | flag | Enable behavioural profiles |

### 5.2 `constants.py`

All numeric tuning constants in one place:

| Constant | Value | Meaning |
|---|---|---|
| `TARGET_FILE_SIZE_MB` | 128 | Maximum size per output file |
| `BYTES_PER_TRANSACTION` | 500 | Estimated JSON bytes for one transaction |
| `BYTES_PER_RIDE` | 575 | Estimated JSON bytes for one ride |
| `TRANSACTIONS_PER_FILE` | 268,435 | Pre-computed from above (128 MB / 500 B) |
| `RIDES_PER_FILE` | 223,696 | Pre-computed from above |
| `RIDES_PER_DRIVER` | 50 | Rides assigned to each driver |
| `STREAM_FLUSH_EVERY` | 5,000 | Lines between fsync calls |

### 5.3 `index_builder.py`

Builds the in-memory lookup tables used by workers before the executor pool is launched:

```python
# Transaction pipeline
customers, devices = generate_customers_and_devices(num, use_profiles, seed)
# Returns: List[dict], List[dict]  (picklable — no class instances)

# Ride pipeline
drivers = generate_drivers(num, seed)
# Returns: List[dict]
```

**Why plain dicts?** Worker arguments must survive `pickle` serialisation. Using `NamedTuple`-backed index types or generator class instances fails; plain lists of dicts are always safe.

### 5.4 Runners

All runners implement `BaseRunner(ABC)` with a single abstract method:

```python
class BaseRunner(ABC):
    @abstractmethod
    def run(self, args: Namespace) -> None: ...
```

| Runner | File | Responsibility |
|---|---|---|
| `BatchRunner` | `runners/batch_runner.py` | Local disk, 4-phase pipeline, ProcessPoolExecutor |
| `MinIORunner` | `runners/minio_runner.py` | S3/MinIO upload, adaptive executor per format |
| `SchemaRunner` | `runners/schema_runner.py` | Declarative schema generation, JSONL output |

**4-phase pipeline** (BatchRunner and MinIORunner):

```
Phase 1 — Customers & Devices   → customers.jsonl, devices.jsonl
Phase 2 — Transactions           → transactions_00000.jsonl …
Phase 3 — Drivers                → drivers.jsonl
Phase 4 — Rides                  → rides_00000.jsonl …
```

Phases 1 and 3 run sequentially (single-process); phases 2 and 4 run in parallel via an executor pool.

### 5.5 Workers

Top-level module-level functions — **not methods** — so they are pickle-safe for `ProcessPoolExecutor`.

| Function | File | Produces |
|---|---|---|
| `worker_generate_batch(args: tuple)` | `workers/tx_worker.py` | One transactions JSONL file |
| `worker_generate_rides_batch(args: tuple)` | `workers/ride_worker.py` | One rides JSONL file |
| `generate_transaction_batch(...)` | `workers/batch_gen.py` | In-memory list of transaction dicts |
| `generate_ride_batch(...)` | `workers/batch_gen.py` | In-memory list of ride dicts |
| `worker_upload_parquet_transactions(args)` | `workers/minio_parquet.py` | Parquet file → MinIO upload |
| `worker_upload_parquet_rides(args)` | `workers/minio_parquet.py` | Parquet file → MinIO upload |

Workers use a **streaming write pattern**: they open the output file, iterate the generator, and write lines in 1,000-line buffers — never accumulating the full batch in memory.

---

## 6. Generators

All generators are stateless after construction. They accept identifiers as arguments and return plain `dict` objects.

### `CustomerGenerator`

```
src/fraud_generator/generators/customer.py
```

```python
gen = CustomerGenerator(seed=42)
customer = gen.generate(customer_id="CUS-0001")
# Returns dict with: customer_id, name, cpf, email, phone,
#   address (nested dict: street, city, state, zip_code, lat, lon),
#   profile, registration_date, age, income_bracket, …
```

Internally uses `Faker` (pt-BR locale) for names, addresses, and contact details. CPF is generated via [`validators/cpf.py`](#14-validators).

### `DeviceGenerator`

```
src/fraud_generator/generators/device.py
```

```python
device = DeviceGenerator(seed=42).generate(device_id="DEV-001", customer_id="CUS-0001")
# Returns dict with: device_id, customer_id, device_type, os, model,
#   fingerprint, ip_address, trusted_device, …
```

### `TransactionGenerator`

```
src/fraud_generator/generators/transaction.py  (594 lines)
```

```python
tx = TransactionGenerator(
    fraud_rate=0.05, seed=42, use_profiles=True
).generate(
    tx_id="TX-001",
    customer_id="CUS-0001",
    device_id="DEV-001",
    timestamp=datetime(...),
    customer_state="SP",
    customer_profile="young_digital",   # optional
    session_state=CustomerSessionState(), # optional
    customer_cpf="123.456.789-09",      # optional; used to hash payer CPF in PIX BACEN fields
)
```

Fraud injection is explicit: fraud type is drawn from `FRAUD_TYPES_LIST` and injects field combinations (inflated amounts, mismatched devices, impossible locations, etc.) rather than creating separate record types.

**Banking fraud types (25):**
`ENGENHARIA_SOCIAL`, `PIX_GOLPE`, `CONTA_TOMADA`, `CARTAO_CLONADO`, `FRAUDE_APLICATIVO`, `BOLETO_FALSO`, `FALSA_CENTRAL_TELEFONICA`, `COMPRA_TESTE`, `MULA_FINANCEIRA`, `CARD_TESTING`, `MICRO_BURST_VELOCITY`, `WHATSAPP_CLONE`, `DISTRIBUTED_VELOCITY`, `PHISHING_BANCARIO`, `FRAUDE_QR_CODE`, `FRAUDE_DELIVERY_APP`, `MAO_FANTASMA`, `CREDENTIAL_STUFFING`, `EMPRESTIMO_FRAUDULENTO`, `GOLPE_INVESTIMENTO`, `SIM_SWAP`, `PIX_AGENDADO_FRAUDE`, `SEQUESTRO_RELAMPAGO`, `SYNTHETIC_IDENTITY`, `DEEP_FAKE_BIOMETRIA`

**`_add_type_specific_fields` signature** (v4.2):

```python
def _add_type_specific_fields(
    self,
    tx: dict,
    tx_type: str,
    banco_destino: str,
    customer_id: str = '',
    customer_cpf: Optional[str] = None,
) -> None:
```

`customer_cpf` is forwarded from `generate()` so that PIX BACEN fields (`cpf_hash_pagador`) hash the real customer CPF rather than a fallback value.

### `DriverGenerator`

```
src/fraud_generator/generators/driver.py  (380 lines)
```

```python
driver = DriverGenerator(seed=42).generate(driver_id="DRV-001", state="SP")
# Returns dict with: driver_id, name, cpf, cnh (license), vehicle,
#   apps (list of ride-share apps), categories, state, coordinates, rating, …
```

Standalone utility functions handle Brazilian driver's licence (CNH) generation, Mercosul licence plate formatting, and vehicle-to-category mapping.

### `RideGenerator`

```
src/fraud_generator/generators/ride.py  (526 lines)
```

```python
ride = RideGenerator(fraud_rate=0.03, seed=42).generate(
    ride_id="RIDE-001",
    driver_id="DRV-001",
    passenger_id="CUS-0001",
    timestamp=datetime(...),
    passenger_state="SP",
    passenger_profile="young_digital",  # optional
    force_fraud=None,                   # optional: forces a specific fraud type
)
```

**Spatial computation:** Origin and destination POIs (Points of Interest) are looked up from `config/geography.py`. Distance is always calculated via **Haversine** (great-circle), never Euclidean.

```python
def haversine_distance(lat1, lon1, lat2, lon2) -> float:  # km
```

Surge pricing is a function of time-of-day and weather condition. Fare formula: `base_fare + (distance × per_km_rate) + (duration × per_min_rate)`.

**Ride-share fraud types (11):**
`GHOST_RIDE`, `GPS_SPOOFING`, `SURGE_ABUSE`, `MULTI_ACCOUNT_DRIVER`, `PROMO_ABUSE`, `RATING_FRAUD`, `SPLIT_FARE_FRAUD`, `REFUND_ABUSE`, `PAYMENT_CHARGEBACK`, `DESTINATION_DISPARITY`, `ACCOUNT_TAKEOVER_RIDE`

---

## 7. Behavioral Profiles

Profiles make generated data statistically coherent — customers behave consistently across all records.

### Transaction Profiles (`profiles/behavioral.py`)

```python
class ProfileType(Enum):
    YOUNG_DIGITAL       = "young_digital"
    BUSINESS_OWNER      = "business_owner"
    TRADITIONAL_ELDERLY = "traditional_elderly"
    MIDDLE_CLASS        = "middle_class"
    HIGH_INCOME         = "high_income"
    LOW_INCOME          = "low_income"
    CORPORATE           = "corporate"
```

Each `BehavioralProfile` dataclass holds weighted distributions for:
- Transaction types (PIX, TED, credit card, debit, …)
- MCC (Merchant Category Codes)
- Channel (mobile, web, ATM, branch)
- Transaction hour / weekend probability
- Value range / distribution

Helper functions provide deterministic selection per profile:

```python
get_transaction_type_for_profile(profile_name) -> str
get_mcc_for_profile(profile_name)              -> str
get_channel_for_profile(profile_name)          -> str
get_transaction_hour_for_profile(profile_name, is_weekend) -> int
get_transaction_value_for_profile(profile_name, ...) -> float
get_monthly_transactions_for_profile(profile_name) -> int
should_transact_on_weekend(profile_name)       -> bool
```

### Ride Profiles (`profiles/ride_behavioral.py`)

```python
class RideProfileType(Enum):
    FREQUENT_COMMUTER     = "frequent_commuter"
    OCCASIONAL_USER       = "occasional_user"
    BUSINESS_TRAVELLER    = "business_traveller"
    NIGHT_OWL             = "night_owl"
    BUDGET_CONSCIOUS      = "budget_conscious"
    PREMIUM_RIDER         = "premium_rider"
    TOURIST               = "tourist"
```

Maps customer transaction profiles → ride profiles. Helper functions:

```python
get_preferred_app_for_profile(profile_name)      -> str   # "Uber", "99", "InDriver"
get_preferred_category_for_profile(profile_name) -> str   # "UberX", "Comfort", …
get_preferred_hour_for_profile(profile_name)     -> int
should_tip_for_profile(profile_name)             -> bool
get_tip_percentage_for_profile(profile_name)     -> float
should_accept_surge_for_profile(profile_name, surge_multiplier) -> bool
```

---

## 8. Exporters

All exporters implement `ExporterProtocol(ABC)`:

```python
class ExporterProtocol(ABC):
    format_name: str          # "jsonl", "csv", …
    extension:   str          # ".jsonl", ".csv", …

    def export_batch(self, records: Iterable[dict], output_path: str, **kwargs) -> ExportStats
    def export_file(self, input_path: str, output_path: str, **kwargs) -> ExportStats
```

### Exporter Registry

```python
from fraud_generator.exporters import get_exporter, list_formats, is_format_available

exporter = get_exporter("parquet")          # returns ParquetExporter instance
exporter = get_exporter("jsonl", compress="zstd")
```

### Available Exporters

| Class | Format | Notes |
|---|---|---|
| `JSONExporter` | JSONL | Line-by-line; memory efficient |
| `JSONArrayExporter` | JSON array | Entire file as JSON array |
| `CSVExporter` | CSV | Streaming via `csv.DictWriter` |
| `TSVExporter` | TSV | Subclass of CSVExporter |
| `ParquetExporter` | Parquet | Requires `pyarrow` + `pandas`; schema inferred |
| `ParquetPartitionedExporter` | Parquet | Partition by state / date |
| `ArrowIPCExporter` | Arrow IPC | Binary columnar streaming format |
| `DatabaseExporter` | SQLite / PG | Batched `INSERT` via SQLAlchemy |
| `MinIOExporter` | Any → S3 | Wraps other exporters + boto3 upload |

### Compression

Compression is orthogonal to format. The `CompressionHandler` wraps any file write:

```python
# utils/compression.py
backends: GzipCompressor | ZstdCompressor | SnappyCompressor | NoOpCompressor
get_compressor(codec: str) -> CompressionBackend
```

Codec is auto-detected from file extension if `--compress` is not specified.

### `MinIOStreamWriter`

Located in `exporters/minio_exporter.py`, `MinIOStreamWriter` enables streaming multipart uploads — data is pushed to S3-compatible storage without first materialising to a temp file (used for JSONL/CSV formats).

---

## 9. Connections (Streaming)

All connections implement `ConnectionProtocol(ABC)`:

```python
class ConnectionProtocol(ABC):
    def connect(self) -> None: ...
    def send(self, record: dict) -> None: ...
    def close(self) -> None: ...
```

### Registry

```python
from fraud_generator.connections import get_connection, is_target_available

conn = get_connection("kafka")    # KafkaConnection
conn = get_connection("webhook")  # WebhookConnection
conn = get_connection("stdout")   # StdoutConnection
```

### Implementations

| Class | Target | Notes |
|---|---|---|
| `StdoutConnection` | stdout | JSON-serialised lines; default target |
| `KafkaConnection` | Apache Kafka | Requires `kafka-python`; configurable topic/broker |
| `WebhookConnection` | HTTP endpoint | POST with JSON body; configurable URL + headers |

Connection configuration is provided via environment variables or CLI arguments parsed in `stream.py`.

---

## 10. Schema System

The declarative schema system allows generating records with custom field names and nested structure without modifying Python code.

```
schemas/banking_full.json
  └─► SchemaParser  (validates structure, resolves field catalog)
        └─► AISchemaCorrector  (optional: repairs malformed JSON, resolves aliases)
              └─► SchemaEngine  (orchestrates generators, calls FieldMapper per record)
                    └─► FieldMapper  (resolves namespace references to generator output)
```

### `schema/parser.py` — `SchemaParser`

Validates the schema JSON against `FIELD_CATALOG` — the complete set of supported `namespace.field` references:

| Namespace | Entity |
|---|---|
| `transaction` | Banking transaction fields |
| `customer` | Customer fields (inc. `customer.address.city` etc.) |
| `device` | Device fields |
| `driver` | Driver fields |
| `ride` | Ride-share ride fields |

Non-strict mode: unknown fields emit a warning and are skipped, never raising.

### `schema/mapper.py` — `FieldMapper`

Resolves output fields to values. Supported reference types:

```jsonc
{
  "my_amount":   "transaction.amount",   // namespace.field — resolved from generator output
  "company_id":  "static:ACME-CORP",     // static value — literal string
  "full_name":   "faker:name",           // faker method — calls Faker().name()
  "created_at":  "transaction.timestamp" // nesting supported via dot-path
}
```

Internal `_DictWrapper` wraps nested dict fields (e.g. `customer.address`) to allow dot-path traversal.

### `schema/ai_corrector.py` — `AISchemaCorrector`

Two-stage correction pipeline:

1. **Heuristic repair** (always runs): fixes trailing commas, JS-style comments, single-quoted keys, unquoted property names
2. **Alias resolution** (always runs): 40+ built-in mappings from Portuguese/domain aliases to canonical references (e.g. `"valor"` → `"transaction.amount"`, `"motorista_id"` → `"driver.driver_id"`)
3. **LLM correction** (optional, `provider=openai|anthropic`): sends malformed schema to GPT-4 / Claude for repair when heuristics fail

```python
corrector = AISchemaCorrector(provider="none")  # heuristics only
result: CorrectionResult = corrector.correct(raw_schema_dict)
```

### `schema/engine.py` — `SchemaEngine`

Orchestrates the full schema-driven generation loop. Two internal sub-pipelines:

- `_generate_banking()` — creates customer → device → transaction per record
- `_generate_rides()` — creates customer → driver → ride per record

The engine flattens the generator output into a `_DictWrapper`-backed object tree so that `FieldMapper` can resolve any dot-path without the mapper needing to know the generator APIs.

---

## 11. Configuration Layer

Static data lives in `src/fraud_generator/config/`. Convention: each module exports a `*_LIST` (all values), a `*_WEIGHTS` (probability distribution), and helper functions `get_*(value)`.

| Module | Content |
|---|---|
| `banks.py` | Brazilian bank codes + names (BACEN codes), weighted selection |
| `merchants.py` | Merchant names, MCC codes, per-MCC weights |
| `geography.py` | 27 Brazilian states, major cities, coordinates, POIs |
| `transactions.py` | Transaction types, channels, fraud type list, value ranges |
| `rideshare.py` | Apps (Uber, 99, InDriver), vehicle categories, surge rules, fare tables |
| `devices.py` | Device types, OS versions, browser fingerprint components |
| `fraud_patterns.py` | Fraud pattern definitions and field-level injection rules |
| `weather.py` | Weather condition types, seasonal distributions, city-level base conditions |
| `calibration_loader.py` | Runtime override loader for RAG-calibrated fraud prevalences |

### Calibration Override System

The `calibration_loader.py` module loads `data/rules/fraud_pattern_overrides.json` at import time. This file is produced by the FraudFlow RAG pipeline (52K+ chunks, 66 sources) and overrides the hardcoded prevalences and amount multipliers in `fraud_patterns.py`.

**Override flow:**

```
fraud_pattern_overrides.json  →  calibration_loader.py  →  TransactionGenerator
         (RAG output)              (normalize weights)       (uses calibrated values)
```

If the override file is absent, all values fall back to the hardcoded defaults with no error. The file is read once and cached.

### Calibration Results (V5 — 2026-03-25)

| Metric | Before (defaults) | After (RAG-calibrated) | Delta |
|---|:---:|:---:|:---:|
| Realism score | 7.9/10 | **8.0/10** | +1.3% |
| Fraud/legit ratio | 1.87× | **5.09×** | +172% |
| Fraud types | 17 | **25** | +8 |
| Fraud mean | R$ 493 | **R$ 1,210** | +145% |
| Tests passing | 194 | 194 | = |

---

## 12. Enricher Pipeline

The enricher pipeline (introduced in v4.7) applies 8 sequential enrichment stages to each transaction record after initial generation. Each enricher implements `EnricherProtocol` and receives a shared `GeneratorBag` with read-only access to caches, RNG buffers, and config.

### Pipeline Architecture

```
TransactionGenerator.generate()
    │
    └─► Raw transaction dict
          │
          └─► Enricher Pipeline (8 stages, canonical order)
                │
                ├─ 1. TemporalEnricher    — sets unusual_time flag
                ├─ 2. GeoEnricher         — IBGE centroids, distance_from_home
                ├─ 3. FraudEnricher       — fraud-pattern field overrides, multi-label taxonomy
                ├─ 4. PIXEnricher         — BACEN pacs.008 fields (12 PIX-specific fields)
                ├─ 5. DeviceEnricher      — device_age_days, emulator/vpn detection
                ├─ 6. SessionEnricher     — velocity, merchant novelty, travel detection
                ├─ 7. RiskEnricher        — fraud_risk_score, 17 signals, ring assignments
                └─ 8. BiometricEnricher   — 10 biometric fields (null for free tier)
                      │
                      └─► Enriched transaction dict
```

### `EnricherProtocol` (Protocol)

```python
class EnricherProtocol(Protocol):
    def enrich(self, tx: dict, bag: GeneratorBag) -> None: ...
```

All enrichers mutate `tx` in-place (no return value). The `GeneratorBag` dataclass provides shared state (customer ID, profile, device, session state, ring registry, etc.).

### Enricher Details

| # | Enricher | Fields Set | Tier |
|---|----------|-----------|------|
| 1 | `TemporalEnricher` | `unusual_time` | Free |
| 2 | `GeoEnricher` | `geolocation_lat/lon`, `codigo_ibge_municipio`, `municipio_nome`; Pro+: `distance_from_home_km`, `is_known_location` | Free / Pro |
| 3 | `FraudEnricher` | Fraud-pattern-specific overrides (amount, device, channel); 24+ fraud type labels | Free |
| 4 | `PIXEnricher` | 12 BACEN fields: `end_to_end_id`, `ispb_pagador/recebedor`, `cpf_hash`, `pacs_status`, etc. | Free |
| 5 | `DeviceEnricher` | `device_age_days`, `emulator_detected`, `vpn_active`, `ip_type` | Free |
| 6 | `SessionEnricher` | `velocity_transactions_24h`, `accumulated_amount_24h`, `new_merchant/beneficiary`; Pro+: extended velocity windows | Free / Pro |
| 7 | `RiskEnricher` | `fraud_risk_score`, `fraud_signals` (17 signals + 4 rules), `fraud_ring_id`, `ring_role` | Free |
| 8 | `BiometricEnricher` | 10 biometric fields (`typing_speed_avg_ms`, `touch_pressure_avg`, etc.) | Paid only |

### Pipeline Factory

```python
from fraud_generator.enrichers.pipeline_factory import get_default_pipeline

pipeline = get_default_pipeline()  # returns list of 8 enricher instances in canonical order
```

---

## 13. Data Models & Indexes

### `models/`

Dataclasses representing the output schema of each entity type — used for type-checking and documentation, not for serialisation (generators return plain dicts):

| Module | Class |
|---|---|
| `models/customer.py` | `Customer` |
| `models/device.py` | `Device` |
| `models/transaction.py` | `Transaction` |
| `models/ride.py` | `Ride` (435 lines — most complex model) |

### Index Types (`utils/streaming.py`)

Lightweight `NamedTuple` structures used to pass entity data between pipeline stages without full objects:

```python
class CustomerIndex(NamedTuple):
    customer_id: str; state: str; profile: str; lat: float; lon: float; ...

class DeviceIndex(NamedTuple):
    device_id: str; customer_id: str; trusted: bool; ...

class DriverIndex(NamedTuple):
    driver_id: str; state: str; lat: float; lon: float; apps: list; ...

class RideIndex(NamedTuple):
    ride_id: str; driver_id: str; ...
```

Constructor helpers:

```python
create_customer_index(customer_dict) -> CustomerIndex
create_device_index(device_dict)     -> DeviceIndex
create_driver_index(driver_dict)     -> DriverIndex
create_ride_index(ride_dict)         -> RideIndex
```

### `CustomerSessionState`

Maintains per-customer mutable state across multiple transaction records in the same worker run (e.g. last transaction timestamp, fraud velocity counter).

---

## 14. Utilities

### `utils/streaming.py` (590 lines)

The main utility module:

| Symbol | Purpose |
|---|---|
| `CustomerIndex`, `DeviceIndex`, `DriverIndex`, `RideIndex` | Index NamedTuples |
| `CustomerSessionState` | Mutable per-customer streaming state |
| `BatchGenerator` | Stateful generator coordinating customer→transaction sequences |
| `batch_iterator(iterable, n)` | Yields fixed-size chunks from any iterable |
| `chunked_range(start, stop, size)` | Yields `(start, end)` slice pairs |
| `estimate_memory_usage(n_customers)` | RAM estimation helper |
| `ProgressTracker` | Thread-safe elapsed/rate/ETA tracking; prints to stderr |

### `utils/weight_cache.py`

Eliminates repeated `random.choices()` weight normalisation overhead (performance issue P2 from roadmap):

```python
@dataclass
class WeightCache:
    choices: np.ndarray
    weights: np.ndarray
    def sample(self, n=1) -> Any

get_weight_cache(name, choices, weights) -> WeightCache   # module-level LRU cache
make_weighted_sampler(name, choices, weights) -> Callable
```

Weights are pre-normalised to `sum=1.0` and stored as numpy arrays. Registered caches are module-level singletons (cleared with `clear_caches()`).

### `utils/compression.py` (238 lines)

Strategy pattern for compression:

```
CompressionBackend (ABC)
  ├── GzipCompressor
  ├── ZstdCompressor   (requires zstandard package)
  ├── SnappyCompressor (requires python-snappy)
  └── NoOpCompressor

CompressionHandler — context manager around any file write operation
get_compressor(codec) -> CompressionBackend
```

### `utils/helpers.py`

```python
generate_ip_brazil()          -> str    # random Brazilian IP range
generate_hash(value, length)  -> str    # SHA-256 hex prefix
generate_random_hash(length)  -> str
weighted_choice(options: dict) -> str   # dict of {value: weight}
parse_size("100MB")            -> int   # bytes
format_size(bytes)             -> str   # "128.0 MB"
format_duration(seconds)       -> str   # "2m 34s"
```

### `utils/redis_cache.py`

Optional Redis-backed index persistence. Allows sharing pre-built customer/device indexes across multiple generator processes or restarts, skipping the build phase.

```python
is_redis_available()              -> bool
load_cached_indexes(redis_url, ...) -> Optional[tuple]
save_cached_indexes(redis_url, ...) -> None
```

---

## 15. Validators

### `validators/cpf.py` (257 lines)

Complete Brazilian CPF (Cadastro de Pessoas Físicas) implementation:

```python
generate_valid_cpf(formatted=False) -> str   # "12345678900" or "123.456.789-00"
validate_cpf(cpf: str)              -> bool  # checks both check digits
format_cpf(cpf: str)                -> str   # adds formatting
unformat_cpf(cpf: str)              -> str   # removes formatting
generate_cpf_from_state(state_code) -> str   # state-keyed CPF (3rd digit encodes state)
```

The algorithm implements the standard mod-11 double-digit validation. CPFs are always validated at generation time; the library never stores or emits invalid CPFs.

---

## 16. Licensing System

The licensing system (`src/fraud_generator/licensing/`) implements HMAC-SHA256 signed licenses with 5 plan tiers for the hosted API at synthfin.com.br. The open-source CLI has no license restrictions.

### Plan Tiers

| Plan | Events/month | Concurrent | Output GB | Kafka | req/s |
|---|---:|---:|---:|---|---:|
| FREE | 1M | 2 | 2.0 | No | 5.0 |
| STARTER | 5M | 3 | 5.0 | No | 5.0 |
| PRO | 100M | 10 | 20.0 | Yes | 20.0 |
| TEAM | unlimited | unlimited | unlimited | Yes | 50.0 |
| ENTERPRISE | unlimited | unlimited | unlimited | Yes | unlimited |

### Components

| Module | Class / Function | Purpose |
|---|---|---|
| `license.py` | `License`, `LicensePlan`, `LicenseError` | License dataclass with HMAC signing (`create()`, `verify_signature()`, `is_expired`) |
| `limits.py` | `PlanLimits`, `PLAN_LIMITS` | Frozen dataclass per plan with 16 limit fields (rate, events, formats, etc.) |
| `validator.py` | `load_from_env()`, `validate_env()`, `check_format_allowed()` | Reads `FRAUDGEN_*` env vars, validates HMAC signature, checks expiry, optional heartbeat |

### License Validation Flow

```
ENV vars (FRAUDGEN_LICENSE_ID, FRAUDGEN_EMAIL, FRAUDGEN_PLAN, ...)
  └─► load_from_env() → License object
        └─► validate_env(phone_home=True)
              ├─ verify_signature() — HMAC-SHA256 check
              ├─ is_expired — datetime comparison
              ├─ 7-day expiry warning
              └─ _send_heartbeat() — POST to api.synthfin.com.br
```

---

## 17. Design Decisions

### SOLID Modular > DDD > Clean Architecture

**Choice:** SOLID Modular + Command/Runner pattern  
**Rejected alternatives:** Domain-Driven Design, Clean Architecture (ports/adapters)

**Rationale:**
- The application is a **generation pipeline**, not a domain with rich business rules
- DDD introduces entities/aggregates/repositories that add bureaucracy without benefit when the domain is "produce synthetic records"
- Clean Architecture's port/adapter layers would add 3–4 indirection levels to what is essentially `generate() → write()`
- SOLID Modular gives the same extensibility (open/closed, dependency inversion) with far less ceremony

### ProcessPoolExecutor for CPU-bound; ThreadPoolExecutor for I/O-bound

Python's GIL prevents true CPU parallelism in threads. Batch generation is CPU-bound (Faker, random, Haversine) so `ProcessPoolExecutor` is used. MinIO JSONL/CSV upload is I/O-bound (network wait) so `ThreadPoolExecutor` is sufficient and avoids serialisation overhead.

### Workers Must Be Top-Level Functions

`ProcessPoolExecutor.submit(fn, ...)` requires `fn` to be picklable. Class methods and lambda functions are not picklable across process boundaries on Linux (fork+exec on macOS/Windows). All worker functions in `cli/workers/` are therefore module-level `def` statements.

### Deterministic Seed Per Worker

```python
worker_seed = base_seed + batch_id × 12345   # transactions
worker_seed = base_seed + batch_id × 54321   # rides
```

This ensures:
1. The same base seed + same count always produces the same dataset
2. Workers can run in any order without collisions
3. Different worker counts produce the same per-batch sub-dataset

### Profile Assignment is Sticky

A customer's behavioural profile is assigned once at customer generation time and is fixed for all downstream records. This makes the dataset statistically coherent (a `low_income` customer does not occasionally make `high_income`-profile transactions).

### Fraud Injection via Field Combinations

Fraud is injected by overwriting specific fields in an otherwise normal record (e.g. inflating `amount`, changing `device_id`, inserting a foreign `ip_address`). This mirrors real fraud — fraudsters don't create obviously labelled records; they create records that look almost normal.

### Weights Must Be Normalised for WeightCache

`random.choices()` accepts unnormalised weights, but `WeightCache` pre-normalises to `sum=1.0` (required for `numpy`). When adding new config weights, ensure they sum to 1.0 or the cache will produce incorrect distributions.

---

## 18. Data Flow Diagrams

### Batch Mode — Full Flow

```
generate.py
    │
    └─► BatchRunner.run(args)
             │
             ├─[Phase 1]─► CustomerGenerator.generate() × N
             │              DeviceGenerator.generate() × N
             │              ──► customers.jsonl, devices.jsonl
             │
             ├─[Phase 2]─► ProcessPoolExecutor
             │              │  worker_generate_batch(batch_args) [×W workers]
             │              │    ├─ TransactionGenerator.generate() per tx
             │              │    └─ write 1000-line buffered JSONL
             │              ──► transactions_00000.jsonl … transactions_NNNNN.jsonl
             │
             ├─[Phase 3]─► DriverGenerator.generate() × M
             │              ──► drivers.jsonl
             │
             └─[Phase 4]─► ProcessPoolExecutor
                            │  worker_generate_rides_batch(batch_args) [×W workers]
                            │    ├─ RideGenerator.generate() per ride
                            │    └─ write 1000-line buffered JSONL
                            ──► rides_00000.jsonl … rides_NNNNN.jsonl
```

### Schema Mode — Full Flow

```
generate.py --schema banking_full.json
    │
    └─► SchemaRunner.run(args)
             │
             └─► AISchemaCorrector.correct(raw_json)
                   │
                   └─► SchemaParser.parse(corrected_json) → ParsedSchema
                         │
                         └─► SchemaEngine.generate(parsed_schema, n_records)
                               │
                               ├─ CustomerGenerator.generate()
                               ├─ DeviceGenerator.generate()
                               ├─ TransactionGenerator.generate()  (banking)
                               │   or
                               ├─ DriverGenerator.generate()
                               └─ RideGenerator.generate()         (rideshare)
                                        │
                                        └─► FieldMapper.resolve(output_tree)
                                              │
                                              └─► write JSONL line
```

### Streaming Mode — Full Flow

```
stream.py --target kafka --type transactions
    │
    ├─► KafkaConnection.connect()
    │
    └─► loop (until SIGINT/SIGTERM)
             │
             ├─ CustomerGenerator.generate()
             ├─ DeviceGenerator.generate()
             ├─ TransactionGenerator.generate()
             │
             └─► KafkaConnection.send(record)
                       └─► kafka-python producer.send(topic, record)
```

---

## 19. Performance Characteristics

| Metric | Value | Conditions |
|---|---|---|
| Batch throughput | ~20,892 rec/s | 4 workers, JSONL, no compression, 12-core host |
| Schema mode throughput | ~7,800 rec/s | JSONL, schema mode, single-process |
| Memory per worker | ~120–180 MB | 128 MB target file, index in-memory |
| MinIO upload (JSONL) | network-bound | ThreadPoolExecutor |
| MinIO upload (Parquet) | CPU+network | ProcessPoolExecutor (generate+compress in child) |

### Known Performance Issues (Roadmap)

| ID | Issue | Status |
|---|---|---|
| P1 | Fraud patterns lack sequential/velocity checks | Open |
| P2 | `random.choices()` called per-record (~25% overhead) | Mitigated by `WeightCache` |
| P3 | CSV/Parquet accumulate full list before write for >1 GB jobs | Open — needs streaming export refactor |

---

## 20. Extension Guide

### Adding a new output format

1. Create `src/fraud_generator/exporters/my_format_exporter.py`
2. Implement `ExporterProtocol`:
   ```python
   class MyFormatExporter(ExporterProtocol):
       format_name = "myformat"
       extension   = ".myfmt"
       def export_batch(self, records, output_path, **kwargs) -> ExportStats: ...
   ```
3. Register in `src/fraud_generator/exporters/__init__.py`:
   ```python
   from .my_format_exporter import MyFormatExporter
   _EXPORTERS["myformat"] = MyFormatExporter
   ```

### Adding a new streaming target

1. Create `src/fraud_generator/connections/my_connection.py`
2. Implement `ConnectionProtocol`:
   ```python
   class MyConnection(ConnectionProtocol):
       def connect(self): ...
       def send(self, record: dict): ...
       def close(self): ...
   ```
3. Register in `src/fraud_generator/connections/__init__.py`

### Adding a new behavioural profile

1. Add a value to `ProfileType(Enum)` in `profiles/behavioral.py`
2. Create a `BehavioralProfile` instance for it with appropriate weighted distributions
3. Register in `_PROFILES` dict within the same module

### Adding new schema field references

1. Add the `namespace.field` entry to `FIELD_CATALOG` in `schema/parser.py`
2. If it references a new entity, add it to both:
   - `SchemaEngine._generate_banking()` or `_generate_rides()` in `schema/engine.py`
   - `FieldMapper.resolve()` in `schema/mapper.py`
3. Optionally add Portuguese/domain aliases to `_ALIAS_MAP` in `schema/ai_corrector.py`

---

## 21. Known Gaps & Limitations

| ID | Category | Issue | Severity | Status |
|---|---|---|---|---|
| P1 | Performance | Fraud patterns lack sequential/velocity checks | Medium | Open |
| P2 | Performance | `random.choices()` per-record overhead | Low | Mitigated (WeightCache) |
| P3 | Performance | Parquet append reads entire file into memory (OOM >1GB) | High | Open |
| S1 | Security | Docker VERIFY_KEY exposed via ARG→ENV | High | Open |
| S2 | Security | Container runs as root | Medium | Open |
| T1 | Testing | No tests for Connections (Kafka, Webhook, Stdout) | Medium | Open |
| T2 | Testing | No tests for Config modules (banks, geography, etc.) | Low | Open |
| T3 | Testing | ~40% estimated test coverage | Medium | Open |
| D1 | Data | CSV uses `.` separator, Parquet uses `_` for nested fields | Medium | Open |
| D2 | Data | Ring registry is module-level singleton (thread-unsafe) | Medium | Open |
| D3 | Data | Schema mode does not validate output against input schema | Low | Open |

For a complete analysis, see [docs/analysis/ANALISE_GAPS_E_MELHORIAS.md](docs/analysis/ANALISE_GAPS_E_MELHORIAS.md).

---

## 22. Environment & Dependencies

### Python Version

Python 3.8+ required. Tested on Python 3.10 / 3.11.

### Installation

```bash
# Core (batch mode)
pip install -r requirements.txt

# Streaming (adds kafka-python)
pip install -r requirements-streaming.txt
```

### Core Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| `Faker` | ≥ 3.8 | Names, addresses, phone numbers (pt-BR locale) |
| `pandas` | ≥ 2.0 | CSV operations, DataFrame manipulation |
| `pyarrow` | ≥ 14.0 | Parquet + Arrow IPC format |
| `boto3` | ≥ 1.28 | MinIO / S3 upload |
| `numpy` | — | WeightCache vectorised sampling |

### Optional Dependencies

| Package | Purpose | Auto-detected? |
|---|---|---|
| `zstandard` | zstd compression | Yes — falls back to gzip |
| `python-snappy` | snappy compression | Yes — falls back to gzip |
| `kafka-python` | Kafka streaming | Yes — `is_target_available("kafka")` |
| `redis` | Index caching across processes | Yes — `is_redis_available()` |
| `openai` / `anthropic` | AI schema correction | Explicit provider arg |

### Environment Variables

| Variable | Purpose |
|---|---|
| `MINIO_ACCESS_KEY` | MinIO/S3 access key |
| `MINIO_SECRET_KEY` | MinIO/S3 secret key |
| `MINIO_ENDPOINT` | MinIO endpoint URL (default: localhost:9000) |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker list |
| `REDIS_URL` | Redis URL for index caching |
| `OPENAI_API_KEY` | OpenAI key for AI schema correction |
| `ANTHROPIC_API_KEY` | Anthropic key for AI schema correction |

### Docker

```bash
# Batch generation
docker run --rm -v $(pwd)/output:/output \
  afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output

# Streaming to stdout
docker run --rm \
  afborda/synthfin-data:latest \
  stream.py --target stdout --rate 10
```

The Docker image includes all core dependencies. For Kafka streaming, use the `-streaming` tagged image.

---

## 23. SynthFin Ecosystem

The **synthfin-data** library is the core engine of a larger SaaS platform. This section documents the relationship between components.

### Components

| Component | Role | Stack | Visibility |
|---|---|---|---|
| **synthfin-data** (this repo) | Core data generation engine | Python, Faker, PyArrow, Pandas | Public (Docker Hub) |
| **synthfin-api** | REST API wrapping the engine | FastAPI, Redis, MinIO, Stripe, Resend | Private (GHCR) |
| **synthfin-web** | SaaS dashboard + marketing site | Next.js 15, React 19, Tailwind | Private (GHCR) |
| **synthfin-saas** | Infrastructure orchestration | Docker Compose, Traefik v3, Ubuntu 24.04 | Private |

### Production Architecture

```
Cloudflare (Edge: DNS + WAF + DDoS)
  │
  └── Traefik v3 (TLS via Let's Encrypt)
        │
        ├── synthfin.com.br        → Landpage (Next.js, port 3001)
        ├── app.synthfin.com.br    → Dashboard (Next.js, port 3000)
        ├── api.synthfin.com.br    → API (FastAPI, port 8000)
        └── deploy.synthfin.com.br → CI/CD webhook (port 9090)
```

**Supporting services** (internal Docker network):
- **Redis 7**: Cache, session state, job queue, rate limiting
- **MinIO**: S3-compatible object storage for generated files
- **Deploy webhook**: HMAC-authenticated endpoint that pulls GHCR images and restarts services

### API Overview (v2)

The API exposes 15 endpoints under `/v2/`:

- **Auth**: register, verify email, rotate API key
- **Generate**: POST job → Redis queue → multiprocessing worker → MinIO storage
- **Jobs**: list, status, cancel
- **Download**: presigned MinIO URL or direct stream
- **Usage**: monthly quota and event counts
- **Billing**: Stripe Checkout session creation, subscription cancellation
- **Admin**: dashboard stats, user management, account freeze

Authentication uses `Bearer fgen_sk_*` API keys. Rate limiting and quota tracking are enforced per plan tier via Redis.

### CI/CD Pipeline

```
git push (main) → GitHub Actions
  ├── Build 3 Docker images (API, Web, Landpage) → push to GHCR
  └── Trigger deploy webhook on VPS
        ├── docker pull latest images
        ├── docker compose up -d --no-deps
        └── docker image prune -f
```

### Full Documentation

See [docs/analysis/ANALISE_ECOSSISTEMA_SYNTHFIN.md](docs/analysis/ANALISE_ECOSSISTEMA_SYNTHFIN.md) for a comprehensive ecosystem analysis including all endpoints, environment variables, security layers, and implementation status.

---

*Generated by GitHub Copilot — synthfin-data v4.15.1 (25 fraud patterns, RAG-calibrated)*
