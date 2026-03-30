# PIX Protocol

> Brazilian instant payment system operated by BCB (Banco Central do Brasil).

## Overview

PIX is the dominant payment method in Brazil, processing 4+ billion transactions monthly. It operates 24/7/365 with settlement in under 10 seconds.

## Architecture

```
Payer → PSP (Payment Service Provider) → SPI (Sistema de Pagamentos Instantâneos) → PSP → Payee
```

- **SPI**: Central infrastructure operated by BCB
- **DICT**: Diretório de Identificadores de Contas Transacionais (key directory)
- **PSP**: Banks and fintechs authorized to offer PIX

## Key Fields in synthfin-data

| Field | Config Location | Values |
|-------|----------------|--------|
| `pix_modalidade_iniciacao` | `config/pix.py` → `MODALIDADE_INICIACAO_LIST` | manual, qr_code_estatico, qr_code_dinamico, qr_code_pix_cobranca |
| `pix_tipo_conta` | `config/pix.py` → `TIPO_CONTA_LIST` | conta_corrente, conta_poupanca, conta_pagamento, conta_salario |
| `pix_holder_type` | `config/pix.py` | PF (pessoa física), PJ (pessoa jurídica) |
| `end_to_end_id` | `config/pix.py` → `generate_end_to_end_id()` | E + ISPB(8) + timestamp + sequence |

## PIX Fraud Patterns

| Pattern | synthfin Key | Description |
|---------|-------------|-------------|
| QR Code Cloning | `pix_cloning` | Attacker replaces merchant QR with their own |
| Social Engineering | `pix_social_engineering` | Victim tricked into sending PIX to fraudster |
| Account Takeover | `pix_account_takeover` | Fraudster gains access to victim's PIX account |
| SIM Swap | `sim_swap_pix` | Attacker takes over phone number to intercept PIX |
| Man-in-the-Middle | `pix_mitm` | Intercept and modify PIX transaction in transit |

## Enrichment Signals for PIX

- `pix_modalidade_risk`: QR dinâmico > QR estático > manual (risk ordering)
- `new_beneficiary`: First-time payee flag (high signal for PIX fraud)
- `velocity_24h`: PIX transactions in last 24h (velocity check)
- `amount_zscore`: Deviation from customer's typical PIX amount

## BCB Calibration

Real-world PIX distribution (BCB 2024 data):
- **70%** of PIX transactions are P2P (pessoa-to-pessoa)
- **Average value**: R$ 280 (P2P), R$ 450 (P2B commerce)
- **Peak hours**: 10h-12h and 18h-20h
- Config: `src/fraud_generator/config/calibration_loader.py`
