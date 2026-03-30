# Fraud Injection Pattern

> How synthfin-data injects fraud into generated records.

## Core Principle

Fraud records are **normal transactions with modified fields**, not separate record types. A fraud transaction starts as a legitimate one, then has specific fields altered based on the fraud pattern.

## Injection Pipeline

```
1. Generate normal transaction (customer → device → TX)
2. Roll dice: random() < fraud_rate?
   ├── No  → return normal transaction
   └── Yes → select fraud pattern from FRAUD_PATTERNS (weighted)
             → apply pattern modifications to fields
             → run enricher pipeline (17+ signals)
             → compute fraud_risk_score
             → set is_fraud=True, fraud_type="{pattern_key}"
             → return enriched fraud transaction
```

## Pattern Definition Structure

Each fraud pattern in `config/fraud_patterns.py` defines:

```python
{
    "key": "pix_cloning",                    # Unique identifier
    "name": "PIX QR Code Cloning",           # Human-readable name
    "category": "pix",                        # Category grouping
    "weight": 0.15,                           # Selection probability
    "anomaly_multiplier": 2.5,               # How much to deviate from normal
    "velocity_increase": True,               # Triggers velocity signals
    "new_beneficiary": True,                 # Flags new_beneficiary signal
    "device_change": False,                  # Whether device fingerprint changes
    "geo_anomaly": False,                    # Geographic velocity anomaly
    "amount_deviation": "high",              # Amount z-score level
    "typical_hour": "off_peak",              # Time-of-day pattern
    "description": "Attacker clones..."      # Documentation
}
```

## Enricher Pipeline Integration

After fraud injection, the enricher pipeline (`enrichers/pipeline_factory.py`) computes:

```
FraudEnricher → RiskEnricher → PIXEnricher → DeviceEnricher
→ TemporalEnricher → GeoEnricher → SessionEnricher → BiometricEnricher
```

Each enricher adds specific signals. The final `fraud_risk_score` aggregates all signals via `generators/score.py`.

## Rules for Adding New Fraud Patterns

1. Add definition to `config/fraud_patterns.py` → `FRAUD_PATTERNS` dict
2. Ensure weights across all patterns sum to ~1.0 (or close — `random.choices` normalizes)
3. Map which enricher signals the pattern should trigger
4. Test: generate 1000 records, verify fraud_risk_score separates fraud from legit
5. Update `docs/CHANGELOG.md` with the new pattern

## Anti-Patterns

- **Separate fraud table**: Don't create fraud records as a different entity
- **Hardcoded signals**: Always compute signals via enricher pipeline, not manually
- **Ignoring calibration**: New patterns should reference BCB data for realistic rates
