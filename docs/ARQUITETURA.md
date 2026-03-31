# Arquitetura — synthfin-data v4.15.1

> Documento técnico completo com diagramas de todas as camadas arquiteturais do projeto.

---

## Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Modos de Execução](#2-modos-de-execução)
3. [Arquitetura SOLID — Pacote `cli/`](#3-arquitetura-solid--pacote-cli)
4. [Pipeline de Geração de Dados](#4-pipeline-de-geração-de-dados)
5. [Sistema de Schema Declarativo](#5-sistema-de-schema-declarativo)
6. [Execução Paralela — Workers](#6-execução-paralela--workers)
7. [Modo Streaming (`stream.py`)](#7-modo-streaming-streampy)
8. [Camada de Exportadores](#8-camada-de-exportadores)
9. [Camada de Conexões (Streaming)](#9-camada-de-conexões-streaming)
10. [Fluxo de Dados Completo — End-to-End](#10-fluxo-de-dados-completo--end-to-end)
11. [Decisões de Design](#11-decisões-de-design)

---

## 1. Visão Geral do Sistema

```
╔══════════════════════════════════════════════════════════════════════════════╗
║           BRAZILIAN FRAUD DATA GENERATOR v4.1.0                            ║
║                                                                            ║
║  Gerador sintético de alta performance para dados bancários e ride-share   ║
║  brasileiros com injeção de fraude configurável.                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

      Usuário / CI/CD / Docker
             │
       ┌─────┴──────┐
       │            │
  generate.py   stream.py
  (batch mode)  (streaming mode)
       │            │
       ▼            ▼
  ┌─────────────────────────────────────────────────────────────┐
  │               src/fraud_generator/                          │
  │                                                             │
  │  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  │
  │  │  cli/    │  │generators/│  │exporters/│  │   schema/│  │
  │  │ (SOLID)  │  │(entidades)│  │(formatos)│  │(decl. JSON│ │
  │  └──────────┘  └───────────┘  └──────────┘  └──────────┘  │
  │                                                             │
  │  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  │
  │  │ profiles/│  │  config/  │  │  models/ │  │  utils/  │  │
  │  │(comportam│  │(configs   │  │(dataclass│  │(helpers) │  │
  │  │  entos)  │  │ estáticas)│  │       es)│  │          │  │
  │  └──────────┘  └───────────┘  └──────────┘  └──────────┘  │
  └─────────────────────────────────────────────────────────────┘
             │                              │
             ▼                              ▼
      📁 Local / DB              ☁️  MinIO / S3 / Kafka
```

---

## 2. Modos de Execução

O sistema suporta três modos independentes. A escolha é feita em `generate.py` através de **dispatch por condição**, seguindo o padrão **Chain of Responsibility** simplificado:

```
generate.py → main()
       │
       ├── args.schema ?  ──────────► SchemaRunner  (JSON declarativo)
       │       YES
       │
       ├── is_minio_url(args.output) ?───► MinIORunner  (S3/MinIO)
       │       YES
       │
       └── default ─────────────────► BatchRunner  (local / DB)
```

### Diagrama de Sequência — Seleção de Modo

```
Usuário          generate.py       Runner          Pipeline
   │                  │               │                │
   │ python generate  │               │                │
   │──────────────────►               │                │
   │                  │ parse_args()  │                │
   │                  │──────┐        │                │
   │                  │◄─────┘        │                │
   │                  │               │                │
   │                  │ --schema ?    │                │
   │                  │──YES──────────► SchemaRunner   │
   │                  │               │   .run(args)──►│
   │                  │               │                │ generate_list()
   │                  │               │                │──────┐
   │                  │               │                │◄─────┘
   │                  │               │◄───────────────│ write JSONL
   │                  │               │                │
   │                  │ MinIO URL ?   │                │
   │                  │──YES──────────► MinIORunner    │
   │                  │               │   .run(args)──►│ upload S3
   │                  │               │                │
   │                  │ default       │                │
   │                  │───────────────► BatchRunner    │
   │                  │               │   .run(args)──►│ write local
   │◄─────────────────│               │                │
   │   exit(0)        │               │                │
```

---

## 3. Arquitetura SOLID — Pacote `cli/`

### Princípios aplicados

| Princípio | Aplicação concreta |
|---|---|
| **S** — Single Responsibility | Cada módulo faz UMA coisa: `args.py` só declara args, `constants.py` só tem números, `index_builder.py` só gera índices |
| **O** — Open/Closed | Novos modes: criar subclasse de `BaseRunner` + 1 linha em `generate.py`. Runners existentes não são tocados |
| **L** — Liskov Substitution | `BatchRunner`, `MinIORunner`, `SchemaRunner` são substituíveis entre si onde `BaseRunner` é esperado |
| **I** — Interface Segregation | `BaseRunner` expõe apenas `run(args)`. Nenhum runner conhece internos do outro |
| **D** — Dependency Inversion | `generate.py` depende da abstração `BaseRunner`, não das classes concretas diretamente |

### Estrutura do Pacote

```
src/fraud_generator/cli/
│
├── __init__.py            ← documentação do pacote
│
├── constants.py           ← S: constantes numéricas (TARGET_FILE_SIZE_MB, etc.)
│
├── args.py                ← S: build_parser() — declara todos os argumentos CLI
│
├── index_builder.py       ← S: generate_customers_and_devices()
│                                generate_drivers()
│
├── runners/               ← padrão Command + Strategy
│   ├── __init__.py        ← exports públicos
│   ├── base.py            ← D+L: BaseRunner(ABC) { run(args) }
│   ├── schema_runner.py   ← O: SchemaRunner(BaseRunner)
│   ├── batch_runner.py    ← O: BatchRunner(BaseRunner)
│   └── minio_runner.py    ← O: MinIORunner(BaseRunner)
│
└── workers/               ← funções picklable para ProcessPoolExecutor
    ├── __init__.py
    ├── tx_worker.py        ← worker_generate_batch()
    ├── ride_worker.py      ← worker_generate_rides_batch()
    ├── batch_gen.py        ← generate_transaction_batch()  (em-memória)
    │                          generate_ride_batch()
    └── minio_parquet.py    ← worker_upload_parquet_transactions()
                               worker_upload_parquet_rides()
```

### Hierarquia de Runners

```
             BaseRunner (ABC)
             run(args: Namespace) → None
                      │
         ┌────────────┼────────────┐
         │            │            │
   SchemaRunner  BatchRunner  MinIORunner
         │            │            │
   --schema flag  local/DB    MinIO/S3
   SchemaEngine   4 fases     4 fases
   JSONL out      local out   upload
```

### Adicionando um novo modo (exemplo: AvroRunner)

```diff
# 1. Criar src/fraud_generator/cli/runners/avro_runner.py
+ class AvroRunner(BaseRunner):
+     def run(self, args): ...

# 2. Exportar em runners/__init__.py
+ from fraud_generator.cli.runners.avro_runner import AvroRunner

# 3. Uma linha em generate.py
+ if args.format == "avro":
+     AvroRunner().run(args)
+     return

# Zero mudanças em BatchRunner, MinIORunner, SchemaRunner
```

---

## 4. Pipeline de Geração de Dados

O `BatchRunner` orquestra 4 fases sequenciais com checkpoint a cada fase:

```
╔══════════════════════════════════════════════════════════════╗
║ FASE 1: Clientes + Dispositivos                             ║
╠══════════════════════════════════════════════════════════════╣
║  index_builder.generate_customers_and_devices()             ║
║                                                             ║
║  ┌──────────────┐   1-N   ┌──────────────┐                 ║
║  │ CustomerGen  │────────►│ DeviceGen    │                 ║
║  │ .generate()  │         │ .generate_   │                 ║
║  │              │         │  for_customer│                 ║
║  └──────┬───────┘         └──────┬───────┘                 ║
║         │                        │                         ║
║         ▼                        ▼                         ║
║  CustomerIndex(tuple) + DeviceIndex(tuple) → picklable      ║
╚══════════════════════════════════════════════════════════════╝
                          │
                     (serializado via pickle para workers)
                          │
╔══════════════════════════════════════════════════════════════╗
║ FASE 2: Transações (paralela)                               ║
╠══════════════════════════════════════════════════════════════╣
║                                                             ║
║  ProcessPoolExecutor (bypass GIL — CPU bound)               ║
║                                                             ║
║  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       ║
║  │Worker 0 │  │Worker 1 │  │Worker 2 │  │Worker N │       ║
║  │tx_00000 │  │tx_00001 │  │tx_00002 │  │tx_000NN │       ║
║  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       ║
║       │            │            │             │            ║
║       └────────────┴────────────┴─────────────┘            ║
║                          │                                 ║
║                    📁 output/                              ║
╚══════════════════════════════════════════════════════════════╝
╔══════════════════════════════════════════════════════════════╗
║ FASE 3: Motoristas (sequencial — rápido)                    ║
╠══════════════════════════════════════════════════════════════╣
║  index_builder.generate_drivers()                           ║
║  DriverGen.generate() × N → DriverIndex(tuple)             ║
╚══════════════════════════════════════════════════════════════╝
╔══════════════════════════════════════════════════════════════╗
║ FASE 4: Corridas (paralela — mesmo padrão da Fase 2)        ║
╠══════════════════════════════════════════════════════════════╣
║  ProcessPoolExecutor → ride_worker.worker_generate_rides_batch║
╚══════════════════════════════════════════════════════════════╝
```

### Entidades Geradas e Relacionamentos

```
Customer ──────────────────────────────────────────────────┐
│  customer_id                                              │
│  cpf (válido via algoritmo)                              │
│  address { state, city, ... }                            │
│  behavioral_profile (7 tipos)                            │
│  bank_code, risk_level, credit_score                     │
└──► Device (1-N)                                          │
         │  device_id                                      │
         │  customer_id (FK)                               │
         │  device_type, os, is_mobile                     │
         │                                                 │
         └──► Transaction                                  │
                   tx_id                                   │
                   customer_id (FK)                        │
                   device_id (FK)                          │
                   amount, type, channel                   │
                   is_fraud, fraud_score                   │
                   merchant { id, name, mcc }              │
                   pix { key_type, dest_bank }     ◄────────┘
                   velocity { txns_24h, amount_24h }

Driver ─────────────────────────────────────────────────────┐
│  driver_id                                                 │
│  cpf (válido)                                             │
│  operating_state, active_apps                             │
│  vehicle { plate, model, year }                           │
│  cnh { number, category }                                 │
│  rating, total_rides                                       │
└──► Ride                                                    │
          ride_id                                            │
          driver_id (FK)                                     │
          passenger_id (FK — Customer)     ◄─────────────────┘
          app (Uber/99/InDriver/Cabify)
          origin { lat, lon, address }
          destination { lat, lon, address }
          distance_km (Haversine)
          fare_total, surge_multiplier
          is_fraud, fraud_type
```

---

## 5. Sistema de Schema Declarativo

Ativado com `--schema schema.json`. Permite ao usuário definir a estrutura exata de saída.

### Arquitetura do Módulo `schema/`

```
src/fraud_generator/schema/
│
├── __init__.py           ← exports: SchemaEngine, SchemaParser,
│                                    FieldMapper, AISchemaCorrector
│
├── parser.py             ← SchemaParser
│   ┌──────────────────────────────────────────────────────┐
│   │ from_file(path)   → parsed dict                     │
│   │ from_string(json) → parsed dict                     │
│   │ from_dict(data)   → parsed dict (validado)          │
│   │ summarize(parsed) → string legível                  │
│   │                                                      │
│   │ Valida: schema_version, profile, fraud_rate,        │
│   │         output (namespace.field / static: / faker:) │
│   │ FIELD_CATALOG: mapping namespace → campos válidos   │
│   └──────────────────────────────────────────────────────┘
│
├── mapper.py             ← FieldMapper
│   ┌──────────────────────────────────────────────────────┐
│   │ resolve(output_tree, *, transaction, customer, ...)  │
│   │                                                      │
│   │ Tipos de referência:                                │
│   │   "transaction.amount"  → namespace.field           │
│   │   "static:My Company"   → valor literal             │
│   │   "faker:uuid4"         → Faker(pt_BR).uuid4()      │
│   │   "faker:city:São Paulo"→ Faker method + arg        │
│   │                                                      │
│   │ Suporta aninhamento:                                │
│   │   "customer.address.city" → dict dentro de dict     │
│   └──────────────────────────────────────────────────────┘
│
├── ai_corrector.py       ← AISchemaCorrector
│   ┌──────────────────────────────────────────────────────┐
│   │ correct(schema_input: str) → CorrectionResult       │
│   │                                                      │
│   │ Provedores:                                         │
│   │   "openai"    → gpt-4o-mini (OPENAI_API_KEY)        │
│   │   "anthropic" → claude-3-haiku (ANTHROPIC_API_KEY)  │
│   │   "none"      → heurísticas apenas                  │
│   │                                                      │
│   │ Heurísticas automáticas:                            │
│   │   - Remove comentários JS (//, /* */)               │
│   │   - Remove trailing commas                          │
│   │   - Resolve aliases ("valor" → "transaction.amount")│
│   │   - 40+ aliases mapeados                            │
│   └──────────────────────────────────────────────────────┘
│
└── engine.py             ← SchemaEngine (orquestrador)
    ┌──────────────────────────────────────────────────────┐
    │ from_file(path, *, auto_correct, ai_provider)        │
    │ from_string(json, *, auto_correct, ai_provider)      │
    │                                                      │
    │ generate(count) → Iterator[dict]                    │
    │ generate_list(count) → List[dict]                   │
    │ summary() → str                                      │
    └──────────────────────────────────────────────────────┘
```

### Fluxo de Processamento de um Schema

```
Arquivo JSON do usuário
         │
         ▼
┌─────────────────────┐
│   AISchemaCorrector │  (se auto_correct=True)
│                     │
│  1. Tenta parse JSON│
│  2. Se falhar:      │
│     - remove // e   │
│       trailing commas│
│     - aplica aliases│
│  3. Se provider !None│
│     envia ao LLM    │
└──────────┬──────────┘
           │ JSON corrigido
           ▼
┌─────────────────────┐
│    SchemaParser     │
│                     │
│  Valida estrutura:  │
│  - schema_version   │
│  - profile válido   │
│  - fraud_rate 0..1  │
│  - output fields    │
│    (FIELD_CATALOG)  │
└──────────┬──────────┘
           │ parsed dict
           ▼
┌─────────────────────┐
│    SchemaEngine     │
│                     │
│  Inicia geradores:  │
│  - CustomerGenerator│
│  - DeviceGenerator  │
│  - TransactionGen   │
│  - DriverGenerator  │
│  - RideGenerator    │
│  (conforme profile) │
└──────────┬──────────┘
           │
           ▼ para cada registro
┌─────────────────────┐
│    FieldMapper      │
│                     │
│  output_template:   │
│  {                  │
│  "id": "tx.tx_id"  │──► resolve → "TXN_abc123"
│  "val": "tx.amount"│──► resolve → 250.00
│  "emp": "static:X" │──► resolve → "X"
│  "uid": "faker:uuid"│──► resolve → "3f9a-..."
│  }                  │
└──────────┬──────────┘
           │ dict resolvido
           ▼
      JSONL output
```

### Formato do Schema JSON

```json
{
  "schema_version": "1.0",
  "profile": "banking",        // banking | ride_share | all
  "fraud_rate": 0.05,
  "seed": 42,                  // opcional — reprodutibilidade
  "output": {
    "meu_campo":   "transaction.amount",     // namespace.field
    "empresa":     "static:Minha Empresa",   // valor literal
    "uuid":        "faker:uuid4",            // método Faker
    "aninhado": {
      "cpf":       "customer.cpf",           // suporta objetos
      "cidade":    "customer.address.city"   // e sub-campos
    }
  }
}
```

### Aliases Automáticos (AI Corrector)

```
"valor"     → "transaction.amount"
"cpf"       → "customer.cpf"
"cidade"    → "customer.address.city"
"estado"    → "customer.address.state"
"fraude"    → "transaction.is_fraud"
"banco"     → "customer.bank_name"
"tipo"      → "transaction.type"
"canal"     → "transaction.channel"
...40+ aliases mapeados
```

---

## 6. Execução Paralela — Workers

### Por que ProcessPoolExecutor?

```
Python GIL (Global Interpreter Lock)
        │
        ▼
   Threading (I/O)         Multiprocessing (CPU)
   ┌─────────────┐          ┌──────────────────┐
   │ ThreadPool  │          │  ProcessPool     │
   │ execução    │          │  execução REAL   │
   │ cooperativa │          │  paralela        │
   │ 1 CPU core  │          │  N CPU cores     │
   └─────────────┘          └──────────────────┘
         ▲                          ▲
         │                          │
   JSONL/CSV MinIO            Parquet, local JSONL/CSV
   (I/O bound)                (CPU bound — geração)
```

### Topologia de Workers

```
BatchRunner._run_local_workers()
         │
         ├── parallel_mode == "thread"
         │         │
         │         ▼
         │   ThreadPoolExecutor(max_workers=min(W, N, 16))
         │   ┌───────────────────────────────────────────┐
         │   │ submit(worker_fn, args_0) → Future        │
         │   │ submit(worker_fn, args_1) → Future        │
         │   │ ...                                       │
         │   │ as_completed → results                    │
         │   └───────────────────────────────────────────┘
         │
         └── parallel_mode in ("auto", "process")
                   │
                   ▼
           ProcessPoolExecutor(max_workers=min(W, N, CPU))
           ┌────────────────────────────────────────────────┐
           │                                                │
           │  Parent Process (BatchRunner)                  │
           │  ┌──────────────────────────────┐             │
           │  │ pickle args_tuple → bytes    │             │
           │  │ send via IPC pipe            │             │
           │  └──────────────────────────────┘             │
           │             │                                  │
           │    ┌────────┴────────┐                        │
           │    │                 │                        │
           │  Child-0           Child-1  ...  Child-N      │
           │  worker_generate_  worker_generate_           │
           │  batch(args_0)     batch(args_1)              │
           │    │                 │                        │
           │    ▼                 ▼                        │
           │  tx_00000.jsonl   tx_00001.jsonl  ...         │
           │                                               │
           └───────────────────────────────────────────────┘
```

### Requisito de Pickling

```
❌ PROIBIDO — não pode ser worker:        ✅ CORRETO — top-level:
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ def main():                  │         │ # workers/tx_worker.py       │
│   def _inner_worker(args):   │         │ def worker_generate_batch(   │
│       ...                    │         │     args: tuple) -> str:     │
│   ProcessPoolExecutor(...)   │         │     ...                      │
│     .submit(_inner_worker)   │         │                              │
│ # PicklingError!             │         │ # pickle resolve por nome    │
└──────────────────────────────┘         └──────────────────────────────┘
```

### Seed Determinístico por Worker

```python
# Cada worker recebe um seed derivado do seed global
# Garante reprodutibilidade independente do número de workers

worker_seed = seed + batch_id × 12_345    # transações
worker_seed = seed + batch_id × 54_321    # corridas

# Resultado: --seed 42 com 4 workers == --seed 42 com 8 workers
# (mesmo dataset na mesma ordem total)
```

---

## 7. Modo Streaming (`stream.py`)

Gera eventos contínuos em vez de arquivos batch. Projetado para integração com sistemas em tempo real.

```
stream.py
   │
   ▼
StreamingMode
   │
   ├── parse_args()
   │     --target {stdout,kafka,webhook}
   │     --rate N (eventos/seg)
   │     --type {transactions,rides,all}
   │
   ▼
ConnectionFactory.get_connection(target)
   │
   ├── "stdout"  → StdoutConnection
   ├── "kafka"   → KafkaConnection
   └── "webhook" → WebhookConnection

   ▼
Generator loop (sinal SIGINT/SIGTERM → _running = False)
   │
   while _running:
   │    record = generator.generate(...)
   │    connection.send(record)
   │    sleep(1/rate)
   │
   ▼
connection.close()


Topologia de Conexões:
─────────────────────

            ConnectionProtocol (ABC)
            connect() → None
            send(record: dict) → None
            close() → None
                 │
     ┌───────────┼───────────┐
     │           │           │
StdoutConn  KafkaConn  WebhookConn
     │           │           │
  json.dumps  Producer    requests.post
  + print    .produce()   (batched)
```

### Graceful Shutdown

```
SIGINT / SIGTERM
      │
      ▼
_signal_handler():
    _running = False
      │
      ▼
Loop condiciona em _running
      │
      ▼ (na próxima iteração)
connection.close()
sys.exit(0)
```

---

## 8. Camada de Exportadores

Padrão **Strategy** — todos os formatos implementam o mesmo protocolo.

```
ExporterProtocol
  .extension    → str    (".jsonl", ".csv", ".parquet", ...)
  .format_name  → str    ("jsonl", "csv", "parquet", ...)
  .export_batch(records, path) → None
         │
         │
 ┌───────┼──────────────────────┐
 │       │                      │
JSONExporter  CSVExporter  ParquetExporter  MinIOExporter
 │            │            │                │
 │ line-by-   │ pandas     │ pyarrow        │ boto3
 │ line JSONL │ DataFrame  │ .write_table() │ s3.put_object
 │ (O(1) mem) │            │                │
 │            │            │                │
 └──── get_exporter(format_name) ──┘        │
                                            │
                            get_minio_exporter(url, ...)
```

### Registro de Formatos

```python
# Registrados em exporters/__init__.py
_REGISTRY = {
    "jsonl":    JSONExporter,
    "csv":      CSVExporter,
    "parquet":  ParquetExporter,  # requer pyarrow + pandas
    "db":       DatabaseExporter, # requer sqlalchemy
}

# Verificação de disponibilidade
is_format_available("parquet")  # False se pyarrow não instalado
```

### MinIO Exporter — Fluxo

```
MinIOExporter.export_batch(records, prefix)
         │
         ├── format == "jsonl"  → gera JSONL em buffer → put_object
         ├── format == "csv"    → pandas DataFrame → put_object
         └── format == "parquet"→ (não usado aqui — ver minio_parquet.py)
                                   ProcessPoolExecutor usa worker dedicado
                                   para evitar serialização do boto3 client
```

---

## 9. Camada de Conexões (Streaming)

```
connections/
├── __init__.py       → get_connection(), is_target_available()
├── base.py           → ConnectionProtocol(ABC)
├── stdout.py         → StdoutConnection
├── kafka.py          → KafkaConnection  (requer kafka-python)
└── webhook.py        → WebhookConnection (requer requests)


is_target_available("kafka")
   │
   ├── True  → KafkaConnection disponível
   └── False → kafka-python não instalado; sugere pip install
```

---

## 10. Fluxo de Dados Completo — End-to-End

### Modo Batch Local (caminho mais comum)

```
CLI: python generate.py --size 1GB --output ./data --seed 42
         │
         ▼
    build_parser() → args
         │
         ▼
    BatchRunner.run(args)
         │
         ├── FASE 1 ─────────────────────────────────────────────┐
         │   CustomerGenerator × 10.000                           │
         │   DeviceGenerator × ~22.000                           │
         │   → List[CustomerIndex(tuple)]                        │
         │   → List[DeviceIndex(tuple)]                          │
         │   → customers.jsonl  devices.jsonl                    │
         │                                                       │
         ├── FASE 2 ─────────────────────────────────────────────┤
         │   ProcessPoolExecutor(workers=N)                       │
         │   ├── Worker 0: transactions_00000.jsonl               │
         │   ├── Worker 1: transactions_00001.jsonl               │
         │   └── Worker N: transactions_000NN.jsonl               │
         │   Cada worker:                                         │
         │     random.seed(seed + batch_id × 12345)              │
         │     TransactionGenerator.generate() × 268.435         │
         │     stream → arquivo (buffer 1000 linhas)             │
         │                                                       │
         ├── FASE 3 ─────────────────────────────────────────────┤
         │   DriverGenerator × 2.000                             │
         │   → drivers.jsonl                                     │
         │                                                       │
         └── FASE 4 ─────────────────────────────────────────────┤
             ProcessPoolExecutor(workers=N)                       │
             ├── Worker 0: rides_00000.jsonl                      │
             └── Worker N: rides_000NN.jsonl                      │
             Cada worker:                                         │
               RideGenerator.generate() × 223.696               │
               Haversine distance calculation                    │
               → stream → arquivo                               │
                                                               ◄─┘

output/
├── customers.jsonl           (~4 MB)
├── devices.jsonl             (~10 MB)
├── drivers.jsonl             (~2 MB)
├── transactions_00000.jsonl  (~128 MB)
├── transactions_00001.jsonl  (~128 MB)
├── rides_00000.jsonl         (~128 MB)
└── rides_00001.jsonl         (~128 MB)
```

### Modo Schema Declarativo

```
CLI: python generate.py --schema schemas/banking_full.json --count 5000
         │
         ▼
    SchemaRunner.run(args)
         │
         ├── AISchemaCorrector.correct(json_text)
         │      └── heuristics → parse → warn/fix
         │
         ├── SchemaParser.from_file(path)
         │      └── valida + retorna parsed dict
         │
         ├── SchemaEngine.__init__(parsed)
         │      └── inicia CustomerGen + DeviceGen + TransactionGen
         │
         └── SchemaEngine.generate(count=5000)
                │
                └── for cada registro:
                      customer = CustomerGen.generate()
                      device   = DeviceGen.generate()
                      tx       = TransactionGen.generate()
                      record   = FieldMapper.resolve(
                                   output_template,
                                   transaction=tx,
                                   customer=customer,
                                   device=device
                                 )
                      yield record → write JSONL
```

---

## 11. Decisões de Design

### Por que não DDD (Domain-Driven Design)?

```
DDD exigiria:
  Domain Layer     → Aggregates, Entities, Value Objects, Domain Events
  Application Layer→ UseCases, Commands, Queries
  Infrastructure   → Repositories, External Services
  Interface        → Controllers, DTOs

Para este projeto seria:
  - Customer(Aggregate) com 0 domain logic (só geração aleatória)
  - TransactionService com 0 business rules (só randomness)
  - 4 camadas para um gerador CLI → overhead sem benefício

✅ Decisão: SOLID Modular — cada módulo tem responsabilidade única
            sem camadas desnecessárias
```

### Por que não Clean Architecture (Uncle Bob)?

```
Clean Architecture exige 4 anéis:
  ┌───────────────────────────────┐
  │ Frameworks & Drivers          │ ← generate.py, argparse
  │  ┌─────────────────────────┐  │
  │  │ Interface Adapters      │  │ ← Runners, Exporters
  │  │  ┌───────────────────┐  │  │
  │  │  │ Application/Use   │  │  │ ← index_builder, workers
  │  │  │ Cases             │  │  │
  │  │  │  ┌─────────────┐  │  │  │
  │  │  │  │  Entities   │  │  │  │ ← generators, models
  │  │  │  └─────────────┘  │  │  │
  │  │  └───────────────────┘  │  │
  │  └─────────────────────────┘  │
  └───────────────────────────────┘

Regra de dependência (interna ← externa) adicionaria:
  - Interfaces para cada gerador
  - DTOs para cruzar camadas
  - Mapeadores entre camadas

✅ Decisão: Os módulos internos (generators, config, models)
            já são estáveis e sem dependências externas.
            A separação de camadas é adequada sem burocracia adicional.
```

### Por que ProcessPoolExecutor > ThreadPoolExecutor para geração?

```
Geração de dados:
  random.seed() + Faker + cálculos numéricos → CPU BOUND
  Python GIL: só 1 thread executa Python por vez

  ThreadPool:   8 threads → ~1.2× speedup (GIL contention)
  ProcessPool:  8 processos → ~6-7× speedup (paralelo real)

  Exceção: MinIO JSONL/CSV upload → I/O bound → ThreadPool OK
           (tempo dominado por network latency, não CPU)
```

### Por que seed por worker (`seed + batch_id × K`)?

```
Objetivo: reprodutibilidade independente do número de workers

❌ seed global compartilhado:
   Worker-0 e Worker-1 concorrem pelo mesmo estado random
   → datasets diferentes a cada execução

✅ seed derivado:
   Worker-0: random.seed(42 + 0 × 12345) = seed(42)
   Worker-1: random.seed(42 + 1 × 12345) = seed(12387)
   → cada worker é determinístico e independente
   → --seed 42 com 4 ou 8 workers → output idêntico (por arquivo)
```

---

*Gerado em: 2026-03-04 | Versão: 4.1.0 | Padrões: SOLID, Strategy, Command, Chain of Responsibility*
