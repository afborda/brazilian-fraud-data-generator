# Brazilian Banking — Quick Reference

## Bank Code Format
- **ISPB**: 8-digit code (Instituto de Sistema de Pagamentos Brasileiro)
- **COMPE**: 3-digit code (legacy clearing system)
- Config: `src/fraud_generator/config/banks.py` → `BANK_CODES`, `BANK_WEIGHTS`

## PIX Key Types
| Type | Format | Example |
|------|--------|---------|
| CPF | 11 digits | 12345678901 |
| CNPJ | 14 digits | 12345678000190 |
| Email | email | user@domain.com |
| Phone | +55DDDNUMBER | +5511999998888 |
| Random (EVP) | UUID v4 | 123e4567-e89b-... |

## CPF Validation Algorithm
1. Multiply first 9 digits by weights 10→2, sum, mod 11
2. If remainder < 2 → check digit = 0, else 11 - remainder
3. Repeat with 10 digits and weights 11→2 for second check digit
- Implementation: `src/fraud_generator/validators/cpf.py`
- NEVER mock CPF — always use `generate_valid_cpf()`

## Transaction Types (synthfin-data)
| Type | Config Key | Description |
|------|-----------|-------------|
| PIX | `pix` | Instant payment (dominant) |
| TED | `ted` | Wire transfer |
| DOC | `doc` | Legacy transfer |
| Boleto | `boleto` | Payment slip |
| Card | `cartao_credito/debito` | Credit/debit card |

## Fraud Categories (25 types)
- **PIX**: Cloning, social engineering, account takeover, man-in-the-middle
- **Card**: Takeover, skimming, CNP fraud, counterfeit
- **Account**: Credential stuffing, SIM swap, money mule
- **Behavioral**: Velocity abuse, amount escalation, geographic anomaly
- Config: `src/fraud_generator/config/fraud_patterns.py`

## Key Enrichment Signals (17)
`bot_confidence`, `device_age_days`, `velocity_24h`, `amount_zscore`,
`geo_velocity_kmh`, `new_beneficiary`, `session_duration_seconds`,
`device_fingerprint_change`, `ip_risk_score`, `transaction_hour_risk`,
`pix_modalidade_risk`, `installment_risk`, `mcc_risk`, `channel_risk`,
`biometric_score`, `account_age_days`, `historical_fraud_count`
