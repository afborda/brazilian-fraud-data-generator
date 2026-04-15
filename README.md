# synthfin-data

<p align="center">
  <img src="docs/assets/Hero%20do%20README.png" alt="synthfin-data — synthetic fraud data for Brazilian banking, PIX, ride-share, fraud signals and exports." width="100%" />
</p>

<p align="center">
  <a href="VERSION"><img src="https://img.shields.io/badge/version-4.18.0-0F766E" alt="Version 4.18.0" /></a>
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

## ⚡ SynthFin API — Hosted Platform (Beta)

> **🧪 Beta phase — testing open to everyone.**
> A hosted version of this generator is available at **[synthfin.com.br](https://synthfin.com.br)** — no infrastructure to run, REST API included, ML quality report delivered by email after every job.
>
> **Want to test it?** Send an email to **[devabnerfonseca@gmail.com](mailto:devabnerfonseca@gmail.com)** and we'll get you set up.
>
> **Have real fraud data to compare against?** We're actively looking for partners who can share anonymized or aggregated real-world data to validate and improve the quality of our synthetic distributions. If you work in fraud prevention at a bank, fintech, or payment processor and would like to collaborate — even informally — please reach out. Any contribution to improve detection accuracy is very welcome.

The hosted API at [api.synthfin.com.br](https://api.synthfin.com.br) delivers:

- **REST API** — `POST /v2/generate` → async job → download link
- **ML Quality Report** — automatic LightGBM analysis after every batch job, grade A+→F emailed to you with AUC-ROC, per-fraud-type breakdown, and feature importance
- **Dashboard** at [app.synthfin.com.br](https://app.synthfin.com.br) — job history, download, quality reports
- **Streaming** — Server-Sent Events feed via `/v2/streams`
- **Webhooks** — job completion notifications to your endpoint

```bash
# Create a batch job via API
curl -X POST https://api.synthfin.com.br/v2/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"transactions","count":100000,"format":"parquet","fraud_rate":0.03}'

# Poll for status (includes quality metrics after analysis)
curl https://api.synthfin.com.br/v2/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
# → {"status":"done","download_url":"...","quality_auc_roc":0.9347,"quality_report_url":"..."}
```

After the job completes, you receive an email with:
- Download link for the dataset (JSONL / CSV / Parquet)
- Quality report link — HTML report with grade, AUC-ROC per fraud type, and signal importance
- Automatic quality flags if any fraud type is `too_easy` or `too_hard` to detect

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

## How It Works — End to End

### Open Source (self-hosted)

```
python generate.py --size 1GB --format parquet --fraud-rate 0.03 --seed 42 --output ./data
```

```
generate.py
    │
    ▼
BatchRunner (multiprocessing, N workers)
    │
    ├── CustomerGenerator  →  customers.jsonl
    ├── DeviceGenerator    →  devices.jsonl
    └── TransactionGenerator
            │
            ▼
        generate_with_pipeline()
            │
            ├── 01 Temporal    (unusual hours, seasonality, time_anomaly)
            ├── 02 Geo         (IBGE lat/lon, municipality, Censo 2022 weights)
            ├── 03 Fraud       (inject pattern, velocity, dest_account_age)
            ├── 04 PIX         (end_to_end_id, ISPB, pacs.008)
            ├── 05 Device      (emulator, VPN, rooted, device_age_days)
            ├── 06 Session     (velocity windows 1h/6h/24h/7d, accumulated amounts)
            ├── 07 Risk        (fraud_risk_score: 17 signals, 4 correlation rules)
            └── 08 Biometric   (typing speed, touch pressure, scroll behavior)
                    │
                    ▼
            Labeled record (114+ fields)
            is_fraud · fraud_type · fraud_risk_score · fraud_signals[]
                    │
                    ▼
        Exporter (JSONL / CSV / Parquet / Arrow / DB / MinIO)
```

### Hosted API (synthfin.com.br)

```
Your app
    │
    ▼  POST /v2/generate
API (FastAPI + Redis queue)
    │
    ▼
Worker Pool (multiprocessing, same pipeline as above)
    │
    ├── Upload dataset  →  MinIO (presigned URL, 48h TTL)
    │
    └── ML Quality Analysis
            │
            ├── evaluate_batch() via LightGBM
            ├── Grade A+→F  (AUC-ROC + penalty for too_easy/too_hard types)
            ├── HTML Quality Report  →  MinIO
            └── Email → you (dataset link + report link + grade + AUC-ROC)
    │
    ▼  GET /v2/jobs/{id}
{
  "status": "done",
  "download_url": "https://...",
  "quality_auc_roc": 0.9347,
  "quality_auc_pr": 0.8812,
  "quality_report_url": "https://...",
  "quality_analysis_id": "ana_f3a91c..."
}
```

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
python stream.py --target redis-stream --rate 50
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

### Quality grades

| Grade | AUC-ROC effective | Meaning |
|---|---|---|
| **A+** | ≥ 0.97 | Excellent — ready for production training |
| **A** | ≥ 0.93 | Very good |
| **B+** | ≥ 0.89 | Good |
| **B** | ≥ 0.85 | Acceptable |
| **C** | ≥ 0.75 | Marginal — review fraud patterns |
| **D** | ≥ 0.65 | Weak — consider regenerating |
| **F** | < 0.65 | Failed |

> Effective AUC-ROC applies penalties for over-deterministic types (`too_easy`, weight 0.12) and statistically insufficient types (`too_hard`, weight 0.05).

### Per-type flags

| Flag | Meaning |
|---|---|
| `healthy_high_signal` | Detectable and well-balanced |
| `healthy_low_signal` | Detectable with few examples |
| `too_easy` | Deterministic signals — model memorizes instead of learning |
| `too_hard` | Too few examples or weak signal — AUC unreliable |

### Run it locally

```bash
# 1. Generate training data
python generate.py --size 50MB --fraud-rate 0.05 --seed 42 --output ./data/train

# 2. Train quality model
python tools/train_ml.py --input ./data/train/*.jsonl --model-dir ./models --version v1

# 3. Analyze a batch
python tools/analyze_batch.py \
  --input ./data/train/transactions_00000.jsonl \
  --output ./data/analysis_report.json
```

---

## 25 Banking Fraud Patterns

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
  "transaction_id": "TXN_DCB02BE69A265CDE9933",
  "customer_id": "CUST_000000002438",
  "timestamp": "2025-04-28T19:15:14.146316",
  "type": "CREDIT_CARD",
  "amount": 127.82,
  "currency": "BRL",
  "channel": "MOBILE_APP",
  "customer_state": "SP",
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
  "transaction_id": "TXN_A3F2B1C4D5E6F7A8B9C0",
  "customer_id": "CUST_000000001711",
  "timestamp": "2025-11-05T23:45:48.844962",
  "type": "PIX",
  "amount": 1689.28,
  "customer_state": "AM",
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
  "dest_account_age_days": 3
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
| `--fraud-rate` | `0.008` | Fraction of fraud records (0.0–1.0) |
| `--workers` | CPU count | Parallel worker processes |
| `--seed` | none | Deterministic seed for reproducibility |
| `--customers` | auto | Fixed customer pool size |
| `--start-date` | 1 year ago | `YYYY-MM-DD` |
| `--end-date` | today | `YYYY-MM-DD` |
| `--compression` | `zstd` | Parquet: `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| `--schema` | none | Declarative JSON schema file |
| `--db-url` | none | SQLAlchemy URL for `db` format |
| `--minio-endpoint` | env | MinIO/S3 endpoint |

</details>

<details>
<summary><strong>stream.py — all flags</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--target` | required | `kafka`, `webhook`, `stdout`, or `redis-stream` |
| `--type` | `transactions` | `transactions` or `rides` |
| `--rate` | `10` | Events per second |
| `--max-events` | infinite | Stop after N events |
| `--fraud-rate` | `0.008` | Fraction of fraud events |
| `--seed` | none | Random seed |
| `--workers` | `1` | Parallel generators |
| `--pretty` | off | Pretty-print JSON (stdout only) |

</details>

---

## Project Structure

```
generate.py                     # Batch entry point
stream.py                       # Streaming entry point
src/fraud_generator/
├── generators/                 # Customer → Device → Transaction / Ride
├── enrichers/                  # 8-stage pipeline (17 signals, 4 rules)
├── ml/                         # LightGBM quality validation
│   ├── features.py             # extract_features() — 31-feature DataFrame
│   ├── trainer.py              # Binary + 25 OvR per-type classifiers
│   └── evaluator.py            # evaluate_batch() — AUC, flags, importance
├── exporters/                  # JSONL, CSV, Parquet, Arrow, DB, MinIO
├── connections/                # Kafka, webhook, redis-stream, stdout
├── config/                     # 14 config modules (*_LIST + *_WEIGHTS)
├── profiles/                   # 7 TX + 7 ride behavioral profiles
├── utils/                      # WeightCache, watermark, compression
└── validators/                 # CPF validation
tools/
├── analyze_batch.py            # Cliff's delta, JSD, Cramér's V, KS-test
├── train_ml.py                 # Offline LightGBM training CLI
├── tstr_benchmark.py           # Train Synthetic Test Real benchmark
└── privacy_metrics.py          # LGPD privacy metrics
```

---

## License

Custom non-commercial license. Free for **personal study, academic research, and educational purposes**. Commercial use requires a paid license — see [LICENSE](LICENSE).

A hosted API is available at **[synthfin.com.br](https://synthfin.com.br)** (currently in beta — contact [devabnerfonseca@gmail.com](mailto:devabnerfonseca@gmail.com) to get access).

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
| Fraud catalog (36 types) | [docs/07_CATALOGO_FRAUDES.md](docs/07_CATALOGO_FRAUDES.md) |
| Docker Hub | [afborda/synthfin-data](https://hub.docker.com/r/afborda/synthfin-data) |
