# Análise de Gaps, Erros e Melhorias — synthfin-data v4.9.1

> **Data**: 2026-03-25  
> **Escopo**: Análise completa do código-fonte, testes, configuração, Docker e documentação  
> **Método**: Revisão estática de todos os módulos em `src/fraud_generator/`

---

## Sumário Executivo

A análise identificou **8 problemas críticos**, **12 problemas maiores** e **15 melhorias sugeridas** distribuídos em 15 módulos do projeto. As categorias mais afetadas são: segurança Docker, thread-safety, eficiência de memória e gaps de testes.

---

## 🔴 Problemas Críticos (Ação Imediata)

### C1. Chave de Verificação Exposta no Docker Image

**Arquivo**: `Dockerfile` (linhas 26 e 38)  
**Problema**: `ARG FRAUDGEN_VERIFY_KEY="CHANGE_THIS_IN_PRODUCTION_BUILD_ARG"` é promovido a `ENV`, ficando visível via `docker inspect`.  
**Impacto**: Qualquer pessoa com acesso à imagem pode extrair a chave de verificação de licença.  
**Correção**: Usar Docker BuildKit `--secret` ou runtime-only env var (nunca ARG→ENV para segredos).

```dockerfile
# ANTES (inseguro)
ARG FRAUDGEN_VERIFY_KEY="CHANGE_THIS_IN_PRODUCTION_BUILD_ARG"
ENV FRAUDGEN_VERIFY_KEY=${FRAUDGEN_VERIFY_KEY}

# DEPOIS (seguro)
# Remover ARG e ENV; passar como runtime: docker run -e FRAUDGEN_VERIFY_KEY=...
```

### C2. Ring Registry Não É Thread-Safe

**Arquivo**: `src/fraud_generator/generators/transaction.py` (linha 162)  
**Problema**: `_ring_registry = _RingRegistry()` é um singleton por processo com mutações em `dict` e incremento de counter sem locks.  
**Impacto**: Seguro no modelo atual (multiprocessing fork), mas quebrará silenciosamente se threads forem usadas (ex: API server).  
**Correção**: Adicionar `threading.Lock` ou passar registry como parâmetro injetado.

### C3. Parquet Append Lê Arquivo Inteiro na Memória

**Arquivo**: `src/fraud_generator/exporters/parquet_exporter.py` (linhas 148-151)  
**Problema**: `pq.read_table(output_path)` carrega o arquivo existente inteiro + `concat_tables` cria cópia adicional.  
**Impacto**: OOM para arquivos >1GB com appends repetidos (pico = 3× tamanho do arquivo).  
**Correção**: Usar `ParquetWriter` com row groups em modo append (já implementado em `export_stream()`).

### C4. Separadores Inconsistentes no Flattening

**Arquivo**: `src/fraud_generator/exporters/csv_exporter.py` vs `parquet_exporter.py`  
**Problema**: CSV usa `.` como separador para campos aninhados, Parquet usa `_`.  
**Impacto**: Downstream consumers recebem schemas diferentes dependendo do formato de export.  
**Correção**: Padronizar para `_` (mais compatível com SQL e Parquet schemas).

### C5. Docker Roda como Root

**Arquivo**: `Dockerfile`  
**Problema**: Nenhuma diretiva `USER` — container roda como root.  
**Impacto**: Se container for comprometido, atacante tem root no filesystem.  
**Correção**: Adicionar `RUN useradd -m synthfin && USER synthfin` antes do ENTRYPOINT.

### C6. CHANGELOG Footer Desatualizado

**Arquivo**: `docs/CHANGELOG.md` (últimas linhas)  
**Problema**: Footer diz `v4.0-beta` e `Dezembro 2025`, mas versão atual é v4.9.1 (Março 2026).  
**Impacto**: Confusão sobre versão atual para contribuidores.

### C7. API app.py é Apenas um Stub

**Arquivo**: `src/fraud_generator/api/app.py`  
**Problema**: O arquivo apenas faz `raise ImportError(...)`. Não há endpoints reais.  
**Impacto**: README menciona "Self-Hosted API Server" mas o módulo não funciona stand-alone.  
**Correção**: Documentar claramente que a API é somente no servidor synthfin.com.br, ou implementar endpoints locais.

### C8. CAPACITY_PLANNING Diverge do Código

**Arquivo**: `docs/performance/CAPACITY_PLANNING.md` vs `src/fraud_generator/licensing/limits.py`  
**Problema**: Doc diz FREE = 5K events/month; código diz FREE = 1M events/month.  
**Impacto**: Informação contraditória sobre limites do plano gratuito.

---

## 🟡 Problemas Maiores

### M1. Credenciais Default em check_schema.py

**Arquivo**: `check_schema.py` (linha 12)  
**Detalhe**: `aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin')` — fallback para credencial default do MinIO.  
**Risco**: Baixo (utilitário de dev), mas viola boas práticas.

### M2. Sem Validação de fraud_rate Upper Bound

**Arquivo**: `src/fraud_generator/generators/transaction.py`  
**Detalhe**: `fraud_rate` aceita qualquer float; não há validação `0.0 ≤ rate ≤ 1.0`.  
**Correção**: Adicionar `clamp(0.0, 1.0)` ou `ValueError` no construtor.

### M3. CNH Expiração Ignora Data Atual

**Arquivo**: `src/fraud_generator/generators/driver.py`  
**Detalhe**: Data de expiração da CNH é gerada sem referência à data atual, podendo gerar CNHs já expiradas para motoristas "ativos".

### M4. CustomerSessionState com Variáveis Mutáveis de Classe

**Arquivo**: `src/fraud_generator/utils/streaming.py`  
**Detalhe**: Variáveis mutáveis (listas, dicts) como class variables são compartilhadas entre instâncias — thread-unsafe.

### M5. WeightCache Key Collision

**Arquivo**: `src/fraud_generator/utils/weight_cache.py`  
**Detalhe**: `_weight_caches` usa strings simples como chaves; módulos diferentes podem colidir se usarem o mesmo nome.  
**Correção**: Usar tupla `(module, name)` como chave.

### M6. Schema Engine Sem Validação de Output

**Arquivo**: `src/fraud_generator/schema/engine.py`  
**Detalhe**: Registros gerados em schema mode não são validados contra o schema de entrada. Campos ausentes passam silenciosamente.

### M7. BatchRunner Sem Recovery de Falhas

**Arquivo**: `src/fraud_generator/cli/runners/batch_runner.py`  
**Detalhe**: Se um worker crashar, o batch inteiro falha sem retry ou checkpoint.  
**Correção**: Implementar checkpoint/retry para workers individuais.

### M8. generate_ip_brazil() Cobertura Incompleta

**Arquivo**: `src/fraud_generator/utils/helpers.py`  
**Detalhe**: Apenas 15 prefixos de IP hardcoded; não cobre todos os ISPs brasileiros.

### M9. Configuração de Banks Pesos Não Somam 100

**Arquivo**: `src/fraud_generator/config/banks.py`  
**Detalhe**: Weights dos bancos não somam 100 (nem 1.0). `random.choices` normaliza, mas `WeightCache` espera sum=1.0.

### M10. POI Fallback Cria POIs Sintéticos

**Arquivo**: `src/fraud_generator/generators/ride.py`  
**Detalhe**: Se nenhum POI real for encontrado para o estado, o gerador cria POIs com coordenadas aleatórias.  
**Impacto**: Rides com pontos de origem/destino inexistentes.

### M11. Kafka Connection Sem Métricas

**Arquivo**: `src/fraud_generator/connections/kafka_connection.py`  
**Detalhe**: Serialização usa `default=str`, que silenciosamente converte erros em strings ao invés de falhar.

### M12. Resend Email Client Sem Retry

**Arquivo**: `src/fraud_generator/email/resend_client.py`  
**Detalhe**: Chamadas à API do Resend não têm retry/backoff. Falha silenciosa possível.

---

## 🟢 Melhorias Sugeridas

### Performance

| # | Melhoria | Impacto Estimado | Esforço |
|---|----------|-----------------|---------|
| P1 | Padrões de fraude sequenciais (velocity checks entre transações) | Alto — realismo | Médio |
| P2 | CSV/Parquet streaming write para datasets >1GB | Alto — remove limite de memória | Médio |
| P3 | Tunável `BATCH_SIZE` no `ParallelStreamManager` (fixo em 200) | Baixo — otimização fina | Baixo |
| P4 | Worker seed: `worker_id * 7919` pode colidir se workers > 100 | Baixo — edge case | Baixo |

### Testes

| # | Melhoria | Impacto Estimado | Esforço |
|---|----------|-----------------|---------|
| T1 | Property-based tests (fraud_rate ± tolerância) | Alto — confiabilidade | Médio |
| T2 | Negative tests (CPF inválido, args inválidos, seed negativa) | Médio — robustez | Baixo |
| T3 | Edge case tests (datasets vazios, seed=0, fraud_rate=1.0) | Médio — robustez | Baixo |
| T4 | Performance/load tests automáticos no CI | Médio — regressão | Médio |
| T5 | Coverage report no CI (atualmente só local) | Baixo — visibilidade | Baixo |

### Arquitetura

| # | Melhoria | Impacto Estimado | Esforço |
|---|----------|-----------------|---------|
| A1 | Injeção de dependência para RingRegistry (remover singleton) | Alto — thread-safety + testabilidade | Baixo |
| A2 | Enricher pipeline configurável via arquivo (não hardcoded) | Médio — extensibilidade | Médio |
| A3 | Schema versionamento (compatible/breaking change detection) | Médio — governança | Médio |
| A4 | Perfis comportamentais carregáveis de arquivo externo | Médio — customização | Baixo |
| A5 | Validação de schema no output (não só no input) | Médio — qualidade | Médio |
| A6 | Connection pooling no DatabaseExporter | Alto — performance DB | Médio |

---

## Matriz de Cobertura de Testes por Módulo

| Módulo | Unit Tests | Integration Tests | Cobertura Estimada |
|--------|-----------|------------------|-------------------|
| Generators (transaction, ride, customer, device, driver) | Parcial (via output_schema) | Sim (7 testes) | ~60% |
| Exporters (jsonl, csv, parquet, arrow, db, minio) | Parcial (phase_2) | Sim (workflow) | ~40% |
| Enrichers (8 enrichers) | Sim (20 testes) | Não | ~50% |
| Connections (kafka, webhook, stdout) | Não | Não | ~0% |
| Schema (parser, mapper, engine, ai_corrector) | Parcial (output_schema) | Não | ~30% |
| Licensing (license, limits, validator) | Sim (12 testes) | Não | ~70% |
| Validators (CPF) | Indireto | Não | ~80% |
| Utils (compression, weight_cache, streaming) | Sim (22 + 25) | Não | ~60% |
| Config (banks, merchants, geography, etc.) | Não | Não | ~0% |
| CLI (args, runners, workers) | Não | Parcial | ~20% |
| Profiles (behavioral, ride_behavioral) | Indireto | Não | ~30% |

**Total estimado**: ~40% de cobertura de código. Lacunas mais críticas: Connections (0%), Config (0%), CLI (20%).

---

## Plano de Priorização

### Sprint 1 (Urgente — Segurança)
1. ~~C1~~ Remover VERIFY_KEY do Dockerfile ARG/ENV
2. ~~C5~~ Adicionar USER non-root no Dockerfile
3. ~~M1~~ Remover credenciais default de check_schema.py

### Sprint 2 (Alta Prioridade — Estabilidade)
4. ~~C2~~ Thread-safety no RingRegistry
5. ~~C3~~ Parquet append streaming
6. ~~C4~~ Padronizar separadores de flattening
7. ~~M2~~ Validar fraud_rate bounds

### Sprint 3 (Média Prioridade — Qualidade)
8. ~~T1-T3~~ Testes property-based, negativos e edge cases
9. ~~A1~~ Injeção de dependência para RingRegistry
10. ~~M7~~ Checkpoint/retry para BatchRunner

### Sprint 4 (Melhoria Contínua)
11. Restantes melhorias de performance e arquitetura

---

*Gerado por GitHub Copilot — synthfin-data v4.9.1*
