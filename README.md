# 🇧🇷 Brazilian Fraud Data Generator

<div align="center">

[![en](https://img.shields.io/badge/lang-en-red.svg)](./README.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](./README.pt-BR.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-Streaming-231F20?logo=apachekafka&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)
[![Stars](https://img.shields.io/github/stars/afborda/brazilian-fraud-data-generator?style=social)](https://github.com/afborda/brazilian-fraud-data-generator)

**Synthetic Brazilian banking transaction data generator for Data Engineering and Machine Learning**

[🚀 Quick Start](#-quick-start) •
[📡 Streaming Mode](#-streaming-mode) •
[🐳 Docker](#-docker) •
[📊 Data Schema](#-data-schema)

</div>

---

## 📋 About

Generate **realistic synthetic data** of Brazilian banking transactions with two modes:

| Mode | Use Case | Command |
|------|----------|---------|
| **📁 Batch** | Generate files for analysis (Spark, ML training) | `python generate.py --size 1GB` |
| **📡 Streaming** | Real-time data for Kafka, APIs, testing pipelines | `python stream.py --target kafka` |

### Features

- ✅ **Valid CPF** with check digits (Faker pt_BR)
- ✅ **Transactions**: PIX, credit/debit cards, TED, boleto, withdrawals
- ✅ **13 fraud types** with realistic distribution
- ✅ **6 behavioral profiles** (young_digital, traditional_senior, business_owner, etc.)
- ✅ **25+ real Brazilian banks** with market share weights
- ✅ **Streaming**: Kafka, Webhooks, stdout
- ✅ **Docker ready**: One command to run with Kafka

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/afborda/brazilian-fraud-data-generator.git
cd brazilian-fraud-data-generator
pip install -r requirements.txt
```

### Batch Mode (Generate Files)

```bash
# Generate 1GB of data
python generate.py --size 1GB

# Generate in Parquet format
python generate.py --size 1GB --format parquet

# Generate 50GB with 8 workers
python generate.py --size 50GB --workers 8
```

**Output:**
```
output/
├── customers.jsonl       # Customers with valid CPF
├── devices.jsonl         # Devices linked to customers
└── transactions_*.jsonl  # ~128MB files each
```

---

## 📡 Streaming Mode

Stream transactions in real-time to different targets.

### Install Streaming Dependencies

```bash
pip install -r requirements-streaming.txt
```

### Stream to stdout (Debug)

```bash
# 5 events per second
python stream.py --target stdout --rate 5

# Limit to 100 events
python stream.py --target stdout --rate 10 --max-events 100
```

### Stream to Kafka

```bash
python stream.py --target kafka \
    --kafka-server localhost:9092 \
    --kafka-topic transactions \
    --rate 100
```

### Stream to Webhook/REST API

```bash
python stream.py --target webhook \
    --webhook-url http://localhost:8080/api/ingest \
    --rate 50
```

### Streaming Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--target` | `stdout` | Target: `stdout`, `kafka`, `webhook` |
| `--rate` | `10` | Events per second |
| `--max-events` | `∞` | Stop after N events (infinite by default) |
| `--customers` | `100` | Number of customers in pool |
| `--fraud-rate` | `0.02` | Fraud rate (2%) |
| `--kafka-server` | - | Kafka bootstrap server |
| `--kafka-topic` | `transactions` | Kafka topic name |
| `--webhook-url` | - | Webhook endpoint URL |

---

## 🐳 Docker

### Quick Start with Docker Compose

```bash
# Start Kafka + Generator
docker-compose up -d

# View streaming logs
docker-compose logs -f fraud-generator

# Stop
docker-compose down
```

### Docker Run (Batch Mode)

```bash
# Generate 1GB of data
docker run -v $(pwd)/output:/output \
    fraud-generator:latest \
    python generate.py --size 1GB --output /output
```

### Docker Run (Streaming to Kafka)

```bash
docker run --network host \
    fraud-generator:latest \
    python stream.py --target kafka \
    --kafka-server localhost:9092 \
    --rate 100
```

---

## ⚙️ Batch Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--size` | `1GB` | Total data size (e.g., `500MB`, `10GB`, `50GB`) |
| `--format` | `jsonl` | Export format: `jsonl`, `csv`, `parquet` |
| `--workers` | `CPU cores` | Parallel processes |
| `--fraud-rate` | `0.02` | Fraud rate (2%) |
| `--output` | `./output` | Output directory |
| `--customers` | `auto` | Number of customers |
| `--no-profiles` | - | Disable behavioral profiles |
| `--seed` | - | Seed for reproducibility |
| `--start-date` | `-1 year` | Start date (YYYY-MM-DD) |
| `--end-date` | `today` | End date (YYYY-MM-DD) |

---

## �� Data Schema

### Customer

```json
{
  "customer_id": "CUST_000000000001",
  "nome": "Maria Silva Santos",
  "cpf": "123.456.789-09",
  "email": "maria.silva@email.com.br",
  "telefone": "(11) 98765-4321",
  "data_nascimento": "1985-03-15",
  "endereco": {
    "logradouro": "Rua das Flores, 123",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01310-100"
  },
  "renda_mensal": 5500.00,
  "banco_codigo": "260",
  "banco_nome": "Nubank",
  "perfil_comportamental": "young_digital"
}
```

### Transaction

```json
{
  "transaction_id": "TXN_000000000000001",
  "customer_id": "CUST_000000000001",
  "device_id": "DEV_000000000001",
  "timestamp": "2024-03-15T14:32:45.123456",
  "tipo": "PIX",
  "valor": 150.00,
  "canal": "APP_MOBILE",
  "merchant_name": "Carrefour",
  "mcc_code": "5411",
  "is_fraud": false,
  "fraud_type": null,
  "fraud_score": 12.5
}
```

---

## 🏦 Banks & Fraud Types

### Supported Banks (25+)

| Bank | Type | Weight |
|------|------|--------|
| Nubank | Digital | 15% |
| Banco do Brasil | Public | 15% |
| Itaú | Private | 15% |
| Caixa | Public | 14% |
| Bradesco | Private | 12% |
| Santander | Private | 10% |
| Inter, C6, PagBank... | Digital | ... |

### Fraud Types (13)

| Type | Description | % |
|------|-------------|---|
| `ENGENHARIA_SOCIAL` | Phone/WhatsApp scams | 20% |
| `CONTA_TOMADA` | Account takeover | 16% |
| `CARTAO_CLONADO` | Cloned card | 15% |
| `IDENTIDADE_FALSA` | Fake documents | 10% |
| `SIM_SWAP` | SIM card fraud | 6% |
| ... | 8 more types | ... |

---

## 👤 Behavioral Profiles

| Profile | % | Characteristics |
|---------|---|-----------------|
| `young_digital` | 25% | PIX, streaming, delivery apps |
| `family_provider` | 22% | Supermarket, utilities, education |
| `subscription_heavy` | 20% | Recurring charges, digital services |
| `traditional_senior` | 15% | Card payments, pharmacies |
| `business_owner` | 10% | B2B, high values, wholesale |
| `high_spender` | 8% | Luxury, travel, high-value |

---

## 🎯 Use Cases

### Apache Spark

```python
df = spark.read.json("output/transactions_*.jsonl")
df.filter("is_fraud = true").groupBy("fraud_type").count().show()
```

### Kafka Consumer

```python
from kafka import KafkaConsumer
consumer = KafkaConsumer('transactions', bootstrap_servers='localhost:9092')
for msg in consumer:
    print(msg.value)
```

### ML Training

```python
import pandas as pd
df = pd.read_json("output/transactions_00000.jsonl", lines=True)
X = df[['valor', 'fraud_score', 'horario_incomum']]
y = df['is_fraud']
```

---

## 📁 Project Structure

```
brazilian-fraud-data-generator/
├── generate.py              # Batch mode script
├── stream.py                # Streaming mode script
├── Dockerfile               # Docker image
├── docker-compose.yml       # Kafka + Generator setup
├── requirements.txt         # Core dependencies
├── requirements-streaming.txt # Kafka/webhook dependencies
└── src/fraud_generator/
    ├── generators/          # Data generators
    ├── connections/         # Kafka, Webhook, Stdout
    ├── exporters/           # JSON, CSV, Parquet
    ├── validators/          # CPF validation
    ├── profiles/            # Behavioral profiles
    └── config/              # Banks, MCCs, etc.
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 👤 Author

**Abner Fonseca** - [@afborda](https://github.com/afborda)

---

<div align="center">

**Made with ❤️ for the Brazilian Data Engineering community**

⭐ Star this repo if it helped you!

</div>
