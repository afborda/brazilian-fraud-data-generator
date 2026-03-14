# 💰 Modelo de Negócio e Estratégia de Pricing
> Data: 04/03/2026 | Moedas: BRL (R$) e USD ($)

---

## 1. Resumo dos Modelos

### ShadowTraffic (concorrente)
```
FREE TRIAL (30 dias) → Developer ($399/ano) → Enterprise (contato)
Sem mensal. Sem tier intermediário. Mercado: global, USD.
```

### Nosso Modelo Proposto
```
FREE (permanente, limitado) → Starter (R$49/mês) → Pro (R$149/mês) → Team (R$399/mês) → Enterprise
Mensal disponível. Preço BR. Hospedagem inclusa (hosted API).
```

---

## 2. Tabela Completa de Planos

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    PLANOS BFDG — PREÇOS EM R$ E USD (mar/2026)                     │
│                    USD: converter por 1 USD = R$ 6,00                              │
├──────────────┬──────────────┬──────────────┬──────────────────────────────────────┤
│ Plano        │ R$/mês       │ USD/mês      │ O que inclui                         │
├──────────────┼──────────────┼──────────────┼──────────────────────────────────────┤
│ FREE         │ R$ 0         │ $0           │ 50K eventos/mês                      │
│              │              │              │ 1 instância concurrent               │
│              │              │              │ apenas JSONL                         │
│              │              │              │ sem Kafka / webhooks                 │
│              │              │              │ sem suporte                          │
├──────────────┼──────────────┼──────────────┼──────────────────────────────────────┤
│ STARTER      │ R$ 49/mês    │ ~$8/mês      │ 5M eventos/mês                       │
│              │ R$ 490/ano   │ ~$82/ano     │ 3 instâncias concurrent              │
│  (= -16%)    │              │              │ JSONL + CSV + Parquet                │
│              │              │              │ Kafka + Webhook                      │
│              │              │              │ Hosted API access (sem Docker)       │
│              │              │              │ suporte básico (community)           │
├──────────────┼──────────────┼──────────────┼──────────────────────────────────────┤
│ PRO          │ R$ 149/mês   │ ~$25/mês     │ 100M eventos/mês                     │
│              │ R$ 1.490/ano │ ~$248/ano    │ 10 instâncias concurrent             │
│  (= -17%)    │              │              │ todos os formatos                    │
│              │              │              │ Kafka + Webhook + S3/MinIO           │
│              │              │              │ Hosted API priority queue            │
│              │              │              │ suporte por email (48h)              │
│              │              │              │ API key gerenciamento multi-env      │
├──────────────┼──────────────┼──────────────┼──────────────────────────────────────┤
│ TEAM         │ R$ 399/mês   │ ~$66/mês     │ eventos ilimitados                   │
│              │ R$ 3.990/ano │ ~$665/ano    │ concurrent ilimitado                 │
│  (= -17%)    │              │              │ todos os formatos                    │
│              │              │              │ Hosted API dedicated worker          │
│              │              │              │ suporte email (24h) + chat           │
│              │              │              │ dashboard de uso da equipe           │
│              │              │              │ até 10 membros de equipe             │
├──────────────┼──────────────┼──────────────┼──────────────────────────────────────┤
│ ENTERPRISE   │ Sob consulta │ Sob consulta │ tudo do Team +                       │
│              │              │              │ on-premise deploy                    │
│              │              │              │ SLA contratual                       │
│              │              │              │ domínio personalizado                │
│              │              │              │ suporte dedicado (SLA < 4h)          │
│              │              │              │ integração LDAP/SSO                  │
└──────────────┴──────────────┴──────────────┴──────────────────────────────────────┘
```

### Comparação direta com ShadowTraffic:
```
  ShadowTraffic Developer: $399/ano = R$ 2.394/ano = R$ 199,50/mês
  Nosso TEAM:              R$ 399/mês → R$ 3.990/ano (MAIS eventos, hosted incluso)
  Nosso PRO:               R$ 149/mês → R$ 1.490/ano (melhor custo-benefício BR)
  Nosso STARTER:           R$ 49/mês  → R$ 490/ano   (R$ 1.904 mais barato que ST)

  ✅ Para usuário BR: BFDG Starter já é melhor que ShadowTraffic Free Trial
     E custa R$ 49/mês vs R$ 0 por apenas 30 dias deles
```

---

## 3. Projeção de Receita e Custos

### 3.1 Custos Fixos de Infraestrutura

```
┌───────────────────────────────────────────────────────────┐
│                CUSTOS MENSAIS (fase inicial)              │
├───────────────────────────────────────────────────────────┤
│ VPS-1 (Hetzner/DO)                │ R$   39/mês ($6,46)  │
│ Domínio automabothub.com           │ R$    8/mês (anual)  │
│ Email Resend (até 3K/mês free)     │ R$    0/mês          │
│ Cloudflare (free tier)             │ R$    0/mês          │
│ Backup VPS                         │ R$    5/mês          │
├───────────────────────────────────────────────────────────┤
│ TOTAL FIXO                         │ R$   52/mês         │
└───────────────────────────────────────────────────────────┘
```

### 3.2 Break-even (quando se paga)

```
  Cenário MÍNIMO:
    2 clientes Starter (R$ 49) = R$ 98/mês → cobre infra (R$ 52) ✅

  Cenário REALISTA (3 meses):
    5 Starter (R$ 245) + 2 Pro (R$ 298) = R$ 543/mês → lucro R$ 491/mês

  Cenário CRESCIMENTO (12 meses):
    20 Starter + 8 Pro + 2 Team = R$ 980 + R$ 1.192 + R$ 798 = R$ 2.970/mês
    Infra cresce para VPS-2 = R$ 60/mês
    Lucro líquido: R$ 2.910/mês (~R$ 34.920/ano)
```

### 3.3 Projeção Anual Conservadora

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    PROJEÇÃO ANUAL (cenário conservador)                   │
├──────────┬──────────────┬───────────────┬────────────────┬────────────────┤
│ Mês      │ Clientes     │ MRR (R$)      │ Custo infra    │ Lucro          │
├──────────┼──────────────┼───────────────┼────────────────┼────────────────┤
│ Mês 1-2  │ 3 Starter    │ R$ 147        │ R$ 52          │ R$ 95          │
│ Mês 3-4  │ 8S + 2P      │ R$ 690        │ R$ 52          │ R$ 638         │
│ Mês 5-6  │ 15S + 5P     │ R$ 1.480      │ R$ 60 (VPS-2)  │ R$ 1.420       │
│ Mês 7-9  │ 25S+10P+2T   │ R$ 3.523      │ R$ 80          │ R$ 3.443       │
│ Mês 10-12│ 40S+15P+4T   │ R$ 5.553      │ R$ 120 (VPS-3) │ R$ 5.433       │
├──────────┼──────────────┼───────────────┼────────────────┼────────────────┤
│ ANO 1    │ total acum.  │ ~R$ 26.000 ARR│ ~R$ 900 total  │ ~R$ 25.100     │
└──────────┴──────────────┴───────────────┴────────────────┴────────────────┘

ARR = Annual Recurring Revenue
MRR = Monthly Recurring Revenue
```

---

## 4. Estratégia de Aquisição

### 4.1 Canais Primários

```
1. COMUNIDADE OPEN-SOURCE (GitHub)
   → README atraente + star gazers → conversão em usuários pagos
   → GitHub Stars como marketing gratuito

2. COMUNIDADE BRASILEIRA DE DADOS
   → r/dataengineering (BR)
   → Slack/Discord Data Hackers (BR)
   → LinkedIn grupos de fintech BR
   → Meetups PyCon BR, Data Day BR

3. LGPD — DOR ESPECÍFICA BR
   → Empresas não podem usar dados reais de clientes para ML (LGPD art. 11)
   → Precisam EXATAMENTE do que fazemos
   → Alvo: DPO (Data Protection Officers) de fintechs

4. SEO
   → "gerar dados CPF python", "dataset fraude PIX"
   → "dados sintéticos bancários brasil"
   → "mock transaction data brazil"
```

### 4.2 Funil de Conversão

```
  GitHub (open-source free) ──► pip install ──► README ──► docs
         │
         ▼
  Usuário experimenta localmente (FREE tier auto-ativado)
         │
         ▼
  Bate no limite (50K eventos/mês) ou precisa de Parquet/Kafka
         │
         ▼
  CTA: "Upgrade para Starter — R$ 49/mês"
         │
         ├──► Acessa dashboard → pega API key → usa Hosted API
         │
         └──► Ou: usa license.env com Docker (self-hosted)
```

---

## 5. Comparação de Valor: Horas de Desenvolvimento

```
┌───────────────────────────────────────────────────────────────────┐
│  QUANTO CUSTA NÃO USAR NOSSA FERRAMENTA?                         │
│  (custo de desenvolver internamente)                              │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Gerar dados sintéticos BR do zero:     40–80h de dev senior      │
│  Dev senior BR: R$ 80–150/h                                       │
│  Custo: R$ 3.200–12.000 de uma vez                                │
│                                                                   │
│  Nossa ferramenta BFDG:   R$ 49–149/mês                          │
│  ROI: 1 mês de uso já economiza semanas de trabalho               │
│                                                                   │
│  = nossa proposta de valor em R$:                                 │
│    "Economize R$ 3.000+ de trabalho por R$ 49/mês"               │
└───────────────────────────────────────────────────────────────────┘
```

---

## 6. Modos de Uso e Pricing Associado

```
┌────────────────────────────────────────────────────────────────────┐
│              MODO DE USO vs PLANO RECOMENDADO                     │
├──────────────────────────────────┬─────────────────────────────────┤
│ Caso de uso                      │ Plano ideal                     │
├──────────────────────────────────┼─────────────────────────────────┤
│ Experimento pessoal / acadêmico  │ FREE (50K eventos, JSONL)       │
│ Script rápido, 1x                │ FREE                            │
│ Jupyter/Colab, CSV pequenos      │ STARTER R$49 (hosted API)       │
│ Pipeline de ML, Parquet          │ STARTER R$49 ou PRO R$149       │
│ Demo de produto fintech          │ PRO R$149                       │
│ CI/CD com geração de dados       │ PRO R$149                       │
│ Kafka em produção (staging)      │ PRO R$149 ou TEAM R$399         │
│ Time inteiro de data science     │ TEAM R$399                      │
│ Empresa fintech com SLA          │ ENTERPRISE (contato)            │
└──────────────────────────────────┴─────────────────────────────────┘
```

---

## 7. Margem por Plano

```
┌──────────────────────────────────────────────────────────────────┐
│                  ANÁLISE DE MARGEM BRUTA                        │
├──────────┬──────────┬─────────────────────────┬─────────────────┤
│ Plano    │ Receita  │ Custo de infra marginal  │ Margem bruta    │
├──────────┼──────────┼─────────────────────────┼─────────────────┤
│ Starter  │ R$49/mês │ ~R$ 0,10 (CPU + armazen)│ ~99,8%          │
│ Pro      │ R$149/mês│ ~R$ 0,50 (jobs maiores)  │ ~99,7%          │
│ Team     │ R$399/mês│ ~R$ 2,00 (worker dedicad)│ ~99,5%          │
└──────────┴──────────┴─────────────────────────┴─────────────────┘

Software + geração de dados tem margem próxima de 100% porque:
  • O código já está escrito
  • CPU é barata ($0,001/hora em cloud)
  • Dados gerados = ativos efêmeros (não armazenamos)
  • Escala horizontalmente sem custo linear
```

---

*Ver 05_HOSTED_API_GUIA_USUARIO.md para como o usuário usa a API na prática*
