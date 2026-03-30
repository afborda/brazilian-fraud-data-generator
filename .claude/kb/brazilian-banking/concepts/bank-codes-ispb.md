# Bank Codes & ISPB

> Brazilian banking institution identifiers used in transaction generation.

## Identification Systems

| System | Digits | Purpose | Example |
|--------|--------|---------|---------|
| **ISPB** | 8 | BCB payment system ID | 00000000 (Banco do Brasil) |
| **COMPE** | 3 | Legacy clearing code | 001 (Banco do Brasil) |
| **CNPJ** | 14 | Tax registration | 00000000000191 |

## Major Banks (by transaction weight in synthfin-data)

| Bank | COMPE | Weight | Category |
|------|-------|--------|----------|
| Banco do Brasil | 001 | High | Public |
| Itaú Unibanco | 341 | High | Private |
| Bradesco | 237 | High | Private |
| Caixa Econômica | 104 | High | Public |
| Santander | 033 | Medium | Foreign |
| Nubank | 260 | Medium | Digital |
| Inter | 077 | Low | Digital |
| C6 Bank | 336 | Low | Digital |

## Config Architecture

```python
# src/fraud_generator/config/banks.py

BANK_CODES = [...]          # List of all bank dicts {code, name, ispb, weight}
BANK_WEIGHTS = [...]        # Probability weights (sum ≈ 1.0)
get_bank_info(code) → dict  # Lookup by COMPE code
```

## Rules for Agents

1. **Always use config**: Never hardcode bank codes — reference `config/banks.py`
2. **Weights reflect reality**: Distribution calibrated against BCB market share data
3. **Digital banks trend**: Nubank/Inter weights should increase over time
4. **ISPB format**: Always 8 digits, zero-padded string (not integer)
5. **When adding banks**: Add to `BANK_CODES` list AND update `BANK_WEIGHTS`
