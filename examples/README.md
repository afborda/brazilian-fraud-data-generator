# 📄 Example Output

This directory contains examples of the generated data format.

## Files Generated

### customers.json
One customer per line (JSON Lines format):

```json
{"customer_id": "CUST_00000001", "nome": "Maria Fernanda Ribeiro", "cpf": "123.456.789-00", "email": "maria.ribeiro@email.com", "telefone": "(11) 98765-4321", "data_nascimento": "1985-03-15", "endereco": {"logradouro": "Rua das Flores, 123", "cidade": "São Paulo", "estado": "SP", "cep": "01234-567"}, "conta_criada_em": "2022-01-15T14:30:00", "tipo_conta": "CORRENTE", "status_conta": "ATIVA", "limite_credito": 15000.00, "score_credito": 750, "nivel_risco": "BAIXO", "banco_codigo": "341", "agencia": "1234", "numero_conta": "567890-1"}
```

### transactions_XXXXX.json
Multiple transaction files, each ~128MB:

```json
{"transaction_id": "TXN_000000000000001", "customer_id": "CUST_00000001", "session_id": "SESS_000000000001", "device_id": "DEV_00000001", "timestamp": "2024-01-15T14:30:00", "tipo": "PIX", "valor": 250.00, "moeda": "BRL", "canal": "APP_MOBILE", "ip_address": "177.45.123.89", "geolocalizacao_lat": -23.550520, "geolocalizacao_lon": -46.633308, "merchant_id": "MERCH_001234", "merchant_name": "iFood", "merchant_category": "Fast Food", "mcc_code": "5814", "mcc_risk_level": "low", "numero_cartao_hash": null, "bandeira": null, "tipo_cartao": null, "parcelas": null, "entrada_cartao": null, "cvv_validado": null, "autenticacao_3ds": null, "chave_pix_tipo": "CPF", "chave_pix_destino": "987.654.321-00", "banco_destino": "260", "distancia_ultima_transacao_km": null, "tempo_desde_ultima_transacao_min": 45, "transacoes_ultimas_24h": 3, "valor_acumulado_24h": 580.50, "horario_incomum": false, "novo_beneficiario": false, "status": "APROVADA", "motivo_recusa": null, "fraud_score": 12.5, "is_fraud": false, "fraud_type": null}
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
        print(tx['transaction_id'], tx['valor'], tx['is_fraud'])
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
