# O Que o Produto Pago Tem que o Open Source Não Tem
**Data:** 19 de março de 2026
**Propósito:** Referência interna clara de diferenciação + base para materiais de vendas

---

## Visão Geral

```
OPEN SOURCE                          PRODUTO PAGO (SaaS)
(GitHub / CLI gratuito)              (synthfin.com.br)

Ferramenta para aprender             Ferramenta para produção
Suficiente para TCC / artigo         Necessário para modelo em prod
Dados para demonstração              Dados que melhoram AUC real
Você descobre como usar              Você entrega resultados
Congela no release                   Atualiza todo mês
Você roda localmente                 API / cloud / integração
```

---

## 1 — Features de Dado: O Que Muda na Qualidade do Dataset

### 1.1 Velocity Windows Completas

```
OPEN SOURCE
  Entrega apenas: velocity_transactions_24h
                  accumulated_amount_24h

PRODUTO PAGO (Pro+)
  Entrega também: velocity_transactions_1h
                  velocity_transactions_6h
                  velocity_transactions_7d
                  velocity_transactions_30d
                  accumulated_amount_1h
                  accumulated_amount_6h
                  accumulated_amount_7d
                  accumulated_amount_30d
                  velocity_unique_merchants_7d
                  velocity_unique_recipients_7d
                  velocity_unique_devices_7d

POR QUE ISSO IMPORTA:
  A Amazon (FDB research) prova: sem velocidade em múltiplas
  janelas, o modelo não performa melhor que random.

  Com o open source, o cliente tem que calcular isso
  do histórico — o que é complexo, custoso e propenso a erros.

  Com o produto pago, vem pronto. O Data Scientist sai do
  zero para modelo treinado em horas, não semanas.

GANHO DE AUC ESPERADO: +5 a +15 pontos percentuais
```

### 1.2 Clustering Geográfico por Cliente

```
OPEN SOURCE
  Geolocalização aleatória dentro do estado do cliente
  → lat/lon variam entre transações sem padrão
  → Feature geográfica é essencialmente ruído para o modelo

PRODUTO PAGO (Pro+)
  Cada cliente tem 3-5 localizações fixas atribuídas:
    → localização_principal (casa)
    → localização_secundaria (trabalho)
    → 1-3 localizações_frequentes (shopping, padaria, etc.)
  Transações legítimas: 80% vêm dessas localizações
  Transações fraudulentas: localização nova ou distante

  Campos adicionais:
    → distance_from_home_km
    → is_known_location (bool)
    → location_cluster_id
    → first_time_at_this_location (bool)

POR QUE ISSO IMPORTA:
  Modelo treinado com geo aleatório aprende que localização
  não importa. Modelo treinado com geo clustered aprende
  que localização nova = sinal de fraude.

  Fraud detection de produção usa geo como feature de peso 8/10.
  Com dados open source, essa feature não contribui.

GANHO DE AUC ESPERADO: +3 a +8 pontos percentuais
```

### 1.3 Consistency de Dispositivo por Cliente

```
OPEN SOURCE
  device_id varia entre transações do mesmo cliente
  sem padrão consistente

PRODUTO PAGO (Pro+)
  Cada cliente tem 1-2 dispositivos principais:
    → device_primary (smartphone pessoal, 90% das transações)
    → device_secondary (tablet ou PC, 10%)

  Campos adicionais:
    → is_primary_device (bool)
    → device_age_days (dias desde primeiro uso deste device)
    → device_session_count (quantas sessões neste device)
    → new_device_flag (bool — device nunca visto antes)
    → days_since_device_added (para ATO: novo device recente = risco)

POR QUE ISSO IMPORTA:
  Account Takeover (ATO) é detectado principalmente por:
  "dispositivo novo + comportamento novo"
  Sem device consistency, esse sinal não existe nos dados.
```

### 1.4 Clustering de Merchant por Cliente

```
OPEN SOURCE
  merchant_id varia aleatoriamente entre transações

PRODUTO PAGO (Pro+)
  Cada cliente tem 5-10 merchants favoritos:
    → 70% das transações vão para esses merchants
    → 30% são transações novas (oportunísticas)

  Campos adicionais:
    → is_known_merchant (bool)
    → merchant_visit_count (quantas vezes neste merchant)
    → days_since_first_merchant_visit
    → new_merchant_flag (bool)

POR QUE ISSO IMPORTA:
  Card testing usa merchants genéricos pela primeira vez.
  ATO usa merchants que a vítima nunca foi.
  Sem merchant clustering, esses sinais não aparecem.
```

### 1.5 Impossible Travel

```
OPEN SOURCE
  Não existe. Localizações são independentes entre transações.

PRODUTO PAGO (Pro+)
  Em 3-8% dos casos de ATO, gera pares de transações
  geograficamente impossíveis:
    → Transação 1: São Paulo, 14:00
    → Transação 2: Miami, 14:05
    → (impossível em 5 minutos)

  Campos:
    → is_impossible_travel (bool)
    → min_travel_time_required_hours
    → actual_gap_hours
    → impossible_travel_group_id (liga as duas transações)

POR QUE ISSO IMPORTA:
  É o sinal mais forte de ATO e um dos primeiros que
  os sistemas de detecção verificam. Treinar modelo sem
  isso significa modelo cego para esse padrão.
```

### 1.6 Multi-Label Fraud Taxonomy

```
OPEN SOURCE
  is_fraud: bool (0 ou 1)
  fraud_type: string (um tipo por transação)

PRODUTO PAGO (Pro+)
  fraud_labels: lista de labels simultâneos
    Ex: ["ATO", "MULA_FINANCEIRA", "ENGENHARIA_SOCIAL"]

  fraud_chain_id: agrupa transações da mesma cadeia de fraude
  fraud_chain_role: papel da transação na cadeia
    → INITIATION / TRANSFER / LAUNDERING / DESTINATION
  fraud_reported_days_after: latência de detecção
    → Simula o delay real entre ocorrência e detecção (2-30 dias)

POR QUE ISSO IMPORTA:
  Fraude real é raramente "um tipo só". Uma conta tomada
  (ATO) que transfere para uma mula (MULA_FINANCEIRA)
  que recebeu dinheiro via engenharia social é 3 labels
  na mesma cadeia. Modelos treinados com labels binários
  não aprendem essa complexidade.
```

---

## 2 — Padrões de Fraude: Cobertura

### 2.1 O que o open source tem

```
OPEN SOURCE — 11 PADRÕES BANCÁRIOS
────────────────────────────────────────────────────────
1.  ENGENHARIA_SOCIAL       Vítima convencida por telefone
2.  CONTA_TOMADA            Acesso não autorizado à conta
3.  CARTAO_CLONADO          Dados de cartão comprometidos
4.  PIX_GOLPE               Fraude via transferência PIX
5.  FRAUDE_APLICATIVO       Malware / app comprometido
6.  COMPRA_TESTE            Micro-transações de teste
7.  MULA_FINANCEIRA         Lavagem via contas laranja
8.  CARD_TESTING            3 fases: micro → silêncio → grande
9.  MICRO_BURST_VELOCITY    10-50 transações em 5-15 min
10. DISTRIBUTED_VELOCITY    Mesmo ataque, IPs/devices rotativos
11. BOLETO_FALSO            Boleto interceptado e substituído

+ 7 PADRÕES DE RIDE-SHARE
```

### 2.2 O que o produto pago adiciona

```
PRODUTO PAGO — NOVOS PADRÕES (a implementar, plano Pro+)
────────────────────────────────────────────────────────
12. MAO_FANTASMA (RAT Fraud)
    Criminoso opera dispositivo da vítima remotamente
    Dispositivo legítimo + localização correta + comportamento anômalo
    → Exclusivo SaaS: sem nenhum paper público com dados calibrados

13. WHATSAPP_CLONE
    Impersonação de familiar via WhatsApp clonado
    → Transação parece legítima, sinal só em "novo destinatário"

14. SIM_SWAP
    Portabilidade fraudulenta do número + ATO subsequente
    → Cadeia multi-etapa: SIM → login → ATO → transferência

15. CREDENTIAL_STUFFING
    Automated login attempts com lista de credenciais vazadas
    → Padrão de bot, não humano: zero variância de intervalo

16. SYNTHETIC_IDENTITY
    Identidade CPF válido mas fictício, criada para fraude
    → Conta com comportamento "perfeito" até ativação de fraude

17. CONTAS_LARANJA_ADVANCED
    Rede estruturada: orquestrador → recrutadores → mulas camadas
    → Estrutura de grafo completa (somente Team+)

18. SEQUESTRO_RELAMPAGO
    Vítima forçada a transferir dinheiro em tempo real
    → Padrão: múltiplas transferências grandes em sequência curta

19+ Padrões adicionados mensalmente para assinantes Pro+
    com base em monitoramento de fontes oficiais e fóruns
```

---

## 3 — Controle e Configuração

### 3.1 Configuração de geração

```
OPEN SOURCE (CLI)
  fgen generate --type transactions --count 10000 --fraud-rate 0.03

PRODUTO PAGO

  Pro: controle por tipo de fraude
  {
    "type": "transactions",
    "count": 1000000,
    "fraud_rate_by_type": {
      "PIX_GOLPE": 0.015,
      "CONTA_TOMADA": 0.008,
      "CARTAO_CLONADO": 0.005
    }
  }

  Team: perfis comportamentais customizados
  {
    "behavioral_profiles": {
      "heavy_pix_user": { "pix_share": 0.8, "avg_amount": 450 },
      "conservative_elderly": { "pix_share": 0.1, "avg_amount": 200 }
    }
  }

  Enterprise: padrões de fraude completamente customizados
  {
    "custom_fraud_pattern": {
      "name": "FRAUDE_INTERNA_ESPECIFICA_DO_BANCO",
      "signals": [...],
      "channels": ["MOBILE_APP"],
      "amount_range": [10000, 50000]
    }
  }
```

### 3.2 Time range e sazonalidade

```
OPEN SOURCE
  Sem controle de período. Dados gerados com data de hoje.

PRODUTO PAGO (Starter+)
  start_date / end_date: gerar dados históricos

  Útil para:
  → Simular 12 meses de histórico para treino de modelo
  → Incluir sazonalidade real (Natal, Black Friday, Carnaval)
  → Criar datasets de treino/validação/teste com períodos separados

  Campos de sazonalidade já calibrados para Brasil:
  → Black Friday (novembro): volume 3x, fraude 2.5x
  → Natal/Réveillon: volume 2x
  → Carnaval: volume 0.7x
  → Datas de pagamento (5, 15, 20): pico de transações
  → 13° salário (novembro/dezembro): pico de valor médio
```

---

## 4 — Integrações e Operação

### 4.1 Como os dados chegam

```
OPEN SOURCE
  fgen generate > output.jsonl
  (arquivo local, processo manual)

PRODUTO PAGO
  Starter: API REST + download de arquivo
  Pro:     API REST + webhook de notificação + MCP
  Team:    Streaming Kafka/Kinesis (eventos em tempo real)
           Push direto para S3/GCS/Azure Blob
           Agendamento de jobs recorrentes
  Enterprise: Tudo + VPC peering (dados nunca saem da cloud do cliente)
```

### 4.2 MCP — Model Context Protocol (Pro+)

```
O QUE É:
  Integração nativa com Claude e outros LLMs via MCP server.
  O modelo de linguagem pode gerar dados diretamente na conversa.

COMO FUNCIONA:
  Claude: "Gere 50.000 transações com 5% de fraude PIX,
           seed 42, formato Parquet"
  → SynthFin API é chamada automaticamente
  → Arquivo disponível para análise em segundos

POR QUE É DIFERENCIAL:
  Nenhum concorrente tem integração MCP.
  Times de ML que usam LLMs para análise podem gerar
  dados sintéticos sem sair do fluxo de trabalho.
```

---

## 5 — Atualização e Inteligência

### 5.1 O moat que o open source não tem

```
OPEN SOURCE
  ─────────────────────────────────────────────────────
  Versão: fixada no release
  Padrões: documentados em papers públicos até 2024
  Atualização: próximo release (meses)
  Fraudes novas: não refletidas
  ─────────────────────────────────────────────────────

PRODUTO PAGO (Pro+)
  ─────────────────────────────────────────────────────
  Versão: atualizada continuamente
  Padrões: novos golpes em 3-6 semanas após surgir no mercado
  Fontes de atualização:
    → Banco Central (dados mensais PIX)
    → Febraban (alertas e pesquisas)
    → Reddit r/FraudPrevention e r/Brazil
    → arXiv cs.CR (papers novos)
    → CERT.br (incidentes reportados)
    → Monitoramento de fóruns especializados

  Assinante Pro recebe:
    → Changelog mensal de novos padrões
    → Boletim de fraudes emergentes no Brasil
    → Acesso antecipado a novos padrões (6 meses antes do open source)
  ─────────────────────────────────────────────────────

ANALOGIA PARA O CLIENTE:
  "É a diferença entre um mapa de 2023 e o Google Maps.
   O mapa de 2023 funciona para a maioria das ruas.
   Mas os golpes de hoje não estavam no mapa de 2023."
```

---

## 6 — Sumário Visual: Free vs. Pago em Uma Página

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPEN SOURCE / FREE                           │
│                                                                 │
│  ✓ Aprenda sobre fraudes brasileiras                           │
│  ✓ Faça um TCC, artigo ou protótipo                           │
│  ✓ 4 padrões de fraude básicos                                │
│  ✓ Velocity 24h                                               │
│  ✓ JSONL + CSV                                                │
│  ✓ 100K eventos/mês                                           │
│  ✓ Seed reproduzível                                          │
│                                                                 │
│  ✗ Não vai ao ar em produção com esses dados                  │
│  ✗ Seu modelo vai underperformar (sem velocity completa)       │
│  ✗ Features geográficas não vão aprender nada                 │
│  ✗ Você vai precisar do Pro quando for pra produção           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PRODUTO PAGO                                 │
│                                                                 │
│  ✓ Velocity windows 1h/6h/7d/30d    → modelo funciona de      │
│    verdade                                                      │
│  ✓ Geo clustering por cliente       → geo feature aprende     │
│  ✓ Device consistency               → ATO detectável          │
│  ✓ Impossible travel                → ATO sinal mais forte    │
│  ✓ 11 padrões completos             → cobertura real          │
│  ✓ Multi-label fraud taxonomy       → modelos avançados       │
│  ✓ Grafo de mulas (Team+)           → GNN possível            │
│  ✓ Padrões novos todo mês           → sempre atual            │
│  ✓ Parquet + cloud push + Kafka     → integra com seu stack   │
│  ✓ MCP integration                  → LLM-native              │
│                                                                 │
│  O modelo que você treinar vai detectar fraudes reais.         │
│  Não só parecer que detecta.                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7 — Para Usar em Materiais de Venda

### Argumento central

```
"O open source é real. Funciona. Você pode usar.

 Mas existe uma diferença entre um modelo que foi
 treinado para detectar fraude e um modelo que realmente
 detecta fraude em produção.

 Velocity windows completas. Clustering geográfico real.
 Redes de mulas estruturadas. Padrões atualizados todo mês.

 É isso que separa um modelo de POC de um modelo de produção.
 E é exatamente isso que o plano Pro entrega."
```

### Pergunta de qualificação para vendas

```
"Você está em fase de aprendizado/prototipagem
 ou precisa de um modelo que vai para produção?"

→ Aprendizado: free é suficiente. Boa sorte!
→ Produção: você vai precisar das velocity windows.
  Posso mostrar por quê em 10 minutos?
```
