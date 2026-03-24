# 🇧🇷 synthfin-data

<div align="center">

[![en](https://img.shields.io/badge/lang-en-red.svg)](./README.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](./README.pt-BR.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
[![Docker Hub](https://img.shields.io/docker/v/afborda/synthfin-data?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/afborda/synthfin-data)
[![Docker Pulls](https://img.shields.io/docker/pulls/afborda/synthfin-data?logo=docker)](https://hub.docker.com/r/afborda/synthfin-data)
![Kafka](https://img.shields.io/badge/Kafka-Streaming-231F20?logo=apachekafka&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3-C72E49?logo=minio&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

**Generate realistic Brazilian banking and ride-share data for Data Engineering & ML**

</div>

---

## 🎯 What is this?

A tool to generate **synthetic Brazilian data** for:
- 🏦 **Banking transactions** (PIX, cards, TED, boleto)
- 🚗 **Ride-share trips** (Uber, 99, Cabify, InDriver)
- 🔴 **Fraud detection** training and testing

Perfect for: **Data pipelines**, **Spark jobs**, **Kafka streaming**, **ML models**, **API testing**

---

## 🚀 5-Minute Quick Start

### A) Batch (files on disk)
1. Install deps (once):
  ```bash
  git clone https://github.com/afborda/synthfin-data.git
  cd synthfin-data
  pip install -r requirements.txt
  ```
2. Generate 100MB of banking data locally:
  ```bash
  python3 generate.py --size 100MB --output ./my_data
  ```
3. Open the files in `./my_data` (customers, devices, transactions).

### B) Streaming (real time)
1. Install streaming deps (once):
  ```bash
  pip install -r requirements-streaming.txt
  ```
2. Stream to terminal (transactions, 5 events/sec):
  ```bash
  python3 stream.py --target stdout --rate 5
  ```
3. Stream to Kafka (transactions):
  ```bash
  python3 stream.py --target kafka --kafka-server localhost:9092 --rate 100
  ```
  For rides, add `--type rides` (topic defaults to `rides`).

### C) Docker (no local Python needed)
```bash
docker run --rm -v $(pwd)/output:/output afborda/synthfin-data:latest \
   generate.py --size 1GB --output /output
```

---

## 📖 Data Types: Banking vs Ride-Share

This generator supports **two different types** of data:

| Type | Command | What it generates | Fraud types |
|------|---------|-------------------|-------------|
| 💳 **Banking** | `--type transactions` | PIX, cards, TED, boleto | Card cloning, account takeover, social engineering |
| 🚗 **Ride-Share** | `--type rides` | Uber, 99, Cabify, InDriver trips | GPS spoofing, fake rides, driver collusion |
| 🔄 **Both** | `--type all` | All of the above | All fraud types |

### Output Files by Type

```bash
# Banking (default): --type transactions
output/
├── customers.jsonl          # 👥 Bank customers
├── devices.jsonl            # 📱 Customer devices
└── transactions_*.jsonl     # 💳 Banking transactions

# Ride-Share: --type rides
output/
├── customers.jsonl          # 👥 Passengers
├── devices.jsonl            # 📱 Passenger devices
├── drivers.jsonl            # 🚘 Drivers with vehicles
└── rides_*.jsonl            # 🚗 Ride-share trips

# Both: --type all
output/
├── customers.jsonl          # 👥 Customers/Passengers
├── devices.jsonl            # 📱 Devices
├── drivers.jsonl            # 🚘 Drivers
├── transactions_*.jsonl     # 💳 Banking transactions
└── rides_*.jsonl            # 🚗 Ride-share trips
```

---

## 📖 Usage Examples

### 🔹 Batch Mode (Generate Files)

| Goal | Command |
|------|---------|
| Generate 1GB of transactions | `python3 generate.py --size 1GB` |
| Generate in CSV format | `python3 generate.py --size 500MB --format csv` |
| Generate in Parquet | `python3 generate.py --size 1GB --format parquet` |
| Generate ride-share data | `python3 generate.py --size 1GB --type rides` |
| Generate both (transactions + rides) | `python3 generate.py --size 1GB --type all` |
| Higher fraud rate (5%) | `python3 generate.py --size 1GB --fraud-rate 0.05` |
| Reproducible data (seed) | `python3 generate.py --size 1GB --seed 42` |
| Faster with 16 workers | `python3 generate.py --size 10GB --workers 16` |

#### 🗜️ Parquet Compression Options

When using `--format parquet`, you can choose the compression algorithm:

| Compression | Command | Best For |
|-------------|---------|----------|
| **ZSTD** (default) | `--compression zstd` | Best compression ratio, recommended |
| Snappy | `--compression snappy` | Faster, legacy compatibility |
| Gzip | `--compression gzip` | Maximum compatibility |
| Brotli | `--compression brotli` | High compression |
| None | `--compression none` | No compression |

```bash
# Default: ZSTD (best compression/speed ratio, ~91% smaller than JSONL)
python3 generate.py --size 1GB --format parquet

# Use Snappy for legacy systems or Spark < 2.4
python3 generate.py --size 1GB --format parquet --compression snappy

# Maximum compression with Gzip
python3 generate.py --size 1GB --format parquet --compression gzip
```

> **💡 Note:** ZSTD is the default because it offers the best balance of compression ratio and speed. 
> If your system doesn't support ZSTD (older Spark, Hive, or Presto versions), use `--compression snappy`.

#### 🗜️ JSONL Compression Options (New!)

For JSONL, you can enable gzip compression to save storage:

| Option | Command | Benefit | Cost |
|--------|---------|---------|------|
| No compression (default) | `--jsonl-compress none` | Maximum speed | Large file |
| **Gzip** | `--jsonl-compress gzip` | -85% file size | -18% speed |

```bash
# Default: JSONL without compression (28.0k records/sec)
python3 generate.py --size 1GB --format jsonl

# JSONL compressed with gzip (22.9k records/sec, 30MB vs 206MB)
python3 generate.py --size 1GB --format jsonl --jsonl-compress gzip

# MinIO with gzip: direct upload compressed
python3 generate.py --size 1GB --output minio://bucket/path --format jsonl --jsonl-compress gzip
```

**Practical examples:**
- **Backups/History:** Use `--jsonl-compress gzip` (save -85%)
- **Training sets on S3:** Use `--jsonl-compress gzip` (save bandwidth)
- **Real-time processing:** Use default no compression (maximum speed)

> **💡 Recommendation:** Enable compression if you need to store or transfer data.
> Disable if generation speed is critical or the file will be processed immediately.

### 🔹 Streaming Mode (Real-time)

First, install streaming dependencies:
```bash
pip install -r requirements-streaming.txt
```

| Goal | Command |
|------|---------|
| Test in terminal (5/sec) | `python3 stream.py --target stdout --rate 5` |
| Stream to Kafka | `python3 stream.py --target kafka --kafka-server localhost:9092 --rate 100` |
| Stream rides to Kafka | `python3 stream.py --target kafka --type rides --kafka-topic rides --rate 50` |
| Stream to REST API | `python3 stream.py --target webhook --webhook-url http://api:8080/ingest` |
| Limited events (1000) | `python3 stream.py --target stdout --max-events 1000` |

#### 📊 Understanding `--rate` (Events per Second)

| Rate | Meaning | Use Case |
|------|---------|----------|
| `--rate 1` | 1 event/sec (1 per 1000ms) | Debug/Testing |
| `--rate 10` | 10 events/sec (1 per 100ms) | Development |
| `--rate 100` | 100 events/sec (1 per 10ms) | Production |
| `--rate 1000` | 1000 events/sec (1 per 1ms) | Stress test |

**Real-time output shows actual throughput:**
```
📊 Events: 1,000 | Rate: 99.6/s | Errors: 0
```

### 🔹 Docker Mode

#### Using Docker Hub (Recommended)

```bash
# Pull the latest version
docker pull afborda/synthfin-data:latest

# Generate 1GB of transactions
docker run --rm -v $(pwd)/output:/output afborda/synthfin-data:latest \
    generate.py --size 1GB --output /output

# Generate in Parquet format
docker run --rm -v $(pwd)/output:/output afborda/synthfin-data:latest \
    generate.py --size 500MB --output /output --format parquet

# Generate ride-share data
docker run --rm -v $(pwd)/output:/output afborda/synthfin-data:latest \
    generate.py --size 1GB --type rides --output /output

# Streaming to Kafka
docker run --rm --network host afborda/synthfin-data:latest \
    stream.py --target kafka --kafka-server localhost:9092 --rate 100
```

#### Using Local Build

```bash
# Build the image locally
docker build -t fraud-generator .

# Batch: Generate 1GB
docker run --rm -v $(pwd)/output:/output fraud-generator \
    generate.py --size 1GB --output /output

# Streaming to Kafka
docker run --rm --network host fraud-generator \
    stream.py --target kafka --kafka-server localhost:9092 --rate 100
```

### 🔹 MinIO/S3 Direct Upload

Upload directly to MinIO or S3-compatible storage:

```bash
# Upload to MinIO bucket
python3 generate.py --size 1GB \
    --output minio://fraud-data/raw \
    --minio-endpoint http://localhost:9000 \
    --minio-access-key minioadmin \
    --minio-secret-key minioadmin

# Or use environment variables
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ROOT_USER=minioadmin
export MINIO_ROOT_PASSWORD=minioadmin

python3 generate.py --size 1GB --output minio://fraud-data/raw
```

---

## 📊 What Data is Generated?

### 👥 Customers

```json
{
  "customer_id": "CUST_000000000001",
  "name": "Maria Silva Santos",
  "cpf": "123.456.789-09",
  "email": "maria.silva@email.com.br",
  "phone": "(11) 98765-4321",
  "birth_date": "1985-03-15",
  "address": {
    "city": "São Paulo",
    "state": "SP",
    "postal_code": "01310-100"
  },
  "monthly_income": 5500.00,
  "bank_name": "Nubank",
  "behavioral_profile": "young_digital"
}
```

### 💳 Transactions

```json
{
  "transaction_id": "TXN_000000000000001",
  "customer_id": "CUST_000000000001",
  "timestamp": "2024-03-15T14:32:45",
  "type": "PIX",
  "amount": 150.00,
  "merchant_name": "Carrefour",
  "is_fraud": false,
  "fraud_type": null,
  "fraud_score": 12.5
}
```

### 🚗 Rides

```json
{
  "ride_id": "RIDE_000000000001",
  "timestamp": "2024-03-15T14:32:45",
  "app": "UBER",
  "category": "UberX",
  "driver_id": "DRV_0000000001",
  "passenger_id": "CUST_000000000001",
  "pickup_location": { "city": "São Paulo", "state": "SP" },
  "dropoff_location": { "city": "São Paulo", "state": "SP" },
  "distance_km": 8.5,
  "final_fare": 27.75,
  "payment_method": "PIX",
  "is_fraud": false
}
```

### 🚘 Drivers

```json
{
  "driver_id": "DRV_0000000001",
  "name": "João Carlos Silva",
  "cpf": "987.654.321-00",
  "vehicle_plate": "ABC1D23",
  "vehicle_model": "HB20",
  "rating": 4.85,
  "active_apps": ["UBER", "99"],
  "operating_city": "São Paulo"
}
```

---

## 🔴 Fraud Types

### Transaction Frauds (13 types)

| Type | Description |
|------|-------------|
| `ENGENHARIA_SOCIAL` | Phone/WhatsApp scams |
| `CONTA_TOMADA` | Account takeover |
| `CARTAO_CLONADO` | Cloned card |
| `IDENTIDADE_FALSA` | Fake documents |
| `SIM_SWAP` | SIM card fraud |
| `TESTE_CARTAO` | Card testing |
| `LAVAGEM_DINHEIRO` | Money laundering |
| ... | + 6 more |

### Ride Frauds (7 types)

| Type | Description |
|------|-------------|
| `GPS_SPOOFING` | Fake GPS to increase distance |
| `DRIVER_COLLUSION` | Driver-passenger fake rides |
| `SURGE_ABUSE` | Artificial surge pricing |
| `PROMO_ABUSE` | Promotional code abuse |
| `FAKE_RIDE` | Fake ride for payout |
| `IDENTITY_FRAUD` | Fake driver/passenger identity |
| `PAYMENT_FRAUD` | Stolen payment methods |

---

## ⚙️ All Parameters

### generate.py (Batch Mode)

```bash
python3 generate.py --help
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--size`, `-s` | `1GB` | Target size: `100MB`, `1GB`, `50GB` |
| `--type`, `-t` | `transactions` | `transactions`, `rides`, or `all` |
| `--output`, `-o` | `./output` | Output dir or `minio://bucket/prefix` |
| `--format`, `-f` | `jsonl` | `jsonl`, `csv`, `parquet` |
| `--fraud-rate`, `-r` | `0.02` | Fraud rate (0.0 to 1.0) |
| `--workers`, `-w` | `CPU cores` | Parallel workers |
| `--seed` | None | Seed for reproducibility |
| `--customers`, `-c` | Auto | Number of customers |
| `--start-date` | -1 year | Start date (YYYY-MM-DD) |
| `--end-date` | today | End date (YYYY-MM-DD) |
| `--no-profiles` | - | Disable behavioral profiles |
| `--compression` | `zstd` | Parquet compression: `zstd`, `snappy`, `gzip`, `brotli`, `none` |
| `--jsonl-compress` | `none` | JSONL compression: `none` or `gzip` |
| `--minio-endpoint` | env | MinIO/S3 endpoint URL |
| `--minio-access-key` | env | MinIO access key |
| `--minio-secret-key` | env | MinIO secret key |

### stream.py (Streaming Mode)

```bash
python3 stream.py --help
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--target`, `-t` | Required | `stdout`, `kafka`, `webhook` |
| `--type` | `transactions` | `transactions` or `rides` |
| `--rate`, `-r` | `10` | Events per second |
| `--max-events`, `-n` | ∞ | Stop after N events |
| `--customers`, `-c` | `1000` | Customer pool size |
| `--fraud-rate` | `0.02` | Fraud rate |
| `--kafka-server` | `localhost:9092` | Kafka bootstrap server |
| `--kafka-topic` | `transactions` | Kafka topic |
| `--webhook-url` | - | Webhook endpoint |
| `--quiet`, `-q` | - | Suppress progress output |

---

## 🐳 Docker Compose (Full Stack)

Run with Kafka included:

```yaml
# docker-compose.yml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on: [zookeeper]
    ports: ["9092:9092"]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT

  fraud-generator:
    build: .
    depends_on: [kafka]
    command: >
      python3 stream.py 
        --target kafka 
        --kafka-server kafka:29092 
        --kafka-topic transactions 
        --rate 10
```

```bash
docker-compose up -d
docker-compose logs -f fraud-generator
```

---

## 🔌 Integration Examples

### Apache Spark

```python
# Read generated data
df = spark.read.json("output/transactions_*.jsonl")

# Analyze frauds
df.filter("is_fraud = true") \
  .groupBy("fraud_type") \
  .count() \
  .show()
```

### Kafka Consumer (Python)

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    tx = message.value
    if tx['is_fraud']:
        print(f"🚨 FRAUD: {tx['transaction_id']} - {tx['fraud_type']}")
```

### Pandas / ML Training

```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_json("output/transactions_00000.jsonl", lines=True)

# Prepare features
X = df[['valor', 'fraud_score', 'horario_incomum']]
y = df['is_fraud']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
```

### MinIO + Spark (Data Lake)

```python
# Configure Spark for MinIO
spark = SparkSession.builder \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .getOrCreate()

# Read from MinIO
df = spark.read.json("s3a://fraud-data/raw/transactions_*.jsonl")
```

---

## 📁 Project Structure

```
synthfin-data/
├── generate.py              # 📁 Batch generation script
├── stream.py                # 📡 Streaming script
├── Dockerfile               # 🐳 Docker image
├── docker-compose.yml       # 🐳 Full stack with Kafka
├── requirements.txt         # 📦 Core dependencies
├── requirements-streaming.txt # 📦 Kafka/webhook deps
│
└── src/fraud_generator/
    ├── generators/          # Customer, Device, Transaction, Driver, Ride
    ├── exporters/           # JSON, CSV, Parquet, MinIO
    ├── connections/         # Kafka, Webhook, Stdout
    ├── validators/          # CPF validation
    ├── profiles/            # Behavioral profiles
    └── config/              # Banks, MCCs, Geography
```

---

## 🏦 Supported Banks (25+)

| Bank | Type | Share |
|------|------|-------|
| Nubank | Digital | 15% |
| Banco do Brasil | Public | 15% |
| Itaú | Private | 15% |
| Caixa | Public | 14% |
| Bradesco | Private | 12% |
| Santander | Private | 10% |
| Inter, C6, PagBank, Original... | Digital | ... |

---

## 👤 Behavioral Profiles

| Profile | % | Behavior |
|---------|---|----------|
| `young_digital` | 25% | PIX, streaming, delivery apps |
| `family_provider` | 22% | Supermarket, utilities, education |
| `subscription_heavy` | 20% | Recurring, digital services |
| `traditional_senior` | 15% | Cards, pharmacies |
| `business_owner` | 10% | B2B, high values |
| `high_spender` | 8% | Luxury, travel |

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 👤 Author

**Abner Fonseca** - [@afborda](https://github.com/afborda)

---

<div align="center">

⭐ **Star this repo if it helped you-rf /home/ubuntu/Estudos/synthfin-data/test_output* ⭐

Made with ❤️ for the Brazilian Data Engineering community

</div>
