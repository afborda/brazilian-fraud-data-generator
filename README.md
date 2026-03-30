# synthfin-data

<p align="center">
  <img src="docs/assets/Hero%20do%20README.png" alt="synthfin-data — synthetic fraud data for Brazilian banking, PIX, ride-share, fraud signals and exports." width="100%" />
</p>

<p align="center">
  <a href="VERSION"><img src="https://img.shields.io/badge/version-4.9.1-0F766E" alt="Version 4.9.1" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Custom%20Non--Commercial-DC2626" alt="Custom Non-Commercial License" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-1D4ED8" alt="Python 3.10 or newer" />
  <img src="https://img.shields.io/badge/domains-banking%20%7C%20ride--share-0F172A" alt="Banking and ride-share domains" />
  <img src="https://img.shields.io/badge/streaming-kafka%20%7C%20webhook%20%7C%20stdout-7C3AED" alt="Kafka, webhook and stdout streaming" />
</p>

<p align="center">
  <strong>Synthetic fraud data for Brazilian banking, PIX and ride-share systems.</strong><br />
  Generate realistic labeled datasets for fraud detection models, QA pipelines, platform testing, red-team simulations and data engineering workflows.
</p>

<p align="center">
  <a href="docs/README.md">Documentation</a>
  ·
  <a href="docs/README.pt-BR.md">Portuguese Docs</a>
  ·
  <a href="ARCHITECTURE.md">Architecture</a>
  ·
  <a href="docs/CHANGELOG.md">Changelog</a>
  ·
  <a href="https://hub.docker.com/r/afborda/synthfin-data">Docker Hub</a>
</p>

## Why This Project

**synthfin-data** is built for teams that need a realistic Brazilian synthetic fraud dataset instead of a toy transaction generator. It covers PIX-heavy banking behavior, Brazilian geography, ride-share fraud scenarios, deterministic seeds, schema-driven output, and a hosted API at [synthfin.com.br](https://synthfin.com.br).

<table>
  <tr>
    <td width="33%"><strong>Brazil-first realism</strong><br />Valid CPF, real banks, PIX BACEN fields, behavioral profiles, seasonality, and Brazilian city or state context.</td>
    <td width="33%"><strong>Ready for pipelines</strong><br />Batch files, streaming events, schema mode, database export, Kafka or webhook delivery, and reproducible seeds.</td>
    <td width="33%"><strong>Fraud-focused labels</strong><br />25 banking fraud patterns (RAG-calibrated), 11 ride-share fraud types, 17 risk signals, and 4 correlation rules in the fraud signal pipeline.</td>
  </tr>
</table>

## Open Source and Hosted API

The entire generator codebase is in this repository under a **custom non-commercial license**. You may use it freely for **personal study, academic research, and educational purposes**. Commercial use by companies or individuals for any revenue-generating purpose requires a paid license — see [LICENSE](LICENSE) for details.

Running from source has **no technical limits** — you get every format, every target, every generator, and unlimited scale.

A hosted cloud API is available at [synthfin.com.br](https://synthfin.com.br) for teams that want managed generation without running their own infrastructure. The platform includes:

- **REST API** at [api.synthfin.com.br](https://api.synthfin.com.br) — 15 endpoints (generate, jobs, download, usage, billing)
- **Dashboard** at [app.synthfin.com.br](https://app.synthfin.com.br) — real-time job management, usage monitoring, billing
- **Plans** from $9/month (Starter) to $99/month (Team), with Enterprise on request

See [docs/analysis/ANALISE_ECOSSISTEMA_SYNTHFIN.md](docs/analysis/ANALISE_ECOSSISTEMA_SYNTHFIN.md) for a full ecosystem overview.

### What you get from the open-source library

| Category | Included |
|---|---|
| Generators | Banking transactions, ride-share rides, or both (`--type all`) |
| Banking fraud | 25 patterns: `ENGENHARIA_SOCIAL`, `PIX_GOLPE`, `CONTA_TOMADA`, `CARTAO_CLONADO`, `FRAUDE_APLICATIVO`, `BOLETO_FALSO`, `FALSA_CENTRAL_TELEFONICA`, `COMPRA_TESTE`, `MULA_FINANCEIRA`, `CARD_TESTING`, `MICRO_BURST_VELOCITY`, `WHATSAPP_CLONE`, `DISTRIBUTED_VELOCITY`, `PHISHING_BANCARIO`, `FRAUDE_QR_CODE`, `FRAUDE_DELIVERY_APP`, `MAO_FANTASMA`, `CREDENTIAL_STUFFING`, `EMPRESTIMO_FRAUDULENTO`, `GOLPE_INVESTIMENTO`, `SIM_SWAP`, `PIX_AGENDADO_FRAUDE`, `SEQUESTRO_RELAMPAGO`, `SYNTHETIC_IDENTITY`, `DEEP_FAKE_BIOMETRIA` |
| Ride-share fraud | 11 types: `GHOST_RIDE`, `GPS_SPOOFING`, `SURGE_ABUSE`, `MULTI_ACCOUNT_DRIVER`, `PROMO_ABUSE`, `RATING_FRAUD`, `SPLIT_FARE_FRAUD`, `REFUND_ABUSE`, `PAYMENT_CHARGEBACK`, `DESTINATION_DISPARITY`, `ACCOUNT_TAKEOVER_RIDE` |
| Fraud scoring | `fraud_risk_score` 0–100 from 17 signals and 4 correlation rules via 8-stage enricher pipeline |
| Behavioral profiles | 7 transaction profiles + 7 ride profiles; sticky per customer |
| Reproducibility | Deterministic seeds, custom date ranges, fixed customer pool |
| Output formats | JSONL, JSON array, CSV, TSV, Parquet, Arrow IPC, database via SQLAlchemy |
| Compression | JSONL: gzip / zstd / snappy; Parquet: snappy / zstd / gzip / brotli |
| Streaming | stdout, Kafka, webhook — see [Streaming](#streaming) below |
| Object storage | MinIO and S3-compatible upload |
| Schema mode | Declarative JSON schemas with optional AI field correction |
| CLI | ~30 flags; full parallel worker control |
| Validation | `validate_realism.py`, `check_schema.py`, pytest suite (220 test functions) |
| Docker | Official image on Docker Hub |
| Scale | Hardware-only limit |
| Cost | Free for study and research; [commercial license](https://synthfin.com.br) required for business use |

## Start Fast

```bash
pip install -r requirements.txt
```

### Batch generation

```bash
# 1 GB of banking transactions at 0.8% fraud rate (default)
python generate.py --size 1GB --output ./data

# Ride-share data
python generate.py --size 500MB --type rides --output ./data

# Both banking and rides in one run
python generate.py --size 1GB --type all --output ./data

# Reproducible dataset: fixed seed, 15% fraud, 8 workers
python generate.py --size 2GB --fraud-rate 0.15 --seed 42 --workers 8 --output ./data

# Custom date range
python generate.py --size 1GB --start-date 2024-01-01 --end-date 2024-12-31 --output ./data

# Export as Parquet, CSV, or Arrow
python generate.py --size 1GB --format parquet --compression zstd --output ./data
python generate.py --size 1GB --format csv --output ./data
python generate.py --size 1GB --format arrow --output ./data

# Upload directly to MinIO or S3
python generate.py --size 5GB --output minio://fraud-data/raw --minio-endpoint http://minio:9000

# Schema-driven generation (custom output fields)
python generate.py --schema schemas/banking_full.json --count 50000 --output ./data

# Validate the output realism
python validate_realism.py --input data/transactions_*.jsonl
```

### Streaming

Streaming mode generates events **continuously in real time** instead of writing a batch file. It is the right tool when you need live traffic rather than a static dataset.

**How it works:**

```
┌─────────────────────────────────────────────────────┐
│  Generator workers (--workers N)                    │
│  Each worker produces events independently,         │
│  bypassing the GIL via multiprocessing              │
└───────────────┬─────────────────────────────────────┘
                │  shared queue (--queue-size)
                ▼
┌─────────────────────────────────────────────────────┐
│  Rate controller (token bucket)                     │
│  Drains the queue at --rate events/second           │
│  Bursts are absorbed; long gaps are filled          │
└───────────────┬─────────────────────────────────────┘
                │
        ┌───────┼───────────┐
        ▼       ▼           ▼
     stdout   Kafka      Webhook
  (terminal) (topics)  (HTTP POST)
```

**Two send modes:**

| Mode | Flag | Behaviour |
|---|---|---|
| Synchronous (default) | — | Each event is sent before the next is generated. Predictable pacing, easy to debug |
| Async | `--async` | A thread pool sends up to `--async-concurrency` events in parallel. Use for burst or high-throughput scenarios |

**Common use cases:**

| Use case | Target | Example |
|---|---|---|
| Debug event shape locally | stdout | `--target stdout --pretty` |
| Test Kafka consumer lag | kafka | `--target kafka --rate 500` |
| Load-test an ML scoring endpoint | webhook | `--target webhook --rate 100 --async` |
| Validate streaming pipeline end-to-end | webhook | `--type all --rate 50 --max-events 100000` |
| Simulate sustained PIX traffic | stdout / kafka | `--type transactions --rate 200 --seed 42` |

```bash
pip install -r requirements-streaming.txt

# Print events to terminal at 5 events/sec
python stream.py --target stdout --rate 5 --pretty

# Stream to Kafka at 100 events/sec
python stream.py --target kafka --kafka-server localhost:9092 --kafka-topic transactions --rate 100

# Stream ride events to a REST endpoint
python stream.py --target webhook --type rides --webhook-url http://api:8080/ingest --rate 50

# Burst test: async sends, up to 50 concurrent HTTP requests
python stream.py --target webhook --webhook-url http://api:8080/ingest --rate 200 --async --async-concurrency 50

# Stop after 10,000 events
python stream.py --target stdout --rate 20 --max-events 10000
```

### Docker

```bash
docker run --rm -v $(pwd)/output:/output \
  afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output

# Stream events via Docker
docker run --rm \
  afborda/synthfin-data:latest \
  stream.py --target stdout --rate 10
```

### Schema mode

```bash
# Bundled schemas ship in schemas/
python generate.py --schema schemas/banking_full.json --count 5000 --output ./data
python generate.py --schema schemas/banking_minimal.json --count 5000 --output ./data
python generate.py --schema schemas/rideshare_full.json --count 5000 --output ./data

# Bring your own schema
python generate.py --schema my_schema.json --count 50000 --output ./data
```

<p align="center">
  <img src="docs/assets/Workflow%20-%20Como%20funciona.png" alt="Workflow showing configuration, generation, fraud modeling and delivery pipelines." width="100%" />
</p>

## CLI Reference

<details>
<summary><strong>generate.py — all flags</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--type` | `transactions` | Data type: `transactions`, `rides`, or `all` |
| `--size` | `1GB` | Target output size: `1GB`, `500MB`, `10GB`, etc. |
| `--output` | `./output` | Output directory or `minio://bucket/prefix` |
| `--format` | `jsonl` | `jsonl`, `json`, `csv`, `tsv`, `parquet`, `parquet_partitioned`, `arrow`, `ipc`, `db` |
| `--jsonl-compress` | `none` | JSONL inline compression: `none`, `gzip`, `zstd`, `snappy` |
| `--fraud-rate` | `0.008` | Fraction of records flagged as fraud (0.0–1.0) |
| `--workers` | CPU count | Parallel worker processes |
| `--seed` | none | Random seed for fully reproducible datasets |
| `--parallel-mode` | `auto` | Execution mode: `auto`, `thread`, `process` |
| `--customers` | auto | Fixed customer pool size |
| `--start-date` | 1 year ago | Timestamp range start `YYYY-MM-DD` |
| `--end-date` | today | Timestamp range end `YYYY-MM-DD` |
| `--no-profiles` | off | Disable behavioral profiles (uniform random) |
| `--compression` | `zstd` | Parquet compression: `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| `--schema` | none | Declarative JSON schema file (schema mode) |
| `--count` | `1000` | Record count in schema mode |
| `--schema-ai-provider` | `openai` | AI schema correction: `openai`, `anthropic`, `none` |
| `--db-url` | none | SQLAlchemy database URL for `db` format |
| `--db-table` | `transactions` | Table name for `db` format |
| `--redis-url` | none | Redis URL for index caching |
| `--minio-endpoint` | env | MinIO/S3 endpoint URL |
| `--minio-access-key` | env | MinIO access key (or `MINIO_ROOT_USER` env) |
| `--minio-secret-key` | env | MinIO secret key (or `MINIO_ROOT_PASSWORD` env) |
| `--no-date-partition` | off | Disable `YYYY/MM/DD` partitioning in MinIO |

</details>

<details>
<summary><strong>stream.py — all flags</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--target` | required | Output target: `kafka`, `webhook`, or `stdout` |
| `--type` | `transactions` | Data type: `transactions` or `rides` |
| `--rate` | `10` | Events per second |
| `--max-events` | infinite | Stop after N events |
| `--kafka-server` | `localhost:9092` | Kafka bootstrap server |
| `--kafka-topic` | `transactions` | Kafka topic name |
| `--webhook-url` | none | HTTP endpoint URL for webhook target |
| `--webhook-method` | `POST` | HTTP method: `POST`, `PUT`, `PATCH` |
| `--fraud-rate` | `0.008` | Fraction of events flagged as fraud (0.0–1.0) |
| `--customers` | `1000` | Customer pool size |
| `--seed` | none | Random seed |
| `--workers` | `1` | Parallel generator processes |
| `--queue-size` | `10000` | Event buffer between workers and sender |
| `--async` | off | Enable async send via background threads |
| `--async-concurrency` | `100` | Max concurrent async sends |
| `--pretty` | off | Pretty-print JSON (stdout only) |
| `--quiet` | off | Suppress progress output |
| `--redis-url` | none | Redis URL for caching base data |
| `--redis-prefix` | `fraudgen` | Redis key prefix |

</details>

## Output Schema

Running `python generate.py --size 1GB --output ./data` creates the following files:

```
./data/
├── customers.jsonl           ← one record per simulated customer
├── devices.jsonl             ← one or more devices per customer
└── transactions_00000.jsonl  ← transactions in batches (one file per worker)
```

For `--type rides`:

```
./data/
├── customers.jsonl
├── drivers.jsonl
└── rides_00000.jsonl
```

For `--type all`:

```
./data/
├── customers.jsonl
├── devices.jsonl
├── drivers.jsonl
├── transactions_00000.jsonl
└── rides_00000.jsonl
```

Every file is JSONL — one JSON object per line. The examples below are real records from a generated dataset.

### Banking transaction — credit card (legitimate)

```json
{
  "transaction_id": "TXN_1773495125210_0000_000000",
  "customer_id": "CUST_000000002438",
  "session_id": "SESS_1773495125210_0000_000000",
  "device_id": "DEV_000000005239",
  "timestamp": "2025-04-28T19:15:14.146316",
  "type": "CREDIT_CARD",
  "amount": 127.82,
  "currency": "BRL",
  "channel": "MOBILE_APP",
  "ip_address": "190.6.70.57",
  "geolocation_lat": -10.123402,
  "geolocation_lon": -67.645855,
  "merchant_id": "MERCH_096662",
  "merchant_name": "Cosi",
  "merchant_category": "Restaurants",
  "mcc_code": "5812",
  "mcc_risk_level": "low",
  "cliente_perfil": "young_digital",
  "classe_social": "C1",
  "card_number_hash": "d63b69225a3a065a",
  "card_brand": "MASTERCARD",
  "card_type": "CREDIT",
  "installments": 4,
  "card_entry": "CONTACTLESS",
  "cvv_validated": true,
  "auth_3ds": true,
  "velocity_transactions_24h": 1,
  "accumulated_amount_24h": 127.82,
  "new_beneficiary": true,
  "customer_velocity_z_score": -2.25,
  "unusual_time": false,
  "status": "APPROVED",
  "fraud_score": 11,
  "is_fraud": false,
  "sim_swap_recent": false,
  "ip_location_matches_account": true,
  "hours_inactive": 0,
  "new_merchant": true,
  "fraud_risk_score": 0,
  "is_impossible_travel": false,
  "distance_from_last_km": 0.0
}
```

<details>
<summary><strong>PIX fraud transaction — BACEN fields, fraud_type, fraud_signals</strong></summary>

```json
{
  "transaction_id": "TXN_1773495125210_0000_000001",
  "customer_id": "CUST_000000001711",
  "session_id": "SESS_1773495125210_0000_000001",
  "device_id": "DEV_000000003680",
  "timestamp": "2025-11-05T23:45:48.844962",
  "type": "PIX",
  "amount": 1689.28,
  "currency": "BRL",
  "channel": "PIX",
  "ip_address": "138.173.228.22",
  "geolocation_lat": -15.808824,
  "geolocation_lon": -55.865657,
  "merchant_id": "MERCH_066504",
  "merchant_name": "Makro",
  "merchant_category": "Supermarkets",
  "mcc_code": "5411",
  "mcc_risk_level": "low",
  "cliente_perfil": "family_provider",
  "pix_key_type": "CPF",
  "pix_key_destination": "d4acecf9ded200b9761356d6addee76f",
  "destination_bank": "290",
  "end_to_end_id": "E30723886202511052007B0471FE3",
  "ispb_pagador": "30723886",
  "ispb_recebedor": "90400888",
  "tipo_conta_pagador": "TRAN",
  "tipo_conta_recebedor": "CACC",
  "holder_type_recebedor": "CUSTOMER",
  "modalidade_iniciacao": "QRCODE_ESTATICO",
  "cpf_hash_pagador": "8ecde4c9e8f01f5a347b69ae826a2cdd238eb7edcdfe94c897abd5828eee31df",
  "cpf_hash_recebedor": "4b3536650b29ea5f445a470a203eee737b0cd677f8c41d599cb242cf376abbb2",
  "pacs_status": "ACSC",
  "is_devolucao": false,
  "new_beneficiary": true,
  "velocity_transactions_24h": 10,
  "accumulated_amount_24h": 11824.96,
  "unusual_time": false,
  "fraud_score": 89,
  "customer_velocity_z_score": 0.67,
  "status": "APPROVED",
  "is_fraud": true,
  "fraud_type": "PIX_GOLPE",
  "sim_swap_recent": false,
  "ip_location_matches_account": false,
  "hours_inactive": 0,
  "new_merchant": true,
  "fraud_risk_score": 43,
  "fraud_signals": ["active_call", "amount_spike"],
  "is_impossible_travel": false,
  "distance_from_last_km": 0.0
}
```

</details>

<details>
<summary><strong>Customer record</strong></summary>

```json
{
  "customer_id": "CUST_000000000001",
  "name": "Joaquim Câmara",
  "cpf": "321.819.601-94",
  "email": "gustavorocha@example.net",
  "phone": "71 1960-0133",
  "birth_date": "2003-10-25",
  "address": {
    "street": "Alameda de Novais, 78",
    "neighborhood": "Estrela",
    "city": "Pastor de da Mota",
    "state": "GO",
    "postal_code": "26542351"
  },
  "monthly_income": 2377.87,
  "profession": "Biotecnólogo",
  "account_created_at": "2021-04-19T14:20:37.497966",
  "account_type": "DIGITAL",
  "account_status": "ACTIVE",
  "credit_limit": 16304.06,
  "credit_score": 719,
  "risk_level": "HIGH",
  "bank_code": "341",
  "bank_name": "Itaú Unibanco",
  "branch": "0107",
  "account_number": "805667-2",
  "behavioral_profile": "subscription_heavy"
}
```

</details>

<details>
<summary><strong>Device record</strong></summary>

```json
{
  "device_id": "DEV_000000000001",
  "customer_id": "CUST_000000000001",
  "type": "SMARTPHONE",
  "manufacturer": "Realme",
  "model": "GT5 Pro",
  "operating_system": "Android 12",
  "fingerprint": "e5da6495f9b75f161af8ba0c7667be98",
  "first_use": "2024-12-06",
  "is_trusted": true,
  "is_rooted_jailbroken": false
}
```

</details>

<details>
<summary><strong>Ride record (--type rides)</strong></summary>

```json
{
  "ride_id": "RIDE_000000000000",
  "timestamp": "2025-08-01T09:08:47.107473",
  "app": "CABIFY",
  "category": "Lite",
  "driver_id": "DRV_0000000205",
  "passenger_id": "CUST_000000000913",
  "pickup_location": {
    "lat": -23.5558,
    "lon": -46.6696,
    "name": "Hospital das Clínicas",
    "poi_type": "HOSPITAL",
    "city": "Manaus",
    "state": "AM"
  },
  "dropoff_location": {
    "lat": -23.4356,
    "lon": -46.4731,
    "name": "Aeroporto de Guarulhos",
    "poi_type": "AIRPORT",
    "city": "Manaus",
    "state": "AM"
  },
  "request_datetime": "2025-08-01T09:08:47.107473",
  "accept_datetime": "2025-08-01T09:09:41.107473",
  "pickup_datetime": "2025-08-01T09:21:41.107473",
  "dropoff_datetime": "2025-08-01T11:33:41.107473",
  "distance_km": 33.75,
  "duration_minutes": 132,
  "wait_time_minutes": 12,
  "base_fare": 72.65,
  "surge_multiplier": 1.32,
  "final_fare": 95.9,
  "driver_pay": 74.8,
  "platform_fee": 21.1,
  "tip": 0.0,
  "payment_method": "CASH",
  "status": "COMPLETED",
  "driver_rating": 5,
  "passenger_rating": 5,
  "weather_condition": "CLEAR",
  "temperature": 21.8,
  "is_fraud": false
}
```

</details>

## What You Can Generate

| Area | What is available today |
|---|---|
| Banking | PIX, TED, DOC, boleto, withdrawals, POS and ecommerce flows, merchant context, device context, BACEN PIX fields, and valid CPF-linked customers |
| Ride-share | Uber, 99, Cabify, and inDrive style trips with drivers, passengers, surge pricing, weather impact, and geospatial distance logic |
| Fraud labels | 25 banking fraud patterns (RAG-calibrated) and 11 ride-share fraud types with configurable fraud rate |
| Fraud scoring | 17 fraud signals plus 4 rule correlations, producing `fraud_risk_score` from 0 to 100 |
| Temporal realism | Trimodal hourly peaks, weekday weighting, Black Friday, Christmas, 13th salary, and Carnaval seasonality |
| Validation | `validate_realism.py`, bundled schemas, deterministic seeds, and schema checks |
| Quality | v5 scorecard: realism 8.0/10, fraud/legit ratio 5.09× (BCB target 5–8×), 25 fraud types, 27 states, 117 columns, 0 always-null columns |

### Banking fraud patterns (25 total)

**BCB/Febraban-calibrated (9 patterns with RAG-validated prevalences):**  
`ENGENHARIA_SOCIAL`, `PIX_GOLPE`, `CONTA_TOMADA`, `CARTAO_CLONADO`, `MULA_FINANCEIRA`, `WHATSAPP_CLONE`, `MAO_FANTASMA`, `BOLETO_FALSO`, `SEQUESTRO_RELAMPAGO`

**Additional patterns (original defaults):**  
`FRAUDE_APLICATIVO`, `COMPRA_TESTE`, `CARD_TESTING`, `MICRO_BURST_VELOCITY`, `DISTRIBUTED_VELOCITY`, `SIM_SWAP`, `CREDENTIAL_STUFFING`, `SYNTHETIC_IDENTITY`

**New patterns (v4-beta — calibrated with MJSP/BCB/Febraban data):**  
`DEEP_FAKE_BIOMETRIA`, `FALSA_CENTRAL_TELEFONICA`, `PIX_AGENDADO_FRAUDE`, `EMPRESTIMO_FRAUDULENTO`, `FRAUDE_DELIVERY_APP`, `FRAUDE_QR_CODE`, `PHISHING_BANCARIO`, `GOLPE_INVESTIMENTO`

### Ride-share fraud types

`GHOST_RIDE`, `GPS_SPOOFING`, `SURGE_ABUSE`, `MULTI_ACCOUNT_DRIVER`, `PROMO_ABUSE`, `RATING_FRAUD`, `SPLIT_FARE_FRAUD`, `REFUND_ABUSE`, `PAYMENT_CHARGEBACK`, `DESTINATION_DISPARITY`, `ACCOUNT_TAKEOVER_RIDE`

## Output And Integrations

| Layer | Supported options |
|---|---|
| File formats | `jsonl`, `json`, `csv`, `tsv`, `parquet`, `arrow`, `ipc` |
| Databases | SQLAlchemy-backed `db` or `database` exporter |
| Object storage | MinIO and S3 style paths via `s3://bucket/prefix` |
| Streaming targets | `stdout`, `kafka`, `webhook` |
| Compression | JSONL inline `gzip`, `zstd`, `snappy`; Parquet `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| AI schema correction | Optional `openai`, `anthropic`, or `none` provider selection |

## Why The Data Is Realistic

The goal is not just to generate random events. The library tries to preserve signals that matter for fraud systems and downstream analytics.

<p align="center">
  <img src="docs/assets/Realismo%20e%20qualidade%20dos%20dados.png" alt="Illustration showing realism pillars such as CPF validation, geography, PIX fields, seasonality, behavioral profiles and validation metrics." width="100%" />
</p>

| Realism layer | What the project does |
|---|---|
| Identity | Generates valid CPF using the official check-digit algorithm |
| Payments | Emits Brazilian transaction types, PIX fields, bank context and BACEN-aligned identifiers |
| Time | Uses trimodal hourly peaks, weekday weighting and calendar effects like Black Friday, Christmas, 13th salary and Carnaval |
| Behavior | Applies behavioral profiles so customers do not transact like uniform random bots |
| Geography | IBGE 2022 centroids for 100 major cities; population-weighted state selection; CEP from verified real addresses via BrasilAPI when `ceps_reais.csv` is present, falling back to valid synthetic CEP ranges per municipality |
| Fraud modeling | Injects explicit banking and ride-share fraud patterns with RAG-calibrated BCB/Febraban/MJSP prevalences (see below) instead of hardcoded guesses |
| Risk scoring | Computes `fraud_risk_score` from 17 signals plus 4 correlation rules |

## RAG-Calibrated Fraud Prevalences

Starting from v4.9.0+, fraud type prevalences and amount multipliers are loaded at runtime from `data/rules/fraud_pattern_overrides.json`, which is produced by the FraudFlow RAG pipeline (52K+ chunks, 66 sources, BCB/Febraban/MJSP evidence).

| Fraud type | Original | Calibrated | Real-world source |
|---|:---:|:---:|---|
| `PIX_GOLPE` | 25.0% | **13.10%** | BCB PIX MED (49 months) |
| `ENGENHARIA_SOCIAL` | 20.0% | **14.98%** | Febraban Tech 2024/2025 |
| `CONTA_TOMADA` | 15.0% | **8.21%** | B3 statistical datasets |
| `CARTAO_CLONADO` | 14.0% | **6.74%** | BCB + EMV chip data |
| `BOLETO_FALSO` | 8.0% | **5.23%** | MJSP tipologias |
| `MULA_FINANCEIRA` | 6.0% | **4.29%** | BCB: 100K–107K accounts flagged/month |
| `WHATSAPP_CLONE` | 5.0% | **2.75%** | SaferNet/MJSP |
| `MAO_FANTASMA` | 4.0% | **1.88%** | Febraban: remote-access trojans |
| `SEQUESTRO_RELAMPAGO` | — | **1.39%** | BCB Res. 142/2021 night limit |

The overrides are applied in `calibration_loader.py` — the file is loaded once at import time and normalizes the weights so they always sum to 1.0. If the file is absent the generator falls back to the original values with no error.

To regenerate overrides from the latest RAG evidence, run the FraudFlow pipeline (`POST /regras/gerar` on the data API) and copy the output to `data/rules/fraud_pattern_overrides.json`.

## Calibration Benchmark — Before vs After

The table below compares the generated data **before** (default hardcoded patterns) and **after** the RAG-calibrated pipeline. Both runs use 268K transactions, seed 42.

| Dimension | Before | After (V5) | Change |
|---|:---:|:---:|:---:|
| **Realism score** | 7.9/10 | **8.0/10** | +1.3% |
| **Fraud/legit ratio** | 1.87× | **5.09×** | **+172%** |
| **Fraud types** | 17 | **25** | **+8 new** |
| Fraud mean value | R$ 493 | **R$ 1,210** | +145% |
| Legit mean value | R$ 264 | **R$ 238** | −10% |
| Temporal score | 7.2/10 | 7.2/10 | = |
| Geographic score | 10/10 | 10/10 | = |
| Fraud rate score | 6.6/10 | **7.0/10** | +5.7% |
| SP+RJ+MG share | 37.0% | **38.2%** | +3.3% |
| Fraud score sep. | 27.7 pts | **29.6 pts** | +6.7% |
| States covered | 27 | 27 | = |
| Output columns | 117 | 117 | = |
| Tests passing | 194/194 | 194/194 | = |

**Key improvements:**
- Fraud amounts are now **5× higher** than legitimate (was 1.87×), matching BCB/Sparkov real-world ratios of 5–8×
- 8 new fraud patterns sourced from MJSP Aliança Nacional, BCB, and Febraban reports
- Fraud score separation improved, making fraud records more distinctly detectable

## Real CEP Pipeline

Customer records include a `postal_code` field. By default this is a synthetic but valid-format CEP derived from the correct numeric range for the customer's municipality (e.g., São Paulo always gets a CEP starting with `01xxx`–`09xxx`).

To upgrade to verified real addresses:

```bash
# Via the FraudFlow data API — generates ~1,000 seeds from all municipalities in
# municipios.py and validates each against BrasilAPI v2 + ViaCEP fallback
curl -X POST http://localhost:8000/coleta/ceps \
  -H 'Content-Type: application/json' \
  -d '{"usar_seeds_municipios": true}'

# Or with custom CEPs
curl -X POST http://localhost:8000/coleta/ceps \
  -H 'Content-Type: application/json' \
  -d '{"ceps_extras": ["01310100", "20040020", "30112020"]}'
```

Once `data/ceps/ceps_reais.csv` exists the generator's `RealCepPool` silently prefers real CEPs over synthetic ones for every city that has coverage. No restart required — the CSV path is checked at first use.

The file path can be overridden with the `CEPS_REAIS_PATH` environment variable.

**APIs used (both free, no key required):**
- BrasilAPI CEP v2 — `https://brasilapi.com.br/api/cep/v2/{cep}` — returns street, neighbourhood, city, state, and GPS coordinates
- ViaCEP — `https://viacep.com.br/ws/{cep}/json/` — fallback when BrasilAPI has no coordinates for a given CEP



## Why The Generated Data Has Value

This is useful when you need synthetic fraud data that is close enough to real operational patterns to stress real systems.

| Use case | Value |
|---|---|
| ML training | Labeled fraud records, configurable fraud rate, deterministic seeds, and explainable fraud signals |
| QA and platform testing | Repeatable datasets for APIs, ETL, warehouses, scoring services and data contracts |
| Streaming validation | Kafka, webhook and stdout outputs for near-real event tests |
| Data engineering benchmarks | JSONL, Parquet, Arrow, DB and object storage targets |
| Schema testing | Bundled schemas and custom schema mode for consumer-specific payloads |

## Quality And Validation

The repository already ships with validation and testing tools so you can inspect output quality instead of trusting marketing claims.

### Validate realism

```bash
python validate_realism.py --input output/transactions_*.jsonl
```

This reports temporal entropy, hour distribution, day-of-week distribution, geographic spread, fraud rate, fraud-type distribution, amount statistics, and a composite realism score.

### Inspect schema and output structure

```bash
python check_schema.py
```

For schema-driven generation, compare your output against the bundled files in `schemas/` and the minimal sample in `output_test/banking_minimal_output.jsonl`.

### Run automated tests

```bash
pytest tests/ -v
pytest tests/integration/ -v
pytest tests/ --cov=src/fraud_generator --cov-report=html
```

### Practical tools to test the generated data

| Tool | Why use it |
|---|---|
| `pytest` | Validate workflows and regressions |
| `validate_realism.py` | Measure realism and fraud distributions |
| `pandas` | Inspect columns, nulls, skew and outliers |
| `DuckDB` | Query JSONL or Parquet quickly with SQL |
| Kafka console consumers | Verify real-time event flow |
| Spark or PyArrow | Test data lake compatibility and scale |

## Performance Snapshot

Measured on an 18-core x86_64 Linux machine, Python 3.12, using the in-process benchmark (`benchmarks/comprehensive_benchmark.py`).

### Batch Generation

| Type | Count | Workers | Time (s) | Events/s | MB/s | Bytes/evt | Mem (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| transactions |     10,000 |       1 |     0.58 |   17,197 |  37.2 |      2,271 |    229 |
| transactions |     10,000 |       4 |     0.24 |   41,876 |  90.7 |      2,271 |    239 |
| transactions |     10,000 |       8 |     0.18 |   56,153 | 121.6 |      2,271 |    239 |
| transactions |     50,000 |       4 |     1.20 |   41,821 |  90.5 |      2,269 |    372 |
| transactions |     50,000 |       8 |     0.88 |   56,937 | 123.2 |      2,269 |    372 |
| transactions |    100,000 |       8 |     1.73 |   57,889 | 124.8 |      2,260 |    505 |
| rides        |     10,000 |       1 |     0.34 |   29,778 |  34.0 |      1,198 |    505 |
| rides        |     50,000 |       4 |     0.74 |   67,495 |  77.2 |      1,199 |    505 |
| all types    |    100,000 |       4 |     1.82 |   54,884 | 118.8 |      2,269 |    531 |

**Peak: ~67k events/s for rides (4w), ~58k events/s for transactions (8w)**

### Streaming (token-bucket pacing)

| Type | Count | Target (evt/s) | Actual (evt/s) | Accuracy |
|---|---:|---:|---:|---:|
| transactions | 2,000 |    10 |    10 | 99.8% |
| transactions | 2,000 |   100 |    98 | 97.7% |
| transactions | 2,000 |   500 |   445 | 89.0% |
| rides        | 2,000 |   100 |    99 | 98.8% |

Streaming accuracy degrades at high rates (≥500 evt/s) due to OS scheduling jitter. For rates above ~200 evt/s the generator keeps up; use `--rate` values your consumer can actually handle.

Raw results: `benchmarks/comprehensive_results.json` · Regenerate: `python3 benchmarks/comprehensive_benchmark.py`

## Self-Hosted API Server

The repository includes a FastAPI service (`src/fraud_generator/api/app.py`) for teams that want to expose the generator over HTTP. The v1 endpoints cover registration, health checks, heartbeats, and admin revocation. See the API README for setup instructions.

## Repository Map

| Start here | Purpose |
|---|---|
| `generate.py` | Batch generation entrypoint |
| `stream.py` | Continuous event streaming |
| `validate_realism.py` | Realism scoring and distribution checks |
| `schemas/` | Bundled JSON schema examples |
| `src/fraud_generator/exporters/` | Output formats and storage adapters |
| `src/fraud_generator/connections/` | Kafka, webhook and stdout connections |
| `src/fraud_generator/api/app.py` | Self-hosted API server v1 |
| `ARCHITECTURE.md` | Architecture overview |
| `docs/README.md` | Documentation hub |

## FAQ

<details>
<summary><strong>Is this only for banking data?</strong></summary>

No. The repository supports both banking fraud datasets and ride-share fraud datasets, and `--type all` can generate both in the same run.

</details>

<details>
<summary><strong>Can I shape the output to my own schema?</strong></summary>

Yes. Use `--schema` with one of the bundled examples in `schemas/` or your own JSON schema file.

</details>

<details>
<summary><strong>Can I use it for ML evaluation and platform testing?</strong></summary>

Yes. The project was designed for fraud detection model training, synthetic dataset generation, QA pipelines, event-stream testing, and validation of downstream analytics systems.

</details>

## Documentation

- Main docs: [docs/README.md](docs/README.md)
- Portuguese docs: [docs/README.pt-BR.md](docs/README.pt-BR.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Changelog: [docs/CHANGELOG.md](docs/CHANGELOG.md)
- Docker publishing: [docs/DOCKER_HUB_PUBLISHING.md](docs/DOCKER_HUB_PUBLISHING.md)

