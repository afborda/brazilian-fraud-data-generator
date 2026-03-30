# Análise de Separação: Tier Gratuito vs Pago — synthfin-data

> **Data**: 2026-03-25  
> **Versão de referência**: v4.9.1  
> **Objetivo**: Definir a estratégia de monetização separando funcionalidades gratuitas e pagas

---

## 1. Visão Geral da Estratégia

O modelo recomendado é **Open Core**: o motor de geração permanece aberto para estudo/pesquisa, enquanto funcionalidades premium (escala, integração enterprise, campos avançados, suporte) são exclusivas da API hospedada ou licenças comerciais.

```
┌─────────────────────────────────────────────────────────┐
│                    synthfin-data                         │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │   GRATUITO (Estudo)  │  │   PAGO (Comercial/API)   │ │
│  │                      │  │                          │ │
│  │  • CLI completo      │  │  • API REST hospedada    │ │
│  │  • Todos os geradores│  │  • Campos biométricos    │ │
│  │  • Formatos básicos  │  │  • Enrichers avançados   │ │
│  │  • Fraudes padrão    │  │  • RAG calibração custom │ │
│  │  • Sem limite escala │  │  • Suporte técnico       │ │
│  │  • Sem uso comercial │  │  • SLA + uptime          │ │
│  └──────────────────────┘  │  • Streaming managed     │ │
│                            │  • Multi-tenant           │ │
│                            └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Matriz de Funcionalidades por Tier

### 2.1 Geração de Dados

| Funcionalidade | FREE (Estudo) | STARTER | PRO | TEAM | ENTERPRISE |
|---|:---:|:---:|:---:|:---:|:---:|
| Transações bancárias | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rides (ride-share) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Modo `--type all` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Seed determinístico | ✅ | ✅ | ✅ | ✅ | ✅ |
| Perfis comportamentais (7) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Custom date ranges | ✅ | ✅ | ✅ | ✅ | ✅ |
| Perfis customizáveis (arquivo) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Calibração RAG personalizada | ❌ | ❌ | ❌ | ✅ | ✅ |
| Geração via API REST | ❌ | ✅ | ✅ | ✅ | ✅ |

### 2.2 Fraude e Scoring

| Funcionalidade | FREE | STARTER | PRO | TEAM | ENTERPRISE |
|---|:---:|:---:|:---:|:---:|:---:|
| 25 tipos de fraude bancária | ✅ | ✅ | ✅ | ✅ | ✅ |
| 11 tipos de fraude ride-share | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraud_risk_score (17 sinais) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Campos BACEN PIX (12 campos) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fraud Rings | ✅ | ✅ | ✅ | ✅ | ✅ |
| Biometria (10 campos) | ❌ null | ❌ null | ✅ real | ✅ real | ✅ real |
| Velocity windows estendidos | Básico (24h) | Básico | Completo (1h-30d) | Completo | Completo |
| Geo clustering avançado | ❌ | ❌ | ✅ | ✅ | ✅ |
| Fraude sequencial (velocity check) | ❌ | ❌ | ❌ | ✅ | ✅ |

### 2.3 Formatos de Output

| Formato | FREE | STARTER | PRO | TEAM | ENTERPRISE |
|---|:---:|:---:|:---:|:---:|:---:|
| JSONL | ✅ | ✅ | ✅ | ✅ | ✅ |
| CSV | ✅ | ✅ | ✅ | ✅ | ✅ |
| JSON Array | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parquet | ✅ | ✅ | ✅ | ✅ | ✅ |
| TSV | ✅ | ❌ | ❌ | ✅ | ✅ |
| Arrow IPC | ✅ | ❌ | ✅ | ✅ | ✅ |
| Database (SQLAlchemy) | ✅ | ❌ | ✅ | ✅ | ✅ |
| MinIO/S3 | ✅ | ❌ | ✅ | ✅ | ✅ |
| Compressão (gzip/zstd/snappy) | ✅ | ✅ | ✅ | ✅ | ✅ |

### 2.4 Escala e Performance

| Limite | FREE (Estudo) | STARTER | PRO | TEAM | ENTERPRISE |
|---|:---:|:---:|:---:|:---:|:---:|
| CLI local (sem limite) | ✅ | ✅ | ✅ | ✅ | ✅ |
| API: eventos/mês | — | 5M | 100M | ilimitado | ilimitado |
| API: processos concorrentes | — | 3 | 10 | ilimitado | ilimitado |
| API: output máximo (GB) | — | 5.0 | 20.0 | ilimitado | ilimitado |
| API: req/segundo | — | 5 | 20 | 50 | ilimitado |
| API: eventos/request | — | 100K | 1M | ilimitado | ilimitado |

### 2.5 Streaming

| Funcionalidade | FREE | STARTER | PRO | TEAM | ENTERPRISE |
|---|:---:|:---:|:---:|:---:|:---:|
| stdout | ✅ | ✅ | ✅ | ✅ | ✅ |
| Kafka (local) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Webhook (local) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Kafka managed (via API) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Streaming multiprocessing | ✅ | ✅ | ✅ | ✅ | ✅ |

### 2.6 Suporte e Infraestrutura

| Funcionalidade | FREE | STARTER | PRO | TEAM | ENTERPRISE |
|---|:---:|:---:|:---:|:---:|:---:|
| Documentação completa | ✅ | ✅ | ✅ | ✅ | ✅ |
| Issues no GitHub | ✅ | ✅ | ✅ | ✅ | ✅ |
| Suporte por email | ❌ | ✅ | ✅ | ✅ | ✅ |
| SLA de resposta | ❌ | ❌ | 48h | 24h | 4h |
| Suporte dedicado | ❌ | ❌ | ❌ | ❌ | ✅ |
| Consultoria dados | ❌ | ❌ | ❌ | ❌ | ✅ |
| On-premise deploy | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Implementação Técnica da Separação

### 3.1 Mecanismo Atual (licensing/)

O sistema de licensing já está implementado em `src/fraud_generator/licensing/`:

```python
# license.py — HMAC-SHA256 assinatura
License.create(license_id, email, plan, expires, max_events, max_concurrent, secret)
License.verify_signature(secret) → bool

# limits.py — limites por plano
PLAN_LIMITS[LicensePlan.PRO].max_events_month  # 100_000_000

# validator.py — validação no startup
validate_env(phone_home=True)  # verifica ENV vars, HMAC, expiração, heartbeat
```

### 3.2 Onde Aplicar os Gates (Pontos de Enforcement)

```
┌─ CLI (generate.py / stream.py) ─────────────────────────────────┐
│                                                                  │
│  1. parse_args()                                                │
│  2. 🔒 validate_env()  ← verifica licença no início             │
│  3. 🔒 check_format_allowed()  ← bloqueia formatos por plano   │
│  4. 🔒 check_size_allowed()  ← limita output size (API only)   │
│  5. generators executam normalmente                             │
│  6. 🔒 BiometricEnricher.enrich()  ← retorna null se FREE      │
│  7. 🔒 GeoEnricher/SessionEnricher  ← campos Pro+ = null       │
│  8. exporters executam normalmente                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Implementação dos Gates por Camada

#### Gate 1: Enricher Tier Check

```python
# Já implementado em BiometricEnricher
class BiometricEnricher:
    def enrich(self, tx: dict, bag: GeneratorBag) -> None:
        if bag.plan_tier < LicensePlan.PRO:
            # Todos os 10 campos = None
            tx['typing_speed_avg_ms'] = None
            tx['touch_pressure_avg'] = None
            # ...
            return
        # Gera valores reais
```

#### Gate 2: API Rate Limiting

```python
# No middleware da API (FastAPI)
from fraud_generator.licensing.limits import PLAN_LIMITS

@app.middleware("http")
async def rate_limit(request, call_next):
    license = get_license_from_header(request)
    limits = PLAN_LIMITS[license.plan]
    
    if await redis.get(f"req_count:{license.license_id}") > limits.max_requests_per_minute:
        raise HTTPException(429, "Rate limit exceeded")
    
    return await call_next(request)
```

#### Gate 3: Format Restriction (API)

```python
# Já implementado em validator.py
check_format_allowed(license, format_name)  # raises LicenseError
```

#### Gate 4: Event Count Tracking (API)

```python
# No endpoint de geração
async def generate_endpoint(request):
    license = get_license(request)
    limits = PLAN_LIMITS[license.plan]
    
    monthly_usage = await redis.get(f"usage:{license.license_id}:{month}")
    if monthly_usage + request.count > limits.max_events_month:
        raise HTTPException(402, "Monthly event limit exceeded")
```

### 3.4 Arquitetura do Enforcement

```
┌── Open Source (CLI) ──────────────────────────────────┐
│                                                        │
│  Sem enforcement de licença no CLI local               │
│  Todos os formatos, todos os geradores, sem limite     │
│  BiometricEnricher → null (sem licença = FREE)         │
│  Licença: Non-Commercial (ver LICENSE)                 │
│                                                        │
└────────────────────────────────────────────────────────┘

┌── API Hospedada (synthfin.com.br) ────────────────────┐
│                                                        │
│  ┌─ Middleware ─────────────────────────────┐          │
│  │  1. Auth (API key → License)             │          │
│  │  2. Rate limiting (Redis + PLAN_LIMITS)  │          │
│  │  3. Usage tracking (mensal)              │          │
│  │  4. Format validation                    │          │
│  │  5. Heartbeat (anti-sharing)             │          │
│  └──────────────────────────────────────────┘          │
│                                                        │
│  ┌─ Gerador (mesmo código) ─────────────────┐         │
│  │  plan_tier injetado no GeneratorBag       │         │
│  │  Enrichers verificam tier para campos Pro+│         │
│  └───────────────────────────────────────────┘         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 4. Modelo de Preços

### 4.1 Tabela de Preços (API Hospedada — Valores Ativos na Landing Page)

| Plano | Preço/mês (USD) | Público-Alvo |
|---|---:|---|
| Open Source | Free | Estudo, pesquisa acadêmica, experimentação |
| STARTER | $9 | Desenvolvedores individuais, startups early-stage |
| PRO | $29 | Equipes de ML, fintechs em crescimento |
| TEAM | $99 | Empresas médias, times de dados |
| ENTERPRISE | Sob consulta | Grandes instituições financeiras, bancos |

> **Nota**: Os valores acima refletem os preços publicados em `synthfin.com.br`. Versões anteriores deste documento citavam preços em BRL (R$97/R$297/R$797) que foram ajustados para o mercado internacional.

### 4.2 Justificativa de Valor

| Valor Entregue | Alternativa no Mercado | Custo da Alternativa |
|---|---|---|
| 25 fraudes brasileiras calibradas | Contratar cientista de dados para criar datasets | R$ 15K+/mês |
| Campos BACEN PIX reais | Comprar dados sintéticos genéricos (Hazy, Mostly AI) | $500-5K/mês |
| Schema customizável | Desenvolver gerador interno | 3-6 meses dev |
| Streaming Kafka pronto | Configurar pipeline de teste | 2-4 semanas ops |

### 4.3 Trial e Conversão

```
Funil de conversão:

1. GitHub (discovery)    → README, exemplos, docs
2. CLI local (adoption)  → Sem limite, non-commercial
3. Necessidade comercial → synthfin.com.br/pricing
4. Trial 14 dias PRO     → API key imediata
5. Conversão paga        → Stripe/PagSeguro
```

---

## 5. O Que NÃO Restringir no Tier Gratuito

É importante manter o tier gratuito funcional o suficiente para ser útil em estudos:

| Manter Gratuito | Razão |
|---|---|
| CLI sem limite de tamanho | Diferencial competitivo; atrai desenvolvedores |
| Todos os 25 tipos de fraude | Valor educacional; não faz sentido limitar |
| Todos os formatos no CLI | Facilita adoção e testes |
| Seed determinístico | Essencial para pesquisa reprodutível |
| Perfis comportamentais | Core do produto; limitar prejudica qualidade |
| Streaming local (stdout/Kafka/webhook) | Necessário para testes de pipeline |
| Documentação completa | Reduz suporte; melhora adoção |

---

## 6. O Que Restringir (Diferenciadores Pagos)

| Funcionalidade Paga | Tier Mínimo | Razão |
|---|---|---|
| Campos biométricos (10 campos) | PRO | Dados avançados para modelos sofisticados |
| Velocity windows estendidos (1h/6h/7d/30d) | PRO | Detecção de fraude avançada |
| Geo clustering avançado | PRO | Análise espacial premium |
| API REST hospedada | STARTER | Conveniência, sem infraestrutura |
| Calibração RAG personalizada | TEAM | Customização enterprise |
| Suporte com SLA | PRO+ | Disponibilidade garantida |
| On-premise deploy | ENTERPRISE | Requisito compliance bancário |
| Fraude sequencial (velocity checks) | TEAM | Padrões complexos de fraude |
| Dashboard de analytics | PRO | Visualização de qualidade dos dados |

---

## 7. Status de Implementação

### Fase 1 — Licença e Gates Básicos ✅
1. ✅ Atualizar LICENSE para non-commercial
2. ✅ Sistema de licensing implementado (`licensing/`)
3. ✅ Gate de tier no `BiometricEnricher`
4. ⬜ Adicionar gate de tier no `GeoEnricher` e `SessionEnricher`
5. ✅ Página de pricing em synthfin.com.br (Next.js landpage com tabela de planos)

### Fase 2 — API Hospedada v2 ✅
1. ✅ FastAPI endpoints (15 rotas em `/v2/`: auth, generate, jobs, download, usage, billing, admin)
2. ✅ Middleware de rate limiting com Redis (4 middleware: auth, metrics, request_log, security_headers)
3. ✅ Tracking de usage mensal (`/v2/usage`)
4. ✅ Dashboard de admin (`/v2/admin/dashboard`, `/v2/admin/users`, freeze)
5. ✅ Integração Stripe (Checkout session + webhook handler)

### Fase 3 — Frontend SaaS ✅
1. ✅ Dashboard SaaS (Next.js 15 + React 19) em `app.synthfin.com.br`
2. ✅ Landing page com pricing em `synthfin.com.br`
3. ✅ Autenticação por API key com cookie session (8h expiry)
4. ✅ Job management (criar, monitorar, cancelar, download)
5. ✅ Billing no dashboard (upgrade via Stripe Checkout, cancel)

### Fase 4 — Infraestrutura de Produção ✅
1. ✅ Docker Compose com 8 serviços (API, Web, Landpage, Redis, MinIO, MinIO-setup, Deploy-webhook, Traefik)
2. ✅ CI/CD completo (GitHub Actions → GHCR → deploy webhook → VPS)
3. ✅ Segurança 6 camadas (Cloudflare, UFW, fail2ban, SSH hardening, Docker, system hardening)
4. ✅ Traefik v3 com TLS automático (Let's Encrypt)

### Pendente (Backlog)
1. ⬜ Gate de tier no `GeoEnricher` e `SessionEnricher`
2. ⬜ Velocity windows estendidos (1h/6h/7d/30d) gate por tier
3. ⬜ Streaming mode via API (hoje apenas batch)
4. ⬜ SSE/WebSocket para progress real-time (polling 5s é suficiente por ora)
5. ⬜ Hetzner Object Storage para arquivos >30GB
6. ⬜ PagSeguro como alternativa ao Stripe para mercado BR
7. ⬜ On-premise deployment guide
8. ⬜ SSO/SAML integration
9. ⬜ Calibração RAG customizada por cliente

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Usuários ignoram licença non-commercial | Alta | Médio | Monitorar uso; enviar cease & desist |
| Fork remove restrição de licença | Média | Baixo | Licença se aplica em qualquer cópia |
| Campos gratuitos são suficientes (ninguém paga) | Média | Alto | Biometria + velocity + API são diferenciadores fortes |
| Preço alto para mercado BR | Média | Médio | Oferecer preços em BRL com desconto regional |
| Competitor copia funcionalidade | Baixa | Médio | Vantagem de primeiro mover; calibração RAG é difícil de replicar |

---

*Gerado por GitHub Copilot — synthfin-data v4.10*
