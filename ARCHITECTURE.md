# Architecture — synthfin-data

> **Version:** 4.18.0 — 2026-04-15
> **Portuguese version:** [docs/ARQUITETURA.md](docs/ARQUITETURA.md)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [High-Level Structure](#2-high-level-structure)
3. [Entry Points](#3-entry-points)
4. [Execution Modes](#4-execution-modes)
5. [CLI Package](#5-cli-package)
6. [Generators](#6-generators)
7. [Behavioral Profiles](#7-behavioral-profiles)
8. [Enricher Pipeline](#8-enricher-pipeline)
9. [ML Quality Layer](#9-ml-quality-layer)
10. [Exporters](#10-exporters)
11. [Connections (Streaming)](#11-connections-streaming)
12. [Schema System](#12-schema-system)
13. [Configuration Layer](#13-configuration-layer)
14. [Data Models & Indexes](#14-data-models--indexes)
15. [Utilities](#15-utilities)
16. [Validators](#16-validators)
17. [Licensing System](#17-licensing-system)
18. [Design Decisions](#18-design-decisions)
19. [Data Flow Diagrams](#19-data-flow-diagrams)
20. [Performance Characteristics](#20-performance-characteristics)
21. [Extension Guide](#21-extension-guide)
22. [Known Gaps & Limitations](#22-known-gaps--limitations)
23. [Environment & Dependencies](#23-environment--dependencies)
24. [SynthFin Ecosystem](#24-synthfin-ecosystem)

---

## 1. Project Overview

**synthfin-data** produces synthetic banking and ride-share event datasets for ML model training, fraud detection research, and system integration testing. It generates datasets ranging from kilobytes to terabytes in multiple output formats, with an adversarial ML quality layer that validates data fidelity using LightGBM.

**Core capabilities:**

| Capability | Details |
|---|---|
| Data types | Banking transactions, ride-share rides |
| Output formats | JSONL, JSON Array, CSV, TSV, Parquet, Arrow IPC, MinIO/S3 |
| Compression | None, gzip, zstd, snappy (auto-detected) |
| Scale | MB → TB via streaming + multiprocessing |
| Fraud simulation | 25 banking fraud patterns + 11 ride-share, configurable rate |
| Reproducibility | Deterministic seed support with UUID5 watermark on transaction IDs |
| Schema customisation | Declarative JSON schema files with optional AI correction |
| Streaming | Stdout, Apache Kafka, HTTP Webhook, Redis Stream |
| ML validation | LightGBM adversarial classifier, per-type AUC-ROC, quality flags |

---

## 2. High-Level Structure

```
synthfin-data/
│
├── generate.py               Batch entry point (thin dispatcher)
├── stream.py                 Streaming entry point
├── check_schema.py           Output validation utility
│
├── schemas/                  Example declarative JSON schemas
├── docs/                     Documentation
├── tools/                    Analysis and training CLI tools
├── benchmarks/               Performance and quality benchmarks
├── models/                   Trained LightGBM models (gitignored)
│
└── src/fraud_generator/      Core library
    ├── cli/                  SOLID CLI orchestration layer
    │   ├── args.py
    │   ├── constants.py
    │   ├── index_builder.py
    │   ├── runners/          Command objects (batch, minio, schema)
    │   └── workers/          Worker functions (module-level, serialization-safe)
    ├── generators/           Entity generators (customer, device, driver, transaction, ride)
    ├── profiles/             Behavioural profile definitions
    ├── enrichers/            8-stage transaction enrichment pipeline
    ├── ml/                   ML quality validation (LightGBM adversarial classifier)
    │   ├── features.py       extract_features() — 31-feature DataFrame
    │   ├── trainer.py        Binary + 25 OvR per-type LightGBM classifiers
    │   └── evaluator.py      evaluate_batch() — AUC, quality flags, feature importance
    ├── exporters/            Output format strategy implementations
    ├── connections/          Streaming target strategy implementations
    ├── schema/               Declarative schema parsing, mapping, AI correction
    ├── config/               Static configuration data (banks, merchants, geography, fraud)
    ├── models/               Data structures and index types
    ├── utils/                Shared utilities (compression, weights, watermark, progress)
    ├── validators/           CPF validation algorithm
    └── licensing/            HMAC-signed license system (5 plan tiers)
```

---

## 3. Entry Points

### `generate.py`

Pure dispatcher — no business logic. Resolves which runner to invoke based on CLI flags:

```
parse args
    │
    ├─ --schema flag?  ──► SchemaRunner().run(args)
    ├─ MinIO URL?      ──► MinIORunner().run(args)
    └─ default         ──► BatchRunner().run(args)
```

### `stream.py`

Standalone streaming mode. Handles continuous event emission to stdout, Kafka, webhook, or redis-stream. Manages its own argument parsing, connection lifecycle, and graceful shutdown via SIGINT/SIGTERM.

---

## 4. Execution Modes

### 4.1 Batch Mode

```
CLI args
  └─► index_builder.generate_customers_and_devices()
        └─► ProcessPoolExecutor (N workers)
              ├─ tx_worker.worker_generate_batch()        → transactions_00000.jsonl …
              └─ ride_worker.worker_generate_rides_batch() → rides_00000.jsonl …
```

**Parallelism model:** One Python subprocess per batch file. Seed per worker = `base_seed + batch_id × K`, guaranteeing reproducibility regardless of worker count.

### 4.2 MinIO / S3 Mode

Activated when `--output` matches `s3://bucket/path/prefix`.

- **Parquet**: ProcessPoolExecutor — generate in child process → write temp file → upload via boto3
- **JSONL / CSV**: ThreadPoolExecutor — generate in main process → stream bytes → upload

### 4.3 Schema Mode

Activated by `--schema path/to/schema.json`. Uses the declarative schema pipeline to produce records with fully user-defined field names and structure.

### 4.4 Streaming Mode

Invoked via `stream.py`. Generator loops indefinitely, emitting one event per `--rate` interval.

Supported targets: `stdout`, `kafka`, `webhook`, `redis-stream`

---

## 5. CLI Package

### Runners

All runners implement `BaseRunner(ABC)`:

| Runner | Responsibility |
|---|---|
| `BatchRunner` | Local disk, 4-phase pipeline, ProcessPoolExecutor |
| `MinIORunner` | S3/MinIO upload, adaptive executor per format |
| `SchemaRunner` | Declarative schema generation, JSONL output |

**4-phase pipeline:**

```
Phase 1 — Customers & Devices   → customers.jsonl, devices.jsonl
Phase 2 — Transactions           → transactions_00000.jsonl …
Phase 3 — Drivers                → drivers.jsonl
Phase 4 — Rides                  → rides_00000.jsonl …
```

### Workers

Top-level module-level functions — serialization-safe for `ProcessPoolExecutor`.

Workers use a **streaming write pattern**: open file → iterate generator → write 1,000-line buffers — never accumulating the full batch in memory.

---

## 6. Generators

All generators are stateless after construction. They accept identifiers as arguments and return plain `dict` objects.

### `TransactionGenerator`

```
src/fraud_generator/generators/transaction.py
```

The central generator. `generate_with_pipeline()` is the active code path for all batch and streaming generation:

```python
tx = generator.generate_with_pipeline(
    tx_id="TX_000001",
    customer_id="CUST_001",
    device_id="DEV_001",
    timestamp=datetime(...),
    customer_state="AM",
    customer_profile="high_spender",
    session_state=CustomerSessionState(),
    customer_cpf="123.456.789-09",
    license=None,
)
```

Key design points:

- **`transaction_id`** uses `make_transaction_id(tx_id, customer_id, timestamp)` — UUID5 deterministic hash, verifiable via `is_synthfin_id()` in `utils/watermark.py`
- **`customer_state`** is included in the output dict (fixed v4.18) so `FraudEnricher` generates realistic location anomalies relative to the customer's actual state
- **Fraud injection** overwrites specific fields in an otherwise normal record — never creates separate record types
- **`_ring_registry`** is a module-level singleton, reset on each new `TransactionGenerator()` via `reset_ring_registry()` — ensures isolated runs in the same process

**Banking fraud types (25):**
`ENGENHARIA_SOCIAL`, `PIX_GOLPE`, `CONTA_TOMADA`, `CARTAO_CLONADO`, `FRAUDE_APLICATIVO`, `BOLETO_FALSO`, `FALSA_CENTRAL_TELEFONICA`, `COMPRA_TESTE`, `MULA_FINANCEIRA`, `CARD_TESTING`, `MICRO_BURST_VELOCITY`, `WHATSAPP_CLONE`, `DISTRIBUTED_VELOCITY`, `PHISHING_BANCARIO`, `FRAUDE_QR_CODE`, `FRAUDE_DELIVERY_APP`, `MAO_FANTASMA`, `CREDENTIAL_STUFFING`, `EMPRESTIMO_FRAUDULENTO`, `GOLPE_INVESTIMENTO`, `SIM_SWAP`, `PIX_AGENDADO_FRAUDE`, `SEQUESTRO_RELAMPAGO`, `SYNTHETIC_IDENTITY`, `DEEP_FAKE_BIOMETRIA`

### `RideGenerator`

Spatial computation uses Haversine distance (great-circle). Surge pricing is a function of time-of-day and weather. Fare formula: `base_fare + (distance × per_km_rate) + (duration × per_min_rate)`.

**Ride-share fraud types (11):**
`GHOST_RIDE`, `GPS_SPOOFING`, `SURGE_ABUSE`, `MULTI_ACCOUNT_DRIVER`, `PROMO_ABUSE`, `RATING_FRAUD`, `SPLIT_FARE_FRAUD`, `REFUND_ABUSE`, `PAYMENT_CHARGEBACK`, `DESTINATION_DISPARITY`, `ACCOUNT_TAKEOVER_RIDE`

### `CustomerGenerator` / `DeviceGenerator` / `DriverGenerator`

Standard entity generators using Faker (pt-BR locale). CPF is always valid (mod-11 algorithm).

---

## 7. Behavioral Profiles

Profiles make generated data statistically coherent — customers behave consistently across all records.

**Transaction profiles** (`profiles/behavioral.py`): `young_digital`, `business_owner`, `traditional_elderly`, `middle_class`, `high_income`, `low_income`, `corporate`

**Ride profiles** (`profiles/ride_behavioral.py`): `frequent_commuter`, `occasional_user`, `business_traveller`, `night_owl`, `budget_conscious`, `premium_rider`, `tourist`

Profile assignment is **sticky** — fixed at customer creation time, never changed.

---

## 8. Enricher Pipeline

The enricher pipeline applies 8 sequential enrichment stages to each transaction record. Each enricher implements `EnricherProtocol(Protocol)` and mutates `tx` in-place via a shared `GeneratorBag`.

```
generate_with_pipeline()
    │
    └─► Raw transaction dict
          │
          ├─ 01 TemporalEnricher   — unusual_time, time_anomaly flag
          ├─ 02 GeoEnricher        — IBGE lat/lon, municipio_nome, Censo 2022 weights
          ├─ 03 FraudEnricher      — fraud-pattern field overrides, customer_state-aware location anomaly
          ├─ 04 PIXEnricher        — 12 BACEN fields: end_to_end_id, ispb, pacs.008
          ├─ 05 DeviceEnricher     — device_age_days, emulator_detected, vpn_active
          ├─ 06 SessionEnricher    — velocity windows (1h/6h/24h/7d/30d), new_beneficiary
          ├─ 07 RiskEnricher       — fraud_risk_score (17 signals, 4 rules), ring assignment
          └─ 08 BiometricEnricher  — typing_speed_avg_ms, touch_pressure_avg, scroll behavior
                │
                └─► Enriched transaction dict (114+ fields)
                    is_fraud · fraud_type · fraud_risk_score · fraud_signals[]
```

### Enricher Details

| # | Enricher | Key fields | Notes |
|---|----------|-----------|-------|
| 01 | `TemporalEnricher` | `unusual_time`, `time_anomaly` | BCB 2024 trimodal hourly distribution |
| 02 | `GeoEnricher` | `geolocation_lat/lon`, `codigo_ibge_municipio`; Pro+: `distance_from_home_km` | Censo 2022 weights |
| 03 | `FraudEnricher` | Pattern field overrides, location anomaly | Uses `tx["customer_state"]` (fixed v4.18) |
| 04 | `PIXEnricher` | `end_to_end_id`, `ispb_pagador/recebedor`, `cpf_hash`, `pacs_status` | 12 BACEN fields |
| 05 | `DeviceEnricher` | `device_age_days`, `emulator_detected`, `vpn_active`, `ip_type` | |
| 06 | `SessionEnricher` | `velocity_*`, `accumulated_amount_*`, `new_merchant/beneficiary` | Baselines: canonical in `session.py` (BCB 2024) |
| 07 | `RiskEnricher` | `fraud_risk_score`, `fraud_signals`, `fraud_ring_id`, `ring_role` | 17 signals + 4 correlation rules |
| 08 | `BiometricEnricher` | `typing_speed_avg_ms`, `touch_pressure_avg`, `scroll_before_confirm` | |

### Velocity Baselines — Single Source of Truth

Defined only in `src/fraud_generator/enrichers/session.py` (`_PROFILE_VELOCITY_BASELINE`, calibrated BCB 2024). `transaction.py` imports from there. Duplicate definitions with divergent values were removed in v4.18.

### Pipeline Factory

```python
from fraud_generator.enrichers.pipeline_factory import get_default_pipeline
pipeline = get_default_pipeline()  # 8 enricher instances in canonical order
```

---

## 9. ML Quality Layer

Introduced in v4.18.0. Measures data fidelity using an adversarial LightGBM classifier.

```
src/fraud_generator/ml/
├── features.py    — extract_features(records) → 31-feature DataFrame
├── trainer.py     — train binary + 25 OvR per-type LightGBM classifiers
└── evaluator.py   — evaluate_batch(records, registry) → quality report dict
```

### How It Works

1. `extract_features()` extracts 31 numerical features per record
2. `trainer.py` trains a binary `is_fraud` classifier and 25 per-type OvR classifiers, saved to `models/final/`
3. `evaluate_batch()` runs the trained models and returns:

```python
{
  "overall": {
    "auc_roc": 0.9347, "auc_pr": 0.8812,
    "n_total": 250000, "n_fraud": 7500, "fraud_rate": 0.03,
  },
  "per_type": {
    "CONTA_TOMADA": {"auc_roc": 0.961, "n_examples": 1800, "flag": "healthy_high_signal"},
    "PIX_FRAUDE":   {"auc_roc": 0.999, "n_examples": 2100, "flag": "too_easy"},
  },
  "feature_importance": {"fraud_score": 0.38, "emulator_detected": 0.10, ...},
  "quality_flags": [{"fraud_type": "PIX_FRAUDE", "flag": "too_easy", "recommendation": "..."}],
}
```

### Quality Grade

Grades range from A+ (excellent) to F (failed), computed from effective AUC-ROC
with penalties for over-deterministic (`too_easy`) and statistically insufficient
(`too_hard`) fraud types.

### Per-Type Flags

| Flag | Condition | Meaning |
|---|---|---|
| `too_easy` | AUC > 0.99 | Over-deterministic signals — model memorises |
| `too_hard` | AUC < 0.70 | Insufficient signal or too few examples |
| `healthy_high_signal` | 0.85–0.99 | Expected for CONTA_TOMADA, CREDENTIAL_STUFFING |
| `healthy_low_signal` | 0.70–0.85 | Expected for ENGENHARIA_SOCIAL, WHATSAPP_CLONE |

### Offline Training CLI

```bash
python tools/train_ml.py \
  --input ./data/*.jsonl \
  --model-dir ./models \
  --version v4
# Produces: models/final/fraud_detector_v4.lgb + train_metrics_v4.json
```

### Integration with Hosted API

When used via [synthfin.com.br](https://synthfin.com.br), `evaluate_batch()` runs automatically after every batch job:
- Result stored in `analysis_reports` DB table
- HTML quality report rendered via Jinja2 and uploaded to MinIO
- Emailed to the user with grade, AUC-ROC, and download links
- Exposed on `GET /v2/jobs/{id}` via `quality_auc_roc`, `quality_report_url`, `quality_analysis_id`

---

## 10. Exporters

All exporters implement `ExporterProtocol(ABC)`:

```python
class ExporterProtocol(ABC):
    format_name: str
    extension:   str
    def export_batch(self, records: Iterable[dict], output_path: str, **kwargs) -> ExportStats
    def export_stream(self, data_iterator, output_path: str, batch_size: int) -> int
```

### Available Exporters

| Class | Format | Notes |
|---|---|---|
| `JSONExporter` | JSONL | Line-by-line; O(1) memory |
| `JSONArrayExporter` | JSON array | `export_stream` truly streaming since v4.18; append warns at >100MB |
| `CSVExporter` | CSV | Streaming via `csv.DictWriter` |
| `TSVExporter` | TSV | Subclass of CSVExporter |
| `ParquetExporter` | Parquet | Requires `pyarrow`; append warns at >100MB since v4.18 |
| `ParquetPartitionedExporter` | Parquet | Partition by state / date |
| `ArrowIPCExporter` | Arrow IPC | Binary columnar streaming format |
| `DatabaseExporter` | SQLite / PG | Batched INSERT via SQLAlchemy |
| `MinIOExporter` | Any → S3 | Wraps other exporters + boto3 upload |

---

## 11. Connections (Streaming)

All connections implement `ConnectionProtocol(ABC)`:

| Class | Target | Notes |
|---|---|---|
| `StdoutConnection` | stdout | JSON-serialised lines |
| `KafkaConnection` | Apache Kafka | Requires `kafka-python` |
| `WebhookConnection` | HTTP endpoint | POST with JSON body |
| `RedisStreamConnection` | Redis Stream | `XADD` to Redis stream key; used by hosted API streaming sessions |

---

## 12. Schema System

```
schemas/banking_full.json
  └─► SchemaParser  (validates structure, resolves field catalog)
        └─► AISchemaCorrector  (heuristic repair + optional LLM correction)
              └─► SchemaEngine  (orchestrates generators)
                    └─► FieldMapper  (resolves namespace.field references)
```

Supported reference types:

```jsonc
{
  "my_amount":  "transaction.amount",   // namespace.field
  "company_id": "static:ACME-CORP",     // static literal
  "full_name":  "faker:name",           // Faker method
}
```

---

## 13. Configuration Layer

Convention: each module exports `*_LIST`, `*_WEIGHTS`, and `get_*()` helpers.

| Module | Content |
|---|---|
| `banks.py` | Brazilian bank codes + names (BACEN) |
| `merchants.py` | Merchant names, MCC codes |
| `geography.py` | 27 states, major cities, coordinates, POIs |
| `transactions.py` | Transaction types, channels, fraud type list |
| `rideshare.py` | Apps, vehicle categories, surge rules, fare tables |
| `devices.py` | Device types, OS versions, fingerprint components |
| `fraud_patterns.py` | Fraud pattern definitions and field-level injection rules |
| `seasonality.py` | Hourly/daily/annual weights (BCB 2024, Python 3.9+ compatible) |
| `calibration_loader.py` | Runtime override loader for RAG-calibrated fraud prevalences |

---

## 14. Data Models & Indexes

### Index Types (`utils/streaming.py`)

Lightweight `NamedTuple` structures — safe for cross-process serialization:

```python
CustomerIndex(customer_id, state, profile, lat, lon, ...)
DeviceIndex(device_id, customer_id, trusted, ...)
DriverIndex(driver_id, state, lat, lon, apps, ...)
```

### `CustomerSessionState`

Maintains per-customer mutable state across multiple transaction records in the same worker run (last transaction timestamp, fraud velocity counter, merchant history).

---

## 15. Utilities

### `utils/watermark.py`

UUID5-based transaction ID fingerprinting for data provenance:

```python
# Deterministic — same inputs always produce same ID
make_transaction_id(tx_id, customer_id, timestamp) -> str
# e.g. "TXN_DCB02BE69A265CDE9933"

# Verify a record was generated by synthfin-data
is_synthfin_id(transaction_id, tx_id, customer_id, timestamp) -> bool
```

The `SYNTHFIN_NS` UUID namespace is public by design — anyone can verify data origin. Used in the pipeline path since v4.18 (previously only in the legacy path).

### `utils/weight_cache.py`

Eliminates repeated weight normalisation overhead. Weights are pre-normalised to `sum=1.0` as numpy arrays. Module-level singletons.

```python
@dataclass
class WeightCache:
    choices: np.ndarray
    weights: np.ndarray
    def sample(self, n=1) -> Any
```

### `utils/compression.py`

Strategy pattern: `GzipCompressor | ZstdCompressor | SnappyCompressor | NoOpCompressor`

### `utils/redis_cache.py`

Optional Redis-backed index persistence. Allows sharing pre-built customer/device indexes across multiple generator processes or restarts.

---

## 16. Validators

### `validators/cpf.py`

Complete Brazilian CPF implementation. CPFs are always validated at generation time using the standard mod-11 double-digit algorithm.

```python
generate_valid_cpf(formatted=False) -> str
validate_cpf(cpf: str) -> bool
generate_cpf_from_state(state_code) -> str  # 3rd digit encodes region
```

---

## 17. Licensing System

HMAC-signed licenses with plan tiers for the hosted API. The open-source CLI has no
license restrictions. See [synthfin.com.br](https://synthfin.com.br) for current plan details.

---

## 18. Design Decisions

### SOLID Modular > DDD

The application is a generation pipeline, not a domain with rich business rules. SOLID Modular gives the same extensibility as DDD/Clean Architecture with far less ceremony.

### CPU-bound vs I/O-bound Parallelism

Batch generation is CPU-bound → `ProcessPoolExecutor`. MinIO JSONL/CSV upload is I/O-bound → `ThreadPoolExecutor`. Workers are top-level module-level functions for cross-process serialization safety.

### Deterministic Seed Per Worker

```
worker_seed = derive(base_seed, batch_id)   # deterministic, collision-free per batch
```

Same base seed + same count always produces the same dataset, regardless of worker count or execution order.

### Profile Assignment is Sticky

A customer's behavioural profile is assigned once at creation time and fixed for all downstream records. This ensures statistical coherence.

### Fraud Injection via Field Combinations

Fraud overwrites specific fields in an otherwise normal record (inflated amount, changed device, foreign IP). This mirrors real fraud — fraudsters don't create obviously labelled records.

### Ring Registry Reset Per Generator Instance

`_ring_registry` is a module-level singleton. Since v4.18, `TransactionGenerator.__init__()` calls `reset_ring_registry()` to ensure each new instance starts with clean state, preventing contamination between runs in the same process.

### Velocity Baselines — Single Source of Truth

Defined only in `session.py` (calibrated BCB 2024). `transaction.py` imports from there. Duplicate definitions with divergent values were removed in v4.18.

---

## 19. Data Flow Diagrams

### Batch Mode — Full Flow

```
generate.py
    │
    └─► BatchRunner.run(args)
             │
             ├─[Phase 1]─► CustomerGenerator × N + DeviceGenerator × N
             │              ──► customers.jsonl, devices.jsonl
             │
             ├─[Phase 2]─► ProcessPoolExecutor [×W workers]
             │              │  worker_generate_batch()
             │              │    ├─ generate_with_pipeline() per tx
             │              │    │    └─► 8 enrichers
             │              │    └─► write 1000-line buffered JSONL
             │              ──► transactions_00000.jsonl … transactions_NNNNN.jsonl
             │
             ├─[Phase 3]─► DriverGenerator × M ──► drivers.jsonl
             │
             └─[Phase 4]─► ProcessPoolExecutor [×W workers]
                            ──► rides_00000.jsonl … rides_NNNNN.jsonl
```

### Hosted API — Post-Job Quality Flow

```
Worker completes job
    │
    ├─► Upload dataset to MinIO (presigned URL, 48h TTL)
    │
    └─► _run_post_job_quality()
              │
              ├─ _load_jsonl(file_path)
              ├─ run_analysis(records) → QualityReport (grade, AUC-ROC, per_type, flags)
              ├─ render_html(report, job_id) via Jinja2
              ├─ _upload_report_to_minio(html) → presigned URL (48h)
              └─ _save_analysis_to_db()
                        │
                        └─► _send_job_email()
                              ├─ Dataset download link
                              ├─ Quality grade + AUC-ROC
                              └─ HTML report link
```

### Streaming Mode — Full Flow

```
stream.py --target redis-stream --rate 50
    │
    ├─► RedisStreamConnection.connect()
    └─► loop (until SIGINT/SIGTERM)
             ├─ generate_with_pipeline() per event
             └─► XADD stream:{stream_id} {data: ...}
```

---

## 20. Performance Characteristics

| Metric | Value | Conditions |
|---|---|---|
| Batch throughput | ~58,000 rec/s | 8 workers, JSONL, 18-core host |
| Schema mode | ~7,800 rec/s | JSONL, single-process |
| Memory per worker | ~120–180 MB | 128 MB target file, index in-memory |
| MinIO upload (JSONL) | network-bound | ThreadPoolExecutor |
| MinIO upload (Parquet) | CPU+network | ProcessPoolExecutor |

---

## 21. Extension Guide

### Adding a new output format

1. Create `src/fraud_generator/exporters/my_format_exporter.py`
2. Implement `ExporterProtocol` with `format_name`, `extension`, `export_batch()`, `export_stream()`
3. Register in `src/fraud_generator/exporters/__init__.py`

### Adding a new streaming target

1. Create `src/fraud_generator/connections/my_connection.py`
2. Implement `ConnectionProtocol` with `connect()`, `send()`, `close()`
3. Register in `src/fraud_generator/connections/__init__.py`

### Adding a new fraud type

1. Add to `FRAUD_TYPES_LIST` and `FRAUD_TYPES_WEIGHTS` in `config/transactions.py`
2. Add field injection rules to `config/fraud_patterns.py`
3. Add OvR model entry in `ml/trainer.py` if per-type ML validation is needed

### Adding a new enricher

1. Create `src/fraud_generator/enrichers/my_enricher.py`
2. Implement `EnricherProtocol` with `enrich(tx: dict, bag: GeneratorBag) -> None`
3. Register in `enrichers/pipeline_factory.py`

---

## 22. Known Gaps & Limitations

| ID | Category | Issue | Severity | Status |
|---|---|---|---|---|
| P1 | Performance | Fraud patterns lack sequential/velocity checks | Medium | Open |
| P2 | Performance | `random.choices()` per-record overhead | Low | Mitigated (WeightCache) |
| P3 | Performance | Parquet append reads full file into memory | High | Partial — warning added v4.18; streaming fix pending |
| T1 | Testing | No tests for Connections (Kafka, Webhook, Stdout) | Medium | Open |
| T2 | Testing | No tests for Config modules | Low | Open |
| D1 | Data | CSV uses `.` separator, Parquet uses `_` for nested fields | Medium | Open |
| D3 | Data | Schema mode does not validate output against input schema | Low | Open |

**Fixed in v4.18:**
- ~~S2: Container runs as root~~ — non-root `appuser` added
- ~~D2: Ring registry singleton not resettable~~ — `clear()` + `reset_ring_registry()` added
- ~~customer_state not propagated to tx dict~~ — location anomaly now uses real state
- ~~transaction_id format inconsistent between pipeline/legacy~~ — UUID5 watermark restored
- ~~Duplicate velocity baselines~~ — consolidated in `session.py`
- ~~JSONArrayExporter.export_stream OOM~~ — true streaming implemented
- ~~Python 3.9 incompatibility in seasonality.py~~ — `date | None` → `Optional[date]`

---

## 23. Environment & Dependencies

### Python Version

Python 3.9+ required (3.10+ recommended). Tested on Python 3.10 / 3.11 / 3.12.

### Core Dependencies

| Package | Purpose |
|---|---|
| `Faker` | Names, addresses, phone numbers (pt-BR locale) |
| `pandas` | DataFrame manipulation |
| `pyarrow` | Parquet + Arrow IPC |
| `boto3` | MinIO / S3 upload |
| `numpy` | WeightCache vectorised sampling |
| `lightgbm` | ML quality validation classifiers |
| `scikit-learn` | AUC metrics for quality evaluation |

### Optional Dependencies

| Package | Purpose |
|---|---|
| `zstandard` | zstd compression |
| `python-snappy` | snappy compression |
| `kafka-python` | Kafka streaming |
| `redis` | Index caching + streaming |
| `jinja2` | HTML quality report rendering |
| `openai` / `anthropic` | AI schema correction |

### Environment Variables

| Variable | Purpose |
|---|---|
| `MINIO_ACCESS_KEY` | MinIO/S3 access key |
| `MINIO_SECRET_KEY` | MinIO/S3 secret key |
| `MINIO_ENDPOINT` | MinIO endpoint URL |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker list |
| `REDIS_URL` | Redis URL for streaming / index caching |
| `OPENAI_API_KEY` | OpenAI key for AI schema correction |
| `ANTHROPIC_API_KEY` | Anthropic key for AI schema correction |

---

## 24. SynthFin Ecosystem

**synthfin-data** is the core engine of a larger hosted platform available at
[synthfin.com.br](https://synthfin.com.br).

| Component | Role |
|---|---|
| **synthfin-data** (this repo) | Core generation engine + ML quality layer |
| **Hosted API** | REST API, job queue, storage, billing |
| **Dashboard** | Job management, quality reports, usage |

The hosted platform runs the same generation pipeline as this open-source library,
with added job orchestration, ML quality analysis, MinIO storage, and email delivery.

For API access during the beta phase, contact [devabnerfonseca@gmail.com](mailto:devabnerfonseca@gmail.com).

---

*synthfin-data v4.18.0 — 25 banking + 11 ride-share fraud patterns, LightGBM ML quality layer, AUC-ROC 0.9991*
