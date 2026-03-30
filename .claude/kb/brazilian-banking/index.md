# Brazilian Banking — Knowledge Base

> Domain entry point for Brazilian banking context used in synthetic fraud data generation.

## Scope

This KB covers Brazilian financial system specifics needed to generate realistic fraud datasets:
- PIX instant payment protocol
- Bank codes and ISPB identifiers
- CPF (Cadastro de Pessoas Físicas) validation
- BCB (Banco Central do Brasil) calibration data
- Fraud pattern definitions and injection logic

## Quick Navigation

| Topic | File | When to Load |
|-------|------|-------------|
| PIX protocol basics | [concepts/pix-protocol.md](concepts/pix-protocol.md) | Working with PIX transactions or fraud types |
| Bank codes & ISPB | [concepts/bank-codes-ispb.md](concepts/bank-codes-ispb.md) | Adding/validating bank entities |
| CPF validation | [concepts/cpf-validation.md](concepts/cpf-validation.md) | Customer generation or ID validation |
| Fraud injection pattern | [patterns/fraud-injection.md](patterns/fraud-injection.md) | Creating or modifying fraud types |
| BCB calibration | [patterns/bcb-calibration.md](patterns/bcb-calibration.md) | Calibrating distributions against real data |
| Fraud type specs | [specs/fraud-types.yaml](specs/fraud-types.yaml) | Machine-readable fraud type definitions |

## Key Facts

- Brazil has **800+** financial institutions registered with BCB
- PIX processes **4+ billion** transactions/month (2025 data)
- CPF has an algorithmic check digit — random 11-digit strings are INVALID
- synthfin-data currently models **25 banking fraud types** and **17 risk signals**
