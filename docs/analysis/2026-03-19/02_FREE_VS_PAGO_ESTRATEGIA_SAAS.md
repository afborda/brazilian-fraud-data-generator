# Estratégia Free vs. Pago — SynthFin SaaS
**Data:** 19 de março de 2026
**Escopo:** Cruzamento entre features do gerador, pesquisa de mercado e modelo de monetização

---

## Premissa Central

A divisão free/pago não deve ser arbitrária. Ela deve responder a uma pergunta estratégica:

> **"O que entregamos de graça que é suficiente para convencer o cliente
> de que precisa pagar para ter o que realmente importa?"**

Um produto free fraco demais não converte. Um produto free bom demais não vende o pago.
O ponto de equilíbrio: **o free resolve o problema de aprendizado e prototipagem.
O pago resolve o problema de produção.**

---

## Parte 1 — Perfis de Usuário e o Que Cada Um Precisa

### 1.1 Quem usa o gerador hoje (open source / free)

```
PERFIL A — Estudante / Pesquisador
  Objetivo: aprender sobre fraudes, treinar modelo para TCC/artigo
  Volume: 10K-100K transações
  O que precisa: dados com estrutura correta, padrões básicos, CSV
  O que NÃO precisa: velocidade, escala, velocity windows completas
  Disposto a pagar: R$ 0 (budget inexistente)
  → DEVE ficar no free / open source

PERFIL B — Data Scientist em Fintech (POC / prototipagem)
  Objetivo: validar hipótese antes de ir para dados reais de produção
  Volume: 100K-1M transações
  O que precisa: padrões realistas, fraud rate configurável, seed
  O que NÃO precisa: grafo de mulas, velocity completo ainda
  Disposto a pagar: R$ 0-200/mês (ainda em avaliação)
  → Plano Free com limites. Converte para Starter quando vai para produção.

PERFIL C — ML Engineer / Time de Fraud (produção)
  Objetivo: treinar modelo de detecção em produção ou benchmark
  Volume: 1M-50M transações
  O que precisa: velocity windows, clustering geo, multi-label, grafo
  O que NÃO precisa: documentação básica (já sabe o que quer)
  Disposto a pagar: R$ 500-5.000/mês
  → Plano Pro/Team. Feature killer: velocity windows completas.

PERFIL D — Fintech / Banco (integração contínua)
  Objetivo: refresh periódico de dados de treino, ambiente de test
  Volume: 10M-500M transações/mês
  O que precisa: tudo + SLA + suporte + customização
  O que NÃO precisa: limitações de quota
  Disposto a pagar: R$ 5.000-50.000/mês
  → Plano Enterprise. Feature killer: grafo de mulas + custom patterns.

PERFIL E — Pesquisador Acadêmico / Publicação
  Objetivo: dataset reproduzível para paper citável
  Volume: 500K-5M transações (uma vez, com seed fixo)
  O que precisa: seed reproducível, multi-label taxonomy, formato diverso
  Disposto a pagar: dependente de verba de pesquisa
  → Plano Academic (gratuito ou com desconto, requer @edu.br ou comprovação)
```

---

## Parte 2 — Matriz de Features por Plano

### 2.1 Lógica de corte

O corte free/pago deve acontecer em três dimensões simultâneas:
- **Volume**: quantidade de eventos por mês
- **Qualidade**: quais features do dado estão disponíveis
- **Controle**: o quanto o usuário pode configurar o gerador

### 2.2 A matriz completa

```
FEATURE                              FREE    STARTER  PRO     TEAM    ENTERPRISE
                                     (CLI)   R$99     R$299   R$799   Custom
─────────────────────────────────────────────────────────────────────────────────
VOLUME
  Eventos por mês                    100K    1M       10M     ∞       ∞
  Eventos por requisição             1K      100K     1M      ∞       ∞
  Jobs simultâneos                   1       3        10      ∞       ∞

FORMATOS DE SAÍDA
  JSONL                              ✓       ✓        ✓       ✓       ✓
  CSV                                ✓       ✓        ✓       ✓       ✓
  Parquet                            ✗       ✓        ✓       ✓       ✓
  Apache Arrow IPC                   ✗       ✗        ✓       ✓       ✓
  Database direct export             ✗       ✗        ✗       ✓       ✓

PADRÕES DE FRAUDE
  4 padrões básicos (PIX_GOLPE,      ✓       ✓        ✓       ✓       ✓
  CARTAO_CLONADO, ATO básico,
  BOLETO_FALSO)
  11 padrões completos               ✗       ✓        ✓       ✓       ✓
  Fraud rate configurável            ✓       ✓        ✓       ✓       ✓
  Fraud rate por tipo (ex: 30%       ✗       ✗        ✓       ✓       ✓
  PIX_GOLPE, 10% ATO)

QUALIDADE DO DADO
  17 sinais de risco                 ✗       ✓        ✓       ✓       ✓
    (fraud_signals, fraud_risk_score)
  Velocity window 24h                ✓       ✓        ✓       ✓       ✓
  Velocity windows completas         ✗       ✗        ✓       ✓       ✓
    (1h / 6h / 7d / 30d)
  Clustering geográfico              ✗       ✗        ✓       ✓       ✓
    (3-5 localizações por cliente)
  Device consistency per customer    ✗       ✗        ✓       ✓       ✓
  Merchant clustering per customer   ✗       ✗        ✓       ✓       ✓
  Impossible travel injection        ✗       ✗        ✓       ✓       ✓
  Multi-label fraud taxonomy         ✗       ✗        ✓       ✓       ✓
  Grafo de mulas (estrutura de rede) ✗       ✗        ✗       ✓       ✓
  Behavioral biometrics simulados    ✗       ✗        ✗       ✓       ✓
  Latência de fraude (2-7 dias)      ✗       ✗        ✗       ✓       ✓

CONTROLE E CONFIGURAÇÃO
  Seed reproduzível                  ✓       ✓        ✓       ✓       ✓
  Perfis comportamentais padrão (7)  ✓       ✓        ✓       ✓       ✓
  Perfis comportamentais customizados ✗      ✗        ✗       ✓       ✓
  Padrões de fraude customizados     ✗       ✗        ✗       ✗       ✓
  Schema declarativo customizado     ✗       ✗        ✓       ✓       ✓
  Time range (start_date/end_date)   ✗       ✓        ✓       ✓       ✓

SUPORTE E SLA
  Documentação pública               ✓       ✓        ✓       ✓       ✓
  Exemplos e tutoriais               ✓       ✓        ✓       ✓       ✓
  Suporte por email                  ✗       ✗        ✓       ✓       ✓
  SLA de resposta                    ✗       ✗        48h     24h     4h
  Canal dedicado (Slack/Discord)     ✗       ✗        ✗       ✓       ✓
  Onboarding dedicado                ✗       ✗        ✗       ✗       ✓
  Customização sob demanda           ✗       ✗        ✗       ✗       ✓

INTEGRAÇÕES
  Download via API REST              ✓       ✓        ✓       ✓       ✓
  Webhook de notificação             ✗       ✓        ✓       ✓       ✓
  Streaming (Kafka/Kinesis)          ✗       ✗        ✗       ✓       ✓
  Push para S3/GCS/Azure Blob        ✗       ✗        ✗       ✓       ✓
  MCP (Model Context Protocol)       ✗       ✗        ✓       ✓       ✓
```

---

## Parte 3 — Raciocínio por Trás de Cada Corte

### 3.1 Por que velocity windows completas ficam no Pro (R$299)?

```
ARGUMENTO:
A pesquisa Amazon FDB prova que sem velocity windows, o modelo
não funciona. Um Data Scientist de fintech que está indo para
produção precisa disso. Ele sabe o valor. Pagar R$299/mês para
economizar semanas de pipeline de feature engineering é trivial
para uma empresa com budget de ML.

SEM ISSO NO FREE/STARTER:
O usuário free consegue treinar um modelo "ok" para POC.
Mas quando vai para produção, o modelo underperforma.
Ele volta para o SynthFin e entende por que precisa do Pro.

RISCO DE NÃO COLOCAR NO STARTER:
Baixo. Starter é para equipes menores que ainda estão validando.
Eles aceitam a limitação porque o volume também é menor.
```

### 3.2 Por que grafo de mulas fica no Team (R$799)?

```
ARGUMENTO:
Grafo de mulas só é útil para quem usa GNN (Graph Neural Networks)
em produção. Isso é nível de maturidade alta em ML. A empresa que
chegou neste ponto está disposta a pagar R$799+/mês. É um recurso
de alto custo computacional para gerar e de altíssimo valor
para quem precisa.

VANTAGEM ESTRATÉGICA:
Nenhum concorrente oferece. Pode ser o único argumento de venda
para certos clientes de alto ticket. Colocar no Pro desvaloriza
o Team. Colocar no Free é suicídio comercial.
```

### 3.3 Por que os 4 padrões básicos ficam no free?

```
ARGUMENTO:
PIX_GOLPE, CARTAO_CLONADO, ATO básico e BOLETO_FALSO são os
padrões mais conhecidos e mais documentados publicamente.
Um estudante consegue entender o produto com eles.
Um concorrente não ganha vantagem por ter esses 4 padrões —
eles estão documentados em papers públicos.

O QUE OS 11 PADRÕES ADICIONAM:
Os outros 7 padrões (MULA_FINANCEIRA, MICRO_BURST_VELOCITY,
DISTRIBUTED_VELOCITY, CARD_TESTING, ENGENHARIA_SOCIAL,
FRAUDE_APLICATIVO, COMPRA_TESTE) têm nuances de calibração
que não estão em nenhum paper público. Esse é o valor
diferenciado que justifica o Starter.
```

### 3.4 Por que Parquet é pago (Starter+)?

```
ARGUMENTO:
Parquet é o formato padrão de data engineering (Spark, dbt,
BigQuery, Redshift, Snowflake). Quem usa Parquet está em
ambiente de produção ou staging — não está experimentando.
Essa pessoa já tem um contexto organizacional com budget.

EXCEÇÃO POSSÍVEL:
Se o feedback de adoção mostrar que o Parquet está sendo
um bloqueio para conversão, pode-se movê-lo para o free.
Mas a hipótese inicial é: formato de produção = plano pago.
```

---

## Parte 4 — Features que NUNCA devem ser open source

### 4.1 Definição do critério

Uma feature não deve ser open source quando cumpre pelo menos um destes critérios:

```
A) Levou meses de pesquisa para calibrar corretamente
   → Velocity windows reais, grafo de mulas realistas,
     latência de fraude calibrada com dados do Banco Central

B) É o principal diferencial de mercado
   → Grafo de mulas para GNN, impossible travel, behavioral biometrics
   → Se open source, qualquer concorrente clona em 1 sprint

C) Requer dados proprietários para funcionar bem
   → Distribuição real de ISPB por tipo de fraude
   → Calendário de feriados + datas de pagamento brasileiro calibrados
   → Proporções reais de chave PIX (CPF vs aleatória) por perfil de fraude

D) É feature de retenção (switching cost)
   → Schema declarativo customizado por empresa
   → Perfis comportamentais customizados por vertical
   → Padrões de fraude proprietários por cliente enterprise
```

### 4.2 A lista de features que ficam SOMENTE no produto pago

```
NUNCA OPEN SOURCE — PROPRIETÁRIO PAGO
──────────────────────────────────────────────────────────
Feature                         Motivo              Plano mínimo
──────────────────────────────────────────────────────────
Velocity windows 1h/6h/7d/30d   Diferencial ML      Pro
Clustering geográfico           Diferencial ML      Pro
Device consistency              Diferencial ML      Pro
Merchant clustering             Diferencial ML      Pro
Impossible travel               Diferencial ML      Pro
Multi-label taxonomy            Diferencial pesquisa Pro
Grafo de mulas (rede laranja)   Diferencial GNN     Team
Behavioral biometrics           Diferencial prod.   Team
Latência de fraude              Calibração prop.    Team
Bot/automação patterns          Calibração prop.    Team
Mão fantasma (RAT pattern)      Exclusivo BR        Team
Padrões custom por cliente      Lock-in             Enterprise
Perfis comportamentais custom   Lock-in             Enterprise
Push para cloud storage         Integração prod.    Team
Streaming Kafka/Kinesis         Integração prod.    Team
```

---

## Parte 5 — Estratégia de Atualização Contínua (Moat de Longo Prazo)

### 5.1 O diferencial que nenhum open source consegue replicar

O maior risco de um produto open source é ser clonado. A defesa não está no código — está na **atualização contínua baseada em inteligência de mercado**.

```
O QUE O PRODUTO PAGO ENTREGA QUE O OPEN SOURCE NÃO CONSEGUE:

Monitoramento contínuo de:
  → Banco Central (relatórios mensais de fraude PIX)
  → Febraban (alertas e estatísticas)
  → Reddit r/FraudPrevention, r/brdev, r/Brazil
  → arXiv cs.CR (papers novos sobre fraud detection)
  → CERT.br (incidentes de segurança)

Ciclo de atualização:
  → Novo padrão descoberto: entra na pesquisa interna
  → Pesquisa interna valida (2-4 semanas)
  → Parâmetros calibrados com dados oficiais quando disponível
  → Publicado para assinantes Pro+ em versão exclusiva
  → 6 meses depois: disponibilizado no open source (se for)

Isso significa:
  → Assinantes Pro sempre têm padrões 6+ meses mais atuais
  → Open source sempre está atrás do estado da arte
  → Clientes enterprise que precisam de detecção dos golpes
    mais recentes PRECISAM do plano pago
```

### 5.2 Comunicação deste diferencial

```
Para o site / materiais de venda:

"O open source congela no dia do release.
 O plano Pro é atualizado todo mês com os golpes que
 estão acontecendo hoje."

"Em 2024, fraudadores mudaram para PIX noturno após
 o Banco Central criar o limite. Nossos assinantes Pro
 tiveram essa atualização em 3 semanas. O open source
 recebeu em novembro."

"O modelo que você treinar com o SynthFin Pro hoje
 vai detectar fraudes que seus concorrentes ainda
 não sabem que existem."
```

---

## Parte 6 — Decisão Final: O Que É Free, O Que É Pago

### Resumo executivo da estratégia

```
FREE (open source + plano free SaaS)
─────────────────────────────────────
O SUFICIENTE PARA: aprender, prototipar, publicar artigo,
                   validar que o produto faz o que promete

ENTREGA:
  4 padrões de fraude básicos
  Velocity 24h
  17 campos de risco (sem velocity completa)
  JSONL + CSV
  100K eventos/mês
  Seed reproduzível
  Documentação completa

NÃO ENTREGA:
  Velocity windows completas (o killer feature de ML)
  Clustering geográfico e de dispositivo
  11 padrões completos
  Parquet

PROPÓSITO ESTRATÉGICO:
  → Convencer o lead de que o produto é real e funciona
  → Gerar estudos, artigos, citações (proof of quality)
  → Pipeline de inbound orgânico via GitHub stars
  → Não canibaliza o pago porque falta a feature crítica


PAGO (Starter/Pro/Team/Enterprise)
────────────────────────────────────
O NECESSÁRIO PARA: produção, resultados reais, features avançadas

ENTREGA PROGRESSIVAMENTE:
  Starter: 11 padrões + 17 sinais + Parquet + volume maior
  Pro: velocity completa + geo clustering + device + impossible travel
  Team: grafo de mulas + behavioral + streaming + cloud push
  Enterprise: tudo + custom patterns + SLA + onboarding

PROPÓSITO ESTRATÉGICO:
  → Resolver o problema real de produção (velocity windows)
  → Criar switching cost com customizações (Enterprise)
  → Atualização contínua como argumento de retenção
  → Preço justificado pelo ROI: semanas de pipeline economizadas
```

---

## Parte 7 — Riscos a Monitorar

```
RISCO 1: Velocity windows sendo construídas pelo próprio cliente
  → Mitiga com: documentação que mostra a complexidade de fazer
    corretamente (sliding windows em JSONL não é trivial)
  → Monitorar: churn por este motivo nas pesquisas de saída

RISCO 2: Concorrente com funding alto clona o produto
  → Mitiga com: atualização contínua (eles sempre estarão 6 meses atrás)
  → Mitiga com: relacionamento direto com clientes enterprise
  → Mitiga com: dados calibrados com Banco Central (difícil de replicar)

RISCO 3: Cliente enterprise não percebe o diferencial
  → Mitiga com: benchmark comparativo (treinar modelo com free vs pro
    e mostrar diferença de AUC)
  → Mitiga com: case de cliente: "modelo melhorou X% com velocity completa"

RISCO 4: Preço mal calibrado
  → Pro a R$299 pode ser barato para o valor entregue
  → Monitorar: time-to-convert e feedback de vendas
  → Alternativa: cobrar por volume depois de certo threshold
```
