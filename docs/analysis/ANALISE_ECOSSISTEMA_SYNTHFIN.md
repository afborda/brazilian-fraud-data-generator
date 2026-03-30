# Análise do Ecossistema SynthFin

> **Data**: 2026-03-25  
> **Versão de referência**: synthfin-data v4.10, API v2.0.0  
> **Objetivo**: Documentar todos os componentes do ecossistema SynthFin com visão integrada

---

## 1. Visão Geral

O ecossistema SynthFin é composto por **4 projetos** que juntos formam uma plataforma SaaS de geração de dados sintéticos para fraude bancária e ride-share no Brasil.

```
┌──────────────────────────────────────────────────────────────────────┐
│                       ECOSSISTEMA SYNTHFIN                           │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│  │ synthfin-data  │  │  synthfin-api  │  │    synthfin-web        │ │
│  │  (Open Source) │  │  (Privado)     │  │    (Privado)           │ │
│  │                │  │                │  │                        │ │
│  │ Gerador core   │  │ FastAPI v2     │  │ ┌──────┐ ┌─────────┐  │ │
│  │ CLI + formatos │  │ Auth/Billing   │  │ │ App  │ │Landpage │  │ │
│  │ 25 fraudes     │  │ Jobs + Workers │  │ │Next15│ │ Next15  │  │ │
│  │ Enrichers      │  │ Stripe         │  │ └──────┘ └─────────┘  │ │
│  │ Streaming      │  │ Redis/MinIO    │  │                        │ │
│  └───────┬────────┘  └───────┬────────┘  └───────────┬────────────┘ │
│          │                   │                        │              │
│          └───────────────────┼────────────────────────┘              │
│                              │                                       │
│                   ┌──────────┴──────────┐                            │
│                   │  synthfin-saas      │                            │
│                   │  (Infraestrutura)   │                            │
│                   │                     │                            │
│                   │  Docker Compose     │                            │
│                   │  Traefik + SSL      │                            │
│                   │  CI/CD Webhook      │                            │
│                   │  Hardening Ubuntu   │                            │
│                   └─────────────────────┘                            │
└──────────────────────────────────────────────────────────────────────┘
```

### Repositórios

| Repo | Visibilidade | Stack | Domínio |
|---|---|---|---|
| `afborda/brazilian-fraud-data-generator` | Público | Python 3.10+, Faker, PyArrow, Pandas | — (CLI local) |
| `afborda/synthfin-api` (em `synthfin/api/`) | Privado (GHCR) | FastAPI, Redis, MinIO, Stripe, Resend | `api.synthfin.com.br` |
| `afborda/synthfin-web` (em `synthfin/web/`) | Privado (GHCR) | Next.js 15, React 19, Tailwind CSS | `app.synthfin.com.br` |
| `afborda/synthfin-saas` | Privado | Docker Compose, Traefik, Ubuntu 24.04 | `synthfin.com.br` |

---

## 2. Componente: synthfin-data (Open Source)

### Função

Motor de geração de dados sintéticos. Todo o código de geração, enriquecimento, exportação e streaming reside aqui. É usado diretamente via CLI ou importado como biblioteca pela API.

### Capacidades

- **Geradores**: Transações bancárias + Ride-share
- **Fraude**: 25 tipos bancários (RAG-calibrados) + 11 ride-share
- **Enrichers**: Pipeline de 8 estágios com `fraud_risk_score` (0-100)
- **Formatos**: JSONL, CSV, Parquet, Arrow IPC, TSV, JSON Array, Database, MinIO/S3
- **Compressão**: gzip, zstd, snappy
- **Streaming**: stdout, Kafka, webhook
- **Schema mode**: Schemas declarativos JSON com correção AI
- **Escala**: MB → TB via multiprocessing

### Distribuição

- **PyPI**: `pip install -r requirements.txt` (from source)
- **Docker Hub**: `afborda/synthfin-data:latest` (público)
- **GHCR**: `ghcr.io/afborda/synthfin-api:latest` (privado, usado pelo SaaS)

### Versão atual: v4.10 (Governança)

---

## 3. Componente: synthfin-api (API REST)

### Função

API REST que expõe o motor de geração como serviço. Gerencia autenticação, billing, job queue, quotas, e download de arquivos gerados.

### Stack Técnico

| Tecnologia | Uso |
|---|---|
| FastAPI | Framework web (async) |
| Uvicorn | ASGI server |
| Redis | Cache, sessões, rate limiting, job state |
| MinIO | Storage de arquivos gerados (S3-compatible) |
| SQLite | Usuários, licenças, logs |
| Stripe | Pagamentos e assinaturas |
| Resend | Emails transacionais (welcome, verify, expiry) |
| Prometheus Client | Métricas de performance |

### Endpoints v2

| Rota | Método | Descrição |
|---|---|---|
| `/v2/auth/register` | POST | Registro de novo usuário (email + verificação) |
| `/v2/auth/verify` | POST | Verificação de email com código |
| `/v2/auth/keys` | POST | Rotação de API key |
| `/v2/generate` | POST | Criar job de geração (type, count, format, fraud_rate, seed, webhook) |
| `/v2/jobs` | GET | Listar jobs do usuário |
| `/v2/jobs/{id}` | GET | Status de job específico |
| `/v2/jobs/{id}` | DELETE | Cancelar job |
| `/v2/download/{id}` | GET | Download do arquivo gerado (stream ou redirect MinIO) |
| `/v2/usage` | GET | Quota e uso mensal |
| `/v2/billing/checkout` | POST | Criar sessão Stripe Checkout |
| `/v2/billing/cancel` | POST | Cancelar assinatura |
| `/webhooks/stripe` | POST | Handler de eventos Stripe |
| `/v2/admin/dashboard` | GET | Painel admin (stats globais) |
| `/v2/admin/users` | GET | Listar usuários |
| `/v2/admin/users/{id}/freeze` | POST | Congelar/descongelar conta |

### Autenticação

- **API Key**: Prefixo `fgen_sk_` (32 chars aleatórios)
- **Header**: `Authorization: Bearer fgen_sk_xxxx`
- **Admin**: Header `X-Admin-Secret` para endpoints admin
- **Stripe Webhook**: Verificação de assinatura HMAC

### Middleware (4 camadas)

1. **Auth Middleware**: Valida Bearer token → injeta user context
2. **Metrics Middleware**: Prometheus counters (requests, latency, status codes)
3. **Request Log Middleware**: JSON structured logging
4. **Security Headers Middleware**: HSTS, X-Content-Type-Options, X-Frame-Options

### Worker Pool

- `multiprocessing.Pool` para jobs de geração
- Tamanho configurável via `WORKERS` env var
- Jobs persistidos em Redis (status, progress, resultado)
- Download via MinIO presigned URL ou stream direto

### Admin Tools

```bash
# Emitir licença manualmente
python admin_tools/issue_license.py \
  --email user@company.com \
  --plan pro \
  --months 12

# Testar emails
RESEND_API_KEY=re_xxx python admin_tools/test_emails.py \
  --to test@email.com --type all
```

### Versão atual: v2.0.0 (Guaraná)

---

## 4. Componente: synthfin-web (Frontend)

### Estrutura

O frontend é composto por 3 sub-projetos:

```
synthfin/web/
├── dashboard/     ← Legacy (HTML/CSS/JS puro)
├── landpage/      ← Marketing site (Next.js 15)
└── app/           ← SaaS dashboard (Next.js 15)
```

### 4.1 App (Dashboard SaaS)

**Stack**: Next.js 15, React 19, Tailwind CSS, TypeScript  
**Porta**: 3000  
**Domínio**: `app.synthfin.com.br`

#### Rotas

| Rota | Tipo | Descrição |
|---|---|---|
| `/` | Login | Autenticação via API key |
| `/dashboard` | Protegida | Cards de uso + form de geração + tabela de jobs |
| `/api-keys` | Protegida | Gerenciamento de API keys |
| `/plans` | Protegida | Upgrade/downgrade de plano |
| `/docs` | Protegida | Documentação inline |

#### Componentes React

| Componente | Função |
|---|---|
| `NavBar` | Navegação com logout |
| `UsageCards` | 3 cards: eventos usados, quota restante, jobs ativos |
| `GenerateForm` | Formulário de geração com campos avançados (type, count, format, fraud_rate, seed, webhook, date range, states, channels) |
| `JobsTable` | Tabela de jobs com polling a cada 5s (status, progress, download, cancel) |
| `KeyManager` | Visualizar e rotacionar API key |
| `CheckoutButton` | Redireciona para Stripe Checkout |
| `CancelButton` | Cancela assinatura ativa |

#### Autenticação

- Cookie `sf_key` (HttpOnly, Secure, SameSite=Strict, 8h expiry)
- Middleware Next.js protege rotas `/dashboard`, `/api-keys`, `/plans`, `/docs`
- API key nunca exposta ao browser — downloads via proxy server-side

#### Server Actions

```typescript
// actions/api.ts — funções server-side
loginAction(formData)           // POST → cookie → redirect
logoutAction()                  // Clear cookie → redirect
getUsage()                      // GET /v2/usage
getJobs(limit)                  // GET /v2/jobs?limit=N
generateData(params)            // POST /v2/generate
cancelJob(jobId)                // DELETE /v2/jobs/{jobId}
rotateKey()                     // POST /v2/auth/keys → update cookie
createCheckoutSession(plan)     // POST /v2/billing/checkout → Stripe URL
cancelSubscription()            // POST /v2/billing/cancel
```

### 4.2 Landpage (Marketing)

**Stack**: Next.js 15, React 19, Tailwind CSS  
**Porta**: 3001  
**Domínio**: `synthfin.com.br`

#### Seções

- **Hero**: Headline + CTA "Get Started Free"
- **Features**: Grid de capacidades do produto
- **Performance**: Benchmarks de geração
- **Formats**: Formatos suportados com exemplos
- **Pricing**: Tabela de planos
- **Quick Start**: Código de exemplo
- **Footer**: Links GitHub, Docker Hub, docs

#### Preços (Landing Page)

| Plano | Preço/mês (USD) | Limites |
|---|---:|---|
| Open Source | Free | CLI ilimitado, non-commercial |
| Starter | $9 | 5M eventos/mês, 3 workers, 5GB output |
| Pro | $29 | 100M eventos/mês, 10 workers, 20GB output |
| Team | $99 | Ilimitado, prioridade, webhook notifications |
| Enterprise | Custom | On-premise, SLA, consultoria |

### 4.3 Dashboard (Legacy)

**Stack**: HTML, CSS, JavaScript puro  
**Status**: Fallback — substituído pelo App Next.js  
**Design**: Tema escuro, accent teal (#00d4aa), Inter + JetBrains Mono

---

## 5. Componente: synthfin-saas (Infraestrutura)

### Função

Orquestração Docker Compose da infraestrutura de produção. Inclui reverse proxy, storage, cache, deploy automation e hardening de segurança.

### Serviços (docker-compose.yml)

| Serviço | Imagem | Porta | Função |
|---|---|---|---|
| `api` | `ghcr.io/afborda/synthfin-api:latest` | 8000 | Backend FastAPI |
| `web` | `ghcr.io/afborda/synthfin-web:latest` | 3000 | Dashboard Next.js |
| `landpage` | `ghcr.io/afborda/synthfin-landpage:latest` | 3001 | Marketing site |
| `redis` | `redis:7-alpine` | 6379 | Cache + sessions + jobs |
| `minio` | `minio/minio` | 9000/9001 | Object storage (S3-compatible) |
| `minio-setup` | `minio/mc` | — | Cria bucket + policy no startup |
| `deploy-webhook` | Custom Python | 9090 | Webhook CI/CD para deploys |
| `traefik` | `traefik:v3` | 80/443 | Reverse proxy + SSL (Let's Encrypt) |

### Rede e Domínios

```
Internet
  │
  ├─ synthfin.com.br        ──► Traefik ──► landpage:3001
  ├─ app.synthfin.com.br     ──► Traefik ──► web:3000
  ├─ api.synthfin.com.br     ──► Traefik ──► api:8000
  └─ deploy.synthfin.com.br  ──► Traefik ──► deploy-webhook:9090
```

- **Cloudflare**: DNS, WAF, DDoS protection (edge)
- **Traefik v3**: TLS automático via Let's Encrypt ACME
- **VPS**: Ubuntu 24.04 LTS @ OVH

### Segurança (6 camadas)

| Camada | Componente | Proteção |
|---|---|---|
| 1 | Cloudflare | WAF, DDoS, rate limiting edge |
| 2 | UFW Firewall | Apenas 22, 80, 443 abertos |
| 3 | fail2ban | SSH: 3 falhas → 24h ban |
| 4 | SSH Hardening | Sem root login, sem password, ED25519 only |
| 5 | Docker Security | Rede isolada, non-root containers |
| 6 | System Hardening | `harden.sh` — swap, sysctl, audit, unattended-upgrades |

### CI/CD Pipeline

```
Developer pushes to main
  │
  ├── GitHub Actions: push-ghcr.yml
  │     ├── Build API image → ghcr.io/afborda/synthfin-api:latest
  │     ├── Build Web image → ghcr.io/afborda/synthfin-web:latest
  │     └── Build Landpage  → ghcr.io/afborda/synthfin-landpage:latest
  │
  └── GitHub Actions: deploy-prod.yml (triggered after push-ghcr)
        └── curl POST https://deploy.synthfin.com.br/deploy
              ├── HMAC Bearer token verification
              ├── docker login ghcr.io
              ├── docker pull all images
              ├── docker compose up -d --no-deps api web landpage
              └── docker image prune -f
```

### Deploy Webhook

- Servidor HTTP Python (~300 linhas)
- Autenticação via HMAC Bearer token
- Timeout de 300s para pull + restart
- Logs de cada operação retornados no response body

---

## 6. Fluxo End-to-End: Do Código ao Usuário Final

```
1. DESENVOLVIMENTO
   Developer → git push → GitHub (main branch)

2. BUILD
   GitHub Actions → Build 3 Docker images → Push to GHCR

3. DEPLOY
   GitHub Actions → POST deploy webhook → VPS pulls images → docker compose up

4. PRODUÇÃO
   ┌─ Usuário acessa synthfin.com.br (landpage) ─┐
   │  • Vê pricing, features, quick start         │
   │  • Clica "Subscribe" → Stripe Checkout        │
   │  • Paga → Webhook → Create user + API key     │
   │  • Recebe email (Resend) com key + login link  │
   └───────────────────────────────────────────────┘

   ┌─ Usuário acessa app.synthfin.com.br ──────────┐
   │  • Login com API key                           │
   │  • Dashboard: usage cards, gerar dados, jobs   │
   │  • POST /v2/generate → job criado no Redis     │
   │  • Worker executa com synthfin-data engine      │
   │  • Arquivo salvo em MinIO                       │
   │  • Download via presigned URL                   │
   └───────────────────────────────────────────────┘

   ┌─ Uso via CLI (Open Source) ───────────────────┐
   │  • pip install + python generate.py            │
   │  • Sem limite, sem autenticação, non-commercial│
   │  • Docker: afborda/synthfin-data:latest        │
   └───────────────────────────────────────────────┘
```

---

## 7. Variáveis de Ambiente (Produção)

| Variável | Serviço | Descrição |
|---|---|---|
| `API_DOMAIN` | Traefik | `api.synthfin.com.br` |
| `WEB_DOMAIN` | Traefik | `app.synthfin.com.br` |
| `LAND_DOMAIN` | Traefik | `synthfin.com.br` |
| `ACME_EMAIL` | Traefik | Email para renovação SSL |
| `SECRET_KEY` | API | Secret para tokens internos |
| `ADMIN_SECRET` | API | Autenticação do painel admin |
| `ALLOWED_ORIGINS` | API | CORS whitelist |
| `RESEND_API_KEY` | API | Chave Resend para emails |
| `STRIPE_SECRET_KEY` | API | Chave secreta Stripe |
| `STRIPE_WEBHOOK_SECRET` | API | Secret do webhook Stripe |
| `STRIPE_PRICE_STARTER` | API | ID do preço Starter no Stripe |
| `STRIPE_PRICE_PRO` | API | ID do preço Pro no Stripe |
| `REDIS_PASSWORD` | Redis/API | Senha do Redis |
| `MINIO_ROOT_USER` | MinIO | Admin username |
| `MINIO_ROOT_PASSWORD` | MinIO | Admin password |
| `MINIO_BUCKET` | MinIO/API | Nome do bucket para jobs |
| `WORKERS` | API | Tamanho do pool de workers |
| `JOBS_FILE_MAX_AGE_SECONDS` | API | Retenção de arquivos (172800 = 48h) |
| `DEPLOY_TOKEN` | Webhook | Token HMAC para deploys |
| `GHCR_TOKEN` | Webhook | Token de login GHCR |

---

## 8. Status de Implementação

### Funcionalidades Implementadas

| Funcionalidade | Status | Componente |
|---|---|---|
| Motor de geração (banking + rides) | ✅ Completo | synthfin-data |
| 25 fraudes bancárias RAG-calibradas | ✅ Completo | synthfin-data |
| 11 fraudes ride-share | ✅ Completo | synthfin-data |
| 8-stage enricher pipeline | ✅ Completo | synthfin-data |
| 8 formatos de exportação | ✅ Completo | synthfin-data |
| Streaming (stdout/Kafka/webhook) | ✅ Completo | synthfin-data |
| Schema mode + AI correction | ✅ Completo | synthfin-data |
| API REST v2 (15 endpoints) | ✅ Completo | synthfin-api |
| Autenticação por API key | ✅ Completo | synthfin-api |
| Rate limiting + quota tracking | ✅ Completo | synthfin-api |
| Job queue (Redis + multiprocessing) | ✅ Completo | synthfin-api |
| Stripe Checkout integration | ✅ Completo | synthfin-api |
| Email transacional (Resend) | ✅ Completo | synthfin-api |
| Admin dashboard (API) | ✅ Completo | synthfin-api |
| SaaS dashboard (Next.js) | ✅ Completo | synthfin-web/app |
| Landing page com pricing | ✅ Completo | synthfin-web/landpage |
| Reverse proxy + SSL (Traefik) | ✅ Completo | synthfin-saas |
| CI/CD (GitHub Actions → GHCR → VPS) | ✅ Completo | synthfin-saas |
| Segurança 6 camadas | ✅ Completo | synthfin-saas |
| Deploy automation (webhook) | ✅ Completo | synthfin-saas |

### Itens Pendentes ou em Refinamento

| Item | Prioridade | Nota |
|---|---|---|
| SSE/WebSocket para progress real-time | Baixa | Polling 5s é suficiente |
| Hetzner Object Storage para >30GB | Média | Atualmente tudo em MinIO local |
| SSO/SAML enterprise | Baixa | Sob demanda |
| PagSeguro (alternativa Stripe para BR) | Média | Apenas Stripe implementado |
| Streaming mode via API | Média | Apenas batch via API hoje |

---

## 9. Divergências Identificadas

### Preços: Landpage vs Análise de Tiers

| Plano | Landpage (USD) | Análise Tiers (BRL) | Análise Tiers (USD) |
|---|---:|---:|---:|
| Starter | $9/mês | R$ 97/mês | $19/mês |
| Pro | $29/mês | R$ 297/mês | $59/mês |
| Team | $99/mês | R$ 797/mês | $149/mês |

**Recomendação**: Adotar os preços da landpage ($9/$29/$99) como fonte de verdade, pois são os valores visíveis ao cliente. A análise de tiers deve ser atualizada para refletir esses valores.

### API v2: Código vs Documentação

- O `api/README.md` marca a API v2 como "Planejado" (❌), mas a implementação em `src/api/` está **completa** com todos os endpoints funcionais
- **Ação**: Atualizar o README da API para refletir o status real

### Plano de Implementação (ANALISE_TIERS §7)

A seção lista Fases 2-4 como pendentes (⬜), mas várias já estão implementadas:

| Item | Status na Análise | Status Real |
|---|---|---|
| FastAPI endpoints (generate, stream, schema) | ⬜ | ✅ Implementado |
| Middleware rate limiting com Redis | ⬜ | ✅ Implementado |
| Tracking de usage mensal | ⬜ | ✅ Implementado |
| Dashboard de admin | ⬜ | ✅ Implementado |
| Integração Stripe | ⬜ | ✅ Implementado |
| Página de pricing | ⬜ | ✅ Implementado |

---

## 10. Diagrama de Tecnologias

```
┌─────────────────────────────────────────────────────────────────┐
│                        STACK COMPLETO                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EDGE          Cloudflare (DNS + WAF + DDoS)                    │
│                                                                  │
│  PROXY         Traefik v3 (TLS + routing + Let's Encrypt)       │
│                                                                  │
│  BACKEND       FastAPI (Python 3.10+)                           │
│                  ├── Pydantic v2 (validation)                    │
│                  ├── Redis 7 (cache + sessions + jobs)           │
│                  ├── SQLite (users + licenses)                   │
│                  ├── MinIO (S3-compatible file storage)          │
│                  ├── Stripe (payments + webhooks)                │
│                  ├── Resend (transactional email)                │
│                  └── Prometheus (metrics)                        │
│                                                                  │
│  ENGINE        synthfin-data (core library)                     │
│                  ├── Faker (pt-BR data generation)               │
│                  ├── PyArrow (Parquet/Arrow)                     │
│                  ├── Pandas (CSV/DataFrame)                      │
│                  ├── boto3 (S3/MinIO upload)                     │
│                  └── kafka-python (streaming)                    │
│                                                                  │
│  FRONTEND      Next.js 15 + React 19 + Tailwind CSS            │
│                  ├── App: SaaS dashboard (:3000)                 │
│                  └── Landpage: Marketing site (:3001)            │
│                                                                  │
│  INFRA         Ubuntu 24.04 LTS (OVH VPS)                      │
│                  ├── Docker Compose (8 services)                 │
│                  ├── UFW + fail2ban + SSH hardening              │
│                  └── GitHub Actions CI/CD                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

*Gerado por GitHub Copilot — synthfin-data v4.10*
