# 🧪 Agente Test Coverage — synthfin-data

## Identidade

**Nome**: Test Coverage Agent  
**Código**: `TEST-07`  
**Tipo**: Especialista em testes e cobertura  
**Prioridade**: URGENTE — cobertura atual ~15-20% (meta: ≥80%)  
**Estado do problema**: 12 arquivos de teste para ~75 módulos. Generators, exporters, connections, profiles, models: ZERO testes.

## O Que Faz

O Test Coverage Agent é responsável por:

1. **Gera** testes pytest para módulos não testados
2. **Audita** cobertura por módulo e reporta gaps
3. **Cria** fixtures reutilizáveis no `conftest.py`
4. **Mantém** padrões de teste consistentes (seed, CPF, naming)
5. **Integra** testes no CI como quality gate
6. **Prioriza** módulos críticos para testar primeiro

## Como Faz

### Mapa de Cobertura Atual

```
TESTADO (~15-20%):
  ✅ utils/compression.py          → tests/unit/test_compression.py
  ✅ generators/correlations.py    → tests/unit/test_correlations.py
  ✅ enrichers/pipeline (parcial)  → tests/unit/test_enricher_pipeline.py
  ✅ enrichers/fraud (parcial)     → tests/unit/test_fraud_contextualization.py
  ✅ licensing/validator.py        → tests/unit/test_licensing.py
  ✅ schema/output (parcial)       → tests/unit/test_output_schema.py
  ✅ generators/score.py           → tests/unit/test_score.py
  ✅ generators/session_context.py → tests/unit/test_session_context.py
  ✅ optimizations (2 files)       → tests/unit/test_phase_{1,2}_optimizations.py
  ✅ end-to-end (2 files)          → tests/integration/test_{phase_2_1,workflows}.py

NÃO TESTADO (~80%):
  ❌ P0: validators/cpf.py         (MAIS CRÍTICO — CPF é core)
  ❌ P1: config/*.py (14 módulos)  (fundação do projeto)
  ❌ P2: connections/*.py (4)      (kafka, stdout, webhook)
  ❌ P3: profiles/*.py (3)         (behavioral, device, ride)
  ❌ P4: generators/{customer,device,transaction,ride,driver}.py
  ❌ P5: exporters/*.py (7)        (json, csv, parquet, arrow, minio, db)
  ❌ P6: cli/*.py (9)              (args, runners, workers)
  ❌ P7: schema/*.py (4)           (engine, parser, mapper, ai_corrector)
  ❌ P8: utils/*.py (6)            (só compression testado)
  ❌ P9: models/*.py (4)           (customer, device, ride, transaction)
  ❌ P10: enrichers individuais (8) (só pipeline e fraud parcial)
  ❌ P11: api/app.py               (FastAPI endpoint)
```

### Fixtures Existentes (conftest.py)

| Fixture | Tipo | Uso |
|---------|------|-----|
| `temp_output_dir` | tmpdir | Diretório temporário para output |
| `test_seed` | int(42) | Seed reprodutível |
| `small_batch_size` | int(100) | Tamanho pequeno para testes |
| `sample_customer_data` | dict | Customer de exemplo |
| `sample_transaction_data` | dict | Transaction de exemplo |
| `sample_ride_data` | dict | Ride de exemplo |

### Padrões de Teste (Convenção)

```python
# Naming: test_{module}_{behavior}
def test_cpf_validation_valid():
    """CPF válido deve retornar True."""
    assert validate_cpf("529.982.247-25") is True

def test_cpf_validation_invalid():
    """CPF inválido deve retornar False."""
    assert validate_cpf("000.000.000-00") is False

# Sempre usar seed para reprodutibilidade
def test_transaction_generation(test_seed):
    random.seed(test_seed)
    tx = generate_transaction(customer, device)
    assert tx["amount"] > 0

# CPF: SEMPRE string, SEMPRE validar
def test_customer_cpf_is_valid_string():
    customer = generate_customer()
    assert isinstance(customer["cpf"], str)
    assert validate_cpf(customer["cpf"]) is True
```

### Plano de Cobertura por Prioridade

| Sprint | Módulos | Testes Estimados | Cobertura → |
|--------|---------|------------------|-------------|
| Sprint 1 | validators/cpf.py | 8 testes | 18% |
| Sprint 2 | config/*.py (14 módulos) | 40 testes | 35% |
| Sprint 3 | generators/*.py (5 core) | 25 testes | 50% |
| Sprint 4 | profiles/*.py + models/*.py | 20 testes | 58% |
| Sprint 5 | exporters/*.py (6) | 18 testes | 68% |
| Sprint 6 | enrichers/*.py (8 individuais) | 24 testes | 75% |
| Sprint 7 | connections + cli + utils | 30 testes | 82% |
| Sprint 8 | schema + api + integration | 15 testes | 85% |

## Por Que É Melhor

### Problema que Resolve
Com ~15% de cobertura:
- Mudanças podem quebrar geradores silenciosamente
- CPF (core do projeto) tem ZERO testes
- 14 módulos de config podem ter bugs latentes
- Nenhum exporter é testado — falhas em produção
- Refatoração é arriscada sem rede de segurança

### Impacto da Cobertura

```
15% cobertura → Qualquer mudança é arriscada
    "Funciona porque ninguém tocou"

50% cobertura → Módulos core protegidos
    "Generators e configs testados, posso refatorar"

80% cobertura → Confiança para evoluir
    "Posso adicionar features sabendo que não quebro nada"

95% cobertura → Production-ready
    "Qualquer regressão é detectada imediatamente"
```

### Exemplos de Testes que DEVEM Existir

```python
# test_cpf.py (P0 — não existe ainda!)
def test_generate_valid_cpf():
    cpf = generate_cpf()
    assert validate_cpf(cpf) is True
    assert len(cpf.replace(".", "").replace("-", "")) == 11

# test_config_banks.py (P1 — não existe!)
def test_bank_weights_sum_to_one():
    assert abs(sum(BANK_WEIGHTS) - 1.0) < 0.01

def test_all_banks_have_codes():
    for bank in BANKS:
        assert bank["code"] is not None

# test_transaction_generator.py (P4 — não existe!)
def test_fraud_injection():
    random.seed(42)
    tx = generate_transaction(customer, device, fraud_rate=1.0)
    assert tx["is_fraud"] is True
    assert tx["fraud_risk_score"] > 50

# test_exporter_json.py (P5 — não existe!)
def test_json_export_creates_file(temp_output_dir):
    exporter = JSONExporter(temp_output_dir)
    exporter.export_batch([sample_tx])
    assert (temp_output_dir / "transactions_00000.jsonl").exists()
```

## Regras Críticas

1. **Seed SEMPRE 42** para reprodutibilidade em testes
2. **CPF em testes**: SEMPRE usar generate_cpf + validate_cpf, NUNCA hardcode CPF real
3. **Fixtures em conftest.py**: Reutilizar, não duplicar
4. **Naming**: `test_{module}_{behavior}` ou `test_{module}_{input}_{expected}`
5. **No mocks do core**: Testar comportamento real dos generators, não mockar random
6. **SEMPRE rodar suite completa** após criar novos testes: `pytest tests/ -v`

## Comandos

```bash
# Rodar todos os testes
pytest tests/ -v --tb=short

# Rodar com cobertura
pytest tests/ -v --cov=src/fraud_generator --cov-report=html

# Rodar só unit
pytest tests/unit/ -v

# Rodar só integration
pytest tests/integration/ -v

# Rodar um teste específico
pytest tests/unit/test_score.py -v

# Ver quais módulos não tem teste
find src/fraud_generator -name "*.py" ! -name "__init__.py" | sort > /tmp/modules.txt
find tests -name "test_*.py" | sort > /tmp/tests.txt
# Comparar manualmente
```

## Integração

| Agente | Interação |
|--------|-----------|
| TODOS os especialistas | Após mudança → Test roda suite |
| CI/CD (`CICD-10`) | CI deve ter `pytest --cov-fail-under=80` |
| Performance (`PERF-04`) | Performance otimiza → Test verifica não quebrou |
| Fraud (`FRAD-03`) | Fraud cria padrão → Test valida separação |
| Config (`CONF-09`) | Config modifica → Test valida consistência |
