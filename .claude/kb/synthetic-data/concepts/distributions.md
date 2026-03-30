# Statistical Distributions

> How synthfin-data models realistic value distributions.

## Transaction Amount Distribution

### Model: Lognormal

Real banking transaction amounts follow a **lognormal distribution** — most transactions are small, with a long right tail of large amounts.

```
X ~ LogNormal(μ, σ)
where μ = log-mean, σ = log-standard-deviation
```

### Configuration

- Location: `src/fraud_generator/config/distributions.py`
- Function: `get_transaction_value(profile, income_class)`
- Income classes calibrated against BCB data:

| Class | μ | σ | Median (R$) | Use Case |
|-------|---|---|-------------|----------|
| A | 7.2 | 1.1 | ~1,340 | High-income customers |
| B | 6.5 | 1.0 | ~665 | Upper-middle |
| C | 5.8 | 0.9 | ~330 | Middle (largest segment) |
| D/E | 5.0 | 0.8 | ~148 | Low-income |

### Fraud Amount Deviation

Fraud transactions use `anomaly_multiplier` to deviate from normal:
```python
fraud_amount = normal_amount × anomaly_multiplier × random.uniform(0.8, 1.5)
```
The `amount_zscore` enricher signal measures this deviation.

## Geographic Distribution

- Brazilian states weighted by population + economic activity
- Config: `src/fraud_generator/config/geography.py`
- São Paulo: ~30% weight, followed by RJ, MG, RS, PR

## Temporal Distribution

- Hourly weights follow real banking patterns
- Config: `src/fraud_generator/config/seasonality.py`
- Two peaks: 10h-12h (business), 18h-20h (post-work)
- Fraud has DIFFERENT temporal pattern: higher at off-peak hours

## Validation

Quality benchmark tests distributions via:
- **KS-test**: Kolmogorov-Smirnov against expected distribution (α=0.05)
- **Chi-squared**: Categorical field uniformity test
- **Visual**: Amount histogram should show lognormal shape
