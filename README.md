# 🇧🇷 Brazilian Fraud Data Generator

<div align="center">

[![Version](https://img.shields.io/badge/version-4.1.0--guaraná-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/afborda/brazilian-fraud-data-generator)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Kafka](https://img.shields.io/badge/Kafka-Streaming-231F20?logo=apachekafka)](docs/README.md#streaming-real-time)
[![API](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](src/fraud_generator/api/)
[![SaaS](https://img.shields.io/badge/SaaS-Licensing%20Ready-8957e5)](src/fraud_generator/licensing/)

**Production-Grade Synthetic Data Generator for Brazilian Banking & Ride-Share Fraud Detection**

*Generate realistic fraud scenarios for ML training, pipeline testing, and system validation*

[📖 Full Docs](docs/README.md) • [🇧🇷 Português](docs/README.pt-BR.md) • [🔄 CHANGELOG](docs/CHANGELOG.md) • [🐳 Docker Hub](https://hub.docker.com/r/afborda/brazilian-fraud-data-generator) • [💰 Pricing](docs/PRICING_ANALYSIS_COMPLETO.md) • [🗺️ Roadmap](docs/ROADMAP_TECNICO_DETALHADO.md)

</div>

---

## 🎯 What is this?

A high-performance **synthetic data generator** specifically designed for **Brazilian financial fraud detection** — with a built-in SaaS licensing layer so you can self-host and sell access.

### **Core Features**

✅ **100% Brazilian Context**
- Valid CPF generation (with check digits)
- Real Brazilian banks (Nubank, Inter, Itaú, etc.)
- PIX transactions (QR code, keys, instant payments)
- Brazilian states, cities, and addresses (Faker pt_BR)

✅ **Dual Domain Support**
- 🏦 **Banking:** PIX, cards, TED, boleto, withdrawals
- 🚗 **Ride-Share:** Uber, 99, Cabify, InDriver trips

✅ **Realistic Fraud Patterns**
- 13 banking fraud types (social engineering, card cloning, account takeover)
- 4 ride-share fraud types (GPS spoofing, fake rides, collusion)
- Behavioral profiles for realistic user patterns

✅ **Seasonality & Temporal Realism** *(v4.1.0)*
- Trimodal hourly distribution (noon / 18h / 21h peaks)
- Day-of-week variance (Friday peak, Sunday minimum)
- Annual events: Black Friday, Christmas, 13th salary, Carnaval
- Fraud-specific timing (ATO attacks spike in the early hours)

✅ **Declarative JSON Schema Mode** *(v4.1.0)*
- Define output structure via JSON schema files
- AI-assisted schema correction and field inference
- Schemas for banking (full/minimal) and ride-share included
- Custom schemas supported (`--schema custom_empresa.json`)

✅ **SaaS Licensing System** *(v4.1.0)*
- HMAC-signed license keys with plan enforcement
- Plans: FREE, STARTER, PRO, TEAM, ENTERPRISE
- Per-event limits, concurrent-run caps, format restrictions
- FastAPI server: `/v1/register`, `/v1/heartbeat`, `/v1/health`
- Docker container phones-home on startup for telemetry

✅ **High Performance**
- **56k–385k transactions/second** (batch mode)
- **2.5M records/second** (Arrow IPC format)
- Multi-format export: JSON, CSV, Parquet, Arrow IPC, PostgreSQL, SQLite, DuckDB
- Memory-efficient streaming for TB-scale datasets
- SOLID CLI refactor with parallel workers pool *(v4.1.0)*

✅ **Production Ready**
- Real-time streaming to Kafka, webhooks
- Docker containerized (generator image + API server image)
- Reproducible with seed support
- Async/parallel processing
- Realism validation tool (`validate_realism.py`)

---

## 🚀 Quick Start (3 Commands)

### Option 1: Batch Generation (Files)

```bash
# 1. Install (one-time)
pip install -r requirements.txt

# 2. Generate 1GB of banking data
python generate.py --size 1GB --output ./data

# 3. Check output
ls -lh data/
# customers.jsonl, devices.jsonl, transactions_*.jsonl
```

### Option 2: Declarative JSON Schema Mode *(v4.1.0)*

```bash
# Generate using a bundled schema
python generate.py --schema schemas/banking_full.json --output ./data

# Generate using your own custom schema
python generate.py --schema schemas/custom_empresa.json --size 500MB --output ./data

# Available bundled schemas:
ls schemas/
# banking_full.json  banking_minimal.json  rideshare_full.json  custom_empresa.json
```

### Option 3: Real-Time Streaming

```bash
# Install streaming deps
pip install -r requirements-streaming.txt

# Stream to Kafka (100 transactions/sec)
python stream.py --target kafka \
  --kafka-server localhost:9092 \
  --rate 100

# Or stream to stdout for testing
python stream.py --target stdout --rate 5
```

### Option 4: Docker (Zero Install)

```bash
docker run --rm -v $(pwd)/output:/output \
  afborda/brazilian-fraud-data-generator:latest \
  generate.py --size 500MB --output /output
```

---

## 🔑 Licensing & Plans *(v4.1.0)*

The project ships with a built-in HMAC-signed license system for self-hosted SaaS distribution:

| Plan | Events/month | Concurrent runs | Formats | Support |
|------|-------------|----------------|---------|---------|
| **FREE** | 5K (30-day trial) | 1 | JSONL, CSV | Community |
| **STARTER** | 5M | 3 | All formats | Email |
| **PRO** | 100M | 10 | All + priority | Priority |
| **TEAM** | Unlimited | Unlimited | All | Dedicated |
| **ENTERPRISE** | Unlimited | Unlimited | All + on-prem | Custom SLA |

Licenses are issued via the **FraudGen API Server** — a separate FastAPI service you run on your VPS that issues signed keys and receives heartbeats from running containers.

```bash
# Validate a license key (inside the container)
python -c "
from fraud_generator.licensing.validator import validate_license
validate_license('YOUR-LICENSE-KEY-HERE')
"
```

See [Licensing Guide](src/fraud_generator/licensing/) and [API Server docs](api/README.md).

---

## 🖥️ API Server (Self-Hosted) *(v4.1.0)*

Run the license issuance + telemetry server on your own VPS:

```bash
# Start the API server (separate Docker image)
docker-compose -f docker-compose.server.yml up -d

# Or directly with uvicorn
pip install -r requirements-api.txt
FRAUDGEN_SECRET_KEY=your-secret \
RESEND_API_KEY=re_xxxx \
uvicorn src.fraud_generator.api.app:app --host 0.0.0.0 --port 8000
```

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/register` | Register user, issue license, send email |
| `POST` | `/v1/heartbeat` | Container startup telemetry |
| `GET`  | `/v1/health` | Load balancer health check |
| `GET`  | `/v1/admin/licenses` | List issued licenses (admin only) |

```bash
# Register a new user (example)
curl -X POST https://api.yourdomain.com/v1/register \
  -H "Content-Type: application/json" \
  -d '{"email": "ml@fintech.com", "plan": "starter", "organization": "My Bank"}'
```

---

## 📊 What Data Do You Get?

### Banking Data (Default: `--type transactions`)

```json
{
  "transaction_id": "tx_1234567890",
  "customer_id": "12345678900",
  "timestamp": "2026-01-30T14:35:22",
  "amount": 1250.50,
  "transaction_type": "PIX",
  "pix_key_type": "CPF",
  "merchant_name": "Supermercado Pão de Açúcar",
  "mcc": "5411",
  "is_fraud": true,
  "fraud_type": "ACCOUNT_TAKEOVER",
  "fraud_score": 0.87,
  "impossible_travel": false,
  "transactions_last_24h": 12,
  "accumulated_value_24h": 5430.00
}
```

**Files Generated:**
- `customers.jsonl` - Brazilian customers with valid CPF
- `devices.jsonl` - Smartphones/tablets linked to customers
- `transactions_*.jsonl` - Financial transactions (~128MB each)

### Ride-Share Data (`--type rides`)

```json
{
  "ride_id": "ride_abc123",
  "passenger_id": "12345678900",
  "driver_id": "driver_xyz789",
  "timestamp": "2026-01-30T14:35:22",
  "app": "99",
  "category": "99Pop",
  "distance_km": 8.5,
  "duration_minutes": 22,
  "fare": 18.90,
  "surge_multiplier": 1.0,
  "is_fraud": false,
  "fraud_type": null
}
```

**Files Generated:**
- `customers.jsonl` - Passengers
- `devices.jsonl` - Passenger devices
- `drivers.jsonl` - Drivers with vehicles and ratings
- `rides_*.jsonl` - Ride trips (~128MB each)

---

## ⚡ Performance Benchmarks

| Metric | Batch (generate.py) | Streaming (stream.py) | Arrow IPC |
|--------|---------------------|----------------------|-----------|
| **Transactions/sec** | 56,000 - 385,000 | 100 - 10,000 | 2,500,000 |
| **Rides/sec** | 56,000 | 100 - 5,000 | 2,500,000 |
| **Memory Usage** | ~200MB (1GB dataset) | ~50MB | ~100MB |
| **1GB Generation Time** | ~3-10 seconds | N/A (streaming) | ~2 seconds |
| **10GB Generation Time** | ~30-100 seconds | N/A | ~20 seconds |

*Tested on: Intel i7-10700K, 32GB RAM, NVMe SSD*

See [Performance Guide](docs/MEMORY_OPTIMIZATION.md) for optimization tips.

---

## 🎨 Use Cases

### 1️⃣ Machine Learning Training
```bash
# Generate 10GB labeled fraud dataset
python generate.py --size 10GB --fraud-rate 0.05 --output ./ml_training
```

**What you get:** Balanced dataset with 5% fraud rate, behavioral profiles, temporal patterns.

### 2️⃣ Data Pipeline Testing
```bash
# Test Spark job with realistic data
python generate.py --size 5GB --format parquet --output ./pipeline_test
```

**What you get:** Parquet files ready for Spark/Hive ingestion.

### 3️⃣ Kafka Streaming
```bash
# Feed Kafka topic with 1000 events/sec
python stream.py --target kafka \
  --kafka-server kafka:9092 \
  --kafka-topic banking-transactions \
  --rate 1000
```

**What you get:** Real-time stream for Kafka Streams, Flink, or Spark Streaming.

### 4️⃣ Database Population
```bash
# Direct PostgreSQL insert
python generate.py --size 1GB --format postgres \
  --postgres-url postgresql://user:pass@localhost/frauddb
```

**What you get:** Populated database ready for SQL queries and analytics.

---

## 🔧 Advanced Configuration

### Behavioral Profiles (Default: Enabled)

Generate realistic spending patterns based on user archetypes:

| Profile | % Users | Characteristics |
|---------|---------|-----------------|
| `young_digital` | 25% | Heavy PIX, streaming, delivery apps |
| `subscription_heavy` | 20% | Netflix, Spotify, SaaS subscriptions |
| `family_provider` | 22% | Supermarket, utilities, education |
| `traditional_senior` | 15% | ATM, pharmacies, physical stores |
| `business_owner` | 10% | B2B, high-value, wholesale |
| `high_spender` | 8% | Luxury, travel, premium services |

```bash
# Enable profiles (default)
python generate.py --size 1GB --output ./data

# Disable for random transactions
python generate.py --size 1GB --no-profiles --output ./data
```

### Fraud Types Distribution

**Banking Fraud (13 types):**
- Social Engineering (20%)
- Account Takeover (16%)
- Card Cloning (15%)
- Identity Fraud (10%)
- First-Party Fraud (8%)
- Friendly Fraud (6%)
- Money Laundering (4%)
- WhatsApp Scams (8%)
- Phishing (6%)
- SIM Swap (3%)
- Fake Boletos (2%)
- Fake QR Codes (2%)
- Device Spoofing (2%)

**Ride-Share Fraud (4 types):**
- GPS Spoofing (40%)
- Fake Rides (30%)
- Driver Collusion (20%)
- Payment Fraud (10%)

### Custom Parameters

```bash
# Banking with custom fraud rate
python generate.py --size 2GB \
  --type transactions \
  --fraud-rate 0.10 \
  --output ./high_fraud_data

# Ride-share with specific seed (reproducible)
python generate.py --size 500MB \
  --type rides \
  --seed 42 \
  --output ./rides_data

# Both domains
python generate.py --size 1GB \
  --type all \
  --fraud-rate 0.03 \
  --output ./complete_data

# Custom date range
python generate.py --size 1GB \
  --start-date 2025-01-01 \
  --end-date 2025-12-31 \
  --output ./yearly_data
```

---

## 📦 Export Formats

| Format | File Extension | Use Case | Compression |
|--------|---------------|----------|-------------|
| **JSON Lines** | `.jsonl` | Default, human-readable | None |
| **CSV** | `.csv` | Spreadsheets, BI tools | None |
| **Parquet** | `.parquet` | Spark, Hive, columnar analytics | Snappy |
| **Arrow IPC** | `.arrow` | Ultra-fast, in-memory processing | LZ4/ZSTD |
| **PostgreSQL** | N/A | Direct database insert | N/A |
| **SQLite** | `.db` | Local analytics, testing | N/A |
| **DuckDB** | `.duckdb` | OLAP queries, Python analytics | N/A |
| **MinIO/S3** | `.jsonl/.csv/.parquet` | Cloud storage, data lakes | Configurable |

```bash
# Export to Parquet
python generate.py --size 1GB --format parquet --output ./data

# Export to Arrow IPC (fastest)
python generate.py --size 1GB --format arrow --output ./data

# Export to PostgreSQL
python generate.py --size 1GB --format postgres \
  --postgres-url postgresql://localhost/mydb \
  --postgres-table transactions

# Export to MinIO
python generate.py --size 1GB --format minio \
  --minio-url s3://my-bucket/fraud-data/ \
  --minio-access-key minioadmin \
  --minio-secret-key minioadmin
```

---

## 🏗️ Architecture

### Project Structure

```
brazilian-fraud-data-generator/
├── 📄 README.md                    # This file
├── 📄 LICENSE                      # MIT License
├── 📄 VERSION                      # Current version (4.1.0 "Guaraná")
├── 📄 requirements.txt             # Core dependencies
├── 📄 requirements-streaming.txt   # Kafka / webhook streaming
├── 📄 requirements-api.txt         # API server (FastAPI, Resend)
├── 🐍 generate.py                  # Main batch generator (SOLID CLI v4.1.0)
├── 🐍 stream.py                    # Real-time streaming
├── 🐍 validate_realism.py          # Data realism validation tool ✨
├── 🐍 check_schema.py              # Schema validation utility
├── 🐳 Dockerfile                   # Generator Docker image
├── 🐳 Dockerfile.server            # API server Docker image ✨
├── 🐳 docker-compose.yml           # Generator + Kafka compose
├── 🐳 docker-compose.server.yml    # API server compose ✨
│
├── 📂 landpage/                    # Landing page (HTML/CSS) ✨
│   ├── index.html                  # Marketing landing page
│   └── styles.css
│
├── 📂 schemas/                     # Declarative JSON schemas ✨
│   ├── banking_full.json           # Full banking schema (all fields)
│   ├── banking_minimal.json        # Minimal banking schema
│   ├── rideshare_full.json         # Full ride-share schema
│   └── custom_empresa.json         # Example custom schema
│
├── 📂 admin_tools/                 # Admin utilities ✨
│   └── issue_license.py            # CLI tool to issue license keys
│
├── 📂 api/                         # API documentation & config ✨
│   └── README.md
│
├── 📂 src/fraud_generator/         # Core library
│   ├── __init__.py
│   ├── config/                     # Static configs
│   │   ├── banks.py                # Brazilian banks + weights
│   │   ├── merchants.py            # MCC codes + merchants
│   │   ├── geography.py            # States, cities, coordinates
│   │   ├── transactions.py         # Transaction type configs
│   │   ├── rideshare.py            # Ride-share apps + categories
│   │   ├── weather.py              # Weather impact on rides
│   │   └── seasonality.py         # Hourly/daily/annual patterns ✨
│   ├── models/                     # Pydantic data models
│   │   ├── customer.py
│   │   ├── device.py
│   │   ├── transaction.py
│   │   └── ride.py
│   ├── generators/                 # Core data generators
│   │   ├── customer.py
│   │   ├── device.py
│   │   ├── transaction.py
│   │   ├── driver.py
│   │   └── ride.py
│   ├── exporters/                  # Output format handlers
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   ├── parquet_exporter.py
│   │   └── minio_exporter.py
│   ├── connections/                # Streaming connections
│   │   └── (kafka, webhook, stdout)
│   ├── profiles/                   # Behavioral profiles
│   │   ├── behavioral.py           # 7 customer archetypes
│   │   └── ride_behavioral.py      # Ride-share profiles
│   ├── validators/                 # Data validation
│   │   └── cpf.py                  # CPF algorithm validation
│   ├── schema/                     # Schema parsing & inference ✨
│   ├── cli/                        # SOLID CLI module (v4.1.0) ✨
│   │   ├── args.py                 # Argument parser
│   │   ├── constants.py
│   │   ├── index_builder.py
│   │   └── runners/                # BatchRunner, MinioRunner, SchemaRunner
│   ├── licensing/                  # License model & enforcement ✨
│   │   ├── license.py              # Plans, HMAC signing, LicensePlan enum
│   │   ├── validator.py            # Key validation at runtime
│   │   └── limits.py               # Per-plan limit enforcement
│   ├── api/                        # FastAPI license server ✨
│   │   └── app.py                  # /register, /heartbeat, /health
│   ├── email/                      # Email delivery via Resend ✨
│   │   └── resend_client.py        # send_welcome_email, send_license_email
│   └── utils/
│       ├── helpers.py
│       ├── streaming.py
│       ├── parallel.py             # ProcessPoolExecutor utils ✨
│       └── precompute.py           # Pre-cached weight tables ✨
│
├── 📂 docs/                        # Documentation
│   ├── README.md                   # Full documentation index
│   ├── README.pt-BR.md             # Portuguese docs
│   ├── CHANGELOG.md                # Version history
│   ├── ARQUITETURA.md              # Architecture deep-dive ✨
│   ├── ROADMAP_TECNICO_DETALHADO.md # Technical roadmap ✨
│   ├── PRICING_ANALYSIS_COMPLETO.md # Pricing & business analysis ✨
│   ├── PLANO_MONETIZACAO_EXECUTIVO_90DIAS.md # 90-day monetization plan ✨
│   ├── ANALISE_SHADOWTRAFFIC_VS_SEU_PROJETO.md # Competitive analysis ✨
│   ├── ANALISE_COMPLETA_PROJETO.md # Full project analysis ✨
│   ├── CAPACITY_PLANNING.md        # Infrastructure sizing ✨
│   ├── MEMORY_OPTIMIZATION.md      # Performance tuning
│   ├── SHADOWTRAFFIC_ANALYSIS.md   # ShadowTraffic research
│   ├── DOCKER_HUB_PUBLISHING.md    # Docker release guide
│   └── benchmarks/                 # Performance benchmarks
│
├── 📂 tests/                       # Test suite
│   ├── unit/
│   │   └── test_licensing.py       # License validation tests ✨
│   └── integration/
│
└── 📂 examples/                    # Usage examples
    └── README.md
```

> ✨ = Added in v4.1.0

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│  generate.py (CLI)  │  stream.py (CLI)  │  Docker Container │
└──────────────┬────────────────┬─────────────────────────────┘
               │                │
               ▼                ▼
┌──────────────────────────────────────────────────────────────┐
│                   Core Generator Library                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Customer   │  │  Device     │  │ Transaction │          │
│  │  Generator  │  │  Generator  │  │  Generator  │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                   │
│         └────────────────┴────────────────┘                   │
│                          │                                    │
│                ┌─────────▼──────────┐                         │
│                │ Behavioral Profiles │                        │
│                │  Fraud Injection    │                        │
│                └─────────┬──────────┘                         │
└──────────────────────────┼──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌─────────────────┐      ┌──────────────────┐
    │   Exporters     │      │   Connections    │
    │  (File-based)   │      │  (Real-time)     │
    ├─────────────────┤      ├──────────────────┤
    │ • JSON          │      │ • Kafka          │
    │ • CSV           │      │ • Webhook        │
    │ • Parquet       │      │ • Stdout         │
    │ • Arrow IPC     │      └──────────────────┘
    │ • PostgreSQL    │
    │ • SQLite        │
    │ • DuckDB        │
    │ • MinIO/S3      │
    └─────────────────┘
```

---

## 🔐 Data Validation & Quality

### CPF Validation
All customer CPFs are **valid** with correct check digits:
```python
from fraud_generator.validators.cpf import validate_cpf, generate_valid_cpf

cpf = generate_valid_cpf()  # "12345678909"
assert validate_cpf(cpf)    # True
```

### Data Consistency
- ✅ Transactions reference existing customers/devices
- ✅ Rides reference existing drivers/passengers
- ✅ Geolocation correlates with customer state
- ✅ Transaction amounts match MCC typical ranges
- ✅ Timestamps respect Brazilian timezone (UTC-3)
- ✅ Fraud patterns have realistic risk indicators

### Schema Validation
```bash
# Validate generated data against schema
python check_schema.py --input ./output/transactions_0.jsonl
```

---

## 🐳 Docker Usage

### Pre-built Image (Recommended)

```bash
# Pull from Docker Hub
docker pull afborda/brazilian-fraud-data-generator:latest

# Generate data
docker run --rm \
  -v $(pwd)/output:/output \
  afborda/brazilian-fraud-data-generator:latest \
  generate.py --size 1GB --output /output
```

### Build Locally

```bash
# Build image
docker build -t fraud-generator .

# Run
docker run --rm -v $(pwd)/output:/output fraud-generator \
  generate.py --size 500MB --format parquet --output /output
```

### Docker Compose (with Kafka)

```bash
# Start Kafka + Generator
docker-compose up -d

# Stream to Kafka
docker-compose run generator \
  stream.py --target kafka --kafka-server kafka:9092 --rate 100
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=src/fraud_generator --cov-report=html
```

### Test Results (v4.0.0)
- ✅ 72 tests passing
- ⚠️ 3 tests skipped (optional dependencies)
- ❌ 7 legacy tests (non-critical)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repo
git clone https://github.com/afborda/brazilian-fraud-data-generator.git
cd brazilian-fraud-data-generator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-streaming.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/

# Format code
black src/ tests/
```

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

**TL;DR:** You can use this for commercial projects, modify it, and distribute it. Just include the original license.

---

## 👤 Author

**Abner Fonseca Borda**

- GitHub: [@afborda](https://github.com/afborda)
- LinkedIn: [Abner Fonseca Borda](https://www.linkedin.com/in/afborda/)

---

## ⭐ Star History

If this project helped you, please consider giving it a ⭐!

---

## 🙏 Acknowledgments

- **Faker** library for realistic Brazilian data generation
- **Apache Arrow** for high-performance columnar format
- **Kafka** ecosystem for real-time streaming
- **Brazilian fintech community** for fraud pattern insights

---

## 📊 Project Status

**Current Version:** 4.1.0 "Guaraná"
**Status:** ✅ Production Ready · 🚧 SaaS Launch In Progress
**Last Updated:** March 4, 2026

### v4.1.0 "Guaraná" — What's New

| Feature | Status | Module |
|---------|--------|--------|
| SOLID CLI refactor (runners, workers pool) | ✅ Done | `src/fraud_generator/cli/` |
| Declarative JSON schema mode | ✅ Done | `schemas/`, `src/fraud_generator/schema/` |
| HMAC-signed licensing system | ✅ Done | `src/fraud_generator/licensing/` |
| FastAPI license server | ✅ Done | `src/fraud_generator/api/` |
| Email delivery via Resend | ✅ Done | `src/fraud_generator/email/` |
| Seasonality config (hourly/daily/annual) | ✅ Done | `src/fraud_generator/config/seasonality.py` |
| Pre-cached weight tables (P2 perf fix) | ✅ Done | `src/fraud_generator/utils/precompute.py` |
| Parallel worker utilities | ✅ Done | `src/fraud_generator/utils/parallel.py` |
| API server Dockerfile + Compose | ✅ Done | `Dockerfile.server`, `docker-compose.server.yml` |
| Landing page (HTML/CSS) | ✅ Done | `landpage/` |
| Admin license issuance CLI | ✅ Done | `admin_tools/issue_license.py` |
| Realism validation tool | ✅ Done | `validate_realism.py` |
| Pricing & business analysis docs | ✅ Done | `docs/PRICING_ANALYSIS_COMPLETO.md` |

### v4.0.0 "Quantum" — Previous Release

- ✨ State machines for fraud sequences
- ✨ Impossible travel detection
- ✨ Arrow IPC export format (+790% performance)
- ✨ Database exports (PostgreSQL, SQLite, DuckDB)
- ✨ Async streaming with semaphore concurrency
- ✨ Batch CSV optimization (+40% speed)
- ✨ Customer session state tracking

See [CHANGELOG](docs/CHANGELOG.md) for complete version history.

---

## 📚 Documentation

| Document | Language | Description |
|----------|----------|-------------|
| [docs/README.md](docs/README.md) | EN | Full feature guide |
| [docs/README.pt-BR.md](docs/README.pt-BR.md) | PT-BR | Documentação completa |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | PT-BR | Arquitetura do sistema |
| [docs/ROADMAP_TECNICO_DETALHADO.md](docs/ROADMAP_TECNICO_DETALHADO.md) | PT-BR | Roadmap técnico detalhado |
| [docs/PRICING_ANALYSIS_COMPLETO.md](docs/PRICING_ANALYSIS_COMPLETO.md) | PT-BR | Análise de precificação (Brasil + Mundo) |
| [docs/PLANO_MONETIZACAO_EXECUTIVO_90DIAS.md](docs/PLANO_MONETIZACAO_EXECUTIVO_90DIAS.md) | PT-BR | Plano de monetização 90 dias |
| [docs/ANALISE_SHADOWTRAFFIC_VS_SEU_PROJETO.md](docs/ANALISE_SHADOWTRAFFIC_VS_SEU_PROJETO.md) | PT-BR | Análise competitiva vs. ShadowTraffic |
| [docs/CAPACITY_PLANNING.md](docs/CAPACITY_PLANNING.md) | PT-BR | Planejamento de infraestrutura |
| [docs/MEMORY_OPTIMIZATION.md](docs/MEMORY_OPTIMIZATION.md) | EN | Performance tuning guide |
| [docs/SHADOWTRAFFIC_ANALYSIS.md](docs/SHADOWTRAFFIC_ANALYSIS.md) | PT-BR | ShadowTraffic deep-dive |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | EN | Version history |

---

## 🗺️ Roadmap

### ✅ Completed (v4.0.0 + v4.1.0)

- [x] SOLID CLI refactor with pluggable runners
- [x] Declarative JSON schema generation mode
- [x] HMAC-signed license keys + plan enforcement
- [x] FastAPI license server (register / heartbeat / health)
- [x] Seasonality: trimodal hourly + Black Friday / Carnaval events
- [x] Pre-cached weight tables (eliminates 25% `random.choices()` overhead)
- [x] Parallel worker pool (`ProcessPoolExecutor`)
- [x] Arrow IPC export (+790% vs JSONL)
- [x] Database exports (PostgreSQL, SQLite, DuckDB)
- [x] State machine fraud sequences
- [x] Impossible travel detection
- [x] Customer session state (24h window)
- [x] Landing page (marketing)
- [x] API server Docker image

### 🔜 In Progress (v4.2.0 — next)

- [ ] **CSV/Parquet streaming export** — fix OOM on >1GB (P3 known issue)
- [ ] **Stripe integration** — webhook → auto-license issuance on payment
- [ ] **Web UI (Streamlit)** — no-CLI generation interface for non-engineers
- [ ] **Fraud velocity sequences** — multi-step fraud journeys (recon → probe → attack)
- [ ] **Fraud networks** — money mule graph, triangulation patterns

### 📋 Planned (v5.0.0+)

- [ ] **GraphQL API** — on-demand generation endpoint
- [ ] **Kubernetes Helm chart** — production-grade deployment
- [ ] **ML auto-training** — generate dataset → train XGBoost baseline automatically
- [ ] **LATAM expansion** — Mexican peso, Colombian peso, Argentine peso context
- [ ] **Open Telemetry** — metrics & tracing for enterprise deployments
- [ ] **Fraud pattern marketplace** — downloadable pre-generated fraud scenario datasets

See [ROADMAP_TECNICO_DETALHADO.md](docs/ROADMAP_TECNICO_DETALHADO.md) for full technical detail.

---

<div align="center">

**Made with ❤️ for the Brazilian Data Engineering & ML Community**

[⬆ Back to Top](#-brazilian-fraud-data-generator)

</div>
