# 🇧🇷 Gerador de Dados de Fraude Brasileiro

<div align="center">

[![en](https://img.shields.io/badge/lang-en-red.svg)](./README.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](./README.pt-BR.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-Streaming-231F20?logo=apachekafka&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3-C72E49?logo=minio&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

**Gerador de dados sintéticos brasileiros para Data Engineering & ML**

</div>

---

## 🎯 O que é isso?

Ferramenta para gerar **dados sintéticos brasileiros** para:
- 🏦 **Transações bancárias** (PIX, cartões, TED, boleto)
- 🚗 **Corridas de app** (Uber, 99, Cabify, InDriver)
- 🔴 **Detecção de fraude** para treino e testes

Ideal para: **Pipelines de dados**, **Jobs Spark**, **Streaming Kafka**, **Modelos ML**, **Testes de API**

---

## 🚀 Início Rápido (5 minutos)

### 1️⃣ Instalação

```bash
git clone https://github.com/afborda/brazilian-fraud-data-generator.git
cd brazilian-fraud-data-generator
pip install -r requirements.txt
```

### 2️⃣ Gere seus primeiros dados

```bash
# Gerar 100MB de transações
python3 generate.py --size 100MB --output ./meus_dados
```

**Pronto!** Veja sua pasta `./meus_dados`:
```
meus_dados/
├── customers.jsonl       # 👥 Clientes com CPFs válidos
├── devices.jsonl         # 📱 Dispositivos por cliente  
└── transactions_00000.jsonl  # 💳 Transações (~128MB cada)
```

---

## 📖 Tipos de Dados: Bancário vs Corridas

Este gerador suporta **dois tipos diferentes** de dados:

| Tipo | Comando | O que gera | Tipos de fraude |
|------|---------|------------|-----------------|
| 💳 **Bancário** | `--type transactions` | PIX, cartões, TED, boleto | Cartão clonado, conta tomada, engenharia social |
| 🚗 **Corridas** | `--type rides` | Viagens Uber, 99, Cabify, InDriver | GPS spoofing, corrida falsa, conluio motorista |
| 🔄 **Ambos** | `--type all` | Tudo acima | Todos os tipos de fraude |

### Arquivos Gerados por Tipo

```bash
# Bancário (padrão): --type transactions
output/
├── customers.jsonl          # 👥 Clientes bancários
├── devices.jsonl            # 📱 Dispositivos dos clientes
└── transactions_*.jsonl     # 💳 Transações bancárias

# Corridas: --type rides
output/
├── customers.jsonl          # 👥 Passageiros
├── devices.jsonl            # 📱 Dispositivos dos passageiros
├── drivers.jsonl            # 🚘 Motoristas com veículos
└── rides_*.jsonl            # 🚗 Corridas de app

# Ambos: --type all
output/
├── customers.jsonl          # 👥 Clientes/Passageiros
├── devices.jsonl            # 📱 Dispositivos
├── drivers.jsonl            # 🚘 Motoristas
├── transactions_*.jsonl     # 💳 Transações bancárias
└── rides_*.jsonl            # 🚗 Corridas de app
```

---

## 📖 Exemplos de Uso

### 🔹 Modo Batch (Gerar Arquivos)

| Objetivo | Comando |
|----------|---------|
| Gerar 1GB de transações | `python3 generate.py --size 1GB` |
| Gerar em formato CSV | `python3 generate.py --size 500MB --format csv` |
| Gerar em Parquet | `python3 generate.py --size 1GB --format parquet` |
| Gerar dados de corridas | `python3 generate.py --size 1GB --type rides` |
| Gerar ambos (transações + corridas) | `python3 generate.py --size 1GB --type all` |
| Taxa de fraude maior (5%) | `python3 generate.py --size 1GB --fraud-rate 0.05` |
| Dados reproduzíveis (seed) | `python3 generate.py --size 1GB --seed 42` |
| Mais rápido com 16 workers | `python3 generate.py --size 10GB --workers 16` |

#### 🗜️ Opções de Compressão Parquet

Ao usar `--format parquet`, você pode escolher o algoritmo de compressão:

| Compressão | Comando | Melhor Para |
|------------|---------|-------------|
| **ZSTD** (padrão) | `--compression zstd` | Melhor taxa de compressão, recomendado |
| Snappy | `--compression snappy` | Mais rápido, compatibilidade legada |
| Gzip | `--compression gzip` | Máxima compatibilidade |
| Brotli | `--compression brotli` | Alta compressão |
| Nenhuma | `--compression none` | Sem compressão |

```bash
# Padrão: ZSTD (melhor relação compressão/velocidade, ~91% menor que JSONL)
python3 generate.py --size 1GB --format parquet

# Use Snappy para sistemas legados ou Spark < 2.4
python3 generate.py --size 1GB --format parquet --compression snappy

# Compressão máxima com Gzip
python3 generate.py --size 1GB --format parquet --compression gzip
```

> **💡 Nota:** ZSTD é o padrão porque oferece o melhor equilíbrio entre taxa de compressão e velocidade.
> Se seu sistema não suporta ZSTD (versões antigas de Spark, Hive ou Presto), use `--compression snappy`.

### 🔹 Modo Streaming (Tempo Real)

Primeiro, instale as dependências de streaming:
```bash
pip install -r requirements-streaming.txt
```

| Objetivo | Comando |
|----------|---------|
| Testar no terminal (5/seg) | `python3 stream.py --target stdout --rate 5` |
| Stream para Kafka | `python3 stream.py --target kafka --kafka-server localhost:9092 --rate 100` |
| Stream corridas para Kafka | `python3 stream.py --target kafka --type rides --kafka-topic rides --rate 50` |
| Stream para API REST | `python3 stream.py --target webhook --webhook-url http://api:8080/ingest` |
| Eventos limitados (1000) | `python3 stream.py --target stdout --max-events 1000` |

#### 📊 Entendendo `--rate` (Eventos por Segundo)

| Rate | Significado | Uso |
|------|-------------|-----|
| `--rate 1` | 1 evento/seg (1 a cada 1000ms) | Debug/Testes |
| `--rate 10` | 10 eventos/seg (1 a cada 100ms) | Desenvolvimento |
| `--rate 100` | 100 eventos/seg (1 a cada 10ms) | Produção |
| `--rate 1000` | 1000 eventos/seg (1 a cada 1ms) | Stress test |

**O output em tempo real mostra a taxa real:**
```
📊 Events: 1,000 | Rate: 99.6/s | Errors: 0
```

### 🔹 Modo Docker

```bash
# Batch: Gerar 1GB
docker run -v $(pwd)/output:/output ghcr.io/afborda/fraud-generator \
    python3 generate.py --size 1GB --output /output

# Streaming para Kafka
docker run --network host ghcr.io/afborda/fraud-generator \
    python3 stream.py --target kafka --kafka-server localhost:9092 --rate 100
```

### 🔹 Upload Direto MinIO/S3

Envie diretamente para MinIO ou storage compatível com S3:

```bash
# Upload para bucket MinIO
python3 generate.py --size 1GB \
    --output minio://fraud-data/raw \
    --minio-endpoint http://localhost:9000 \
    --minio-access-key minioadmin \
    --minio-secret-key minioadmin

# Ou use variáveis de ambiente
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ROOT_USER=minioadmin
export MINIO_ROOT_PASSWORD=minioadmin

python3 generate.py --size 1GB --output minio://fraud-data/raw
```

---

## 📊 Quais Dados São Gerados?

### 👥 Clientes

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

### 💳 Transações

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

### 🚗 Corridas

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

### 🚘 Motoristas

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

## 🔴 Tipos de Fraude

### Fraudes em Transações (13 tipos)

| Tipo | Descrição |
|------|-----------|
| `ENGENHARIA_SOCIAL` | Golpes por telefone/WhatsApp |
| `CONTA_TOMADA` | Roubo de conta |
| `CARTAO_CLONADO` | Cartão clonado |
| `IDENTIDADE_FALSA` | Documentos falsos |
| `SIM_SWAP` | Fraude de chip de celular |
| `TESTE_CARTAO` | Teste de cartão |
| `LAVAGEM_DINHEIRO` | Lavagem de dinheiro |
| ... | + 6 outros |

### Fraudes em Corridas (7 tipos)

| Tipo | Descrição |
|------|-----------|
| `GPS_SPOOFING` | GPS falso para aumentar distância |
| `DRIVER_COLLUSION` | Conluio motorista-passageiro |
| `SURGE_ABUSE` | Manipulação de preço dinâmico |
| `PROMO_ABUSE` | Abuso de código promocional |
| `FAKE_RIDE` | Corrida falsa para pagamento |
| `IDENTITY_FRAUD` | Identidade falsa motorista/passageiro |
| `PAYMENT_FRAUD` | Métodos de pagamento roubados |

---

## ⚙️ Todos os Parâmetros

### generate.py (Modo Batch)

```bash
python3 generate.py --help
```

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--size`, `-s` | `1GB` | Tamanho alvo: `100MB`, `1GB`, `50GB` |
| `--type`, `-t` | `transactions` | `transactions`, `rides` ou `all` |
| `--output`, `-o` | `./output` | Diretório ou `minio://bucket/prefix` |
| `--format`, `-f` | `jsonl` | `jsonl`, `csv`, `parquet` |
| `--fraud-rate`, `-r` | `0.02` | Taxa de fraude (0.0 a 1.0) |
| `--workers`, `-w` | `CPUs` | Workers paralelos |
| `--seed` | Nenhum | Seed para reprodutibilidade |
| `--customers`, `-c` | Auto | Número de clientes |
| `--start-date` | -1 ano | Data inicial (YYYY-MM-DD) |
| `--end-date` | hoje | Data final (YYYY-MM-DD) |
| `--no-profiles` | - | Desabilitar perfis comportamentais |
| `--minio-endpoint` | env | URL do MinIO/S3 |
| `--minio-access-key` | env | Chave de acesso MinIO |
| `--minio-secret-key` | env | Chave secreta MinIO |

### stream.py (Modo Streaming)

```bash
python3 stream.py --help
```

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--target`, `-t` | Obrigatório | `stdout`, `kafka`, `webhook` |
| `--type` | `transactions` | `transactions` ou `rides` |
| `--rate`, `-r` | `10` | Eventos por segundo |
| `--max-events`, `-n` | ∞ | Parar após N eventos |
| `--customers`, `-c` | `1000` | Tamanho do pool de clientes |
| `--fraud-rate` | `0.02` | Taxa de fraude |
| `--kafka-server` | `localhost:9092` | Servidor bootstrap Kafka |
| `--kafka-topic` | `transactions` | Tópico Kafka |
| `--webhook-url` | - | Endpoint do webhook |
| `--quiet`, `-q` | - | Suprimir progresso |

---

## 🐳 Docker Compose (Stack Completa)

Execute com Kafka incluído:

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

## 🔌 Exemplos de Integração

### Apache Spark

```python
# Ler dados gerados
df = spark.read.json("output/transactions_*.jsonl")

# Analisar fraudes
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
        print(f"🚨 FRAUDE: {tx['transaction_id']} - {tx['fraud_type']}")
```

### Pandas / Treino ML

```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Carregar dados
df = pd.read_json("output/transactions_00000.jsonl", lines=True)

# Preparar features
X = df[['valor', 'fraud_score', 'horario_incomum']]
y = df['is_fraud']

# Dividir
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
```

### MinIO + Spark (Data Lake)

```python
# Configurar Spark para MinIO
spark = SparkSession.builder \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .getOrCreate()

# Ler do MinIO
df = spark.read.json("s3a://fraud-data/raw/transactions_*.jsonl")
```

---

## 📁 Estrutura do Projeto

```
brazilian-fraud-data-generator/
├── generate.py              # 📁 Script de geração batch
├── stream.py                # 📡 Script de streaming
├── Dockerfile               # 🐳 Imagem Docker
├── docker-compose.yml       # 🐳 Stack completa com Kafka
├── requirements.txt         # 📦 Dependências principais
├── requirements-streaming.txt # 📦 Deps Kafka/webhook
│
└── src/fraud_generator/
    ├── generators/          # Customer, Device, Transaction, Driver, Ride
    ├── exporters/           # JSON, CSV, Parquet, MinIO
    ├── connections/         # Kafka, Webhook, Stdout
    ├── validators/          # Validação de CPF
    ├── profiles/            # Perfis comportamentais
    └── config/              # Bancos, MCCs, Geografia
```

---

## 🏦 Bancos Suportados (25+)

| Banco | Tipo | % |
|-------|------|---|
| Nubank | Digital | 15% |
| Banco do Brasil | Público | 15% |
| Itaú | Privado | 15% |
| Caixa | Público | 14% |
| Bradesco | Privado | 12% |
| Santander | Privado | 10% |
| Inter, C6, PagBank, Original... | Digital | ... |

---

## 👤 Perfis Comportamentais

| Perfil | % | Comportamento |
|--------|---|---------------|
| `young_digital` | 25% | PIX, streaming, delivery |
| `family_provider` | 22% | Supermercado, contas, educação |
| `subscription_heavy` | 20% | Recorrente, serviços digitais |
| `traditional_senior` | 15% | Cartões, farmácias |
| `business_owner` | 10% | B2B, valores altos |
| `high_spender` | 8% | Luxo, viagens |

---

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE)

---

## 👤 Autor

**Abner Fonseca** - [@afborda](https://github.com/afborda)

---

<div align="center">

⭐ **Dê uma estrela se este projeto te ajudou-100 /home/ubuntu/Estudos/brazilian-fraud-data-generator/README.md* ⭐

Feito com ❤️ para a comunidade brasileira de Data Engineering

</div>
