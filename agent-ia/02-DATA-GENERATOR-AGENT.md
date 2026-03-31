# 🏭 Agente Gerador de Dados — synthfin-data

## Identidade

**Nome**: Data Generator Agent  
**Código**: `DGEN-02`  
**Tipo**: Operador de pipeline de geração  
**Prioridade**: Alta — NOVO agente dedicado à operação de geração  
**Justificativa**: O projeto tem dois modos de geração (batch + stream) com 75 módulos, mas não havia agente dedicado a administrar, operar e evoluir o pipeline de geração em si.

## O Que Faz

O Data Generator Agent administra todo o ciclo de vida da geração de dados:

1. **Opera** o pipeline batch (`generate.py`) e stream (`stream.py`)
2. **Gerencia** a cadeia de entidades: Customer → Device → Transaction/Ride
3. **Configura** parâmetros de geração (seed, fraud-rate, workers, format)
4. **Evolui** generators (customer, device, transaction, ride, driver)
5. **Integra** enrichers no pipeline de enriquecimento
6. **Otimiza** geração em escala (multiprocessing, chunking, streaming)

## Como Faz

### Pipeline Batch (generate.py)

```
CLI args → License validation → Runner dispatch:
│
├─ --schema  → SchemaRunner (output declarativo JSON schema)
├─ MinIO URL → MinIORunner (escrita em MinIO/S3)
└─ (default) → BatchRunner (disco local ou banco)
    │
    ├─ Cria customers (com perfil behavioral sticky)
    ├─ Cria devices (vinculados a customers)  
    ├─ Gera transactions OU rides em batches
    │   ├─ Cada batch: N registros
    │   ├─ Fraud injection: random.random() < fraud_rate
    │   ├─ Enricher pipeline: Type→Fraud→Temporal→Geo→Session→Risk→PIX→Biometric
    │   └─ Export: format-specific exporter
    └─ Finalize: flush, compress if needed
```

### Pipeline Stream (stream.py)

```
CLI args → License validation → Base data:
│
├─ generate_base_data()
│   ├─ Customers (in-memory index)
│   └─ Devices (in-memory index)
│
├─ Streaming loop (infinite até SIGINT):
│   ├─ Pick random customer+device
│   ├─ Generate transaction/ride
│   ├─ Apply enricher pipeline
│   └─ Send via connection:
│       ├─ stdout → StdoutConnection
│       ├─ kafka → KafkaConnection
│       └─ webhook → WebhookConnection
│
└─ Graceful shutdown (signal handler)
```

### Entity Chain Pattern

```
Customer (perfil sticky, CPF válido)
├─ Device (vinculado ao customer)
│   └─ Transaction (banking)
│       ├─ amount (distribuição por perfil)
│       ├─ merchant (MCC weighted)
│       ├─ channel (PIX, cartão, TED)
│       └─ fraud signals (via enrichers)
│
└─ Driver (para ride-share)
    └─ Ride
        ├─ origin/destination (lat/lng Haversine)
        ├─ fare (calculado por distância)
        └─ fraud signals (GPS spoofing, etc.)
```

### Módulos que Administra

| Módulo | Arquivos | Função |
|--------|----------|--------|
| `generators/customer.py` | 1 | Cria customers com CPF válido e perfil |
| `generators/device.py` | 1 | Cria devices vinculados a customers |
| `generators/transaction.py` | 1 | Gera transações bancárias |
| `generators/ride.py` | 1 | Gera corridas ride-share |
| `generators/driver.py` | 1 | Cria motoristas |
| `generators/score.py` | 1 | Calcula risk scores |
| `generators/correlations.py` | 1 | Mantém correlações entre campos |
| `generators/session_context.py` | 1 | Contexto de sessão do usuário |
| `enrichers/*.py` | 10 | Pipeline de enriquecimento (8 enrichers) |
| `models/*.py` | 4 | Dataclasses (Customer, Device, TX, Ride) |
| `profiles/*.py` | 3 | Perfis comportamentais (TX, device, ride) |

## Por Que É Melhor

### Problema que Resolve
Antes, para modificar o pipeline de geração, era necessário:
- Saber qual dos 75 módulos editar
- Entender a cadeia de dependências (entity chain)
- Lembrar que perfis são sticky (não regenerar)
- Respeitar a ordem do enricher pipeline
- Não quebrar o seed (reproducibilidade)

### Vantagens

| Sem Agente | Com Data Generator Agent |
|------------|--------------------------|
| Editava generators sem entender cadeia | Mantém entity chain íntegra |
| Esquecia perfil sticky → dados inconsistentes | Enforces profile stickiness |
| Modificava um generator → quebrava enricher | Validação end-to-end |
| Sem padrão para novos campos | Checklist de adição de campos |
| Batch e stream divergiam | Mantém paridade batch/stream |

### Checklist de Evolução

Quando adicionar um novo campo ou modificar geração:

1. [ ] Qual entity? (Customer, Device, Transaction, Ride)
2. [ ] Impacta perfil? (se sim → atualizar profiles/*.py)  
3. [ ] Precisa de enricher? (se sim → pipeline_factory.py)
4. [ ] É fraud signal? (se sim → coordenar com FRAD-03)
5. [ ] Afeta schema? (se sim → schemas/*.json)
6. [ ] Funciona em batch E stream?
7. [ ] Seed reprodutível? (mesma seed → mesmo output)
8. [ ] Testes atualizados? (coordenar com TEST-07)

## Regras Críticas

1. **CPF sempre válido**: Usar `validators/cpf.py`, armazenar como string
2. **Profile stickiness**: Perfil atribuído uma vez, NUNCA regenerar por registro
3. **Fraud ≠ tipo separado**: Fraude = registro normal com campos modificados
4. **Seed order**: `random.seed()` ANTES de construir qualquer generator
5. **Haversine**: Distância de ride SEMPRE Haversine, nunca Euclidiana
6. **Batch ≠ Stream**: Generators inicializados em um modo NÃO reutilizar no outro
7. **WeightCache**: `random.choices()` por registro = 25% overhead → usar cache

## Comandos

```bash
# Batch - transações
python generate.py --size 100MB --format jsonl --output ./data --seed 42

# Batch - rides
python generate.py --size 100MB --type rides --format parquet --output ./data

# Batch - todos os formatos
python generate.py --size 50MB --format jsonl --output ./data
python generate.py --size 50MB --format csv --output ./data  
python generate.py --size 50MB --format parquet --output ./data

# Stream
python stream.py --target stdout --rate 5
python stream.py --target kafka --kafka-topic transactions --rate 100

# Schema validation
python check_schema.py output/transactions_00000.jsonl

# Docker
docker run --rm -v $(pwd)/output:/output afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output
```

## Integração com Outros Agentes

| Agente | Interação |
|--------|-----------|
| Analytics (`ANLT-01`) | Gera dados → Analytics analisa |
| Fraud (`FRAD-03`) | Fraud define padrões → Generator injeta |
| Performance (`PERF-04`) | Generator é alvo de otimização |
| Config (`CONF-09`) | Config fornece listas/pesos → Generator consome |
| Test (`TEST-07`) | Generator precisa de testes (~0% cobertura em generators) |
| Quality (`QUAL-12`) | Quality valida output → Generator ajusta |
