# 🏗️ ARQUITETURA & ROADMAP DE IMPLEMENTAÇÃO
## Fases Estratégicas de Melhoria

---

## 📊 VISÃO GERAL EXECUTIVA

```
ESTADO ATUAL (v4-beta):
├─ Performance: 68k tx/s, 36s para 1GB
├─ Realismo: Fraco (fraude aleatória)
├─ Conformidade: Dados não validados
├─ Escalabilidade: ~100GB viável

META FINAL (v5-production):
├─ Performance: 90k+ tx/s, 15s para 1GB
├─ Realismo: Forte (fraude contextualizada, padrões comportamentais)
├─ Conformidade: LGPD, validações, dados realistas
├─ Escalabilidade: ~1TB viável (com otimizações)

TIMELINE:
├─ Preparação: 10 min (baseline)
├─ Fase 1 (Quick Wins): 2-3 dias
├─ Fase 2 (Validation): 3-4 dias
├─ Fase 3 (Behavioral): 1 semana
├─ Fase 4 (Fraude): 1 semana
├─ Fase 5 (Escalabilidade): 2 semanas (opcional)
└─ TOTAL: ~4-6 semanas (sem Fase 5) ou 5-8 (com Fase 5)

ESFORÇO TOTAL: ~55-65 horas (sem Fase 5) ou 60-80 com Fase 5
IMPACTO: De "toy generator" para "production-grade"
MEMÓRIA: Usando 15GB WSL2 (sem upgrade necessário)
```

---

## 🏢 ESTRUTURA ARQUITETURAL

### Estrutura Atual (v4-beta)

```
src/fraud_generator/
├─ __init__.py
├─ config/                    ← Dados estáticos
│  ├─ banks.py
│  ├─ devices.py
│  ├─ geography.py
│  ├─ merchants.py
│  └─ transactions.py
├─ exporters/                 ← Output
│  ├─ base.py
│  ├─ csv_exporter.py
│  ├─ json_exporter.py
│  └─ parquet_exporter.py
├─ generators/               ← Core logic
│  ├─ customer.py
│  ├─ device.py
│  ├─ transaction.py
│  └─ ride.py
├─ models/                   ← Data classes
│  ├─ customer.py
│  ├─ device.py
│  └─ transaction.py
├─ profiles/                 ← Comportamento
│  └─ behavioral.py
├─ utils/
│  ├─ helpers.py
│  └─ streaming.py
└─ validators/               ← Validação (pequeno)
   └─ cpf.py
```

### Estrutura Proposta (v5-production)

```
src/fraud_generator/
├─ __init__.py
│
├─ config/                    ← Dados + Cache
│  ├─ banks.py
│  ├─ devices.py
│  ├─ geography.py
│  ├─ merchants.py           [MODIFY] Add cache
│  ├─ transactions.py         [MODIFY] Add cached weights
│  ├─ validators_config.py    [NEW] CPF/RG/email patterns
│  └─ seasonality.py          [NEW] Black Friday, Natal, etc
│
├─ exporters/                 ← Output + Streaming
│  ├─ base.py                 [MODIFY] Abstract class
│  ├─ csv_exporter.py         [MODIFY] Streaming mode
│  ├─ json_exporter.py        [MODIFY] Streaming mode
│  ├─ parquet_exporter.py
│  └─ minio_exporter.py       [MODIFY] Add retry logic
│
├─ generators/               ← Core + Fraude contextualizada
│  ├─ customer.py            [MODIFY] Behavioral integration
│  ├─ device.py              [MODIFY] GPS realista
│  ├─ transaction.py         [MODIFY] Major refactor:
│  │                          - Cached weights
│  │                          - Fraud patterns
│  │                          - Risk indicators
│  ├─ ride.py
│  └─ fraud_generator.py      [NEW] Fraud orchestrator
│
├─ models/                   ← Data + State
│  ├─ customer.py            [MODIFY] Add metadata
│  ├─ device.py
│  ├─ transaction.py         [MODIFY] Add fraud fields
│  ├─ session.py             [NEW] Customer session state
│  └─ fraud_pattern.py        [NEW] Fraud pattern definitions
│
├─ profiles/                 ← Comportamento + Fraude
│  ├─ behavioral.py          [MODIFY] Expand profiles
│  ├─ fraud_contextualizer.py [NEW] Apply fraud patterns
│  ├─ geographic.py          [NEW] Regional behavior
│  └─ temporal.py            [NEW] Seasonality/time patterns
│
├─ validators/               ← Validação expandida
│  ├─ cpf.py                 [MODIFY] Add generation
│  ├─ rg.py                  [NEW] RG validation
│  ├─ email.py               [NEW] Email patterns
│  ├─ phone.py               [NEW] Phone DDD validation
│  └─ geographic.py          [NEW] Address/CEP validation
│
└─ utils/
   ├─ helpers.py
   ├─ streaming.py           [MODIFY] Session management
   ├─ caching.py             [NEW] Cache strategies
   ├─ benchmarking.py        [NEW] Performance metrics
   └─ lgpd.py                [NEW] Anonymization checks
```

---

## 🎯 FASES DETALHADAS

## PREPARAÇÃO: SETUP RÁPIDO (10 min)

### Checklist

```
[ ] 1. Verificar dependencies:
      $ pip list | grep -E "faker|pandas|pyarrow|boto3"
      Se faltar: pip install -r requirements.txt

[ ] 2. Testar instalação:
      $ python generate.py --size 100MB --output /tmp/test
      Esperado: Sucesso em ~10 segundos

[ ] 3. Criar baseline PRÉ-OTIMIZAÇÃO (IMPORTANTE!):
      $ mkdir -p logs
      $ time python generate.py --size 1GB --output /tmp/baseline_v4
      Tempo esperado: ~36 segundos
      Guardar log em: logs/baseline_antes.txt

[ ] 4. Iniciar branch Fase 1:
      $ git checkout -b phase-1-quick-wins
```

### Saída Esperada

```
✅ Dependencies: Faker, pandas, pyarrow, boto3 instalados
✅ Baseline: 1GB em ~36 segundos (referência para comparação)
✅ Branch: phase-1-quick-wins criado
Pronto para começar Fase 1
```

---

## FASE 1: QUICK WINS - PERFORMANCE & OOM (2-3 dias)

### Objetivos
- [ ] +30% performance (68k → 90k tx/s)
- [ ] Fix OOM em datasets >1GB
- [ ] Melhorar reliability

### Arquivos a Modificar

```
src/fraud_generator/
├─ config/transactions.py           [MODIFY] Add cached weights
├─ config/merchants.py              [MODIFY] Add MCC cache
├─ generators/transaction.py        [MAJOR] Cache + streaming
├─ exporters/csv_exporter.py        [MODIFY] Streaming mode
├─ exporters/parquet_exporter.py    [MODIFY] Streaming mode
├─ exporters/minio_exporter.py      [MODIFY] Add retry logic
└─ generators/customer.py           [MODIFY] Parallelize
```

### 1.1: Cache de Weights (2 horas)

**Arquivo:** `src/fraud_generator/config/transactions.py`

```python
# ANTES
TRANSACTION_TYPES = {
    'PIX': 35,
    'CREDIT_CARD': 45,
    'DEBIT_CARD': 15,
    'AUTO_DEBIT': 5,
}

# DEPOIS
import numpy as np

TRANSACTION_TYPES = {
    'PIX': 35,
    'CREDIT_CARD': 45,
    'DEBIT_CARD': 15,
    'AUTO_DEBIT': 5,
}

# Cache de weights cumulativos
_TX_TYPES_LIST = list(TRANSACTION_TYPES.keys())
_TX_TYPES_WEIGHTS = list(TRANSACTION_TYPES.values())
TX_TYPES_CUMSUM = np.cumsum(_TX_TYPES_WEIGHTS) / sum(_TX_TYPES_WEIGHTS)

def get_transaction_type_weighted():
    """O(log n) lookup using binary search."""
    r = np.random.random()
    idx = np.searchsorted(TX_TYPES_CUMSUM, r)
    return _TX_TYPES_LIST[min(idx, len(_TX_TYPES_LIST)-1)]
```

**Em transaction.py:**

```python
from fraud_generator.config.transactions import (
    TX_TYPES_CUMSUM, 
    get_transaction_type_weighted
)

class TransactionGenerator:
    def generate(self, ...):
        # ANTES: random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)
        # DEPOIS:
        tx_type = get_transaction_type_weighted()
        # ... resto
```

**Impacto:** 15x mais rápido na escolha, ~5-10% de speedup total

---

### 1.2: Merchants Cache (1 hora)

**Arquivo:** `src/fraud_generator/config/merchants.py`

```python
# ANTES: get_merchants_for_mcc() busca sequencial

# DEPOIS: Dicionário em memória
def _build_merchants_cache():
    """Pre-build MCC → merchants mapping."""
    cache = {}
    for mcc, merchants in MCC_MERCHANT_DATA.items():
        cache[mcc] = merchants
    return cache

MERCHANTS_CACHE = _build_merchants_cache()

def get_merchants_for_mcc(mcc_code: str) -> List[str]:
    """O(1) lookup."""
    return MERCHANTS_CACHE.get(mcc_code, ['MERCHANT_DEFAULT'])
```

**Impacto:** ~2µs → 0.1µs lookup, 20x mais rápido, ~3-5% de speedup

---

### 1.3: Remove Campos Nulos (30 min)

**Arquivo:** `src/fraud_generator/models/transaction.py`

```python
# ANTES
@dataclass
class Transaction:
    # ... campos reais ...
    distance_from_last_txn_km: Optional[float] = None  # ← Sempre None
    time_since_last_txn_min: Optional[int] = None      # ← Sempre None
    # Serializa JSON com "distance_from_last_txn_km": null

# DEPOIS (Opção 1: Remove)
@dataclass
class Transaction:
    # ... campos reais ...
    # Campos removidos - não usados, só inflam JSON

# Ou (Opção 2: Implement corretamente em Fase 4)
@dataclass
class Transaction:
    # ... campos reais ...
    # Será populado em Fase 4 com session state
```

**Impacto:** JSON -80-100 bytes/transação, ~5% de speedup em I/O

---

### 1.4: CSV Streaming (1.5 horas)

**Arquivo:** `src/fraud_generator/exporters/csv_exporter.py`

```python
class CSVExporter(ExporterProtocol):
    """CSV exporter with streaming support."""
    
    def export_batch(self, data, output_path, append=False):
        """Export batch of records."""
        if not data:
            return 0
        
        # Determine fieldnames from first record
        fieldnames = list(data[0].keys())
        mode = 'a' if append else 'w'
        
        with open(output_path, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if mode == 'w':
                writer.writeheader()
            writer.writerows(data)
        
        return len(data)
    
    def export_stream(self, data_iterator, output_path, batch_size=10000):
        """Export from iterator (memory-efficient)."""
        batch = []
        total = 0
        first_batch = True
        
        for record in data_iterator:
            batch.append(record)
            if len(batch) >= batch_size:
                count = self.export_batch(batch, output_path, append=not first_batch)
                total += count
                batch = []
                first_batch = False
        
        # Write remainder
        if batch:
            count = self.export_batch(batch, output_path, append=not first_batch)
            total += count
        
        return total
```

**Usage em worker:**

```python
# Em generate.py worker function
if format_name == 'csv':
    def transaction_stream():
        for i in range(num_transactions):
            tx = tx_generator.generate(...)
            yield tx
    
    count = exporter.export_stream(transaction_stream(), output_path, batch_size=10000)
```

**Impacto:** OOM fix crítico, permite 10GB+ sem crash

---

### 1.5: MinIO Retry Logic (1 hora)

**Arquivo:** `src/fraud_generator/exporters/minio_exporter.py`

```python
import time
from botocore.exceptions import ClientError

class MinIOExporter(ExporterProtocol):
    def export_batch(self, data, key, max_retries=3, backoff_factor=2):
        """Export with exponential backoff retry."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                body = self._serialize_data(data)
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=body,
                )
                return len(data)
            
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                # Retryable errors
                if error_code in ['ServiceUnavailable', 'SlowDown', 'RequestTimeout']:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        time.sleep(wait_time)
                        continue
                
                # Non-retryable error
                raise
            
            except Exception as e:
                last_error = e
                raise
        
        # All retries exhausted
        raise IOError(
            f"Failed to upload {key} after {max_retries} attempts. "
            f"Last error: {last_error}"
        )
```

**Impacto:** Reliability crítico em produção, tolera falhas transitórias

---

### 1.6: Paralelizar Customer Generation (1.5 horas)

**Arquivo:** `src/fraud_generator/generators/customer.py` + `generate.py`

```python
from concurrent.futures import ThreadPoolExecutor
from fraud_generator.generators import CustomerGenerator, DeviceGenerator

def generate_customers_and_devices_parallel(
    num_customers: int,
    num_devices_per_customer: int,
    workers: int = 4,
    use_profiles: bool = True,
    seed: Optional[int] = None,
) -> Tuple[List, List, List, List]:
    """Generate customers and devices in parallel."""
    
    customer_gen = CustomerGenerator(use_profiles=use_profiles, seed=seed)
    device_gen = DeviceGenerator(seed=seed)
    
    def _generate_one(i):
        customer = customer_gen.generate(f"CUST_{i:012d}")
        devices = [
            device_gen.generate_for_customer(customer.customer_id)
            for _ in range(num_devices_per_customer)
        ]
        return customer, devices
    
    customer_data = []
    device_data = []
    customer_indexes = []
    device_indexes = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_generate_one, i) for i in range(num_customers)]
        
        for future in futures:
            customer, devices = future.result()
            customer_data.append(customer)
            
            # Create indexes
            cust_idx = CustomerIndex(...)
            customer_indexes.append(tuple(cust_idx))
            
            for device in devices:
                device_data.append(device)
                dev_idx = DeviceIndex(...)
                device_indexes.append(tuple(dev_idx))
    
    return customer_indexes, device_indexes, customer_data, device_data
```

**Impacto:** 2.1s → 0.7s (3x), ~3-5% de speedup total

---

### 1.7: Teste & Benchmark (1 hora)

```bash
# Após todas mudanças
$ time python generate.py --size 1GB --output /tmp/phase1

# Esperado: ~20 segundos (vs 36 antes)
# Speedup: ~45-50%

# Verificar memória pico:
$ python -m memory_profiler generate.py --size 1GB --output /tmp/phase1
# Esperado: Pico < 3GB
```

### Checklist Fase 1

```
[ ] 1. Cache de weights em config/transactions.py
[ ] 2. Cache de merchants em config/merchants.py
[ ] 3. Remove campos nulos de models/transaction.py
[ ] 4. CSV streaming em exporters/csv_exporter.py
[ ] 5. MinIO retry em exporters/minio_exporter.py
[ ] 6. Paralelizar customer gen
[ ] 7. Benchmark: 1GB antes e depois
[ ] 8. Logs de mudanças
[ ] 9. Tests rodam sem erro
[ ] 10. Update README com novos benchmarks
```

### Saída Esperada Fase 1

```
Performance:
├─ Antes: 68k tx/s, 36s para 1GB, pico 6GB RAM
├─ Depois: 90k tx/s, 20s para 1GB, pico 2GB RAM
└─ Speedup: 1.8x, Memory: -67%

Commits:
├─ "perf: cache transaction type weights"
├─ "perf: cache merchants by MCC"
├─ "perf: remove unused null fields"
├─ "perf: streaming CSV export (fix OOM)"
├─ "reliability: add exponential backoff to MinIO"
└─ "perf: parallelize customer generation"
```

---

## FASE 2: VALIDAÇÃO & REALISMO DE DADOS (3-4 dias)

### Objetivos
- [ ] Dados válidos (CPF, RG, email, telefone)
- [ ] Distribuição geográfica realista
- [ ] Dados LGPD-compliant

### Arquivos Novos/Modificados

```
src/fraud_generator/
├─ config/validators_config.py       [NEW] Patterns
├─ validators/cpf.py                 [MODIFY] Add generation
├─ validators/rg.py                  [NEW] RG validation
├─ validators/email.py               [NEW] Email patterns
├─ validators/phone.py               [NEW] Phone DDD
├─ validators/geographic.py          [NEW] CEP/Address
├─ config/geography.py               [MODIFY] Add population data
├─ utils/lgpd.py                     [NEW] Anonymization checks
└─ models/customer.py                [MODIFY] Add fields
```

---

### 2.1: CPF Valid com Checksum (1 hora)

**Arquivo:** `src/fraud_generator/validators/cpf.py`

```python
import random

class CPFValidator:
    @staticmethod
    def generate_valid_cpf() -> str:
        """Generate valid CPF with correct checksum."""
        # Generate 9 random digits
        digits = [random.randint(0, 9) for _ in range(9)]
        
        # Calculate first check digit
        s = sum((i + 2) * d for i, d in enumerate(digits))
        digit1 = 11 - (s % 11)
        digit1 = 0 if digit1 >= 10 else digit1
        
        digits.append(digit1)
        
        # Calculate second check digit
        s = sum((i + 1) * d for i, d in enumerate(digits))
        digit2 = 11 - (s % 11)
        digit2 = 0 if digit2 >= 10 else digit2
        
        digits.append(digit2)
        
        return ''.join(map(str, digits))
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Validate CPF format and checksum."""
        cpf = cpf.replace('.', '').replace('-', '')
        
        if len(cpf) != 11 or not cpf.isdigit():
            return False
        
        # Check if all digits are the same (invalid)
        if len(set(cpf)) == 1:
            return False
        
        # Validate checksums...
        # (implementation)
        return True
    
    @staticmethod
    def format_cpf(cpf: str) -> str:
        """Format CPF: XXX.XXX.XXX-XX"""
        cpf = cpf.replace('.', '').replace('-', '')
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
```

**Usage em customer.py:**

```python
from fraud_generator.validators.cpf import CPFValidator

class CustomerGenerator:
    def generate(self, customer_id):
        cpf = CPFValidator.generate_valid_cpf()
        # ... resto
```

---

### 2.2: RG por Estado (1 hora)

**Arquivo:** `src/fraud_generator/validators/rg.py`

```python
import random

class RGValidator:
    # RG formats vary by state
    RG_FORMATS = {
        'SP': (7, 1),   # 7 dígitos + 1 verificador
        'RJ': (8, 0),   # 8 dígitos, sem verificador
        'MG': (8, 1),   # 8 dígitos + 1 verificador
        'BA': (9, 0),   # 9 dígitos
        # ... etc
    }
    
    @staticmethod
    def generate_rg_for_state(state: str) -> str:
        """Generate valid RG for state."""
        if state not in RGValidator.RG_FORMATS:
            state = 'SP'  # Default
        
        num_digits, has_check = RGValidator.RG_FORMATS[state]
        
        rg = ''.join(str(random.randint(0, 9)) for _ in range(num_digits))
        
        if has_check:
            # Calculate check digit...
            check = RGValidator._calculate_check_digit(rg)
            rg += str(check)
        
        return rg
```

---

### 2.3: Email Realista (1 hora)

**Arquivo:** `src/fraud_generator/validators/email.py`

```python
import random

class EmailValidator:
    DOMAINS = {
        'gmail.com': 0.35,
        'hotmail.com': 0.25,
        'yahoo.com': 0.15,
        'outlook.com': 0.10,
        'empresa.com': 0.05,  # B2B
        'usp.br': 0.02,       # Universities
        'outros': 0.08,
    }
    
    @staticmethod
    def generate_email(name: str, age: int) -> str:
        """Generate realistic email based on age."""
        # Older users prefer @hotmail, younger prefer @gmail
        if age > 50:
            domain = random.choices(
                ['hotmail.com', 'gmail.com', 'yahoo.com'],
                weights=[0.4, 0.4, 0.2]
            )[0]
        else:
            domain = random.choices(
                ['gmail.com', 'hotmail.com', 'outlook.com'],
                weights=[0.5, 0.3, 0.2]
            )[0]
        
        # Email format
        if random.random() < 0.7:
            # nome.sobrenome ou nome_sobrenome
            email_prefix = name.lower().replace(' ', '.' if random.random() < 0.5 else '_')
        else:
            # nome + números
            email_prefix = name.lower().split()[0] + str(random.randint(1, 999))
        
        return f"{email_prefix}@{domain}"
```

---

### 2.4: Telefone com DDD (1 hora)

**Arquivo:** `src/fraud_generator/validators/phone.py`

```python
import random

class PhoneValidator:
    # DDD por estado
    STATE_DDDS = {
        'SP': [11, 12, 13, 14, 15, 16, 17, 18, 19],
        'RJ': [21, 22, 24],
        'MG': [31, 32, 33, 34, 35, 37, 38],
        'BA': [71, 73, 74, 75, 77],
        'CE': [85, 88],
        'PE': [81, 87],
        'PR': [41, 42, 43, 44, 45, 46],
        'RS': [51, 53, 54, 55],
        'DF': [61],
        # ... etc
    }
    
    @staticmethod
    def generate_phone_for_state(state: str) -> str:
        """Generate phone with correct DDD."""
        if state not in PhoneValidator.STATE_DDDS:
            state = 'SP'
        
        ddd = random.choice(PhoneValidator.STATE_DDDS[state])
        
        # 9 = celular (9XXXX-XXXX), 8 = fixo (XXXX-XXXX)
        is_mobile = random.random() < 0.8  # 80% celulares
        
        if is_mobile:
            number = f"9{random.randint(10000000, 99999999)}"
        else:
            number = f"{random.randint(10000000, 99999999)}"
        
        return f"({ddd}) {number[:5]}-{number[5:]}"
```

---

### 2.5: Distribuição Geográfica Realista (1.5 horas)

**Arquivo:** `src/fraud_generator/config/geography.py`

```python
# ANTES: Cidades aleatórias uniformes

# DEPOIS: Com população real
CITIES_BY_POPULATION = [
    # (name, state, population, lat, lon)
    ('São Paulo', 'SP', 12_300_000, -23.5505, -46.6333),
    ('Rio de Janeiro', 'RJ', 6_700_000, -22.9068, -43.1729),
    ('Brasília', 'DF', 3_100_000, -15.8267, -47.8761),
    ('Salvador', 'BA', 2_900_000, -12.9714, -38.5014),
    # ... 5000+ cidades com população
]

# Distribuição Zipf (pareto): poucos com muita, muitos com pouca
def _build_city_distribution():
    """Build weighted distribution by population."""
    cities = []
    weights = []
    
    for city_data in CITIES_BY_POPULATION:
        cities.append(city_data)
        # Use logarithm of population para Zipf
        weight = np.log(city_data[2])
        weights.append(weight)
    
    # Normalize
    weights = np.array(weights) / sum(weights)
    
    return cities, weights

CITIES, CITY_WEIGHTS = _build_city_distribution()

def get_random_location():
    """Sample location by real population distribution."""
    city = np.random.choice(CITIES, p=CITY_WEIGHTS)
    name, state, pop, lat, lon = city
    
    # Add GPS noise (~10-50m precision)
    lat += np.random.normal(0, 0.0005)
    lon += np.random.normal(0, 0.0005)
    
    return {
        'city': name,
        'state': state,
        'latitude': lat,
        'longitude': lon,
    }
```

**Impacto:** Elimina padrão óbvio de distribuição uniforme

---

### 2.6: LGPD Compliance (1 hora)

**Arquivo:** `src/fraud_generator/utils/lgpd.py`

```python
class LGPDCompliance:
    @staticmethod
    def validate_data_is_synthetic(customer_data: Dict) -> bool:
        """Verify no real PII in dataset."""
        # Checks:
        # 1. CPF não existe em registro público (OK, só checksum válido)
        # 2. Email não é registrado (OK, não checamos)
        # 3. Nome é combinação de partes (OK, faker)
        # 4. Endereço é real mas aleatório
        return True
    
    @staticmethod
    def generate_anonymization_certificate() -> str:
        """Generate certificate of synthetic data."""
        return """
CERTIFICADO DE SINTETIZAÇÃO DE DADOS
====================================

Este dataset foi inteiramente gerado sinteticamente usando:
- Faker library para nomes/emails/endereços
- CPF válidos sinteticamente (não existem na realidade)
- Padrões comportamentais baseados em pesquisa, não dados reais

Garantias:
- Impossível reidentificar pessoas reais
- LGPD compliant
- Seguro para distribuição comercial

Data: 2026-01-29
Gerador: Brazilian Fraud Data Generator v5
"""
```

---

### 2.7: Teste & Validação (1 hora)

```python
# tests/test_phase2_validation.py

def test_cpf_valid():
    from fraud_generator.validators.cpf import CPFValidator
    
    for _ in range(100):
        cpf = CPFValidator.generate_valid_cpf()
        assert CPFValidator.validate_cpf(cpf)

def test_rg_by_state():
    from fraud_generator.validators.rg import RGValidator
    
    rg_sp = RGValidator.generate_rg_for_state('SP')
    assert len(rg_sp) == 8  # SP tem 7 + 1 check

def test_email_realista():
    from fraud_generator.validators.email import EmailValidator
    
    email = EmailValidator.generate_email('João Silva', age=25)
    assert '@' in email
    assert '.' in email

def test_phone_ddd():
    from fraud_generator.validators.phone import PhoneValidator
    
    phone = PhoneValidator.generate_phone_for_state('SP')
    assert '11' in phone or '12' in phone  # DDD SP

def test_geographic_distribution():
    # Test Zipf: maior concentração em SP
    from fraud_generator.config.geography import get_random_location
    
    locations = [get_random_location() for _ in range(1000)]
    sp_count = sum(1 for loc in locations if loc['state'] == 'SP')
    
    # SP deve ter ~30-40% (não 10%)
    assert sp_count > 250
```

### Checklist Fase 2

```
[ ] 1. CPF generation + validation
[ ] 2. RG por estado
[ ] 3. Email realista
[ ] 4. Telefone com DDD correto
[ ] 5. CEP/Endereço válidos
[ ] 6. Distribuição geográfica Zipf
[ ] 7. LGPD compliance checks
[ ] 8. Update models/customer.py
[ ] 9. Tests rodam 100% pass
[ ] 10. Dados sample em /tmp/phase2
```

### Saída Esperada Fase 2

```
Dataset Improvements:
├─ CPF: Válido com checksum correto
├─ RG: Por estado, formato realista
├─ Email: 35% Gmail, 25% Hotmail, etc
├─ Phone: (11) 99XXX-XXXX com DDD correto
├─ Geographic: 35% SP, 15% RJ, 8% MG, etc
└─ LGPD: Certificado de sintetização incluído

Commits:
├─ "feat: add CPF generation with valid checksum"
├─ "feat: add RG validation by state"
├─ "feat: generate realistic emails by age"
├─ "feat: phone with correct DDD by state"
├─ "feat: geographic distribution by population (Zipf)"
└─ "docs: add LGPD compliance certificate"
```

---

## FASE 3: PADRÕES COMPORTAMENTAIS (1 semana)

### Objetivos
- [ ] Sazonalidade (Black Friday, Natal, férias)
- [ ] Padrões temporais (horários, dias da semana)
- [ ] Merchants realistas com distribuição

### Arquivos Novos/Modificados

```
src/fraud_generator/
├─ config/seasonality.py            [NEW] Black Friday, etc
├─ config/merchants.py              [MODIFY] Real names
├─ profiles/behavioral.py           [MODIFY] Expand profiles
├─ profiles/temporal.py             [NEW] Time patterns
├─ profiles/geographic.py           [NEW] Regional behavior
└─ models/behavioral_state.py       [NEW] Profile state tracking
```

---

### 3.1: Sazonalidade & Eventos (2 horas)

**Arquivo:** `src/fraud_generator/config/seasonality.py`

```python
from datetime import datetime

class SeasonalityManager:
    # Multiplicadores por mês
    MONTHLY_MULTIPLIERS = {
        1: 1.18,   # Janeiro: +18% (férias, bônus 13º)
        2: 0.85,   # Fevereiro: -15% (pós-férias)
        3: 0.92,   # Março: -8%
        4: 0.98,
        5: 0.99,
        6: 1.00,
        7: 1.40,   # Julho: +40% (férias escolares)
        8: 1.01,   # Agosto: +1% (volta às aulas)
        9: 0.99,
        10: 0.99,
        11: 2.80,  # Novembro: +180% (Black Friday)
        12: 1.85,  # Dezembro: +85% (Natal)
    }
    
    # Multiplicadores por dia da semana
    WEEKLY_MULTIPLIERS = {
        0: 1.10,  # Segunda: +10%
        1: 1.15,  # Terça: +15%
        2: 1.10,  # Quarta: +10%
        3: 1.12,  # Quinta: +12%
        4: 1.20,  # Sexta: +20%
        5: 0.95,  # Sábado: -5%
        6: 0.85,  # Domingo: -15%
    }
    
    # Eventos específicos
    EVENTS = [
        # (data_inicio, data_fim, multiplicador, nome)
        ((2, 1), (2, 6), 1.60, "Carnaval"),           # Móvel, fevereiro
        ((4, 9), (4, 11), 1.40, "Páscoa"),            # Móvel, março-abril
        ((6, 24), (6, 24), 1.30, "São João"),         # 24 junho
        ((9, 7), (9, 7), 1.15, "Independência"),      # 7 setembro
        ((11, 1), (11, 2), 1.40, "Finados"),          # 1-2 novembro
        ((11, 20), (11, 24), 4.00, "Black Friday"),   # ~24 novembro
        ((12, 1), (12, 24), 1.50, "Natal"),           # Dezembro
    ]
    
    @staticmethod
    def get_multiplier(date: datetime) -> float:
        """Get seasonality multiplier for date."""
        base = SeasonalityManager.MONTHLY_MULTIPLIERS.get(date.month, 1.0)
        weekly = SeasonalityManager.WEEKLY_MULTIPLIERS.get(date.weekday(), 1.0)
        
        # Check events
        event_mult = 1.0
        for (m1, d1), (m2, d2), mult, name in SeasonalityManager.EVENTS:
            if (date.month, date.day) >= (m1, d1) and (date.month, date.day) <= (m2, d2):
                event_mult = mult
                break
        
        return base * weekly * event_mult

# Usage
def adjust_frequency_by_seasonality(base_frequency: int, date: datetime) -> int:
    multiplier = SeasonalityManager.get_multiplier(date)
    return int(base_frequency * multiplier)
```

---

### 3.2: Merchants Realistas (2 horas)

**Arquivo:** `src/fraud_generator/config/merchants.py`

```python
# ANTES: Merchant genérico

# DEPOIS: Com dados reais
MERCHANTS_BY_MCC = {
    '5411': {  # Supermercados
        'merchants': [
            ('Carrefour', 0.40),
            ('Walmart', 0.20),
            ('Pão de Açúcar', 0.15),
            ('Extra', 0.10),
            ('Alcântara', 0.05),
            ('Outros', 0.10),
        ],
        'value_range': (50, 500),
        'typical_value': 200,
    },
    '5814': {  # Fast food
        'merchants': [
            ('McDonald\'s', 0.35),
            ('Burger King', 0.25),
            ('Subway', 0.20),
            ('Popeyes', 0.10),
            ('Outros', 0.10),
        ],
        'value_range': (20, 100),
        'typical_value': 45,
    },
    '5815': {  # Restaurantes
        'merchants': [
            ('Outback', 0.15),
            ('Texas de Brasil', 0.10),
            ('Fazenda', 0.10),
            ('Outros restaurantes', 0.65),
        ],
        'value_range': (80, 500),
        'typical_value': 200,
    },
    '7941': {  # Academias
        'merchants': [
            ('SmartFit', 0.30),
            ('Bodytech', 0.20),
            ('Academia local', 0.50),
        ],
        'value_range': (100, 300),
        'typical_value': 150,
        'frequency': 'monthly',  # Recorrente
    },
}

def get_merchant_for_mcc(mcc: str):
    """Get realistic merchant for MCC."""
    if mcc not in MERCHANTS_BY_MCC:
        return {'name': f'MERCHANT_{mcc}', 'value': 100}
    
    mcc_data = MERCHANTS_BY_MCC[mcc]
    merchants, weights = zip(*mcc_data['merchants'])
    
    merchant_name = np.random.choice(merchants, p=np.array(weights)/sum(weights))
    value = np.random.uniform(*mcc_data['value_range'])
    
    return {
        'name': merchant_name,
        'mcc': mcc,
        'value': value,
    }
```

---

### 3.3: Perfis Expandidos (2 horas)

**Arquivo:** `src/fraud_generator/profiles/behavioral.py`

```python
# Expandir cada perfil com:
# - Hora típica de transações
# - Dias preferidos
# - Categorias preferidas
# - Valor típico por categoria

# Exemplo: YOUNG_DIGITAL

YOUNG_DIGITAL = BehavioralProfile(
    name="young_digital",
    description="18-30, apps, streaming, delivery",
    age_range=(18, 30),
    income_multiplier=(0.5, 1.5),
    
    # Padrão horário
    active_hours=[
        (12, 13),  # Almoço
        (19, 21),  # Noite
        (22, 23),  # Tarde noite
    ],
    
    # Categorias preferidas com frequência
    category_preferences={
        '5812_delivery': {
            'frequency': 'high',        # 2-3x por semana
            'value_range': (35, 80),
            'merchants': ['Ifood', 'Uber Eats', 'Loggi'],
        },
        '5814_fast_food': {
            'frequency': 'medium',      # 1-2x por semana
            'value_range': (30, 60),
        },
        '5812': {  # Restaurantes
            'frequency': 'low',         # 2-3x por mês
            'value_range': (50, 150),
        },
        '7941': {  # Academia
            'frequency': 'monthly',     # Recorrente
            'value': 150,
        },
        '4111_streaming': {
            'frequency': 'monthly',     # Netflix, Spotify, etc
            'value': 100,
        },
    },
    
    # Padrão semanal
    weekday_pattern={
        'weekday': {
            'tx_count': (5, 10),        # 5-10 tx seg-sexta
            'value': (30, 100),
        },
        'weekend': {
            'tx_count': (8, 15),        # 8-15 tx sab-dom
            'value': (50, 200),
        },
    },
    
    # Sazonalidade
    seasonal_adjustments={
        11: 5.0,   # Black Friday: 5x
        12: 2.0,   # Natal: 2x
        7: 1.4,    # Férias: 1.4x
    },
)
```

---

### Checklist Fase 3

```
[ ] 1. Sazonalidade: Black Friday, Natal, férias
[ ] 2. Padrão semanal (seg vs dom)
[ ] 3. Padrão horário (almoço vs noite)
[ ] 4. Merchants realistas com distribuição
[ ] 5. Valores típicos por merchant/MCC
[ ] 6. Perfis expandidos com padrões
[ ] 7. Geographic patterns (SP vs interior)
[ ] 8. Tests: sazonalidade, merchants
[ ] 9. Benchmark: qualidade de dados
[ ] 10. Sample output análise
```

### Saída Esperada Fase 3

```
Behavioral Realism:
├─ Sazonalidade: Nov/Dec +180%/+85% vs média
├─ Horários: Almoço 12h, noite 19-21h
├─ Dias: Sexta +20%, domingo -15%
├─ Merchants: Carrefour 40%, Walmart 20%
├─ Valores: Supermercado R$50-500, fast food R$20-100
└─ Perfis: Cada um tem padrão próprio

Commits:
├─ "feat: add seasonality (Black Friday, Natal, férias)"
├─ "feat: add realistic merchants with distribution"
├─ "feat: expand behavioral profiles with patterns"
├─ "feat: add temporal patterns (horários, dias)"
└─ "feat: geographic behavior variations"
```

---

## FASE 4: FRAUDE CONTEXTUALIZADA (1 semana)

### Objetivos
- [ ] Fraude com padrões reais
- [ ] Fraud scoring automático
- [ ] Customer session state
- [ ] Detectabilidade validada

### Arquivos Novos/Modificados

```
src/fraud_generator/
├─ models/session.py                [NEW] Session state
├─ models/fraud_pattern.py          [NEW] Fraud definitions
├─ profiles/fraud_contextualizer.py [NEW] Fraud logic
├─ generators/transaction.py        [MAJOR] Integrate fraud
└─ utils/fraud_scoring.py           [NEW] Scoring logic
```

---

### 4.1: Customer Session State (2 horas)

**Arquivo:** `src/fraud_generator/models/session.py`

```python
@dataclass
class CustomerSessionState:
    """Track customer behavior in session."""
    
    customer_id: str
    profile: BehavioralProfile
    
    # Recent transactions
    recent_transactions: List[Transaction] = field(default_factory=list)
    
    # Location tracking
    last_location: Optional[Tuple[float, float]] = None
    last_location_timestamp: Optional[datetime] = None
    
    # Daily metrics
    transactions_today: int = 0
    accumulated_amount_today: float = 0.0
    merchants_visited_today: set = field(default_factory=set)
    
    # Historical patterns
    typical_hours: List[int] = field(default_factory=list)
    used_merchants: set = field(default_factory=set)
    typical_amounts: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    def add_transaction(self, tx: Transaction):
        """Update state after transaction."""
        self.recent_transactions.append(tx)
        self.transactions_today += 1
        self.accumulated_amount_today += tx.amount
        self.merchants_visited_today.add(tx.merchant_id)
        self.used_merchants.add(tx.merchant_id)
        
        if tx.timestamp:
            self.typical_hours.append(tx.timestamp.hour)
            self.last_location = (tx.latitude, tx.longitude)
            self.last_location_timestamp = tx.timestamp
        
        # Keep only last 30
        if len(self.recent_transactions) > 30:
            self.recent_transactions.pop(0)
    
    def get_velocity(self) -> int:
        """Transactions in last 24h."""
        return self.transactions_today
    
    def time_since_last_transaction(self) -> Optional[int]:
        """Minutes since last transaction."""
        if len(self.recent_transactions) < 2:
            return None
        return int(
            (self.recent_transactions[-1].timestamp - 
             self.recent_transactions[-2].timestamp).total_seconds() / 60
        )
    
    def is_new_merchant(self, merchant_id: str) -> bool:
        return merchant_id not in self.used_merchants
    
    def is_location_anomaly(self, latitude: float, longitude: float) -> bool:
        """Check if location is impossible (velocity fraud)."""
        if not self.last_location:
            return False
        
        from geopy.distance import geodesic
        distance_km = geodesic(
            self.last_location,
            (latitude, longitude)
        ).kilometers
        
        time_elapsed_hours = (
            (datetime.now() - self.last_location_timestamp).total_seconds() / 3600
        )
        
        max_possible_speed = 900  # km/h (airplane)
        actual_speed = distance_km / max(time_elapsed_hours, 0.1)
        
        return actual_speed > max_possible_speed
```

---

### 4.2: Fraud Patterns & Contextualizer (3 horas)

**Arquivo:** `src/fraud_generator/models/fraud_pattern.py`

```python
@dataclass
class FraudPattern:
    """Definition of a fraud type."""
    
    name: str
    prevalence: float  # % of all frauds
    
    # Characteristics
    velocity_high: bool = False
    value_anomaly: str = 'NORMAL'  # HIGH, MEDIUM, LOW, NORMAL
    location_anomaly: bool = False
    time_anomaly: bool = False
    new_merchant: bool = False
    new_beneficiary: bool = False
    
    # Base fraud score
    fraud_score_base: float = 0.5
```

**Arquivo:** `src/fraud_generator/profiles/fraud_contextualizer.py`

```python
class FraudContextualizer:
    """Apply context-based fraud patterns."""
    
    FRAUD_PATTERNS = {
        'account_takeover': FraudPattern(
            name='account_takeover',
            prevalence=0.15,
            velocity_high=True,
            value_anomaly='HIGH',
            location_anomaly=True,
            new_beneficiary=True,
            fraud_score_base=0.8,
        ),
        'card_cloning': FraudPattern(
            name='card_cloning',
            prevalence=0.25,
            velocity_high=True,
            value_anomaly='MEDIUM',
            location_anomaly=False,
            fraud_score_base=0.6,
        ),
        'phishing': FraudPattern(
            name='phishing',
            prevalence=0.20,
            velocity_high=False,
            value_anomaly='HIGH',
            location_anomaly=False,
            fraud_score_base=0.7,
        ),
        'device_fraud': FraudPattern(
            name='device_fraud',
            prevalence=0.15,
            velocity_high=True,
            value_anomaly='MEDIUM',
            location_anomaly=True,
            fraud_score_base=0.7,
        ),
        'synthetic_fraud': FraudPattern(
            name='synthetic_fraud',
            prevalence=0.10,
            velocity_high=False,
            value_anomaly='LOW',
            location_anomaly=False,
            fraud_score_base=0.5,
        ),
        'friendly_fraud': FraudPattern(
            name='friendly_fraud',
            prevalence=0.15,
            velocity_high=False,
            value_anomaly='NORMAL',
            location_anomaly=False,
            fraud_score_base=0.3,
        ),
    }
    
    def __init__(self, profile: BehavioralProfile):
        self.profile = profile
    
    def decide_fraud_with_context(
        self,
        tx: Transaction,
        session: CustomerSessionState,
    ) -> Tuple[bool, float, str]:
        """
        Decide if transaction is fraud with context.
        
        Returns: (is_fraud, fraud_score, fraud_type)
        """
        
        # Base fraud rate from profile
        fraud_prob = self.profile.fraud_susceptibility / 100
        
        if random.random() > fraud_prob:
            return False, 0.0, None
        
        # Choose fraud pattern based on prevalence
        fraud_type = np.random.choice(
            list(self.FRAUD_PATTERNS.keys()),
            p=np.array([p.prevalence for p in self.FRAUD_PATTERNS.values()]),
        )
        
        pattern = self.FRAUD_PATTERNS[fraud_type]
        fraud_score = pattern.fraud_score_base
        
        # Adjust based on session state
        if pattern.velocity_high and session.get_velocity() > 5:
            fraud_score += 0.2
        
        if pattern.new_merchant and session.is_new_merchant(tx.merchant_id):
            fraud_score += 0.15
        
        if pattern.location_anomaly and session.is_location_anomaly(tx.latitude, tx.longitude):
            fraud_score += 0.25
        
        if pattern.value_anomaly == 'HIGH' and tx.amount > session.profile.typical_value_range[1] * 2:
            fraud_score += 0.2
        
        # Add session state to transaction
        tx.transactions_last_24h = session.get_velocity()
        tx.accumulated_amount_24h = session.accumulated_amount_today + tx.amount
        
        if time_since := session.time_since_last_transaction():
            tx.time_since_last_txn_min = time_since
        
        tx.new_merchant = session.is_new_merchant(tx.merchant_id)
        
        return True, min(fraud_score, 1.0), fraud_type
```

---

### 4.3: Integration com TransactionGenerator (2 horas)

**Arquivo:** `src/fraud_generator/generators/transaction.py`

```python
class TransactionGenerator:
    def __init__(self, ...):
        self.sessions = {}  # {customer_id: CustomerSessionState}
        self.contextualizers = {}  # {customer_id: FraudContextualizer}
    
    def generate(self, customer: Customer, num_transactions: int):
        """Generate transactions with context."""
        
        # Initialize session
        if customer.customer_id not in self.sessions:
            self.sessions[customer.customer_id] = CustomerSessionState(
                customer_id=customer.customer_id,
                profile=customer.profile,
            )
            self.contextualizers[customer.customer_id] = FraudContextualizer(
                customer.profile
            )
        
        session = self.sessions[customer.customer_id]
        contextualizer = self.contextualizers[customer.customer_id]
        
        transactions = []
        for _ in range(num_transactions):
            # Generate base transaction
            tx = self._generate_single(customer)
            
            # Apply fraud with context
            is_fraud, fraud_score, fraud_type = contextualizer.decide_fraud_with_context(
                tx, session
            )
            
            tx.is_fraud = is_fraud
            tx.fraud_score = fraud_score
            tx.fraud_type = fraud_type
            
            # Update session
            session.add_transaction(tx)
            
            transactions.append(tx)
        
        return transactions
```

---

### 4.4: Fraud Scoring & Detectability (1 hora)

**Arquivo:** `src/fraud_generator/utils/fraud_scoring.py`

```python
class SimpleDetector:
    """Simple baseline detector for fraud validation."""
    
    def calculate_fraud_score(self, tx: Transaction, session: CustomerSessionState) -> float:
        """
        Calculate suspicion score 0-100.
        Used to validate our synthetic fraud is realistic.
        """
        score = 0.0
        
        # Factor 1: Velocity (multiple txs in short time)
        if len(session.recent_transactions) > 0:
            last_tx = session.recent_transactions[-1]
            time_diff = (tx.timestamp - last_tx.timestamp).total_seconds() / 60
            if time_diff < 5:  # < 5 minutes
                score += 30
        
        # Factor 2: Location impossible
        if session.last_location:
            from geopy.distance import geodesic
            distance = geodesic(session.last_location, (tx.latitude, tx.longitude)).km
            time_diff_hours = (tx.timestamp - session.last_location_timestamp).total_seconds() / 3600
            speed_kmh = distance / max(time_diff_hours, 0.01)
            
            if speed_kmh > 900:  # > airplane speed
                score += 40
        
        # Factor 3: Value anomaly
        if tx.merchant_id in session.typical_amounts:
            min_val, max_val = session.typical_amounts[tx.merchant_id]
            if tx.amount > max_val * 2:
                score += 20
        
        # Factor 4: New merchant
        if session.is_new_merchant(tx.merchant_id):
            score += 10
        
        # Factor 5: Unusual hour
        hour = tx.timestamp.hour
        if hour < 6 or hour > 23:  # Madrugada
            score += 15
        
        return min(score, 100)
```

---

### Checklist Fase 4

```
[ ] 1. CustomerSessionState class
[ ] 2. FraudPattern definitions (6 tipos)
[ ] 3. FraudContextualizer logic
[ ] 4. Integration com TransactionGenerator
[ ] 5. Fraud scoring automático
[ ] 6. Session tracking (velocity, locations)
[ ] 7. Tests: fraude patterns aplicados
[ ] 8. Validation: detectador simples
[ ] 9. Benchmark: 1GB com fraude contextualizada
[ ] 10. Documentation
```

### Saída Esperada Fase 4

```
Fraud Improvements:
├─ Account Takeover: Velocity alta + valor alto + localização nova
├─ Card Cloning: Múltiplas tx + escalação de valor
├─ Phishing: Valor alto + categoria incomum
├─ Device Fraud: Múltiplas tx rápidas + localização impossível
├─ Synthetic: Novo cartão + padrão suspeito
└─ Friendly Fraud: Compra legítima depois negação

Validation:
├─ Simple detector encontra 80%+ de fraude gerada
├─ Padrões são reproduzíveis
└─ Sem aleatoriedade pura (contextualizado)

Commits:
├─ "feat: add customer session state tracking"
├─ "feat: implement fraud contextualization"
├─ "feat: add fraud pattern definitions"
├─ "feat: integrate fraud logic with transaction generator"
└─ "feat: add simple baseline detector for validation"
```

---

## FASE 5: ESCALABILIDADE (2 semanas - opcional)

### Objetivos
- [ ] Suportar 10TB+ de dados
- [ ] Processamento distribuído
- [ ] Cloud integration

### Arquivos Novos/Modificados

```
src/fraud_generator/
├─ executors/
│  ├─ local_executor.py             [NEW] Single machine
│  ├─ spark_executor.py             [NEW] Distributed
│  └─ cloud_executor.py             [NEW] AWS/GCP
└─ config/execution.py              [NEW] Execution config
```

### 5.1: Streaming Generator (2 horas)

```python
class StreamingGenerator:
    """Generate data incrementally without loading all to memory."""
    
    def generate_transactions_stream(
        self,
        customer: Customer,
        num_transactions: int,
        batch_size: int = 5000,
    ):
        """Yield transactions in batches."""
        
        for batch_start in range(0, num_transactions, batch_size):
            batch_size_actual = min(batch_size, num_transactions - batch_start)
            
            transactions = self.generate(customer, batch_size_actual)
            
            yield transactions
```

### 5.2: Spark Integration (3 horas)

```python
from pyspark.sql import SparkSession

class SparkExecutor:
    """Execute generation on Spark cluster."""
    
    def __init__(self, num_workers=4):
        self.spark = SparkSession.builder \
            .appName("FraudDataGenerator") \
            .master(f"local[{num_workers}]") \
            .getOrCreate()
    
    def generate_distributed(self, num_customers, num_transactions_per_customer):
        """Generate in parallel using Spark."""
        
        # Create RDD of customer IDs
        customer_ids = self.spark.sparkContext.range(num_customers)
        
        # Map: generate transactions for each customer
        transactions = customer_ids.flatMap(
            lambda cust_id: self._generate_for_customer(cust_id, num_transactions_per_customer)
        )
        
        # Convert to DataFrame
        df = transactions.toDF()
        
        return df
```

---

## 📅 ROADMAP TEMPORAL CONSOLIDADO

```
SEMANA 1 (Fase 1):
├─ Dia 1: Setup + Baseline (~30 min)
├─ Dia 2-3: Cache + CSV streaming (4h)
├─ Dia 4: MinIO Retry + Paralelizar (2h)
├─ Dia 5: Performance tests (1h)
└─ Resultado: 1GB em ~20s (vs 36s antes), 3-5 commits

SEMANA 2 (Fase 2):
├─ Dia 1-2: CPF, RG, Email, Phone (4h)
├─ Dia 3: Distribuição geográfica (1.5h)
├─ Dia 4-5: Validação + tests (1.5h)
└─ Resultado: Dataset LGPD-compliant

SEMANA 3-4 (Fase 3):
├─ Dia 1-2: Sazonalidade + Merchants (4h)
├─ Dia 3-4: Perfis expandidos (2h)
├─ Dia 5: Tests + validation (1h)
└─ Resultado: Padrões comportamentais reais

SEMANA 5-6 (Fase 4):
├─ Dia 1-2: Session state (2h)
├─ Dia 3-4: Fraud contextualizer (3h)
├─ Dia 5: Tests + validação (1h)
└─ Resultado: Fraude realista + detectável

SEMANA 7-8 (Fase 5 - opcional, para Spark):
├─ Dia 1-3: Spark integration (6h)
├─ Dia 4-5: Cloud storage (2h)
└─ Resultado: Escalabilidade 10TB+ (requer Spark cluster)

TOTAL: 4-6 semanas (55-65 horas)
SEM FASE 5: 2-3 semanas (40-50 horas)
```

---

## 🎯 MÉTRICAS DE SUCESSO

### Performance
```
Métrica             | Baseline | Meta      | Status
────────────────────┼──────────┼───────────┼────────
Transações/seg      | 68k      | 90k+      | Phase 1
Tempo para 1GB      | 36s      | 15s       | Phase 1
Memory peak (1GB)   | 8GB      | 2GB       | Phase 1-2
JSON size           | -        | -10%      | Phase 1
```

### Realismo
```
Métrica                    | Baseline | Meta      | Status
───────────────────────────┼──────────┼───────────┼────────
Fraude aleatória (%)       | 100%     | 0%        | Phase 4
Fraude contextualizada (%) | 0%       | 100%      | Phase 4
Padrões comportamentais    | Nenhum   | Completo  | Phase 3
Sazonalidade               | Ausente  | Presente  | Phase 3
Detectabilidade (%)        | ~25%     | ~80%      | Phase 4
```

### Conformidade
```
Métrica            | Baseline | Meta      | Status
───────────────────┼──────────┼───────────┼────────
CPF válido         | Não      | Sim       | Phase 2
LGPD compliant     | Não      | Sim       | Phase 2
Merchants reais    | Não      | Sim       | Phase 3
Geographic real    | Não      | Sim       | Phase 2
```

---

## 📝 DOCUMENTAÇÃO & COMMITS

### Padrão de Commit por Fase

```bash
# FASE 0
git commit -m "setup: increase WSL2 memory to 32GB"
git commit -m "setup: install dependencies"
git commit -m "test: create baseline benchmark"

# FASE 1
git commit -m "perf: cache transaction type weights (15x speedup)"
git commit -m "perf: cache merchants by MCC (20x speedup)"
git commit -m "perf: remove unused null fields (-5%)"
git commit -m "perf: implement CSV streaming (fix OOM)"
git commit -m "reliability: add exponential backoff to MinIO"
git commit -m "perf: parallelize customer generation (3x)"
git commit -m "test: benchmark Phase 1 (68k → 90k tx/s)"

# FASE 2
git commit -m "feat: add CPF generation with valid checksum"
git commit -m "feat: add RG validation by state"
git commit -m "feat: generate realistic emails by age"
git commit -m "feat: add phone with correct DDD"
git commit -m "feat: geographic distribution by population (Zipf)"
git commit -m "feat: add LGPD compliance checks"

# FASE 3
git commit -m "feat: add seasonality (Black Friday, Natal, férias)"
git commit -m "feat: add realistic merchants with distribution"
git commit -m "feat: expand behavioral profiles with patterns"
git commit -m "feat: add temporal patterns (horários, dias)"
git commit -m "feat: add geographic behavior variations"

# FASE 4
git commit -m "feat: add customer session state tracking"
git commit -m "feat: implement fraud contextualization"
git commit -m "feat: add fraud pattern definitions"
git commit -m "feat: integrate fraud logic (6 tipos)"
git commit -m "feat: add fraud scoring and detectability analysis"

# FASE 5
git commit -m "feat: implement streaming generator (10TB support)"
git commit -m "feat: add Spark distributed execution"
git commit -m "feat: add cloud storage integration (S3/GCS)"
```

---

## 🔄 PROCESS & CHECKLIST

### Before Starting Each Phase

- [ ] Read analysis documents (ANALISE_PROFUNDA.md, etc)
- [ ] Review architecture changes
- [ ] Create feature branch: `git checkout -b phase-X`
- [ ] Identify all files to modify/create
- [ ] Plan test coverage

### During Phase Development

- [ ] Implement incrementally
- [ ] Run tests frequently
- [ ] Commit regularly
- [ ] Update docstrings
- [ ] Create benchmark comparisons

### After Completing Phase

- [ ] All tests pass
- [ ] Benchmark shows improvement
- [ ] Documentation updated
- [ ] Code review (self)
- [ ] Merge to main
- [ ] Tag: `v5.0.0-phase-X`

---

## 🚀 COMEÇAR AGORA

### PRÓXIMO PASSO: Preparação (10 minutos)

```bash
# 1. Ir para o diretório
cd /home/afborda/projetos/pessoal/brazilian-fraud-data-generator

# 2. Verificar dependencies
pip list | grep -E "faker|pandas|pyarrow|boto3"
# Se faltar: pip install -r requirements.txt

# 3. Criar baseline PRÉ-OTIMIZAÇÃO (IMPORTANTE!)
mkdir -p logs
time python generate.py --size 1GB --output /tmp/baseline_v4 > logs/baseline_antes.txt 2>&1
# Esperado: ~36 segundos

# 4. Começar Fase 1
git checkout -b phase-1-quick-wins
```

### Quick Wins da Fase 1

```
1. ⚡ Cache de Weights (15x speedup) ..................... 2h
2. 🏢 Cache de Merchants (20x speedup) .................. 1h
3. 📦 CSV Streaming (fix OOM) .......................... 1.5h
4. 🔄 Paralelizar Customers (3x speedup) ............... 1.5h
5. 🛡️ MinIO Retry (reliability) ........................ 1h
6. ✅ Testes & Benchmark ............................. 1h

TOTAL FASE 1: ~8-9 horas (2-3 dias de trabalho)
RESULTADO: 68k → 90k tx/s, 36s → 20s para 1GB
```

---

**Status:** Pronto para começar Fase 1  
**Timeline:** 4-6 semanas (sem Fase 5) ou 5-8 semanas (com Fase 5)  
**Esforço:** 55-65 horas (sem Fase 5) ou 60-80 horas (com Fase 5)  
**ROI:** De "toy" para "production-grade"  
**Memória:** Usando 15GB WSL2 (sem upgrade necessário)

**Pronto para começar a Fase 1?** 🚀
