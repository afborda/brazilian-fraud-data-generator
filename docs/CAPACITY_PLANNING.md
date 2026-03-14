# Capacity Planning: VPS × Planos × Usuários Concorrentes

**Data:** 2026-03-05  
**Versão:** 4.1.0 (guaraná) — com otimizações RAM + multiprocessing  
**Benchmark real:** máquina 18 cores (dev), projetado para VPS 4-24 cores  

---

## 1. Otimização RAM Implementada (OTIMIZAÇÃO 3)

### O que é
Ao invés de chamar `random.choices()`, `random.uniform()`, `hashlib.sha256()` individualmente para **cada evento**, pré-geramos **10.000 valores de uma vez** em arrays na RAM e consumimos sequencialmente.

### Como funciona
```
┌─ Abordagem ANTERIOR ────────────────────────────────────┐
│  Para cada evento:                                       │
│    random.choices(lista, weights)  → 3µs overhead Python │
│    random.randint(0,255) × 3      → 1.5µs               │
│    hashlib.sha256()               → 2µs                  │
│    string concatenation           → 4µs                  │
│  Total overhead: ~10µs/evento                            │
└──────────────────────────────────────────────────────────┘

┌─ Abordagem NOVA (PrecomputeBuffers) ────────────────────┐
│  A cada 10.000 eventos:                                  │
│    os.urandom(80KB)               → 0.1ms (uma vez)      │
│    [rng.random() for _ in 10000]  → 0.3ms (uma vez)      │
│    bulk IP formatting             → 1ms (uma vez)        │
│                                                          │
│  Para cada evento:                                       │
│    buf._data[buf._pos]; buf._pos += 1  → ~0.05µs        │
│                                                          │
│  Overhead real: ~0.5µs/evento (20x menos)                │
└──────────────────────────────────────────────────────────┘
```

### Resultado medido
| Métrica | Antes | Depois | Ganho |
|---------|-------|--------|-------|
| TX single-process | 35.000 evt/s | **52.000 evt/s** | **+49%** |
| TX 8 workers | 123.000 evt/s | **173.000 evt/s** | **+40%** |
| TX 16 workers | 197.000 evt/s | **195.000 evt/s** | ~igual (queue-bound) |
| Rides single-process | 53.000 evt/s | **52.000 evt/s** | ~igual (rides são IO-heavier) |
| Rides 16 workers | 220.000 evt/s | **207.000 evt/s** | ~igual |

### Memória adicional usada
| Buffer | Tamanho | Uso |
|--------|---------|-----|
| 10K IPs | ~200 KB | Endereços BR pré-formatados |
| 10K hashes (16 char) | ~160 KB | Card hashes |
| 10K hashes (32 char) | ~320 KB | PIX keys |
| 10K floats | ~80 KB | Decisões aleatórias |
| 10K merchant IDs | ~150 KB | "MERCH_XXXXXX" |
| Weighted choice buffers | ~100 KB | Status, profiles |
| **TOTAL** | **~1 MB** por worker | **Negligível** vs 8-96 GB RAM |

---

## 2. Specs dos VPS

| VPS | vCores | RAM | SSD | Bandwidth | Preço |
|-----|--------|-----|-----|-----------|-------|
| VPS-1 | 4 | 8 GB | 75 GB SSD | 400 Mbps | $6,46/mês |
| VPS-2 | 6 | 12 GB | 100 GB NVMe | 1 Gbps | $9,99/mês |
| VPS-3 | 8 | 24 GB | 200 GB NVMe | 1.5 Gbps | $19,97/mês |
| VPS-4 | 12 | 48 GB | 300 GB NVMe | 2 Gbps | $36,98/mês |
| VPS-5 | 16 | 64 GB | 350 GB NVMe | 2.5 Gbps | $54,82/mês |
| VPS-6 | 24 | 96 GB | 400 GB NVMe | 3 Gbps | $73,10/mês |

---

## 3. Throughput Estimado por VPS

Baseado nos benchmarks reais, projetado para VPS (single-user, 100% CPU):

| VPS | Workers recomendados | TX/s estimado | Rides/s estimado |
|-----|---------------------|---------------|------------------|
| VPS-1 (4 cores) | 3 (1 para API) | ~40.000 | ~35.000 |
| VPS-2 (6 cores) | 5 | ~70.000 | ~60.000 |
| VPS-3 (8 cores) | 7 | ~130.000 | ~85.000 |
| VPS-4 (12 cores) | 10 | ~170.000 | ~150.000 |
| VPS-5 (16 cores) | 14 | ~195.000 | ~200.000 |
| VPS-6 (24 cores) | 20 | ~250.000+ | ~250.000+ |

> **Nota:** Reservamos 1 core para o FastAPI + sistema. VPS com hyperthreading pode dar mais.

---

## 4. Planos e Limites (alinhado código + modelo de negócio)

### 5 Planos (implementado em `limits.py`):

| Plano | Preço | Eventos/mês | Trial | Concurrent | Formatos | Targets |
|-------|-------|------------|-------|------------|----------|--------|
| FREE | R$ 0 | **5K** | **30 dias** | 1 | JSONL | stdout |
| STARTER | R$ 49/mês | 5M | permanente | 3 | jsonl, csv, parquet, json | stdout, webhook |
| PRO | R$ 149/mês | 100M | permanente | 10 | todos | stdout, kafka, webhook |
| TEAM | R$ 399/mês | ilimitado | permanente | ilimitado | todos | todos |
| ENTERPRISE | consulta | ilimitado | permanente | ilimitado | todos | todos |

### Rate Limiting por Plano (controlado pela API, não pelo usuário):

| Plano | req/s | req/min | Max eventos/request | Burst |
|-------|-------|---------|--------------------|---------| 
| FREE | 0.5 (1 a cada 2s) | 10 | 1.000 | sem burst |
| STARTER | 5 | 120 | 100.000 | 2x por 10s |
| PRO | 20 | 600 | 1.000.000 | 3x por 10s |
| TEAM | 50 | 1.500 | ilimitado | 5x |
| ENTERPRISE | ilimitado | ilimitado | ilimitado | ilimitado |

> **Rate limiting é controlado POR NÓS na API**, não pelo usuário.
> Cada license key tem um token-bucket que limita automaticamente.
> O usuário pode fazer requests até atingir seu limite — depois recebe HTTP 429.

---

## 5. Como funcionaria com 30 usuários simultâneos

### Cenário: "30 usuários simultaneos buscando dados, divididos em todos os níveis iniciais"

Distribuição hipotética (mix inicial realista):

| Plano | Qtd | Concurrent max cada | Total slots concurrent |
|-------|-----|--------------------|-----------------------|
| FREE | 15 | 1 | 15 |
| STARTER | 10 | 3 | 30 |
| PRO | 4 | 10 | 40 |
| TEAM | 1 | ilimitado | ~10 (auto-limitado) |
| **TOTAL** | **30** | — | **~95 slots possíveis** |

Mas na prática **30 usuários simultâneos NÃO significa 95 jobs simultâneos**. FREE tem trial de 30 dias — após isso, precisa fazer upgrade. Aqui está como funciona:

### 5.1 Modelo de Execução via Hosted API

```
┌─ Usuário (browser / curl / SDK) ─────────────────────────┐
│  POST /v1/generate                                        │
│  {                                                        │
│    "type": "transactions",                                │
│    "count": 100000,                                       │
│    "format": "jsonl",                                     │
│    "fraud_rate": 0.05                                     │
│  }                                                        │
└─────────────────────┬─────────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─ FastAPI no VPS ──────────────────────────────────────────┐
│  1. Valida licença (HMAC)                                 │
│  2. Verifica limites (eventos/mês, concurrent)            │
│  3. Coloca job na fila (Redis / asyncio.Queue)            │
│  4. Retorna job_id + ETA                                  │
└─────────────────────┬─────────────────────────────────────┘
                      │
                      ▼
┌─ Worker Pool ─────────────────────────────────────────────┐
│  N workers processando jobs da fila                       │
│  Cada job: gera dados → salva temporário → retorna URL    │
│                                                           │
│  Jobs pequenos (<10K): inline (resposta imediata)         │
│  Jobs médios (10K-1M): background + polling               │
│  Jobs grande (>1M): background + webhook callback         │
└───────────────────────────────────────────────────────────┘
```

### 5.2 Capacidade Real por VPS com 30 Usuários

Assumindo:
- Job médio FREE = 10K eventos (burst rápido)
- Job médio STARTER = 100K eventos
- Job médio PRO = 500K eventos
- Job médio TEAM = 2M eventos
- **Fator de concorrência real:** nem todos pedem ao mesmo tempo. ~50% idle em qualquer momento.

| VPS | Max concurrent jobs | Tempo médio/job (100K evt) | Jobs/hora | Custo/job |
|-----|--------------------|-----------------------------|-----------|-----------|
| VPS-1 (4c) | 2-3 jobs | ~2.5s | ~1.440 | $0.0001 |
| VPS-2 (6c) | 3-4 jobs | ~1.4s | ~2.880 | $0.0001 |
| **VPS-3 (8c)** | **4-5 jobs** | **~0.8s** | **~5.000** | **$0.00005** |
| VPS-4 (12c) | 6-8 jobs | ~0.6s | ~10.000 | $0.00004 |
| VPS-5 (16c) | 8-12 jobs | ~0.5s | ~15.000 | $0.00004 |
| VPS-6 (24c) | 12-18 jobs | ~0.4s | ~25.000 | $0.00003 |

### 5.3 Cenário Detalhado: 30 Usuários no VPS-3 ($19,97/mês)

```
VPS-3: 8 vCores, 24 GB RAM, 200 GB NVMe

Alocação de recursos:
├── 1 core: FastAPI + nginx + redis
├── 7 cores: Worker pool para geração
│
│   RAM:
│   ├── FastAPI + Redis: ~500 MB
│   ├── 5 jobs concurrent × ~100 MB cada: ~500 MB  
│   ├── PrecomputeBuffers: ~1 MB × 5 workers: ~5 MB
│   ├── OS + buffers: ~2 GB
│   └── LIVRE: ~21 GB (amplo headroom)
│
│   Assumindo 30 users ativos total:
│   ├── 15 FREE (trial 30d): 5K evt/mês cada = 75K evt/mês total
│   │   → Demanda: ~75K / 30 dias = 2.5K evt/dia
│   │   → Tempo: 2.5K ÷ 130K evt/s = 0.02s/dia (negligível)
│   │   → Rate limit: 0.5 req/s, 10 req/min, max 1K evt/req
│   │
│   ├── 10 STARTER: 5M evt/mês cada = 50M evt/mês total
│   │   → Demanda: 50M / 30 dias = 1.67M evt/dia
│   │   → Tempo: 1.67M ÷ 130K evt/s = 12.8s/dia
│   │   → Rate limit: 5 req/s, 120 req/min, max 100K evt/req
│   │
│   ├── 4 PRO: 100M evt/mês cada = 400M evt/mês total
│   │   → Demanda: 400M / 30 dias = 13.3M evt/dia
│   │   → Tempo: 13.3M ÷ 130K evt/s = 102s/dia (~1.7min)
│   │   → Rate limit: 20 req/s, 600 req/min, max 1M evt/req
│   │
│   └── 1 TEAM: ilimitado, assume 500M evt/mês
│       → Demanda: 500M / 30 = 16.7M evt/dia
│       → Tempo: 16.7M ÷ 130K evt/s = 128s/dia (~2.1min)
│       → Rate limit: 50 req/s, sem teto de eventos
│
│   TOTAL CPU DIÁRIO: ~243 segundos = ~4 minutos de geração
│   UTILIZAÇÃO CPU: 4 min / 1.440 min dia = 0.28%
│
│   STORAGE:
│   ├── Evento médio: ~500 bytes (JSONL)
│   ├── 31.7M evt/dia × 500B = ~15.8 GB/dia
│   ├── Temp files (delete after download): ~0 GB residual
│   └── Se guardar 3 dias: ~47 GB (cabe nos 200 GB NVMe)
│
│   REDE:  
│   ├── 15.8 GB/dia = ~1.5 Mbps sustentado
│   ├── VPS-3 tem 1.5 Gbps → usa 0.1% da banda
│   └── Download de 10 GB em burst: 10GB ÷ 1.5Gbps = ~53s
│
│   CONCLUSÃO VPS-3:
│   ✅ CPU: usa 0.28% do dia — FOLGA GIGANTE
│   ✅ RAM: usa 3 GB de 24 GB — sobra 21 GB
│   ✅ Disco: 47 GB de 200 GB — OK
│   ✅ Rede: 0.1% da banda — OK
│   ⚡ Pode suportar 10x mais usuários facilmente
```

### 5.4 Pior Caso: 30 Usuários fazendo requests SIMULTÂNEOS

```
Se TODOS os 30 pedem ao MESMO INSTANTE:

VPS-1 (4 cores):
  → Fila: 2-3 jobs parallel, 27 na fila
  → Job médio 100K: 2.5s cada
  → Tempo para limpar fila: ~30 × 2.5s ÷ 3 = 25s espera
  → 30 users: último user espera ~25s ❌ (ruim para UX)

VPS-2 (6 cores):
  → Fila: 4 jobs parallel, 26 na fila
  → Tempo: ~30 × 1.4s ÷ 4 = 10.5s espera ⚠️

VPS-3 (8 cores):
  → Fila: 5 jobs parallel
  → Tempo: ~30 × 0.8s ÷ 5 = 4.8s espera ✅

VPS-4 (12 cores):
  → Fila: 8 jobs parallel
  → Tempo: ~30 × 0.6s ÷ 8 = 2.3s espera ✅✅

VPS-5 (16 cores):
  → Fila: 12 jobs parallel
  → Tempo: ~30 × 0.5s ÷ 12 = 1.3s espera ✅✅✅

VPS-6 (24 cores):
  → Fila: 18 jobs parallel
  → Tempo: ~30 × 0.4s ÷ 18 = 0.7s espera ✅✅✅✅
```

---

## 6. Recomendação: Qual VPS para Cada Fase

### Fase Inicial (0-30 clientes): VPS-1 ou VPS-2
```
VPS-1 ($6,46/mês):
  ✅ Suficiente para 30 users FREE + até 5 STARTER
  ✅ Break-even: 1 STARTER (R$49) > $6,46
  ⚠️ Pico de 30 requests simultâneos: ~25s de espera
  
VPS-2 ($9,99/mês):  ← RECOMENDADO fase inicial
  ✅ 30 users com mix FREE/STARTER/PRO
  ✅ Pico: ~10s espera (aceitável)
  ✅ 12 GB RAM para jobs maiores
  ✅ NVMe (2-3x mais rápido para I/O que SSD normal)
```

### Crescimento (30-100 clientes): VPS-3
```
VPS-3 ($19,97/mês):
  ✅ 8 cores para paralelismo real
  ✅ 24 GB RAM — jobs de 10 GB+ sem problema
  ✅ Pico 30 simultâneos: ~5s espera
  ✅ Pode atender 100+ users diários
```

### Escala (100-500 clientes): VPS-4 ou VPS-5
```
VPS-4 ($36,98/mês):
  ✅ 12 cores, 48 GB RAM
  ✅ Jobs enterprise (Parquet 50 GB)
  ✅ 100 concurrent no pico: ~8s espera

VPS-5 ($54,82/mês):
  ✅ 16 cores, 64 GB RAM  
  ✅ Dataset gigantes (TB-scale com streaming)
  ✅ 100 concurrent no pico: ~4s espera
```

### Enterprise (500+ clientes): VPS-6 ou clustered
```
VPS-6 ($73,10/mês):
  ✅ 24 cores, 96 GB RAM
  ✅ ~250K evt/s = ~20 GB/minuto
  ✅ Pode gerar 1 TB em ~50 minutos
```

---

## 7. Resumo: Tabela de Decisão Rápida

| Pergunta | Resposta |
|----------|---------|
| **"Tenho R$50/mês de budget, dá?"** | VPS-2 ($10) + domínio ($1) = R$66. Dá de sobra. |
| **"30 users FREE vão saturar?"** | Não. 30×5K = 150K evt/mês = <1 segundo de CPU/dia. FREE expira em 30 dias. |
| **"E se 30 pedem ao mesmo tempo?"** | VPS-2: ~10s espera. VPS-3: ~5s. Aceitável para API. |
| **"Quando upgrade para VPS-3?"** | Quando tiver >5 PRO ou latência média >5s. |
| **"RAM importa?"** | Para geração: não (usa ~1 MB por worker). Para jobs grandes em memória (Parquet): sim, 24+ GB ajuda. |
| **"Disco importa?"** | Só se armazenar datasets. Se for stream → download → delete, 75 GB do VPS-1 basta. |
| **"Dá para usar RAM para ir mais rápido?"** | ✅ Sim! Implementamos PrecomputeBuffers: +49% single-process, ~costless (~1 MB RAM). |
| **"Rate limit é controlado por quem?"** | **Por NÓS na API.** Token-bucket por license key. User recebe HTTP 429 ao exceder. |

---

## 8. Arquitetura da API para Concorrência

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Server                           │
│                                                                 │
│  POST /v1/generate  ──┐                                        │
│  POST /v1/stream    ──┤                                        │
│  GET  /v1/job/{id}  ──┤                                        │
│  GET  /v1/download  ──┘                                        │
│                                                                 │
│  ┌─── Rate Limiter (per license key) ───────────────────────────┐  │
│  │ FREE:    0.5 req/s, 10 req/min, max 1K evt/req, 30-day trial │  │
│  │ STARTER: 5 req/s, 120 req/min, max 100K evt/req              │  │
│  │ PRO:     20 req/s, 600 req/min, max 1M evt/req               │  │
│  │ TEAM:    50 req/s, 1500 req/min, unlimited evt/req            │  │
│  │ ENTERPRISE: unlimited (fair-use policy)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── Job Queue (Redis) ────────────────────────────────────┐  │
│  │  priority=0: TEAM/ENTERPRISE (processed first)           │  │
│  │  priority=1: PRO                                         │  │
│  │  priority=2: STARTER                                     │  │
│  │  priority=3: FREE (best-effort)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── Worker Pool ──────────────────────────────────────────┐  │
│  │  Workers=N_CORES-1: consomem jobs da fila                │  │
│  │  Cada worker: ParallelStreamManager(workers=1) interno   │  │
│  │  Resultado: /tmp/job_{id}.jsonl → download via URL       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Para 30 users simultâneos no VPS-3:
  ┌ FastAPI (1 core) ──────────────────────┐
  │  uvicorn --workers 2 (ASGI)            │
  │  Aceita 30 requests instantaneamente   │
  │  Coloca na fila, retorna job_id        │
  └────────────────────────────────────────┘
  ┌ Workers (7 cores) ─────────────────────┐
  │  7 slots processando jobs paralelos    │
  │  Job FREE 50K:   ~1s    → rapido       │
  │  Job STARTER 1M: ~20s   → background   │
  │  Job PRO 10M:    ~200s  → background   │
  └────────────────────────────────────────┘
```

### Fluxo para cada tipo de usuário:

**FREE (5K/mês, 1 concurrent, trial 30 dias):**
```
1. POST /v1/generate → body: {count: 1000}  (max 1K por request)
2. Server: valida license, verifica trial não expirou, 5K/mês restante
3. Rate limiter: 0.5 req/s → se fez request há <2s → HTTP 429
4. Geração inline (~0.02s), resposta imediata com JSONL
5. Após 30 dias: license.is_expired = True → HTTP 403 "Trial expired"
```

**STARTER (5M/mês, 3 concurrent):**
```
1. POST /v1/generate → body: {count: 100000, format: "parquet"}
   Rate limit: 5 req/s → burst 2x por 10s → OK
2. Server: cria job_id, enqueue com priority=2
3. Resposta: {job_id: "xyz", status: "queued", eta: "12s"}
4. Client: GET /v1/job/xyz → {status: "running", progress: 45%}
5. Client: GET /v1/job/xyz → {status: "done", download_url: "/v1/download/xyz"}
6. Client: GET /v1/download/xyz → arquivo parquet
7. Server: delete /tmp/job_xyz.parquet após 1h
```

**PRO (100M/mês, 10 concurrent):**
```
Mesmo fluxo do STARTER, mas:
- Até 10 jobs simultâneos
- Priority maior na fila  
- 20 req/s (burst 3x por 10s)
- Kafka e webhook desbloqueados
- Webhook callback quando pronto (opcional)
- API key management multi-env
```

**TEAM (ilimitado):**
```
Mesmo fluxo, mas:
- Sem limite de eventos
- Priority máxima
- 50 req/s (burst 5x)
- Worker dedicado (se VPS-4+)
- Dashboard de uso da equipe
```
