# synthfin-data

<p align="center">
  <img src="docs/assets/Hero%20do%20README.png" alt="synthfin-data — synthetic fraud data for Brazilian banking, PIX, ride-share, fraud signals and exports." width="100%" />
</p>

<p align="center">
  <a href="VERSION"><img src="https://img.shields.io/badge/version-4.17-0F766E" alt="Version 4.17" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Custom%20Non--Commercial-DC2626" alt="Custom Non-Commercial License" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-1D4ED8" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/AUC--ROC-0.9991-0F766E" alt="AUC-ROC 0.9991" />
  <img src="https://img.shields.io/badge/quality-9.70%2F10-0F766E" alt="Quality 9.70/10" />
  <img src="https://img.shields.io/badge/domains-banking%20%7C%20ride--share-0F172A" alt="Banking and ride-share" />
  <img src="https://img.shields.io/badge/streaming-kafka%20%7C%20webhook%20%7C%20stdout%20%7C%20redis--stream-7C3AED" alt="Streaming targets" />
</p>

<p align="center">
  <strong>Synthetic fraud data for Brazilian banking, PIX and ride-share systems.</strong><br />
  Generate realistic labeled datasets for fraud detection models, QA pipelines, platform testing, and data engineering workflows.
</p>

<p align="center">
  <a href="docs/README.md">Documentation</a> · <a href="docs/README.pt-BR.md">Português</a> · <a href="ARCHITECTURE.md">Architecture</a> · <a href="docs/CHANGELOG.md">Changelog</a> · <a href="https://hub.docker.com/r/afborda/synthfin-data">Docker Hub</a>
</p>

---

## Why This Project

**synthfin-data** generates realistic Brazilian fraud datasets — not toy random data. It covers PIX-heavy banking, ride-share fraud, behavioral profiles, deterministic seeds, and schema-driven output.

<table>
  <tr>
    <td width="33%"><strong>Brazil-first realism</strong><br />Valid CPF, real BACEN ISPBs, IBGE municipal codes, behavioral profiles, seasonality, and geolocation based on Censo 2022 population weights.</td>
    <td width="33%"><strong>Ready for pipelines</strong><br />Batch files, streaming events, schema mode, database export, Kafka/webhook delivery, MinIO/S3 upload, and reproducible seeds.</td>
    <td width="33%"><strong>Fraud-focused labels</strong><br />25 banking + 11 ride-share fraud patterns, 17 risk signals, 4 correlation rules, and <code>fraud_risk_score</code> 0–100 with per-signal breakdown.</td>
  </tr>
</table>

---

## Quick Start

```bash
pip install -r requirements.txt

# 1 GB of banking transactions (default 0.8% fraud)
python generate.py --size 1GB --output ./data

# Reproducible: fixed seed, 5% fraud, 8 workers
python generate.py --size 2GB --fraud-rate 0.05 --seed 42 --workers 8 --output ./data

# Ride-share data
python generate.py --size 500MB --type rides --output ./data

# Both domains
python generate.py --size 1GB --type all --output ./data
```

### Streaming

```bash
pip install -r requirements-streaming.txt

python stream.py --target stdout  --rate 5  --pretty
python stream.py --target kafka   --kafka-server localhost:9092 --kafka-topic transactions --rate 100
python stream.py --target webhook --webhook-url http://api:8080/ingest --rate 50
```

### Docker

```bash
docker run --rm -v $(pwd)/output:/output \
  afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output
```

---

## 8-Stage Enrichment Pipeline

Every transaction passes through a deterministic pipeline that builds realistic fraud context layer by layer:

```
Customer + Device
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  01 Temporal   →  02 Geo   →  03 Fraud   →  04 PIX   →  05 Device          │
│                                                                              │
│  06 Session    →  07 Risk (17 signals)   →  08 Biometric                    │
└─────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
  Labeled record (114+ fields)
  is_fraud · fraud_type · fraud_risk_score · fraud_signals[]
```

| # | Enricher | What it adds |
|---|----------|--------------|
| 01 | **Temporal** | Unusual hours (22h–5h), weekday seasonality, time_anomaly flag |
| 02 | **Geo** | IBGE lat/lon centroid, 7-digit municipality code, weighted by Censo 2022 population |
| 03 | **Fraud** | Fraud type injection, amount multiplier, velocity burst, log-normal noise |
| 04 | **PIX** | `end_to_end_id`, real ISPB (BACEN IF.data), `pacs.008` / `pacs.004` status |
| 05 | **Device** | `device_age_days`, `emulator_detected`, `vpn_active`, `rooted_or_jailbreak` |
| 06 | **Session** | `velocity_24h`, `new_beneficiary`, `accumulated_amount_24h`, `dest_account_age_days` |
| 07 | **Risk** | 17-signal score (weights: `active_call`=35, `emulator`=35, `rooted`=30, …, `odd_hours`=8) |
| 08 | **Biometric** | `typing_speed_avg_ms`, `touch_pressure_avg`, `scroll_before_confirm`, `session_duration_sec` |

---

## ML Quality Validation

Beyond label accuracy, synthfin-data ships an **adversarial ML quality layer** that measures how detectable the generated fraud is against a held-out LightGBM classifier — giving you an independent signal of data fidelity.

### What it does

1. Trains a LightGBM binary classifier (`is_fraud`) on a generated dataset
2. Trains 25 per-type OvR classifiers (`fraud_type` X vs all legit)
3. Reports AUC-ROC / AUC-PR overall + per fraud type
4. Flags quality issues:

| Per-type AUC | Diagnostic | Meaning |
|---|---|---|
| > 0.99 | `too_easy` | Enricher is over-deterministic — signals don't overlap with legit |
| 0.85–0.99 | Healthy (high signal) | Expected for CONTA_TOMADA, CREDENTIAL_STUFFING |
| 0.70–0.85 | Healthy (low signal) | Expected for ENGENHARIA_SOCIAL, WHATSAPP_CLONE |
| < 0.70 | `too_hard` | Enricher not activating enough discriminative signals |

### Run it

```bash
# 1. Generate a training dataset (5% fraud for per-type coverage)
python generate.py --size 50MB --fraud-rate 0.05 --seed 42 --output ./data/ml_training

# 2. Train the quality model
python tools/train_ml.py \
  --input ./data/ml_training/*.jsonl \
  --model-dir ./models \
  --version v1

# 3. Analyze a new batch
python tools/analyze_batch.py \
  --input ./data/ml_training/transactions_00000.jsonl \
  --output ./data/ml_analysis_report.json
```

### Analysis report (excerpt)

```json
{
  "metadata": { "total_records": 52418, "fraud_count": 2601, "fraud_rate_actual": 0.0496 },
  "ml_quality": {
    "overall": { "auc_roc": 0.997, "auc_pr": 0.981, "n_fraud": 2601 },
    "per_type": {
      "CONTA_TOMADA":      { "auc_roc": 0.961, "n_examples": 312 },
      "ENGENHARIA_SOCIAL": { "auc_roc": 0.847, "n_examples": 289 },
      "PIX_GOLPE":         { "auc_roc": 0.934, "n_examples": 201 },
      "FRAUDE_QR_CODE":    { "auc_roc": 0.783, "n_examples": 87  }
    },
    "feature_importance": {
      "velocity_transactions_24h": 0.128,
      "accumulated_amount_24h":    0.123,
      "amount":                    0.121,
      "device_age_days":           0.080,
      "fraud_risk_score":          0.062
    },
    "quality_flags": []
  },
  "signal_analysis": {
    "odd_hours_activation": 0.083,
    "ato_triad_activation": 0.211,
    "emulator_activation":  0.034
  }
}
```

### Scientific analysis tools

`tools/analyze_batch.py` computes:

- **Cliff's delta** — effect size between fraud and legit for each numeric signal
- **Jensen-Shannon divergence** — distribution distance per fraud type
- **Cramér's V** — association between categorical fields and `fraud_type`
- **KS-test** — separability of `fraud_score` and `fraud_risk_score` distributions
- **Cohen's d** — velocity signal separability across 1h/6h/24h/7d windows

---

## 25 Banking Fraud Patterns

Each pattern has calibrated enricher weights, velocity profiles, device signal activations, and amount multipliers derived from BCB/Febraban/MJSP public reports.

| Pattern | Key signals |
|---------|-------------|
| `CONTA_TOMADA` | new_device + ip_mismatch + hours_inactive ≥ 168 (ATO triad) |
| `PIX_GOLPE` | new_beneficiary + dest_account_age < 7d + social pressure |
| `ENGENHARIA_SOCIAL` | active_call + notification_ignored + customer's own device |
| `SIM_SWAP` | sim_swap_recent + new_device + ATO velocity |
| `CARTAO_CLONADO` | ip_mismatch + high velocity + CNP channel |
| `CREDENTIAL_STUFFING` | emulator_detected + bot typing interval < 15ms |
| `MAO_FANTASMA` | is_rooted + nav_anomaly + zero touch pressure |
| `WHATSAPP_CLONE` | active_call + new_beneficiary + customer's own device |
| `MICRO_BURST_VELOCITY` | 10–50 transactions in 5–15 min + multiple IPs |
| `BOLETO_FALSO` | new_beneficiary + dest_account_age < 7d |
| + 15 more | Full catalog: [docs/07_CATALOGO_FRAUDES.md](docs/07_CATALOGO_FRAUDES.md) |

---

## Output Schema

```
./data/
├── customers.jsonl           ← one record per customer
├── devices.jsonl             ← one or more devices per customer
└── transactions_00000.jsonl  ← transactions (one file per worker)
```

For `--type rides`: `customers.jsonl` + `drivers.jsonl` + `rides_00000.jsonl`  
For `--type all`: all five files.

<details>
<summary><strong>Banking transaction — legitimate (click to expand)</strong></summary>

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
  "fraud_score": 11,
  "is_fraud": false,
  "fraud_risk_score": 0
}
```

</details>

<details>
<summary><strong>PIX fraud (BACEN fields + risk signals)</strong></summary>

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
  "fraud_signals": ["active_call", "amount_spike"],
  "new_beneficiary": true,
  "dest_account_age_days": 3,
  "touch_pressure_avg": 0.62,
  "typing_speed_avg_ms": 180
}
```

</details>

---

## What You Can Generate

| Area | Details |
|---|---|
| **Banking** | PIX, TED, DOC, boleto, withdrawals, POS, e-commerce — with merchant context, device, BACEN PIX fields, valid CPF |
| **Ride-share** | Uber, 99, Cabify, inDrive — drivers, surge pricing, weather, geospatial distance |
| **Fraud patterns** | 25 banking (BCB/Febraban/MJSP calibrated) + 11 ride-share types |
| **Fraud scoring** | 17 signals + 4 correlation rules → `fraud_risk_score` 0–100 |
| **Profiles** | 7 transaction + 7 ride behavioral profiles, sticky per customer |
| **Formats** | JSONL, JSON, CSV, TSV, Parquet, Arrow IPC, database (SQLAlchemy), MinIO/S3 |
| **Compression** | JSONL: gzip/zstd/snappy · Parquet: snappy/zstd/gzip/brotli |
| **Streaming** | stdout, Kafka, webhook, redis-stream — sync or async |
| **Schema mode** | Declarative JSON schemas with optional AI field correction |
| **ML validation** | LightGBM adversarial classifier, per-type AUC, Cliff's delta, JSD |

---

## Project Structure

```
generate.py                     # Batch entry point (→ BatchRunner / MinIORunner / SchemaRunner)
stream.py                       # Streaming entry point (→ stdout / kafka / webhook / redis-stream)
src/fraud_generator/
├── generators/                 # Customer → Device → Transaction / Ride entity chain
├── enrichers/                  # 8-stage fraud signal pipeline (8 enrichers, 17 signals, 4 rules)
│   ├── temporal.py             # Timestamps, unusual_time, time_anomaly
│   ├── geo.py                  # IBGE centroids, CEP ranges, Censo 2022 weights
│   ├── fraud.py                # Fraud injection, velocity noise, dest_account_age
│   ├── pix.py                  # end_to_end_id, ISPB, pacs.008
│   ├── device.py               # Device signals, emulator, VPN, rooted
│   ├── session.py              # Velocity windows, accumulated amounts
│   ├── risk.py                 # fraud_risk_score (17-signal weighted sum)
│   └── biometric.py            # Typing speed, touch pressure, scroll behavior
├── ml/                         # ML quality validation package (NEW)
│   ├── features.py             # extract_features() — 31-feature DataFrame
│   ├── trainer.py              # LightGBM binary + 25 OvR per-type classifiers
│   └── evaluator.py            # evaluate_batch() — AUC, quality flags, feature importance
├── exporters/                  # JSONL, CSV, Parquet, Arrow, DB, MinIO
├── connections/                # Streaming targets (Kafka, webhook, redis-stream, stdout)
├── config/                     # 14 config modules (*_LIST + *_WEIGHTS + get_*())
├── profiles/                   # Behavioral profiles (7 TX + 7 ride), device profiles
├── models/                     # Data classes (Customer, Device, Transaction, Ride)
├── schema/                     # Declarative JSON schema engine
├── validators/                 # CPF validation
├── utils/                      # WeightCache, compression, parallel, streaming state
├── cli/                        # CLI args, runners, workers (multiprocessing)
└── licensing/                  # Tier validation (proprietary, excluded from OS release)
tools/
├── analyze_batch.py            # Scientific analysis (Cliff's delta, JSD, Cramér's V)
├── train_ml.py                 # Offline LightGBM training CLI
├── backtest_rules.py           # Simulate fraud rule changes before regenerating
├── tstr_benchmark.py           # Train Synthetic Test Real (RF + XGBoost)
├── privacy_metrics.py          # LGPD privacy metrics (exact match, k-neighbors)
├── qde_filter.py               # Quality Data Extractor — filter inconsistencies
└── validate/dashboard.py       # Streamlit validation dashboard
schemas/                        # Bundled JSON schema examples
benchmarks/                     # Performance and quality benchmarks
tests/                          # pytest: unit/ (11 files) + integration/ (2 files)
docs/                           # Full documentation
```

---

## CLI Reference

<details>
<summary><strong>generate.py — all flags</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--type` | `transactions` | `transactions`, `rides`, or `all` |
| `--size` | `1GB` | Target output size: `1GB`, `500MB`, `10GB` |
| `--output` | `./output` | Output directory or `minio://bucket/prefix` |
| `--format` | `jsonl` | `jsonl`, `json`, `csv`, `tsv`, `parquet`, `parquet_partitioned`, `arrow`, `ipc`, `db` |
| `--jsonl-compress` | `none` | `none`, `gzip`, `zstd`, `snappy` |
| `--fraud-rate` | `0.008` | Fraction of fraud records (0.0–1.0) |
| `--workers` | CPU count | Parallel worker processes |
| `--seed` | none | Deterministic seed for reproducibility |
| `--parallel-mode` | `auto` | `auto`, `thread`, `process` |
| `--customers` | auto | Fixed customer pool size |
| `--start-date` | 1 year ago | `YYYY-MM-DD` |
| `--end-date` | today | `YYYY-MM-DD` |
| `--no-profiles` | off | Disable behavioral profiles |
| `--compression` | `zstd` | Parquet: `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| `--schema` | none | Declarative JSON schema file |
| `--count` | `1000` | Record count (schema mode) |
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
| `--target` | required | `kafka`, `webhook`, `stdout`, or `redis-stream` |
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
| `--quiet` | off | Suppress progress output |

</details>

<details>
<summary><strong>tools/train_ml.py — ML quality model</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--input` | required | Glob of JSONL files (e.g. `./data/*.jsonl`) |
| `--model-dir` | `./models` | Directory to save trained models |
| `--version` | `v1` | Model version tag (e.g. `v4`) |
| `--skip-multilabel` | off | Skip per-type OvR classifiers |
| `--max-records` | unlimited | Cap records loaded into memory |
| `--min-examples-per-class` | `50` | Skip types with fewer examples |

Output: `{model-dir}/fraud_detector_{version}.pkl` + `train_metrics_{version}.json`

</details>

---

## Quality And Validation

```bash
# Realism validation (temporal, geographic, fraud distributions)
python validate_realism.py --input output/transactions_*.jsonl

# Schema structure validation
python check_schema.py

# Full test suite
pytest tests/ -v

# Scientific analysis report
python tools/analyze_batch.py \
  --input output/transactions_00000.jsonl \
  --output analysis_report.json

# ML quality model (offline training)
python tools/train_ml.py \
  --input output/*.jsonl \
  --model-dir ./models \
  --version v1
```

**Current benchmarks:**

| Metric | Value |
|---|---|
| Quality score | 9.70 / 10 |
| AUC-ROC (binary classifier) | 0.9991 |
| Throughput (8 workers, 18-core) | ~58K events/s |
| Fraud types covered | 25 banking + 11 ride-share |
| Fields per transaction | 114+ |
| Geographic coverage | 104 municipalities, 27 states |
| Signal coverage | 17 risk signals, 4 correlation rules |

---

## Performance

Peak throughput (18-core Linux, Python 3.12):

| Type | Workers | Events/s | MB/s |
|---|---:|---:|---:|
| Transactions | 8 | ~58,000 | 125 |
| Rides | 4 | ~67,000 | 77 |
| All types | 4 | ~55,000 | 119 |

Detail: `benchmarks/comprehensive_results.json` · Regenerate: `python benchmarks/comprehensive_benchmark.py`

---

## License

Custom non-commercial license. Free for **personal study, academic research, and educational purposes**. Commercial use requires a paid license — see [LICENSE](LICENSE).

A hosted API is available at [synthfin.com.br](https://synthfin.com.br) for managed generation with BACEN/IBGE real reference data, streaming, webhooks, and ML Quality Lab.

## Privacy & Telemetry

This open-source distribution does **not** send any telemetry, analytics, or data to external servers. The `phone_home` parameter in `generate.py`/`stream.py` is a **no-op** — the proprietary licensing module is excluded via `.gitignore`.

---

## Documentation

| Resource | Link |
|----------|------|
| Documentation hub | [docs/README.md](docs/README.md) |
| Portuguese docs | [docs/README.pt-BR.md](docs/README.pt-BR.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Changelog | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| Fraud catalog (25 types) | [docs/07_CATALOGO_FRAUDES.md](docs/07_CATALOGO_FRAUDES.md) |
| AI Agents (9 specialists) | [AGENTS.md](AGENTS.md) |
| Docker publishing | [docs/DOCKER_HUB_PUBLISHING.md](docs/DOCKER_HUB_PUBLISHING.md) |
