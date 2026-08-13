# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

High-performance synthetic data generator for Brazilian banking & ride-share fraud detection. Generates labeled datasets (JSONL, CSV, Parquet) at MB–TB scale. Published on PyPI as `fraud-generator`.

**Em correção (camada 1, branch `fix/camada-1-vazamento`):** as métricas históricas "quality 9.70/10 (A+), AUC-ROC 0.9991" medem vazamento de rótulo, não qualidade. Uma AUC próxima de 1.0 significa fraude trivialmente separável — dado que não transfere para produção. O alvo é AUC efetiva **0.75–0.95**. Não trate quedas de AUC como regressão.

## Commands

```bash
# Generate batch data
python generate.py --size 100MB --format jsonl --output ./data --seed 42
python generate.py --size 1GB --type rides --format parquet --output ./data

# Stream to targets
python stream.py --target stdout --rate 5
python stream.py --target kafka --kafka-topic transactions --rate 100

# Schema validation
python check_schema.py output/transactions_00000.jsonl

# Quality benchmark (runs ~2min, outputs JSON grades A+→F)
python benchmarks/data_quality_benchmark.py

# ML model training
python tools/train_ml.py --input ./data/*.jsonl --model-dir ./models

# Tests (always run after changes)
pytest tests/ -v --tb=short

# Single test file
pytest tests/unit/test_output_schema.py -v

# With coverage
pytest tests/ --cov=src/fraud_generator --cov-report=term-missing

# Lint
ruff check src/ tests/
ruff format --check src/ tests/
```

**O lint NÃO está limpo.** `ruff check src/` acusa ~468 problemas pré-existentes,
e por isso o passo de lint do `.github/workflows/test.yml` falha hoje, inclusive
no `main`. A composição:

| Regra | Qtd | Situação |
|---|---|---|
| `W293` blank-line-with-whitespace | 239 | dentro de strings/docstrings; só sai com `--unsafe-fixes` |
| `F401` unused-import | 93 | **não auto-corrigir** — pode haver re-export ou import com efeito colateral |
| `I001` unsorted-imports | 80 | reordenar pode quebrar import cíclico; requer verificação |
| `E501` line-too-long | 30 | cosmético |
| `E402`, `F841`, `E741`, `F541` | 26 | avulsos |

Ao mexer num arquivo, deixe-o mais limpo do que encontrou, mas **não rode
`ruff check src/ --fix` de uma vez**: o diff resultante enterra qualquer mudança
real de comportamento na mesma revisão. Espaço em branco puro (`W291,W293,W292`)
é seguro corrigir em commit separado.

## Architecture

### Two execution modes

Both share `--seed`, `--fraud-rate`, `--type`:

- **Batch** (`generate.py`): Parses args → `BatchRunner` / `MinIORunner` / `SchemaRunner` → Generator pipeline → Exporter → disk/S3
- **Stream** (`stream.py`): Parses args → creates customer/device pool → `get_connection(target)` → continuous generation loop → network

Generators initialized for one mode cannot be reused in the other.

### Entity chain (invariant)

Customer → Device → Transaction/Ride. Never generate transactions without parent entities. Indexes are built BEFORE generation: `CustomerIndex`, `DeviceIndex`, `DriverIndex`.

### Enricher pipeline — 8 stages, order matters

Defined in `enrichers/pipeline_factory.py`. Each enricher implements `EnricherProtocol.enrich(tx, bag)` — mutates `tx` dict in-place.

```
1. TemporalEnricher    — unusual_time flag (must run before Fraud)
2. GeoEnricher         — lat/lon from IBGE (must run before Fraud)
3. FraudEnricher       — pattern injection, velocity, dest_account_age
4. PIXEnricher         — BACEN pacs.008 fields (needs channel from Fraud)
5. DeviceEnricher      — emulator, VPN, rooted signals
6. SessionEnricher     — velocity windows 1h/6h/24h/7d (needs device_id)
7. RiskEnricher        — aggregates 17 signals into fraud_risk_score [0-100]
8. BiometricEnricher   — typing speed, touch pressure (Pro+ gated)
```

The ordering has data dependencies — don't reorder without understanding why each position exists.

`GeneratorBag` carries shared state (caches, profile, fraud info) through the pipeline.

### Strategy patterns

- **Exporters** (`exporters/__init__.py`): Registry `EXPORTERS` maps format names → classes implementing `ExporterProtocol`. Use `get_exporter(format_name)`. Conditional: Parquet/Arrow/DB only if deps available.
- **Connections** (`connections/__init__.py`): Registry `CONNECTIONS` maps target names → classes implementing `ConnectionProtocol`. Use `get_connection(target)`.

### Config convention (enforced in all 14 config modules)

Every config module in `config/` exports: `THING_LIST`, `THING_WEIGHTS`, `get_thing()`. Never hardcode domain values in generators — always go through config. Weights must be proportional and close to sum ≈ 1.0. Mismatched list/weights lengths crash at runtime.

### Fraud patterns

25 banking + 11 ride-share patterns in `config/fraud_patterns.py`. Each has `characteristics` dict (anomaly levels, velocity, channel/type preferences, amount multiplier), `prevalence` weight, and `fraud_score_base`. Fraud injection works by: normal TX → `random() < fraud_rate` → select pattern by prevalence weights → apply characteristic overrides → run enricher pipeline.

### Risk scoring — 17 signals

`generators/score.py` computes `fraud_risk_score` [0-100] by summing weighted boolean signals (emulator=35, rooted=30, ATO triad=25, etc.) plus 4 correlation rules. The score must remain meaningful after optimization — guard with effective AUC-ROC within the 0.75–0.95 band (CI fails above 0.97). An AUC above 0.97 means the fraud is trivially separable and the batch must FAIL, not pass: see tools/analyze_batch.py.

### ML quality validation

`ml/` module: extracts 29 features → trains LightGBM binary + multilabel models → evaluates AUC-ROC/AUC-PR. `fraud_score` and `fraud_risk_score` are deliberately NOT features — the generator derives them from the label, so feeding them back in is circular. Do not re-add them. Used by `benchmarks/data_quality_benchmark.py` which scores 9 quality dimensions and assigns letter grades. The quality pipeline is optional (graceful degradation if LightGBM unavailable).

### Profile stickiness

Once a customer is assigned a behavioral profile, it's fixed across all their transactions. Use `get_*_for_profile()` functions, never reassign.

## Testing

- **Fixtures** (in `conftest.py`): `temp_output_dir`, `test_seed` (42), `small_batch_size` (100), `sample_customer_data`, `sample_transaction_data`, `sample_ride_data`
- **Seed**: Always `random.seed(42)` BEFORE generator construction
- **CPF**: Never mock — use `generate_valid_cpf()` from `validators/cpf.py`
- **Naming**: `test_{behavior}_when_{condition}`
- **Unit tests** (9 files): enricher pipeline, scoring, session context, fraud patterns, correlations, compression, optimizations, output schema
- **Integration tests** (2 files): full batch workflow, compression+streaming end-to-end
- Run `pytest tests/unit/test_output_schema.py -v` after any config weight changes

## Versioning

Three files must stay in sync (atomic updates): `VERSION`, `pyproject.toml [project.version]`, `docs/CHANGELOG.md`. The `__init__.py` version may lag — canonical version is `VERSION` file.

## Documentation governance

- CHANGELOG mandatory for every behavioral change (Portuguese, `## v{X.Y} — {Name} ({date})` format)
- Check `docs/INDEX.md` before creating new docs — no duplicates
- Planning docs are ephemeral: deliver → CHANGELOG → delete → update INDEX
- Permanent docs (never delete): CHANGELOG.md, INDEX.md, ARCHITECTURE.md, README.md

## Performance

- Use `WeightCache` for repeated `random.choices()` — init in `__init__`, prefer `choose_batch(n)`
- Never accumulate full dataset in memory — stream via `export_batch()`
- Known P3: CSV/Parquet OOM on >1GB (streaming rewrite needed)
- Always benchmark before/after: `python benchmarks/data_quality_benchmark.py`

## Scoped rules

Detailed per-domain rules in `.github/instructions/` are loaded by IDE agents when editing scoped paths. Key files: `generators.md`, `exporters.md`, `config.md`, `testing.md`, `cicd.md`, `performance.md`, `documentation.md`.

## Agent routing

See `AGENTS.md` for the full 9-agent registry. Keywords route to specialists (fraud patterns, quality analysis, testing, CI/CD, performance, config, documentation).
