# 🇧🇷 Brazilian Fraud Data Generator

<div align="center">

[![en](https://img.shields.io/badge/lang-en-red.svg)](./README.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](./README.pt-BR.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Faker](https://img.shields.io/badge/Faker-pt__BR-green)
![License](https://img.shields.io/badge/License-MIT-blue)
[![Stars](https://img.shields.io/github/stars/afborda/brazilian-fraud-data-generator?style=social)](https://github.com/afborda/brazilian-fraud-data-generator)

**Synthetic Brazilian banking transaction data generator for Data Engineering and Machine Learning studies**

[🚀 Quick Start](#-quick-start) •
[📊 Generated Data](#-generated-data) •
[⚙️ Parameters](#️-parameters) •
[🎯 Use Cases](#-use-cases)

</div>

---

## 📋 About

This project generates **realistic synthetic data** of Brazilian banking transactions, including:

- ✅ **Customers** with **valid CPF** (with check digits), name, address, income (Faker pt_BR)
- ✅ **Devices** (smartphones, tablets, desktops with real manufacturers)
- ✅ **Transactions** (PIX, credit/debit cards, wire transfers, bank slips, withdrawals)
- ✅ **Frauds** (13 different types with realistic distribution)
- ✅ **Behavioral Profiles** (6 customer archetypes with realistic spending patterns)
- ✅ **Geolocation** correlated with customer's state
- ✅ **Real Brazilian banks** with realistic market share (25+ banks)
- ✅ **MCCs** with typical values per category
- ✅ **Temporal patterns** (more transactions during business hours)
- ✅ **Multiple export formats** (JSON Lines, CSV, Parquet)

### 🆕 What's new in v3.0

- **Valid CPF numbers** - All generated CPFs now have proper check digits
- **Behavioral profiles** - Customers have realistic spending patterns based on their profile (young_digital, traditional_senior, business_owner, etc.)
- **Multiple formats** - Export to JSON Lines, CSV, or Parquet
- **Modular architecture** - Clean code with separate modules for config, generators, validators, and exporters
- **Memory optimization** - Efficient streaming for large datasets

### 🎯 Why was it created?

While studying **Data Engineering**, I needed a large and realistic dataset to:
- Test Apache Spark pipelines at scale
- Practice Medallion architecture (Bronze → Silver → Gold)
- Train fraud detection models
- Simulate Big Data scenarios (50GB+)

I couldn't find quality Brazilian datasets, so I built this generator!

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/afborda/brazilian-fraud-data-generator.git
cd brazilian-fraud-data-generator

# Install dependencies
pip install -r requirements.txt

# Optional: For Parquet/CSV export
pip install pandas pyarrow
```

### Generate data

```bash
# Generate 1GB of data (quick test)
python3 generate.py --size 1GB

# Generate in CSV format
python3 generate.py --size 1GB --format csv

# Generate in Parquet format (best for analytics)
python3 generate.py --size 1GB --format parquet

# Generate without behavioral profiles (random transactions)
python3 generate.py --size 1GB --no-profiles

# Generate 50GB of data (recommended for Big Data)
python3 generate.py --size 50GB --workers 8

# Generate reproducible data (same seed = same data)
python3 generate.py --size 1GB --seed 42
```

### Output

```
output/
├── customers.jsonl       # Brazilian customers with valid CPF
├── devices.jsonl         # Devices linked to customers
└── transactions_*.jsonl  # ~128MB files each (JSON Lines)
```

---

## ⚙️ Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--size` | `1GB` | Total data size (e.g., `1GB`, `10GB`, `50GB`) |
| `--format` | `jsonl` | Export format (`jsonl`, `csv`, `parquet`) |
| `--workers` | `CPU cores` | Number of parallel processes |
| `--fraud-rate` | `0.02` | Fraud rate (2% = ~20 per 1000) |
| `--output` | `./output` | Output directory |
| `--customers` | `auto` | Number of customers (auto-calculated from size) |
| `--no-profiles` | - | Disable behavioral profiles (random transactions) |
| `--start-date` | `-1 year` | Start date (YYYY-MM-DD) |

| `--end-date` | - | End date (YYYY-MM-DD) |
| `--seed` | - | Seed for reproducibility |
| `--quiet` | - | Quiet mode (JSON output) |
| `--customers-only` | - | Generate only customers and devices |

### Examples

```bash
# Quick test (500MB, 2 workers)
python3 generate.py --size 500MB --workers 2

# Production (50GB, max workers, 1% fraud)
python3 generate.py --size 50GB --workers 10 --fraud-rate 0.01

# Specific date range
python3 generate.py --size 5GB --start-date 2024-01-01 --end-date 2024-06-30

# Reproducible (always generates the same data)
python3 generate.py --size 1GB --seed 42

# For scripts/CI (JSON output)
python3 generate.py --size 1GB --quiet

# Customized (20GB, 200K customers)
python3 generate.py --size 20GB --customers 200000 --output ./my_data
```

---

## 📊 Generated Data

### 👥 Customers (`customers.json`)

```json
{
  "customer_id": "CUST_00000001",
  "nome": "Maria Silva Santos",
  "cpf": "123.456.789-00",
  "email": "maria.silva@email.com.br",
  "telefone": "(11) 98765-4321",
  "data_nascimento": "1985-03-15",
  "endereco": {
    "logradouro": "Rua das Flores, 123",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01310-100"
  },
  "renda_mensal": 5500.00,
  "profissao": "Analista de Sistemas",
  "conta_criada_em": "2018-06-01T10:30:00",
  "tipo_conta": "DIGITAL",
  "status_conta": "ATIVA",
  "limite_credito": 22000.00,
  "score_credito": 750,
  "nivel_risco": "BAIXO",
  "banco_codigo": "260",
  "banco_nome": "Nubank",
  "agencia": "0001",
  "numero_conta": "123456-7"
}
```

### 📱 Devices (`devices.json`)

```json
{
  "device_id": "DEV_00000001",
  "customer_id": "CUST_00000001",
  "tipo": "SMARTPHONE",
  "fabricante": "Samsung",
  "modelo": "Galaxy S23",
  "sistema_operacional": "Android 14",
  "fingerprint": "a1b2c3d4e5f6789...",
  "primeiro_uso": "2023-01-15",
  "is_trusted": true,
  "is_rooted_jailbroken": false
}
```

### 💳 Transactions (`transactions_*.json`)

```json
{
  "transaction_id": "TXN_000000000000001",
  "customer_id": "CUST_00000001",
  "session_id": "SESS_000000000001",
  "device_id": "DEV_00000001",
  "timestamp": "2024-03-15T14:32:45.123456",
  "tipo": "PIX",
  "valor": 150.00,
  "moeda": "BRL",
  "canal": "APP_MOBILE",
  "ip_address": "177.45.123.89",
  "geolocalizacao_lat": -23.550520,
  "geolocalizacao_lon": -46.633308,
  "merchant_id": "MERCH_012345",
  "merchant_name": "Carrefour",
  "merchant_category": "Supermercados",
  "mcc_code": "5411",
  "mcc_risk_level": "low",
  "numero_cartao_hash": null,
  "bandeira": null,
  "tipo_cartao": null,
  "parcelas": null,
  "entrada_cartao": null,
  "cvv_validado": null,
  "autenticacao_3ds": null,
  "chave_pix_tipo": "CPF",
  "chave_pix_destino": "a1b2c3d4e5f6...",
  "banco_destino": "341",
  "distancia_ultima_transacao_km": 5.23,
  "tempo_desde_ultima_transacao_min": 45,
  "transacoes_ultimas_24h": 3,
  "valor_acumulado_24h": 450.00,
  "horario_incomum": false,
  "novo_beneficiario": false,
  "status": "APROVADA",
  "motivo_recusa": null,
  "fraud_score": 12.5,
  "is_fraud": false,
  "fraud_type": null
}
```

---

## 🏦 Supported Banks

Banks are selected with weight proportional to real market share:

| Code | Bank | Type | Weight |
|------|------|------|--------|
| 001 | Banco do Brasil | Public | 12% |
| 341 | Itaú Unibanco | Private | 12% |
| 104 | Caixa Econômica | Public | 12% |
| 237 | Bradesco | Private | 10% |
| 033 | Santander | Private | 8% |
| 260 | Nubank | Digital | 15% |
| 077 | Banco Inter | Digital | 6% |
| 336 | C6 Bank | Digital | 5% |
| 290 | PagBank | Digital | 4% |
| 380 | PicPay | Digital | 3% |
| 212 | Banco Original | Digital | 2% |
| ... | +14 others | ... | ... |

---

## 🚨 Fraud Types

The generator includes **13 fraud types** with distribution based on real data:

| Type | Description | % of Total |
|------|-------------|------------|
| `ENGENHARIA_SOCIAL` | Phone/WhatsApp scams | ~20% |
| `CONTA_TOMADA` | Account takeover | ~16% |
| `CARTAO_CLONADO` | Cloned card/data | ~15% |
| `IDENTIDADE_FALSA` | Fake documents | ~10% |
| `AUTOFRAUDE` | Customer claims false fraud | ~8% |
| `FRAUDE_AMIGAVEL` | Fraud by acquaintances | ~6% |
| `LAVAGEM_DINHEIRO` | Money laundering | ~4% |
| `TRIANGULACAO` | Triangulation fraud | ~3% |
| `SIM_SWAP` | SIM card fraud | ~6% |
| `PHISHING` | Phishing attacks | ~5% |
| `BOLETO_FALSO` | Fake bank slip | ~3% |
| `QR_CODE_FALSO` | Fake QR code | ~2% |
| `DEVICE_SPOOFING` | Device fingerprint fraud | ~2% |

---

## 👤 Behavioral Profiles

Version 3.0 introduces **behavioral profiles** that give customers realistic spending patterns:

| Profile | % of Customers | Characteristics |
|---------|---------------|-----------------|
| `young_digital` | 25% | Heavy PIX user, streaming services, food delivery |
| `subscription_heavy` | 20% | Many recurring charges, digital services |
| `family_provider` | 22% | Supermarket, utilities, education expenses |
| `traditional_senior` | 15% | Prefers card payments, pharmacies, traditional stores |
| `business_owner` | 10% | B2B transactions, higher values, wholesale purchases |
| `high_spender` | 8% | Luxury goods, travel, high-value transactions |

Each profile affects:
- **Transaction types** (PIX vs Card preferences)
- **Merchant categories** (MCC preferences)
- **Transaction values** (min/max ranges)
- **Active hours** (when they transact)
- **Transaction frequency** (per month average)

To disable profiles and generate random transactions:
```bash
python3 generate.py --size 1GB --no-profiles
```

---

## 📈 Data Realism

### Transaction Distribution
- **PIX**: 45% (dominates in Brazil since 2021)
- **Credit Card**: 25%
- **Debit Card**: 15%
- **Bank Slip (Boleto)**: 8%
- **Wire Transfer (TED)**: 4%
- **Withdrawal**: 3%

### Channels
- **Mobile App**: 60%
- **Web Banking**: 25%
- **ATM**: 8%
- **Branch**: 5%
- **WhatsApp Pay**: 2%

### Temporal Patterns
- More transactions between 8am-8pm
- Peak at 12pm-2pm and 6pm-8pm
- Late night (0am-6am) marked as `horario_incomum` (unusual time)

### Values by Category (MCC)
- **Fast Food**: R$ 15-100
- **Supermarkets**: R$ 15-800
- **Gas Stations**: R$ 50-500
- **Electronics**: R$ 100-8,000
- **Jewelry**: R$ 200-15,000

---

## 📈 Performance

Tested on VPS with 8 cores / 24GB RAM:

| Size | Files | Time | Speed |
|------|-------|------|-------|
| 1 GB | 8 | ~1 min | 17 MB/s |
| 10 GB | 80 | ~8 min | 21 MB/s |
| 50 GB | 400 | ~35 min | 24 MB/s |

> 💡 **Tip:** Use `--workers` equal to the number of CPU cores for maximum performance

---

## 🎯 Use Cases

### 1️⃣ Study Apache Spark

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("FraudAnalysis").getOrCreate()

# Read transactions
df = spark.read.json("output/transactions_*.json")
df.printSchema()
df.show()

# Fraud analysis
df.filter("is_fraud = true").groupBy("fraud_type").count().show()
```

### 2️⃣ Train ML Model

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load data
df = pd.read_json("output/transactions_00000.json", lines=True)

# Features
features = ['valor', 'fraud_score', 'transacoes_ultimas_24h', 
            'valor_acumulado_24h', 'horario_incomum', 'novo_beneficiario']
X = df[features]
y = df['is_fraud']

# Train
model = RandomForestClassifier()
model.fit(X, y)
```

### 3️⃣ Medallion Pipeline

```
Raw (JSON) → Bronze (Parquet) → Silver (Clean) → Gold (Aggregated)
   51 GB   →      5 GB        →      5.4 GB    →     2 GB
                              90% compression!
```

### 4️⃣ BI Dashboards

Connect Metabase, PowerBI or Tableau to create dashboards for:
- Fraud rate by state
- Most common fraud types
- Temporal transaction analysis
- Top suspicious merchants

---

## 📁 Project Structure

```
brazilian-fraud-data-generator/
├── 📄 README.md           # Documentation (English)
├── 📄 README.pt-BR.md     # Documentation (Portuguese)
├── 📄 requirements.txt    # Dependencies
├── 📄 generate.py         # Main script (v3.0)
├── 📄 generate_v2.py      # Legacy script (v2.1)
├── 📄 LICENSE             # MIT License
├── 📂 src/                # Source modules
│   └── fraud_generator/
│       ├── config/        # Constants (banks, MCCs, etc.)
│       ├── models/        # Data models (Customer, Device, Transaction)
│       ├── generators/    # Data generators
│       ├── validators/    # CPF validation
│       ├── exporters/     # JSON, CSV, Parquet exporters
│       ├── profiles/      # Behavioral profiles
│       └── utils/         # Streaming utilities
├── 📂 examples/           # Usage examples
│   └── README.md
└── 📂 output/             # Generated data (gitignore)
    ├── customers.jsonl
    ├── devices.jsonl
    └── transactions_*.jsonl
```

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the project
2. Create a branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

### Ideas to contribute:
- [ ] Add more transaction types (DOC, direct debit)
- [ ] Support for other Latin American countries
- [ ] Real-time streaming mode
- [ ] API endpoint for on-demand generation

---

## 📄 License

This project is under the MIT license. See the [LICENSE](LICENSE) file for more details.

---

## 👤 Author

**Abner Fonseca**
- LinkedIn: [linkedin.com/in/abnerfonseca](https://www.linkedin.com/in/abner-fonseca-25658b67)
- GitHub: [@afborda](https://github.com/afborda)

---

## ⭐ Like it?

If this project helped you, leave a ⭐ on the repository!

---

<div align="center">

**Made with ❤️ for the Brazilian Data Engineering community**

</div>
