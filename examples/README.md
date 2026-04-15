# 📄 Example Output

This directory contains examples of the generated data format.

## Files Generated

### customers.json
One customer per line (JSON Lines format):

```json
{"customer_id": "CUST_00000001", "name": "Maria Fernanda Ribeiro", "cpf": "123.456.789-00", "email": "maria.ribeiro@email.com", "phone": "(11) 98765-4321", "birth_date": "1985-03-15", "address": {"street": "Rua das Flores, 123", "city": "São Paulo", "state": "SP", "postal_code": "01234-567"}, "account_created_at": "2022-01-15T14:30:00", "account_type": "CHECKING", "account_status": "ACTIVE", "credit_limit": 15000.00, "credit_score": 750, "risk_level": "LOW", "bank_code": "341", "branch": "1234", "account_number": "567890-1"}
```

### transactions_XXXXX.json
Multiple transaction files, each ~128MB:

```json
{"transaction_id": "TXN_000000000000001", "customer_id": "CUST_00000001", "session_id": "SESS_000000000001", "device_id": "DEV_00000001", "timestamp": "2024-01-15T14:30:00", "type": "PIX", "amount": 250.00, "currency": "BRL", "channel": "MOBILE_APP", "ip_address": "177.45.123.89", "geolocation_lat": -23.550520, "geolocation_lon": -46.633308, "merchant_id": "MERCH_001234", "merchant_name": "iFood", "merchant_category": "Fast Food", "mcc_code": "5814", "mcc_risk_level": "low", "card_number_hash": null, "card_brand": null, "card_type": null, "installments": null, "card_entry": null, "cvv_validated": null, "auth_3ds": null, "pix_key_type": "CPF", "pix_key_destination": "987.654.321-00", "destination_bank": "260", "distance_from_last_txn_km": null, "time_since_last_txn_min": 45, "transactions_last_24h": 3, "accumulated_amount_24h": 580.50, "unusual_time": false, "new_beneficiary": false, "status": "APPROVED", "refusal_reason": null, "fraud_score": 12.5, "is_fraud": false, "fraud_type": null}
```

## Reading the Data

### Python
```python
import json

# Read customers
with open('output/customers.json', 'r') as f:
    customers = [json.loads(line) for line in f]

# Read transactions (streaming for large files)
with open('output/transactions_00000.json', 'r') as f:
    for line in f:
        tx = json.loads(line)
        print(tx['transaction_id'], tx['amount'], tx['is_fraud'])
```

### PySpark
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Read all transaction files
df = spark.read.json('output/transactions_*.json')
df.printSchema()
df.show(5)
```

### Pandas
```python
import pandas as pd

# Single file
df = pd.read_json('output/transactions_00000.json', lines=True)

# Multiple files
import glob
files = glob.glob('output/transactions_*.json')
df = pd.concat([pd.read_json(f, lines=True) for f in files])
```
