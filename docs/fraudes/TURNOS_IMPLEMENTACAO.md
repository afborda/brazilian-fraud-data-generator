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

**Total estimado**: ~9 semanas (paralelo T1+T2 e T3+T5 possível)

---

## Rastreamento de Status

> Atualizar esta seção conforme cada turno for concluído.

| Turno | Status | Data início | Data fim | Notas |
|---|---|---|---|---|
| T0 | ✅ Concluído | 2026-03-05 | 2026-03-05 | `validate_realism.py` criado, REALISM_METRICS.json baseline |
| T1 | ✅ Concluído | 2026-03-05 | 2026-03-05 | Temporal 9.6/10 (era 6.7) — picos [12,13,18,19,20,21] |
| T2 | ✅ Concluído | 2026-03-05 | 2026-03-05 | Geo 10.0/10 — `location_cluster`, `is_impossible_travel` |
| T3 | ✅ Concluído | 2026-03-05 | 2026-03-05 | 10 tipos únicos, 3 novos: CARD_TESTING/MICRO_BURST_VELOCITY/DISTRIBUTED_VELOCITY |
| T4 | ⬜ Aguardando | — | — | Consistência comportamental de clientes |
| T5 | ⬜ Não iniciado | — | — | — |
| T6 | ⬜ Não iniciado | — | — | — |
| T7 | ⬜ Não iniciado | — | — | — |

**Legenda**: ⬜ Não iniciado · 🟡 Em andamento · ✅ Concluído · 🔴 Bloqueado

---

*Fontes: FRAUDES_DESCOBERTAS.md · ANALISE_VALIDACAO_DADOS.md · INDICE_EXECUTIVO.md · MATRIZ_FRAUDES.md*  
*Última atualização: Março 2026*
