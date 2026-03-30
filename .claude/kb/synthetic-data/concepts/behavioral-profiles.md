# Behavioral Profiles

> Customer behavioral profiles that drive consistent transaction patterns.

## Core Concept

Each customer is assigned ONE behavioral profile at creation time. This profile determines:
- Transaction types they prefer
- Typical transaction values
- Preferred channels (app, web, ATM, branch)
- Active hours
- MCC (merchant category) preferences
- Device usage patterns

## The 7 Transaction Profiles

| Profile | Key | Characteristics |
|---------|-----|-----------------|
| **Young Digital** | `young_digital` | Mobile-first, PIX heavy, low amounts, late hours |
| **Business Owner** | `business_owner` | High values, TED/PIX, business hours, diverse MCC |
| **Senior Traditional** | `senior_traditional` | Branch/ATM, boleto, lower tech, regular hours |
| **High Income** | `high_income` | Large amounts, credit card, travel MCCs |
| **Student** | `student` | Very low amounts, PIX, food/transport MCCs |
| **Rural Worker** | `rural_worker` | Infrequent, boleto/PIX, agricultural MCCs |
| **Urban Professional** | `urban_professional` | Balanced, card+PIX, commute hours |

## Profile Assignment

```python
# At customer creation time (ONE TIME — sticky)
profile = random.choices(PROFILE_KEYS, weights=PROFILE_WEIGHTS)[0]
customer.behavioral_profile = profile

# At transaction generation time (EVERY TX — lookup)
tx_type = get_transaction_type_for_profile(profile)
tx_value = get_transaction_value_for_profile(profile)
tx_hour = get_transaction_hour_for_profile(profile)
tx_channel = get_channel_for_profile(profile)
tx_mcc = get_mcc_for_profile(profile)
```

## Implementation

- Config: `src/fraud_generator/profiles/behavioral.py`
- Key functions: `get_*_for_profile(profile_key)` — all return weighted random choices
- Ride profiles: `src/fraud_generator/profiles/ride_behavioral.py` — maps TX profiles to ride preferences

## Rules

1. **Stickiness**: NEVER reassign a profile after customer creation
2. **Consistency**: A `student` should NOT get `high_income` transaction values
3. **Coverage**: All 7 profiles should appear in generated data (check with benchmark)
4. **Override**: Fraud injection CAN override profile-typical behavior (that's what makes it anomalous)
5. **Weights**: Profile distribution is configurable but defaults should match Brazilian demographics
