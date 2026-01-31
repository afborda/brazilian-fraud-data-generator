# 🇧🇷 Brazilian Fraud Data Generator

<div align="center">

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/afborda/brazilian-fraud-data-generator)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Kafka](https://img.shields.io/badge/Kafka-Streaming-231F20?logo=apachekafka)](docs/README.md#streaming-real-time)

**Production-Grade Synthetic Data Generator for Brazilian Banking & Ride-Share Fraud Detection**

*Generate realistic fraud scenarios for ML training, pipeline testing, and system validation*

[📖 Full Documentation](docs/README.md) • [🇧🇷 Português](docs/README.pt-BR.md) • [🔄 CHANGELOG](docs/CHANGELOG.md) • [🐳 Docker Hub](https://hub.docker.com/r/afborda/brazilian-fraud-data-generator)

</div>

---

## 🎯 What is this?

A high-performance **synthetic data generator** specifically designed for **Brazilian financial fraud detection**:

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

✅ **High Performance**
- **56k-385k transactions/second** (batch mode)
- **2.5M records/second** (Arrow IPC format)
- Multi-format export: JSON, CSV, Parquet, Arrow IPC, PostgreSQL, SQLite, DuckDB
- Memory-efficient streaming for TB-scale datasets

✅ **Production Ready**
- Real-time streaming to Kafka, webhooks
- Docker containerized
- Reproducible with seed support
- Async/parallel processing

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

### Option 2: Real-Time Streaming

```bash
# 1. Install streaming deps
pip install -r requirements-streaming.txt

# 2. Stream to Kafka (100 transactions/sec)
python stream.py --target kafka \
  --kafka-server localhost:9092 \
  --rate 100

# Or stream to stdout for testing
python stream.py --target stdout --rate 5
```

### Option 3: Docker (Zero Install)

```bash
docker run --rm -v $(pwd)/output:/output \
  afborda/brazilian-fraud-data-generator:latest \
  generate.py --size 500MB --output /output
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
├── 📄 README.md                   # This file
├── 📄 LICENSE                     # MIT License
├── 📄 VERSION                     # Current version (4.0.0)
├── 📄 requirements.txt            # Core dependencies
├── 📄 requirements-streaming.txt  # Streaming dependencies
├── 🐍 generate.py                 # Main batch generator
├── 🐍 stream.py                   # Real-time streaming
├── 🐍 check_schema.py             # Schema validation utility
├── 🐳 Dockerfile                  # Docker image
├── 🐳 docker-compose.yml          # Docker Compose setup
│
├── 📂 src/fraud_generator/        # Core library
│   ├── config/                    # Static configs (banks, MCCs, states)
│   ├── models/                    # Data models (Customer, Transaction, Ride)
│   ├── generators/                # Data generators
│   ├── exporters/                 # Export format handlers
│   ├── connections/               # Streaming connections (Kafka, webhook)
│   ├── profiles/                  # Behavioral profiles
│   ├── validators/                # CPF, data validation
│   └── utils/                     # Helper utilities
│
├── 📂 docs/                       # Documentation
│   ├── README.md                  # Detailed documentation
│   ├── README.pt-BR.md            # Portuguese docs
│   ├── CHANGELOG.md               # Version history
│   ├── MEMORY_OPTIMIZATION.md     # Performance tuning
│   ├── SHADOWTRAFFIC_ANALYSIS.md  # Competitive analysis
│   ├── DOCKER_HUB_PUBLISHING.md   # Docker release guide
│   └── benchmarks/                # Performance benchmarks
│
├── 📂 tests/                      # Test suite
│   ├── unit/                      # Unit tests
│   └── integration/               # Integration tests
│
└── 📂 examples/                   # Usage examples
    └── README.md                  # Example scenarios
```

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

## 📚 Documentation

- **[Full Documentation](docs/README.md)** - Complete guide with all features
- **[Portuguese Docs](docs/README.pt-BR.md)** - Documentação completa em português
- **[CHANGELOG](docs/CHANGELOG.md)** - Version history and release notes
- **[Performance Guide](docs/MEMORY_OPTIMIZATION.md)** - Optimization techniques
- **[Phase 2 Guide](docs/PHASE_2_GUIDE.md)** - Advanced features (v4.0.0)
- **[Docker Publishing](docs/DOCKER_HUB_PUBLISHING.md)** - Release process
- **[Competitive Analysis](docs/SHADOWTRAFFIC_ANALYSIS.md)** - vs ShadowTraffic

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

**Current Version:** 4.0.0 "Quantum"  
**Status:** ✅ Production Ready  
**Last Updated:** January 30, 2026

### Recent Updates (v4.0.0)
- ✨ State machines for fraud sequences
- ✨ Impossible travel detection
- ✨ Arrow IPC export format (+790% performance)
- ✨ Database exports (PostgreSQL, SQLite, DuckDB)
- ✨ Redis caching for distributed generation
- ✨ Async streaming with semaphore concurrency
- ✨ Batch CSV optimization (+40% speed)
- ✨ Customer session state tracking

See [CHANGELOG](docs/CHANGELOG.md) for complete version history.

---

## 🗺️ Roadmap

### Planned Features (Phase 3)

- [ ] **State Machines for Fraud Journeys** - Model fraud as sequences (reconnaissance → attempt → detection)
- [ ] **Geolocation Validation** - Impossible travel detection (SP → MG in 5 minutes = fraud)
- [ ] **Temporal Scheduling** - Black Friday peaks, weekend patterns, hourly variance
- [ ] **Fraud Networks** - Money mule networks, triangulation patterns
- [ ] **GraphQL API** - REST/GraphQL endpoints for on-demand generation
- [ ] **Web UI** - Streamlit/Gradio interface for non-technical users
- [ ] **ML Model Integration** - Auto-train fraud detection models
- [ ] **Kubernetes Deployment** - Helm charts for production deployment

See [GitHub Issues](https://github.com/afborda/brazilian-fraud-data-generator/issues) for detailed roadmap.

---

<div align="center">

**Made with ❤️ for the Brazilian Data Engineering & ML Community**

[⬆ Back to Top](#-brazilian-fraud-data-generator)

</div>
