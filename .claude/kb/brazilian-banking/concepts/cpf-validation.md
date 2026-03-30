# CPF Validation

> Brazilian individual taxpayer identification (Cadastro de Pessoas Físicas).

## Format

`XXX.XXX.XXX-DD` where DD are algorithmically computed check digits.
- 11 digits total (9 base + 2 check)
- Stored as **string** in synthfin-data (preserves leading zeros)

## Validation Algorithm

### First Check Digit (position 10)
```
weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
sum = Σ(digit[i] × weight[i]) for i in 0..8
remainder = sum % 11
digit_10 = 0 if remainder < 2 else (11 - remainder)
```

### Second Check Digit (position 11)
```
weights = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
sum = Σ(digit[i] × weight[i]) for i in 0..9
remainder = sum % 11
digit_11 = 0 if remainder < 2 else (11 - remainder)
```

### Invalid CPFs (all same digits)
`000.000.000-00`, `111.111.111-11`, ..., `999.999.999-99` — rejected despite passing algorithm.

## Implementation in synthfin-data

```
src/fraud_generator/validators/cpf.py
├── validate_cpf(cpf: str) → bool    # Check if CPF is algorithmically valid
└── generate_valid_cpf() → str        # Generate random valid CPF (11-digit string)
```

## Rules for Agents

1. **NEVER mock CPF**: Always use `generate_valid_cpf()` from `validators/cpf.py`
2. **Store as string**: CPFs with leading zeros would lose data as integers
3. **Validate on generation**: Every customer entity gets a validated CPF at creation time
4. **No third-party**: The validator is self-contained — no external libs needed
