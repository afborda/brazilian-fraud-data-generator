# 🔍 Pesquisa de Mercado — ShadowTraffic
> Data da pesquisa: 04/03/2026 | Fontes: shadowtraffic.io, HackerNews, Reddit, docs.shadowtraffic.io

---

## 1. O que é o ShadowTraffic

ShadowTraffic é uma ferramenta **containerizada** (Docker) para geração de dados sintéticos
declarativos. O usuário escreve um JSON descrevendo o schema, e a ferramenta gera dados
realistas e os envia para Kafka, Postgres, S3, Webhooks, etc.

**Fundador:** Michael Drogalis  
**Lançamento público (HN):** Novembro de 2023  
**Modelo:** Produto, não SaaS — o usuário roda localmente  
**Repositório/Site:** https://shadowtraffic.io

---

## 2. Pricing Oficial (pesquisado em 04/03/2026)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PLANOS SHADOWTRAFFIC — 2026                          │
├──────────────────┬──────────────┬──────────────┬────────────────────────┤
│ Plano            │ Preço USD    │ Preço BRL*   │ Período               │
├──────────────────┼──────────────┼──────────────┼────────────────────────┤
│ Free Trial       │ $0           │ R$ 0         │ 30 dias                │
│ Developer        │ $399/ano     │ R$ 2.394/ano │ Anual (sem mensal)     │
│ Enterprise       │ Sob consulta │ Sob consulta │ Anual                  │
└──────────────────┴──────────────┴──────────────┴────────────────────────┘
* Conversão: 1 USD = R$ 6,00 (março 2026)
```

### Limites por plano:

```
                        FREE TRIAL          DEVELOPER         ENTERPRISE
                        ──────────          ─────────         ──────────
  Time                  30 dias             1 ano             1 ano
  Usuários              1                   1                 ilimitado
  Concurrent instances  1                   3                 ilimitado
  Eventos/min           600 (= ~10/s)       ilimitado         ilimitado
  Data/mês              200 GB              1 TB              ilimitado
  Suporte               ❌ nenhum           best effort       plano padrão
```

### Análise do Pricing:

- **Gap enorme de $0 → $399/ano** — não existe plano mensal, não existe tier intermediário
- Um freelancer que precisa por 1 mês paga $399 (R$ 2.394) ou não usa
- Sem opção mensal = barreira alta para adoção individual
- Sem plano "Team" — de Developer ($399) pula direto para Enterprise (preço oculto)
- Modelo **annual-only** é agressivo para mercado B2C

---

## 3. Funcionalidades e Pontos POSITIVOS 👍

### 3.1 API Declarativa Poderosa
```json
{
  "topic": "customers",
  "row": {
    "name":       { "_gen": "string", "expr": "#{Name.full_name}" },
    "age":        { "_gen": "uniformDistribution", "bounds": [18, 80] },
    "membership": { "_gen": "oneOf", "choices": ["gold","silver","bronze"] }
  }
}
```
→ Fácil de ler, expressivo, composable

### 3.2 Primitivos Avançados
| Primitivo          | O que faz                                          |
|--------------------|----------------------------------------------------|
| `stateMachine`     | Modela sequências de eventos (funil de conversão)  |
| `fork`             | Paraleliza N instâncias (ex: 10.000 sensores)      |
| `histogram`        | Distribui dados em proporções (lei de Pareto 80/20)|
| `intervals`        | Varia taxa por horário/dia da semana (cron-like)   |
| `lookup`           | Referência entre tabelas (joins realistas)         |
| `delay`/`duplicate`| Simula falhas de rede, dados out-of-order          |

### 3.3 Targets de Saída Suportados
- ✅ Apache Kafka (com serializers customizáveis)
- ✅ Confluent Cloud
- ✅ Amazon S3
- ✅ PostgreSQL / MySQL
- ✅ Webhook HTTP
- ✅ stdout para pipelines Unix

### 3.4 Developer Experience
- Seed para reproducibilidade (`--seed 146726570`)
- Preprocessors para compor arquivos JSON dinamicamente
- Hot reload durante desenvolvimento
- LLM context para uso com Claude/Cursor
- Documentação bem estruturada com vídeos

### 3.5 Testemunhos Reais (do site)
> *"ShadowTraffic made it easy to stream terabytes of synthetic data into our product"*
> — Chinmay Soman, Head of Product @ StarTree

> *"State machine support was incredibly useful for deterministic scenarios for clickstream analysis and anomaly detection"*
> — Testemunho de uso em competição de desenvolvedores

> *"After spending significant time writing my own data generator tools, I have been consistently impressed and delighted with ShadowTraffic"*
> — Gordon Murray, Platform Engineer @ Teamwork

---

## 4. Pontos NEGATIVOS e GAPS 👎

### 4.1 Encontrado no Hacker News (Show HN — Nov 2023, 77 pontos)

**Polêmica de astroturfing:**
> *"This is a weirdly astroturfed post, a full 50% of the top level comments are the author or accounts created moments before this post, specifically to comment here."*
> — abstractbeliefs, HN

- 3+ contas criadas **minutos antes** do post apenas para comentar positivamente
- Sem disclosure de relação com o projeto
- Comunidade técnica ficou com **"bad taste in the mouth"**
- Dano à credibilidade de longo prazo

**Feedback técnico indireto:**
- O próprio founder admitiu no HN: *"I'm looking forward to offering this as a cloud service someday"*
  → Em 2026, **ainda não existe hosted API** — promessa não cumprida após 2+ anos

### 4.2 Gaps Estruturais Identificados

#### ❌ Gap 1: ZERO hosted API
- Usuário **obrigatoriamente** precisa instalar Docker
- Para um cientista de dados que só quer um `.parquet`, isso é friction enorme
- Nenhum endpoint HTTP direto — você não pode usar do Google Colab

#### ❌ Gap 2: Zero contexto regional/localizado
O ShadowTraffic gera dados genéricos americanos:
```
"Sang Torphy"        ← nome aleatório
"49001 Jefferson Street, Wisconsin"  ← endereço americano
"herman.brakus"      ← username genérico
```
Não existe:
- CPF (Cadastro de Pessoas Físicas) válido
- CNPJ válido
- Endereços brasileiros (CEP, logradouro)
- Bancos brasileiros (Bradesco, Itaú, Nubank, etc.)
- PIX como método de pagamento
- Padrões de fraude do mercado brasileiro
- Real (R$) como moeda

#### ❌ Gap 3: Não é ML-ready
- Foco: **simular tráfego** para testar sistemas
- Não foca em: **gerar datasets rotulados** para treinar modelos
- Não existe campo `is_fraud: true/false`, `fraud_type: "pix_cloning"` prontos
- Para treinar um modelo de detecção de fraude **você teria que implementar do zero**

#### ❌ Gap 4: Curva de aprendizado da DSL
```json
{
  "topic": "funnelEvents",
  "fork": { "key": { "_gen": "string", "expr": "..." }, "stagger": { "ms": 200 } },
  "stateMachine": {
    "_gen": "stateMachine",
    "initial": "viewLandingPage",
    "transitions": { "viewLandingPage": "addItemToCart", ... }
  }
}
```
→ Você precisa aprender toda uma DSL JSON antes de gerar dados úteis
→ Não é "one-liner" — é uma linguagem de configuração completa

#### ❌ Gap 5: Sem plano mensal / sem tier Team intermediário
```
FREE (30d, 10 ev/s)  →→→→→→→→ [VAZIO $0→$399] →→→→→→→→ Developer ($399/ano)
```
Usuários que precisam por 1-3 meses = sem solução

#### ❌ Gap 6: Dados sem padrão de negócio embutido
- Não existe preset "e-commerce", "banking", "ride-share"
- Tudo precisa ser declarado do zero pelo usuário
- Nenhum "fraud injection" automático com padrões realistas

---

## 5. Posicionamento de Mercado

### 5.1 Quem são os usuários do ShadowTraffic
1. **Solutions Engineers** (Confluent, Timescale, Materialize) — para demos
2. **Platform Engineers** — para testes de pipeline de dados
3. **Data Engineers** — para testar CDC, Kafka consumers
4. **Sales Engineers** — para mostrar produto com dados realistas

### 5.2 Quem ShadowTraffic NÃO atende bem
1. **Cientistas de dados brasileiros** que precisam de dados rotulados para ML
2. **Pesquisadores de fraude** no contexto BR (PIX, boleto, TED)
3. **Startups de fintech BR** treinando modelos anti-fraude
4. **Usuários simples** que só querem um CSV e não querem aprender Docker+DSL

---

## 6. Tamanho do Mercado (referência)

```
Mercado global de Synthetic Data Generation (2024):    ~$550M USD
Projeção 2030:                                          ~$3.7B USD
CAGR:                                                   ~38%/ano

Mercado de detecção de fraude fintech Brasil (2024):   ~R$ 2.1B
Crescimento anual BR:                                   ~24%/ano

Empresas BR que precisam de dados sintéticos:
  - Fintechs (ex: Nubank, Inter, C6, PicPay, Mercado Pago)  ~800 empresas
  - Seguradoras com área de fraude                           ~120 empresas
  - Bancos com time de data science                          ~50 bancos
  - Startups de fraud detection                              ~60 startups
  - Pesquisadores acadêmicos (LGPD = não pode usar dados reais) ~500 grupos
```

---

## 7. Conclusão da Pesquisa

O ShadowTraffic é um produto **tecnicamente bem feito** e com boa adoção no mercado
norte-americano enterprise. Porém deixa **lacunas críticas** que são exactamente nossa
vantagem competitiva:

1. ❌ Sem hosted API → ✅ Nós vamos ter
2. ❌ Sem dados brasileiros → ✅ Nossa especialidade
3. ❌ Sem rotulagem ML → ✅ Saída pronta para treinar modelos
4. ❌ Pricing anual inflexível → ✅ Mensal acessível em R$
5. ❌ DSL complexa para gerar dados → ✅ Um POST HTTP simples

---

*Fim do documento 01 — ver 02_ANALISE_COMPARATIVA.md para análise cruzada detalhada*
