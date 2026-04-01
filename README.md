# synthfin-data

<p align="center">
  <img src="docs/assets/Hero%20do%20README.png" alt="synthfin-data — synthetic fraud data for Brazilian banking, PIX, ride-share, fraud signals and exports." width="100%" />
</p>

<p align="center">
  <a href="VERSION"><img src="https://img.shields.io/badge/version-4.17-0F766E" alt="Version 4.17" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Custom%20Non--Commercial-DC2626" alt="Custom Non-Commercial License" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-1D4ED8" alt="Python 3.10 or newer" />
  <img src="https://img.shields.io/badge/domains-banking%20%7C%20ride--share-0F172A" alt="Banking and ride-share domains" />
  <img src="https://img.shields.io/badge/streaming-kafka%20%7C%20webhook%20%7C%20stdout-7C3AED" alt="Kafka, webhook and stdout streaming" />
</p>

<p align="center">
  <strong>Synthetic fraud data for Brazilian banking, PIX and ride-share systems.</strong><br />
  Generate realistic labeled datasets for fraud detection models, QA pipelines, platform testing, and data engineering workflows.
</p>

<p align="center">
  <a href="docs/README.md">Documentation</a> · <a href="docs/README.pt-BR.md">Português</a> · <a href="ARCHITECTURE.md">Architecture</a> · <a href="docs/CHANGELOG.md">Changelog</a> · <a href="https://hub.docker.com/r/afborda/synthfin-data">Docker Hub</a>
</p>

## Why This Project

**synthfin-data** generates realistic Brazilian fraud datasets — not toy random data. It covers PIX-heavy banking, ride-share fraud, behavioral profiles, deterministic seeds, and schema-driven output.

<table>
  <tr>
    <td width="33%"><strong>Brazil-first realism</strong><br />Valid CPF, real banks, PIX BACEN fields, behavioral profiles, seasonality, and Brazilian geography.</td>
    <td width="33%"><strong>Ready for pipelines</strong><br />Batch files, streaming events, schema mode, database export, Kafka/webhook delivery, and reproducible seeds.</td>
    <td width="33%"><strong>Fraud-focused labels</strong><br />25 banking + 11 ride-share fraud patterns, 17 risk signals, 4 correlation rules, and fraud_risk_score 0–100.</td>
  </tr>
</table>

## Quick Start

```bash
pip install -r requirements.txt

# Generate 1 GB of banking transactions
python generate.py --size 1GB --output ./data

# Generate ride-share data
python generate.py --size 500MB --type rides --output ./data

# Both domains in one run
python generate.py --size 1GB --type all --output ./data

# Reproducible: fixed seed, 15% fraud, 8 workers
python generate.py --size 2GB --fraud-rate 0.15 --seed 42 --workers 8 --output ./data
```

### Streaming

```bash
pip install -r requirements-streaming.txt

# Print events to terminal
python stream.py --target stdout --rate 5 --pretty

# Stream to Kafka
python stream.py --target kafka --kafka-server localhost:9092 --kafka-topic transactions --rate 100

# Stream to a webhook endpoint
python stream.py --target webhook --webhook-url http://api:8080/ingest --rate 50
```

### Docker

```bash
docker run --rm -v $(pwd)/output:/output \
  afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output
```

## Output Schema

```
./data/
├── customers.jsonl           ← one record per customer
├── devices.jsonl             ← one or more devices per customer
└── transactions_00000.jsonl  ← transactions (one file per worker)
```

For `--type rides`: `customers.jsonl` + `drivers.jsonl` + `rides_00000.jsonl`  
For `--type all`: all five files above.

<details>
<summary><strong>Banking transaction example (legitimate)</strong></summary>

```json
{
  "transaction_id": "TXN_1773495125210_0000_000000",
  "customer_id": "CUST_000000002438",
  "timestamp": "2025-04-28T19:15:14.146316",
  "type": "CREDIT_CARD",
  "amount": 127.82,
  "currency": "BRL",
  "channel": "MOBILE_APP",
  "merchant_name": "Cosi",
  "merchant_category": "Restaurants",
  "mcc_code": "5812",
  "cliente_perfil": "young_digital",
  "card_brand": "MASTERCARD",
  "fraud_score": 11,
  "is_fraud": false,
  "fraud_risk_score": 0
}
```

</details>

<details>
<summary><strong>PIX fraud transaction (with BACEN fields and fraud_signals)</strong></summary>

```json
{
  "transaction_id": "TXN_1773495125210_0000_000001",
  "customer_id": "CUST_000000001711",
  "timestamp": "2025-11-05T23:45:48.844962",
  "type": "PIX",
  "amount": 1689.28,
  "pix_key_type": "CPF",
  "end_to_end_id": "E30723886202511052007B0471FE3",
  "ispb_pagador": "30723886",
  "ispb_recebedor": "90400888",
  "velocity_transactions_24h": 10,
  "accumulated_amount_24h": 11824.96,
  "fraud_score": 89,
  "is_fraud": true,
  "fraud_type": "PIX_GOLPE",
  "fraud_risk_score": 43,
  "fraud_signals": ["active_call", "amount_spike"]
}
```

</details>

<details>
<summary><strong>Customer and device records</strong></summary>

```json
{
  "customer_id": "CUST_000000000001",
  "name": "Joaquim Câmara",
  "cpf": "321.819.601-94",
  "bank_code": "341",
  "bank_name": "Itaú Unibanco",
  "behavioral_profile": "subscription_heavy",
  "monthly_income": 2377.87,
  "credit_score": 719
}
```

```json
{
  "device_id": "DEV_000000000001",
  "customer_id": "CUST_000000000001",
  "type": "SMARTPHONE",
  "manufacturer": "Realme",
  "model": "GT5 Pro",
  "operating_system": "Android 12",
  "is_rooted_jailbroken": false
}
```

</details>

<details>
<summary><strong>Ride record</strong></summary>

```json
{
  "ride_id": "RIDE_000000000000",
  "app": "CABIFY",
  "driver_id": "DRV_0000000205",
  "passenger_id": "CUST_000000000913",
  "distance_km": 33.75,
  "duration_minutes": 132,
  "final_fare": 95.9,
  "surge_multiplier": 1.32,
  "weather_condition": "CLEAR",
  "is_fraud": false
}
```

</details>

## What You Can Generate

| Area | Details |
|---|---|
| **Banking** | PIX, TED, DOC, boleto, withdrawals, POS, ecommerce — with merchant context, device context, BACEN PIX fields, and valid CPF |
| **Ride-share** | Uber, 99, Cabify, inDrive style trips — with drivers, surge pricing, weather, and geospatial distance |
| **Fraud patterns** | 25 banking (RAG-calibrated from BCB/Febraban/MJSP) + 11 ride-share types |
| **Fraud scoring** | 17 signals + 4 correlation rules → `fraud_risk_score` 0–100 via 8-stage enricher pipeline |
| **Profiles** | 7 transaction + 7 ride behavioral profiles, sticky per customer |
| **Formats** | JSONL, JSON, CSV, TSV, Parquet, Arrow IPC, database (SQLAlchemy), MinIO/S3 |
| **Compression** | JSONL: gzip/zstd/snappy · Parquet: snappy/zstd/gzip/brotli |
| **Streaming** | stdout, Kafka, webhook — sync or async mode |
| **Schema mode** | Declarative JSON schemas with optional AI field correction |

## CLI Reference

<details>
<summary><strong>generate.py — all flags</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--type` | `transactions` | `transactions`, `rides`, or `all` |
| `--size` | `1GB` | Target output size: `1GB`, `500MB`, `10GB` |
| `--output` | `./output` | Output directory or `minio://bucket/prefix` |
| `--format` | `jsonl` | `jsonl`, `json`, `csv`, `tsv`, `parquet`, `parquet_partitioned`, `arrow`, `ipc`, `db` |
| `--jsonl-compress` | `none` | JSONL compression: `none`, `gzip`, `zstd`, `snappy` |
| `--fraud-rate` | `0.008` | Fraction of fraud records (0.0–1.0) |
| `--workers` | CPU count | Parallel worker processes |
| `--seed` | none | Random seed for reproducibility |
| `--parallel-mode` | `auto` | `auto`, `thread`, `process` |
| `--customers` | auto | Fixed customer pool size |
| `--start-date` | 1 year ago | `YYYY-MM-DD` |
| `--end-date` | today | `YYYY-MM-DD` |
| `--no-profiles` | off | Disable behavioral profiles |
| `--compression` | `zstd` | Parquet: `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| `--schema` | none | Declarative JSON schema file |
| `--count` | `1000` | Record count in schema mode |
| `--schema-ai-provider` | `openai` | AI correction: `openai`, `anthropic`, `none` |
| `--db-url` | none | SQLAlchemy URL for `db` format |
| `--db-table` | `transactions` | Table name for `db` format |
| `--redis-url` | none | Redis URL for index caching |
| `--minio-endpoint` | env | MinIO/S3 endpoint |
| `--minio-access-key` | env | MinIO access key |
| `--minio-secret-key` | env | MinIO secret key |
| `--no-date-partition` | off | Disable date partitioning in MinIO |

</details>

<details>
<summary><strong>stream.py — all flags</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--target` | required | `kafka`, `webhook`, or `stdout` |
| `--type` | `transactions` | `transactions` or `rides` |
| `--rate` | `10` | Events per second |
| `--max-events` | infinite | Stop after N events |
| `--kafka-server` | `localhost:9092` | Kafka bootstrap server |
| `--kafka-topic` | `transactions` | Kafka topic |
| `--webhook-url` | none | HTTP endpoint URL |
| `--webhook-method` | `POST` | `POST`, `PUT`, `PATCH` |
| `--fraud-rate` | `0.008` | Fraction of fraud events |
| `--customers` | `1000` | Customer pool size |
| `--seed` | none | Random seed |
| `--workers` | `1` | Parallel generators |
| `--queue-size` | `10000` | Event buffer size |
| `--async` | off | Async send via thread pool |
| `--async-concurrency` | `100` | Max concurrent sends |
| `--pretty` | off | Pretty-print JSON |
| `--quiet` | off | Suppress progress |

</details>

## Quality And Validation

```bash
# Validate realism (temporal, geographic, fraud distributions)
python validate_realism.py --input output/transactions_*.jsonl

# Validate schema structure
python check_schema.py

# Run test suite
pytest tests/ -v
```

Current quality: realism 8.0/10 · fraud/legit ratio 5.09× (BCB target 5–8×) · 25 fraud types · 27 states · 117 columns · AUC-ROC 0.9991.

## Project Structure

```
generate.py                    # Batch entry point
stream.py                     # Streaming entry point
validate_realism.py            # Realism scoring
check_schema.py                # Schema validation
src/fraud_generator/
├── generators/                # Customer → Device → Transaction/Ride
├── enrichers/                 # 8-stage fraud signal pipeline (17 signals, 4 rules)
├── exporters/                 # JSONL, CSV, Parquet, Arrow, DB, MinIO
├── connections/               # stdout, Kafka, webhook
├── config/                    # 14 config modules (*_LIST + *_WEIGHTS + get_*())
├── profiles/                  # Behavioral and device profiles
├── models/                    # Data classes
├── schema/                    # Declarative JSON schema engine
├── validators/                # CPF validation
├── utils/                     # WeightCache, compression, streaming, parallel
├── cli/                       # CLI args, runners, workers
├── api/                       # Self-hosted FastAPI server
└── licensing/                 # Tier validation
schemas/                       # Bundled JSON schema examples
benchmarks/                    # Performance and quality benchmarks
tests/                         # pytest: unit/ + integration/
tools/                         # Utility scripts (see below)
docs/                          # Full documentation
```

## Utility Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `tools/backtest_rules.py` | Simulate fraud rule changes before regenerating | `python tools/backtest_rules.py --type PIX_GOLPE --prev 0.15` |
| `tools/tstr_benchmark.py` | Train Synthetic, Test Real (RF + XGBoost) | `python tools/tstr_benchmark.py data/transactions.csv` |
| `tools/privacy_metrics.py` | LGPD privacy metrics (exact match, neighbors) | `python tools/privacy_metrics.py` |
| `tools/qde_filter.py` | Quality Data Extractor — filter inconsistencies | `python tools/qde_filter.py data/transactions.csv` |
| `tools/validate/dashboard.py` | Interactive Streamlit validation dashboard | `streamlit run tools/validate/dashboard.py` |

## Performance

Peak throughput (18-core Linux, Python 3.12):

| Type | Workers | Events/s | MB/s |
|---|---:|---:|---:|
| Transactions | 8 | ~58,000 | 125 |
| Rides | 4 | ~67,000 | 77 |
| All types | 4 | ~55,000 | 119 |

Detail: `benchmarks/comprehensive_results.json` · Regenerate: `python benchmarks/comprehensive_benchmark.py`

## License

Custom non-commercial license. Free for **personal study, academic research, and educational purposes**. Commercial use requires a paid license — see [LICENSE](LICENSE).

A hosted API is available at [synthfin.com.br](https://synthfin.com.br) for managed generation.

## Documentation

| Resource | Link |
|----------|------|
| Documentation hub | [docs/README.md](docs/README.md) |
| Portuguese docs | [docs/README.pt-BR.md](docs/README.pt-BR.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Changelog | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| Fraud catalog | [docs/07_CATALOGO_FRAUDES.md](docs/07_CATALOGO_FRAUDES.md) |
| AI Agents (9 specialists) | [AGENTS.md](AGENTS.md) |
| Docker publishing | [docs/DOCKER_HUB_PUBLISHING.md](docs/DOCKER_HUB_PUBLISHING.md) |
