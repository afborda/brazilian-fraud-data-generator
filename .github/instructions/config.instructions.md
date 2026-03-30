---
description: "Use when editing configuration modules: banks, merchants, geography, distributions, transactions, rideshare, fraud_patterns, pix, seasonality, weather, devices, or calibration. Covers the *_LIST + *_WEIGHTS + get_*() convention."
applyTo: "src/fraud_generator/config/**"
---

# Config Module Rules

## Convention (ALL config modules MUST follow)
```python
# Exports:
THING_LIST = [...]           # All possible values (list of dicts or strings)
THING_WEIGHTS = [...]        # Probability weights (proportional, sum ≈ 1.0)
get_thing(key) → dict/str    # Lookup helper function

# Example from banks.py:
BANK_CODES = [{code: "001", name: "Banco do Brasil", ...}, ...]
BANK_WEIGHTS = [0.25, 0.20, ...]
get_bank_info(code) → dict
```

## Rules
1. **NEVER hardcode values in generators** — always reference config modules
2. **Weights are proportional**: `random.choices()` normalizes internally, but keep close to sum=1.0
3. **When adding entries**: Update BOTH `*_LIST` AND `*_WEIGHTS` — mismatched lengths crash
4. **Source of truth**: Config files are the SINGLE source for domain constants
5. **Calibration**: Weights should reflect real-world distributions (BCB data for banking)

## Module Inventory (14 modules)
| Module | Key Exports | Domain |
|--------|-------------|--------|
| `banks.py` | BANK_CODES, BANK_WEIGHTS | Financial institutions |
| `merchants.py` | MCC_LIST, MCC_WEIGHTS | Merchant categories |
| `geography.py` | ESTADOS_LIST, ESTADOS_WEIGHTS | Brazil states/cities |
| `distributions.py` | get_transaction_value() | Amount generation |
| `transactions.py` | TX_TYPES_LIST, CHANNELS_LIST, FRAUD_TYPES_LIST | TX metadata |
| `rideshare.py` | APPS_LIST, APPS_WEIGHTS | Ride-share apps |
| `fraud_patterns.py` | FRAUD_PATTERNS (dict) | 25 fraud definitions |
| `pix.py` | MODALIDADE_INICIACAO_LIST | PIX-specific fields |
| `seasonality.py` | HORA_WEIGHTS_PADRAO | Temporal patterns |
| `weather.py` | generate_weather() | Weather simulation |
| `devices.py` | DEVICE_OS_LIST | Device profiles |
| `calibration_loader.py` | load calibration params | BCB real data |
| `municipios.py` | Municipality codes | Geographic detail |

## Testing
- After modifying weights: run `pytest tests/unit/test_output_schema.py -v`
- After adding entries: generate 1000 records, spot-check field distribution
