# BCB Calibration

> Calibrating synthetic data distributions against real Banco Central do Brasil statistics.

## Purpose

synthfin-data uses BCB (Banco Central do Brasil) public statistics to ensure generated transaction distributions match real-world patterns. This improves ML model training quality.

## Calibration Sources

| Source | Data | synthfin Usage |
|--------|------|----------------|
| BCB SGS (time series) | PIX volume, TED/DOC counts | Transaction type weights |
| BCB Payment Stats | Average values per channel | Amount distributions (lognormal) |
| FEBRABAN reports | Bank market share | Bank weights in `config/banks.py` |
| BCB Fraud Reports | Fraud rates per channel | `fraud_rate` default calibration |

## Calibrated Parameters

### Transaction Value Distribution
- Model: **Lognormal** (matches real banking data)
- Config: `src/fraud_generator/config/distributions.py`
- Parameters calibrated per income class:
  - Class A: μ=7.2, σ=1.1 (median ~R$1,340)
  - Class B: μ=6.5, σ=1.0 (median ~R$665)
  - Class C: μ=5.8, σ=0.9 (median ~R$330)
  - Class D/E: μ=5.0, σ=0.8 (median ~R$148)

### Transaction Type Weights (BCB 2024)
| Type | Real Share | synthfin Weight |
|------|-----------|----------------|
| PIX | 65% | 0.65 |
| Card (credit+debit) | 22% | 0.22 |
| TED | 7% | 0.07 |
| Boleto | 5% | 0.05 |
| DOC | 1% | 0.01 |

### Temporal Distribution
- Peak: 10h-12h (30% of daily volume)
- Secondary peak: 18h-20h (20%)
- Trough: 00h-06h (<5%)
- Config: `src/fraud_generator/config/seasonality.py`

### Fraud Rate Calibration
- BCB reported fraud rate: ~0.007% of PIX transactions (2024)
- synthfin default `--fraud-rate`: 0.02 (2%) for ML utility (class imbalance)
- Configurable: `--fraud-rate 0.007` for realistic simulation

## How to Update Calibration

1. Obtain new BCB data (annual reports, SGS series)
2. Update parameters in `config/calibration_loader.py`
3. Run quality benchmark: `python benchmarks/data_quality_benchmark.py`
4. Verify distributions via KS-test (should not reject at α=0.05)
5. Update `docs/analysis/CALIBRACAO_DADOS_REAIS_BCB.md` with new data source
