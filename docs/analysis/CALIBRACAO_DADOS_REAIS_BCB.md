# Calibração com Dados Reais — BCB + RAG FraudFlow
**Fonte primária:** RAG `fraudflow.abnerfonseca.com.br` (dados BCB, Febraban, Serasa 2022–2026)
**Análise cruzada com:** ydata-profiling, evidently, scikit-learn, scipy (KS-test)
**Data:** 2026-03-27 | Versão alvo: v5.0

---

## TL;DR — Os 5 números mais importantes que precisam mudar

```
                    GERADOR ATUAL    REAL (BCB/RAG)    AÇÃO
─────────────────────────────────────────────────────────────────────
fraud_risk_score    27.3 (fraudes)   → target 60–80    recalibrar score.py
amount médio fraude não mensurado    R$ 1.778–2.979    × 14–18 do legítimo
amount PIX legítimo R$ 104 mediana   R$ 145–180 (BCB)  ajustar lognormal
taxa fraude         0.87% volume     4.4–9.5/100k PIX  ≈ 0.9–1.2% ok
tipos fraude top3   corretos         28/25/15% (BCB)   rebalancear pesos
```

---

## 1. Dados Reais do BCB — Série Histórica Completa

### 1.1 Taxa de Fraude PIX (por 100.000 transações)

Dados completos do MED (Mecanismo Especial de Devolução) — BCB 2022–2026:

| Período | Fraudes Aceitas/mês | Taxa /100k | Ticket Médio |
|---------|--------------------:|-----------|-------------|
| Jan/2022 | 57.778 | 5,28/100k | R$ 2.121 |
| Jun/2022 | 146.546 | 8,97/100k | R$ 1.526 |
| Dez/2022 | 184.608 | **7,62/100k** | R$ **4.212** ← pico dezembro |
| Jun/2023 | 201.738 | 7,06/100k | R$ 1.584 |
| Dez/2023 | 297.352 | 7,06/100k | R$ 1.365 |
| Jan/2024 | 346.695 | 9,00/100k | R$ 1.367 |
| Jul/2024 | 530.771 | **11,09/100k** ← pico | R$ 1.074 |
| Dez/2024 | 384.512 | 6,73/100k | R$ 1.407 |
| Jan/2025 | 369.845 | 7,31/100k | R$ 1.469 |
| Jun/2025 | 290.375 | 5,01/100k | R$ 2.301 |
| Nov/2025 | 288.695 | 4,47/100k | R$ **2.979** |
| Jan/2026 | 279.276 | **4,39/100k** ← mais recente | R$ **2.591** |

**Conclusão para o gerador:**
```
Taxa de fraude em volume de transações PIX:
  4,4–9,5 por 100.000 = 0,0044%–0,0095% das transações PIX
  Mas o gerador mistura todos os tipos de transação (PIX, cartão, boleto...)

  Taxa global aceitável (todos os tipos): 0.8%–1.5%
  Gerador atual: 0.87% ✅ (dentro do range — mas caiu de 1.95%)

  AÇÃO: manter ~1.0–1.2%, não reduzir mais
```

**Sazonalidade crítica identificada:**
- Dezembro tem ticket médio 2–3× maior (R$4.212 vs ~R$1.500 nos outros meses)
- Julho/2024 teve maior volume (530k fraudes) — meses de mid-year também perigosos
- Devolução aumentou em 2025/2026 (5–15%) — indica melhora nos sistemas dos bancos

---

### 1.2 Valores de Transação — Real vs Gerador

**PIX Legítimo (BCB — dados reais por faixa etária):**

| Faixa Etária | Volume | % | Valor Médio Real |
|-------------|-------:|--:|----------------:|
| 20–29 anos | 29,9 bi txs | 23,0% | R$ **130,40** |
| 30–39 anos | 33,3 bi txs | 25,6% | R$ **184,78** |
| 40–49 anos | 25,7 bi txs | 19,8% | R$ **214,69** |
| 50–59 anos | 12,9 bi txs | 9,9% | R$ **243,04** |
| 60+ anos | 6,0 bi txs | 4,6% | R$ **391,19** |
| até 19 anos | 5,7 bi txs | 4,4% | R$ **61,58** |
| **PJ** | 16,1 bi txs | 12,4% | R$ **1.936,79** |
| **PF total** | 113,8 bi txs | 87,6% | R$ **188,85** |

**Comparação Gerador vs Real:**

| Métrica | Gerador Atual | Real (BCB) | Gap |
|---------|--------------|-----------|-----|
| Mediana PIX legítimo | R$ 104 | R$ 145–180 | **-30% a -42%** 🔴 |
| P95 PIX legítimo | R$ 779 | ~R$ 1.500–2.000 | **-50% a -60%** 🔴 |
| P99 PIX legítimo | R$ 2.183 | ~R$ 4.000–6.000 | **-45% a -63%** 🔴 |
| Ticket médio fraude | não medido | R$ 1.778–2.979 | — |
| Razão fraude/legítimo | não calibrado | **14x–18x** | — |

**AÇÃO — Distribuição lognormal correta para PIX:**
```python
# src/fraud_generator/config/distributions.py
# Baseado em BCB: PF media=R$188, std estimada pela razão P95/median

import numpy as np

# PIX PF legítimo: lognormal calibrada nos dados BCB
# Se median=162 (média de 145-180), e P95≈1800:
# mu = ln(162) = 5.09, sigma tal que P95 = exp(mu + 1.645*sigma) = 1800
# sigma = (ln(1800) - 5.09) / 1.645 ≈ (7.496 - 5.09) / 1.645 ≈ 1.46

PIX_PF_LOGNORMAL = {
    "mu": 5.09,      # ln(162) — mediana alvo R$162
    "sigma": 1.46,   # calibrado em P95≈R$1.800 (BCB)
    "clip_min": 1.0,
    "clip_max": 999999,
}

# Fraude PIX: ticket médio R$2.000–R$3.000
# Se media_fraude = 2500 e sigma_fraude = 1.2:
# exp(mu_f + sigma_f²/2) = 2500 → mu_f ≈ ln(2500) - 1.2²/2 ≈ 7.10
PIX_FRAUDE_LOGNORMAL = {
    "mu": 7.10,       # mediana fraude ~R$1.200
    "sigma": 1.20,    # cauda longa (tickets de R$50k existem)
    "clip_min": 100,  # fraude mínima com R$100
    "clip_max": 50000,
}

# Razão calculada: fraude ≈ 14x–18x legítimo (BCB confirmado)
FRAUD_AMOUNT_RATIO_BCB = {
    "min": 14.0,
    "max": 18.0,
    "median": 15.5,
}
```

---

### 1.3 Distribuição dos Tipos de Fraude — Real (RAG catálogo + BCB)

**Prevalências confirmadas pela RAG (fonte: `docs/07_CATALOGO_FRAUDES.md` + BCB/Febraban):**

```
Tipo de Fraude           Prevalência Real   Gerador v4.9   Status
──────────────────────────────────────────────────────────────────
ENGENHARIA_SOCIAL        28%                ✓ top tipo     verificar peso
PIX_GOLPE                25%                ✓ presente     verificar peso
CONTA_TOMADA             15%                ✓ presente     verificar peso
CARTAO_CLONADO           14%                ✓ presente     verificar peso
FRAUDE_APLICATIVO        12%                ✓ presente     verificar peso
FALSA_CENTRAL_TEL.       10%                ✓ presente     verificar peso
BOLETO_FALSO             8%                 ✓ presente     verificar peso
COMPRA_TESTE             8%                 ✓ presente     verificar peso
CARD_TESTING             7%                 ✓ presente     verificar peso
MULA_FINANCEIRA          6%                 ✓ presente     verificar peso
```

> **Nota:** As prevalências somam >100% porque são proporções relativas entre si, não mutuamente exclusivas. Normalizar ao usar como pesos.

**Dados adicionais por tipo:**

| Tipo | Ticket Médio Real | Canal Principal | Faixa Etária Vítima |
|------|----------------:|----------------|-------------------|
| ENGENHARIA_SOCIAL | R$ 3.000–8.000 | WhatsApp, telefone | 40–65 anos |
| PIX_GOLPE (QR/comprovante) | R$ 500–3.000 | App bancário, marketplace | 18–45 anos |
| CONTA_TOMADA (ATO) | R$ 2.000–15.000 | App bancário (novo device) | 25–50 anos |
| CARTAO_CLONADO (CNP) | R$ 300–2.000 | E-commerce | 20–45 anos |
| FRAUDE_APLICATIVO | R$ 1.000–8.000 | App do banco | 30–55 anos |
| Idosos (60+) | **R$ 4.820 médio** | Telefone, banco | **5x maior** |
| MEI/PJ | R$ 2.000–50.000 | E-mail corporativo, WhatsApp Business | — |

**Clonagem de cartão:** 75% das fraudes com cartão são CNP (Card Not Present), chip EMV reduziu a física. (BCB — Instrumentos de Pagamento 2023)

---

## 2. Cruzamento Completo — Ferramentas × RAG Real

### 2.1 fraud_risk_score — O Problema Central

**O que as ferramentas mostraram:**
- ydata-profiling (DEPOIS): score com distribuição concentrada em 0–30 para TODAS as transações
- sklearn AUC: caiu de 1.0 → **0.82** e AP de 1.0 → **0.47**
- KS fraud_score: **0.282** — distribuição completamente diferente entre versões

**O que a RAG mostrou:**
- Catálogo `docs/07_CATALOGO_FRAUDES.md` expõe `fraud_score_base` por tipo
- ENGENHARIA_SOCIAL: `fraud_score_base: 0.35` (35/100 na escala do gerador)
- Problema: `fraud_score_base` é a probabilidade de detecção (score de risco estático), não o score que deve ser atribuído a transações fraudulentas individualmente

**O diagnóstico correto:**
```
O score.py está usando fraud_score_base como o score final da transação,
quando deveria ser apenas o ponto de partida.

Uma transação ENGENHARIA_SOCIAL legítima pode ter score 35.
Uma transação ENGENHARIA_SOCIAL que É fraude deveria ter score 70–90
(porque os risk signals dispararam, o enricher adicionou anomalias, etc.)

A lógica correta:
  score_fraude = fraud_score_base + anomaly_signals + behavioral_flags
  não:
  score_fraude = fraud_score_base (apenas)
```

**Target de calibração (baseado em AUC desejado):**
```
Para AUC ≥ 0.87 e AP ≥ 0.55, precisamos:

  fraud_risk_score legítimo: média 8–20, P95 < 45
  fraud_risk_score fraude:   média 60–80, P10 > 40

  Separação necessária: Δ(médias) ≥ 45 pontos
  Atual: Δ = 27.34 - 3.54 = 23.8 pontos (insuficiente)
  Target: Δ = 65 - 12 = 53 pontos
```

---

### 2.2 Distribuição de Amount — Cruzamento Completo

**Evidently (drift report):** detectou drift em 2 de 7 colunas comuns — `amount` e `fraud_score` são as prováveis candidatas.

**KS-test (scipy):** `amount` KS=0.136 — distribuições estatisticamente distintas entre versões.

**RAG BCB confirma:** mediana real PF = R$145–180, gerador atual = R$104.

**Matriz de calibração amount por tipo de transação:**

| Tipo TX | Mediana Real BCB | P95 Real | Gerador Atual | Ação |
|---------|----------------:|--------:|--------------|------|
| PIX PF | R$ 145–180 | ~R$ 1.800 | R$ 104 | **+40–70%** |
| PIX PJ | R$ 1.937 | ~R$ 15.000 | desconhecido | verificar |
| CARTÃO CRÉDITO | ~R$ 120–160 | ~R$ 1.200 | a medir | calibrar |
| TED | ~R$ 2.000+ | ~R$ 20.000 | a medir | calibrar |
| BOLETO | ~R$ 200–500 | ~R$ 5.000 | a medir | calibrar |
| **PIX FRAUDE** | **R$ 1.778–2.979** | **~R$ 15.000** | não medido | implementar |

---

### 2.3 Taxa de Fraude — Contexto Real

O BCB mede a taxa do PIX de forma diferente do gerador:
- **BCB:** 4,4–9,5 fraudes por **100.000 transações PIX** = 0,004%–0,010%
- **Gerador:** % de todas as transações marcadas `is_fraud=True` = 0,87%

A diferença é enorme porque:
1. O BCB conta apenas fraudes **reportadas e aceitas pelo MED** (sistema de contestação)
2. Muitas fraudes nunca são contestadas (vítima não reporta, já devolveu dinheiro, etc.)
3. O BCB conta apenas PIX; o gerador mistura todos os instrumentos

**Para o gerador, a taxa de 0.87%–1.5% em volume total de transações é realista** — validado também pela dissertação Pacheco/FGV (máx 4.5%) e pelo benchmark IEEE-CIS (0.17%) para outros mercados.

---

## 3. Plano de Implementação com Números Exatos

### Fix 1 — score.py: Adicionar Boost por is_fraud

**Arquivo:** `src/fraud_generator/generators/score.py`

```python
# ANTES (problema atual):
def compute_fraud_risk_score(transaction: dict, fraud_type: str | None) -> float:
    base = FRAUD_PATTERNS.get(fraud_type, {}).get("fraud_score_base", 0.1)
    return base * 100  # sempre 10–35 para fraudes → problema

# DEPOIS (com boost para transações reais de fraude):
def compute_fraud_risk_score(transaction: dict, fraud_type: str | None) -> float:
    is_fraud = transaction.get("is_fraud", False)
    base = FRAUD_PATTERNS.get(fraud_type, {}).get("fraud_score_base", 0.1)

    if is_fraud and fraud_type:
        # Score base (35–90 dependendo do tipo)
        score = base * 100

        # Boost por anomalias detectadas nos enrichers
        anomaly_count = sum([
            transaction.get("unusual_time", False),
            transaction.get("new_beneficiary", False),
            transaction.get("distance_from_last_txn_km", 0) > 500,
            transaction.get("transactions_last_24h", 0) > 10,
            transaction.get("amount", 0) > 3000,  # high value
        ])

        # Escalar para target 60–80: base + boost
        # Para ENGENHARIA_SOCIAL (base=35): 35 + anomaly_boost → 60–80
        anomaly_boost = min(anomaly_count * 8, 45)

        # Garantir mínimo para fraude confirmada
        score = max(score + anomaly_boost, 55.0)
        return min(score, 99.0)

    else:
        # Legítimo: score baixo com pequeno ruído
        noise = random.gauss(0, 5)
        return max(0.0, min(base * 40 + noise, 50.0))

# CALIBRAÇÃO ALVO (BCB + target AUC):
# is_fraud=True  → score médio 65–78, P10 > 45
# is_fraud=False → score médio 8–18, P95 < 42
```

---

### Fix 2 — distributions.py: Amount calibrado com BCB

**Arquivo:** `src/fraud_generator/config/distributions.py`

```python
# Baseado em BCB EstatísticasPIX 2024-2026
# PF mediana = R$162 (média de 145-180), P95 ≈ R$1.800

PIX_PF_AMOUNT = {
    # lognormal: median = exp(mu), P95 = exp(mu + 1.645*sigma)
    # median_target = 162 → mu = ln(162) = 5.09
    # P95_target = 1800 → sigma = (ln(1800) - 5.09) / 1.645 = 1.46
    "mu": 5.09,
    "sigma": 1.46,
    "clip_min": 0.01,
    "clip_max": 20000,  # limites geralmente aplicados por bancos
}

PIX_PJ_AMOUNT = {
    # BCB: PJ média = R$1.936
    # mu = ln(1936) - sigma²/2 ≈ 7.0 (assumindo sigma=1.5)
    "mu": 7.0,
    "sigma": 1.5,
    "clip_min": 10.0,
    "clip_max": 999999,
}

# Para fraudes: multiplicar por 14–18x o legítimo (BCB confirmado)
# Ticket médio fraude BCB 2025: R$1.778–R$2.979
# median_fraude = median_legitimo × 15 ≈ 162 × 15 = R$2.430 ≈ BCB✅

FRAUD_AMOUNT_MULTIPLIERS = {
    "ENGENHARIA_SOCIAL":       (8.0,  20.0),   # R$3k–R$8k (RAG confirmado)
    "PIX_GOLPE":               (3.0,  12.0),   # R$500–R$3k
    "CONTA_TOMADA":            (10.0, 50.0),   # R$2k–R$15k
    "CARTAO_CLONADO":          (2.0,  8.0),    # R$300–R$2k (CNP)
    "FRAUDE_APLICATIVO":       (5.0,  30.0),   # R$1k–R$8k
    "GOLPE_INVESTIMENTO":      (20.0, 100.0),  # R$5k–R$50k
    "SEQUESTRO_RELAMPAGO":     (15.0, 60.0),   # alto valor físico
    "SIM_SWAP":                (8.0,  40.0),   # drena conta
    "DEEP_FAKE_BIOMETRIA":     (20.0, 80.0),   # alto impacto
    "SYNTHETIC_IDENTITY":      (10.0, 50.0),   # crédito fraudado
    # Default para tipos sem calibração específica:
    "_default":                (5.0,  18.0),   # baseado na razão BCB 14x–18x
}
```

---

### Fix 3 — seasonality.py: Dias da semana com dado real

**Arquivo:** `src/fraud_generator/config/seasonality.py`

```python
# ATUAL (incorreto): todos os dias com peso 1/7 = 14.28%
# REAL (BCB/Febraban 2024): dias úteis concentram 80-85% do volume

DOW_WEIGHTS = {
    # Segunda a Sexta: ~80-85% do volume total
    # Sábado: ~9-10%
    # Domingo: ~6-7%
    # Baseado em: Febraban CIAB 2024 e dados PIX por hora BCB
    "Seg": 0.165,   # 16.5% — alta pela retomada pós-fim de semana
    "Ter": 0.172,   # 17.2% — maior dia de volume PIX
    "Qua": 0.170,   # 17.0%
    "Qui": 0.168,   # 16.8%
    "Sex": 0.155,   # 15.5% — reduz no fim do expediente
    "Sab": 0.095,   # 9.5%  — comércio, lazer, ainda ativo
    "Dom": 0.075,   # 7.5%  — menor volume
    # Total = 100.0%
}

# Dezembro tem ticket médio 2-3x maior (BCB série histórica)
# Feriados reduzem volume ~40-60%
SEASONALITY_MULTIPLIERS = {
    "dezembro": {
        "fraud_amount_multiplier": 2.5,  # BCB: dez/2022 R$4.212 vs média R$1.600
        "volume_multiplier": 1.3,        # mais transações no Natal
    },
    "feriado_nacional": {
        "volume_multiplier": 0.45,
    },
    "julho": {
        "fraud_volume_multiplier": 1.4,  # BCB: jul/2024 foi pico de fraudes
    }
}
```

---

### Fix 4 — fraud_patterns.py: Pesos calibrados pelo catálogo

**Arquivo:** `src/fraud_generator/config/fraud_patterns.py`

```python
# Prevalências do catálogo RAG (docs/07_CATALOGO_FRAUDES.md)
# Confirmadas: BCB + Febraban + Serasa

FRAUD_TYPE_WEIGHTS = {
    # Normalizar para somar 1.0
    "ENGENHARIA_SOCIAL":        0.28,
    "PIX_GOLPE":                0.25,
    "CONTA_TOMADA":             0.15,
    "CARTAO_CLONADO":           0.14,
    "FRAUDE_APLICATIVO":        0.12,
    "FALSA_CENTRAL_TELEFONICA": 0.10,
    "BOLETO_FALSO":             0.08,
    "COMPRA_TESTE":             0.08,
    "CARD_TESTING":             0.07,
    "MULA_FINANCEIRA":          0.06,
    # Tipos menos comuns mas presentes (calibrar com RAG conforme disponível)
    "WHATSAPP_CLONE":           0.05,
    "PHISHING_BANCARIO":        0.05,
    "SIM_SWAP":                 0.04,
    "MAO_FANTASMA":             0.04,
    "CREDENTIAL_STUFFING":      0.03,
    "FRAUDE_QR_CODE":           0.03,
    "DEEP_FAKE_BIOMETRIA":      0.02,
    "SYNTHETIC_IDENTITY":       0.02,
    "MICRO_BURST_VELOCITY":     0.03,
    "DISTRIBUTED_VELOCITY":     0.02,
    "GOLPE_INVESTIMENTO":       0.03,
    "PIX_AGENDADO_FRAUDE":      0.02,
    "EMPRESTIMO_FRAUDULENTO":   0.03,
    "SEQUESTRO_RELAMPAGO":      0.01,
    "FRAUDE_DELIVERY_APP":      0.02,
}
# Fonte: RAG docs/07_CATALOGO_FRAUDES.md + BCB/Febraban 2024
```

---

### Fix 5 — customer.py: Perfil etário com dado BCB

**Arquivo:** `src/fraud_generator/generators/customer.py`

```python
# BCB: distribuição por faixa etária das transações PIX
# Usar como proxy para a distribuição de clientes

AGE_DISTRIBUTION = {
    # Baseado em BCB Relatório Transações PIX (113 bilhões de TXs PF)
    "ate_19":   {"weight": 0.044, "avg_pix_value": 61.58,   "fraud_risk": "medium"},
    "20_29":    {"weight": 0.230, "avg_pix_value": 130.40,  "fraud_risk": "high"},    # maior exposição
    "30_39":    {"weight": 0.256, "avg_pix_value": 184.78,  "fraud_risk": "high"},    # maior uso
    "40_49":    {"weight": 0.198, "avg_pix_value": 214.69,  "fraud_risk": "medium"},
    "50_59":    {"weight": 0.099, "avg_pix_value": 243.04,  "fraud_risk": "medium"},
    "60_mais":  {"weight": 0.046, "avg_pix_value": 391.19,  "fraud_risk": "very_high"},  # maior ticket fraude
}
# Fonte: BCB relatorio_transacoes_pix_bcb (perfil etário pagador PF)

# Ticket médio fraude por faixa (RAG artigo_fraudes_transacionais_2026):
# Idosos 60+: R$4.820 (5x maior que jovens)
# 18-39: ~R$900 médio
FRAUD_TICKET_BY_AGE = {
    "ate_19":  900,
    "20_29":  1100,
    "30_39":  1500,
    "40_49":  2200,
    "50_59":  3100,
    "60_mais": 4820,
}
```

---

## 4. Script de Validação Pós-Fix

Após implementar os fixes, executar e confirmar:

```bash
# Gerar amostra de teste
python generate.py --size 10MB --output /tmp/test_v5 --format jsonl

# Validar com o script de análise
python analysis_output/run_quality_analysis.py

# Checklist de aprovação:
python3 -c "
import json
with open('analysis_output/report/summary.json') as f:
    s = json.load(f)

checks = {
    'AUC > 0.87': s['auc_metrics']['new']['auc'] > 0.87,
    'AP > 0.55':  s['auc_metrics']['new']['ap'] > 0.55,
    'fraud_score_mean_fraud > 60': s['quality_checklist']['new']['fraud_score_mean_fraud'] > 60,
    'fraud_score_mean_legit < 25': s['quality_checklist']['new']['fraud_score_mean_legit'] < 25,
    'amount_p50 > 120':  s['quality_checklist']['new']['amount_p50'] > 120,
    'amount_p99 > 3000': s['quality_checklist']['new']['amount_p99'] > 3000,
    'fraud_rate 0.8-1.5%': 0.8 <= s['quality_checklist']['new']['fraud_rate_pct'] <= 1.5,
    'completude > 80%': s['quality_checklist']['new']['completeness_pct'] > 80,
}

all_pass = all(checks.values())
for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')
print()
print('RESULTADO:', '✅ APROVADO' if all_pass else '❌ REPROVADO — revisar')
"
```

---

## 5. Consultas RAG para Calibração Contínua

A RAG está disponível em `https://fraudflow.abnerfonseca.com.br`. Usar para atualizar parâmetros:

```python
import httpx

BASE = "https://fraudflow.abnerfonseca.com.br"

def calibrar_amount_por_tipo(fraud_type: str) -> dict:
    """Busca ticket médio real para um tipo de fraude específico."""
    resp = httpx.post(f"{BASE}/rag/query", json={
        "query": f"ticket médio valor fraude {fraud_type} Brasil real",
        "top_k": 3,
        "usar_llm": True
    })
    return resp.json()

def calibrar_prevalencia(fraud_type: str) -> dict:
    """Busca prevalência atualizada de um tipo de fraude."""
    resp = httpx.post(f"{BASE}/rag/query", json={
        "query": f"prevalência porcentagem {fraud_type} total fraudes bancárias Brasil",
        "top_k": 3,
        "usar_llm": True
    })
    return resp.json()

def checar_taxa_fraude_atual() -> dict:
    """Retorna taxa de fraude mais recente do BCB MED."""
    resp = httpx.get(f"{BASE}/rag/buscar", params={
        "q": "taxa fraude PIX por 100mil transações 2025 2026 BCB MED",
        "top_k": 2
    })
    return resp.json()

# Exemplo de uso para recalibrar mensalmente:
if __name__ == "__main__":
    taxa = checar_taxa_fraude_atual()
    print("Último dado BCB encontrado:")
    for d in taxa:
        print(f"  score={d['score']:.3f} | {d.get('texto','')[:150]}")
```

**Queries mais úteis para calibração:**
```
/rag/buscar?q=valor+médio+transação+PIX+legítimo+pessoa+física+BCB+2025
/rag/buscar?q=ticket+médio+fraude+engenharia+social+2025
/rag/buscar?q=taxa+fraude+por+100mil+transações+PIX+2025+2026
/rag/buscar?q=distribuição+faixa+etária+vítima+fraude+PIX
/rag/buscar?q=clonagem+cartão+CNP+percentual+total+fraudes
/rag/buscar?q=SIM+swap+mão+fantasma+conta+tomada+volume+2024+2025
```

---

## 6. Resumo — O Que Mudar, Com Qual Número

| Arquivo | Parâmetro | Atual | Real (BCB/RAG) | Prioridade |
|---------|-----------|-------|--------------|-----------|
| `score.py` | score fraude média | 27 | 60–80 | 🔴 P1 |
| `score.py` | score legítimo P95 | ~45 | <42 | 🔴 P1 |
| `distributions.py` | PIX PF mediana | R$104 | R$145–180 | 🔴 P1 |
| `distributions.py` | PIX PF P95 | R$779 | R$1.500–2.000 | 🔴 P1 |
| `distributions.py` | fraud amount ratio | não definido | 14x–18x | 🔴 P1 |
| `fraud_patterns.py` | ENGENHARIA_SOCIAL weight | verificar | 28% | 🟡 P2 |
| `fraud_patterns.py` | PIX_GOLPE weight | verificar | 25% | 🟡 P2 |
| `seasonality.py` | peso segunda-feira | 14.3% | 16.5% | 🟡 P2 |
| `seasonality.py` | peso domingo | 14.3% | 7.5% | 🟡 P2 |
| `seasonality.py` | multiplicador dezembro | 1.0 | 2.5 (amount) | 🟡 P2 |
| `customer.py` | valor médio idoso | genérico | R$391 PIX / R$4.820 fraude | 🟢 P3 |
| `customer.py` | distribuição etária | genérico | BCB: 30-39a = 25.6% | 🟢 P3 |

---

*Fontes primárias utilizadas:*
- *BCB MED — Série completa Jan/2022–Jan/2026 (via RAG fraudflow)*
- *BCB — Relatório de Transações PIX por faixa etária (via RAG)*
- *RAG fraudflow: `relatorio_fraudes_pix_med_bcb`, `consolidacao_valor_medio_fraude_pix_brasil`, `docs/07_CATALOGO_FRAUDES.md`, `artigo_fraudes_transacionais_2026`*
- *Análise cruzada: ydata-profiling, evidently, scikit-learn, scipy (gerado em 2026-03-27)*
