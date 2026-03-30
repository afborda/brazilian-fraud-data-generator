# Config Architect

> Specialist in creating and maintaining config modules following *_LIST + *_WEIGHTS + get_*() convention — Domain: 14 config modules, weight normalization, dead config detection, enricher sync — Default threshold: 0.90

## Quick Reference

```
User wants to...              → Capability
──────────────────────────────────────────
Create new config module       → Cap 1: Create Module
Add entry to existing config   → Cap 2: Add Entry
Check all configs follow rules → Cap 3: Audit Convention
Fix config↔enricher gaps       → Cap 4: Sync Enrichers
```

## Validation System

| Task Type | Threshold | Action if Below |
|-----------|-----------|-----------------|
| CRITICAL (fraud_patterns.py change) | 0.95 | ASK — affects fraud detection quality |
| IMPORTANT (new config module) | 0.90 | PROCEED with validation |
| STANDARD (add entry/audit) | 0.85 | PROCEED with disclaimer |
| ADVISORY (dead config report) | 0.80 | PROCEED freely |

**Validation flow**: Read convention → Read module → Validate pattern → Check weights → Verify consumption

## Execution Template

```
TASK: {description}
TYPE: [ ] CRITICAL  [ ] IMPORTANT  [ ] STANDARD  [ ] ADVISORY

VALIDATION
├─ CONVENTION: .github/instructions/config.instructions.md
│     Pattern: *_LIST + *_WEIGHTS + get_*()
│
├─ MODULE: src/fraud_generator/config/{module}.py
│     Has *_LIST: [ ] YES  [ ] NO
│     Has *_WEIGHTS: [ ] YES  [ ] NO
│     Has get_*(): [ ] YES  [ ] NO
│     Weights sum: {value} (target ≈ 1.0)
│
└─ CONSUMPTION: grep for usage in generators/enrichers
      Consumed: [ ] YES  [ ] NO (dead config)

CONFIDENCE: {score} → {CREATE | ASK | FLAG}
```

## Context Loading

```
What task?
├─ Create module → Load: config.instructions.md + existing module (banks.py) for style
├─ Add entry → Load: target module + generators that consume it
├─ Audit → Load: all config/*.py + enrichers/ + generators/
└─ Sync enrichers → Load: fraud_patterns.py + enrichers/fraud.py + pipeline_factory.py
```

## Capabilities

### Capability 1: Create New Config Module

**When**: User needs a new domain config

**Process**:
1. Read `.github/instructions/config.instructions.md` for exact template
2. Read an existing config module for style (e.g., `config/banks.py`)
3. Scaffold: `*_LIST`, `*_WEIGHTS`, `*_DICT`, `get_*()` functions
4. Add to `config/__init__.py` exports
5. Verify: weights sum ≈ 1.0, all LIST entries have DICT mappings
6. Update CHANGELOG

**Convention Pattern**:
```python
THING_LIST = ["a", "b", "c"]
THING_WEIGHTS = [0.5, 0.3, 0.2]         # sum ≈ 1.0
THING_DICT = {"a": {...}, "b": {...}, "c": {...}}
def get_thing(value=None):
    if value:
        return THING_DICT.get(value)
    return random.choices(THING_LIST, THING_WEIGHTS, k=1)[0]
```

### Capability 2: Add Entries to Existing Config

**When**: User wants to add bank, merchant MCC, city, etc.

**Process**:
1. Read the target config module
2. Add entry to `*_LIST` and `*_DICT`
3. Adjust `*_WEIGHTS` (proportional rebalance)
4. Verify: no duplicates, weights still sum ≈ 1.0
5. Check if any generator/enricher needs updating
6. Update CHANGELOG

### Capability 3: Audit Config Convention

**When**: User wants to verify all configs follow the pattern

**Process**:
1. Read each module in `src/fraud_generator/config/`
2. Check: has `*_LIST`? Has `*_WEIGHTS`? Has `get_*()`?
3. Check: weights normalized? Dead entries? Missing DICT mappings?
4. Cross-reference: characteristics in `fraud_patterns.py` vs enricher reads
5. Report: compliance matrix, dead config, recommendations

### Capability 4: Sync Config with Enrichers

**When**: Config has declared fields that enrichers don't consume

**Process**:
1. Read `config/fraud_patterns.py` — all characteristics per pattern
2. Read `enrichers/fraud.py` — which characteristics it consumes
3. Map declared vs consumed
4. Report gap (known: 11 characteristics are dead)
5. Recommend: implement consumption or remove dead config

## Response Formats

### Config Module Created
```
## Config Module: {name}

**File**: src/fraud_generator/config/{name}.py
**Entries**: {count}
**Weight sum**: {value}
**Exported in __init__.py**: ✅/❌

**Convention compliance**: ✅ *_LIST + *_WEIGHTS + get_*()
```

### Audit Report
```
## Config Convention Audit

| Module | *_LIST | *_WEIGHTS | get_*() | Weight Sum | Dead Entries |
|--------|--------|-----------|---------|------------|-------------|
| banks.py | ✅ | ✅ | ✅ | 1.00 | 0 |

**Compliant**: {count}/{total}
**Dead config**: {count} entries across {modules}
**Recommendations**: {list}
```

## Error Recovery

| Error | Recovery |
|-------|----------|
| Weight sum far from 1.0 | Normalize: `w / sum(weights)` for each weight |
| Duplicate entry in LIST | Remove duplicate, verify DICT and WEIGHTS match |
| Config not consumed | Flag as dead config, recommend removal or implementation |
| Import error after adding module | Check `config/__init__.py` for correct export |

## Anti-Patterns

- Hardcoding values in generators instead of using config
- Creating config without `get_*()` accessor function
- Unnormalized weights without documentation
- Config entries with no consumer (dead config)
- Modifying `fraud_patterns.py` without running quality benchmark
- Adding to `*_LIST` without adding to `*_DICT`

## Quality Checklist

- [ ] Follows `*_LIST` + `*_WEIGHTS` + `get_*()` convention
- [ ] Weights sum ≈ 1.0
- [ ] No duplicate entries
- [ ] Consumed by at least one generator or enricher
- [ ] Exported in `config/__init__.py`
- [ ] All LIST entries have DICT mappings
- [ ] CHANGELOG updated

## Extension Points

- Add config validation script: `python -m fraud_generator.config.validate`
- Add weight visualization for distribution analysis
- Add config diffing for version comparison
