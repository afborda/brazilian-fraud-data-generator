# Entity Chain Pattern

> The foundational pattern for synthetic data generation in synthfin-data.

## Pattern

Every transaction requires parent entities created in strict order:

```
Customer (1) → Device (N) → Transaction (M)
```

- One Customer can have N Devices
- One Device can generate M Transactions
- A Transaction ALWAYS has a parent Customer AND Device

## Implementation

### Batch Mode (generate.py)

```
1. CustomerGenerator.generate(count=K)     → List[Customer]
   │  Creates: CUST_* IDs, CPF, profile, income_class, state
   │
2. DeviceGenerator.generate(customers)     → List[Device]
   │  Creates: DEV_* IDs, OS, browser, fingerprint
   │  Links: device.customer_id → customer.id
   │
3. TransactionGenerator.generate(customers, devices) → Iterator[Transaction]
      Creates: TX_* IDs, amount, type, channel, fraud signals
      Links: tx.customer_id, tx.device_id
      Uses: CustomerIndex, DeviceIndex for fast lookup
```

### Streaming Mode (stream.py)

```
1. Create small pool of customers + devices (in-memory)
2. Loop:
   a. Pick random customer from pool
   b. Pick random device for that customer
   c. Generate single transaction
   d. Send to connection (stdout/kafka/webhook)
   e. Optionally: rotate customer pool
```

### Index Objects

- `CustomerIndex`: Groups customers by state for geographic consistency
- `DeviceIndex`: Maps customer_id → list of devices
- `RideIndex`: Groups drivers by state (ride-share mode)
- Built by: `src/fraud_generator/cli/index_builder.py`

## Rules

1. **Never skip entities**: Don't generate transactions without parent customer + device
2. **Index before generate**: Build index objects BEFORE entering generator loop
3. **Memory model**: Indexes are in-memory lookup tables — generators don't store state
4. **ID format**: `CUST_XXXXXXXX`, `DEV_XXXXXXXX`, `TX_XXXXXXXX` (8-char hex suffix)
5. **Seed order**: `random.seed()` → Customer gen → Device gen → TX gen (deterministic)

## Anti-Patterns

- **Orphan transactions**: TX without valid customer_id/device_id
- **Re-generating parents**: Creating new customers inside the TX generator loop
- **Stateful generators**: Storing transaction history in the generator (use enrichers instead)
