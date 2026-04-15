---
description: Config module convention — *_LIST + *_WEIGHTS + get_*() pattern
paths:
  - "src/fraud_generator/config/**"
---

# Config Module Rules

## Convention
```python
THING_LIST = [...]           # All possible values
THING_WEIGHTS = [...]        # Probability weights (sum ≈ 1.0)
get_thing(key) → dict/str    # Lookup helper
```

## Rules
1. NEVER hardcode values in generators — reference config modules
2. Weights are proportional, keep close to sum=1.0
3. Update BOTH `*_LIST` AND `*_WEIGHTS` — mismatched lengths crash
4. Config = SINGLE source of truth for domain constants
5. Calibrate weights against real BCB data

## Testing
- After modifying: `pytest tests/unit/test_output_schema.py -v`
- After adding entries: generate 1000 records, check distribution
