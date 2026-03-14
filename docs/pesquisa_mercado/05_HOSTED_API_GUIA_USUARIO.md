# 🚀 Guia do Usuário — Hosted API
> Como usar a API hospedada sem precisar instalar nada

---

## 1. O que é a Hosted API?

A Hosted API é a versão mais simples de usar o BFDG: **você não precisa instalar nada**.
Nem Python, nem Docker, nem dependências.

Você manda um POST HTTP e recebe um link para download do arquivo gerado.

```
  ANTES (self-hosted):                    DEPOIS (hosted API):
  ─────────────────────                   ────────────────────
  1. instalar Python                      1. criar conta grátis
  2. pip install -r requirements.txt      2. fazer 1 chamada HTTP
  3. python3 generate.py --size 100MB     3. baixar o arquivo
  4. esperar geração                      
  5. mover arquivo                        
```

---

## 2. Fluxo Completo: Passo a Passo

```
╔══════════════════════════════════════════════════════════════════╗
║              FLUXO COMPLETO DO USUÁRIO                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  PASSO 1: Criar conta (grátis)                                  ║
║  ─────────────────────────────                                  ║
║  → Acesse: https://automabothub.com/register                   ║
║  → Preencha nome, email, empresa                               ║
║  → Você recebe um email com sua API key:                       ║
║                                                                  ║
║    De: noreply@automabothub.com                                 ║
║    Assunto: Sua licença BFDG está pronta!                      ║
║                                                                  ║
║    Sua API Key: fg_live_abc123def456...                        ║
║    Plano: FREE (50.000 eventos/mês)                            ║
║                                                                  ║
║─────────────────────────────────────────────────────────────────║
║                                                                  ║
║  PASSO 2: Gerar dados (1 chamada HTTP)                          ║
║  ────────────────────────────────────                           ║
║  → POST https://api.automabothub.com/v1/generate               ║
║                                                                  ║
║    Resposta imediata (< 200ms):                                 ║
║    { "job_id": "job_xyz789", "status": "queued" }              ║
║                                                                  ║
║─────────────────────────────────────────────────────────────────║
║                                                                  ║
║  PASSO 3: Verificar status (polling)                            ║
║  ───────────────────────────────────                            ║
║  → GET https://api.automabothub.com/v1/jobs/job_xyz789         ║
║                                                                  ║
║    Enquanto processando: { "status": "running" }               ║
║    Quando pronto:        { "status": "done",                   ║
║                             "download_url": "https://...",     ║
║                             "expires_at": "2026-03-05T10:00Z" }║
║                                                                  ║
║─────────────────────────────────────────────────────────────────║
║                                                                  ║
║  PASSO 4: Baixar o arquivo                                      ║
║  ─────────────────────────                                      ║
║  → wget "https://..." -O meus_dados.parquet                    ║
║  → ou: import pandas as pd; df = pd.read_parquet("url...")     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 3. Exemplos de Código

### 3.1 Usando curl (terminal)

```bash
# 1. Enviar pedido de geração
curl -X POST https://api.automabothub.com/v1/generate \
  -H "Authorization: Bearer fg_live_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "transactions",
    "count": 10000,
    "fraud_rate": 0.05,
    "format": "parquet",
    "seed": 42
  }'

# Resposta:
# {"job_id": "job_xyz789", "status": "queued", "estimated_seconds": 2}

# 2. Verificar quando ficou pronto
curl https://api.automabothub.com/v1/jobs/job_xyz789 \
  -H "Authorization: Bearer fg_live_abc123"

# Resposta quando pronto:
# {
#   "status": "done",
#   "records": 10000,
#   "fraud_records": 500,
#   "format": "parquet",
#   "file_size_mb": 2.3,
#   "download_url": "https://storage.automabothub.com/jobs/job_xyz789/result.parquet?token=...",
#   "expires_at": "2026-03-05T10:30:00Z"
# }

# 3. Baixar o arquivo
wget -O transacoes_fraude.parquet "https://storage.automabothub.com/..."
```

### 3.2 Usando Python (Jupyter / Google Colab)

```python
import requests
import pandas as pd
import time

API_KEY = "fg_live_abc123"
BASE_URL = "https://api.automabothub.com/v1"

headers = {"Authorization": f"Bearer {API_KEY}"}

# ─── 1. Solicitar geração ───────────────────────────────────────────────────
resp = requests.post(f"{BASE_URL}/generate", headers=headers, json={
    "type": "transactions",
    "count": 50000,
    "fraud_rate": 0.05,
    "format": "parquet",
    "seed": 42
})
job = resp.json()
job_id = job["job_id"]
print(f"Job criado: {job_id}")

# ─── 2. Aguardar conclusão ─────────────────────────────────────────────────
while True:
    status = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers).json()
    print(f"Status: {status['status']}")
    if status["status"] == "done":
        download_url = status["download_url"]
        break
    elif status["status"] == "failed":
        raise Exception(f"Job falhou: {status.get('error')}")
    time.sleep(2)

# ─── 3. Carregar direto no pandas ─────────────────────────────────────────
df = pd.read_parquet(download_url)

print(f"Shape: {df.shape}")
print(f"Fraudes: {df['is_fraud'].sum()} ({df['is_fraud'].mean()*100:.1f}%)")
print(df.head())

# Output esperado:
# Job criado: job_xyz789
# Status: running
# Status: done
# Shape: (50000, 24)
# Fraudes: 2500 (5.0%)
#   transaction_id  customer_id       amount  ...  is_fraud  fraud_type
# 0  txn_a1b2c3d4  cust_001234   R$ 234,50  ...     False      None
# 1  txn_e5f6g7h8  cust_005678  R$ 1.890,00 ...      True  pix_cloning
```

### 3.3 Usando Python SDK (helper simplificado para incluir no projeto)

```python
# futuramente: pip install bfdg-sdk
from bfdg import BFDGClient

client = BFDGClient(api_key="fg_live_abc123")

# Uma linha para gerar e baixar
df = client.generate(
    type="transactions",
    count=50000,
    fraud_rate=0.05,
    format="parquet"
)
# Bajo automaticamente, retorna DataFrame pronto

print(df["fraud_type"].value_counts())
```

### 3.4 Gerando corridas de ride-share

```python
# Gerar corridas (Uber, 99, InDrive)
resp = requests.post(f"{BASE_URL}/generate", headers=headers, json={
    "type": "rides",
    "count": 10000,
    "fraud_rate": 0.08,     # 8% de fraude
    "format": "csv",
    "seed": 99
})

# Campos disponíveis no resultado:
# ride_id, driver_id, passenger_id, app (uber/99/indriver),
# origin_city, destination_city, distance_km, fare_brl,
# surge_multiplier, duration_minutes, is_fraud, fraud_type
# (gps_spoofing, fake_ride, driver_collusion, payment_fraud)
```

### 3.5 Gerando ambos (transactions + rides)

```python
# Tipo "all" gera os dois conjuntos de dados
resp = requests.post(f"{BASE_URL}/generate", headers=headers, json={
    "type": "all",
    "count": 5000,          # 5000 de cada tipo
    "fraud_rate": 0.05,
    "format": "parquet"
})

# Retorna ZIP com:
# result_transactions.parquet
# result_rides.parquet
# result_customers.jsonl  (compartilhado entre os dois)
```

---

## 4. Referência Completa da API

### POST /v1/generate

**Request body:**
```json
{
  "type":       "transactions" | "rides" | "all",   // obrigatório
  "count":      50000,                               // obrigatório, número de registros
  "fraud_rate": 0.05,                               // opcional, padrão: 0.05 (5%)
  "format":     "parquet" | "csv" | "jsonl",        // opcional, padrão: "parquet"
  "seed":       42,                                 // opcional (para reprodutibilidade)
  "filters": {                                      // opcional
    "state": "SP",                                  // filtrar por estado BR
    "bank": "nubank"                                // filtrar por banco
  }
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "job_abc123xyz",
  "status": "queued",
  "plan": "starter",
  "events_used_this_month": 45200,
  "events_limit_this_month": 5000000,
  "estimated_seconds": 8
}
```

### GET /v1/jobs/{job_id}

**Response quando processando:**
```json
{
  "job_id": "job_abc123xyz",
  "status": "running",
  "progress_pct": 45,
  "started_at": "2026-03-04T10:00:00Z"
}
```

**Response quando pronto:**
```json
{
  "job_id": "job_abc123xyz",
  "status": "done",
  "records": 50000,
  "fraud_records": 2500,
  "format": "parquet",
  "file_size_mb": 4.7,
  "download_url": "https://storage.automabothub.com/.../result.parquet?token=...",
  "expires_at": "2026-03-05T10:00:00Z",
  "stats": {
    "fraud_types": {
      "pix_cloning":    1100,
      "card_takeover":  850,
      "social_eng":     350,
      "account_takeover": 200
    },
    "top_banks":  ["nubank", "itau", "bradesco"],
    "states":     ["SP", "RJ", "MG", "RS"],
    "avg_amount_brl": 487.32
  }
}
```

### GET /v1/usage

```json
{
  "plan": "starter",
  "events_used_this_month": 45200,
  "events_limit": 5000000,
  "pct_used": 0.9,
  "reset_date": "2026-04-01",
  "jobs_this_month": 12
}
```

---

## 5. Como Verificar que está Funcionando

### Teste rápido (< 5 segundos):

```bash
# Teste de saúde da API
curl https://api.automabothub.com/v1/health
# → {"status": "ok", "version": "5.0.0"}

# Gerar 100 registros (mínimo possível, retorno quase imediato)
curl -X POST https://api.automabothub.com/v1/generate \
  -H "Authorization: Bearer fg_live_SEU_TOKEN" \
  -d '{"type":"transactions","count":100,"format":"jsonl"}' | python3 -m json.tool

# Se retornar job_id com status "queued" → funcionando ✅
```

### Verificar no Python:

```python
import requests

r = requests.get(
    "https://api.automabothub.com/v1/health",
    headers={"Authorization": "Bearer fg_live_SEU_TOKEN"}
)
assert r.status_code == 200
assert r.json()["status"] == "ok"
print("✅ API funcionando!")

# Verificar seus limites
r = requests.get(
    "https://api.automabothub.com/v1/usage",
    headers={"Authorization": "Bearer fg_live_SEU_TOKEN"}
)
uso = r.json()
print(f"Plano: {uso['plan']}")
print(f"Usado: {uso['events_used_this_month']:,} / {uso['events_limit']:,}")
print(f"Percentual: {uso['pct_used']*100:.1f}%")
```

---

## 6. Integração com Ferramentas Populares

### Google Colab (sem instalar nada):
```python
# Direto no Colab — sem pip install, sem Docker
!pip install requests pandas pyarrow  # já vem instalado no Colab

import requests, pandas as pd

resp = requests.post("https://api.automabothub.com/v1/generate",
    headers={"Authorization": "Bearer fg_live_xxx"},
    json={"type":"transactions","count":10000,"format":"parquet"})

# [... aguardar e baixar conforme seção 3.2 ...]

df = pd.read_parquet(download_url)
df["fraud_type"].value_counts().plot(kind="bar")
```

### Apache Spark:
```python
spark.read.parquet(download_url).createOrReplaceTempView("transacoes")
spark.sql("SELECT fraud_type, COUNT(*) FROM transacoes GROUP BY fraud_type").show()
```

### dbt / SQL:
```bash
# Baixar como CSV e importar no seu banco
wget -O transacoes.csv "https://storage.automabothub.com/.../result.csv?token=..."
psql -d meu_banco -c "\copy transacoes FROM 'transacoes.csv' CSV HEADER"
```

---

## 7. Diagrama de Status de Jobs

```
  [POST /v1/generate]
          │
          ▼
       "queued"  ←─── (na fila, aguardando worker livre)
          │
          ▼
       "running" ←─── (worker processando, pode levar segundos/minutos)
          │
     ┌────┴────┐
     ▼         ▼
   "done"   "failed"
     │
     ▼
  download_url disponível (expira em 24h)
     │
     ▼
  after 24h: "expired" (arquivo deletado — baixe antes!)
```

---

## 8. Dicas e Boas Práticas

```
✅ Use seed fixo (ex: seed: 42) para resultados reprodutíveis
   → Dois jobs com mesmo seed + mesmos parâmetros = arquivos idênticos

✅ Para datasets grandes, use format: "parquet"
   → ~5x menor que CSV, ~10x menor que JSONL para mesmos dados

✅ Faça poll a cada 2-5 segundos (não por segundo)
   → Evita rate limiting desnecessário

✅ Baixe o arquivo logo após ficar pronto
   → URLs expiram em 24 horas

✅ Para CI/CD, guarde um seed fixo no pipeline
   → Garante dados de teste determinísticos entre builds

⚠️  Não compartilhe sua API key em repos públicos
   → Revogue em automabothub.com/dashboard se exposta

⚠️  Jobs que falham não consomem cota
   → Apenas jobs "done" descontam do seu limite mensal
```

---

*Fim dos documentos de pesquisa. Ver 01-04 para análise completa do mercado.*
