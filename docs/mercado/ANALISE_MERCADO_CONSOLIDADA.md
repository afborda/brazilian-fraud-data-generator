# Análise de Mercado Consolidada: Existe demanda real?

> **Veredicto**: **GO com foco** — Mercado existe e é crescente, mas exige nicho claro para não virar commodity.

*Pesquisa realizada via Reddit, Kaggle, HuggingFace, LinkedIn, Indeed, sites de vendors, FEBRABAN, BCB e outros fóruns técnicos — Março 2026.*

---

## 1. Sinais de demanda confirmados

### 1.1 Volume de busca em marketplaces de dados

| Plataforma | Query | Resultados |
|---|---|---|
| Kaggle | "fraud detection dataset" | ~7.855 datasets/notebooks |
| Kaggle | "synthetic transaction data" | ~1.451 resultados |
| HuggingFace | "fraud detection" | Dezenas de datasets, vários com >1.000 downloads/mês |
| HuggingFace | "synthetic financial" | Datasets com tração crescente |

**Interpretação**: Existe uma base ativa de pessoas buscando esses dados agora. A maioria usa datasets genéricos (IEEE-CIS, Kaggle Credit Card) por falta de alternativa localizada.

### 1.2 Pedidos explícitos em fóruns

Threads ativas encontradas:

| Subreddit | Post | Sinal |
|---|---|---|
| r/datasets | "Looking for fraud detection dataset and SOTA model" | Pedido direto de dataset |
| r/datasets | "Searching for dataset for fiscal fraud detection" | Pedido direto |
| r/MachineLearning | "Near realtime fraud detection system" | Necessidade de dados realistas para testar sistema |
| r/fintech | "Advice wanted: Best way to learn Payments Risk" | Profissional buscando recursos |
| r/fintech | "Transitioning into Fintech Risk & Fraud Roles" | Mercado de trabalho aquecido |
| r/Brasil / r/investimentos | Múltiplos tópicos sobre "golpe PIX" | Problema real e atual no Brasil |

### 1.3 Mercado de trabalho — prova de demanda corporativa

Vagas encontradas em busca ativa (Indeed, 2025-2026):

| Empresa | Cargo | Relevância |
|---|---|---|
| **Plaid** | Fraud/Risk Data Scientist | Fintech de infraestrutura, ~1000 FTEs |
| **Uber** | Fraud ML Engineer | Ride-share + payments, contexto diretamente aplicável |
| **Whatnot** (marketplace) | Risk & Fraud Analyst/DS | E-commerce com pagamentos |
| **Truist Bank** | Fraud Analytics | Banco tradicional com time dedicado |
| **iFood** (Brasil) | Cientista de Dados Sênior, MLE IA | Contexto brasileiro + fintech (iFood Pago) |

**Interpretação**: Empresas estão contratando times de fraud ML → precisam treinar modelos → precisam de dados. Esse é o caminho de compra mais direto.

### 1.4 Ecossistema de vendors com tração

| Vendor | Métrica publicada | O que valida |
|---|---|---|
| **Sift** | 700+ marcas, ~1 trilhão de eventos/ano | Mercado de detecção de fraude pago existe e é grande |
| **Feedzai** | 90 bilhões de eventos/ano, $8 trilhões em pagamentos protegidos | Demanda enterprise é real |
| **SEON** | 5.000+ clientes, foco em fintechs/bancos | SMB e mid-market também compram |
| **Forter / Ravelin** | Lista pública de clientes enterprise | Mercado global maduro |

**Interpretação**: Esses vendors resolvem o problema de *detecção* em produção. Nosso gerador resolve o problema de *treinamento e teste* de modelos — segmentos complementares, não concorrentes diretos.

---

## 2. Contexto regulatório brasileiro — vento a favor

| Evento/Fato | Impacto no mercado |
|---|---|
| **PIX** lançado em 2020, ~180M usuários, R$22 trilhões em 2024 | Novo vetor de fraude massivo sem datasets históricos disponíveis |
| **LGPD** (Lei Geral de Proteção de Dados) | Bancos não podem compartilhar dados reais de transações → necessidade de dados sintéticos cresce |
| **BC PROTEGE+** (Banco Central, 2024) | BCB reconhece formalmente problema de fraude de abertura de conta — ecossistema vai exigir mais testes |
| **FEBRABAN SEC** (evento março 2026) | Setor bancário com foco explícito em segurança cibernética e fraude digital |
| **Resolução BCB Segurança Digital** (vigência março 2026) | Novo marco regulatório para PSTIs — compliance vai exigir testes de fraude |
| **Open Finance** (2021-2026) | Mais canais = mais superfície de ataque = mais necessidade de dados de teste |

**Interpretação**: A regulação brasileira está criando necessidade involuntária de dados sintéticos. Bancos e fintechs precisam testar sistemas sem expor dados reais de clientes — e a LGPD torna isso ainda mais crítico.

---

## 3. Fóruns e comunidades mapeados

### Brasil — alta relevância
| Comunidade | Tamanho | Tipo de sinal |
|---|---|---|
| **Data Hackers** (Slack) | +30k membros | Maior comunidade de dados/ML do Brasil |
| **LinkedIn** — grupos de Risk Analytics BR | Variado | Profissionais de fraud/risk em fintechs |
| **FEBRABAN TECH** | Evento anual, +10k participantes | Decisores do setor financeiro |
| **r/brdev** | 150k+ membros | Devs brasileiros, menos ruído sobre fraude-produto |
| **r/investimentos** | 500k+ membros | Usuários finais relatando golpes (sinal de tendência) |
| **r/Brasil** | 1M+ membros | Idem |

### Internacional — alta relevância
| Comunidade | Tamanho/Tráfego | Por que relevante |
|---|---|---|
| **r/FraudPrevention** | Ativo | Profissionais de fraude discutem vetores novos |
| **r/datasets** | 23k visitantes/semana | Pedidos diretos de datasets de fraude |
| **r/MachineLearning** | >2M membros | Cases de fraud ML discutidos |
| **r/fintech** | 18k visitantes/semana | Discussões de risco e compliance |
| **Kaggle Discussions** | Enorme | Comunidade ativa de competições de fraud detection |
| **HackerNews** | ~5M visitantes | High quality — papers e ferramentas de fraud ML |

### Internacional — relevância média (nicho)
| Comunidade | Área |
|---|---|
| **r/AskNetsec** | Segurança/fraud técnica |
| **r/scams** | Relatos de vítimas (tendências) |
| ACFE Community | Auditores certificados de fraude |
| FS-ISAC | Setor financeiro, alertas coordenados |

---

## 4. Empresas-alvo (compradores potenciais)

### Tier 1 — Maior probabilidade de compra, impacto alto

| Empresa | Sede | Por que compraria |
|---|---|---|
| **Nubank** | Brasil | Maior banco digital BR, time de ML ativo, compliance LGPD crítico |
| **PicPay** | Brasil | Wallet + PIX, histórico de fraude reportado publicamente |
| **Mercado Pago** | Brasil/Argentina | Maior PSP da América Latina, time de fraud enorme |
| **iFood Pago** | Brasil | Fintech embedded em food delivery + ride-share (match com gerador) |
| **Itaú / Bradesco / Banco do Brasil** | Brasil | Maior base de clientes PIX, times de analytics grandes |
| **Cielo / Rede / GetNet** | Brasil | Adquirentes com problema de chargeback |

### Tier 2 — Potencial, ciclo de venda mais longo

| Empresa | Sede | Por que compraria |
|---|---|---|
| **99 (DiDi Brazil)** | Brasil | Ride-share BR — contexto de fraude de corrida/driver |
| **Rappi** | Colômbia/Brasil | Marketplace + wallet, contexto de fraude de entregador |
| **Stone / Ton** | Brasil | Adquirente mid-market, clientes de alto risco |
| **Creditas / Creditas Card** | Brasil | Crédito com risco de fraud no onboarding |
| **Plaid** | EUA | Infraestrutura financeira — pode querer benchmark em mercados emergentes |
| **Stripe / Adyen** | Global | PSP global com clientes BR — podem querer dados de contexto local |

### Tier 3 — Indirect (via plataformas e implementadores)

| Canal | Como funciona |
|---|---|
| **Consultoras de dados** (Accenture, Capgemini, CI&T no BR) | Usam dados sintéticos em projetos para bancos — comprariam para acelerar entrega |
| **Kaggle Competition sponsors** | Patrocinar competição com dataset gerado — aquisição de usuários e credibilidade |
| **Universidades/Pesquisa** (FGV, USP, UFMG) | Pesquisa acadêmica de fraud detection no Brasil — adotam ferramentas open source |

---

## 5. O que NÃO está confirmado (gaps)

| Hipótese | Status | Próxima ação |
|---|---|---|
| Alguém pagaria R$199/mês por dataset atualizado | Não validado — apenas inferido | Criar landing page com waitlist e medir conversão |
| Times de ML em bancos BR têm autonomia para contratar ferramentas SaaS | Incerto — pode ser procurement demorado | Validar com entrevistas com profissionais |
| Mercado é grande o suficiente para sustentar empresa full-time | Incerto | Calcular TAM com dados de vagas e budget de dados disponíveis |

---

## 6. Veredicto final

### GO — com estas condições

**Por que sim:**
- Demanda técnica comprovada (buscas, posts, projetos)
- Demanda corporativa confirmada (vagas de fraud ML em empresas que precisam dos dados)
- Contexto brasileiro único (PIX, LGPD, Open Finance) cria necessidade não atendida por vendors globais
- Custo de entrada baixo (projeto já existe, pipeline de IA vem sobre o que já está feito)

**Com foco em:**
1. Posicionamento explícito: "dados sintéticos de fraude brasileira para times de ML" — não genérico
2. Diferenciação via IA de atualização contínua (veja [PLANOS_PAGOS_IA.md](PLANOS_PAGOS_IA.md))
3. Validação de willingness-to-pay antes de escalar infraestrutura

**Evitar:**
- Disputar mercado genérico com Gretel/MOSTLY AI (batalha perdida)
- Escalar infraestrutura antes de validar pagantes

### Próximos 30 dias

```
Semana 1: Criar landing page com proposta de valor focada e formulário de interesse
Semana 2: Postar dataset de exemplo no HuggingFace + thread no r/datasets com o caso de uso
Semana 3: Entrar em Data Hackers Slack, compartilhar o projeto, coletar feedback
Semana 4: Medir: quantas pessoas baixaram? Quantas se inscreveram? Alguma perguntou preço?
```

---

*Relacionados: [RISCO_COMMODITY.md](RISCO_COMMODITY.md) | [PLANOS_PAGOS_IA.md](PLANOS_PAGOS_IA.md)*

*Última atualização: Março 2026*
