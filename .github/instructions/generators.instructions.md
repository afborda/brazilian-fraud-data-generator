---
description: "Use when editing data generators: customer, device, transaction, ride, driver, score, correlations, or session context modules. Covers entity chain pattern, fraud injection, profile-aware generation, WeightCache usage."
applyTo: "src/fraud_generator/generators/**"
---

# Generator Rules

## Entity Chain (MUST follow)
- Customer → Device → Transaction/Ride — never generate a TX without parent entities
- Build `CustomerIndex`/`DeviceIndex` BEFORE entering the generation loop
- ID format: `CUST_XXXXXXXX`, `DEV_XXXXXXXX`, `TX_XXXXXXXX` (8-char hex suffix)

## Profile-Aware Generation
- Every customer has a sticky `behavioral_profile` (assigned once at creation)
- Use `get_*_for_profile(profile)` functions from `profiles/behavioral.py`
- NEVER reassign a profile after customer creation
- Fraud injection CAN override profile-typical values (that's the anomaly signal)

## Fraud Injection
- Fraud = normal transaction with modified fields, NOT a separate record type
- Pipeline: generate normal TX → check `random() < fraud_rate` → apply pattern → run enrichers
- Fraud patterns defined in `config/fraud_patterns.py` — never hardcode fraud logic
- Always run enricher pipeline after injection (`enrichers/pipeline_factory.py`)

## Performance (P2 mitigation)
- Use `WeightCache` from `utils/weight_cache.py` for per-record weighted selections
- Initialize caches in `__init__`, not in the generate loop
- For batch operations, prefer `choose_batch(n)` over N single `choose()` calls

## Reproducibility
- Set `random.seed()` BEFORE any generator construction
- Generators must produce identical output for same seed
- Timestamp generation is derived from seed, not wall-clock `datetime.now()`
