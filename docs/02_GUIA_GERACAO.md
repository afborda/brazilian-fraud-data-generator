# Guia de Geração de Dados

## Por que Gerar Dados Sintéticos?

Dados financeiros reais são protegidos por sigilo bancário (Lei Complementar 105/2001) e LGPD (Lei 13.709/2018). Não é possível compartilhar transações reais para treinar modelos de ML, testar sistemas ou fazer pesquisa acadêmica.

O SynthFin resolve isso gerando dados que:

- **São realistas** — Calibrados com dados públicos reais do BCB, IBGE e FEBRABAN
- **Contêm fraude** — 25 tipos de fraude bancária + 11 tipos de fraude ride-share
- **São reprodutíveis** — Seed determinístico garante mesma saída para mesma configuração
- **São seguros** — Nenhum dado real é exposto; CPFs são gerados algoritmicamente
- **São escaláveis** — De 1.000 a milhões de registros, com paralelismo multicore

---

## Pré-requisitos

- Python 3.10+
- Dependências: `pip install -r requirements.txt`
- Docker (opcional, para containerização)

---

## Modos de Geração

O SynthFin suporta 3 modos de execução:

### 1. Modo Batch (Local)

Gera arquivos em disco. É o modo padrão e mais utilizado.

```bash
# Gerar 1GB de transações bancárias
python generate.py --size 1GB --output ./data

# Gerar 500MB de corridas ride-share
python generate.py --size 500MB --type rides --output ./data

# Gerar ambos (transações + corridas)
python generate.py --size 1GB --type all --output ./data

# Controlar taxa de fraude e seed
python generate.py --size 2GB --fraud-rate 0.15 --seed 42 --workers 8

# Formato Parquet com compressão zstd
python generate.py --size 1GB --format parquet --compression zstd
```

#### Parâmetros do Modo Batch

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `--size` | `100MB` | Tamanho aproximado dos dados gerados |
| `--output` | `./output` | Diretório de saída |
| `--type` | `transactions` | Tipo: `transactions`, `rides`, `all` |
| `--format` | `jsonl` | Formato: `jsonl`, `json`, `csv`, `tsv`, `parquet`, `arrow` |
| `--compression` | `none` | Compressão: `none`, `gzip`, `zstd`, `snappy` |
| `--fraud-rate` | `0.008` | Taxa de fraude (0.8% padrão, calibrado para realismo) |
| `--seed` | aleatório | Seed para reprodutibilidade |
| `--workers` | CPU count | Número de processos paralelos |
| `--num` | calculado | Número exato de registros (sobrescreve `--size`) |

### 2. Modo MinIO/S3

Upload direto para object storage compatível com S3.

```bash
# Upload para MinIO
python generate.py --size 5GB --output minio://fraud-data/raw

# Com formato Parquet
python generate.py --size 5GB --output minio://fraud-data/processed --format parquet
```

O modo MinIO usa:
- **ThreadPoolExecutor** para JSONL/CSV (I/O-bound)
- **ProcessPoolExecutor** para Parquet (CPU-bound)

### 3. Modo Schema (Declarativo)

Gera dados baseado em um JSON schema declarativo. Ideal para integração com sistemas específicos que precisam de campos customizados.

```bash
# Usar schema bancário completo
python generate.py --schema schemas/banking_full.json --count 50000

# Usar schema minimalista
python generate.py --schema schemas/banking_minimal.json --count 10000

# Schema customizado
python generate.py --schema meu_schema.json --count 100000
```

#### Exemplo de Schema

```json
{
  "fields": {
    "id_transacao": "transaction.tx_id",
    "valor": "transaction.amount",
    "data": "transaction.timestamp",
    "cpf_cliente": "customer.cpf",
    "tipo": "transaction.type",
    "canal": "transaction.channel",
    "empresa": "static:MINHA-EMPRESA",
    "nome_fantasia": "faker:company"
  }
}
```

Referências de campo disponíveis:
- `transaction.*` — Campos da transação
- `customer.*` — Campos do cliente
- `device.*` — Campos do dispositivo
- `ride.*` — Campos da corrida
- `static:VALOR` — Valor fixo
- `faker:METODO` — Dados fake via Faker

---

## Modo Streaming

Para geração contínua de eventos em tempo real:

```bash
# Streaming para stdout
python stream.py --rate 100 --target stdout

# Streaming para Kafka
python stream.py --rate 1000 --target kafka --kafka-brokers localhost:9092 --kafka-topic transactions

# Streaming para webhook
python stream.py --rate 50 --target webhook --webhook-url https://api.exemplo.com/ingest

# Limitar número de eventos
python stream.py --rate 100 --target stdout --max-events 10000
```

#### Parâmetros do Streaming

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `--rate` | `100` | Eventos por segundo |
| `--target` | `stdout` | Destino: `stdout`, `kafka`, `webhook` |
| `--max-events` | ilimitado | Parar após N eventos |
| `--async` | `false` | Envio assíncrono (thread pool) |

---

## Pipeline de Geração (4 Fases)

O modo batch processa em 4 fases sequenciais:

```
Fase 1: Clientes + Dispositivos
    ↓
    CustomerGenerator → CPFs válidos, endereços, perfis
    DeviceGenerator   → Dispositivos, OS, fingerprints
    ↓
Fase 2: Transações
    ↓
    ProcessPoolExecutor (N workers)
    TransactionGenerator → 117 campos por transação
    ↓
Fase 3: Motoristas (se type=rides ou all)
    ↓
    DriverGenerator → CNH, veículos, apps
    ↓
Fase 4: Corridas (se type=rides ou all)
    ↓
    ProcessPoolExecutor (N workers)
    RideGenerator → Distância Haversine, surge pricing, fraudes
```

### Seed Determinístico

Cada worker recebe um seed derivado do seed base:

```
Worker seed transações = base_seed + batch_id × 12345
Worker seed corridas   = base_seed + batch_id × 54321
```

Isso garante reprodutibilidade mesmo com múltiplos processos.

---

## Formatos de Output

### Arquivos

| Formato | Extensão | Características |
|---------|----------|-----------------|
| JSONL | `.jsonl` | Uma transação por linha, streaming-friendly |
| JSON Array | `.json` | Array completo em memória |
| CSV | `.csv` | Compatível com planilhas e ferramentas BI |
| TSV | `.tsv` | Separado por tab |
| Parquet | `.parquet` | Colunar, comprimido, ideal para analytics |
| Arrow IPC | `.arrow` | Binary columnar, zero-copy reads |

### Compressão

| Algoritmo | Extensão | Caso de Uso |
|-----------|----------|-------------|
| gzip | `.gz` | Compatibilidade universal |
| zstd | `.zst` | Melhor ratio tamanho/velocidade |
| snappy | `.snappy` | Velocidade máxima, compressão moderada |

### Banco de Dados

```bash
# Exportar para banco via SQLAlchemy
python generate.py --size 1GB --format database --db-url "sqlite:///dados.db"
```

### Object Storage (MinIO/S3)

```bash
python generate.py --size 5GB --output minio://bucket/prefix --format parquet
```

---

## Estrutura dos Dados Gerados

### Transação Bancária (117 campos)

Campos principais:

| Grupo | Campos |
|-------|--------|
| **Identificação** | tx_id, customer_id, device_id, timestamp |
| **Valor** | amount (BRL), currency |
| **Tipo** | type (PIX, CREDIT_CARD, TED, DOC, BOLETO, DEBITO) |
| **Canal** | channel (MOBILE_APP, WEB_BANKING, ATM, BRANCH) |
| **Merchant** | merchant_id, merchant_name, mcc, category |
| **Cartão** | card_brand, card_type, entry_mode, installments, cvv_verified, 3ds |
| **PIX** | pix_key_type, ISPB, tipo_conta, holder_type, end_to_end_id |
| **Risco** | fraud_score, fraud_risk_score (17 sinais), is_fraud, fraud_type |
| **Velocidade** | velocity_transactions_24h, accumulated_amount_24h |
| **Geo** | latitude, longitude, unusual_location |
| **Beneficiário** | new_beneficiary, beneficiary_account_age |
| **Sessão** | session_duration, login_method, ip_address |
| **Status** | status (APPROVED/DECLINED), refusal_reason |

### Corrida Ride-Share

| Grupo | Campos |
|-------|--------|
| **Identificação** | ride_id, driver_id, passenger_id, timestamp |
| **Rota** | origin_lat/lon, destination_lat/lon, distance_km |
| **Preço** | base_fare, distance_rate, duration_rate, surge_multiplier, total_fare |
| **Motorista** | cnh_number, vehicle_plate, vehicle_model, rating |
| **App** | app (Uber, 99, Cabify, InDriver), vehicle_category |
| **Fraude** | is_fraud, fraud_type (11 tipos), fraud_score |

---

## Validação dos Dados

### Script de Validação

```bash
# Validação completa (13 seções + score)
python _validate_generated.py

# Verificar calibração (9 overrides)
python verify_calibration.py

# Benchmark de evolução
python _benchmark_evolucao.py
```

### Validação de Realismo

```bash
# Score de realismo (10 dimensões)
python validate_realism.py

# Verificar schema de output
python check_schema.py
```

### TSTR Benchmark (Train Synthetic, Test Real)

```bash
# Treina modelos em dados sintéticos, testa em dados reais
python tools/tstr_benchmark.py
```

Resultados: AUC gap = 0.0% nos modelos LR, RF e XGBoost.

---

## Docker

### Build e Run

```bash
# Build da imagem
docker build -t synthfin-core .

# Gerar dados via Docker
docker run -v $(pwd)/output:/app/output synthfin-core \
    python generate.py --size 1GB --output /app/output --seed 42

# Docker Compose (ecossistema completo)
cd /opt/fraudflow
docker compose up -d
```

### Imagem Docker Hub

```bash
docker pull afborda/synthfin-core:latest
```

---

## Exemplos Práticos

### Gerar dataset para treino de modelo

```bash
python generate.py \
    --size 5GB \
    --fraud-rate 0.01 \
    --seed 42 \
    --format parquet \
    --compression zstd \
    --output ./data/treino
```

### Gerar dataset pequeno para testes

```bash
python generate.py \
    --num 1000 \
    --seed 42 \
    --format csv \
    --output ./data/teste
```

### Gerar streaming para demonstração

```bash
python stream.py \
    --rate 10 \
    --target stdout \
    --max-events 100
```

### Gerar com schema customizado

```bash
python generate.py \
    --schema schemas/banking_full.json \
    --count 50000 \
    --output ./data/custom
```
