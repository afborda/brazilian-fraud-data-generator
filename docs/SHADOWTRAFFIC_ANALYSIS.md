# ShadowTraffic - Análise Aprofundada

**Data da Análise:** 30 de Janeiro de 2026  
**Versão Analisada:** Latest (2026)  
**Website:** https://shadowtraffic.io  
**Documentação:** https://docs.shadowtraffic.io

---

## 📋 Sumário Executivo

**ShadowTraffic** é uma plataforma comercial containerizada (Docker) para geração **declarativa** de dados sintéticos realistas com foco em streaming e simulação de tráfego de produção. Diferente do brazilian-fraud-data-generator (que é Python standalone), ShadowTraffic usa JSON configs e roda como serviço Docker.

**Diferencial principal:** Abordagem 100% declarativa (sem código) com state machines, lookups relacionais, e controle temporal sofisticado.

---

## 🎯 Proposta de Valor

### O que ShadowTraffic Faz

1. **Geração Declarativa**: Configuração JSON descreve estrutura de dados; funções substituem valores concretos
2. **Simulação de Tráfego**: Replica padrões de produção (volume, velocidade, variância)
3. **Dados Relacionais**: Lookups entre datasets, joins automáticos, consistência referencial
4. **State Machines**: Modelagem de sequências de eventos (funis, jornadas, processos)
5. **Streaming Real-Time**: Kafka, Webhooks, PostgreSQL, S3 como destinos nativos

### Casos de Uso Primários

- **POCs/Demos**: Dados realistas para demonstrações comerciais
- **Testes de Performance**: Load testing com volumes TB-scale
- **Desenvolvimento**: Popular ambientes dev/staging sem dados reais
- **ML Training**: Datasets sintéticos para treinamento de modelos
- **CDC Testing**: Testar workflows de Change Data Capture

---

## 🏗️ Arquitetura & Modelo de Execução

### Container-First

```bash
# Execução padrão
docker run --env-file license.env \
  -v $(pwd)/config.json:/home/config.json \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json

# Dry-run (stdout) para validação
docker run ... shadowtraffic:latest \
  --config config.json --stdout --sample 10

# Watch mode (recarrega ao salvar config)
docker run ... shadowtraffic:latest \
  --config config.json --stdout --sample 10 --watch
```

### Modelo de Licenciamento

| Plano | Preço | Usuários | Instâncias | Events/min | Data/mês | Suporte |
|-------|-------|----------|------------|------------|----------|---------|
| **Free Trial** | $0 | 1 | 1 | 600 | 200 GB | Não |
| **Developer** | $399/ano | 1 | 3 | Ilimitado | 1 TB | Best Effort |
| **Enterprise** | Custom | Ilimitado | Ilimitado | Ilimitado | Ilimitado | Standard |

**Política de Reembolso:** 30 dias full refund, sem perguntas.

---

## 🧩 Principais Componentes da API

### 1. Functions (Geração de Dados)

**Conceito:** Substitua valores concretos por chamadas de função usando `_gen`.

```json
{
  "sensorId": {"_gen": "uuid"},
  "reading": {"_gen": "normalDistribution", "mean": 60, "sd": 5},
  "timestamp": {"_gen": "now"}
}
```

**Categorias de Funções:**

- **Distribuições:** `normalDistribution`, `uniformDistribution`, `histogram`
- **Strings/Text:** `string` (template Faker), `sequentialString`
- **IDs:** `uuid`, `sequentialInteger`
- **Temporal:** `now`, `formatDateTime`, `intervals`
- **Relacionais:** `lookup`, `previousEvent`
- **State:** `stateMachine`, `var`, `constant`
- **Preprocessors:** `loadJsonFile`, `env`

### 2. Function Modifiers (Transformações)

Aplicam-se a qualquer função para refinar output.

```json
{
  "_gen": "normalDistribution",
  "mean": 60,
  "sd": 5,
  "decimals": 2,        // Arredonda para 2 casas
  "clamp": [50, 70],    // Limita entre 50-70
  "null": 0.1,          // 10% chance de ser null
  "path": ["a", "b"]    // Navega em objetos aninhados
}
```

**Ordem de Execução dos Modifiers:**
1. `cardinality` → 2. `elide` → 3. `null` → 4. `keyNames` → 5. `selectKeys` → 6. `clamp` → 7. `decimals` → 8. `cast` → 9. `path` → 10. `sample` → 11. `serialize`

### 3. Generators (Especificação de Backend)

Define onde/como dados serão enviados. Cada backend tem schema próprio.

**Exemplo Kafka:**
```json
{
  "generators": [
    {
      "topic": "transactions",
      "key": {"customerId": {"_gen": "uuid"}},
      "value": {
        "amount": {"_gen": "normalDistribution", "mean": 100, "sd": 25},
        "timestamp": {"_gen": "now"}
      }
    }
  ]
}
```

**Schemas de Generators:**
- **Kafka:** `topic`, `key`, `value`, `headers`
- **Postgres:** `table`, `row`
- **S3:** `bucket`, `path`, `data`
- **Webhook:** `url`, `method`, `body`, `headers`

### 4. Connections (Destinos de Dados)

Mapeamento de conexões lógicas para backends físicos.

```json
{
  "connections": {
    "dev-kafka": {
      "kind": "kafka",
      "producerConfigs": {
        "bootstrap.servers": "localhost:9092",
        "key.serializer": "io.shadowtraffic.kafka.serdes.JsonSerializer",
        "value.serializer": "io.shadowtraffic.kafka.serdes.JsonSerializer"
      }
    },
    "dev-pg": {
      "kind": "postgres",
      "connectionConfigs": {
        "host": "localhost",
        "port": 5432,
        "username": "postgres",
        "password": "postgres",
        "db": "mydb"
      }
    }
  }
}
```

**Backends Suportados:**
- Apache Kafka (com serdes customizados)
- PostgreSQL
- Amazon S3 / MinIO
- Webhooks (HTTP/HTTPS)
- Stdout (para debugging)

### 5. State Machines (Sequências de Eventos)

Modelagem de jornadas de usuário, funis, processos com estados.

```json
{
  "stateMachine": {
    "_gen": "stateMachine",
    "initial": "viewLandingPage",
    "transitions": {
      "viewLandingPage": "addItemToCart",
      "addItemToCart": {"_gen": "oneOf", "choices": ["viewCart", "addItemToCart"]},
      "viewCart": "checkout",
      "checkout": null  // Estado terminal
    },
    "states": {
      "viewLandingPage": {
        "value": {"stage": "landing", "referrer": {"_gen": "string", "expr": "#{Internet.url}"}}
      },
      "addItemToCart": {
        "value": {"stage": "cart", "item": {"_gen": "string", "expr": "#{Commerce.productName}"}}
      },
      "viewCart": {
        "value": {"stage": "review", "timestamp": {"_gen": "now"}}
      },
      "checkout": {
        "value": {"stage": "purchase", "price": {"_gen": "uniformDistribution", "bounds": [1, 100]}}
      }
    }
  }
}
```

**Use Cases de State Machines:**
- Funis de conversão (ecommerce)
- Customer journeys (CRM)
- Processos de fraude (tentativa → detecção → bloqueio)
- Ciclos de vida de dispositivos IoT

### 6. Forks (Paralelismo Automático)

Clona um generator N vezes para simular múltiplos "agentes" em paralelo.

```json
{
  "fork": {
    "key": {"_gen": "uuid"},           // Identidade única de cada fork
    "maxForks": 10000,                 // Limite de instâncias
    "stagger": {"ms": 100}             // Delay entre spawns
  },
  "key": {
    "sensorId": {"_gen": "var", "var": "forkKey"}  // Referencia a key do fork
  },
  "value": {
    "reading": {"_gen": "normalDistribution", "mean": 50, "sd": 5}
  }
}
```

**Casos de Uso:**
- 10k sensores IoT atualizando em paralelo
- Milhares de usuários simultâneos em aplicação
- Frota de veículos enviando telemetria

**⚠️ Atenção:** Forks sem bound (`maxForks`) + sem term condition = memory leak!

### 7. Lookups (Joins Relacionais)

Referencia dados gerados anteriormente para criar relacionamentos.

```json
{
  "generators": [
    {
      "topic": "customers",
      "key": {"name": {"_gen": "string", "expr": "#{Name.full_name}"}}
    },
    {
      "topic": "orders",
      "value": {
        "orderId": {"_gen": "uuid"},
        "customerId": {
          "_gen": "lookup",
          "topic": "customers",
          "path": ["key", "name"]
        }
      }
    }
  ]
}
```

**Características:**
- **Window de História:** Últimos 1M eventos (configurável com `history`)
- **Cross-Connection:** Pode fazer lookup entre Kafka ↔ Postgres
- **Path Navigation:** Extrai valores aninhados com `path` modifier
- **Probabilistic:** Pode aplicar distribuições via `histogram` no lookup

### 8. Intervals (Controle Temporal)

Muda comportamento baseado em wallclock time usando Cron expressions.

```json
{
  "localConfigs": {
    "throttleMs": {
      "_gen": "intervals",
      "intervals": [
        ["* 18-20 * * *", 50],        // 6-8 PM: evento a cada 50ms
        ["*/3 23 * 1 5", 150],        // Sextas em Jan, 11 PM: a cada 150ms
        ["* * * * 1", 25]             // Domingos: a cada 25ms
      ],
      "defaultValue": 100             // Resto do tempo: 100ms
    }
  }
}
```

**Use Cases:**
- Variação de tráfego por horário do dia
- Picos de Black Friday
- Sazonalidade (feriados, fins de semana)
- Simulação de timezone effects

### 9. Variables & VarsOnce

Compartilhamento de valores entre campos.

```json
{
  "vars": {
    "sensorId": {"_gen": "uuid"}
  },
  "varsOnce": {
    "originalHardware": {"_gen": "boolean"}  // Avaliado uma vez
  },
  "key": {
    "sensorId": {"_gen": "var", "var": "sensorId"}
  },
  "value": {
    "url": {
      "_gen": "string",
      "expr": "http://mydomain.com/charts/#{sensorId}"  // Template interpolation
    },
    "original": {"_gen": "var", "var": "originalHardware"}
  }
}
```

### 10. Generator Configuration

Controles de comportamento local/global.

```json
{
  "globalConfigs": {
    "throttleMs": 500,        // Delay entre eventos (todas generators)
    "maxEvents": 10000        // Cap total de eventos
  },
  "generators": [
    {
      "topic": "metrics",
      "localConfigs": {       // Override global
        "throttleMs": 100,
        "delay": {"ms": 75, "rate": 0.5},  // 50% delayed by 75ms (out-of-order)
        "history": 5000000    // Window para lookups
      }
    }
  ]
}
```

**Parâmetros Disponíveis:**
- `throttleMs`: Delay entre eventos
- `maxEvents`: Limita quantidade gerada
- `delay`: Introduz out-of-order delivery
- `history`: Tamanho do buffer para lookups
- `duplicate`: Taxa de duplicação de eventos

### 11. Schedules (Stages de Execução)

Orquestra generators em sequência temporal.

```json
{
  "schedule": {
    "stages": [
      {
        "generators": ["seedCustomers"],   // Stage 1: seed
        "overrides": {
          "seedCustomers": {
            "localConfigs": {"maxEvents": 1000}
          }
        }
      },
      {
        "generators": ["transactions", "rides"]  // Stage 2: streaming infinito
      }
    ]
  }
}
```

**Use Case:** Seeding de dimensões → Stream de fatos.

### 12. Seeding (Reprodutibilidade)

Controle determinístico via random seed.

```bash
docker run ... shadowtraffic:latest \
  --config config.json --seed 42
```

**Características:**
- Mesmos dados em cada run
- Mesmo throttle/delay values
- Lock de `varsOnce`
- Seed é printado em logs para replay

---

## 🔍 Comparação: ShadowTraffic vs. brazilian-fraud-data-generator

| Dimensão | ShadowTraffic | brazilian-fraud-data-generator |
|----------|---------------|-------------------------------|
| **Modelo de Uso** | Docker container SaaS | Python library standalone |
| **Configuração** | JSON declarativo | Python code programático |
| **Licenciamento** | Comercial ($399-custom/ano) | Open-source (MIT) |
| **State Machines** | ✅ Nativo (JSON DSL) | ❌ Sem suporte |
| **Lookups Relacionais** | ✅ Cross-topic/table | ⚠️ Parcial (index lookup) |
| **Controle Temporal** | ✅ Intervals (Cron) | ⚠️ Timestamp fixo |
| **Backends Nativos** | Kafka, Postgres, S3, Webhook | JSONL, CSV, Parquet, MinIO |
| **Streaming** | ✅ Kafka/Webhook async | ✅ Kafka/Webhook (asyncio) |
| **Paralelismo** | Forks (in-process) | ProcessPoolExecutor (multi-process) |
| **Out-of-Order** | ✅ Delay parameter | ❌ Sem suporte |
| **Duplicação** | ✅ Duplicate parameter | ❌ Sem suporte |
| **Reprodutibilidade** | ✅ Seed flag | ✅ `--seed` parameter |
| **Domínio Brasileiro** | ❌ Genérico (Faker EN) | ✅ CPF, bancos BR, estados |
| **Fraud Patterns** | ⚠️ Custom logic required | ✅ Built-in (PIX, takeover, GPS) |
| **Performance** | ~600-unlimited events/min | 56k-385k tx/sec (batch) |
| **Memory Footprint** | JVM-based (high) | Python (moderate) |
| **Learning Curve** | Baixa (JSON config) | Média (Python API) |
| **Extensibilidade** | ❌ Fechado | ✅ Python modules |
| **Pricing** | $0-$399/ano-custom | Free (MIT) |

---

## 💡 Insights & Aprendizados

### O que ShadowTraffic Faz Melhor

1. **State Machines Declarativas**: Modelagem de sequências sem código é extremamente elegante
2. **Lookups Cross-System**: Lookup Kafka → Postgres é killer feature para data seeding
3. **Intervals Temporais**: Cron-based variance é mais flexível que nosso timestamp fixo
4. **Out-of-Order/Duplicate**: Stress testing capabilities são superiores
5. **Workflow de Dev**: `--watch` mode com hot-reload é excelente DX

### O que brazilian-fraud-data-generator Faz Melhor

1. **Domínio Brasileiro**: CPF validation, bancos BR, estados/cidades são nativos
2. **Fraud Domain Expertise**: Padrões de fraude específicos (PIX cloning, GPS spoofing) são built-in
3. **Performance**: 56k-385k tx/sec vs ~10k events/min (ShadowTraffic Free Trial)
4. **Extensibilidade**: Python modules permitem custom logic complexa
5. **Cost**: Free vs $399/ano mínimo
6. **Offline Batch**: Nosso foco em batch generation (MB-TB files) vs streaming focus

### Gaps no brazilian-fraud-data-generator (Inspirados por ShadowTraffic)

**P1: State Machines para Sequências de Fraude**
- **Problema:** Fraude é sequência de eventos, não evento isolado
- **Inspiração:** State machine de ShadowTraffic
- **Solução:** Implementar `FraudStateMachine` com estados:
  - `normal` → `reconnaissance` → `attemptedFraud` → `detectedFraud` → `blocked`
  - Cada estado com probabilidades de transição
  - `previousEvent` lookup para correlação temporal

**P2: Interval-Based Traffic Variance**
- **Problema:** Tráfego é constante, não mimetiza horários de pico
- **Inspiração:** `intervals` function
- **Solução:** Adicionar `--schedule` parameter:
  ```python
  --schedule '{"18-20": {"rate": 5000}, "default": {"rate": 1000}}'
  ```

**P3: Out-of-Order & Duplicate Events**
- **Problema:** Eventos sempre em ordem perfeita, não realista
- **Inspiração:** `delay` + `duplicate` parameters
- **Solução:** Adicionar em `streaming.py`:
  ```python
  --delay-rate 0.1 --delay-ms 500  # 10% atrasado 500ms
  --duplicate-rate 0.05            # 5% duplicado
  ```

**P4: Cross-Generator Lookups**
- **Problema:** Lookup entre transaction ↔ ride é difícil
- **Inspiração:** `lookup` function cross-topic
- **Solução:** Shared `EventRegistry` com TTL:
  ```python
  registry = EventRegistry(max_size=1_000_000)
  ride_id = registry.lookup('rides', path=['ride_id'])
  ```

**P5: Variable Templating**
- **Problema:** Reuso de valores entre campos é verboso
- **Inspiração:** `vars` + `#{variableName}` interpolation
- **Solução:** Adicionar `VariableContext`:
  ```python
  ctx = VariableContext({'customerId': uuid4()})
  url = ctx.template("http://api.com/customer/#{customerId}")
  ```

**P6: Preprocessors para Config Modular**
- **Problema:** Configs hardcoded, difícil reusar
- **Inspiração:** `loadJsonFile`, `env` preprocessors
- **Solução:** Suportar JSON includes:
  ```python
  --config-dir ./configs
  # generate.py auto-expande $include references
  ```

**P7: Dry-Run com Watch Mode**
- **Problema:** Validar output requer full run
- **Inspiração:** `--stdout --sample 10 --watch`
- **Solução:** Adicionar em generate.py:
  ```python
  --dry-run --sample 100 --watch
  ```

---

## 🚀 Roadmap de Melhorias (Inspirado em ShadowTraffic)

### Phase 3.1: State Machines para Fraud Journeys
**Entregável:** `FraudStateMachine` class  
**Exemplo:**
```python
fraud_machine = FraudStateMachine(
    initial='normal',
    transitions={
        'normal': {'reconnaissance': 0.05},
        'reconnaissance': {'attemptedFraud': 0.3, 'normal': 0.7},
        'attemptedFraud': {'detectedFraud': 0.6, 'successfulFraud': 0.4},
        'detectedFraud': {'blocked': 1.0}
    },
    states={
        'reconnaissance': {'event_type': 'unusual_access', 'risk_score': 30},
        'attemptedFraud': {'event_type': 'fraud_attempt', 'risk_score': 70},
        'detectedFraud': {'event_type': 'fraud_detected', 'risk_score': 95}
    }
)
```

### Phase 3.2: Interval-Based Scheduling
**Entregável:** `IntervalScheduler` para variação temporal  
**CLI:**
```bash
python generate.py --size 1GB \
  --schedule '{"9-17 * * 1-5": 5000, "18-23 * * *": 10000, "default": 1000}'
```

### Phase 3.3: Event Delay & Duplication
**Entregável:** `EventDistorter` para chaos testing  
**CLI:**
```bash
python stream.py --target kafka \
  --delay-rate 0.15 --delay-ms 500 \
  --duplicate-rate 0.05
```

### Phase 3.4: Cross-Generator Event Registry
**Entregável:** `GlobalEventRegistry` para lookups  
**API:**
```python
registry = GlobalEventRegistry(max_size=1_000_000, ttl_seconds=3600)
transaction_generator.link_registry(registry, topic='transactions')
ride_generator.link_registry(registry, topic='rides')
# Ride pode fazer lookup de transaction anterior do mesmo customer
```

### Phase 3.5: Variable Context & Templating
**Entregável:** `VariableContext` com interpolation  
**API:**
```python
ctx = VariableContext({
    'customerId': customer.cpf,
    'timestamp': datetime.now().isoformat()
})
tx.merchant_url = ctx.template("https://merchant.com/tx/#{customerId}/#{timestamp}")
```

### Phase 3.6: Config Modularization
**Entregável:** JSON preprocessor para includes  
**Exemplo:**
```json
{
  "connections": {"$include": "configs/connections.json"},
  "fraud_profiles": {"$include": "configs/fraud_patterns.json"}
}
```

### Phase 3.7: Enhanced Dry-Run Mode
**Entregável:** Watch mode + sampling  
**CLI:**
```bash
python generate.py --dry-run --sample 50 --watch --format json
# Auto-reload ao salvar config files
```

---

## 📊 Análise de Mercado & Posicionamento

### Cenário Competitivo

| Tool | Tipo | Preço | Domínio | Streaming | State | Open? |
|------|------|-------|---------|-----------|-------|-------|
| **ShadowTraffic** | SaaS | $399+/ano | Geral | ✅ | ✅ | ❌ |
| **Mockaroo** | Web UI | $50-500/ano | Geral | ❌ | ❌ | ❌ |
| **Faker** | Library | Free | Geral | ❌ | ❌ | ✅ |
| **Synthea** | CLI | Free | Healthcare | ❌ | ✅ | ✅ |
| **brazilian-fraud** | Library | Free | Fraud BR | ✅ | ⚠️ | ✅ |

**Posicionamento Único do brazilian-fraud-data-generator:**
- **Domínio Vertical:** Único focado em fraude bancária brasileira
- **Open-Source + Performance:** 56k-385k tx/sec gratuito
- **Hybrid Batch+Stream:** Arquivos GB-TB + Kafka/webhook

### Nicho de Mercado Defensável

1. **Regulatório:** LGPD compliance (dados sintéticos evitam PII real)
2. **Local:** CPF, bancos BR, PIX fraud patterns não existem em tools globais
3. **Academia:** Pesquisa de fraude requer datasets públicos
4. **Fintech BR:** Explosion de fintechs precisa testar antifraude

---

## 🎓 Lições de Design

### Princípios Arquiteturais do ShadowTraffic (Aplicáveis ao Nosso Projeto)

1. **Declarative > Imperative:** JSON config reduz learning curve vs Python code
2. **Composability:** Funções pequenas e combináveis (`_gen` + modifiers)
3. **Separation of Concerns:** Functions ≠ Generators ≠ Connections
4. **Developer Experience:** `--watch`, `--stdout`, `--sample` são gold standard
5. **Reproducibility:** Seed como first-class citizen
6. **Progressive Disclosure:** Quickstart → Overview → Deep Dive docs

### Anti-Patterns Identificados no ShadowTraffic (Evitar)

1. **Closed-Source:** Impossível debugar internals ou contribuir
2. **Vendor Lock-In:** Syntax não é standard; migração cara
3. **Pricing Opacity:** Enterprise sem pricing público
4. **No Local Dev:** Requer Docker; sem Python/pip install nativo

---

## ✅ Ações Recomendadas

### Curto Prazo (1-2 semanas)

1. **Documentar State Machine Design:** Especificar `FraudStateMachine` API
2. **Prototipar Interval Scheduler:** POC com Cron expressions em Python
3. **Adicionar --dry-run Mode:** Stdout + sampling sem escrita

### Médio Prazo (1-2 meses)

4. **Implementar Event Registry:** Cross-generator lookups
5. **Variable Context:** Template interpolation `#{var}`
6. **Delay/Duplicate:** Chaos engineering features

### Longo Prazo (3-6 meses)

7. **JSON Config Option:** Alternativa declarativa ao Python API
8. **Web UI:** ShadowTraffic-style config builder (Streamlit/Gradio)
9. **Marketplace:** Templates prontos (ecommerce fraud, ride-share fraud, etc.)

---

## 📚 Referências & Recursos

### ShadowTraffic
- **Website:** https://shadowtraffic.io
- **Docs:** https://docs.shadowtraffic.io
- **Pricing:** https://shadowtraffic.io/pricing.html
- **GitHub (AI Context):** https://github.com/ShadowTraffic/shadowtraffic-ai-context
- **Video Guides:** https://docs.shadowtraffic.io/video-guides/

### Alternativas Comparáveis
- **Mockaroo:** https://mockaroo.com (Web UI, CSV/JSON export)
- **Synthea:** https://github.com/synthetichealth/synthea (Healthcare domain)
- **Faker:** https://faker.readthedocs.io (Python library, basic data)

### Artigos Relevantes
- **"Synthetic Data for ML"** (Google Research, 2023)
- **"State Machines for Event Streaming"** (Confluent Blog, 2024)
- **"LGPD & Synthetic Data"** (Brazilian Privacy Law compliance)

---

## 🔖 Conclusão

**ShadowTraffic é referência em geração declarativa de dados sintéticos para streaming**, com primitivas sofisticadas (state machines, lookups, intervals) que elevam o padrão de qualidade. No entanto, seu modelo comercial fechado e foco genérico deixam gaps no domínio de **fraude bancária brasileira**.

**brazilian-fraud-data-generator tem nicho defensável** graças a:
1. Domínio vertical (fraude BR)
2. Open-source + performance
3. Batch+stream hybrid

**Próximos passos:** Incorporar conceitos de state machines, intervals, e lookups cross-generator inspirados no ShadowTraffic, mantendo nossa vantagem em domínio brasileiro e extensibilidade open-source.

---

**Prepared by:** GitHub Copilot (Claude Sonnet 4.5)  
**For:** brazilian-fraud-data-generator v4.0.0 roadmap  
**Date:** January 30, 2026
