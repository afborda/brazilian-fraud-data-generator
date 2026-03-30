# Synthetic Data — Knowledge Base

> Domain entry point for synthetic data generation patterns and best practices.

## Scope

This KB covers data generation techniques used in synthfin-data:
- Statistical distributions for realistic value generation
- Behavioral profiles that drive entity-level consistency
- Entity chain pattern (Customer → Device → Transaction)
- Weighted random selection and caching strategies

## Quick Navigation

| Topic | File | When to Load |
|-------|------|-------------|
| Distribution models | [concepts/distributions.md](concepts/distributions.md) | Working with amount/value generation |
| Behavioral profiles | [concepts/behavioral-profiles.md](concepts/behavioral-profiles.md) | Profile-aware generation or fraud patterns |
| Entity chain | [patterns/entity-chain.md](patterns/entity-chain.md) | Modifying generator pipeline |
| Weighted random | [patterns/weighted-random.md](patterns/weighted-random.md) | Performance optimization or new weighted selections |

## Key Metrics

- **Quality Score**: 9.70/10 (A+) via `benchmarks/data_quality_benchmark.py`
- **AUC-ROC**: 0.9991 (fraud vs legit separation)
- **Average Precision**: 0.9732
- **7 quality batteries**: completeness, uniqueness, validity, consistency, distributions, fraud quality, patterns
