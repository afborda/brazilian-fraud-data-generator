# 🔌 GUIA TÉCNICO DE COMPONENTES & USO

**Data:** 3 de Março de 2026  
**Versão:** 4.0.0  
**Propósito:** Referência técnica detalhada para desenvolvedores

---

## 📖 COMO USAR CADA COMPONENTE

### 1️⃣ GENERATORS - Gerando Dados

#### CustomerGenerator
```python
from fraud_generator.generators import CustomerGenerator

# Criar gerador
gen = CustomerGenerator(
    use_profiles=True,    # Usa perfis comportamentais
    seed=42               # Reproduzível
)

# Gerar um cliente
customer = gen.generate(customer_id="CUST_001")
# Retorna: {
#   'customer_id': 'CUST_001',
#   'cpf': '12345678900',  # CPF válido (check digits corretos)
#   'name': 'João Silva',
#   'email': 'joao@example.com',
#   'phone': '11987654321',
#   'income': 5000.00,     # Baseado em perfil
#   'profile_type': 'young_digital',  # Um de 7 tipos
#   'state': 'SP',         # Com pesos: SP 25%, RJ 10%, etc
#   'risk_score': 0.25,    # Inversamente proporcional à idade
#   'created_at': '2023-01-15'
# }

# Gerar batch
customers = gen.generate_batch(count=1000, start_id=1)
# Retorna: list[dict] com 1000 clientes

# Acessar estrutura de dados
print(customer.get('profile_type'))  # 'young_digital'
income_per_profile = {
    'young_digital': 2000,
    'business_owner': 15000,
    'retiree': 3000,
    # etc
}
```

#### DeviceGenerator
```python
from fraud_generator.generators import DeviceGenerator

gen = DeviceGenerator(seed=42)

# Gerar um dispositivo
device = gen.generate(
    device_id="DEV_001",
    customer_id="CUST_001"
)
# Retorna: {
#   'device_id': 'DEV_001',
#   'customer_id': 'CUST_001',
#   'ip_address': '186.200.XXX.XXX',  # IP Brasil válido
#   'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)',
#   'device_type': 'MOBILE',
#   'os': 'iOS',
#   'browser': 'Safari',
#   'device_model': 'iPhone 12',
#   'created_at': '2023-01-15'
# }

# Cada customer tem 2-3 dispositivos típicos
devices = gen.generate_batch(count=3, customer_id="CUST_001")
```

#### TransactionGenerator
```python
from fraud_generator.generators import TransactionGenerator
from fraud_generator.utils import CustomerIndex, DeviceIndex

# Preparar índices (cache de lookups)
customer_index = CustomerIndex(customers_list)
device_index = DeviceIndex(devices_list)

# Criar gerador
gen = TransactionGenerator(
    use_profiles=True,      # Transações baseadas em perfil
    fraud_rate=0.02,        # 2% das transações são fraude
    seed=42
)

# Gerar uma transação
tx = gen.generate(
    tx_id="TX_00001",
    customer_index=customer_index,
    device_index=device_index,
    timestamp=datetime.now(),
    is_fraud=False              # Ou None para decidir via fraud_rate
)
# Retorna: {
#   'transaction_id': 'TX_00001',
#   'customer_id': 'CUST_001',
#   'device_id': 'DEV_001',
#   'timestamp': '2023-01-15T14:30:00Z',
#   'transaction_type': 'PIX',
#   'amount': 250.50,
#   'mcc_code': '5411',
#   'mcc_name': 'Supermercado',
#   'merchant_name': 'Walmart Carrefour',
#   'channel': 'MOBILE_APP',
#   'status': 'APPROVED',
#   'is_fraud': False,
#   'fraud_type': None,
#   # Risk Indicators (Phase 2.2):
#   'velocity_24h': 5,                    # Transações nas últimas 24h
#   'accumulated_amount_24h': 1250.50,    # Total gasto 24h
#   'new_merchant': True,                 # First time with this merchant?
#   'distance_from_last_txn_km': 12.5,    # Haversine
#   'time_since_last_txn_min': 23,
#   # Geolocation
#   'geolocation_lat': -23.5505,
#   'geolocation_lon': -46.6333,
#   'geolocation_city': 'São Paulo',
#   'geolocation_state': 'SP'
# }

# Gerar batch
transactions = gen.generate_batch(
    count=1000,
    customer_index=customer_index,
    device_index=device_index,
    num_customers=100,
    num_devices=250
)
```

#### DriverGenerator
```python
from fraud_generator.generators import DriverGenerator

gen = DriverGenerator(seed=42)

# Gerar um motorista
driver = gen.generate(driver_id="DRIV_001", state="SP")
# Retorna: {
#   'driver_id': 'DRIV_001',
#   'name': 'Carlos Oliveira',
#   'cpf': '98765432100',  # CPF válido
#   'cnh_number': '12345678901',  # 11 dígitos
#   'cnh_category': 'B',           # B, AB, C, D, E
#   'cnh_validity': '2028-01-15',
#   'phone': '11987654321',
#   'email': 'carlos@example.com',
#   'vehicle_plate': 'ABC1D23',     # Mercosul (70%)
#   'vehicle_brand': 'Honda',
#   'vehicle_model': 'Civic',
#   'vehicle_year': 2023,
#   'vehicle_color': 'Branco',
#   'rating': 4.8,
#   'trips_completed': 2350,
#   'active_apps': ['UBER', '99'],  # Apps ativas
#   'operating_city': 'São Paulo',
#   'operating_state': 'SP',
#   'categories_enabled': ['UberX', '99Pop'],
#   'is_active': True,
#   'registration_date': '2019-03-20'
# }
```

#### RideGenerator
```python
from fraud_generator.generators import RideGenerator
from fraud_generator.utils import DriverIndex

# Preparar índice
driver_index = DriverIndex(drivers_list)

gen = RideGenerator(seed=42)

# Gerar uma corrida
ride = gen.generate(
    ride_id="RIDE_001",
    driver_index=driver_index,
    passenger_id="CUST_001",
    timestamp=datetime.now()
)
# Retorna: {
#   'ride_id': 'RIDE_001',
#   'timestamp': '2023-01-15T14:30:00Z',
#   'app': 'UBER',
#   'category': 'UberX',
#   'driver_id': 'DRIV_001',
#   'passenger_id': 'CUST_001',
#   # Locations
#   'pickup_location': {
#       'lat': -23.5505,
#       'lon': -46.6333,
#       'name': 'Centro',
#       'poi_type': 'BUSINESS',
#       'city': 'São Paulo',
#       'state': 'SP'
#   },
#   'dropoff_location': {
#       'lat': -23.6500,
#       'lon': -46.6000,
#       'name': 'Parque Ibirapuera',
#       'poi_type': 'PARK',
#       'city': 'São Paulo',
#       'state': 'SP'
#   },
#   # Times
#   'request_datetime': '2023-01-15T14:30:00Z',
#   'accept_datetime': '2023-01-15T14:32:15Z',
#   'pickup_datetime': '2023-01-15T14:35:45Z',
#   'dropoff_datetime': '2023-01-15T14:52:30Z',
#   # Ride details
#   'distance_km': 8.5,              # Haversine calculation
#   'duration_minutes': 22,
#   'wait_time_minutes': 5,
#   'base_fare': 5.00,
#   'surge_multiplier': 1.3,         # Horário de pico
#   'final_fare': 32.50,
#   'driver_pay': 28.75,
#   'platform_fee': 3.75,
#   'tip': 2.00,
#   'payment_method': 'CREDIT_CARD',
#   'status': 'COMPLETED',
#   'driver_rating': 4.9,
#   'passenger_rating': 5.0,
#   'cancellation_reason': None,
#   'weather_condition': 'CLEAR',
#   'temperature': 28,
#   'is_fraud': False,
#   'fraud_type': None
# }
```

---

### 2️⃣ EXPORTERS - Salvando Dados

#### JSONExporter (Streaming)
```python
from fraud_generator.exporters import JSONExporter

# Criar exporter
exporter = JSONExporter(
    skip_none=True,    # Remove valores None (menores arquivos)
    compress=None      # ou 'gzip', 'zstd', 'snappy'
)

# Exportar um batch (streaming, não acumula)
transactions = [tx1, tx2, tx3, ...]  # ~1000 registros
exporter.export_batch(transactions, '/output/transactions.jsonl')

# Resultado: 1000 linhas JSON, 1 por linha
# {"transaction_id": "TX_00001", "amount": 250.50, ...}
# {"transaction_id": "TX_00002", "amount": 150.25, ...}
# ...

# Com compressão
exporter_gz = JSONExporter(compress='gzip')
exporter_gz.export_batch(transactions, '/output/transactions.jsonl.gz')
# Resultado: 30-40% do tamanho original (mais lento)

# Com zstd (recomendado)
exporter_zst = JSONExporter(compress='zstd')
exporter_zst.export_batch(transactions, '/output/transactions.jsonl.zst')
# Resultado: 25-35% do tamanho, 3-4x mais rápido
```

#### CSVExporter (Colunas)
```python
from fraud_generator.exporters import CSVExporter

# Criar exporter
exporter = CSVExporter()

# Exportar batch
transactions = [tx1, tx2, tx3, ...]
exporter.export_batch(transactions, '/output/transactions.csv')

# Resultado: Headers + dados em colunas
# transaction_id,customer_id,amount,mcc_code,...
# TX_00001,CUST_001,250.50,5411,...
# TX_00002,CUST_002,150.25,7011,...
# ...

# Para TSV (Tab-Separated Values)
exporter_tsv = TSVExporter()
exporter_tsv.export_batch(transactions, '/output/transactions.tsv')
```

#### ParquetExporter (Columnar)
```python
from fraud_generator.exporters import ParquetExporter

# Criar exporter
exporter = ParquetExporter(
    compression='snappy'  # Padrão: bom balanço speed/ratio
)

# Exportar batch
transactions = [tx1, tx2, tx3, ...]
exporter.export_batch(transactions, '/output/transactions.parquet')

# Resultado: Arquivo binário otimizado para leitura columnar
# Excelente para data science / analytics

# Com particionamento por estado
exporter_partitioned = ParquetPartitionedExporter(
    compression='snappy',
    partition_column='geolocation_state'
)
exporter_partitioned.export_batch(transactions, '/output/partitioned/')
# Resultado:
# /output/partitioned/geolocation_state=SP/data_00000.parquet
# /output/partitioned/geolocation_state=RJ/data_00001.parquet
# /output/partitioned/geolocation_state=MG/data_00002.parquet
# (excelente para queries Hadoop/Spark)
```

#### ArrowIPCExporter (Ultra-Rápido)
```python
from fraud_generator.exporters import ArrowIPCExporter

# Criar exporter
exporter = ArrowIPCExporter(
    compression='none'  # ou 'lz4', 'zstd'
)

# Exportar batch
transactions = [tx1, tx2, tx3, ...]
exporter.export_batch(transactions, '/output/transactions.arrow')

# Resultado: Arrow IPC format (10x mais rápido que Parquet)
# Ideal para streaming entre processos
# Memória compartilhada, zero-copy reads

# Ler volta
import pyarrow as pa
reader = pa.ipc.open_file('/output/transactions.arrow')
table = reader.read_all()
```

#### DatabaseExporter (PostgreSQL/DuckDB/SQLite)
```python
from fraud_generator.exporters import DatabaseExporter

# PostgreSQL
exporter = DatabaseExporter(
    url='postgresql://user:pass@localhost/fraud_db',
    table_name='transactions',
    if_exists='append'  # ou 'replace', 'fail'
)
exporter.export_batch(transactions, None)  # path é ignored
# Resultado: INSERT INTO transactions VALUES (...)

# DuckDB (mais rápido, local)
exporter = DatabaseExporter(
    url='duckdb:///./fraud.duckdb',
    table_name='transactions'
)
exporter.export_batch(transactions, None)

# SQLite
exporter = DatabaseExporter(
    url='sqlite:///./fraud.db',
    table_name='transactions'
)
exporter.export_batch(transactions, None)
```

#### MinIOExporter (S3 Upload)
```python
from fraud_generator.exporters import MinIOExporter

# Criar exporter
exporter = MinIOExporter(
    bucket='fraud-data',
    host='minio.example.com',
    port=9000,
    access_key='minioadmin',
    secret_key='minioadmin',
    use_ssl=True,
    jsonl_compress='gzip'  # Compressão do JSON
)

# Exportar batch (faz upload para S3)
transactions = [tx1, tx2, tx3, ...]
exporter.export_batch(transactions, 's3://fraud-data/2026-03-03/transactions')

# Resultado:
# s3://fraud-data/2026-03-03/transactions.jsonl.gz (uploaded)
# Com retry automático (5 tentativas com backoff exponencial)
```

#### Factory Pattern (Uso Genérico)
```python
from fraud_generator.exporters import get_exporter

# Usar factory para escolher no runtime
format_choice = 'json'  # 'json', 'csv', 'parquet', 'arrow', 'database'

exporter = get_exporter(format_choice, **kwargs)
if exporter:
    exporter.export_batch(transactions, '/path/to/output')
else:
    print(f"Format {format_choice} not available")

# Listar formatos disponíveis
from fraud_generator.exporters import list_formats
print(list_formats())  # ['json', 'csv', 'parquet', 'arrow', 'database', ...]

# Validar formato
from fraud_generator.exporters import is_format_available
if is_format_available('zstd-json'):
    print("zstd-json is available")
```

---

### 3️⃣ CONNECTIONS - Streaming Real-Time

#### KafkaConnection
```python
from fraud_generator.connections import KafkaConnection
import json

# Criar conexão
conn = KafkaConnection(
    bootstrap_servers=['localhost:9092'],  # ou string 'host:port'
    topic='transactions',
    client_id='fraud-generator-001'
)

# Conectar
conn.connect()

# Enviar transações (streaming)
for tx in transactions:
    conn.send(json.dumps(tx))

# Fechar
conn.close()

# Uso em tempo real
from fraud_generator.generators import TransactionGenerator, CustomerGenerator

gen = TransactionGenerator(fraud_rate=0.02)
conn = KafkaConnection(bootstrap_servers='localhost:9092', topic='tx')
conn.connect()

try:
    while True:  # Continuous streaming
        tx = gen.generate(...)
        conn.send(json.dumps(tx))
        time.sleep(0.01)  # 100 tx/sec
except KeyboardInterrupt:
    conn.close()
```

#### WebhookConnection
```python
from fraud_generator.connections import WebhookConnection
import json

# Criar conexão
conn = WebhookConnection(
    url='http://api.example.com/ingest',
    method='POST',  # POST, PUT
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    timeout=30,
    retry=True,
    max_retries=3
)

# Conectar (validar URL está acessível)
conn.connect()

# Enviar transações
for tx in transactions:
    conn.send(json.dumps(tx))
    # Resultado: HTTP POST para seu webhook
    # HTTP 200 = sucesso
    # HTTP 5xx = retentará automaticamente

# Fechar
conn.close()

# Padrão para ingestão em tempo real
import requests
@app.post("/webhook/ingest")
def ingest_fraud_data(body: dict):
    # Seu endpoint recebe eventos assim
    tx = body  # {'transaction_id': ..., 'amount': ..., ...}
    db.transactions.insert(tx)
    return {"ok": True}
```

#### StdoutConnection (Debug)
```python
from fraud_generator.connections import StdoutConnection
import json

# Perfeito para testes
conn = StdoutConnection()
conn.connect()

for tx in transactions[:10]:  # Apenas 10 para debug
    conn.send(json.dumps(tx))

# Resultado: Imprime JSON bonito no console
# {"transaction_id": "TX_00001", "amount": 250.50, ...}
# {"transaction_id": "TX_00002", "amount": 150.25, ...}
# ...
```

#### Factory Pattern
```python
from fraud_generator.connections import get_connection

# Escolher no runtime
target = 'kafka'  # 'kafka', 'webhook', 'stdout'

conn = get_connection(target, bootstrap_servers='localhost:9092', ...)
conn.connect()
for tx in transactions:
    conn.send(json.dumps(tx))
conn.close()

# Validar disponibilidade
from fraud_generator.connections import is_target_available
if is_target_available('kafka'):
    print("Kafka está disponível")
```

---

### 4️⃣ UTILITIES - Ferramentas Auxiliares

#### WeightCache (O(log n) Sampling)
```python
from fraud_generator.utils.weight_cache import WeightCache

# Criar cache de pesos
items = ['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'BOLETO']
weights = [0.42, 0.22, 0.15, 0.21]

cache = WeightCache(items, weights)

# Amostrar
for _ in range(100):
    sampled_type = cache.sample()
    # Resultado: 'PIX' (42%), 'CREDIT_CARD' (22%), etc

# Bench:
# ✅ random.choices(): 3.2µs per sample
# ✅ WeightCache.sample(): 0.2µs per sample (16x mais rápido)
```

#### CustomerSessionState (Histórico 24h)
```python
from fraud_generator.utils.streaming import CustomerSessionState
from datetime import datetime

# Criar sessão para cliente
session = CustomerSessionState(customer_id='CUST_001')

# Adicionar transações (em ordem temporal)
tx1 = {
    'transaction_id': 'TX_001',
    'timestamp': datetime(2026, 3, 3, 10, 0),
    'amount': 100.0,
    'merchant_id': 'MERC_A',
    'geolocation_lat': -23.5505,
    'geolocation_lon': -46.6333,
    'device_id': 'DEV_001'
}
session.add_transaction(tx1, tx1['timestamp'])

tx2 = {
    'transaction_id': 'TX_002',
    'timestamp': datetime(2026, 3, 3, 10, 23),
    'amount': 150.0,
    'merchant_id': 'MERC_B',
    'geolocation_lat': -23.6500,
    'geolocation_lon': -46.6000,
    'device_id': 'DEV_001'
}
session.add_transaction(tx2, tx2['timestamp'])

# Obter métricas
now = datetime(2026, 3, 3, 10, 25)

velocity = session.get_velocity(now)
# Resultado: 2 (duas transações nas últimas 24h)

accumulated = session.get_accumulated_24h(now)
# Resultado: 250.0 (soma de valores)

is_new = session.is_new_merchant('MERC_C', now)
# Resultado: True (MERC_C never seen before)

minutes_ago = session.get_last_transaction_minutes_ago(now)
# Resultado: 2 (TX_002 foi há 2 minutos)

distance = session.get_distance_from_last_txn_km(-23.6600, -46.5900, now)
# Resultado: ~1.5 km (distância desde última transação)

# Resultado: Indicadores realistas para fraude
```

#### DriverIndex & RideIndex
```python
from fraud_generator.utils.streaming import DriverIndex, RideIndex, create_driver_index

# Criar índices para lookup rápido
drivers = [driver1, driver2, ...]
driver_index = DriverIndex(
    driver_id=driver1['driver_id'],
    operating_state='SP',
    operating_city='São Paulo',
    active_apps=('UBER', '99')
)

# Usar em gerador
gen = RideGenerator()
ride = gen.generate(
    ride_id='RIDE_001',
    driver_index=driver_index,  # Para lookup rápido
    passenger_id='CUST_001'
)
```

#### Compression Handler
```python
from fraud_generator.utils.compression import CompressionHandler

# Criar handler (auto-fallback se lib não instalada)
handler = CompressionHandler('zstd')  # Com fallback a gzip

# Comprimir
data = b'my binary data...'
compressed = handler.compress(data)
# Resultado: Dados comprimidos com zstd (3-4x mais rápido)

# Descomprimir (detecta automaticamente o tipo)
recovered = handler.decompress(compressed)
assert recovered == data
```

#### Parse & Format Size
```python
from fraud_generator.utils.helpers import parse_size, format_size

# Parser de tamanho (CLI)
size_bytes = parse_size('1GB')      # 1073741824
size_bytes = parse_size('100MB')    # 104857600
size_bytes = parse_size('512KB')    # 524288
size_bytes = parse_size('100000')   # 100000 (default bytes)

# Formatar para legível
formatted = format_size(1073741824)  # '1.0 GB'
formatted = format_size(104857600)   # '100.0 MB'
formatted = format_size(524288)      # '512.0 KB'
```

#### CPF Validation
```python
from fraud_generator.validators.cpf import validate_cpf, generate_valid_cpf

# Validar CPF
is_valid = validate_cpf('12345678900')  # False (check digits errados)
is_valid = validate_cpf('00000000000')  # False (todos zeros)

# Gerar CPF válido (com check digits corretos)
cpf = generate_valid_cpf()  # '12345678900' (garantidamente válido)

# Usar em geração
cpf_valido = generate_valid_cpf()
assert validate_cpf(cpf_valido)  # True
```

---

## 🧠 ADVANCED PATTERNS

### Pattern 1: Processamento em Lotes com Sessions
```python
from fraud_generator.generators import CustomerGenerator, TransactionGenerator
from fraud_generator.utils.streaming import CustomerSessionState
from datetime import datetime, timedelta
import random

# Setup
num_customers = 1000
days_to_generate = 30

gen_customer = CustomerGenerator(seed=42)
gen_transaction = TransactionGenerator(seed=42, fraud_rate=0.02)

# Gerar clientes
customers = [
    gen_customer.generate(f"CUST_{i:06d}")
    for i in range(num_customers)
]

# Preparar sessões (uma por cliente)
sessions = {
    customer['customer_id']: CustomerSessionState(customer['customer_id'])
    for customer in customers
}

# Gerar transações dia por dia
start_date = datetime(2026, 1, 1)
all_transactions = []

for day in range(days_to_generate):
    current_date = start_date + timedelta(days=day)
    daily_transactions = []
    
    # ~2-5 transações por cliente por dia
    for customer in customers:
        num_txs_today = random.randint(2, 5)
        
        for tx_idx in range(num_txs_today):
            # Tempo aleatório durante o dia
            hour = random.randint(6, 23)
            minute = random.randint(0, 59)
            tx_time = current_date.replace(hour=hour, minute=minute)
            
            # Gerar transação
            tx = gen_transaction.generate(
                tx_id=f"TX_{len(all_transactions):08d}",
                customer=customer,
                timestamp=tx_time,
                session=sessions[customer['customer_id']]
            )
            
            # Atualizar sessão
            sessions[customer['customer_id']].add_transaction(tx, tx_time)
            
            daily_transactions.append(tx)
    
    all_transactions.extend(daily_transactions)
    print(f"  Day {day+1}/{days_to_generate}: {len(daily_transactions)} txs")

# Resultado: Transações realistas com padrões correlacionados!
print(f"Total: {len(all_transactions)} transações")
```

### Pattern 2: Geração Paralela com ProcessPool
```python
from fraud_generator.generators import TransactionGenerator
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

def worker_generate_batch(worker_id, batch_size, customer_index):
    """Worker function que roda em processo separado."""
    gen = TransactionGenerator(
        use_profiles=True,
        fraud_rate=0.02,
        seed=42 + worker_id  # Seed diferente por worker
    )
    
    transactions = []
    for i in range(batch_size):
        tx = gen.generate(
            tx_id=f"TX_{worker_id:02d}_{i:06d}",
            customer_index=customer_index,
            # ...
        )
        transactions.append(tx)
    
    return transactions

# Setup
num_workers = mp.cpu_count()  # 8 (tipicamente)
batch_size = 10000
total_batches = 10

customer_index = building.index_from_customers(...)

# Executar em paralelo
all_transactions = []
with ProcessPoolExecutor(max_workers=num_workers) as executor:
    futures = []
    
    for batch_id in range(total_batches):
        future = executor.submit(
            worker_generate_batch,
            batch_id,
            batch_size,
            customer_index
        )
        futures.append(future)
    
    # Coletar resultados
    for future in futures:
        batch = future.result()
        all_transactions.extend(batch)

print(f"Total: {len(all_transactions)} transactions generated in parallel")
# Speedup: ~6-8x em octa-core CPU
```

### Pattern 3: Streaming com Taxa Configurável
```python
from fraud_generator.generators import TransactionGenerator, CustomerGenerator
from fraud_generator.connections import KafkaConnection
from datetime import datetime
import time

# Setup
gen_customer = CustomerGenerator(seed=42)
gen_transaction = TransactionGenerator(seed=42)

customers = [gen_customer.generate(f"CUST_{i:06d}") for i in range(100)]

conn = KafkaConnection(
    bootstrap_servers='localhost:9092',
    topic='fraud-transactions'
)
conn.connect()

# Stream at X transactions per second
target_rate = 10  # 10 tx/sec
interval = 1.0 / target_rate

try:
    tx_count = 0
    start_time = time.time()
    
    while True:
        # Gerar transação aleatória
        customer = random.choice(customers)
        tx = gen_transaction.generate(
            tx_id=f"TX_{tx_count:08d}",
            customer=customer,
            timestamp=datetime.now()
        )
        
        # Enviar
        conn.send(json.dumps(tx))
        tx_count += 1
        
        # Rate limiting
        elapsed = time.time() - start_time
        expected_elapsed = tx_count * interval
        if expected_elapsed > elapsed:
            time.sleep(expected_elapsed - elapsed)
        
        # Status a cada 100 txs
        if tx_count % 100 == 0:
            rate = tx_count / (time.time() - start_time)
            print(f"🔄 {tx_count} txs @ {rate:.1f} tx/sec")

except KeyboardInterrupt:
    elapsed = time.time() - start_time
    rate = tx_count / elapsed
    print(f"✅ Streamed {tx_count} txs in {elapsed:.1f}s ({rate:.1f} tx/sec)")
    conn.close()
```

---

## 📊 PERFORMANCE TUNING

### Para Máxima Velocidade
```bash
# 1. Usar Arrow IPC (2.5M tx/s)
python generate.py --size 10GB --format arrow --output /tmp/fast

# 2. Desabilitar compressão
python generate.py --size 10GB --format json --jsonl-compress none

# 3. Maximize workers
python generate.py --size 10GB --workers 16  # ou $(nproc)

# 4. Usar RAM disk para I/O
mkdir -p /tmp/ramdisk
mount -t tmpfs -o size=50G tmpfs /tmp/ramdisk
python generate.py --size 50GB --output /tmp/ramdisk/
```

### Para Máxima Compressão
```bash
# 1. Usar zstd (3-4x mais rápido, melhor ratio)
python generate.py --size 10GB --format json --jsonl-compress zstd

# 2. Usar Parquet (45MB/GB)
python generate.py --size 10GB --format parquet --output ./data

# 3. Remover campos None
# (já implementado com skip_none=True por padrão)
```

### Para Máxima Realismo
```bash
# 1. Ativar perfis comportamentais (padrão)
python generate.py --size 10GB --use-profiles  # ou omitir

# 2. Ajustar fraud rate para seu caso
python generate.py --size 10GB --fraud-rate 0.05  # 5% fraude

# 3. Usar histórico do cliente (Session State)
# (já integrado automaticamente em v4.0)
```

---

## 🔍 DEBUGGING & TROUBLESHOOTING

### Issue: OOM (Out of Memory)
```python
# ❌ Errado: Acumula tudo em memória
all_txs = []
for i in range(1000000):
    tx = gen.generate(...)
    all_txs.append(tx)
exporter.export_batch(all_txs, 'output.jsonl')  # CRASH em 10GB

# ✅ Correto: Processa em batches
batch_size = 10000
for batch_start in range(0, 1000000, batch_size):
    batch = []
    for i in range(batch_start, batch_start + batch_size):
        tx = gen.generate(...)
        batch.append(tx)
    exporter.export_batch(batch, f'output_{batch_start:08d}.jsonl')
    del batch  # Libera memória
```

### Issue: Lento na Exportação
```python
# ❌ Problema: Chamando json.dumps por item
for tx in transactions:
    json_str = json.dumps(tx)  # Lento!

# ✅ Solução: Deixar exporter fazer
exporter.export_batch(transactions, 'output.jsonl')  # Otimizado

# Ou usar Arrow IPC para streaming ultra-rápido
arrow_exporter = ArrowIPCExporter(compression='zstd')
arrow_exporter.export_batch(transactions, 'output.arrow')
```

### Issue: CPF Inválido
```python
# ❌ Gerar aleatório
cpf = str(random.randint(10000000000, 99999999999))  # INVÁLIDO!

# ✅ Usar gerador
from fraud_generator.validators.cpf import generate_valid_cpf
cpf = generate_valid_cpf()  # Garantido válido
```

---

## 🚀 PRÓXIMOS PASSOS

1. **Ler:** [ANALISE_COMPLETA_PROJETO.md](ANALISE_COMPLETA_PROJETO.md)
2. **Praticar:** Rodar `generate.py` e `stream.py` localmente
3. **Estender:** Criar seu próprio exporter/connection
4. **Contribuir:** Submeter PR contra v4-beta
5. **Deploy:** Usar Docker para produção

---

**Guia Compilado em:** 3 de Março de 2026  
**Para Versão:** 4.0.0  
**Status:** Complete & Ready

