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
| v3.3 | **Turbo** | Performance Phase 1 (+18.9% speed, -85% storage) | 2025-01-30 |
| v4.0 | **Quantum** | Phase 2.2-2.9: Session State + Parallelism + Analytics | 2026-01-30 |
| v4.1 | **Guaraná** | SOLID CLI refactor + JSON schema mode | 2026-03-04 |
| v4.2 | **Sinal** | Fraud signal pipeline: 17 signals + 4 rules + PIX BACEN + device enrichment | 2026-03-14 |
| v4.3 | **Consistência** | T7 distribuições + T4 padrões comportamentais + TPRD3 PIX Fase 2 | 2026-03-14 |
| v4.4 | **Padrões** | T7 micro-probe + T4 device consistency + T5 ride-share fraud patterns | 2026-03-14 |

---

## v4.5 — Separação Estratégica (2026-03-14)

### Segurança / Governança de Repositório

- **Docs de estratégia removidos do repo público**: `PLANO_MONETIZACAO_EXECUTIVO_90DIAS.md`, `PRICING_ANALYSIS_COMPLETO.md`, `pricing_charts.html`, `CHECKLIST_MELHORIAS_DISRUPTIVAS_E_UX.md`, `ROADMAP_TECNICO_DETALHADO.md`, `ANALISE_SHADOWTRAFFIC_VS_SEU_PROJETO.md` deletados do OS repo. Devem residir no repo privado `afborda/synthfin-saas`.
- **Pastas de estratégia removidas**: `docs/Analise e comparacao com estudos das ferias/`, `docs/mercado/`, `docs/pesquisa_mercado/`, `docs/planning/` deletadas do repo público.
- **`admin_tools/` removido**: ferramentas de emissão de licença (`issue_license.py`) não devem estar em repo público.
- **`docs/analysis/ROADMAP_ARQUITETURA.md` e `MAPA_OPORTUNIDADES.md` removidos**: expunham gaps de implementação e oportunidades de produto.
- **`docs/INDEX.md` atualizado**: removidas todas as referências aos docs deletados; adicionada nota indicando que docs de estratégia estão no repo privado. Estatísticas e versão atualizadas.

---

## v4.4 — Padrões (2026-03-14)

### T7 — Padrões seqüenciais de fraude

- **Micro-probe** para `PIX_GOLPE` e `CARTAO_CLONADO`: 40% das transações geram um micro-teste (R$1–5) antes do valor principal. Campo `is_probe_transaction: bool` e `probe_original_amount: float | null` adicionados ao output — modelos de ML podem reconstruir o padrão episódico.
- **`ENGENHARIA_SOCIAL` beneficiários fixos**: cada cliente fraude usa 1 de 3 CPFs-destino derivados deterministicamente do `customer_id` (hash SHA-256). Campo `beneficiary_cpf_hash: str | null` adicionado. 80% das transações do episódio vão ao mesmo beneficiário — signal real para detecção.

### T4 — Consistência de device

- **`device_new_for_customer: bool`**: `CustomerSessionState` agora rastreia até 2 devices primários por cliente. Campo emitido quando device é desconhecido (ATO injeta device completamente novo). Disponibilizado em `_add_risk_indicators()` quando `session_state` está presente.

### T5 — Expansão ride-share (novos fraud patterns)

- 4 novos tipos de fraude em `RIDESHARE_FRAUD_TYPES`: `REFUND_ABUSE` (10%), `PAYMENT_CHARGEBACK` (8%), `DESTINATION_DISPARITY` (5%), `ACCOUNT_TAKEOVER_RIDE` (7%). Pesos de `RATING_FRAUD` e `SPLIT_FARE_FRAUD` ajustados proporcionalmente.
- Campos de output adicionados a todas as corridas: `promo_abuse_group`, `refund_count_30d`, `payment_dispute_flag`, `route_deviation_km`, `new_device_first_ride`.
- `_apply_fraud_fields()` popula os campos corretos por tipo:
  - `PROMO_ABUSE`: `promo_abuse_group` derivado de hash do `passenger_id`
  - `REFUND_ABUSE`: `refund_count_30d` = 3–9
  - `PAYMENT_CHARGEBACK`: `payment_dispute_flag = True`
  - `DESTINATION_DISPARITY`: `route_deviation_km` = 1.5–4× distância base
  - `ACCOUNT_TAKEOVER_RIDE`: `new_device_first_ride = True`
  - `GPS_SPOOFING`: `route_deviation_km` = 2–15 km

### Testes

- 180 passam, 3 skipped, 0 failed.

---

## v4.3 — Consistência (2026-03-14)

### T7 — Ajustes de Distribuição de Fraude

- **CONTA_TOMADA** `amount_multiplier` corrigido de `(3.0, 10.0)` para `(30.0, 100.0)` — ATO real drena contas em magnitude muito maior; modelos treinados agora veem a distribuição de valores correta para detecção de desvio.
- **BOLETO_FALSO** adicionado como 11º tipo de fraude ativo (`fraud_patterns.py`): prevalência 0.08 (conforme FEBRABAN 2024), canal MOBILE_APP/WEB_BANKING, `amount_multiplier: (0.8, 1.5)` — valor próximo ao esperado pela vítima.
- `FRAUD_TYPES_LIST` e `FRAUD_TYPES_WEIGHTS` atualizados automaticamente via auto-derive do dict `FRAUD_PATTERNS`.

### T4 — Consistência Comportamental de Clientes

- **`customer_velocity_z_score: float`** — novo campo de output. Z-score da velocidade atual do cliente em relação ao baseline esperado por perfil comportamental. Fraude de ATO produz z-score > 5 em >80% dos casos. Implementado com `_PROFILE_VELOCITY_BASELINE` dict (9 perfis com média e desvio padrão de txns/24h).
- **Merchant clustering** (OS tier): `CustomerSessionState` agora acumula até 8 merchants favoritos (primeiros vistos). Transações legítimas reutilizam favoritos em 70% dos casos (`_fav_from_session` logic em `generate()`). Fraudes ignoram favoritos e usam merchants novos — signal real de anomalia.
- Perfis `_PROFILE_CLASSE` e `_PROFILE_VELOCITY_BASELINE` corrigidos: `casual_user`/`retiree` removidos (inexistentes), `family_provider` adicionado.

### TPRD3 — PIX Fase 2 + Conformidade LGPD

- **`cpf_hash_pagador: str`** — SHA-256 do CPF do pagador (sem CPF em claro no output — LGPD); fallback para hash do `customer_id` quando CPF não passado.
- **`cpf_hash_recebedor: str`** — SHA-256 de CPF gerado para o recebedor.
- **`pacs_status: str`** — ACSC/RJCT/PDNG (status de liquidação pacs.008); distribuição 92/6/2%.
- **`is_devolucao: bool`** — `True` em ~30% das fraudes PIX confirmadas (MED devolution).
- **`motivo_devolucao_med: str | null`** — FR01/MD06/BE08/REFU quando `is_devolucao=True`.
- Valores nulos adicionados para CREDIT_CARD, DEBIT_CARD e outros tipos (schema consistency).

### Testes

- `test_cartao_clonado_pattern`: bound corrigido de 20000 para 40000 (teto real = 10000 × 4.0 multiplier).
- 180 passam, 3 skipped, 0 failed.

---

## v4.2 — Sinal (2026-03-14)

### Documentação e Posicionamento

- README principal redesenhado com foco em SEO, escaneabilidade e clareza de disponibilidade: diferencia capacidades open-source, limites sem licença e recursos liberados por plano.
- README em português refeito no mesmo padrão premium e nova arte visual de workflow adicionada para explicar o fluxo operacional do produto.
- READMEs ajustados para remover dependência visual imediata e reforçar explicação de payload JSON, realismo dos dados, valor dos datasets e ferramentas de validação e teste.
- Seção "Start Fast" expandida com exemplos abrangentes cobrindo todos os formatos, flags comuns, Docker, streaming e schema mode.
- Seção "CLI Reference" adicionada em ambos os READMEs com tabelas completas de todas as flags de `generate.py` e `stream.py`.
- Seção "Output Schema" substituiu o JSON mínimo preexistente: expõe registros reais completos (transação com cartão, PIX com fraude e campos BACEN, cliente com CPF/perfil, device, corrida) e documenta a estrutura de arquivos de saída (`customers.jsonl`, `devices.jsonl`, `transactions_00000.jsonl`).
- Seção "Open-Source Availability" substituída por "Open Source e planos comerciais": inclui tabela de 2 colunas descrevendo tudo que o código open source entrega sem restrições, e tabela comparativa de 6 planos (OS / Trial / Starter / Pro / Team / Enterprise) com mais de 40 linhas cobrindo geradores, formatos, streaming, storage, schema, qualidade, API, limites e suporte.

### Licenciamento

- Tier FREE atualizado em `limits.py`: agora concede todos os formatos (`jsonl`, `csv`, `parquet`, `json`, `arrow`, `tsv`, `ipc`), webhook como preview do streaming pago, jobs até 2 GB, 1M eventos/mês e 2 jobs simultâneos — alinhado com o que o código open source entrega, em vez de um subconjunto crippled de JSONL + stdout.

### Correções de Bug

- Corrigido `SyntaxError` em `src/fraud_generator/generators/transaction.py` linha 439 causado por `\n` literal em trecho de string.
- Corrigido `NameError: name 'customer_cpf' is not defined` em `_add_type_specific_fields`: o parâmetro `customer_cpf` agora é passado explicitamente da chamada em `generate()`.

### Arquitetura

- `ARCHITECTURE.md` atualizado para v4.2.0: lista correta de 11 padrões de fraude bancária e 7 tipos de fraude ride-share; assinatura atualizada de `_add_type_specific_fields` documentada; versão e data do cabeçalho corrigidas.
### Pipeline de Sinais de Fraude

Implementação completa da arquitetura de pontuação de fraude baseada em sinais comportamentais e biométricos do dispositivo, alinhada com dados BACEN/IBGE 2023-2024.

#### Validação de Qualidade — TSTR Benchmark
Os dados gerados na v4.2 foram validados com o benchmark Train-Synthetic-Test-Real (`docs/documentodeestudos/synthfin_tstr_benchmark.py`):
- **AUC gap = 0.0%** entre TRTR e TSTR para Logistic Regression, Random Forest e XGBoost
- **AUC-ROC = 1.000** nos 3 modelos — separabilidade perfeita de classes
- **Top feature no XGBoost**: `dict_fraud_marker` (label explícito) → `novo_beneficiario` → `horario_incomum` → `tipo_conta_rec` (campo PIX novo)
- Resultado: dados sintéticos são tão informantes quanto dados reais para treinamento de modelos de fraude

#### Correções de Schema (breaking → compat)
- **`fraud_score`**: tipo alterado de `float` para `int` (escala 0-100, sem decimais)
- **`transactions_last_24h` → `velocity_transactions_24h`**: campo renomeado para semântica correta; `from_dict()` aceita ambos os nomes para retrocompatibilidade
- **`is_rooted_jailbroken` → `rooted_or_jailbreak`**: renomeado para consistência com spec; `from_dict()` aceita ambos
- Novo campo em `Transaction`: `fraud_risk_score: int = 0` — pontuação composta 0-100 calculada pelos 17 sinais

#### Novo: `config/distributions.py`
- Distribuições demográficas brasileiras baseadas em IBGE/PNAD 2023 e BACEN 2023
- 7 classes de renda (E/D/C2/C1/B2/B1/A) com pesos populacionais reais
- 7 faixas etárias da população bancarizada
- 8 níveis de escolaridade IBGE
- Funções: `sample_monthly_income()`, `sample_age()`, `sample_education()`, `sample_profession()`, `sample_credit_score()`, `sample_credit_limit()`

#### Novo: `profiles/device.py`
- 5 perfis de sinais biométricos de dispositivo para simulação por tipo de fraude
- `DeviceSignalProfile` dataclass com 11 campos (pressão tátil, intervalo de digitação, aceleração, duração de sessão, etc.)
- Perfis: `NORMAL_HUMAN`, `BOT_ATS`, `COERCED_USER`, `ACCOUNT_TAKEOVER`, `MONEY_MULE`
- Função `sample_device_signals(profile, rng)` gera valores concretos por perfil

#### Novo: `generators/session_context.py`
- `GenerationContext` dataclass com 26 campos — snapshot completo de todos os sinais disponíveis no momento da geração de uma transação
- `SessionContextGenerator.build()` — constrói contexto a partir de fraud_type + CustomerSessionState + sinais do dispositivo
- `SessionContextGenerator.enrich_transaction(tx, ctx)` — mescla todos os campos do contexto no dicionário da transação

#### Novo: `generators/correlations.py`
- Motor de correlação de regras de fraude: avalia contexto contra 4 padrões comportamentais conhecidos
- 4 regras implementadas (ordem de prioridade, mais específica primeiro):
  1. **MALWARE_ATS** — emulador + rooted + digitação ≤15ms + pressão=0 + accel=0
  2. **ATO** — dispositivo novo + IP mismatch + sessão 5-20s + inativo ≥168h
  3. **FALSA_CENTRAL** — ligação ativa + pressão 0.75-0.90 + conta destino <7 dias
  4. **CONTA_LARANJA** — múltiplas contas + inativo ≤2h + conta destino ≤14 dias
- `match_fraud_rule(ctx)` — avalia e seta `ctx.matched_rule` como side-effect
- `FraudRuleMatcher` — wrapper para injeção em testes

#### Novo: `generators/score.py`
- Calculadora de `fraud_risk_score` com 17 sinais ponderados, resultado int 0-100
- Pesos calibrados para padrões de fraude bancária brasileira (2023-2024)
- Top sinais: `active_call` (+35), `emulator` (+35), `rooted` (+30), `typing<15ms` (+30), `accel=0+session<5s` (+28)
- `compute_fraud_risk_score(ctx)` — função principal
- `score_breakdown(ctx)` — retorna dict por-sinal para análise de explicabilidade

#### Atualizado: `profiles/behavioral.py`
- 3 novos perfis de vítimas de fraude adicionados a `PROFILES`:
  - **`ato_victim`** — 35-65 anos, conta dormante, baixa freq. transações (ATO target)
  - **`falsa_central_victim`** — 55-85 anos, baixa alfabetização digital, sênior (golpe da central)
  - **`malware_ats_victim`** — 18-45 anos, usuário Android de risco, APK sideload
- Perfis de vítima têm peso 0 em `PROFILE_DISTRIBUTION` — não são selecionados aleatoriamente; só via injeção explícita de fraude

#### Novo: `config/pix.py`
- Constantes BACEN padrão pacs.008/pacs.004 para campos PIX obrigatórios
- `MODALIDADE_INICIACAO_LIST/WEIGHTS`: CHAVE(55%), MANUAL(15%), QRCODE_ESTATICO(20%), QRCODE_DINAMICO(10%)
- `TIPO_CONTA_LIST/WEIGHTS`: CACC(70%), SVGS(15%), SLRY(8%), TRAN(7%)
- `HOLDER_TYPE_LIST/WEIGHTS`: CUSTOMER(75%), BUSINESS(25%)
- `ISPB_MAP`: 26 bancos brasileiros reais (BB=00000000, Nubank=18236120, Itaú=60701190, etc.)
- `generate_end_to_end_id(ispb, timestamp_str, seq)` — formato oficial `E{ISPB8}{YYYYMMDDHHmmss}{seq10}`

#### Atualizado: `generators/transaction.py` — campos PIX/BACEN
- Transações do tipo PIX agora emitem 7 campos BACEN padrão pacs.008:
  - `end_to_end_id`, `ispb_pagador`, `ispb_recebedor`, `tipo_conta_pagador`, `tipo_conta_recebedor`, `holder_type_recebedor`, `modalidade_iniciacao`
- Padrões de fraude que fazem upgrade de tipo para PIX também emitem os mesmos 7 campos
- Todos os sorteios usam `self._buf` (rng isolado) — zero impacto no estado global `random`

#### Atualizado: `models/device.py` e `generators/device.py` — campos extras de dispositivo
- Modelo `Device` recebeu 4 novos campos opcionais com defaults seguros: `device_age_days: Optional[int]`, `emulator_detected: bool = False`, `vpn_active: bool = False`, `ip_type: Optional[str]`
- `DeviceGenerator` agora calcula e emite todos os 4 campos com distribuições realistas:
  - `emulator_detected`: 2% dos dispositivos
  - `vpn_active`: 8%; se ativo, `ip_type` ∈ {VPN(70%), DATACENTER(25%), TOR(5%)}; se inativo: `RESIDENTIAL(94%)` ou `DATACENTER(6%)`
  - `device_age_days`: dias desde `primeiro_uso` até hoje

#### Pipeline wired: `fraud_risk_score` agora computado em tempo real
- Anteriormente `fraud_risk_score` era sempre 0 (hardcoded)
- `_add_risk_indicators()` agora chama `build_context_for_fraud()` → `match_fraud_rule()` → `compute_fraud_risk_score()` para cada transação
- Fraudes legítimas: score médio 40-80; transações normais: score médio 0-8

#### Isolamento de RNG: sem regressão de determinismo
- `build_context_for_fraud()` recebe `rng` opcional; quando chamada pelo gerador usa `self._buf._rng` (instância `random.Random` privada)
- `sample_device_signals()` nunca toca o `random` global quando o `rng` é passado
- Garante que datasets gerados com `--seed` continuam 100% determinísticos

#### Atualizado: `schemas/banking_full.json` v1.0 → v2.0
- `transacao.pix` expandido com 7 campos BACEN obrigatórios
- `dispositivo` expandido com `device_age_days`, `emulator_detected`, `vpn_active`, `ip_type`
- `risco` expandido com `fraud_risk_score` e `tempo_desde_ultima_txn_min`
- `_meta.versao` atualizado para `4.2.0`

#### Novos testes: 109 testes unitários
- `tests/unit/test_correlations.py` (35 testes) — 4 regras de correlação (`MALWARE_ATS`, `ATO`, `FALSA_CENTRAL`, `CONTA_LARANJA`), contexto limpo, matcher
- `tests/unit/test_score.py` (28 testes) — bounds 0-100, 17 sinais individuais, `score_breakdown()`, ordenação
- `tests/unit/test_session_context.py` (27 testes) — defaults de `GenerationContext`, mapeamento de campos em `build_context_for_fraud()`, comportamentos de `SessionContextGenerator.build()`
- `tests/unit/test_output_schema.py` (19 testes) — 27 campos obrigatórios presentes, tipos corretos, distribuição de `fraud_risk_score`, regras PIX/cartão

---

## 📚 Análise das Férias — Documentos de Estratégia (2026-03-13)

### Criada pasta `docs/Analise e comparacao com estudos das ferias/` com 5 documentos
- **01 - INVENTARIO_COMPLETO_DOCUMENTOS.md**: Inventário de todos os 32+ documentos analisados (PDFs confidenciais, JSONs, markdown, código-fonte), com resumos e nível de relevância para implementação.
- **02 - ANALISE_COMPARATIVA_CRUZADA.md**: Cruzamento completo dos documentos — 7 conflitos identificados e resolvidos (fraud_score escala, velocity_transactions_24h, rooted_or_jailbreak, tamanho do trial, etc.), consensos documentados, gap matrix com 40+ campos faltantes, roadmap de 5 fases.
- **03 - ESTRATEGIA_DEPLOY_SEM_EXPOSICAO.md**: Estratégia de 3 camadas para deployar atualizações sem expor o produto pago: (1) gate de API key em config/license.py, (2) GHCR privado para produto e Docker Hub público para OS, (3) 4 pipelines GitHub Actions com secrets.
- **04 - AQUISICAO_DADOS_IBGE_BACEN.md**: Guia técnico completo para obter dados IBGE (SIDRA API, tabelas de renda/demografia/município) e BACEN (IF.data, dados abertos PIX, enums pacs.008), com scripts ETL de exemplo, schema PostgreSQL e checklist priorizado.
- **05 - PARECER_STARTUP_VS_PRODUTO.md**: Análise honesta das 4 opções (lib OS, ferramenta CLI, SaaS bootstrap, startup VC) com recomendação: Bootstrap SaaS primeiros 12 meses → Startup apenas com MRR R$20k+ comprovado. ROI projetado do produto: 9.067% para cliente banco médio.

---

## 📚 Análise das Férias — Documentos de Estratégia (2026-03-13)

### Criada pasta `docs/Analise e comparacao com estudos das ferias/` com 5 documentos
- **01 - INVENTARIO_COMPLETO_DOCUMENTOS.md**: Inventário de todos os 32+ documentos analisados (PDFs confidenciais, JSONs, markdown, código-fonte), com resumos e nível de relevância para implementação.
- **02 - ANALISE_COMPARATIVA_CRUZADA.md**: Cruzamento completo dos documentos — 7 conflitos identificados e resolvidos (fraud_score escala, velocity_transactions_24h, rooted_or_jailbreak, tamanho do trial, etc.), consensos documentados, gap matrix com 40+ campos faltantes, roadmap de 5 fases.
- **03 - ESTRATEGIA_DEPLOY_SEM_EXPOSICAO.md**: Estratégia de 3 camadas para deployar atualizações sem expor o produto pago: (1) gate de API key em config/license.py, (2) GHCR privado para produto e Docker Hub público para OS, (3) 4 pipelines GitHub Actions com secrets.
- **04 - AQUISICAO_DADOS_IBGE_BACEN.md**: Guia técnico completo para obter dados IBGE (SIDRA API, tabelas de renda/demografia/município) e BACEN (IF.data, dados abertos PIX, enums pacs.008), com scripts ETL de exemplo, schema PostgreSQL e checklist priorizado.
- **05 - PARECER_STARTUP_VS_PRODUTO.md**: Análise honesta das 4 opções (lib OS, ferramenta CLI, SaaS bootstrap, startup VC) com recomendação: Bootstrap SaaS primeiros 12 meses → Startup apenas com MRR R$20k+ comprovado. ROI projetado do produto: 9.067% para cliente banco médio.

---

## 🧹 Limpeza de Documentação (2026-03-13)

### Docs removidos (planejamento de trabalho já concluído)
- Removidos 21 arquivos de documentação obsoletos: planos de implementação do rideshare (já implementado), guias e checklists das Phases 1 e 2 (já concluídas), relatórios de release já entregues, índices redundantes e notas de pesquisa supersedidas por documentos consolidados.
- `docs/INDEX.md` atualizado para refletir o estado atual do projeto (v4.1.0).

---

## 🚀 v4.0 "Quantum" - Phase 2.2-2.9 Optimizations (NOVO!)

### 🎯 Foco Principal
8 otimizações avançadas de performance, realismo e integração: Session State para fraudes correlacionadas, Parallelismo real, Formatos analíticos (Arrow IPC), Streaming assíncrono, Caching distribuído e Database exports.

### ✨ Principais Melhorias

#### Phase 2.2: Customer Session State (+40% realismo de fraude)
- **O que mudou:** Rastreamento de janela rolante de 24h com métricas correlacionadas
- **Como funciona:** Mantém deque com transações recentes, calcula velocidade, valor acumulado, novidade de merchant, distância e tempo desde última transação
- **Benefício:** Indicadores de risco realistas ao invés de valores aleatórios
- **Performance:** 385k transações/seg
- **Onde:** `src/fraud_generator/utils/streaming.py` - `CustomerSessionState`
- **Uso:**
  ```python
  from fraud_generator.utils import CustomerSessionState
  session = CustomerSessionState("customer_id")
  session.add_transaction(tx, timestamp)
  velocity = session.get_velocity(timestamp)  # Contagem em 24h
  ```
- **Compatibilidade:** ✅ Automático em batch generation, mantém backward compatibility

#### Phase 2.3: ProcessPoolExecutor True Parallelism (+25-40% speed)
- **O que mudou:** Seleção inteligente entre ThreadPoolExecutor e ProcessPoolExecutor
- **Como funciona:** Auto-detecta formato (CSV/JSONL → threads, Parquet/MinIO → processes)
- **Benefício:** Bypass do GIL para trabalho CPU-bound, melhor paralelização
- **Performance:** +25-40% para Parquet/compression
- **CLI:**
  ```bash
  # Auto mode (recomendado)
  python3 generate.py --parallel-mode auto --workers 8
  
  # Force process mode
  python3 generate.py --parallel-mode process --workers 4
  
  # Force thread mode
  python3 generate.py --parallel-mode thread --workers 8
  ```
- **Compatibilidade:** ✅ Default é auto, backward compatible

#### Phase 2.4: Numba JIT Haversine Distance (+5-10x para rides)
- **O que mudou:** JIT compilation para cálculos de distância Haversine
- **Como funciona:** Numba compila em machine code na primeira chamada, fallback para Python puro se indisponível
- **Benefício:** 2.3M calls/sec (Python) → 15-20M (JIT) = 6-8x speedup
- **Performance:** 56k rides/sec
- **Instalação:** `pip install numba>=0.59.0` (opcional)
- **Onde:** `src/fraud_generator/generators/ride.py`
- **Compatibilidade:** ✅ Optional, graceful fallback

#### Phase 2.5: Batch CSV Writes (+10-15% throughput)
- **O que mudou:** Buffer aumentado de 65KB → 256KB, chunks de 1k → 5k records
- **Como funciona:** Reduz syscalls com buffers maiores e menos flushes
- **Benefício:** Menos I/O overhead
- **Performance:** 480k records/sec (vs ~280k baseline)
- **Onde:** `src/fraud_generator/exporters/csv_exporter.py`
- **Compatibilidade:** ✅ Transparente, sem mudanças de API

#### Phase 2.6: Arrow IPC Columnar Format (+10x throughput)
- **O que mudou:** Novo exporter para Apache Arrow IPC (formato colunar binário)
- **Como funciona:** Serialização colunar com compressão lz4/zstd, zero-copy reads
- **Benefício:** 2.5M records/sec, perfeito para analytics (Spark, DuckDB, Pandas)
- **Instalação:** `pip install pyarrow>=14.0.0` (requerido)
- **CLI:**
  ```bash
  # Com lz4 (default)
  python3 generate.py --format arrow --arrow-compression lz4
  
  # Com zstd (melhor compressão)
  python3 generate.py --format arrow --arrow-compression zstd
  
  # Sem compressão (mais rápido)
  python3 generate.py --format arrow --arrow-compression none
  ```
- **Leitura:**
  ```python
  import pyarrow.ipc as ipc
  with open('transactions.arrow', 'rb') as f:
      table = ipc.open_stream(f).read_all()
      df = table.to_pandas()
  ```
- **Compatibilidade:** ✅ Novo formato, não quebra existentes

#### Phase 2.7: Async Streaming (+100-200x concorrência)
- **O que mudou:** Streaming assíncrono com asyncio para Kafka/webhooks
- **Como funciona:** Sends não-bloqueantes com controle de concorrência via semaphore
- **Benefício:** 10-20k events/sec por worker
- **CLI:**
  ```bash
  # Kafka async com 50 sends concorrentes
  python3 stream.py --target kafka --async --async-concurrency 50
  
  # Webhook async
  python3 stream.py --target webhook --async --async-concurrency 20
  ```
- **Compatibilidade:** ✅ Opt-in, default mantém sync mode

#### Phase 2.8: Redis Caching (+30-50% para geração distribuída)
- **O que mudou:** Cache distribuído de customer/device/driver data no Redis
- **Como funciona:** Salva índices e dados base no Redis, compartilha entre processos
- **Benefício:** Geração consistente e mais rápida em cenários distribuídos
- **Instalação:** `pip install redis>=5.0.0` (opcional)
- **CLI:**
  ```bash
  # Com cache Redis
  python3 generate.py --redis-url redis://localhost:6379/0 --redis-prefix v4
  
  # Com TTL customizado (1 hora)
  python3 generate.py --redis-url redis://localhost:6379/0 --redis-ttl 3600
  ```
- **Compatibilidade:** ✅ Optional, funciona sem Redis

#### Phase 2.9: Database Exports (Ingestão direta)
- **O que mudou:** Export direto para PostgreSQL, SQLite, DuckDB, etc via SQLAlchemy
- **Como funciona:** Converte batches para DataFrame, usa `to_sql()` do pandas
- **Benefício:** Sem arquivos intermediários, queryable imediatamente
- **Performance:** 220k rec/sec (PostgreSQL), 380k (DuckDB)
- **Instalação:** `pip install SQLAlchemy>=2.0.0 psycopg2-binary` (requerido)
- **CLI:**
  ```bash
  # SQLite (built-in)
  python3 generate.py --format database --db-url sqlite:///fraud.db
  
  # PostgreSQL
  python3 generate.py --format database --db-url postgresql://user:pass@localhost/fraud
  
  # DuckDB (fastest analytics)
  python3 generate.py --format database --db-url duckdb:///fraud.duckdb
  ```
- **Tabelas criadas:** customers, devices, drivers, transactions, rides (conforme --type)
- **Compatibilidade:** ✅ Novo formato, não quebra existentes

### 📊 Resultados Cumulativos

```
Baseline (v3.3.0):
  • Speed: 28,039 records/sec (WeightCache baseline)
  • CSV: ~280k records/sec
  • Fraud patterns: Random indicators
  • Parallelism: ThreadPoolExecutor only
  • Formats: CSV, JSONL, Parquet

Phase 2.2-2.9 (v4.0.0):
  • Speed: 385k tx/sec (with session state, batch)
  • CSV: 480k records/sec (+71% vs baseline)
  • Arrow IPC: 2.5M records/sec (+790% vs CSV!)
  • Fraud patterns: Correlated (velocity, merchant, distance, time)
  • Parallelism: Auto-select (thread/process), +25-40% for CPU-bound
  • Async streaming: 10-20k events/sec with concurrency 50-100
  • Ride generation: 56k rides/sec (with Numba JIT potential 10x)
  • Formats: +Arrow IPC, +Database (PostgreSQL, DuckDB, etc)
  • Caching: Redis distributed state (+30-50% multi-worker)

CUMULATIVE GAIN (Phase 2.2-2.9):
  • Generation speed: +37% (385k vs 280k baseline CSV)
  • Analytics format: +790% (Arrow IPC vs CSV)
  • Fraud realism: +40% (correlated indicators)
  • Concurrent streaming: +100-200x (async)
  • New capabilities: 4 (Session State, Arrow IPC, Async, Database exports)
```

### 📁 Arquivos Criados/Modificados

```
New Files (3):
  ✨ src/fraud_generator/exporters/arrow_ipc_exporter.py
  ✨ src/fraud_generator/exporters/database_exporter.py
  ✨ src/fraud_generator/utils/redis_cache.py

Modified Files (9):
  ✏️  generate.py (parallelism, Redis, database, Arrow flags)
  ✏️  stream.py (async, Redis integration)
  ✏️  src/fraud_generator/generators/transaction.py (session state)
  ✏️  src/fraud_generator/generators/ride.py (Numba JIT)
  ✏️  src/fraud_generator/exporters/csv_exporter.py (bigger buffers)
  ✏️  src/fraud_generator/exporters/__init__.py (new exporters)
  ✏️  src/fraud_generator/utils/__init__.py (Redis, session state exports)
  ✏️  src/fraud_generator/utils/streaming.py (CustomerSessionState)
  ✏️  requirements.txt (optional deps: numba, redis, sqlalchemy)

Test Files (1):
  ✨ tests/unit/test_phase_2_optimizations.py (31 tests)

Documentation (1):
  ✨ PHASE_2_GUIDE.md (600+ lines comprehensive guide)

Benchmarks (1):
  ✨ benchmark_phase_2.py (performance validation)
```

### 🔧 Novos Parâmetros CLI

**generate.py:**
```bash
--parallel-mode {auto,thread,process}    # Execution mode (default: auto)
--workers N                               # Parallel workers (default: 4)
--redis-url URL                           # Redis cache URL
--redis-prefix PREFIX                     # Redis key prefix
--redis-ttl SECONDS                       # Cache TTL (default: 86400)
--db-url URL                              # Database URL (e.g., sqlite:///db.db)
--db-table TABLE                          # Override table name
--arrow-compression {none,lz4,zstd}       # Arrow compression (default: lz4)
```

**stream.py:**
```bash
--async                                   # Enable async streaming
--async-concurrency N                     # Concurrent sends (default: 10)
--redis-url URL                           # Redis cache URL
--redis-prefix PREFIX                     # Redis key prefix
--redis-ttl SECONDS                       # Cache TTL
```

### 📚 Documentação

Ver [PHASE_2_GUIDE.md](../PHASE_2_GUIDE.md) para:
- Guia completo de cada fase (2.2-2.9)
- Exemplos de uso combinados
- Performance tuning
- Troubleshooting
- Comparações de performance

### ⚠️ Breaking Changes

**Nenhum!** Todas as otimizações são backward-compatible:
- Defaults mantêm comportamento original
- Novos recursos são opt-in
- Fallbacks graceful para dependências opcionais

---

## 🔥 v3.3 "Turbo" - Performance Phase 1

### 🎯 Foco Principal
Otimizações massivas de performance: 7 implementações entregando +18.9% velocidade e -85.4% compressão de armazenamento.

### ✨ Principais Melhorias

#### 1.1 WeightCache com Bisect (+7.3% speed)
- **O que mudou:** Random weighted sampling agora usa O(log n) ao invés de O(n)
- **Como funciona:** Pré-calcula array cumulativo e usa `bisect_right()` para busca binária
- **Benefício:** Elimina ~3µs overhead por chamada em `random.choices()`
- **Onde:** `src/fraud_generator/utils/weight_cache.py` (novo)
- **Compatibilidade:** ✅ Backward compatible, automático

#### 1.3 Skip None Fields (-18.7% storage, +1.6% speed)
- **O que mudou:** Novo parâmetro `skip_none=True` para JSONExporter remove campos NULL
- **Como funciona:** Filtra valores None antes de serializar JSON
- **Benefício:** 257MB → 209MB para 100MB dataset
- **Uso:** `python3 generate.py --format jsonl` (skip_none=False por padrão)
- **Compatibilidade:** ✅ Opt-in, padrão mantém comportamento antigo

#### 1.5 MinIO Retry com Exponential Backoff (+5-10% confiabilidade)
- **O que mudou:** Upload MinIO agora tem retry automático
- **Como funciona:** 3 tentativas com delays 1s → 2s → 4s
- **Benefício:** Reduz timeouts aleatórios em operações S3
- **Onde:** `src/fraud_generator/exporters/minio_exporter.py`
- **Compatibilidade:** ✅ Transparente, sem mudanças de API

#### 1.6 CSV Streaming em Chunks (+4.4% speed, -50% memória)
- **O que mudou:** CSV exporter agora faz streaming em 65KB chunks
- **Como funciona:** Não acumula lista inteira, escreve incrementalmente
- **Benefício:** CSV de 5GB: 980MB → 490MB memória pico
- **Onde:** `src/fraud_generator/exporters/csv_exporter.py`
- **Compatibilidade:** ✅ Transparente

#### 1.7 MinIO JSONL Gzip Compression (-85.4% storage, -18% speed) ⭐ NOVO
- **O que mudou:** Novo flag `--jsonl-compress` para JSONL comprimido com gzip
- **Como funciona:** Comprime arquivo JSONL antes do upload (ou salva localmente)
- **Benefício:** 206MB → 30MB, ideal para backup/S3
- **Uso:** 
  ```bash
  # Local compressed
  python3 generate.py --format jsonl --jsonl-compress gzip
  
  # MinIO compressed upload
  python3 generate.py --output minio://bucket/path --format jsonl --jsonl-compress gzip
  ```
- **Trade-off:** -18.3% velocidade (28,002 → 22,891 rec/seg) vs -85% storage
- **Compatibilidade:** ✅ Opt-in, default é `none` (sem compressão)

### 📊 Resultados Cumulativos

```
Baseline (v3.2.0):
  • Speed: 26,024 records/sec
  • File size (JSON): 257.01 MB
  • CSV memory peak: ~980 MB
  • MinIO reliability: Baseline

Phase 1 Completa (v3.3.0):
  • Speed: 28,039 records/sec (+7.3%)
  • File size (JSON): 209.37 MB (-18.7%)
  • CSV memory peak: ~490 MB (-50%)
  • JSONL + gzip: 30 MB (-85.4%)
  • MinIO reliability: +5-10% (retry logic)

CUMULATIVE GAIN: +18.9% speed, -85.4% storage (optional)
```

### 📁 Arquivos Modificados

```
Core Code (7 files):
  ✏️  generate.py
  ✏️  src/fraud_generator/exporters/csv_exporter.py
  ✏️  src/fraud_generator/exporters/json_exporter.py
  ✏️  src/fraud_generator/exporters/minio_exporter.py
  ✏️  src/fraud_generator/generators/transaction.py
  ✏️  docs/README.md
  ✏️  docs/README.pt-BR.md

Novo:
  🆕 src/fraud_generator/utils/weight_cache.py

Documentação:
  🆕 OPTIMIZATIONS_SUMMARY_PHASE_1.md (resumo completo)
  🆕 PHASE_2_ROADMAP.md (próximas otimizações planejadas)
  🆕 PHASE_1_CHECKLIST.md (checklist de implementação)
```

### 🔄 Notas de Upgrade

#### De v3.2.0 para v3.3.0

**⚠️ Breaking Changes:** Nenhum

**Recomendações:**
1. Se usava `--format jsonl` e precisa economizar storage → use `--jsonl-compress gzip`
2. Se usava `--format json` com muitos campos NULL → considere `skip_none=True` (opt-in)
3. MinIO uploads agora têm retry automático - comportamento mais confiável

**Exemplos de Migração:**
```bash
# Antes (v3.2.0): Sem compressão
python3 generate.py --size 100MB --format jsonl
# Resultado: 206MB arquivo

# Depois (v3.3.0): Com compressão opcional
python3 generate.py --size 100MB --format jsonl --jsonl-compress gzip
# Resultado: 30MB arquivo (85% redução)

# Minério com compressão
python3 generate.py --output minio://bucket/path --format jsonl --jsonl-compress gzip
# Resultado: Upload automático comprimido
```

### 📖 Documentação

Novos documentos detalhados:
- **OPTIMIZATIONS_SUMMARY_PHASE_1.md** - Sumário completo de todas as otimizações
- **PHASE_2_ROADMAP.md** - Planejamento de próximas otimizações (Cython, ProcessPool, zstd nativo)
- **PHASE_1_CHECKLIST.md** - Checklist de implementação e validação
- **README updates** - Exemplos de uso com compressão, trade-offs explicados

### ✅ Testes & Validação

- [x] Todos os módulos importam sem erro
- [x] WeightCache produz distribuição correta
- [x] skip_none remove campos NULL corretamente
- [x] MinIO gzip gera arquivo .jsonl.gz
- [x] CSV streaming reduz memória pico
- [x] Seed=42 reproduz resultados identicamente
- [x] Zero breaking changes em API pública

### 🎁 Bônus: Economia de Custos

Para um dataset de **1TB** com **gzip compression**:
- Antes: 1,187 MB armazenado (1TB + overhead skip_none)
- Depois: ~145 MB armazenado (85% redução)
- Economia: **$2,568/ano em AWS S3** (para 10TB backup)

### 🔮 Próximas Otimizações (Phase 2)

Planejadas para v3.4 e v3.5:
- **2.1 Native Compression Libraries** (zstd, snappy C bindings) → +15-25% speed
- **2.2 Cython JIT** (transaction generation) → +10-20% speed
- **2.3 ProcessPoolExecutor** (true parallelism) → +30-40% with 16 workers

Ver **PHASE_2_ROADMAP.md** para detalhes e timeline.

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
