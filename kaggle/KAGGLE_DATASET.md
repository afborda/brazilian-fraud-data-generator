# 🇧🇷 Brazilian Banking Fraud Dataset — 268K Transactions, 25 Fraud Types, PIX Fields & Risk Signals

**Synthetic, labeled, and ready for ML** — the most complete Brazilian banking fraud dataset available for research.

## Overview

| Metric | Value |
|--------|-------|
| Transactions | 268,435 |
| Customers | 2,684 |
| Devices | 5,770 |
| Fraud rate | ~1.0% (realistic for Brazil) |
| Fraud types | 25 distinct patterns |
| Features per transaction | 82 |
| Risk signals | 17 behavioral/velocity/device signals |
| Behavioral profiles | 7 customer archetypes |
| Currency | BRL (Brazilian Real) |
| Seed | 42 (fully reproducible) |

## Why This Dataset?

Most fraud datasets are either: (a) from the US/EU market with no PIX/BACEN fields, (b) anonymized beyond usefulness (like IEEE-CIS), or (c) have only 2-3 fraud types. This dataset was built specifically for the **Brazilian financial ecosystem**:

- **PIX fields**: `pix_key_type`, `end_to_end_id`, `ispb_pagador`, `ispb_recebedor`, `modalidade_iniciacao`, `tipo_conta_pagador`, `tipo_conta_recebedor` — following BACEN (Central Bank of Brazil) specifications
- **25 fraud patterns**: From social engineering and PIX scams to deepfake biometric fraud and SIM swap
- **Calibrated with real BCB data**: Fraud rates, transaction amounts, age distributions, and fraud type prevalences were calibrated using data from Brazil's Central Bank (BCB MED — Mecanismo Especial de Devolução), Febraban, and Serasa reports (2022–2026)
- **Valid CPFs**: All customer CPFs pass the official Brazilian validation algorithm
- **Real Brazilian geography**: 27 states, weighted by actual population density (SP 20%, MG 10%, RJ 8%...)
- **Real bank codes**: Itaú (341), Bradesco (237), Nubank (260), Inter (077), etc.

## Files

| File | Records | Size | Description |
|------|---------|------|-------------|
| `transactions.csv` | 268,435 | ~156 MB | All banking transactions with 82 features |
| `customers.csv` | 2,684 | ~0.8 MB | Customer profiles (flattened address) |
| `devices.csv` | 5,770 | ~0.9 MB | Device fingerprints linked to customers |
| `transactions.jsonl` | 268,435 | ~430 MB | Same transactions in JSONL format (nested PIX fields) |
| `customers.jsonl` | 2,684 | ~1.8 MB | Same customers in JSONL (nested address) |
| `devices.jsonl` | 5,770 | ~2.1 MB | Same devices in JSONL |

> **Tip**: Use the CSV files for quick exploration in Kaggle's Data Explorer. Use JSONL if you prefer nested structures.

## Data Dictionary

### transactions.csv — Main table (82 columns)

#### Core Transaction Fields
| Column | Type | Description |
|--------|------|-------------|
| `transaction_id` | string | Unique ID (`TXN_...`) |
| `customer_id` | string | FK to customers (`CUST_...`) |
| `device_id` | string | FK to devices (`DEV_...`) |
| `session_id` | string | Browser/app session |
| `timestamp` | datetime | Transaction datetime (ISO 8601) |
| `type` | string | `PIX`, `CREDIT_CARD`, `DEBIT_CARD`, `TED`, `BOLETO` |
| `amount` | float | Value in BRL |
| `currency` | string | Always `BRL` |
| `channel` | string | `MOBILE_APP`, `WEB`, `ATM`, `BRANCH`, `WHATSAPP` |
| `status` | string | `APPROVED`, `DECLINED`, `PENDING` |
| `ip_address` | string | Source IP |
| `geolocation_lat` | float | Latitude |
| `geolocation_lon` | float | Longitude |

#### Merchant Fields
| Column | Type | Description |
|--------|------|-------------|
| `merchant_id` | string | Merchant identifier |
| `merchant_name` | string | Business name |
| `merchant_category` | string | Category (Restaurants, Supermarkets, ...) |
| `mcc_code` | string | Merchant Category Code (ISO 18245) |
| `mcc_risk_level` | string | `low`, `medium`, `high` |

#### Card Fields (non-PIX transactions)
| Column | Type | Description |
|--------|------|-------------|
| `card_number_hash` | string | Hashed card number |
| `card_brand` | string | `VISA`, `MASTERCARD`, `ELO`, `HIPERCARD` |
| `card_type` | string | `CREDIT`, `DEBIT` |
| `installments` | int | Number of installments (1–12) |
| `card_entry` | string | `CHIP`, `CONTACTLESS`, `MANUAL`, `ONLINE` |
| `cvv_validated` | bool | CVV check passed |
| `auth_3ds` | bool | 3D Secure authentication |

#### PIX/BACEN Fields (PIX transactions only)
| Column | Type | Description |
|--------|------|-------------|
| `pix_key_type` | string | `CPF`, `CNPJ`, `EMAIL`, `PHONE`, `RANDOM` |
| `pix_key_destination` | string | Hashed destination key |
| `destination_bank` | string | Receiving bank code |
| `end_to_end_id` | string | BACEN End-to-End ID (E2E) |
| `ispb_pagador` | string | ISPB code — paying institution |
| `ispb_recebedor` | string | ISPB code — receiving institution |
| `tipo_conta_pagador` | string | `CACC` (current), `SVGS` (savings), `SLRY` (salary) |
| `tipo_conta_recebedor` | string | Account type of receiver |
| `holder_type_recebedor` | string | `CUSTOMER`, `MERCHANT` |
| `modalidade_iniciacao` | string | `CHAVE`, `QRCODE_STATIC`, `QRCODE_DYNAMIC` |

#### Behavioral & Risk Signals
| Column | Type | Description |
|--------|------|-------------|
| `cliente_perfil` | string | Behavioral profile (see Profiles section) |
| `classe_social` | string | `A`, `B1`, `B2`, `C1`, `C2`, `D-E` |
| `unusual_time` | bool | Transaction at unusual hour for this customer |
| `new_beneficiary` | bool | First transaction to this recipient |
| `new_merchant` | bool | First transaction at this merchant |
| `velocity_transactions_24h` | int | Number of transactions in last 24h |
| `accumulated_amount_24h` | float | Total BRL spent in last 24h |
| `customer_velocity_z_score` | float | Z-score of transaction velocity vs. customer's baseline |
| `device_new_for_customer` | bool | Device not previously seen for this customer |
| `device_age_days` | int | Days since device first used |
| `emulator_detected` | bool | Android emulator detected |
| `vpn_active` | bool | VPN connection detected |
| `ip_type` | string | `RESIDENTIAL`, `MOBILE`, `DATACENTER`, `VPN` |
| `sim_swap_recent` | bool | Recent SIM swap on phone number |
| `ip_location_matches_account` | bool | IP geolocation matches account address |
| `active_call_during_tx` | bool | Phone call active during transaction |
| `is_probe_transaction` | bool | Small test transaction pattern |
| `is_impossible_travel` | bool | Location impossible given last transaction |
| `distance_from_last_km` | float | KM from last transaction location |
| `hours_inactive` | int | Hours since last activity |
| `network_type` | string | `WIFI`, `4G`, `5G`, `3G` |
| `bot_confidence_score` | float | Probability of automated behavior (0–1) |
| `automation_signature` | string | `HUMAN`, `SCRIPTED`, `BOT` |
| `recipient_is_mule` | bool | Recipient flagged as money mule |

#### Fraud Labels (TARGET VARIABLES)
| Column | Type | Description |
|--------|------|-------------|
| `is_fraud` | bool | **Binary target** — `True` if fraudulent |
| `fraud_type` | string | Fraud category (25 types, empty if legitimate) |
| `fraud_score` | int | Fraud likelihood score (0–100) |
| `fraud_risk_score` | int | Risk score from enricher pipeline (0–100) |
| `fraud_signals` | string | Pipe-separated list of triggered signals |

### customers.csv
| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | string | Primary key |
| `name` | string | Full name (Faker pt_BR) |
| `cpf` | string | Valid Brazilian CPF (xxx.xxx.xxx-xx) |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `birth_date` | date | Date of birth |
| `monthly_income` | float | Monthly income in BRL |
| `profession` | string | Occupation |
| `credit_score` | int | Credit score (300–900) |
| `risk_level` | string | `LOW`, `MEDIUM`, `HIGH` |
| `bank_name` | string | Primary bank |
| `behavioral_profile` | string | One of 7 profiles |
| `address_city` | string | City |
| `address_state` | string | State (UF — 2 letters) |
| `address_postal_code` | string | CEP (Brazilian ZIP) |

### devices.csv
| Column | Type | Description |
|--------|------|-------------|
| `device_id` | string | Primary key |
| `customer_id` | string | FK to customers |
| `type` | string | `SMARTPHONE`, `TABLET`, `DESKTOP`, `LAPTOP` |
| `manufacturer` | string | Samsung, Apple, Motorola, Xiaomi... |
| `model` | string | Device model |
| `operating_system` | string | OS + version |
| `is_trusted` | bool | Device marked as trusted |
| `rooted_or_jailbreak` | bool | Root/jailbreak detected |
| `device_age_days` | int | Days since first use |

## The 25 Fraud Types

| Fraud Type | Prevalence | Description |
|------------|-----------|-------------|
| `ENGENHARIA_SOCIAL` | 15.0% | Social engineering — impersonating bank employees via phone/WhatsApp |
| `PIX_GOLPE` | 13.1% | PIX scams — fake QR codes, cloned links, fake payment receipts |
| `CONTA_TOMADA` | 8.2% | Account takeover — stolen credentials, new device login |
| `CARTAO_CLONADO` | 6.7% | Cloned card (75% are CNP — Card Not Present) |
| `FRAUDE_APLICATIVO` | 6.3% | App fraud — fake banking apps, overlay attacks |
| `BOLETO_FALSO` | 5.2% | Fake boleto — altered barcode redirecting payment |
| `FALSA_CENTRAL_TELEFONICA` | 4.9% | Fake call center — "your account was compromised" |
| `COMPRA_TESTE` | 4.8% | Test purchases — small amounts to validate stolen cards |
| `MULA_FINANCEIRA` | 4.3% | Money mule — accounts used to launder fraud proceeds |
| `CARD_TESTING` | 3.7% | Card testing — automated small-value probes |
| `MICRO_BURST_VELOCITY` | 2.8% | Micro-burst — multiple transactions in seconds |
| `WHATSAPP_CLONE` | 2.8% | WhatsApp cloning — hijacked messaging to request money |
| `DISTRIBUTED_VELOCITY` | 2.5% | Distributed velocity — same card across many merchants |
| `PHISHING_BANCARIO` | 2.4% | Bank phishing — fake login pages, SMS links |
| `FRAUDE_QR_CODE` | 2.0% | QR Code fraud — tampered QR at point of sale |
| `FRAUDE_DELIVERY_APP` | 2.0% | Delivery app fraud — fake orders, payment manipulation |
| `MAO_FANTASMA` | 1.9% | Ghost hand — remote access trojan controlling device |
| `CREDENTIAL_STUFFING` | 1.7% | Credential stuffing — reusing leaked passwords |
| `EMPRESTIMO_FRAUDULENTO` | 1.7% | Fraudulent loan — taken using stolen identity |
| `GOLPE_INVESTIMENTO` | 1.7% | Investment scam — fake high-return schemes |
| `SIM_SWAP` | 1.6% | SIM swap — hijacking phone number for 2FA bypass |
| `PIX_AGENDADO_FRAUDE` | 1.5% | Scheduled PIX fraud — delayed execution to evade detection |
| `SEQUESTRO_RELAMPAGO` | 1.4% | Express kidnapping — physical coercion for transfers |
| `SYNTHETIC_IDENTITY` | 1.1% | Synthetic identity — fabricated identity for credit |
| `DEEP_FAKE_BIOMETRIA` | 0.8% | Deepfake biometric — AI-generated face/voice for KYC bypass |

## 7 Behavioral Profiles

Each customer is assigned one sticky behavioral profile that determines their transaction patterns:

| Profile | Description | Typical Transactions |
|---------|-------------|---------------------|
| `young_digital` | 18–29, mobile-first, PIX-heavy | Many small PIX, food delivery, streaming |
| `conservative_senior` | 55+, branch-preferred, card-heavy | Large card purchases, few PIX |
| `business_owner` | SME owner, high volume, mixed channels | High-value TED/PIX, supplier payments |
| `suburban_family` | 30–50, supermarket/school/health | Regular boleto, medium PIX |
| `subscription_heavy` | Digital nomad, recurring payments | Streaming, SaaS, international services |
| `cash_heavy` | Prefers ATM/branch, low digital adoption | ATM withdrawals, branch deposits |
| `high_income` | Premium banking, high limits | Large investments, international transfers |

## Calibration Sources — Where the Data Patterns Come From

This dataset was **not generated with random distributions**. Every key parameter was calibrated against real Brazilian financial data:

### Primary Sources

| Source | Data Used | Period |
|--------|-----------|--------|
| **BCB — Mecanismo Especial de Devolução (MED)** | PIX fraud rates per 100K transactions, monthly fraud volumes, average fraud ticket values | Jan/2022 – Jan/2026 |
| **BCB — Estatísticas PIX** | Transaction volume by age group, average PIX values by person type (PF/PJ), channel distribution | 2022–2026 |
| **Febraban — CIAB Report** | Day-of-week transaction distribution, peak hours, digital banking adoption rates | 2023–2024 |
| **Serasa Experian** | Fraud type prevalences (social engineering 28%, PIX scams 25%, account takeover 15%...) | 2024–2025 |

### Key Calibration Points

| Parameter | Real Value (BCB/Febraban) | In This Dataset |
|-----------|--------------------------|-----------------|
| PIX fraud rate | 4.4–9.5 per 100K PIX transactions | ~1.0% across all transaction types |
| Average legitimate PIX (PF) | R$ 188.85 | R$ 238 (includes non-PIX) |
| Average fraud amount | R$ 1,778–2,979 | R$ 1,210 |
| Fraud/legitimate amount ratio | 14×–18× | 5× (conservative for ML training) |
| Top fraud type | Social engineering (28%) | `ENGENHARIA_SOCIAL` (15%) |
| Peak transaction hours | 10h, 14h, 19h | 10h, 14h, 19h ✅ |
| Geographic concentration (SP+RJ+MG) | ~40% of financial volume | 38.2% ✅ |
| Elderly fraud ticket | R$ 4,820 (5× higher) | Modeled via profiles |

> **Full calibration methodology**: See the [BCB Calibration Document](https://github.com/afborda/synthfin-data/blob/main/docs/CALIBRACAO_DADOS_REAIS_BCB.md) in the source repository.

## How the Tool Works — Generation Pipeline

This dataset was generated by [**synthfin-data**](https://github.com/afborda/synthfin-data) (v4.9.1), an open-source synthetic data generator for Brazilian banking fraud research.

### Architecture

```
Seed (42) → Customer Pool → Device Assignment → Transaction Generation
                                                       ↓
                                              8-Stage Enricher Pipeline
                                                       ↓
                                    Temporal → Geo → Fraud Injection → PIX/BACEN
                                         → Device → Session → Risk Score → Output
```

### The 8-Stage Enricher Pipeline

Each transaction passes through 8 sequential enrichment stages:

1. **Temporal Enricher**: Assigns realistic timestamps following Brazilian banking hours (peak at 10h, 14h, 19h; low at 2h–5h)
2. **Geographic Enricher**: Assigns coordinates consistent with customer's state, weighted by population density
3. **Fraud Injector**: Decides if transaction is fraudulent (~1% rate), selects fraud type by weighted distribution
4. **PIX/BACEN Enricher**: For PIX transactions, generates compliant BACEN fields (E2E ID, ISPB codes, account types)
5. **Device Enricher**: Links device metadata, checks for anomalies (new device, emulator, VPN)
6. **Session Enricher**: Computes velocity signals (transactions in 24h, accumulated amount, Z-scores)
7. **Risk Score Calculator**: Computes `fraud_risk_score` (0–100) from 17 individual signals and 4 correlation rules
8. **Biometric/Output Enricher**: Adds remaining signals (bot score, automation signature, SIM swap) and formats output

### Reproducibility

```bash
# Generate exactly this dataset
python3 generate.py --size 50MB --seed 42 --output ./output
```

Same seed → same customers → same devices → same transactions → same fraud labels. Always.

## License

**Dataset**: Released for **personal study, academic research, and educational purposes** under the synthfin-data [Custom Non-Commercial License](https://github.com/afborda/synthfin-data/blob/main/LICENSE).

**Commercial use** (by companies, in products, or for revenue) requires a paid license from [synthfin.com.br](https://synthfin.com.br).

**Suggested Kaggle license**: CC BY-NC 4.0 (Attribution-NonCommercial)

## Quick Start

```python
import pandas as pd

# Load the data
transactions = pd.read_csv("transactions.csv")
customers = pd.read_csv("customers.csv")
devices = pd.read_csv("devices.csv")

# Check fraud distribution
print(transactions["is_fraud"].value_counts(normalize=True))
# False    0.990
# True     0.010

# Explore fraud types
print(transactions[transactions["is_fraud"]]["fraud_type"].value_counts())

# Join with customer profiles
merged = transactions.merge(customers[["customer_id", "behavioral_profile", "credit_score"]], on="customer_id")
```

## Citation

```bibtex
@misc{synthfin2026,
  author       = {Abner Fonseca},
  title        = {synthfin-data: Synthetic Brazilian Banking Fraud Dataset},
  year         = {2026},
  version      = {4.9.1},
  publisher    = {Kaggle},
  howpublished = {\url{https://kaggle.com/datasets/afborda/brazilian-banking-fraud}},
  note         = {268K transactions, 25 fraud types, PIX/BACEN fields, calibrated with BCB data}
}
```

## Tags

`fraud-detection`, `binary-classification`, `banking`, `brazil`, `pix`, `finance`, `synthetic-data`, `imbalanced-classification`, `anti-fraud`, `machine-learning`

## Links

- **Source code**: [github.com/afborda/synthfin-data](https://github.com/afborda/synthfin-data)
- **Hosted API**: [synthfin.com.br](https://synthfin.com.br)
- **Author**: [Abner Fonseca](https://github.com/afborda)
