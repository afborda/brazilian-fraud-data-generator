# ⚔️ Análise Comparativa Cruzada
> ShadowTraffic vs Brazilian Fraud Data Generator (BFDG)
> Data: 04/03/2026

---

## 1. Comparação Feature-by-Feature

```
┌─────────────────────────────────────┬───────────────────────┬───────────────────────┐
│ Feature                             │ ShadowTraffic         │ BFDG (nosso projeto)  │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ DADOS BRASILEIROS                   │                       │                       │
│  CPF válido (algoritmo real)        │ ❌ não existe         │ ✅ validator próprio   │
│  CNPJ válido                        │ ❌ não existe         │ 🔜 planejado           │
│  Bancos BR (Itaú, Nubank, etc.)     │ ❌ não existe         │ ✅ config/banks.py     │
│  PIX como método de pagamento       │ ❌ não existe         │ ✅ fraud patterns PIX  │
│  MCC codes Brasil                   │ ❌ não existe         │ ✅ config/merchants.py │
│  Cidades/estados BR com coords GPS  │ ❌ não existe         │ ✅ config/geography.py │
│  Endereços BR realistas             │ ❌ não existe         │ ✅ via Faker pt_BR     │
│  Real (R$) como moeda               │ ❌ não existe         │ ✅ nativo              │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ FRAUDE                              │                       │                       │
│  Rotulagem is_fraud / fraud_type    │ ❌ você implementa    │ ✅ automático          │
│  PIX cloning (fraude BR específica) │ ❌ não existe         │ ✅ implementado        │
│  Card takeover                      │ ❌ não existe         │ ✅ implementado        │
│  Social engineering                 │ ❌ não existe         │ ✅ implementado        │
│  Account takeover                   │ ❌ não existe         │ ✅ implementado        │
│  GPS spoofing (ride-share)          │ ❌ não existe         │ ✅ implementado        │
│  Fake ride fraud                    │ ❌ não existe         │ ✅ implementado        │
│  Driver collusion                   │ ❌ não existe         │ ✅ implementado        │
│  Taxa de fraude configurável        │ ❌ você implementa    │ ✅ --fraud-rate flag    │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ RIDE-SHARE                          │                       │                       │
│  Dados de corridas (ride-share)     │ ❌ não existe         │ ✅ domínio completo    │
│  Uber / 99 / InDrive                │ ❌ não existe         │ ✅ apps BR             │
│  Cálculo de distância Haversine     │ ❌ não existe         │ ✅ implementado        │
│  Surge pricing                      │ ❌ não existe         │ ✅ implementado        │
│  Perfis de motorista/passageiro     │ ❌ não existe         │ ✅ 7 perfis BR         │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ FORMATOS DE SAÍDA                   │                       │                       │
│  JSON / JSONL                       │ ✅                    │ ✅                    │
│  CSV                                │ ❌ não nativo         │ ✅                    │
│  Parquet                            │ ❌ não nativo         │ ✅ pyarrow             │
│  MinIO / S3                         │ ✅ (S3)               │ ✅ (MinIO + S3)        │
│  Kafka                              │ ✅ nativo, avançado   │ ✅ via streaming        │
│  Webhook                            │ ✅                    │ ✅                    │
│  stdout                             │ ✅                    │ ✅                    │
│  Postgres / MySQL                   │ ✅                    │ 🔜 planejado           │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ GERAÇÃO EM LOTE (BATCH)             │                       │                       │
│  Geração offline de arquivos        │ ✅ (--stdout + pipe)  │ ✅ generate.py         │
│  Controle de tamanho (ex: 1GB)      │ ❌ por eventos        │ ✅ --size 1GB          │
│  Workers paralelos em batch         │ ❌ forks declarativos │ ✅ --workers N         │
│  Compressão (gzip, snappy)          │ ❌                    │ ✅ Phase 2.1           │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ STREAMING                           │                       │                       │
│  Modo streaming contínuo            │ ✅ modo padrão        │ ✅ stream.py           │
│  Rate configurável (ev/s)           │ ✅                    │ ✅ --rate N            │
│  Graceful shutdown (SIGINT)         │ ✅                    │ ✅ _running flag        │
│  State machines                     │ ✅ nativo, avançado   │ 🔜 básico              │
│  Forks (N instâncias paralelas)     │ ✅ nativo, avançado   │ 🔜 planejado           │
│  Intervals (cron-like timing)       │ ✅ nativo             │ 🔜 planejado           │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ ML / DATA SCIENCE                   │                       │                       │
│  Dataset rotulado para ML           │ ❌ não é o foco       │ ✅ foco principal      │
│  Seed para reproducibilidade        │ ✅ --seed             │ ✅ --seed              │
│  Perfis comportamentais realistas   │ ❌ você declara       │ ✅ 7 perfis embutidos  │
│  Distribuições estatísticas         │ ✅ avançadas          │ ✅ básicas             │
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ INFRAESTRUTURA / DEPLOY             │                       │                       │
│  Docker                             │ ✅ modo único         │ ✅ suportado           │
│  pip install (Python)               │ ❌ não existe         │ ✅ modo padrão         │
│  Hosted API (sem instalar nada)     │ ❌ NÃO EXISTE         │ 🔜 NOSSA OPORTUNIDADE  │
│  Cloud-native (nós hospedamos)      │ ❌ você hospeda       │ 🔜 api.automabothub.com│
├─────────────────────────────────────┼───────────────────────┼───────────────────────┤
│ LICENSING / NEGÓCIO                 │                       │                       │
│  Plano gratuito                     │ ✅ 30 dias, limitado  │ ✅ 50K ev/mês          │
│  Plano mensal                       │ ❌ NÃO EXISTE         │ ✅ a partir R$ 49/mês  │
│  Plano anual                        │ ✅ $399/ano           │ ✅ desconto 2 meses    │
│  Preço em R$ (mercado BR)           │ ❌ só USD             │ ✅ nativo BRL          │
│  Pagamento BR (PIX, boleto)         │ ❌ só cartão USD      │ 🔜 via Stripe BR       │
│  Sistema de licença HMAC            │ ✅ license.env        │ ✅ idêntico modelo      │
│  Phone-home / heartbeat             │ ✅ sim                │ ✅ sim                  │
│  Revogação remota                   │ ❓ desconhecido       │ ✅ via API admin        │
└─────────────────────────────────────┴───────────────────────┴───────────────────────┘
```

---

## 2. Matriz de Forças e Fraquezas

### Nossa Posição

```
                    FORÇAS ÚNICAS (nós)
                    ───────────────────────────────────
                    ✅ CPF/CNPJ válido
                    ✅ Dados 100% BR (cidades, bancos, MCC)
                    ✅ Fraud injection automático ML-ready
  FRAQUEZAS         ✅ Ride-share (nicho inexistente no mercado)    OPORTUNIDADES
  ─────────         ✅ Parquet ML-ready                             ────────────
  ❌ State machines ✅ pip install sem Docker                       🎯 Hosted API
  ❌ Forks avançado ✅ Pricing mensal em R$                        🎯 Mercado BR
  ❌ Joins avançados ✅ License HMAC + phone-home                  🎯 Colab/Jupyter
  ❌ Postgres target                                                🎯 Fintechs BR
                    AMEAÇAS
                    ─────────────────────────────────────
                    ⚠️  ShadowTraffic lançar hosted API
                    ⚠️  ShadowTraffic adicionar pt_BR locale
                    ⚠️  Concorrente open-source clonar ideia
```

---

## 3. Análise Cruzada: O que temos HOJE vs O que podemos TER

### 3.1 Estado Atual (v4.1.0 — guaraná)

```
HOJE:

  generate.py ──► TransactionGenerator ──► JSONL / CSV / Parquet / MinIO
       │
       └──► RideGenerator ──────────────► JSONL / CSV / Parquet / MinIO

  stream.py ──► TransactionGenerator ──► stdout / Kafka / Webhook
      │
      └──► RideGenerator ─────────────► stdout / Kafka / Webhook

  License System:
    FRAUDGEN_LICENSE_KEY (env) → HMAC verify → plan limits enforcement
    Phone-home → api.automabothub.com
```

### 3.2 Estado Futuro com Hosted API

```
FUTURO (v5.0.0 — pitanga):

  [Usuário] ─── POST /v1/generate ──► [API automabothub.com]
                                            │
                                            ├── auth (API key)
                                            ├── rate limit por plano
                                            ├── job queue (async)
                                            │        │
                                            │        ▼
                                            │   Worker Pool
                                            │   (generate.py workers)
                                            │        │
                                            │        ▼
                                            │   MinIO / S3 storage
                                            │        │
                                            │        ▼
                                    ◄───────┘   signed URL (24h)
  [Usuário] ─── GET /v1/jobs/id ──► download_url ──► arquivo .parquet/.csv/.jsonl
```

---

## 4. Jornada de Adoção: ShadowTraffic vs BFDG

### ShadowTraffic (complexo):
```
  Passo  1: Conhecer o produto → site
  Passo  2: Criar conta → Stripe
  Passo  3: Instalar Docker (se não tiver)
  Passo  4: Aprender a DSL JSON (_gen, stateMachine, fork, etc.)
  Passo  5: Criar config.json do zero
  Passo  6: docker run shadowtraffic --config config.json
  Passo  7: Verificar output
  Passo  8: Ajustar config até ficar certo
  Passo  9: Conectar target (Kafka, Postgres, etc.)
  Passo 10: Dados finalmente gerados

  Tempo até primeiro dado útil: 1–4 horas
```

### BFDG Modo Self-Hosted (fácil):
```
  Passo 1: pip install (ou docker pull)
  Passo 2: python3 generate.py --type transactions --size 100MB
  Passo 3: Dados prontos em ./output/

  Tempo até primeiro dado útil: 2 minutos
```

### BFDG Modo Hosted API (ultra simples):
```
  Passo 1: Criar conta em automabothub.com (grátis)
  Passo 2: Pegar API key no dashboard
  Passo 3: curl -X POST https://api.automabothub.com/v1/generate \
               -H "Authorization: Bearer fg_live_xxxx" \
               -d '{"type":"transactions","count":50000,"format":"parquet"}'
  Passo 4: Download do arquivo pronto

  Tempo até primeiro dado útil: 30 segundos
```

---

## 5. Para Quem Cada Produto Serve Melhor

```
┌────────────────────────────────────┬──────────────────┬──────────────────────────┐
│ Perfil do Usuário                  │ ShadowTraffic    │ BFDG                     │
├────────────────────────────────────┼──────────────────┼──────────────────────────┤
│ Solutions Engineer US/EU demos     │ ✅ ideal         │ ⚠️  não foco              │
│ Data Engineer testando pipeline    │ ✅ bom           │ ✅ bom                   │
│ Cientista de dados BR (ML)         │ ❌ ruim          │ ✅ IDEAL                 │
│ Pesquisador LGPD (sem dados reais) │ ❌ dados US      │ ✅ IDEAL                 │
│ Fintech BR anti-fraude             │ ❌ sem PIX/CPF   │ ✅ IDEAL                 │
│ Startup ride-share BR              │ ❌ não existe    │ ✅ ÚNICO no mercado       │
│ Testador de pipeline Kafka         │ ✅ excelente     │ ✅ bom                   │
│ Colab/Jupyter sem instalar Docker  │ ❌ impossível    │ ✅ hosted API            │
│ Empresa grande (enterprise)        │ ✅ suporte       │ 🔜 enterprise plan        │
│ Freelancer/individual BR           │ ❌ $399/ano caro │ ✅ R$ 49/mês             │
└────────────────────────────────────┴──────────────────┴──────────────────────────┘
```

---

## 6. Resumo Executivo

```
╔══════════════════════════════════════════════════════════════════════╗
║             VEREDITO: NÃO SOMOS CONCORRENTES DIRETOS                ║
║                                                                      ║
║  ShadowTraffic:  ferramenta GERAL de simulação de tráfego            ║
║                  para engenharia de dados/demos enterprise US/EU     ║
║                                                                      ║
║  BFDG:           ferramenta ESPECIALIZADA em dados de fraude BR      ║
║                  para ML, pesquisa e fintechs brasileiras            ║
║                                                                      ║
║  Nichos diferentes → não precisamos vencê-los diretamente           ║
║  Precisamos DOMINAR o nicho que eles deixaram completamente vazio    ║
╚══════════════════════════════════════════════════════════════════════╝
```

**Nossa tese de produto:**
- Ser o **ShadowTraffic do mercado brasileiro de fraude financeira/ride-share**
- Adicionar o que eles nunca vão ter (**CPF, PIX, Nubank, ride-share BR**)
- Eliminar a fricção que eles nunca eliminaram (**Hosted API = zero instalação**)
- Pricing acessível para o mercado BR (**R$ 49/mês vs R$ 2.394/ano**)

---

*Ver 03_CAPACIDADE_E_ESCALABILIDADE.md para análise técnica de capacidade*
