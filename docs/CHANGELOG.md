# 📜 Changelog - Brazilian Fraud Data Generator

## Histórico de Evolução do Projeto

Este documento detalha a evolução do projeto desde a v1.0 até a v4.0, incluindo mudanças, cuidados na migração e novidades de cada versão.

---

## 🚀 Visão Geral das Versões

| Versão | Nome Código | Foco Principal | Data |
|--------|-------------|----------------|------|
| v1.0 | **Genesis** | Transações bancárias básicas | 2024-Q3 |
| v2.0 | **Expansion** | Perfis comportamentais + Multi-formato | 2024-Q4 |
| v3.0 | **Stream** | Kafka streaming + Conexões | 2025-Q1 |
| v4.0 | **DataLake** | MinIO/S3 + Ride-share + Enterprise | 2025-Q2 |

---

## 📦 v1.0 "Genesis" - Fundação

### O que era
A primeira versão focada em gerar dados básicos de transações bancárias brasileiras.

### Funcionalidades
- ✅ Geração de clientes com CPF válido
- ✅ Transações básicas (PIX, cartão, TED)
- ✅ Bancos brasileiros reais
- ✅ Exportação JSON/JSONL
- ✅ Taxa de fraude configurável

### Limitações
- ❌ Apenas um formato de saída
- ❌ Sem perfis comportamentais (transações aleatórias)
- ❌ Sem streaming
- ❌ Single-threaded (lento para grandes volumes)
- ❌ Sem validação de dados

### Estrutura de Arquivos
```
output/
├── customers.json
└── transactions.json
```

### Comando Básico
```bash
python generate.py --count 1000
```

---

## 📦 v2.0 "Expansion" - Perfis e Formatos

### Mudanças da v1 → v2

#### ✨ Novidades
| Feature | Descrição |
|---------|-----------|
| **Perfis Comportamentais** | 6 perfis realistas (young_digital, family_provider, etc.) |
| **Multi-formato** | JSON, CSV, Parquet |
| **Multiprocessing** | Geração paralela com workers |
| **Devices** | Dispositivos vinculados aos clientes |
| **Fraud Score** | Score de risco em cada transação |
| **Seed** | Reprodutibilidade dos dados |

#### 🔧 Cuidados na Migração v1 → v2
```diff
# Antes (v1)
- python generate.py --count 1000

# Depois (v2)
+ python generate.py --size 100MB --format jsonl
```

⚠️ **Breaking Changes:**
- Argumento `--count` removido, usar `--size`
- Estrutura do JSON de transações mudou (novos campos)
- Campo `fraud_score` adicionado (float 0-100)

#### Schema Changes
```diff
# Transaction schema
{
  "transaction_id": "...",
  "customer_id": "...",
+ "device_id": "...",
  "timestamp": "...",
  "tipo": "...",
  "valor": 0.0,
+ "fraud_score": 0.0,
+ "horario_incomum": false,
+ "valor_atipico": false,
  "is_fraud": false
}
```

### Estrutura de Arquivos v2
```
output/
├── customers.jsonl
├── devices.jsonl          # NOVO
└── transactions_00000.jsonl
```

---

## 📦 v3.0 "Stream" - Streaming e Conexões

### Mudanças da v2 → v3

#### ✨ Novidades
| Feature | Descrição |
|---------|-----------|
| **Kafka Streaming** | Envio em tempo real para Kafka |
| **Webhook** | Envio para APIs REST |
| **stdout** | Debug no terminal |
| **Rate Control** | Controle de eventos/segundo |
| **Arquitetura Modular** | Separação em connections, exporters, generators |
| **Docker Support** | Dockerfile e docker-compose |

#### 🔧 Cuidados na Migração v2 → v3
```diff
# Nova estrutura de projeto
src/fraud_generator/
├── generators/      # Customer, Device, Transaction
├── exporters/       # JSON, CSV, Parquet
├── connections/     # Kafka, Webhook, Stdout  # NOVO
├── validators/      # CPF validation
└── config/          # Banks, MCCs, Geography
```

⚠️ **Breaking Changes:**
- Estrutura de diretórios reorganizada
- Imports mudaram para `from fraud_generator import ...`
- Novo script `stream.py` para streaming

#### Novos Comandos
```bash
# Batch (mantido)
python generate.py --size 1GB

# Streaming (NOVO)
python stream.py --target kafka --kafka-server localhost:9092 --rate 100
python stream.py --target stdout --rate 5
python stream.py --target webhook --webhook-url http://api:8080/ingest
```

#### Dependências Adicionais
```bash
# requirements-streaming.txt (NOVO)
kafka-python>=2.0.2
requests>=2.28.0
```

---

## 📦 v4.0 "DataLake" - Enterprise Ready

### Mudanças da v3 → v4

#### ✨ Novidades Principais

| Feature | Descrição | Impacto |
|---------|-----------|---------|
| **🚗 Ride-Share Data** | Uber, 99, Cabify, InDriver | Novo domínio de dados |
| **📦 MinIO/S3 Upload** | Upload direto para object storage | Integração Data Lake |
| **🚘 Drivers** | Motoristas com CNH, veículos, rating | Novo modelo |
| **🔴 Ride Frauds** | 7 tipos de fraude de corrida | GPS spoofing, etc. |
| **📊 Date Partitioning** | Organização YYYY/MM/DD no MinIO | Otimização Spark |
| **⚡ Memory Optimization** | Suporte a 50GB+ de geração | Enterprise scale |

#### 🆕 Novos Tipos de Dados

**`--type transactions`** (padrão - mantido da v3)
```
output/
├── customers.jsonl
├── devices.jsonl
└── transactions_*.jsonl
```

**`--type rides`** (NOVO)
```
output/
├── customers.jsonl      # Passageiros
├── devices.jsonl
├── drivers.jsonl        # NOVO - Motoristas
└── rides_*.jsonl        # NOVO - Corridas
```

**`--type all`** (NOVO)
```
output/
├── customers.jsonl
├── devices.jsonl
├── drivers.jsonl
├── transactions_*.jsonl
└── rides_*.jsonl
```

#### 🔧 Cuidados na Migração v3 → v4

```diff
# Novos argumentos
+ --type {transactions,rides,all}
+ --output minio://bucket/prefix
+ --minio-endpoint http://localhost:9000
+ --minio-access-key minioadmin
+ --minio-secret-key minioadmin
+ --no-date-partition
```

⚠️ **Breaking Changes:**
- Novo argumento `--type` (padrão: transactions, mantém compatibilidade)
- MinIO exporter requer `boto3` instalado
- Novos schemas para Driver e Ride

#### Novos Schemas

**Driver (NOVO)**
```json
{
  "driver_id": "DRV_0000000001",
  "nome": "João Carlos Silva",
  "cpf": "987.654.321-00",
  "cnh_numero": "12345678901",
  "cnh_categoria": "B",
  "cnh_validade": "2027-05-15",
  "vehicle_plate": "ABC1D23",
  "vehicle_brand": "Hyundai",
  "vehicle_model": "HB20",
  "vehicle_year": 2022,
  "vehicle_color": "Prata",
  "rating": 4.85,
  "trips_completed": 1250,
  "active_apps": ["UBER", "99"],
  "operating_city": "São Paulo",
  "operating_state": "SP"
}
```

**Ride (NOVO)**
```json
{
  "ride_id": "RIDE_000000000001",
  "timestamp": "2024-03-15T14:32:45",
  "app": "UBER",
  "category": "UberX",
  "driver_id": "DRV_0000000001",
  "passenger_id": "CUST_000000000001",
  "pickup_location": {
    "lat": -23.5614,
    "lon": -46.6558,
    "name": "Av. Paulista",
    "city": "São Paulo",
    "state": "SP"
  },
  "dropoff_location": {
    "lat": -23.6261,
    "lon": -46.6564,
    "name": "Aeroporto de Congonhas",
    "city": "São Paulo",
    "state": "SP"
  },
  "distance_km": 8.5,
  "duration_minutes": 25,
  "base_fare": 18.50,
  "surge_multiplier": 1.5,
  "final_fare": 27.75,
  "payment_method": "PIX",
  "status": "FINALIZADA",
  "is_fraud": false,
  "fraud_type": null
}
```

#### Novos Tipos de Fraude (Rides)

| Tipo | Descrição |
|------|-----------|
| `GPS_SPOOFING` | GPS falso para aumentar distância |
| `DRIVER_COLLUSION` | Conluio motorista-passageiro |
| `SURGE_ABUSE` | Manipulação de preço dinâmico |
| `PROMO_ABUSE` | Abuso de código promocional |
| `FAKE_RIDE` | Corrida falsa para pagamento |
| `IDENTITY_FRAUD` | Identidade falsa |
| `PAYMENT_FRAUD` | Pagamento fraudulento |

#### MinIO/S3 Integration

```bash
# Upload direto para MinIO
python generate.py --size 1GB \
    --output minio://fraud-data/raw \
    --minio-endpoint http://localhost:9000

# Com particionamento por data
# Resultado: minio://fraud-data/raw/2025/12/06/transactions_00000.jsonl
```

#### Dependências Adicionais v4
```bash
# requirements.txt atualizado
+ boto3>=1.26.0
+ botocore>=1.29.0
```

---

## 📊 Comparativo de Versões

| Feature | v1 | v2 | v3 | v4 |
|---------|----|----|----|----|
| Transações bancárias | ✅ | ✅ | ✅ | ✅ |
| CPF válido | ✅ | ✅ | ✅ | ✅ |
| Perfis comportamentais | ❌ | ✅ | ✅ | ✅ |
| Multi-formato | ❌ | ✅ | ✅ | ✅ |
| Multiprocessing | ❌ | ✅ | ✅ | ✅ |
| Kafka streaming | ❌ | ❌ | ✅ | ✅ |
| Webhook | ❌ | ❌ | ✅ | ✅ |
| Docker | ❌ | ❌ | ✅ | ✅ |
| **Ride-share** | ❌ | ❌ | ❌ | ✅ |
| **MinIO/S3** | ❌ | ❌ | ❌ | ✅ |
| **Drivers** | ❌ | ❌ | ❌ | ✅ |
| **50GB+ support** | ❌ | ❌ | ❌ | ✅ |

---

## 🎯 Roadmap Futuro (v5+)

### Possíveis Features
- [ ] Schema Registry (Avro/Protobuf)
- [ ] Delta Lake / Iceberg support
- [ ] Real-time fraud detection demo
- [ ] Airflow DAG templates
- [ ] dbt models incluídos
- [ ] Flink connector
- [ ] PII masking options
- [ ] Multi-language (EN/ES data)

---

## 🏷️ Sugestões de Nomes para Versões

### Já Usados
| Versão | Nome | Significado |
|--------|------|-------------|
| v1.0 | **Genesis** | Início, fundação |
| v2.0 | **Expansion** | Expansão de funcionalidades |
| v3.0 | **Stream** | Streaming em tempo real |
| v4.0 | **DataLake** | Integração com data lakes |

### Sugestões Futuras
| Versão | Nome | Tema |
|--------|------|------|
| v5.0 | **Lakehouse** | Delta/Iceberg |
| v5.0 | **Sentinel** | Detecção de fraude |
| v5.0 | **Orchestrate** | Airflow/dbt |
| v5.0 | **Shield** | Segurança/PII |
| v5.0 | **Nexus** | Conectores |

### Nomes Alternativos para o Projeto
| Nome | Significado |
|------|-------------|
| **FraudForge** | Forjar dados de fraude |
| **BrasilData** | Dados brasileiros |
| **SyntheticBR** | Dados sintéticos BR |
| **DataMockerBR** | Mock de dados BR |
| **FraudStream** | Stream de fraudes |
| **TxnGenerator** | Gerador de transações |

---

## 🖼️ Prompt para Geração de Imagem (Gemini/DALL-E)

### Prompt para Imagem de Evolução v4

```
Create a modern, professional infographic showing the evolution of a data generation software from v1 to v4.

Style: Clean tech illustration, dark theme with neon accents (blue, purple, green), Brazilian flag colors subtle in background.

Layout: Horizontal timeline from left to right with 4 major milestones.

Version 1 "Genesis" (left):
- Simple database icon
- Single arrow pointing down
- Label: "Basic Transactions"
- Color: Gray/Silver
- Small, simple

Version 2 "Expansion" (center-left):
- Multiple format icons (JSON, CSV, Parquet)
- User profiles icons (6 personas)
- Parallel arrows (multiprocessing)
- Label: "Profiles & Formats"
- Color: Blue
- Medium size

Version 3 "Stream" (center-right):
- Kafka logo stylized
- Real-time streaming waves
- Docker whale icon
- API webhook icon
- Label: "Real-time Streaming"
- Color: Purple
- Larger size

Version 4 "DataLake" (right):
- Large data lake illustration
- MinIO/S3 bucket icon
- Car/ride icon (Uber style)
- Brazilian map outline
- Multiple data streams flowing into lake
- Label: "Enterprise Data Lake"
- Color: Green/Gold (Brazilian)
- Largest, most prominent

Additional elements:
- Brazilian flag colors subtly integrated
- "🇧🇷 Brazilian Fraud Data Generator" title at top
- Version numbers clearly visible
- Modern, tech startup aesthetic
- Gradient background dark blue to black
- Glowing connection lines between versions
- Small icons: CPF, PIX, credit card, car, driver
- "v4.0 DataLake - Enterprise Ready" badge glowing

Text overlay:
- "From Simple Generator to Enterprise Data Lake"
- "4 Versions of Evolution"
- Stats: "50GB+ | Kafka | MinIO | Rides"
```

### Prompt Alternativo (Mais Simples)

```
Tech evolution infographic, 4 stages left to right:

1. Small gray box "v1 Genesis" - basic transaction icon
2. Medium blue box "v2 Expansion" - multiple file formats, user icons
3. Large purple box "v3 Stream" - Kafka streams, Docker whale
4. Extra large green/gold box "v4 DataLake" - S3 bucket, car icon, data lake

Brazilian theme, dark background, neon accents, modern tech style.
Title: "Brazilian Fraud Data Generator Evolution"
Subtitle: "From MVP to Enterprise Data Lake"
```

### Prompt para Logo v4

```
Modern tech logo for "Brazilian Fraud Data Generator v4"

Elements:
- Stylized "BFG" or "BFDG" letters
- Brazilian flag colors (green, yellow, blue)
- Data lake/wave motif
- Subtle fraud/shield icon
- Clean, minimal design
- Works on dark and light backgrounds

Style: Flat design, geometric, tech startup aesthetic
Colors: Primary green (#009739), accent gold (#FFDF00), blue (#002776)
```

---

## 📝 Notas de Migração

### v3 → v4 Checklist

- [ ] Atualizar requirements.txt (adicionar boto3)
- [ ] Verificar se `--type transactions` mantém comportamento anterior
- [ ] Testar MinIO credentials se usar upload direto
- [ ] Atualizar docker-compose se necessário
- [ ] Revisar schemas no Spark (novos campos)
- [ ] Documentar novos tipos de fraude para equipe de ML

### Compatibilidade

| Versão Anterior | Compatível com v4? | Notas |
|-----------------|-------------------|-------|
| v3.x | ✅ Sim | Usar `--type transactions` |
| v2.x | ⚠️ Parcial | Verificar imports |
| v1.x | ❌ Não | Reescrever scripts |

---

*Última atualização: Dezembro 2025*
*Versão atual: v4.0-beta*
