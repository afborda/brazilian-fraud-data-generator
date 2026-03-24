# Pesquisa de Mercado: Fraudes Financeiras no Brasil e Demanda por Dados Sintéticos
**Data:** 19 de março de 2026
**Escopo:** Padrões de fraude atuais, mercado de dados sintéticos, posicionamento competitivo

---

## Parte 1 — O Tamanho do Problema que Resolvemos

### 1.1 Escala das perdas no Brasil (2024)

O Brasil é hoje o laboratório global de fraude financeira digital. Os números de 2024 confirmam que o problema não está diminuindo — está acelerando.

```
R$ 10,1 bilhões em perdas totais com fraude (2024)
             ▲ 17% em relação a 2023 (R$ 8,6 bi)

R$ 6,5 bilhões somente em fraudes via PIX
             ▲ 80% em relação a 2023

390.000+ notificações de fraude PIX por mês (dezembro 2024)
             ▲ vs 216.000/mês em 2023
             ▲ vs 30.892/mês em 2021 (início do PIX)

28 milhões de brasileiros vítimas de golpe via PIX em 2025 (projeção)

Apenas 7% das perdas são reembolsadas pelas instituições
```

**O que isso significa para o mercado de dados sintéticos:**
Cada real perdido representa uma falha de detecção. Cada falha de detecção é um modelo mal treinado. Cada modelo mal treinado é uma oportunidade de venda de dados melhores.

---

### 1.2 Distribuição dos tipos de fraude (2024)

```
VOLUME DE OCORRÊNCIAS

Cartão de crédito (CNP + clonado)   ████████████████████████  47,9%
PIX e boleto                         ████████████████          32,8%
Phishing (SMS, WhatsApp, email)      ██████████                21,6%

PARTICIPAÇÃO POR CANAL DE PHISHING
SMS                                  ████████████████████████  54%
WhatsApp                             ████████████              27%
Email                                █████████                 19%

ORIGEM DAS PERDAS
Engenharia social                    ██████████████████████████ ~70%
Acesso não autorizado                ██████████                ~20%
Fraude de identidade                 █████                     ~10%
```

---

### 1.3 Os 8 padrões mais relevantes no Brasil hoje

Ordenados por impacto financeiro e relevância para treinamento de modelos:

**1. PIX Fraude (R$ 6,5 bi / ano)**
```
O que é: Vítima realiza transferência PIX para conta fraudulenta.
Subttipos:
  → Engenharia social: vítima é convencida por telefone/WhatsApp
  → Mão fantasma: criminoso assume controle remoto do dispositivo
  → Falso suporte: se passa por banco para "resolver problema"
  → Pix agendado: muda destinatário de transferência legítima
Por que importa para ML: PIX é instantâneo e irreversível.
  Janela de detecção = segundos. Modelos precisam de dados
  com esta urgência temporal simulada corretamente.
```

**2. Conta Tomada — ATO (Account Takeover)**
```
O que é: Criminoso ganha acesso à conta bancária da vítima.
Vetores principais:
  → Vazamento de credenciais + credential stuffing
  → SIM Swap: portabilidade fraudulenta do número de telefone
  → Phishing bancário (site falso)
  → Aplicativo malicioso (RAT: Remote Access Trojan)
Sinal no dado: dispositivo novo + localização nova + alto valor
  + horário incomum + tentativas múltiplas
Por que importa para ML: padrão de maior perda por evento.
  Modelos sem dados de ATO calibrados subestimam este risco.
```

**3. Cartão Clonado / CNP (Card Not Present)**
```
O que é: Dados do cartão copiados ou comprados em dark web.
Vetores:
  → Skimming físico em caixas eletrônicos
  → Vazamento de e-commerce
  → Phishing de dados de cartão
Sinal no dado: MCC incomum + localização distante + valor
  escalado progressivamente (teste → compra grande)
Por que importa para ML: mais comum em volume (47,9% das
  ocorrências). Dataset sem isso é incompleto.
```

**4. Mão Fantasma (Ghost Hand / RAT Fraud)**
```
O que é: Criminoso instala RAT no celular da vítima via
  link malicioso (WhatsApp, SMS, e-mail) e opera o banco
  enquanto a vítima assiste sem perceber.
Características únicas:
  → Dispositivo legítimo da vítima (não detectado por device ID)
  → Sessão com comportamento humano (não bot)
  → Localização correta (GPS do celular da vítima)
  → Porém: velocidade de digitação diferente, sequência
    de telas incomum, horário atípico para o usuário
Por que importa para ML: é o tipo mais difícil de detectar.
  Não existe em nenhum dataset global. Só ocorre no Brasil.
```

**5. Contas Laranja (Mule Account Networks)**
```
O que é: Rede de contas bancárias reais usadas para
  receber, fragmentar e repassar dinheiro de fraude.
Estrutura típica:
  → Orquestrador (raiz da rede)
  → Recrutadores (2-5 por orquestrador)
  → Mulas de primeiro nível (recebem o dinheiro)
  → Mulas de segundo nível (fragmentam em pequenos valores)
  → Destino final (crypto, compras, saques)
Por que importa para ML: detecção de redes de mulas
  requer dados de grafo. GNN (Graph Neural Networks) é
  o estado da arte em fraud detection — e precisa de
  dados com esta estrutura para treinamento.
```

**6. WhatsApp Clone / Impersonação**
```
O que é: Criminoso clona conta WhatsApp e pede dinheiro
  fingindo ser familiar ou amigo.
Características:
  → Vítima nunca tem contato com o banco (sem transação
    bancária anômala — golpe é a vítima mesma que paga)
  → Alta prevalência em pessoas acima de 60 anos
Por que importa para ML: embora a transação pareça legítima,
  há sinais comportamentais: primeiro PIX para aquela chave,
  valor fora do padrão, horário incomum para aquela pessoa.
```

**7. Card Testing (Probe Transactions)**
```
O que é: Criminoso valida lote de dados de cartão roubados
  fazendo micro-transações antes de usar o cartão para
  compras grandes.
Padrão:
  Fase 1: 10-50 transações de R$1-10 em intervalo de 5-15 min
  Silêncio: 24-72 horas (aguarda confirmação)
  Fase 2: transações de R$3.000-15.000
Por que importa para ML: micro-burst de velocidade + pausa
  + escalada de valor é padrão muito específico. Modelos
  treinados sem isso perdem a Fase 2 completamente.
```

**8. Boleto Falso / Substituído**
```
O que é: Vítima paga boleto com código de barras alterado
  para conta do fraudador. Montante idêntico ao legítimo.
Por que é difícil de detectar:
  → Valor idêntico ao esperado pela vítima
  → Horário comercial normal
  → Dispositivo e localização normais
  → Único sinal: destinatário é novo/desconhecido
Por que importa para ML: este padrão tem fraud_score
  baixo em modelos ingênuos. Precisa de features de
  "novo destinatário para este remetente + valor típico"
  calibradas corretamente.
```

---

## Parte 2 — O Que os Modelos de ML Realmente Precisam

### 2.1 Features que mais impactam performance do modelo

Baseado em pesquisa Amazon FDB (2022), IEEE-CIS benchmark e literatura recente (2024-2025):

```
IMPACTO NO AUC DO MODELO (escala 1-10)

Janelas de velocidade (1h/6h/24h/7d/30d)        ██████████  10 — CRÍTICO
  Sem esse feature, modelos não performam
  melhor que random em alguns datasets (Amazon FDB)

Novo beneficiário / destinatário inédito          █████████   9 — CRÍTICO
  Feature mais simples e mais eficaz para PIX

Device fingerprint + device change recency        ████████    8 — ALTO
  Novo device = ATO. Precisa de histórico.

Localização geográfica + clustering por usuário   ████████    8 — ALTO
  Localização aleatória = feature inútil para ML
  Localização clustered = sinal forte

Valor vs. histórico do usuário                    ███████     7 — ALTO
  Anomalia de valor relativa, não absoluta

Horário vs. padrão do usuário                     ███████     7 — ALTO
  Transação às 3h para usuário que nunca transaciona
  à noite

Features de identidade (account age, KYC level)  ██████      6 — MÉDIO
  Conta nova + alto valor = risco elevado

Network/graph features (device compartilhado)    ██████████  10 — CRÍTICO
  Para redes de mulas — estado da arte atual
  Sem grafo, impossível detectar mulas

Behavioral biometrics (typing speed, swipe)      █████       5 — FUTURO
  Ainda emergente, mas empresas como Feedzai
  e SEON já usam em produção
```

### 2.2 A instrução mais importante da pesquisa Amazon

> "Without adding aggregates calculated from the prior history of users,
> modeling techniques cannot perform better than random on some datasets."
>
> — Amazon Science, Fraud Dataset Benchmark (2022)

**Tradução prática:** um dataset de fraude que não tem as janelas de velocidade pré-computadas (transações nas últimas 1h, 6h, 24h, 7 dias) força o cliente a construir essa lógica por conta própria. Se nosso gerador entrega isso como campos prontos, eliminamos semanas de trabalho do cliente e melhoramos diretamente a qualidade do modelo deles.

---

### 2.3 O que os compradores de dados pedem hoje

Baseado em análise de fóruns (Reddit r/MachineLearning, r/datascience, r/FraudPrevention) e artigos técnicos recentes:

```
"Preciso de dados com Brazilian payment rails (PIX, TED, boleto)"
→ Citado em threads sobre fraud ML para mercado BR

"Preciso de velocity features pré-computadas, não quero implementar
 janelas deslizantes no meu pipeline"
→ Mencionado como pain point frequente

"Preciso de dados com ground truth de fraude por tipo, não só
 binário fraud/legit"
→ Multi-label fraud taxonomy — feature diferenciadora

"Preciso de grafo de mulas para treinar GNN"
→ Crescente desde 2023, com adoção de PyG e DGL

"Preciso que o dado seja reproduzível (seed) para que meus
 experimentos sejam replicáveis"
→ Padrão em pesquisa acadêmica e validação de modelo
```

---

## Parte 3 — Análise Competitiva

### 3.1 Quem existe no mercado

```
COMPETIDOR          TIPO           FORÇA               FRAQUEZA CRÍTICA
──────────────────────────────────────────────────────────────────────────
PaySim              Open source    24M records          África (M-Pesa)
                    (Java)         Citado em papers     Sem PIX, sem device
                                   Gratuito             Última atualização 2016
                                                        Sem behavioral features

IEEE-CIS / Vesta    Dataset real   590K transações      E-commerce americano
(Kaggle)            (anonimizado)  431 features         Anonimizado ao ponto
                                   Benchmark clássico   de ser inútil
                                                        Sem contexto BR

Sparkov             Gerador        Simples de usar      Cartão de crédito EUA
(Python)            sintético      Gratuito             Sem social engineering
                                                        Sem comportamento temporal

Gretel.ai           Plataforma     Enterprise-grade     Genérico (aprendizado
                    comercial      GDPR/LGPD compliance estatístico, não semântico)
                    $$$            Integração AWS/GCP   Não tem PIX/CPF
                                                        Não simula padrões BR

MOSTLY AI           Plataforma     Forte em bancos EU   Focado em privacidade,
                    comercial      Casos publicados     não em fraude
                    $$$            Certificações        Não tem padrões BR
                                   compliance

SDV / CTGAN         Lib Python     Open source          Precisa de dados REAIS
                    (genérico)     Fácil de usar        como input
                                                        Sem semântica de fraude
                                                        Distribui estatística,
                                                        não comportamento

Amazon FDB          Benchmark      9 datasets reais     Somente leitura
                    (pesquisa)     API padronizada      Não é gerador
                                                        Sem dados brasileiros
```

### 3.2 O gap de mercado

```
                    PaySim  IEEE-CIS  Gretel  MOSTLY  Sparkov  SynthFin
────────────────────────────────────────────────────────────────────────
PIX nativo            ✗       ✗        ✗       ✗        ✗        ✓
CPF/CNPJ válido       ✗       ✗        ✗       ✗        ✗        ✓
Bancos BR (ISPB)      ✗       ✗        ✗       ✗        ✗        ✓
Taxonomia BR          ✗       ✗        ✗       ✗        ✗        ✓
Velocity windows      ✗       ✗        ✗       ✗        ✗        PARCIAL
11 padrões fraude     ✗       ✗        ✗       ✗        ✗        ✓
17 sinais de risco    ✗       ✗        ✗       ✗        ✗        ✓
Sazonalidade BR       ✗       ✗        ✗       ✗        ✗        ✓
Reprodutível (seed)   ✗       ✓        ✗       ✗        ✗        ✓
Multi-formato         ✗       ✗        ✓       ✓        ✗        ✓
Grafo de mulas        ✗       ✗        ✗       ✗        ✗        PLANEJADO
Preço                FREE    FREE     $$$     $$$      FREE      SaaS
```

**Conclusão da análise competitiva:**
Não existe nenhum produto que gera dados sintéticos de fraude com contexto brasileiro. O gap é total, não parcial. A janela de oportunidade é real e os dados de perdas (R$10,1 bi em 2024) validam que há budget disponível no mercado.

---

## Parte 4 — Gaps Identificados no Nosso Produto

### 4.1 O que temos hoje (estado real em 19/03/2026)

```
IMPLEMENTADO E FUNCIONANDO
──────────────────────────
✓ 11 padrões de fraude bancária
✓ 7 padrões de fraude em ride-share
✓ 17 sinais de risco pré-computados
✓ Sazonalidade temporal (picos 12h, 18h, 21h)
✓ Dia da semana e feriados brasileiros
✓ 7 perfis comportamentais por cliente
✓ PIX com tipos de chave (CPF, CNPJ, email, telefone, aleatória)
✓ Parâmetros de fraude por tipo (fraud_rate)
✓ Formatos: JSONL, CSV, Parquet, Arrow, DB, S3/MinIO
✓ Compressão: gzip, zstd, snappy, brotli
✓ CLI com ~30 flags
✓ Reproducibilidade por seed
✓ Streaming (stdout, Kafka, webhook)
✓ MCC codes com distribuição brasileira
✓ Códigos ISPB de bancos reais
```

```
PARCIALMENTE IMPLEMENTADO
──────────────────────────
◐ Clustering geográfico (planejado Turno 2 — parcial)
◐ Consistência de dispositivo por cliente (Turno 4 — parcial)
◐ Clustering de merchant por cliente (Turno 4 — parcial)
◐ Velocity window 24h (existe, mas não 1h/6h/7d/30d)
◐ Fraud ring ID (campo existe, mas sem estrutura de grafo real)
```

```
NÃO IMPLEMENTADO (alto impacto)
──────────────────────────────
✗ Velocity windows completas (1h / 6h / 7d / 30d)
✗ Impossible travel (São Paulo 14h → Miami 14h05)
✗ Estrutura de grafo de mulas (orquestrador → recrutador → mula)
✗ Latência de fraude (2-7 dias entre comprometimento e uso)
✗ Bot/automação patterns (zero intervalo humano entre transações)
✗ Mão fantasma (RAT fraud — dispositivo legítimo, comportamento anômalo)
✗ 50+ padrões descobertos na pesquisa de fraudes
✗ Multi-label fraud taxonomy (ATO + mula + SE na mesma cadeia)
✗ Behavioral biometrics (typing speed, swipe patterns)
```

### 4.2 Prioridade de implementação por impacto em vendas

```
PRIORIDADE 1 — Bloqueia venda para times de ML (fazer agora)
─────────────────────────────────────────────────────────────
① Velocity windows completas (1h/6h/7d/30d)
   Impacto: sem isso, modelos do cliente underperformam
   Esforço: ~3 dias
   Diferencial de mercado: NENHUM concorrente entrega isso pronto

② Clustering geográfico por cliente (3-5 localizações fixas)
   Impacto: geolocalização aleatória = feature inútil para ML
   Esforço: ~1 semana
   Diferencial: elimina o maior ruído nos dados geográficos

PRIORIDADE 2 — Aumenta ticket médio (próximas 4-8 semanas)
───────────────────────────────────────────────────────────
③ Impossible travel injection
   Impacto: sinal mais forte para ATO — muito pedido
   Esforço: ~3 dias

④ Estrutura de grafo de mulas
   Impacto: GNN fraud detection é o estado da arte atual
   Esforço: ~2 semanas
   Diferencial: NENHUM dataset público tem isso para BR

⑤ Multi-label fraud taxonomy
   Impacto: clientes de pesquisa precisam de labels granulares
   Esforço: ~1 semana

PRIORIDADE 3 — Feature para plano enterprise (2-3 meses)
─────────────────────────────────────────────────────────
⑥ Latência de fraude (tempo entre roubo de credencial e uso)
⑦ Bot/automação patterns
⑧ Behavioral biometrics simulados
⑨ Mão fantasma (RAT fraud pattern)
```

---

## Parte 5 — Fontes e Referências

```
PERDAS E ESTATÍSTICAS
• Poder360: "Golpes causaram prejuízo de R$ 10,1 bi em 2024"
• CNN Brasil: "Perdas com fraudes no PIX crescem 70% em 2024"
• ISTOE Dinheiro: "Fraudes no PIX disparam acima de 390 mil/mês"
• TI Inside: "Golpes via Pix somam 28 milhões de casos em 2025"
• Banco Central do Brasil: dados de notificações de fraude PIX
• Febraban: Pesquisa de Tecnologia Bancária 2024

TAXONOMIA E PADRÕES
• arXiv 2511.20902: "A Taxonomy of Pix Fraud in Brazil" (nov/2024)
• IronVest: "Brazilian Banks: Stopping Social Engineering Scams"
• QED Investors: "Brazil as a global testbed for financial crime"

ML E DADOS SINTÉTICOS
• Amazon Science / arXiv 2208.14417: "Fraud Dataset Benchmark"
• IEEE-CIS Fraud Detection (Kaggle competition)
• MDPI Technologies 13(4):141 — Synthetic Data for Fraud Detection
• Preprints.org 202502.0278 — AI-Powered Fraud Detection
• SDV / CTGAN GitHub: github.com/sdv-dev/SDV
• PaySim: github.com/EdgarLopezPhD/PaySim
• Amazon FDB: github.com/amazon-science/fraud-dataset-benchmark

COMPETIDORES
• Gretel.ai: gretel.ai
• MOSTLY AI: mostly.ai
• Hazy: hazy.com
• YData: ydata.ai
```
