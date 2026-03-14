# 🏗️ Capacidade da API e Escalabilidade
> Baseado em benchmark real rodado em 04/03/2026
> Ambiente: local machine, seed 42, 5% fraud rate, pool 200 customers + 100 drivers

---

## 1. Resultados do Benchmark Real

### 1.1 Velocidade de Geração

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    BENCHMARK RESULTS — BFDG v4.1.0                            │
│                    (benchmarks/streaming_benchmark.py)                         │
├────────────┬───────────────────────────────────┬──────────────────────────────┤
│            │         TRANSACTIONS               │          RIDES               │
│  Nível     ├──────────┬──────────┬─────────────┼──────────┬────────┬──────────┤
│            │ ev/s real│ µs/evento│ bytes/evento │ ev/s real│µs/evto │bytes/evt │
├────────────┼──────────┼──────────┼─────────────┼──────────┼────────┼──────────┤
│   10/s     │  6.213   │   96 µs  │   1.025 B   │  4.728   │ 132 µs │  1.071 B │
│  100/s     │  6.170   │   97 µs  │   1.025 B   │  4.795   │ 128 µs │  1.071 B │
│  500/s     │  6.768   │   86 µs  │   1.025 B   │  4.978   │ 124 µs │  1.071 B │
│ 1.000/s    │  6.706   │   87 µs  │   1.024 B   │  5.116   │ 121 µs │  1.071 B │
│ 5.000/s    │  6.512   │   90 µs  │   1.024 B   │  5.044   │ 122 µs │  1.071 B │
└────────────┴──────────┴──────────┴─────────────┴──────────┴────────┴──────────┘

CONCLUSÃO: Um único processo Python gera:
  • Transações: ~6.500 eventos/segundo (teto do GIL)
  • Corridas:   ~5.000 eventos/segundo (mais cálculo Haversine)
```

### 1.2 Memória

```
┌───────────────────────────────────────────────────────────┐
│ CONSUMO DE MEMÓRIA (RSS)                                  │
├───────────────────────────────────────────────────────────┤
│ Base (Python + imports)          │  115 MB               │
│ Pool: 200 customers + 100 drivers│  +0.7 MB              │
│ 10K sessões em memória           │  +5 MB                │
│ TOTAL processo único             │  ~121 MB              │
│                                  │                       │
│ Cada worker adicional:           │  +121 MB (processo py)│
└───────────────────────────────────────────────────────────┘
```

---

## 2. Projeções por VPS

### 2.1 Tabela de VPS (preços de referência, mar/2026)

```
┌──────┬──────────────┬─────────┬───────────┬─────────────────────────────────────┐
│ VPS  │ Custo/mês    │ vCPUs   │ RAM       │ Provedor (referência)               │
├──────┼──────────────┼─────────┼───────────┼─────────────────────────────────────┤
│ VPS-1│ $6,46/mês    │ 2 vCPU  │  8 GB RAM │ Hetzner CX21 / DigitalOcean $6     │
│ VPS-2│ $9,99/mês    │ 4 vCPU  │ 12 GB RAM │ Hetzner CX31 / DigitalOcean $12    │
│ VPS-3│ $19,97/mês   │ 8 vCPU  │ 24 GB RAM │ Hetzner CX41 / DigitalOcean $24    │
│      │              │         │           │ (em BRL: R$ 39 / R$ 60 / R$ 120)   │
└──────┴──────────────┴─────────┴───────────┴─────────────────────────────────────┘
```

### 2.2 Capacidade Sustentável (70% do pico, evitando overload)

```
┌──────┬────────────────────────────────────────────────────────────────────────┐
│ VPS  │ CAPACIDADE SUSTENTÁVEL                                                  │
│      │ (70% de (vCPUs × 6.500 TX/s ou 5.000 rides/s))                        │
├──────┼────────────────────────────────────────────────────────────────────────┤
│ VPS-1│ 2 vCPU × 6.500 × 70% =  9.100 TX/s    │  7.000 rides/s               │
│ VPS-2│ 4 vCPU × 6.500 × 70% = 18.200 TX/s    │ 14.000 rides/s               │
│ VPS-3│ 8 vCPU × 6.500 × 70% = 36.400 TX/s    │ 28.000 rides/s               │
└──────┴────────────────────────────────────────────────────────────────────────┘

NOTA: Em Python, o GIL impede true multi-threading.
  → Para escalar: rodar N processos Python paralelos (1 por vCPU)
  → Cada processo = ~121 MB RAM
  → VPS-1 (8GB): max ~60 processos por memória, mas 2 vCPUs = 2 produtivos
```

### 2.3 Diagrama: Capacidade vs Usuários Simultâneos (Hosted API)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   QUANTO A API AGUENTARIA SIMULTANEAMENTE                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  VPS-1 ($6,46/mês = R$ 39/mês):                                             ║
║                                                                              ║
║  [User 1] ─┐                                                                ║
║  [User 2] ─┼──► [FastAPI] ──► [Job Queue] ──► [Worker 1] ──► MinIO         ║
║  [User 3] ─┤                                                                ║
║  [User 4] ─┘                               ──► [Worker 2] ──► MinIO         ║
║                                                                              ║
║  Cenário A: Todos pedem 10K registros (pequeno)                             ║
║    Tempo de geração: 10.000 ÷ 6.500/s = 1.5 segundos por job               ║
║    → 2 workers → 2 jobs paralelos                                           ║
║    → 120 jobs/minuto processados                                            ║
║    → Aguentaria ~60 usuários simultâneos enviando 1 job/minuto              ║
║                                                                              ║
║  Cenário B: Pedidos de 1M registros (grande)                                ║
║    Tempo de geração: 1.000.000 ÷ 6.500/s = 154 segundos (~2.5 min)         ║
║    → 2 workers → job grande "ocupa" o worker                                ║
║    → Adequado para 20-30 usuários com jobs assíncronos                     ║
║    → Fila cresce se muitos usuários simultâneos                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Throughput por Plano de Assinatura

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     RELAÇÃO: PLANO × THROUGHPUT GERADO                      │
├──────────────┬────────────────┬────────────────────┬─────────────────────────┤
│ Plano BFDG   │ Eventos/mês    │ Tempo de geração   │ Custo por evento (R$)  │
├──────────────┼────────────────┼────────────────────┼─────────────────────────┤
│ FREE         │ 50.000         │ ~8 segundos        │ R$ 0,00 (gratuito)     │
│ Starter R$49 │ 5.000.000      │ ~13 minutos        │ R$ 0,0000098 (~R$0/ev) │
│ Pro R$149    │ 100.000.000    │ ~4,3 horas         │ R$ 0,0000015 (~R$0/ev) │
│ Team R$399   │ ilimitado      │ ilimitado          │ R$ 0 marginal          │
└──────────────┴────────────────┴────────────────────┴─────────────────────────┘

Para o PRO: 100M eventos ÷ 6.500/s ÷ 3600s = ~4,3 horas de CPU
  → VPS-1 = $6,46 ÷ (4,3h ÷ 744h/mês) = ~$0,037 de custo de CPU
  → Margem bruta: R$ 149 receita − R$ 0,22 custo de CPU = R$ 148,78 (99.8% margem)
```

---

## 4. Diagrama: Arquitetura da Hosted API

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ARQUITETURA HOSTED API (v5.0.0 planejado)               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   USUÁRIO                        NOSSA INFRAESTRUTURA                       ║
║   ───────                        ──────────────────────────────────────────║
║                                                                              ║
║   curl / requests                [Traefik] (HTTPS termination)              ║
║   Python SDK      ──────────►    [FastAPI] POST /v1/generate                ║
║   Google Colab                        │                                     ║
║   Jupyter                             │ 1. valida API key                   ║
║                                       │ 2. verifica limite do plano         ║
║                                       │ 3. enfileira job (SQLite/Redis)     ║
║                                       │ 4. retorna job_id imediatamente     ║
║                                       ▼                                     ║
║   [polling GET /v1/jobs/id]    [Worker Pool]                                ║
║           │                       │   │                                     ║
║           │                Worker-1   Worker-2  ...Worker-N                 ║
║           │               (generate.py subprocess)                          ║
║           │                       │                                         ║
║           │                       ▼                                         ║
║           │                  [MinIO / S3]                                   ║
║           │               (armazenamento temporário)                        ║
║           │                       │                                         ║
║           │              gera URL assinada (expira 24h)                     ║
║           │                       │                                         ║
║           └──────── download_url ◄┘                                        ║
║                                                                              ║
║   wget/curl → arquivo .parquet/.csv/.jsonl pronto para uso                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. Escalabilidade Horizontal

```
COMO ESCALAR QUANDO CRESCER:

  Fase 1 (0-100 usuários): 1 VPS-1 ($6,46/mês)
  ├── FastAPI + SQLite
  ├── 2 workers Python (1 por vCPU)
  └── MinIO local

  Fase 2 (100-1.000 usuários): 1 VPS-2 ($9,99/mês)
  ├── FastAPI + PostgreSQL
  ├── 4 workers Python
  └── MinIO local ou S3 (AWS/Cloudflare R2)

  Fase 3 (1.000-10.000 usuários): VPS-3 + CDN
  ├── FastAPI + PostgreSQL (managed)
  ├── 8+ workers Python
  ├── Redis para filas
  └── Cloudflare R2 (saída gratuita)

  Fase 4 (10.000+ usuários): cluster
  ├── Kubernetes / Docker Swarm
  ├── N pods worker
  └── Auto-scaling por fila de jobs
```

---

## 6. Limitador: Python GIL

```
                PYTHON GIL — POR QUE É O GARGALO

  ┌─────────────────────────────────────────────────────────┐
  │  GIL (Global Interpreter Lock) = apenas 1 thread Python │
  │  executa código Python simultaneamente por processo      │
  │                                                         │
  │  IMPACTO: adicionar threads NÃO acelera geração         │
  │           adicionar PROCESSOS sim (subprocess / fork)   │
  │                                                         │
  │  SOLUÇÃO NOSSA:                                         │
  │    • Batch: --workers N → N processos paralelos         │
  │    • API: N workers como subprocessos Python            │
  │    • Streaming: N instâncias stream.py paralelas         │
  │      (1 por Kafka partition)                            │
  └─────────────────────────────────────────────────────────┘

  BANDWIDTH: NUNCA é o gargalo
    • 6.500 TX/s × 1.024 B = 6,6 MB/s = 53 Mbps
    • VPS-1 típico: 200-1000 Mbps uplink
    • Margem de 4-19x → CPU sempre esgota primeiro
```

---

## 7. SLAs Razoáveis para Hosted API

```
┌───────────────────────────────────────────────────────────────┐
│              SLA PROPOSTO (meta inicial — VPS-1)              │
├───────────────────────────────────────────────────────────────┤
│ Latência de enfileiramento (POST /v1/generate):  < 200 ms     │
│ Jobs pequenos (≤ 100K eventos):                  < 30 s      │
│ Jobs médios (100K–1M eventos):                   < 5 min     │
│ Jobs grandes (1M–10M eventos):                   < 30 min    │
│ Downloads disponíveis por:                       24 horas    │
│ Uptime target:                                   99%         │
│ Concorrência máxima (VPS-1, 2 workers):          2 jobs      │
└───────────────────────────────────────────────────────────────┘
```

---

*Ver 04_MODELO_NEGOCIO.md para estratégia de pricing e projeção de receita*
