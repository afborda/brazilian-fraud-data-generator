---
name: Codebase Ground Truth Map
description: What actually exists in the code RIGHT NOW — verified by source inspection, not docs. Use this to quickly orient in the project.
type: reference
verified: 2026-04-05
---

# Synthfin-Core: Mapa Real do Código

> Gerado por inspeção direta dos arquivos `.py`. Não são os docs — é o que existe de verdade.

---

## Entry Points

| Arquivo | O que faz |
|---------|-----------|
| `generate.py` | Batch CLI → despacha para SchemaRunner / MinIORunner / BatchRunner |
| `stream.py` | Streaming contínuo → stdout / kafka / webhook / redis-stream |
| `check_schema.py` | Valida JSONL gerado contra schema declarativo |

---

## src/fraud_generator/ — Módulos Reais

### cli/
| Arquivo | Função |
|---------|--------|
| `args.py` | Todos os flags CLI (sem lógica de negócio) |
| `constants.py` | TARGET_FILE_SIZE_MB, TRANSACTIONS_PER_FILE, RIDES_PER_FILE |
| `index_builder.py` | Cria CustomerIndex / DeviceIndex / DriverIndex para streaming |
| `runners/batch_runner.py` | Pipeline 4 fases: customers → devices → txs → rides |
| `runners/minio_runner.py` | Upload direto MinIO/S3 com particionamento |
| `runners/schema_runner.py` | Modo declarativo via JSON schema |
| `workers/batch_gen.py` | `generate_transaction_batch()`, `generate_ride_batch()` |
| `workers/tx_worker.py` | Worker multiprocesso para transações |
| `workers/ride_worker.py` | Worker multiprocesso para rides |
| `workers/minio_parquet.py` | Parquet writer especializado para MinIO |

### generators/
| Arquivo | Função |
|---------|--------|
| `customer.py` | CustomerGenerator: CPF válido, perfil comportamental, renda, estado |
| `device.py` | DeviceGenerator: tipo, OS, fingerprint |
| `transaction.py` | Core: gera TX base → injeta fraude → roda pipeline enrichers |
| `ride.py` | RideGenerator: Uber/99/Lyft |
| `driver.py` | DriverGenerator: perfis de motorista |
| `score.py` | `compute_fraud_risk_score(ctx)` — **17 sinais** → int 0-100 |
| `session_context.py` | GenerationContext, `build_context_for_fraud()` |
| `correlations.py` | `match_fraud_rule(ctx)` — mapeia contexto → padrão de fraude |

### enrichers/ — Pipeline de 8 Estágios (ORDEM CRÍTICA)
```
1. TemporalEnricher  → unusual_time flag
2. GeoEnricher       → lat/lon, distância (antes do Fraud para ter baseline)
3. FraudEnricher     → overrides de amount/location/device/channel
4. PIXEnricher       → campos BACEN pacs.008
5. DeviceEnricher    → sinais de device (emulator, rooted, new_for_customer)
6. SessionEnricher   → velocity 24h, merchant novelty, impossible travel
7. RiskEnricher      → chama compute_fraud_risk_score, ring TPRD2
8. BiometricEnricher → biometria (typing_interval, accel, touch) — gated por licença
```
Arquivo chave: `enrichers/pipeline_factory.py` — `get_default_pipeline()`

### config/ — **25 Padrões de Fraude (não 10, não 11)**
Fraudes reais em `config/fraud_patterns.py`:
```
ENGENHARIA_SOCIAL, CONTA_TOMADA, CARTAO_CLONADO, PIX_GOLPE,
FRAUDE_APLICATIVO, COMPRA_TESTE, MULA_FINANCEIRA, CARD_TESTING,
MICRO_BURST_VELOCITY, DISTRIBUTED_VELOCITY, BOLETO_FALSO,
MAO_FANTASMA, WHATSAPP_CLONE, SIM_SWAP, CREDENTIAL_STUFFING,
SYNTHETIC_IDENTITY, SEQUESTRO_RELAMPAGO, FALSA_CENTRAL_TELEFONICA,
PIX_AGENDADO_FRAUDE, FRAUDE_DELIVERY_APP, EMPRESTIMO_FRAUDULENTO,
DEEP_FAKE_BIOMETRIA, GOLPE_INVESTIMENTO, FRAUDE_QR_CODE,
PHISHING_BANCARIO
```
Total: **25 padrões bancários** (fraude ride-share está em `config/rideshare.py`)

Outros configs:
| Arquivo | Conteúdo |
|---------|----------|
| `transactions.py` | TX types, channels, MCC, card brands, installments |
| `banks.py` | Códigos bancários + pesos |
| `geography.py` | Estados (ESTADOS_LIST/WEIGHTS), municípios |
| `municipios.py` | Municípios com CEPs |
| `merchants.py` | MCC codes + nomes de estabelecimentos |
| `devices.py` | Tipos de device, OS |
| `seasonality.py` | HORA_WEIGHTS_PADRAO, HORA_WEIGHTS_FRAUD_ATO, multiplicadores mensais |
| `distributions.py` | Classes de renda (A, B1, B2, C1, C2, D, E), distribuições etárias |
| `pix.py` | modalidade_iniciacao, tipo_conta, ISPB, end-to-end ID |
| `weather.py` | Anomalias correlacionadas com clima |
| `rideshare.py` | Configs ride-share |
| `calibration_loader.py` | Carrega calibrações externas |

### exporters/ — Strategy Pattern
Todos implementam `ExporterProtocol`: `export_batch(data, path)` + `export_stream(iterator, path)`
| Arquivo | Formato |
|---------|---------|
| `json_exporter.py` | JSONL (streaming linha a linha) + JSON array |
| `csv_exporter.py` | CSV + TSV via pandas |
| `parquet_exporter.py` | Parquet + Parquet particionado via PyArrow |
| `arrow_ipc_exporter.py` | Arrow IPC binário |
| `database_exporter.py` | SQL via SQLAlchemy |
| `minio_exporter.py` | Upload streaming MinIO/S3 |

### connections/ — Strategy Pattern para Streaming
Todos implementam `ConnectionProtocol`: `connect()`, `send(record)`, `close()`
| Arquivo | Target |
|---------|--------|
| `stdout_connection.py` | JSON → stdout |
| `kafka_connection.py` | Kafka producer |
| `webhook_connection.py` | HTTP POST |
| `redis_stream_connection.py` | Redis XADD |

### models/
`transaction.py`, `customer.py`, `device.py`, `ride.py` — dataclasses de entidade

### profiles/
| Arquivo | Conteúdo |
|---------|----------|
| `behavioral.py` | Perfis sticky por customer (6-9 perfis: young_digital, traditional_senior, business_owner, etc.) + `get_*_for_profile()` |
| `device.py` | Perfis de device |
| `ride_behavioral.py` | Perfis ride-share |

### schema/ — Modo Declarativo
`engine.py` (SchemaEngine) → `parser.py` (valida JSON) → `mapper.py` (FieldMapper) → `ai_corrector.py` (opcional OpenAI/Claude fix)

### utils/ — Performance Core
| Arquivo | O que faz | Ganho |
|---------|-----------|-------|
| `weight_cache.py` | WeightCache: bisect O(log n) | 1000× vs random.choices() |
| `precompute.py` | PrecomputeBuffers: ring buffer de IPs/hashes/floats | 5-10× throughput |
| `parallel.py` | ParallelStreamManager: pool multiprocesso para streaming | >5k eventos/s |
| `streaming.py` | CustomerIndex, CustomerSessionState (velocity tracking) | — |
| `compression.py` | GZIP, Zstd, Snappy para JSONL | — |
| `helpers.py` | `generate_ip_brazil()`, `generate_random_hash()`, `parse_size()` | — |
| `redis_cache.py` | Cache Redis distribuído (opcional) | — |

### validators/
`cpf.py` — `generate_valid_cpf()`, `validate_cpf()`, `generate_cpf_from_state(state)`

---

## Score: 17 Sinais (com pesos reais)

```python
_W_ACTIVE_CALL         = 35  # Vítima no telefone (FALSA_CENTRAL)
_W_EMULATOR            = 35  # Device emulado (MALWARE_ATS)
_W_ROOTED              = 30  # Device rooted/jailbroken
_W_TYPING_BOT          = 30  # Typing < 15ms → automação
_W_ACCEL_SESSION       = 28  # Zero accel + session < 5s
_W_ATO_TRIAD           = 25  # new_device + ip_mismatch + 168h inativo
_W_DEST_ACCOUNT_NEW    = 20  # Conta destino < 7 dias
_W_PRESSURE_ZERO       = 20  # Touch pressure = 0 (sem dedo humano)
_W_MULTIPLE_ACCOUNTS   = 18  # Multi-conta no mesmo device
_W_VPN_DATACENTER      = 15  # VPN + sessão curta
_W_SESSION_HIGH_VALUE  = 15  # Sessão < 10s + valor alto
_W_CONFIRM_FAST        = 12  # Confirmação < 5s (fluxo scriptado)
_W_NAV_ANOMALY         = 10  # Navegação não-humana
_W_SIM_SWAP            = 10  # SIM swap nos últimos 7 dias
_W_ODD_HOURS           = 8   # 00h-06h
_W_AMOUNT_SPIKE        = 8   # Valor > 5× média histórica
_W_NOTIF_IGNORED       = 5   # Push de segurança ignorado
```

---

## Tests

### Unit (9 arquivos)
`test_enricher_pipeline.py`, `test_score.py`, `test_session_context.py`,
`test_fraud_contextualization.py`, `test_correlations.py`, `test_compression.py`,
`test_phase_1_optimizations.py`, `test_phase_2_optimizations.py`, `test_output_schema.py`

### Integration (2 arquivos)
`test_workflows.py` — pipeline batch completo
`test_phase_2_1_endtoend.py` — compressão + streaming + export

### Fixtures (conftest.py)
`temp_output_dir`, `test_seed=42`, `small_batch_size=100`, `sample_customer_data`, `sample_transaction_data`

---

## Benchmarks (7 arquivos)
| Arquivo | Mede |
|---------|------|
| `data_quality_benchmark.py` | AUC-ROC (must ≥ 0.9991) |
| `streaming_benchmark.py` | 5 níveis de tráfego, TX + rides |
| `multiprocessing_benchmark.py` | Speedup 1-16 workers |
| `format_benchmark.py` | Throughput JSONL vs CSV vs Parquet |
| `phase_2_1_compression_benchmark.py` | Ratio + velocidade de compressão |
| `benchmark_phase_2.py` | Regressão perf histórica fase 2 |
| `comprehensive_benchmark.py` | Suite completa |

---

## Tools (não é src, é utilitário)
`backtest_rules.py`, `privacy_metrics.py`, `qde_filter.py`, `tstr_benchmark.py`, `validate/dashboard.py`

---

## Divergências Encontradas nos Docs

| Doc afirma | Realidade no código |
|-----------|---------------------|
| "10+ fraud types" (CLAUDE.md) | **25 padrões** em fraud_patterns.py |
| "11 enrichers" (CLAUDE.md) | **8 enrichers** no pipeline |
| "17+ signals" (CLAUDE.md) | Exato: **17 sinais** com pesos fixos |
| "config/weather.py (optional)" | Existe e tem lógica real |
| profiles/device.py descrito como "coming soon" | **Arquivo existe** no código |

---

## Regras Críticas de Desenvolvimento

1. **Ordem do pipeline de enrichers é sagrada** — mudar quebra correlações
2. **Nunca `random.choices()` em loop** — sempre `WeightCache`
3. **Nunca acumular dataset completo em RAM** — sempre streaming por batch
4. **Seed antes de qualquer construção de generator**
5. **Pesos de config devem somar ≈ 1.0** — mismatch entre LIST e WEIGHTS crasha
6. **CPF via validators/cpf.py** — nunca gerar CPF fake manualmente
7. **AUC-ROC ≥ 0.9991** — rodar benchmark após qualquer mudança em enrichers/score
