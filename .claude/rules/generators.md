---
description: Entity chain pattern, fraud injection, profile-aware generation, WeightCache usage
paths:
  - "src/fraud_generator/generators/**"
---

# Generator Rules

## Entity Chain
- Customer → Device → Transaction/Ride — never generate TX without parent entities
- Build `CustomerIndex`/`DeviceIndex` BEFORE entering generation loop
- ID format: `CUST_XXXXXXXX`, `DEV_XXXXXXXX`, `TX_XXXXXXXX`

## Profile-Aware Generation
- Every customer has a sticky `behavioral_profile` (assigned once at creation)
- Use `get_*_for_profile(profile)` from `profiles/behavioral.py`
- NEVER reassign profile after customer creation
- Fraud injection CAN override profile-typical values

## Fraud Injection
- Fraud = normal TX with modified fields, NOT separate record type
- Pipeline: normal TX → `random() < fraud_rate` → apply pattern → run enrichers
- Patterns in `config/fraud_patterns.py` — never hardcode fraud logic
- Always run enricher pipeline after injection

## Performance
- Use `WeightCache` for per-record weighted selections
- Initialize caches in `__init__`, not in generate loop
- Prefer `choose_batch(n)` for batch operations

## Reproducibility
- `random.seed()` BEFORE any generator construction
- Same seed = identical output
