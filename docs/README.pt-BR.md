# Gerador de Dados de Fraude Brasileiro

<p align="center">
  <img src="assets/Hero%20do%20README.png" alt="Visao premium do gerador de dados de fraude com banking, PIX, ride-share, sinais e exportacoes." width="100%" />
</p>

<p align="center">
  <a href="./README.md"><img src="https://img.shields.io/badge/lang-en-B91C1C" alt="Documentacao em ingles" /></a>
  <a href="./README.pt-BR.md"><img src="https://img.shields.io/badge/lang-pt--BR-15803D" alt="Documentacao em portugues" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-1D4ED8" alt="Python 3.10 ou superior" />
  <img src="https://img.shields.io/badge/modos-batch%20%7C%20stream%20%7C%20schema-0F172A" alt="Batch, stream e schema" />
  <img src="https://img.shields.io/badge/saida-jsonl%20csv%20parquet%20arrow-7C3AED" alt="Saidas JSONL CSV Parquet Arrow" />
</p>

<p align="center">
  <strong>Dados sintéticos brasileiros para antifraude, QA e engenharia de dados.</strong><br />
  Gere datasets realistas de transações bancárias, PIX e corridas de app para treino de modelos, validação de pipelines e testes de integração.
</p>

<p align="center">
  <a href="../README.md">README principal</a>
  ·
  <a href="../ARCHITECTURE.md">Architecture</a>
  ·
  <a href="./README.md">Docs em inglês</a>
  ·
  <a href="./CHANGELOG.md">Changelog</a>
</p>

## Por que este projeto existe

Este repositório foi construído para quem precisa de um dataset sintético de fraude com contexto brasileiro realista, e não apenas um gerador genérico de transações. Ele combina CPF válido, bancos brasileiros, PIX com campos BACEN, sazonalidade local, ride-share, score de fraude, schema declarativo e entrega por arquivo ou streaming.

<table>
  <tr>
    <td width="33%"><strong>Realismo brasileiro</strong><br />CPF válido, geografia nacional, perfis comportamentais, sazonalidade e sinais ligados a PIX e device.</td>
    <td width="33%"><strong>Pronto para produção</strong><br />Batch, streaming, schema mode, banco de dados, Kafka, webhook, MinIO ou S3.</td>
    <td width="33%"><strong>Foco em fraude</strong><br />25 padrões bancários, 11 fraudes de ride-share, 17 sinais de risco e 4 regras de correlação.</td>
  </tr>
</table>

## Open Source e planos comerciais

Todo o código do gerador está neste repositório sob **licença custom non-commercial**. Rodar a partir do código-fonte **não tem limites técnicos** — você tem todos os formatos, todos os targets, todos os geradores e escala ilimitada. Uso gratuito para estudo pessoal, pesquisa acadêmica e experimentação não-comercial. Uso comercial requer licença paga — veja [LICENSE](../LICENSE).

Uma API hospedada está disponível em [synthfin.com.br](https://synthfin.com.br) para equipes que querem geração gerenciada sem operar infraestrutura própria. A plataforma inclui:

- **REST API** em [api.synthfin.com.br](https://api.synthfin.com.br) — 15 endpoints (generate, jobs, download, usage, billing)
- **Dashboard** em [app.synthfin.com.br](https://app.synthfin.com.br) — gestão de jobs, monitoramento, billing
- **Planos** a partir de $9/mês (Starter) até $99/mês (Team), com Enterprise sob consulta

### O que o open source entrega (sem licença)

| Categoria | O que está incluído |
|---|---|
| Geradores | Transações bancárias, corridas de ride-share ou ambos (`--type all`) |
| Fraude bancária | 25 padrões: `ENGENHARIA_SOCIAL`, `PIX_GOLPE`, `CONTA_TOMADA`, `CARTAO_CLONADO`, `FRAUDE_APLICATIVO`, `BOLETO_FALSO`, `FALSA_CENTRAL_TELEFONICA`, `COMPRA_TESTE`, `MULA_FINANCEIRA`, `CARD_TESTING`, `MICRO_BURST_VELOCITY`, `WHATSAPP_CLONE`, `DISTRIBUTED_VELOCITY`, `PHISHING_BANCARIO`, `FRAUDE_QR_CODE`, `FRAUDE_DELIVERY_APP`, `MAO_FANTASMA`, `CREDENTIAL_STUFFING`, `EMPRESTIMO_FRAUDULENTO`, `GOLPE_INVESTIMENTO`, `SIM_SWAP`, `PIX_AGENDADO_FRAUDE`, `SEQUESTRO_RELAMPAGO`, `SYNTHETIC_IDENTITY`, `DEEP_FAKE_BIOMETRIA` |
| Fraude ride-share | 11 tipos: `GHOST_RIDE`, `GPS_SPOOFING`, `SURGE_ABUSE`, `MULTI_ACCOUNT_DRIVER`, `PROMO_ABUSE`, `RATING_FRAUD`, `SPLIT_FARE_FRAUD`, `REFUND_ABUSE`, `PAYMENT_CHARGEBACK`, `DESTINATION_DISPARITY`, `ACCOUNT_TAKEOVER_RIDE` |
| Score de fraude | `fraud_risk_score` 0–100 a partir de 17 sinais e 4 regras de correlação |
| Perfis comportamentais | 7 perfis de transação + 7 perfis de ride-share; fixos por cliente |
| Reprodutibilidade | Seeds determinísticas, intervalo de datas customizado, pool de clientes fixo |
| Formatos de saída | JSONL, JSON array, CSV, TSV, Parquet, Arrow IPC, banco via SQLAlchemy |
| Compressão | JSONL: gzip / zstd / snappy; Parquet: snappy / zstd / gzip / brotli |
| Streaming | stdout, Kafka, webhook |
| Object storage | Upload MinIO e S3-compatible |
| Schema mode | Schemas JSON declarativos com correção por IA (OpenAI / Anthropic / none) |
| CLI | ~30 flags; controle total de workers paralelos (`--workers`, `--parallel-mode`) |
| Validação | `validate_realism.py`, `check_schema.py`, suite pytest de integração |
| API | FastAPI v1 self-hosted para emissão de licenças e telemetria |
| Docker | Imagem oficial no Docker Hub |
| Escala | Limitada apenas pelo seu hardware |
| Custo | Gratuito para sempre |

### Comparativo de planos

Veja os planos disponíveis em [synthfin.com.br](https://synthfin.com.br).

| Funcionalidade | Open Source (self-hosted) | Planos comerciais |
|---|:---:|:---:|
| Todos os geradores e formatos | ✓ | ✓ |
| 25 padrões de fraude bancária | ✓ | ✓ |
| 11 tipos de fraude ride-share | ✓ | ✓ |
| Streaming (stdout, Kafka, webhook) | ✓ | ✓ |
| Workers paralelos, Docker | ✓ | ✓ |
| Escala ilimitada | ✓ | ✓ |
| Suporte prioritário | – | ✓ |
| API hospedada | – | ✓ |
| SLA dedicado | – | Enterprise |

## Comece rápido

```bash
pip install -r requirements.txt
```

### Geração batch

```bash
# 1 GB de transações bancárias com 2% de fraude (padrão)
python generate.py --size 1GB --output ./dados

# Dados de ride-share
python generate.py --size 500MB --type rides --output ./dados

# Bancário e ride-share juntos
python generate.py --size 1GB --type all --output ./dados

# Dataset reproduzível: seed fixo, 15% de fraude, 8 workers
python generate.py --size 2GB --fraud-rate 0.15 --seed 42 --workers 8 --output ./dados

# Janela de datas específica
python generate.py --size 1GB --start-date 2024-01-01 --end-date 2024-12-31 --output ./dados

# Exportar como Parquet, CSV ou Arrow
python generate.py --size 1GB --format parquet --compression zstd --output ./dados
python generate.py --size 1GB --format csv --output ./dados
python generate.py --size 1GB --format arrow --output ./dados

# Enviar direto para MinIO ou S3
python generate.py --size 5GB --output minio://fraud-data/raw --minio-endpoint http://minio:9000

# Geração orientada a schema (campos customizados)
python generate.py --schema schemas/banking_full.json --count 50000 --output ./dados

# Validar realismo da saída
python validate_realism.py --input dados/transactions_*.jsonl
```

### Streaming

```bash
pip install -r requirements-streaming.txt

# Imprimir eventos no terminal a 5 eventos/seg
python stream.py --target stdout --rate 5 --pretty

# Enviar para Kafka a 100 eventos/seg
python stream.py --target kafka --kafka-server localhost:9092 --kafka-topic transactions --rate 100

# Enviar corridas de ride-share para um endpoint REST
python stream.py --target webhook --type rides --webhook-url http://api:8080/ingest --rate 50

# Parar após 10.000 eventos
python stream.py --target stdout --rate 20 --max-events 10000
```

### Docker

```bash
docker run --rm -v $(pwd)/output:/output \
  afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output

# Streaming via Docker
docker run --rm \
  afborda/synthfin-data:latest \
  stream.py --target stdout --rate 10
```

### Modo schema

```bash
# Schemas prontos em schemas/
python generate.py --schema schemas/banking_full.json --count 5000 --output ./dados
python generate.py --schema schemas/banking_minimal.json --count 5000 --output ./dados
python generate.py --schema schemas/rideshare_full.json --count 5000 --output ./dados

# Use seu próprio schema
python generate.py --schema meu_schema.json --count 50000 --output ./dados
```

<p align="center">
  <img src="assets/Workflow%20-%20Como%20funciona.png" alt="Fluxo mostrando configuracao, geracao, modelagem de fraude e entrega dos dados." width="100%" />
</p>

## Referência de CLI

<details>
<summary><strong>generate.py — todas as flags</strong></summary>

| Flag | Padrão | Descrição |
|---|---|---|
| `--type` | `transactions` | Tipo: `transactions`, `rides` ou `all` |
| `--size` | `1GB` | Tamanho alvo: `1GB`, `500MB`, `10GB` etc. |
| `--output` | `./output` | Diretório ou `minio://bucket/prefix` |
| `--format` | `jsonl` | `jsonl`, `json`, `csv`, `tsv`, `parquet`, `parquet_partitioned`, `arrow`, `ipc`, `db` |
| `--jsonl-compress` | `none` | Compressão inline para JSONL: `none`, `gzip`, `zstd`, `snappy` |
| `--fraud-rate` | `0.02` | Fração de registros marcados como fraude (0.0–1.0) |
| `--workers` | nº de CPUs | Processos paralelos |
| `--seed` | nenhum | Seed para datasets reproduzíveis |
| `--parallel-mode` | `auto` | Modo de execução: `auto`, `thread`, `process` |
| `--customers` | automático | Tamanho fixo do pool de clientes |
| `--start-date` | 1 ano atrás | Início do intervalo de datas `YYYY-MM-DD` |
| `--end-date` | hoje | Fim do intervalo de datas `YYYY-MM-DD` |
| `--no-profiles` | off | Desativa perfis comportamentais (aleatório uniforme) |
| `--compression` | `zstd` | Compressão Parquet: `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| `--schema` | nenhum | Arquivo de schema JSON declarativo |
| `--count` | `1000` | Número de registros no modo schema |
| `--schema-ai-provider` | `openai` | IA para correção de schema: `openai`, `anthropic`, `none` |
| `--db-url` | nenhum | URL SQLAlchemy para o formato `db` |
| `--db-table` | `transactions` | Nome da tabela no formato `db` |
| `--redis-url` | nenhum | URL Redis para cache de índices |
| `--minio-endpoint` | env | URL do endpoint MinIO/S3 |
| `--minio-access-key` | env | Access key MinIO (ou variável `MINIO_ROOT_USER`) |
| `--minio-secret-key` | env | Secret key MinIO (ou variável `MINIO_ROOT_PASSWORD`) |
| `--no-date-partition` | off | Desativa particionamento `YYYY/MM/DD` no MinIO |

</details>

<details>
<summary><strong>stream.py — todas as flags</strong></summary>

| Flag | Padrão | Descrição |
|---|---|---|
| `--target` | obrigatório | Destino: `kafka`, `webhook` ou `stdout` |
| `--type` | `transactions` | Tipo: `transactions` ou `rides` |
| `--rate` | `10` | Eventos por segundo |
| `--max-events` | infinito | Parar após N eventos |
| `--kafka-server` | `localhost:9092` | Bootstrap server Kafka |
| `--kafka-topic` | `transactions` | Nome do tópico Kafka |
| `--webhook-url` | nenhum | URL do endpoint HTTP (target webhook) |
| `--webhook-method` | `POST` | Método HTTP: `POST`, `PUT`, `PATCH` |
| `--fraud-rate` | `0.02` | Fração de eventos marcados como fraude |
| `--customers` | `1000` | Tamanho do pool de clientes |
| `--seed` | nenhum | Seed aleatória |
| `--workers` | `1` | Processos geradores paralelos |
| `--queue-size` | `10000` | Buffer de eventos entre workers e sender |
| `--async` | off | Habilita envio assíncrono por threads |
| `--async-concurrency` | `100` | Máximo de envios assíncronos simultâneos |
| `--pretty` | off | JSON formatado (apenas stdout) |
| `--quiet` | off | Suprimir output de progresso |
| `--redis-url` | nenhum | URL Redis para cache base |
| `--redis-prefix` | `fraudgen` | Prefixo de chaves Redis |

</details>

## Schema de saída

Rodar `python generate.py --size 1GB --output ./dados` cria os seguintes arquivos:

```
./dados/
├── customers.jsonl           ← um registro por cliente simulado
├── devices.jsonl             ← um ou mais devices por cliente
└── transactions_00000.jsonl  ← transações em lotes (um arquivo por worker)
```

Com `--type rides`:

```
./dados/
├── customers.jsonl
├── drivers.jsonl
└── rides_00000.jsonl
```

Com `--type all`:

```
./dados/
├── customers.jsonl
├── devices.jsonl
├── drivers.jsonl
├── transactions_00000.jsonl
└── rides_00000.jsonl
```

Cada arquivo é JSONL — um objeto JSON por linha. Os exemplos abaixo são registros reais de um dataset gerado.

### Transação bancária — cartão de crédito (legítima)

```json
{
  "transaction_id": "TXN_1773495125210_0000_000000",
  "customer_id": "CUST_000000002438",
  "session_id": "SESS_1773495125210_0000_000000",
  "device_id": "DEV_000000005239",
  "timestamp": "2025-04-28T19:15:14.146316",
  "type": "CREDIT_CARD",
  "amount": 127.82,
  "currency": "BRL",
  "channel": "MOBILE_APP",
  "ip_address": "190.6.70.57",
  "geolocation_lat": -10.123402,
  "geolocation_lon": -67.645855,
  "merchant_id": "MERCH_096662",
  "merchant_name": "Cosi",
  "merchant_category": "Restaurants",
  "mcc_code": "5812",
  "mcc_risk_level": "low",
  "cliente_perfil": "young_digital",
  "classe_social": "C1",
  "card_number_hash": "d63b69225a3a065a",
  "card_brand": "MASTERCARD",
  "card_type": "CREDIT",
  "installments": 4,
  "card_entry": "CONTACTLESS",
  "cvv_validated": true,
  "auth_3ds": true,
  "velocity_transactions_24h": 1,
  "accumulated_amount_24h": 127.82,
  "new_beneficiary": true,
  "customer_velocity_z_score": -2.25,
  "unusual_time": false,
  "status": "APPROVED",
  "fraud_score": 11,
  "is_fraud": false,
  "sim_swap_recent": false,
  "ip_location_matches_account": true,
  "hours_inactive": 0,
  "new_merchant": true,
  "fraud_risk_score": 0,
  "is_impossible_travel": false,
  "distance_from_last_km": 0.0
}
```

<details>
<summary><strong>Transação PIX fraudulenta — campos BACEN, fraud_type, fraud_signals</strong></summary>

```json
{
  "transaction_id": "TXN_1773495125210_0000_000001",
  "customer_id": "CUST_000000001711",
  "session_id": "SESS_1773495125210_0000_000001",
  "device_id": "DEV_000000003680",
  "timestamp": "2025-11-05T23:45:48.844962",
  "type": "PIX",
  "amount": 1689.28,
  "currency": "BRL",
  "channel": "PIX",
  "ip_address": "138.173.228.22",
  "geolocation_lat": -15.808824,
  "geolocation_lon": -55.865657,
  "merchant_id": "MERCH_066504",
  "merchant_name": "Makro",
  "merchant_category": "Supermarkets",
  "mcc_code": "5411",
  "mcc_risk_level": "low",
  "cliente_perfil": "family_provider",
  "pix_key_type": "CPF",
  "pix_key_destination": "d4acecf9ded200b9761356d6addee76f",
  "destination_bank": "290",
  "end_to_end_id": "E30723886202511052007B0471FE3",
  "ispb_pagador": "30723886",
  "ispb_recebedor": "90400888",
  "tipo_conta_pagador": "TRAN",
  "tipo_conta_recebedor": "CACC",
  "holder_type_recebedor": "CUSTOMER",
  "modalidade_iniciacao": "QRCODE_ESTATICO",
  "cpf_hash_pagador": "8ecde4c9e8f01f5a347b69ae826a2cdd238eb7edcdfe94c897abd5828eee31df",
  "cpf_hash_recebedor": "4b3536650b29ea5f445a470a203eee737b0cd677f8c41d599cb242cf376abbb2",
  "pacs_status": "ACSC",
  "is_devolucao": false,
  "new_beneficiary": true,
  "velocity_transactions_24h": 10,
  "accumulated_amount_24h": 11824.96,
  "unusual_time": false,
  "fraud_score": 89,
  "customer_velocity_z_score": 0.67,
  "status": "APPROVED",
  "is_fraud": true,
  "fraud_type": "PIX_GOLPE",
  "sim_swap_recent": false,
  "ip_location_matches_account": false,
  "hours_inactive": 0,
  "new_merchant": true,
  "fraud_risk_score": 43,
  "fraud_signals": ["active_call", "amount_spike"],
  "is_impossible_travel": false,
  "distance_from_last_km": 0.0
}
```

</details>

<details>
<summary><strong>Registro de cliente</strong></summary>

```json
{
  "customer_id": "CUST_000000000001",
  "name": "Joaquim Câmara",
  "cpf": "321.819.601-94",
  "email": "gustavorocha@example.net",
  "phone": "71 1960-0133",
  "birth_date": "2003-10-25",
  "address": {
    "street": "Alameda de Novais, 78",
    "neighborhood": "Estrela",
    "city": "Pastor de da Mota",
    "state": "GO",
    "postal_code": "26542351"
  },
  "monthly_income": 2377.87,
  "profession": "Biotecnólogo",
  "account_created_at": "2021-04-19T14:20:37.497966",
  "account_type": "DIGITAL",
  "account_status": "ACTIVE",
  "credit_limit": 16304.06,
  "credit_score": 719,
  "risk_level": "HIGH",
  "bank_code": "341",
  "bank_name": "Itaú Unibanco",
  "branch": "0107",
  "account_number": "805667-2",
  "behavioral_profile": "subscription_heavy"
}
```

</details>

<details>
<summary><strong>Registro de device</strong></summary>

```json
{
  "device_id": "DEV_000000000001",
  "customer_id": "CUST_000000000001",
  "type": "SMARTPHONE",
  "manufacturer": "Realme",
  "model": "GT5 Pro",
  "operating_system": "Android 12",
  "fingerprint": "e5da6495f9b75f161af8ba0c7667be98",
  "first_use": "2024-12-06",
  "is_trusted": true,
  "is_rooted_jailbroken": false
}
```

</details>

<details>
<summary><strong>Registro de corrida (--type rides)</strong></summary>

```json
{
  "ride_id": "RIDE_000000000000",
  "timestamp": "2025-08-01T09:08:47.107473",
  "app": "CABIFY",
  "category": "Lite",
  "driver_id": "DRV_0000000205",
  "passenger_id": "CUST_000000000913",
  "pickup_location": {
    "lat": -23.5558,
    "lon": -46.6696,
    "name": "Hospital das Clínicas",
    "poi_type": "HOSPITAL",
    "city": "Manaus",
    "state": "AM"
  },
  "dropoff_location": {
    "lat": -23.4356,
    "lon": -46.4731,
    "name": "Aeroporto de Guarulhos",
    "poi_type": "AIRPORT",
    "city": "Manaus",
    "state": "AM"
  },
  "request_datetime": "2025-08-01T09:08:47.107473",
  "accept_datetime": "2025-08-01T09:09:41.107473",
  "pickup_datetime": "2025-08-01T09:21:41.107473",
  "dropoff_datetime": "2025-08-01T11:33:41.107473",
  "distance_km": 33.75,
  "duration_minutes": 132,
  "wait_time_minutes": 12,
  "base_fare": 72.65,
  "surge_multiplier": 1.32,
  "final_fare": 95.9,
  "driver_pay": 74.8,
  "platform_fee": 21.1,
  "tip": 0.0,
  "payment_method": "CASH",
  "status": "COMPLETED",
  "driver_rating": 5,
  "passenger_rating": 5,
  "weather_condition": "CLEAR",
  "temperature": 21.8,
  "is_fraud": false
}
```

</details>

## O que já está disponível hoje

| Área | Disponível agora |
|---|---|
| Bancário | PIX, TED, DOC, boleto, saque, POS, ecommerce, contexto de merchant, device e campos BACEN para PIX |
| Ride-share | Uber, 99, Cabify e inDrive com motoristas, passageiros, surge, distância e impacto climático |
| Labels de fraude | 25 padrões bancários e 11 tipos de fraude em corridas com taxa configurável |
| Score de fraude | `fraud_risk_score` de 0 a 100 baseado em 17 sinais e 4 regras de correlação |
| Realismo temporal | Picos trimodais, pesos por dia da semana, Black Friday, Natal, 13o e Carnaval |
| Validação | `validate_realism.py`, schemas prontos, checagem de schema e seeds determinísticas |

### Padrões de fraude bancária

`ENGENHARIA_SOCIAL`, `PIX_GOLPE`, `CONTA_TOMADA`, `CARTAO_CLONADO`, `FRAUDE_APLICATIVO`, `BOLETO_FALSO`, `FALSA_CENTRAL_TELEFONICA`, `COMPRA_TESTE`, `MULA_FINANCEIRA`, `CARD_TESTING`, `MICRO_BURST_VELOCITY`, `WHATSAPP_CLONE`, `DISTRIBUTED_VELOCITY`, `PHISHING_BANCARIO`, `FRAUDE_QR_CODE`, `FRAUDE_DELIVERY_APP`, `MAO_FANTASMA`, `CREDENTIAL_STUFFING`, `EMPRESTIMO_FRAUDULENTO`, `GOLPE_INVESTIMENTO`, `SIM_SWAP`, `PIX_AGENDADO_FRAUDE`, `SEQUESTRO_RELAMPAGO`, `SYNTHETIC_IDENTITY`, `DEEP_FAKE_BIOMETRIA`

### Tipos de fraude em ride-share

`GHOST_RIDE`, `GPS_SPOOFING`, `SURGE_ABUSE`, `MULTI_ACCOUNT_DRIVER`, `PROMO_ABUSE`, `RATING_FRAUD`, `SPLIT_FARE_FRAUD`, `REFUND_ABUSE`, `PAYMENT_CHARGEBACK`, `DESTINATION_DISPARITY`, `ACCOUNT_TAKEOVER_RIDE`

## Formatos e integrações

| Camada | Opções suportadas |
|---|---|
| Arquivos | `jsonl`, `json`, `csv`, `tsv`, `parquet`, `arrow`, `ipc` |
| Banco de dados | Exporter `db` ou `database` via SQLAlchemy |
| Object storage | MinIO e S3 via caminhos `s3://bucket/prefix` |
| Streaming | `stdout`, `kafka`, `webhook` |
| Compressão | JSONL com `gzip`, `zstd`, `snappy`; Parquet com `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| Correção de schema com IA | `openai`, `anthropic` ou `none` |

## Por que os dados ficam próximos do real

O foco aqui não é gerar evento aleatório bonito. O foco é preservar sinais que importam para antifraude, analytics e teste de plataforma.

<p align="center">
  <img src="assets/Realismo%20e%20qualidade%20dos%20dados.png" alt="Ilustracao dos pilares de realismo: CPF, geografia, PIX, sazonalidade, perfis e metricas de validacao." width="100%" />
</p>

| Camada de realismo | O que o projeto faz |
|---|---|
| Identidade | Gera CPF válido com algoritmo oficial de dígito verificador |
| Pagamentos | Usa tipos bancários brasileiros, PIX com campos BACEN e contexto de banco |
| Tempo | Aplica picos trimodais, pesos por dia da semana e eventos como Black Friday, Natal, 13o e Carnaval |
| Comportamento | Perfis comportamentais evitam distribuição uniforme sem sentido |
| Geografia | Usa contexto brasileiro de cidade, estado e endereço |
| Fraude | Injeta padrões explícitos de fraude bancária e de ride-share |
| Score | Calcula `fraud_risk_score` com 17 sinais e 4 regras de correlação |

## Qual é o valor dos dados criados

Esses dados têm valor quando você precisa de uma base sintética que se comporte de forma útil para sistemas reais.

| Cenário | Valor entregue |
|---|---|
| Treino de ML | Labels de fraude, taxa configurável, seed determinística e sinais explicáveis |
| QA e testes | Base repetível para APIs, ETL, scoring, contratos de dados e pipelines |
| Streaming | Eventos em tempo quase real para Kafka, webhook ou stdout |
| Benchmark | Saída em JSONL, Parquet, Arrow, banco e object storage |
| Teste de schema | Schemas prontos e schema mode customizável |

## Como validar qualidade e testar

O repositório já traz ferramentas para medir qualidade de saída, em vez de confiar só na descrição.

### Validar realismo

```bash
python validate_realism.py --input output/transactions_*.jsonl
```

Isso mede entropia temporal, distribuição por hora, distribuição por dia da semana, geografia, taxa de fraude, distribuição por tipo de fraude, estatísticas de valor e score composto de realismo.

### Conferir schema e estrutura

```bash
python check_schema.py
```

Para schema mode, compare a saída com os arquivos em `schemas/` e com o exemplo mínimo em `output_test/banking_minimal_output.jsonl`.

### Rodar os testes automatizados

```bash
pytest tests/ -v
pytest tests/integration/ -v
pytest tests/ --cov=src/fraud_generator --cov-report=html
```

### Ferramentas práticas para testar os dados

| Ferramenta | Para que serve |
|---|---|
| `pytest` | Validar workflows e regressões |
| `validate_realism.py` | Medir realismo e distribuição de fraude |
| `pandas` | Inspecionar colunas, skew, nulos e outliers |
| `DuckDB` | Consultar JSONL e Parquet com SQL rápido |
| Consumers Kafka | Testar entrega em tempo real |
| Spark ou PyArrow | Validar compatibilidade com lakehouse e escala |

## Performance em poucas linhas

O benchmark incluído no repositório mostra hoje cerca de 123k a 196k eventos bancários por segundo com 8 a 16 workers, e cerca de 123k a 220k eventos de ride-share por segundo na máquina do benchmark. O throughput real varia por hardware, formato, compressão e número de workers.

Se você quiser os dados brutos, consulte `benchmarks/multiprocessing_results.json` e `MULTIPROCESSING_BENCHMARK.md`.

## API self-hosted

O repositório também inclui uma API FastAPI para emissão de licença e telemetria. A v1 implementada hoje cobre registro, health check, heartbeat e revogação administrativa.

```bash
pip install -r requirements-api.txt
FRAUDGEN_SECRET_KEY=seu-segredo \
RESEND_API_KEY=re_xxxx \
uvicorn src.fraud_generator.api.app:app --host 0.0.0.0 --port 8000
```

Isso permite operar o gerador como oferta self-hosted com controle de licença, sem separar a camada principal de geração em outro repositório.

## Mapa rápido do repositório

| Comece aqui | Para quê serve |
|---|---|
| `generate.py` | Entrada principal da geração batch |
| `stream.py` | Streaming contínuo de eventos |
| `validate_realism.py` | Medição de realismo temporal, geográfico e de fraude |
| `schemas/` | Schemas JSON de exemplo |
| `src/fraud_generator/exporters/` | Formatos de saída e adaptadores |
| `src/fraud_generator/connections/` | Kafka, webhook e stdout |
| `src/fraud_generator/api/app.py` | API self-hosted v1 |
| `../ARCHITECTURE.md` | Visão de arquitetura em inglês |
| `README.md` | Hub de documentação em inglês |

## FAQ

<details>
<summary><strong>Serve só para transações bancárias?</strong></summary>

Não. O projeto gera dados bancários e dados de ride-share, e `--type all` permite gerar os dois no mesmo job.

</details>

<details>
<summary><strong>Posso adaptar para o meu schema?</strong></summary>

Sim. Use `--schema` com um dos arquivos em `schemas/` ou com um JSON schema próprio.

</details>

<details>
<summary><strong>É útil para treino de modelo e teste de plataforma?</strong></summary>

Sim. O projeto foi pensado para datasets sintéticos antifraude, validação de pipelines, streaming de eventos, testes de integração e cenários de QA com contexto brasileiro.

</details>

## Leitura recomendada

- Docs em inglês: [README.md](README.md)
- Arquitetura: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Hub de documentação: [README.md](README.md)
- Publicação Docker: [DOCKER_HUB_PUBLISHING.md](DOCKER_HUB_PUBLISHING.md)

Se o objetivo for descoberta orgânica ou avaliação técnica rápida, os temas mais fortes deste repositório hoje são: dados sintéticos de fraude no Brasil, geração de dataset PIX, simulação de transações bancárias, simulação de fraude em ride-share, schema-driven test data e streaming de eventos antifraude.