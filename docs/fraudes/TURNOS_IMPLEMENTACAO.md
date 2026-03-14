# Turnos de Implementação — Fraudes & Qualidade de Dados

> Baseado na análise completa de: `FRAUDES_DESCOBERTAS.md`, `ANALISE_VALIDACAO_DADOS.md`, `INDICE_EXECUTIVO.md`, `MATRIZ_FRAUDES.md`

**Critério de priorização**: Impacto ML × Viabilidade ÷ Esforço  
**Objetivo**: Cada turno é entregável e testável independentemente antes de avançar.

---

## TURNO 0 — Pré-condição (antes de qualquer implementação)

> **Objetivo**: garantir baseline mensurável para comparar antes/depois.

- [x] Gerar dataset de referência com o gerador atual (`--seed 42 --size 50MB`)
- [x] Salvar métricas baseline: distribuição de horários, distribuição de locais, AUC de modelo simples (XGBoost)
- [x] Documentar distribuição atual de fraud types (% por tipo)
- [x] Criar script `validate_realism.py` com as métricas: temporal entropy, geo entropy, fraud_rate_by_type

**Entregável**: arquivo `baseline_seed42/REALISM_METRICS.json` ✅ — temporal=6.7 geo=8.1 overall=8.3  
**Estimativa**: 1 dia  
**Status**: ✅ **CONCLUÍDO**

---

## TURNO 1 — Realismo Temporal (crítico para ML)

> **Objetivo**: dados deixam de ter distribuição uniforme de horários — modelos de sequência (LSTM, RNN) param de ser inúteis.  
> **Esforço**: ~1 semana  
> **Impacto**: ⭐⭐⭐⭐⭐

### Ajustes de dados

- [x] **Picos intra-dia trimodais** — implementar distribuição de horários com 3 picos reais:
  - Pico 1: 12h–13h (almoço / comércio)
  - Pico 2: 17h–19h (saída do trabalho)
  - Pico 3: 21h–22h (lazer / e-commerce)
  - Valle: 1h–6h (volume mínimo, 80% menor que pico)
  - Arquivos alterados: `src/fraud_generator/config/seasonality.py` (novo), `src/fraud_generator/cli/workers/tx_worker.py`, `src/fraud_generator/profiles/behavioral.py`

- [x] **Picos do dia da semana** — segunda (retomada) e sexta (consumo) com +10%; sábado/domingo com -40%
  - Arquivo: `src/fraud_generator/config/seasonality.py` — `DOW_WEIGHTS`

- [x] **Sazonalidade anual** — multiplicadores por evento:
  - Black Friday (novembro): 3.0×
  - Natal (dezembro): 2.0×
  - 13º salário (novembro/dezembro): 1.5×
  - Carnaval: 0.7×
  - Feriados nacionais: 0.6×
  - Arquivo: `src/fraud_generator/config/seasonality.py` — `get_day_multiplier()`

- [ ] **Latência de fraude** — ENGENHARIA_SOCIAL e PHISHING devem ter delay de 2–7 dias entre "comprometimento" e primeiro uso:
  - Hoje: fraude começa imediato
  - Target: adicionar `compromise_date` + `first_fraud_date` com gap paramétrico

### Validação do turno

- [x] Plotar distribuição de horários antes/depois — picos em [12, 13, 18, 19, 20, 21]
- [ ] Verificar que Black Friday gera spike de volume detectável
- [ ] Confirmar que LSTM treinado nos novos dados performa melhor na detecção de ATO nocturno

**Resultado medido**: `after_t1/REALISM_METRICS.json` — temporal=**9.6/10** (era 6.7/10) entropy=0.9206 (era 0.9378)  
**Status**: ✅ **CONCLUÍDO** (latência de fraude → movido para T4)

---

## TURNO 2 — Realismo Geográfico (crítico para geo-features)

> **Objetivo**: clientes têm locações fixas (casa, trabalho, mercado favorito) — geo-features param de ser ruído.  
> **Esforço**: ~1 semana  
> **Impacto**: ⭐⭐⭐⭐⭐

### Ajustes de dados

- [ ] **Geoloc clustering por cliente** — cada cliente recebe 3–5 locações favoritas fixas na criação:
  ```python
  customer.locations = {
      'home':     (lat, lon, weight=0.55),
      'work':     (lat, lon, weight=0.20),
      'shopping': (lat, lon, weight=0.15),
      'gym':      (lat, lon, weight=0.07),
      'other':    (lat, lon, weight=0.03),
  }
  ```
  - Arquivo alvo: `src/fraud_generator/generators/transaction.py` + `CustomerIndex`

- [ ] **Transações legítimas usam apenas locações do cluster** — 95% das transações normais dentro de raio de 50km das locações fixas

- [ ] **Impossible Travel** — fraude de CONTA_TOMADA e CARTAO_CLONADO injeta transações impossíveis geograficamente:
  - Critério: 2 transações com `time_diff < 30min` e `distance > 400km`
  - Campo novo: `is_impossible_travel: bool`
  - Exemplo: São Paulo (09:00) → Porto Alegre (09:25) — impossível
  - Arquivo alvo: novo fraud pattern em `src/fraud_generator/generators/transaction.py`

- [ ] **Fraud location coerência** — fraudador usa locações fixas próprias (não aleatórias):
  - CONTA_TOMADA: sempre de 1–2 IPs/cidades fixas (cidade do fraudador)
  - CARTAO_CLONADO: primeiro uso no ponto de clonagem (mesmo merchant onde foi clonado)

### Validação do turno

- [ ] Verificar que >90% transações legítimas estão dentro do cluster geográfico do cliente
- [ ] Confirmar que `is_impossible_travel=True` aparece em ~2% das fraudes de CONTA_TOMADA
- [ ] Checar que geo-features (cidade_origem, distância_média) têm correlação com label de fraude

---

## TURNO 3 — Novos Tipos de Fraude: Alta Prioridade (Card Testing + Velocity)

> **Objetivo**: adicionar 2 novos fraud patterns com maior signal-to-noise para ML.  
> **Esforço**: ~1 semana  
> **Impacto**: ⭐⭐⭐⭐⭐

**Status**: ✅ **CONCLUÍDO**  
**Resultado**: 10 tipos únicos de fraude (era 7). Score Geral: 9.9/10 sem regressão.

### Implementações novas

- [x] **Card Testing (ID 23)** — micro-fraude em 3 fases:
  - Fase 1 (65%): R$0,01–R$1,00 em merchants diferentes
  - Fase 3 (35%): R$3.000–R$15.000 (burst escalado)
  - Campo `card_test_phase: [1, 3, null]` — Phase 2 (silêncio) é implícita

- [x] **Micro-Burst Velocity (ID 38)** — 10–50 transações com timestamp comprimido em janela 5–15 min  
  - Campo `velocity_burst_id: str | null`

- [x] **Distributed Velocity (ID 39)** — rotação de device/IP, 2–3 txns por device  
  - Campo `distributed_attack_group: str | null`

- [x] `FRAUD_TYPES_LIST` atualizado em `fraud_patterns.py` (auto — usa `FRAUD_PATTERNS.keys()`)
- [x] Campos T3 com default `null` em todas as transações (schema backward-compatible)

---

## TURNO 4 — Consistência Comportamental de Clientes

> **Objetivo**: cliente legítimo tem padrão estável — desvio se torna sinal real de fraude.  
> **Esforço**: ~1 semana  
> **Impacto**: ⭐⭐⭐⭐

### Ajustes de dados

- [ ] **Device consistency** — cada cliente tem 1–2 devices principais com lifespan de meses:
  - Device upgrade: substituição gradual, nunca instantânea
  - ATO injeta device completamente novo
  - Arquivo alvo: `src/fraud_generator/generators/transaction.py` + `DeviceIndex`

- [ ] **Merchant clustering** — cliente tem 5–10 merchants favoritos recorrentes:
  - 70% das transações legítimas nesses merchants
  - Fraude usa merchants novos (nunca vistos pelo cliente)
  - Arquivo alvo: `CustomerIndex` + `TransactionGenerator`

- [ ] **Channel preference** — cliente tem canal principal fixo:
  - `YOUNG_DIGITAL` → sempre mobile (95%)
  - `RETIREE` → nunca web banking puro (0.5%)
  - ATO usa canal nunca usado antes
  - Arquivo alvo: `src/fraud_generator/profiles/behavioral.py`

- [ ] **Velocity baseline por cliente** — cada cliente tem `avg_tx_day` histórico; fraude desvia em 5–10×:
  - Campo: `customer_velocity_z_score: float` (z-score em relação à média do cliente)

- [ ] **Account ramp-up** — clientes novos (dias 1–30) têm valores progressivamente maiores (não já começam com transações altas):
  - Dias 1–7: máx R$200
  - Dias 8–30: máx R$1.000
  - Dias 31+: padrão normal do perfil

### Validação do turno

- [ ] Checar que `customer_velocity_z_score > 5` aparece em >80% dos casos de ATO
- [ ] Verificar que novos merchants aparecem em >90% das fraudes de cartão clonado
- [ ] Confirmar que clientes legítimos usam o mesmo device em >70% das transações

---

## TURNO 5 — Expansão Ride-Share (novos fraud patterns)

> **Objetivo**: cobrir os gaps de 70% identificados nas fraudes de ride-share.  
> **Esforço**: ~1,5 semana  
> **Impacto**: ⭐⭐⭐⭐

### Implementações novas

- [ ] **Promo Code Farming (ID 57)** — cliente cria múltiplas contas para abusar de créditos de cadastro:
  - Padrão: emails variantes (+1, .a, etc.), CPFs diferentes
  - Comportamento: conta usada 1–3 vezes e abandonada
  - Campo: `promo_abuse_group: str | null`

- [ ] **Refund Abuse (ID 60)** — passageiro reporta problema frequente para obter créditos:
  - Padrão: > 3 reclamações/mês, sempre com crédito concedido
  - Campo: `refund_count_30d: int`

- [ ] **Non-Payment / Chargeback Loop (ID 52, 59)** — cartão clonado em rides, depois chargeback:
  - Padrão: cartão novo a cada 3–5 corridas antes do chargeback
  - Campo: `payment_dispute_flag: bool`

- [ ] **Destination Disparity (ID 55)** — rota solicitada difere significativamente da rota realizada:
  - Campo: `route_deviation_km: float` (desvio em km da rota esperada)
  - Fraude: desvio > 2× a rota solicitada

- [ ] **Account Takeover (Ride) (ID 61)** — conta de passageiro tomada, corridas imediatas:
  - Padrão: login de novo device + corrida em < 10 min
  - Campo: `new_device_first_ride: bool`

- [ ] Atualizar `RIDESHARE_FRAUD_TYPES` em `src/fraud_generator/config/rideshare.py`
- [ ] Atualizar `RideGenerator` em `src/fraud_generator/generators/ride.py`

### Validação do turno

- [ ] Gerar 10.000 corridas e verificar distribuição dos novos tipos de fraude
- [ ] Confirmar que `promo_abuse_group` aparece em clusters de CPFs similares
- [ ] Checar coerência temporal: ATO → primeira corrida < 10 min

---

## TURNO 6 — Fraud Rings (padrões coordenados avançados)

> **Objetivo**: gerar padrões de fraude coordenada que apareçam em grafos — preparar dados para GNN (Graph Neural Networks).  
> **Esforço**: ~2 semanas  
> **Impacto**: ⭐⭐⭐⭐⭐

### Implementações novas

- [ ] **Fraud Ring base (ID 62)** — grupos de 3–15 contas coordenadas:
  - Compartilham device, IP ou endereço em comum
  - Cada membro faz transações "normais" por 30–90 dias (latência)
  - Depois: burst coordenado (todos no mesmo dia/hora)
  - Campo: `fraud_ring_id: str | null` (mesmo ID para todos do ring)
  - Campo: `ring_role: [mule, orchestrator, recruiter, null]`

- [ ] **Mule Account Pattern** — conta laranja que recebe transferências de múltiplas vítimas:
  - Recipient CPF aparece em > 3 transferências de clientes não relacionados
  - Campo: `recipient_is_mule: bool`
  - Arquivo alvo: `src/fraud_generator/generators/transaction.py`

- [ ] **Multi-Account Stacking** — mesma pessoa (CPFs diferentes) com padrões correlacionados:
  - Mesmo IP de origem
  - Mesmo device fingerprint
  - Campo: `linked_accounts: list[str]` (outros CPFs relacionados)

- [ ] Criar índice de beneficiários para detectar mule candidates em `CustomerIndex`

### Validação do turno

- [ ] Extrair grafo de transações e verificar que fraud rings formam clusters visíveis
- [ ] Confirmar que mule accounts recebem de > 3 fontes diferentes em curto período
- [ ] Checar que `fraud_ring_id` agrupa transações temporalmente coerentes

---

## TURNO 7 — Ajustes Finos de Distribuição e Qualidade Final

> **Objetivo**: corrigir os gaps menores identificados na ANALISE_VALIDACAO_DADOS.md que não foram cobertos nos turnos anteriores.  
> **Esforço**: ~1 semana  
> **Impacto**: ⭐⭐⭐

### Ajustes de dados

- [ ] **BOLETO_FALSO** (hoje em 2%, real é 8%) — aumentar taxa base e corrigir padrão:
  - Hoje: único evento
  - Real: boleto pago + 2–5 dias → chargeback; ou múltiplos pagamentos do mesmo boleto

- [ ] **AUTOFRAUDE** (hoje 8%, real ~0% puro) — remover como fraud type isolado ou reclassificar como subcategoria de FRAUDE_AMIGAVEL:
  - Refactoring em `FRAUD_TYPES_LIST` + ajuste de pesos totais

- [ ] **Beneficiário recorrente em fraudes** — ENGENHARIA_SOCIAL deve usar 2–3 beneficiários fixos (não aleatórios a cada transação):
  - Hoje: cada transação gera novo beneficiário
  - Target: 80% das txs de um episódio vão para o mesmo CPF destino

- [ ] **Valor das fraudes** — CONTA_TOMADA atual é conservador (3–10× normal); real é 30–100×:
  - Ajustar multiplicador em `src/fraud_generator/generators/transaction.py`

- [ ] **First fraud transaction** — PIX_GOLPE e CARTAO_CLONADO devem sempre começar com micro-teste (R$1–5) antes da transação grande

- [ ] Revisar e atualizar `check_schema.py` para validar todos os novos campos adicionados nos turnos anteriores

### Validação do turno

- [ ] Rodar `check_schema.py` — zero erros em todos os formatos (JSONL, CSV, Parquet)
- [ ] Gerar dataset 1GB e comparar distribuições com baseline do Turno 0
- [ ] Confirmar que métricas de realismo (temporal, geo, behavioral) batem os targets:
  - Temporal realism: ≥ 7/10
  - Geo realism: ≥ 8/10
  - Behavioral realism: ≥ 6/10
  - AUC overfitting sintético vs. real: < 1%

---

## Resumo de Esforço e Sequência

| Turno | Tema | Esforço | Arquivos principais | Depende de |
|---|---|---|---|---|
| **T0** | Baseline & métricas | 1 dia | `validate_realism.py` (novo) | — |
| **T1** | Realismo temporal | 1 semana | `transaction.py`, `transactions.py` | T0 |
| **T2** | Realismo geográfico | 1 semana | `transaction.py`, `CustomerIndex` | T0 |
| **T3** | Card Testing + Velocity | 1 semana | `transaction.py`, `transactions.py` | T1, T2 |
| **T4** | Consistência de cliente | 1 semana | `transaction.py`, `behavioral.py`, `DeviceIndex` | T2 |
| **T5** | Ride-Share (novos fraudes) | 1,5 semanas | `ride.py`, `rideshare.py` | T0 |
| **T6** | Fraud Rings | 2 semanas | `transaction.py`, `CustomerIndex` | T3, T4 |
| **T7** | Ajustes finos + QA | 1 semana | múltiplos + `check_schema.py` | T1–T6 |
| **TSN** | Pipeline de Risco v4.2.0 | 1 semana | `score.py`, `correlations.py`, `session_context.py`, `pix.py` | T3 |
| **TPRD1** | Campos de contexto faltantes | 3 dias | `transaction.py`, `session_context.py` | TSN |
| **TPRD2** | Biometria (Tier Pago) | 1 semana | `profiles/biometric.py`, `config/license.py` | TSN |
| **TPRD3** | PIX Fase 2 + Campos extras | 3 dias | `config/pix.py`, `transaction.py` | TSN |
| **TPRD4** | Refactor Enricher/Pipeline | 2 semanas | `enrichers/`, `pipeline/` | TPRD1–3 |
| **TPRD5** | Produção: CI/CD + VPS | 1 semana | `.github/workflows/`, `brazildata-infra/` | TPRD4 |

**Total estimado**: ~9 semanas qualidade de dados + ~5 semanas produto (paralelo possível a partir de TPRD1)

---

## TURNO SN — Pipeline de Risco (v4.2.0 Sinal)

> **Objetivo**: transformar `fraud_risk_score` de campo hardcoded=0 em score real baseado em 17 sinais comportamentais e biométricos.  
> **Concluído em**: 2026-03-13/14  
> **Status**: ✅ **CONCLUÍDO**

### O que foi feito

- [x] **`generators/score.py`** — wired: 17 sinais ponderados, resultado int 0–100
- [x] **`generators/correlations.py`** — wired: 4 regras de correlação (MALWARE_ATS, ATO, FALSA_CENTRAL, CONTA_LARANJA)
- [x] **`generators/session_context.py`** — `build_context_for_fraud()` converte dict de transação em `GenerationContext` para alimentar score.py + correlations.py
- [x] **`config/pix.py`** — criado: constantes BACEN pacs.008 (ISPB_MAP 26 bancos, MODALIDADE_INICIACAO, TIPO_CONTA, HOLDER_TYPE) + `generate_end_to_end_id()`
- [x] **PIX transações** — 7 campos BACEN emitidos: `end_to_end_id`, `ispb_pagador`, `ispb_recebedor`, `tipo_conta_pagador`, `tipo_conta_recebedor`, `holder_type_recebedor`, `modalidade_iniciacao`
- [x] **Padrões de fraude que fazem upgrade para PIX** — também emitem os 7 campos BACEN
- [x] **`models/device.py`** + **`generators/device.py`** — 4 campos novos: `device_age_days`, `emulator_detected`, `vpn_active`, `ip_type` (presentes em `devices.jsonl`)
- [x] **Isolamento de RNG** — `build_context_for_fraud(rng=self._buf._rng)` garante que `sample_device_signals()` nunca toca o `random` global; seed determinística preservada
- [x] **`schemas/banking_full.json`** — atualizado de v1.0 para v2.0 com todos os campos novos
- [x] **VERSION** — bumped de 4.1.0 para 4.2.0
- [x] **109 testes unitários novos** — `test_correlations.py` (35), `test_score.py` (28), `test_session_context.py` (27), `test_output_schema.py` (19) — todos passando
- [x] **CHANGELOG.md** — atualizado com seção v4.2.0 Sinal
- [x] **Git commit + tag** — `252ce35` / `v4.2.0`

### O que NÃO foi feito (para próximos turnos)

- [ ] `config/license.py` — gate OS/Pago com API key `sk-*` (→ TPRD2)
- [ ] `profiles/biometric.py` — sinais biométricos detalhados para tier pago (→ TPRD2)
- [ ] PIX Fase 2: `cpf_hash_pagador`, `motivo_devolucao_med`, `pacs_status` (→ TPRD3)
- [ ] Campos de contexto faltantes no output de transação: `new_merchant`, `cliente_perfil`, `classe_social`, `ip_location_matches_account`, `sim_swap_recent`, `hours_inactive` (→ TPRD1)
- [ ] `fraud_signals: list[str]` — array explicando quais sinais ativaram o score (→ TPRD1)
- [ ] Padrão beneficiário recorrente: ENGENHARIA_SOCIAL deve reusar 2–3 CPFs destino fixos (→ T7)
- [ ] `validate_correlations.py` — script de validação dos 15 checks (→ TPRD1)

---

## TURNO TPRD1 — Campos de Contexto Faltantes no Output

> **Objetivo**: completar o output de transações com campos definidos no `brazildata_schema.json` mas ausentes no JSON gerado.  
> **Esforço**: ~3 dias  
> **Depende de**: TSN  
> **Status**: ⬜ Não iniciado

### Campos a adicionar ao output de transação

- [ ] `new_merchant: bool` — se o merchant nunca foi usado pelo cliente antes (já calculado em CustomerSessionState, não serializado)
- [ ] `cliente_perfil: str` — ex: `young_digital`, `business_owner` (já atribuído ao gerar cliente, não propagado para transação)
- [ ] `classe_social: str` — ex: `C1`, `B2` (já existe no generator internamente)
- [ ] `ip_location_matches_account: bool` — se IP bate com UF do cadastro
- [ ] `sim_swap_recent: bool` — SIM swap nos últimos 30 dias (atualmente usado no score mas não emitido)
- [ ] `hours_inactive: int` — horas desde última transação (calculado em CustomerSessionState, não serializado)
- [ ] `fraud_signals: list[str]` — array de strings identificando quais sinais contribuíram para `fraud_risk_score` (usar `score_breakdown()`)
- [ ] `num_failed_auth_attempts: int` — tentativas de autenticação falhadas na sessão

### Validação
- [ ] `check_schema.py` passa sem diff em todos os novos campos
- [ ] `test_output_schema.py` atualizado para incluir os novos campos obrigatórios

---

## TURNO TPRD2 — Biometria e Gate OS/Pago

> **Objetivo**: implementar a separação OS/Pago via `config/license.py` + campos biométricos detalhados para o tier pago.  
> **Esforço**: ~1 semana  
> **Depende de**: TSN  
> **Status**: ⬜ Não iniciado  
> **Fonte**: `02 - ANALISE_COMPARATIVA_CRUZADA.md` Fase 1 + Fase 4, `03 - ESTRATEGIA_DEPLOY_SEM_EXPOSICAO.md`

### Implementações

- [ ] **`config/license.py`** — gate `sk-*` que distingue OS de Pago:
  ```python
  def is_paid_tier(api_key: str) -> bool:
      return api_key.startswith("sk-") and len(api_key) == 32
  ```
- [ ] **`profiles/biometric.py`** — perfis biométricos detalhados para tier pago (10 campos):
  - `typing_speed_avg_ms`, `typing_rhythm_variance`, `touch_pressure_avg`
  - `accelerometer_variance`, `gyroscope_variance`, `scroll_before_confirm`
  - `time_to_confirm_tx_sec`, `session_duration_sec`, `copy_paste_on_key`, `navigation_order_anomaly`
- [ ] Campos biométricos = `null` no tier OS, preenchidos no tier Pago
- [ ] `active_call_during_tx: bool` — serializado no output (já existe em GenerationContext)
- [ ] `network_type: str` — WIFI/4G/5G/3G
- [ ] `language_locale: str` — ex: `pt-BR`

### Validação
- [ ] OS tier: campos biométricos = null em 100% dos registros
- [ ] Paid tier: campos biométricos preenchidos com distribuições corretas por fraud_type

---

## TURNO TPRD3 — PIX Fase 2 e Campos BACEN Avançados

> **Objetivo**: completar a conformidade com pacs.008 e adicionar campos de devolução/status.  
> **Esforço**: ~3 dias  
> **Depende de**: TSN  
> **Status**: ⬜ Não iniciado  
> **Fonte**: `02 - ANALISE_COMPARATIVA_CRUZADA.md` Fase 3

### Implementações

- [ ] `cpf_hash_pagador: str` — SHA-256 do CPF pagador (sem CPF em claro — LGPD)
- [ ] `cpf_hash_recebedor: str` — SHA-256 do CPF recebedor
- [ ] `motivo_devolucao_med: str | null` — FR01/MD06/BE08/REFU (apenas em devoluções; já definido em `config/pix.py`)
- [ ] `pacs_status: str` — ACSC/RJCT/PDNG (status da liquidação)
- [ ] `is_devolucao: bool` — se é transação de devolução MED
- [ ] Serializar `motivo_devolucao_med` nos casos de fraude confirmada (is_fraud=True + PIX)

### Validação
- [ ] Nenhum CPF em claro no output (apenas hashes)
- [ ] `motivo_devolucao_med` presente em 100% das devoluções e null em transações normais
- [ ] Schema `banking_full.json` atualizado para v2.1 com campos PIX Fase 2

---

## TURNO TPRD4 — Refactor Enricher / Pipeline

> **Objetivo**: substituir o `TransactionGenerator` monolítico por uma pipeline de enriquecedores modulares.  
> **Esforço**: ~2 semanas  
> **Depende de**: TPRD1, TPRD2, TPRD3  
> **Status**: ⬜ Não iniciado  
> **Fonte**: `02 - ANALISE_COMPARATIVA_CRUZADA.md` Fase 4, `03 - ESTRATEGIA_DEPLOY_SEM_EXPOSICAO.md`

### Arquivos a criar

- [ ] `pipeline/context.py` — `TransactionContext` dataclass com todos os campos intermediários
- [ ] `pipeline/transaction_pipeline.py` — orquestrador que chama enrichers em ordem
- [ ] `enrichers/base.py` — `EnricherProtocol` abstrato
- [ ] `enrichers/temporal.py` — enriquecimento de timestamp, horario_incomum, sazonalidade
- [ ] `enrichers/geo.py` — lat/lon, is_impossible_travel, location_cluster
- [ ] `enrichers/device.py` — campos de device mergeados na transação
- [ ] `enrichers/session.py` — velocity, accumulated_amount, new_merchant, new_beneficiary
- [ ] `enrichers/fraud.py` — injeção de padrão de fraude
- [ ] `enrichers/risk.py` — fraud_risk_score, fraud_signals, correlations
- [ ] `enrichers/pix.py` — campos BACEN PIX
- [ ] `enrichers/biometric.py` — campos biométricos (com gate OS/Pago)

### Validação
- [ ] `pytest tests/` — zero regressões
- [ ] Dataset gerado com novo pipeline idêntico ao anterior (diff no output = zero para mesmo seed)
- [ ] `scripts/validate_correlations.py` — 15 checks passam

---

## TURNO TPRD5 — Produção: CI/CD + VPS

> **Objetivo**: colocar SynthFin em produção na VPS OVH Value com os 4 pipelines CI/CD.  
> **Esforço**: ~1 semana  
> **Depende de**: TPRD4  
> **Status**: ⬜ Não iniciado  
> **Fonte**: `docs/documentodeestudos/SynthLab_CICD_Pipelines.md`, `docs/documentodeestudos/brazildata-infra-README.md`

### Pipelines GitHub Actions

- [x] **Pipeline 4: OS Release** — `.github/workflows/docker-publish.yml` já existe ✅
- [ ] **Pipeline 1: Produto** — `.github/workflows/deploy-product.yml` — push main → test → build GHCR → deploy VPS
- [ ] **Pipeline 2: Site** — `.github/workflows/deploy-site.yml` — push main → build Next.js → deploy VPS
- [ ] **Pipeline 3: Infra** — `.github/workflows/deploy-infra.yml` — apply configs na VPS via SSH

### VPS Setup (brazildata-infra)

- [ ] Criar repo `brazildata-infra` com estrutura definida em `brazildata-infra-README.md`
- [ ] `security/01-07-*.sh` — hardening do OS (SSH porta 2222, UFW, fail2ban, kernel)
- [ ] `traefik/` — reverse proxy + SSL Let's Encrypt + rate limiting
- [ ] `services/docker-compose.services.yml` — PostgreSQL, Redis, MinIO, API, Worker, Beat
- [ ] `monitoring/` — Prometheus + Grafana dashboards
- [ ] `backup/backup.sh` — backup diário automático (PostgreSQL + acme.json)

### Validação
- [ ] Push para main dispara deploy automático
- [ ] `api.synthlab.io/health` retorna 200
- [ ] SSL A+ no SSL Labs
- [ ] Rate limit: 1000 req/min para trial, 10k para pro

---

## Rastreamento de Status

> Atualizar esta seção conforme cada turno for concluído.

| Turno | Status | Data início | Data fim | Notas |
|---|---|---|---|---|
| T0 | ✅ Concluído | 2026-03-05 | 2026-03-05 | `validate_realism.py` criado, REALISM_METRICS.json baseline |
| T1 | ✅ Concluído | 2026-03-05 | 2026-03-05 | Temporal 9.6/10 (era 6.7) — picos [12,13,18,19,20,21] |
| T2 | ✅ Concluído | 2026-03-05 | 2026-03-05 | Geo 10.0/10 — `location_cluster`, `is_impossible_travel` |
| T3 | ✅ Concluído | 2026-03-05 | 2026-03-05 | 10 tipos únicos, 3 novos: CARD_TESTING/MICRO_BURST_VELOCITY/DISTRIBUTED_VELOCITY |
| TSN | ✅ Concluído | 2026-03-13 | 2026-03-14 | fraud_risk_score live, PIX BACEN 7 campos, device 4 campos, 109 testes, v4.2.0 |
| T4 | ⬜ Aguardando | — | — | Consistência comportamental de clientes — device/merchant clustering, velocity z-score |
| T5 | ⬜ Não iniciado | — | — | Novos fraud patterns ride-share: promo abuse, refund abuse, destination disparity |
| T6 | ⬜ Não iniciado | — | — | Fraud rings: fraud_ring_id, ring_role, recipient_is_mule |
| T7 | ⬜ Não iniciado | — | — | Ajustes finos: BOLETO_FALSO 8%, ENGENHARIA_SOCIAL beneficiário fixo, QA final |
| TPRD1 | ⬜ Não iniciado | — | — | Campos faltantes: new_merchant, cliente_perfil, classe_social, sim_swap_recent, fraud_signals |
| TPRD2 | ⬜ Não iniciado | — | — | config/license.py gate + profiles/biometric.py tier pago |
| TPRD3 | ⬜ Não iniciado | — | — | PIX Fase 2: cpf_hash, motivo_devolucao_med, pacs_status |
| TPRD4 | ⬜ Não iniciado | — | — | Refactor enricher/pipeline |
| TPRD5 | ⬜ Não iniciado | — | — | CI/CD Pipelines 1-3 + VPS OVH setup |

**Legenda**: ⬜ Não iniciado · 🟡 Em andamento · ✅ Concluído · 🔴 Bloqueado

---

*Fontes: FRAUDES_DESCOBERTAS.md · ANALISE_VALIDACAO_DADOS.md · INDICE_EXECUTIVO.md · MATRIZ_FRAUDES.md · docs/Analise e comparacao com estudos das ferias/ · docs/documentodeestudos/SynthLab_CICD_Pipelines.md*  
*Última atualização: 2026-03-14*
