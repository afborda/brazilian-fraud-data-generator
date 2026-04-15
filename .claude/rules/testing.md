---
description: pytest conventions, fixture patterns, conftest.py, test naming, seed management, CPF handling
paths:
  - "tests/**"
---

# Testing Rules

## Conventions
- Use pytest functions, NOT `unittest.TestCase` classes
- File naming: `tests/unit/test_{module}.py` or `tests/integration/test_{workflow}.py`
- Function naming: `test_{behavior}_when_{condition}` or `test_{behavior}_{result}`

## Fixtures
- Project-wide: `tests/conftest.py` → `temp_output_dir`, `test_seed`, `sample_customer_data`, `sample_transaction_data`
- Module-specific in local `conftest.py` files
- Use `tmp_path` for temporary files, `monkeypatch` for env vars

## CPF Handling
- NEVER mock CPF — use real `generate_valid_cpf()` from `validators/cpf.py`
- CPF = valid 11-digit string, always

## Seed Management
- Set `random.seed()` BEFORE constructing generators
- Use seed 42 for consistency
- Test distribution properties, not exact random values

## Structure
```python
def test_behavior_when_condition(test_seed):
    random.seed(test_seed)
    result = function_under_test()
    assert result.field == expected_value
```
