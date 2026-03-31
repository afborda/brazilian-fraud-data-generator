# 🧭 IA Agent Norte — Guia Estratégico

## Documento Guia

Este é o **documento norte** do sistema multi-agente do synthfin-data. Define a visão, estratégia e coordenação dos 13 agentes de IA que administram o projeto.

## Visão

> Transformar o synthfin-data no gerador de dados sintéticos de fraude mais completo e confiável do ecossistema financeiro brasileiro, operado por um sistema de agentes de IA que garante qualidade, evolução contínua e competitividade de mercado.

## Os 13 Agentes

| # | Agente | Missão em Uma Frase |
|---|--------|---------------------|
| 0 | [Orquestrador](agent-ia/00-ORQUESTRADOR.md) | Analisa qualquer pedido e roteia para o agente certo |
| 1 | [Analytics Agent](agent-ia/01-ANALYTICS-AGENT.md) | Analisa dados gerados com profundidade estatística (SDMetrics, TSTR, Privacy) |
| 2 | [Data Generator Agent](agent-ia/02-DATA-GENERATOR-AGENT.md) | Administra o pipeline de geração batch + stream |
| 3 | [Fraud Pattern Engineer](agent-ia/03-FRAUD-PATTERN-ENGINEER.md) | Cria e calibra padrões de fraude contra dados BCB reais |
| 4 | [Performance Optimizer](agent-ia/04-PERFORMANCE-OPTIMIZER.md) | Elimina bottlenecks sem degradar qualidade |
| 5 | [Docker & Infra Agent](agent-ia/05-DOCKER-INFRA-AGENT.md) | Containeriza, publica e opera a infraestrutura |
| 6 | [Documentation Keeper](agent-ia/06-DOCUMENTATION-KEEPER.md) | Mantém docs atualizados e versões sincronizadas |
| 7 | [Test Coverage Agent](agent-ia/07-TEST-COVERAGE-AGENT.md) | Sobe cobertura de testes de 15% para 80%+ |
| 8 | [Market Research Agent](agent-ia/08-MARKET-RESEARCH-AGENT.md) | Pesquisa mercado, concorrentes e regulamentação |
| 9 | [Config Architect](agent-ia/09-CONFIG-ARCHITECT.md) | Gerencia os 14 módulos de configuração |
| 10 | [CI/CD Specialist](agent-ia/10-CICD-SPECIALIST.md) | Automatiza quality gates e pipelines |
| 11 | [Explorer Agent](agent-ia/11-EXPLORER-AGENT.md) | Explora codebase (read-only) e faz impact analysis |
| 12 | [Data Quality Analyst](agent-ia/12-DATA-QUALITY-ANALYST.md) | Valida qualidade e bloqueia regressões |

## Princípios de Design

### 1. Especialização > Generalização
Cada agente tem um domínio claro. Um agente não faz o trabalho de outro.

### 2. Orquestração > Acesso Direto
Sempre passe pelo Orquestrador — ele sabe quem é melhor para cada tarefa.

### 3. Qualidade como Gate
NENHUMA mudança é aprovada sem passar pelo Data Quality Analyst.

### 4. Olhar para Fora + para Dentro
Market Research olha para fora (concorrentes, BCB). Os outros olham para dentro (código).

### 5. Medição > Opinião
Todo agente trabalha com NÚMEROS, não impressões. Score, AUC-ROC, cobertura, versão.

## Métricas do Projeto (Baseline - Março 2026)

| Métrica | Valor | Meta | Agente Responsável |
|---------|-------|------|-------------------|
| Quality Score | 9.70/10 | ≥ 9.50 | QUAL-12 |
| AUC-ROC | 0.9991 | ≥ 0.995 | QUAL-12 + ANLT-01 |
| Distribuições | 8.0/10 | ≥ 9.0 | ANLT-01 + CONF-09 |
| Test Coverage | ~15% | ≥ 80% | TEST-07 |
| Version Sync | ❌ Drift | ✅ Sync | DOCS-06 |
| CI Quality Gates | 0 | 7+ gates | CICD-10 |
| Docker Issues | 4 | 0 | DOCK-05 |
| Fraud Types | 36 | 45+ | FRAD-03 + MRKT-08 |

## Roadmap por Agente

### Fase 1: Fundação (Imediato)
- `DOCS-06`: Corrigir version drift (4.9.1 → 4.15.1+)
- `DOCK-05`: Corrigir 4 issues Docker
- `TEST-07`: Sprint 1-2 (CPF + configs = 48 testes)

### Fase 2: Qualidade (Curto prazo)
- `CICD-10`: Implementar quality gates básicos
- `QUAL-12`: Melhorar distribuições 8.0 → 9.0
- `TEST-07`: Sprint 3-5 (generators + exporters = 63 testes)

### Fase 3: Evolução (Médio prazo)
- `MRKT-08`: Pesquisar DREX, PIX NFC, Open Finance
- `FRAD-03`: Implementar novos padrões de fraude
- `PERF-04`: Resolver P2 (WeightCache) e P3 (OOM)
- `ANLT-01`: Integrar SDMetrics e TSTR

### Fase 4: Escala (Longo prazo)
- `MRKT-08`: Benchmark público contra Gretel/SDV
- `DGEN-02`: Modelo generativo (VAE) como alternativa
- `CICD-10`: Auto-release com quality gates
- `TEST-07`: Cobertura 95%+

## Detalhes Completos

Cada agente tem documentação detalhada em [agent-ia/](agent-ia/README.md):
- O que faz (capabilities)
- Como faz (processos, pipelines, algoritmos)
- Por que é melhor (comparação, justificativa, impacto)
- Regras críticas (constraints)
- Integração com outros agentes
- Comandos de execução

---

*Criado: Março 2026 | synthfin-data v4.15.1*
