# Formatos de Output e Schemas

## Formatos Suportados

O SynthFin exporta dados em 8 formatos, cada um otimizado para um caso de uso.

| Formato | Extensão | Caso de Uso |
|---------|----------|-------------|
| **JSONL** | `.jsonl` | Streaming, ingestão linha a linha |
| **JSON Array** | `.json` | APIs, pequenos datasets |
| **CSV** | `.csv` | Planilhas, BI tools, importação |
| **TSV** | `.tsv` | Processos ETL com tab separator |
| **Parquet** | `.parquet` | Analytics, Spark, data lakes |
| **Arrow IPC** | `.arrow` | Zero-copy reads, interprocess |
| **Database** | SQL | Bancos de dados relacionais |
| **MinIO/S3** | qualquer | Object storage cloud |

---

## JSONL (JSON Lines)

Cada linha é um JSON completo. Formato mais versátil.

```bash
python generate.py --format jsonl --size 1GB --output ./data
```

```jsonl
{"tx_id":"TX_000001","customer_id":"CUST_000042","amount":1523.45,"type":"PIX","is_fraud":false}
{"tx_id":"TX_000002","customer_id":"CUST_000108","amount":8750.00,"type":"TED","is_fraud":true,"fraud_type":"CONTA_TOMADA"}
```

**Vantagens:** Streaming-friendly, processamento linha a linha, baixo uso de memória.

---

## CSV

```bash
python generate.py --format csv --size 1GB --output ./data
```

```csv
tx_id,customer_id,amount,type,is_fraud,fraud_type
TX_000001,CUST_000042,1523.45,PIX,false,
TX_000002,CUST_000108,8750.00,TED,true,CONTA_TOMADA
```

**Vantagens:** Universal, compatível com Excel, pandas, BI tools.

---

## Parquet

```bash
# Parquet simples
python generate.py --format parquet --size 1GB --output ./data

# Parquet com compressão
python generate.py --format parquet --compression zstd --size 1GB --output ./data

# Parquet particionado (por estado/data)
python generate.py --format parquet --size 1GB --output ./data --partitioned
```

**Vantagens:** Colunar, comprimido, leitura parcial de colunas, ideal para Spark/Athena/BigQuery.

---

## Arrow IPC

```bash
python generate.py --format arrow --size 1GB --output ./data
```

**Vantagens:** Zero-copy reads, interprocess communication, máxima performance de leitura.

---

## Database (SQLAlchemy)

```bash
# SQLite
python generate.py --format database --db-url "sqlite:///fraudes.db" --size 500MB

# PostgreSQL
python generate.py --format database --db-url "postgresql://user:pass@host/db" --size 1GB
```

**Vantagens:** Consulta SQL imediata, integração com aplicações existentes.

---

## MinIO/S3

```bash
# Upload para MinIO
python generate.py --output minio://bucket/prefix --format parquet --size 5GB

# Requer variáveis de ambiente:
# MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
```

---

## Compressão

| Algoritmo | Cmd Flag | Ratio | Velocidade | Uso |
|-----------|----------|-------|------------|-----|
| **Nenhuma** | `--compression none` | 1:1 | Máxima | Debug, datasets pequenos |
| **gzip** | `--compression gzip` | ~5:1 | Lenta | Compatibilidade universal |
| **zstd** | `--compression zstd` | ~6:1 | Rápida | Melhor equilíbrio geral |
| **snappy** | `--compression snappy` | ~3:1 | Muito rápida | Streaming, Spark |

---

## Schema de Transação Bancária (117 campos)

### Identificação

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `tx_id` | string | `TX_000001` |
| `customer_id` | string | `CUST_000042` |
| `device_id` | string | `DEV_000015` |
| `timestamp` | datetime | `2024-03-15T14:32:18` |

### Valor e Tipo

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `amount` | float | `1523.45` |
| `currency` | string | `BRL` |
| `type` | string | `PIX`, `CREDIT_CARD`, `TED`, `DOC`, `BOLETO`, `DEBITO` |
| `channel` | string | `MOBILE_APP`, `WEB_BANKING`, `ATM`, `BRANCH` |

### Merchant

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `merchant_id` | string | `MERCH_000123` |
| `merchant_name` | string | `Supermercado Extra` |
| `mcc` | int | `5411` |
| `merchant_category` | string | `GROCERY` |

### Cartão

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `card_brand` | string | `VISA`, `MASTERCARD`, `ELO` |
| `card_type` | string | `CREDIT`, `DEBIT` |
| `entry_mode` | string | `CONTACTLESS`, `CHIP`, `MAGNETIC`, `ECOMMERCE` |
| `installments` | int | `1` – `12` |
| `cvv_verified` | bool | `true` |
| `three_ds_authenticated` | bool | `true` |

### PIX (campos BACEN)

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `pix_key_type` | string | `CPF`, `PHONE`, `EMAIL`, `RANDOM` |
| `pix_ispb` | string | `00000000` (ISPB do banco) |
| `pix_tipo_conta` | string | `CACC` (conta corrente) |
| `pix_holder_type` | string | `NATURAL_PERSON` |
| `pix_end_to_end_id` | string | `E00000000202403151432...` |

### Indicadores de Risco

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `fraud_score` | int | `0` – `100` |
| `fraud_risk_score` | int | `0` – `100` (17 sinais + 4 correlações) |
| `is_fraud` | bool | `true` / `false` |
| `fraud_type` | string | `CONTA_TOMADA`, `null` se legítimo |

### Velocidade e Comportamento

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `velocity_transactions_24h` | int | `5` |
| `accumulated_amount_24h` | float | `3500.00` |
| `unusual_time` | bool | `true` (madrugada) |
| `new_beneficiary` | bool | `true` |
| `beneficiary_account_age_days` | int | `15` |

### Geolocalização

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `latitude` | float | `-23.5505` |
| `longitude` | float | `-46.6333` |
| `unusual_location` | bool | `false` |
| `customer_state` | string | `SP` |
| `customer_city` | string | `São Paulo` |

### Sessão

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `session_duration_seconds` | int | `342` |
| `login_method` | string | `BIOMETRIC`, `PASSWORD`, `TOKEN` |
| `ip_address` | string | `189.45.xx.xx` |

### Status

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `status` | string | `APPROVED`, `DECLINED` |
| `refusal_reason` | string | `null`, `SUSPECTED_FRAUD`, `INSUFFICIENT_FUNDS` |

---

## Schema de Corrida Ride-Share

### Identificação

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `ride_id` | string | `RIDE_000001` |
| `driver_id` | string | `DRV_000042` |
| `passenger_id` | string | `CUST_000108` |
| `timestamp` | datetime | `2024-03-15T22:15:30` |

### Rota

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `origin_latitude` | float | `-23.5631` |
| `origin_longitude` | float | `-46.6544` |
| `destination_latitude` | float | `-23.5886` |
| `destination_longitude` | float | `-46.6822` |
| `distance_km` | float | `6.3` |
| `duration_minutes` | float | `22.5` |

### Tarifa

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `base_fare` | float | `5.50` |
| `distance_rate` | float | `12.60` |
| `duration_rate` | float | `6.75` |
| `surge_multiplier` | float | `1.4` |
| `total_fare` | float | `34.79` |

### Motorista

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `driver_name` | string | `José da Silva` |
| `cnh_number` | string | `12345678901` |
| `cnh_category` | string | `B`, `AB`, `C` |
| `vehicle_plate` | string | `ABC1D23` (Mercosul) |
| `vehicle_model` | string | `Toyota Corolla 2022` |
| `driver_rating` | float | `4.85` |
| `trips_completed` | int | `1523` |

### App e Categoria

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `app` | string | `Uber`, `99`, `Cabify`, `InDriver` |
| `vehicle_category` | string | `ECONOMY`, `COMFORT`, `PREMIUM` |
| `payment_method` | string | `PIX`, `CREDIT_CARD`, `CASH` |

### Fraude

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `is_fraud` | bool | `true` / `false` |
| `fraud_type` | string | `GPS_SPOOFING`, `null` se legítimo |
| `fraud_score` | int | `0` – `100` |

---

## JSON Schema Declarativo

Para gerar dados com campos customizados, use o modo schema.

### Exemplo: Schema Banking Completo

```json
{
  "name": "banking_full",
  "description": "Full banking transaction schema",
  "fields": {
    "transaction_id": "transaction.tx_id",
    "amount": "transaction.amount",
    "currency": "static:BRL",
    "timestamp": "transaction.timestamp",
    "type": "transaction.type",
    "channel": "transaction.channel",
    "customer_cpf": "customer.cpf",
    "customer_name": "customer.name",
    "customer_state": "customer.state",
    "merchant_name": "transaction.merchant_name",
    "merchant_mcc": "transaction.mcc",
    "is_fraud": "transaction.is_fraud",
    "fraud_type": "transaction.fraud_type",
    "fraud_score": "transaction.fraud_risk_score"
  }
}
```

### Exemplo: Schema Minimalista

```json
{
  "name": "banking_minimal",
  "fields": {
    "id": "transaction.tx_id",
    "valor": "transaction.amount",
    "fraude": "transaction.is_fraud"
  }
}
```

### Referências de Campo Disponíveis

| Prefixo | Fonte | Exemplo |
|---------|-------|---------|
| `transaction.*` | Dados da transação | `transaction.amount` |
| `customer.*` | Dados do cliente | `customer.cpf` |
| `device.*` | Dados do dispositivo | `device.os` |
| `ride.*` | Dados da corrida | `ride.distance_km` |
| `static:VALOR` | Valor constante | `static:BRL` |
| `faker:METODO` | Faker pt-BR | `faker:company` |

---

## Schemas Pré-definidos

| Arquivo | Campos | Descrição |
|---------|--------|-----------|
| `schemas/banking_minimal.json` | ~10 | Campos essenciais apenas |
| `schemas/banking_full.json` | ~50 | Schema bancário completo |
| `schemas/rideshare_full.json` | ~40 | Schema ride-share completo |
| `schemas/custom_empresa.json` | variável | Template para customização |
