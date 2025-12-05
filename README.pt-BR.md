# 🇧�� Gerador de Dados de Fraude Brasileiro

<div align="center">

[![en](https://img.shields.io/badge/lang-en-red.svg)](./README.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](./README.pt-BR.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-Streaming-231F20?logo=apachekafka&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)
[![Stars](https://img.shields.io/github/stars/afborda/brazilian-fraud-data-generator?style=social)](https://github.com/afborda/brazilian-fraud-data-generator)

**Gerador de dados sintéticos de transações bancárias brasileiras para Data Engineering e Machine Learning**

[🚀 Início Rápido](#-início-rápido) •
[📡 Modo Streaming](#-modo-streaming) •
[🐳 Docker](#-docker) •
[📊 Schema dos Dados](#-schema-dos-dados)

</div>

---

## 📋 Sobre

Gere **dados sintéticos realistas** de transações bancárias brasileiras com dois modos:

| Modo | Uso | Comando |
|------|-----|---------|
| **📁 Batch** | Gerar arquivos para análise (Spark, treino ML) | `python generate.py --size 1GB` |
| **📡 Streaming** | Dados em tempo real para Kafka, APIs, testes | `python stream.py --target kafka` |

### Funcionalidades

- ✅ **CPF válido** com dígitos verificadores (Faker pt_BR)
- ✅ **Transações**: PIX, cartão crédito/débito, TED, boleto, saque
- ✅ **13 tipos de fraude** com distribuição realista
- ✅ **6 perfis comportamentais** (young_digital, traditional_senior, business_owner, etc.)
- ✅ **25+ bancos brasileiros reais** com pesos de market share
- ✅ **Streaming**: Kafka, Webhooks, stdout
- ✅ **Docker ready**: Um comando para rodar com Kafka

---

## 🚀 Início Rápido

### Instalação

```bash
git clone https://github.com/afborda/brazilian-fraud-data-generator.git
cd brazilian-fraud-data-generator
pip install -r requirements.txt
```

### Modo Batch (Gerar Arquivos)

```bash
# Gerar 1GB de dados
python generate.py --size 1GB

# Gerar em formato Parquet
python generate.py --size 1GB --format parquet

# Gerar 50GB com 8 workers
python generate.py --size 50GB --workers 8
```

**Saída:**
```
output/
├── customers.jsonl       # Clientes com CPF válido
├── devices.jsonl         # Dispositivos vinculados
└── transactions_*.jsonl  # Arquivos de ~128MB cada
```

---

## 📡 Modo Streaming

Transmita transações em tempo real para diferentes destinos.

### Instalar Dependências de Streaming

```bash
pip install -r requirements-streaming.txt
```

### Stream para stdout (Debug)

```bash
# 5 eventos por segundo
python stream.py --target stdout --rate 5

# Limitar a 100 eventos
python stream.py --target stdout --rate 10 --max-events 100
```

### Stream para Kafka

```bash
python stream.py --target kafka \
    --kafka-server localhost:9092 \
    --kafka-topic transactions \
    --rate 100
```

### Stream para Webhook/API REST

```bash
python stream.py --target webhook \
    --webhook-url http://localhost:8080/api/ingest \
    --rate 50
```

### Parâmetros de Streaming

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--target` | `stdout` | Destino: `stdout`, `kafka`, `webhook` |
| `--rate` | `10` | Eventos por segundo |
| `--max-events` | `∞` | Parar após N eventos (infinito por padrão) |
| `--customers` | `100` | Número de clientes no pool |
| `--fraud-rate` | `0.02` | Taxa de fraude (2%) |
| `--kafka-server` | - | Servidor bootstrap Kafka |
| `--kafka-topic` | `transactions` | Nome do tópico Kafka |
| `--webhook-url` | - | URL do endpoint webhook |

---

## 🐳 Docker

### Início Rápido com Docker Compose

```bash
# Iniciar Kafka + Generator
docker-compose up -d

# Ver logs do streaming
docker-compose logs -f fraud-generator

# Parar
docker-compose down
```

### Docker Run (Modo Batch)

```bash
# Gerar 1GB de dados
docker run -v $(pwd)/output:/output \
    fraud-generator:latest \
    python generate.py --size 1GB --output /output
```

### Docker Run (Streaming para Kafka)

```bash
docker run --network host \
    fraud-generator:latest \
    python stream.py --target kafka \
    --kafka-server localhost:9092 \
    --rate 100
```

---

## ⚙️ Parâmetros Batch

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--size` | `1GB` | Tamanho total (ex: `500MB`, `10GB`, `50GB`) |
| `--format` | `jsonl` | Formato: `jsonl`, `csv`, `parquet` |
| `--workers` | `CPU cores` | Processos paralelos |
| `--fraud-rate` | `0.02` | Taxa de fraude (2%) |
| `--output` | `./output` | Diretório de saída |
| `--customers` | `auto` | Número de clientes |
| `--no-profiles` | - | Desabilitar perfis comportamentais |
| `--seed` | - | Seed para reprodutibilidade |
| `--start-date` | `-1 ano` | Data início (YYYY-MM-DD) |
| `--end-date` | `hoje` | Data fim (YYYY-MM-DD) |

---

## 📊 Schema dos Dados

### Cliente

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

### Transação

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

## 🏦 Bancos e Tipos de Fraude

### Bancos Suportados (25+)

| Banco | Tipo | Peso |
|-------|------|------|
| Nubank | Digital | 15% |
| Banco do Brasil | Público | 15% |
| Itaú | Privado | 15% |
| Caixa | Público | 14% |
| Bradesco | Privado | 12% |
| Santander | Privado | 10% |
| Inter, C6, PagBank... | Digital | ... |

### Tipos de Fraude (13)

| Tipo | Descrição | % |
|------|-----------|---|
| `ENGENHARIA_SOCIAL` | Golpes por telefone/WhatsApp | 20% |
| `CONTA_TOMADA` | Invasão de conta | 16% |
| `CARTAO_CLONADO` | Cartão clonado | 15% |
| `IDENTIDADE_FALSA` | Documentos falsos | 10% |
| `SIM_SWAP` | Fraude de chip SIM | 6% |
| ... | 8 tipos adicionais | ... |

---

## 👤 Perfis Comportamentais

| Perfil | % | Características |
|--------|---|-----------------|
| `young_digital` | 25% | PIX, streaming, delivery |
| `family_provider` | 22% | Supermercado, utilidades, educação |
| `subscription_heavy` | 20% | Assinaturas, serviços digitais |
| `traditional_senior` | 15% | Cartão, farmácias |
| `business_owner` | 10% | B2B, valores altos, atacado |
| `high_spender` | 8% | Luxo, viagens, alto valor |

---

## 🎯 Casos de Uso

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

### Treino de ML

```python
import pandas as pd
df = pd.read_json("output/transactions_00000.jsonl", lines=True)
X = df[['valor', 'fraud_score', 'horario_incomum']]
y = df['is_fraud']
```

---

## 📁 Estrutura do Projeto

```
brazilian-fraud-data-generator/
├── generate.py              # Script modo batch
├── stream.py                # Script modo streaming
├── Dockerfile               # Imagem Docker
├── docker-compose.yml       # Setup Kafka + Generator
├── requirements.txt         # Dependências core
├── requirements-streaming.txt # Dependências Kafka/webhook
└── src/fraud_generator/
    ├── generators/          # Geradores de dados
    ├── connections/         # Kafka, Webhook, Stdout
    ├── exporters/           # JSON, CSV, Parquet
    ├── validators/          # Validação de CPF
    ├── profiles/            # Perfis comportamentais
    └── config/              # Bancos, MCCs, etc.
```

---

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE)

---

## 👤 Autor

**Abner Fonseca** - [@afborda](https://github.com/afborda)

---

<div align="center">

**Feito com ❤️ para a comunidade brasileira de Data Engineering**

⭐ Dê uma estrela se este projeto te ajudou!

</div>
