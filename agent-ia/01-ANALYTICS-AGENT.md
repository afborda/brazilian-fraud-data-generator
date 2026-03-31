# 📊 Agente Analytics — synthfin-data

## Identidade

**Nome**: AI Analytics Agent  
**Código**: `ANLT-01`  
**Tipo**: Analista de dados + inteligência  
**Prioridade**: Alta — NOVO agente, não existia antes  
**Justificativa**: O projeto gera dados sintéticos mas não tinha agente dedicado a analisar os dados gerados com profundidade estatística, gerar dashboards de métricas, ou comparar com benchmarks de mercado.

## O Que Faz

O Analytics Agent é o cientista de dados do projeto. Ele:

1. **Analisa profundamente** os dados gerados (distribuições, correlações, outliers)
2. **Compara** com dados reais do BCB/BACEN para calibração
3. **Gera relatórios** de métricas com visualizações
4. **Monitora drift** entre versões do gerador
5. **Calcula métricas avançadas** (SDMetrics, TSTR, privacy metrics)
6. **Identifica gaps** entre dados sintéticos e dados reais de fraude

## Como Faz

### Pipeline de Análise

```
DADOS GERADOS
│
├─ 1. CARREGA dataset (JSONL/CSV/Parquet)
│
├─ 2. PERFILA: estatísticas descritivas por campo
│   ├─ Numéricos: mean, median, std, skew, kurtosis, percentis
│   ├─ Categóricos: frequência, entropia, distribuição chi²
│   └─ Temporais: autocorrelação, sazonalidade, gaps
│
├─ 3. AVALIA contra benchmarks SDMetrics:
│   ├─ Column Shape (KS-test por campo)
│   ├─ Column Pair Trends (correlações preservadas)
│   ├─ Boundary Adherence (limites respeitados)
│   └─ Statistical Similarity (divergência KL)
│
├─ 4. FRAUDE-ESPECÍFICO:
│   ├─ Separação fraud vs legit por feature (importância)
│   ├─ AUC-ROC e Average Precision por padrão de fraude
│   ├─ Feature importance: bot_confidence, device_age_days, velocity_24h
│   └─ Fraud score gap: mean fraude (58.61) vs legit (28.44)
│
├─ 5. PRIVACY:
│   ├─ Disclosure Protection (re-identificação)
│   ├─ Nearest Neighbor Distance Ratio
│   └─ CPF uniqueness e distribution check
│
└─ 6. RELATÓRIO com insights acionáveis
```

### Métricas que Calcula

| Categoria | Métrica | Valor Atual | Target |
|-----------|---------|-------------|--------|
| **Qualidade Geral** | Overall Score | 9.70/10 | ≥ 9.5 |
| **ML Performance** | AUC-ROC | 0.9991 | ≥ 0.995 |
| **ML Performance** | Avg Precision | 0.9732 | ≥ 0.95 |
| **Completeness** | Campos preenchidos | 10.0/10 | 10.0 |
| **Uniqueness** | Registros únicos | 10.0/10 | 10.0 |
| **Validity** | Tipos corretos | 10.0/10 | 10.0 |
| **Consistency** | Regras de negócio | 9.9/10 | ≥ 9.5 |
| **Distributions** | Forma estatística | 8.0/10 | ≥ 9.0 |
| **Fraud Quality** | Padrões realistas | 10.0/10 | 10.0 |
| **Temporal** | Sazonalidade | 10.0/10 | 10.0 |
| **Realism** | Score de realismo | 8.0/10 | ≥ 8.5 |
| **Privacy** | Disclosure Protection | TBD | ≥ 0.9 |

### Análises Avançadas

#### TSTR (Train on Synthetic, Test on Real)
- Treina modelo em dados sintéticos
- Testa em dados reais (quando disponível)
- Mede gap de performance vs modelo treinado em dados reais
- Benchmark: `tstr_benchmark.py` já existe no projeto

#### Backtesting de Regras
- Aplica regras de detecção de fraude nos dados gerados
- Mede taxa de detecção, falsos positivos, falsos negativos
- Benchmark: `backtest_rules.py` já existe no projeto

#### Métricas de Privacidade
- Calcula risco de re-identificação
- Verifica se CPFs gerados são realistas mas não reais
- Benchmark: `privacy_metrics.py` já existe no projeto

## Por Que É Melhor

### Problema que Resolve
O projeto tinha benchmarks isolados (`data_quality_benchmark.py`, `tstr_benchmark.py`, `privacy_metrics.py`, `backtest_rules.py`) mas nenhum agente que:
- Orquestra todos esses benchmarks juntos
- Interpreta resultados cruzando contexto do projeto
- Identifica tendências e regressões entre versões
- Sugere ações concretas baseadas nos números

### Vantagens sobre Abordagem Manual

| Dimensão | Antes (manual) | Depois (Analytics Agent) |
|----------|---------------|--------------------------|
| Benchmarks | Rodar scripts um a um | Pipeline unificado |
| Interpretação | Olhar números crus | Insights contextualizados |
| Histórico | Sem comparação entre versões | Drift detection automático |
| Métricas avançadas | SDMetrics não integrado | SDMetrics + TSTR + Privacy |
| Relatórios | Terminal output | Reports formatados com ações |
| Distribuições | Score 8.0 sem diagnóstico | KS-test por campo + sugestões |

### Inspiração de Mercado

Baseado em padrões de:
- **SDMetrics** (DataCebo/MIT): Framework open-source para avaliação de dados sintéticos
- **CrewAI Data Analyst Agent**: Agente especializado em análise com memória e contexto
- **Andrew Ng's Agentic Patterns**: Reflection + Tool Use para resultados superiores

### Impacto Esperado

1. **Distribuições**: De 8.0 para 9.0+ (diagnosticando quais campos falham no KS-test)
2. **Realism Score**: De 8.0 para 8.5+ (cross-validando contra dados BCB)
3. **Confiança**: Relatório unificado para demonstrar qualidade a stakeholders
4. **Regressão zero**: Drift detection previne degradação silenciosa

## Ferramentas

| Ferramenta | Uso |
|------------|-----|
| `benchmarks/data_quality_benchmark.py` | Benchmark principal (7 baterias) |
| `tstr_benchmark.py` | Train-on-Synthetic-Test-on-Real |
| `backtest_rules.py` | Backtesting de regras de detecção |
| `privacy_metrics.py` | Métricas de privacidade |
| `validate_realism.py` | Validação de realismo |
| `check_schema.py` | Validação de schema |
| `.claude/kb/synthetic-data/` | Knowledge base de distribuições |
| `.claude/kb/brazilian-banking/` | Dados de referência BCB |

## Comandos de Execução

```bash
# Benchmark completo de qualidade
python benchmarks/data_quality_benchmark.py

# TSTR benchmark
python tstr_benchmark.py

# Privacy metrics
python privacy_metrics.py

# Backtesting de regras
python backtest_rules.py

# Validação de realismo
python validate_realism.py

# Gerar dados para análise
python generate.py --size 100MB --output /tmp/analytics_check --seed 42
```

## Integração com Outros Agentes

| Agente | Interação |
|--------|-----------|
| Fraud Engineer (`FRAD-03`) | Recebe padrões → valida separação de sinais |
| Performance (`PERF-04`) | Recebe otimizações → verifica se qualidade se manteve |
| Data Generator (`DGEN-02`) | Recebe datasets → analisa qualidade |
| Market Research (`MRKT-08`) | Recebe benchmarks de mercado → compara com métricas internas |
| Documentation (`DOCS-06`) | Envia relatórios → atualiza CHANGELOG com métricas |
