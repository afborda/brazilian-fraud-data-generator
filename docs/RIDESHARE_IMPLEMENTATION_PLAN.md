# 🚗 Plano de Implementação: Ride-Share Data Generator

**Versão Target:** 3.2.0  
**Módulo:** Geração de dados de corridas para apps de mobilidade  
**Apps Suportados:** Uber, 99, Cabify, InDriver  
**Data:** Dezembro 2025

---

## 📋 Visão Geral do Projeto Atual

O **Brazilian Fraud Data Generator** já possui uma arquitetura bem definida:

```
src/fraud_generator/
├── config/          # Configurações estáticas (banks, devices, geography, merchants, transactions)
├── connections/     # Conectores de streaming (kafka, stdout, webhook)
├── exporters/       # Exportadores de arquivo (csv, json, parquet)
├── generators/      # Geradores de dados (customer, device, transaction)
├── models/          # Dataclasses (Customer, Device, Transaction)
├── profiles/        # Perfis comportamentais (behavioral.py)
├── utils/           # Utilidades e streaming helpers
└── validators/      # Validadores (CPF)
```

**Entidades Existentes:**
- `Customer` → Dados pessoais, bancários, perfil comportamental
- `Device` → Dispositivos vinculados ao customer
- `Transaction` → Transações financeiras com 13 tipos de fraude

**Padrões Estabelecidos:**
- Dataclasses com `to_dict()`, `to_json()`, `from_dict()`
- Index classes (NamedTuple) para referências leves em memória
- Generators com `generate()`, `generate_batch()`
- Configurações com dicts de pesos para distribuições realistas

---

## 🎯 Objetivo da Implementação

Adicionar um módulo completo de **corridas de mobilidade urbana** que:
1. Reutiliza `Customer` como passageiro
2. Cria nova entidade `Driver` com veículo
3. Cria nova entidade `Ride` conectando passageiro ↔ motorista
4. Suporta batch e streaming como o módulo de transações
5. Implementa 6 tipos de fraude específicos de rideshare
6. Integra condições climáticas que afetam surge pricing

---

## 📊 Etapas de Implementação

### **ETAPA 1: Configurações Base**
**Duração Estimada:** 4-6 horas  
**Dependências:** Nenhuma  
**Arquivos Criados:**
- `src/fraud_generator/config/rideshare.py`
- `src/fraud_generator/config/weather.py`

#### 1.1 Criar `config/rideshare.py`

**Conteúdo:**
```python
# Apps e categorias
RIDESHARE_APPS = {
    'UBER': { 'categorias': ['UberX', 'Comfort', 'Black', 'Flash'], 'peso': 45 },
    '99': { 'categorias': ['Pop', '99Comfort', 'Black'], 'peso': 35 },
    'CABIFY': { 'categorias': ['Lite', 'Cabify', 'Plus'], 'peso': 10 },
    'INDRIVER': { 'categorias': ['Economy', 'Comfort'], 'peso': 10 },
}

# POIs (Points of Interest) por capital - 15-20 por cidade
POIS_POR_CAPITAL = {
    'SP': [
        {'nome': 'Aeroporto de Congonhas', 'tipo': 'AEROPORTO', 'lat': -23.6261, 'lon': -46.6564},
        {'nome': 'Aeroporto de Guarulhos', 'tipo': 'AEROPORTO', 'lat': -23.4356, 'lon': -46.4731},
        {'nome': 'Shopping Ibirapuera', 'tipo': 'SHOPPING', 'lat': -23.6098, 'lon': -46.6653},
        # ... mais POIs
    ],
    # ... 27 capitais
}

# Veículos populares brasileiros
VEICULOS_POPULARES = [
    {'marca': 'Hyundai', 'modelo': 'HB20', 'categoria_min': 'Pop'},
    {'marca': 'Chevrolet', 'modelo': 'Onix', 'categoria_min': 'Pop'},
    {'marca': 'Fiat', 'modelo': 'Argo', 'categoria_min': 'Pop'},
    {'marca': 'Fiat', 'modelo': 'Mobi', 'categoria_min': 'Pop'},
    {'marca': 'Renault', 'modelo': 'Kwid', 'categoria_min': 'Pop'},
    {'marca': 'Volkswagen', 'modelo': 'Gol', 'categoria_min': 'Pop'},
    {'marca': 'Toyota', 'modelo': 'Corolla', 'categoria_min': 'Comfort'},
    {'marca': 'Honda', 'modelo': 'Civic', 'categoria_min': 'Comfort'},
    {'marca': 'Toyota', 'modelo': 'Corolla Cross', 'categoria_min': 'Black'},
    # ... mais veículos
]

# Taxas por categoria
TAXAS_POR_CATEGORIA = {
    'UberX': {'base': 5.0, 'km': 1.20, 'min': 0.25},
    'Pop': {'base': 4.5, 'km': 1.10, 'min': 0.20},
    # ...
}

# Status de corrida
RIDE_STATUS = ['SOLICITADA', 'ACEITA', 'EM_ANDAMENTO', 'FINALIZADA', 'CANCELADA_PASSAGEIRO', 'CANCELADA_MOTORISTA', 'SEM_MOTORISTA']

# Fraudes específicas de rideshare
RIDESHARE_FRAUD_TYPES = {
    'CORRIDA_FANTASMA': 15,        # Driver inicia/finaliza sem passageiro
    'GPS_SPOOFING': 20,            # Manipulação de localização
    'SURGE_ABUSE': 15,             # Criar demanda artificial
    'CONTA_MULTIPLA_DRIVER': 12,   # Mesmo motorista, várias contas
    'PROMO_ABUSE': 18,             # Criar contas para usar promoções
    'RATING_FRAUD': 10,            # Manipulação de avaliações
    'SPLIT_FARE_FRAUD': 10,        # Fraude em corridas compartilhadas
}

# Métodos de pagamento
PAYMENT_METHODS = {
    'PIX': 30,
    'CARTAO_CREDITO': 35,
    'CARTAO_DEBITO': 15,
    'DINHEIRO': 15,
    'VOUCHER_CORPORATIVO': 5,
}
```

#### 1.2 Criar `config/weather.py`

**Conteúdo:**
```python
# Regiões brasileiras
REGIOES = {
    'NORTE': ['AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO'],
    'NORDESTE': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'CENTRO_OESTE': ['DF', 'GO', 'MT', 'MS'],
    'SUDESTE': ['ES', 'MG', 'RJ', 'SP'],
    'SUL': ['PR', 'RS', 'SC'],
}

# Condições climáticas e impacto no surge
WEATHER_CONDITIONS = {
    'CLEAR': {'surge_impact': 1.0, 'desc': 'Tempo limpo'},
    'CLOUDY': {'surge_impact': 1.0, 'desc': 'Nublado'},
    'LIGHT_RAIN': {'surge_impact': 1.3, 'desc': 'Garoa'},
    'RAIN': {'surge_impact': 1.6, 'desc': 'Chuva'},
    'HEAVY_RAIN': {'surge_impact': 2.0, 'desc': 'Chuva forte'},
    'STORM': {'surge_impact': 2.5, 'desc': 'Tempestade'},
}

# Temperaturas médias por região e estação
TEMP_POR_REGIAO = {
    'NORTE': {'verao': (26, 34), 'inverno': (24, 32)},
    'NORDESTE': {'verao': (26, 35), 'inverno': (22, 30)},
    'CENTRO_OESTE': {'verao': (24, 35), 'inverno': (18, 30)},
    'SUDESTE': {'verao': (22, 35), 'inverno': (12, 25)},
    'SUL': {'verao': (20, 32), 'inverno': (5, 18)},
}

def generate_weather(state: str, dt: datetime) -> dict:
    """Gera condição climática realista para estado e data."""
    # Implementação
```

#### 1.3 Atualizar `config/__init__.py`

Adicionar exports dos novos módulos.

---

### **ETAPA 2: Modelos de Dados**
**Duração Estimada:** 3-4 horas  
**Dependências:** Etapa 1  
**Arquivos Criados:**
- `src/fraud_generator/models/ride.py`

#### 2.1 Criar `models/ride.py`

**Estrutura seguindo padrão existente:**

```python
@dataclass
class Driver:
    """Motorista de app de mobilidade."""
    driver_id: str
    nome: str
    cpf: str
    cnh_numero: str
    cnh_categoria: str  # B, AB, C, D
    cnh_validade: date
    telefone: str
    email: str
    # Veículo
    vehicle_plate: str
    vehicle_brand: str
    vehicle_model: str
    vehicle_year: int
    vehicle_color: str
    # Métricas
    rating: float
    trips_completed: int
    registration_date: datetime
    active_apps: List[str]
    operating_city: str
    operating_state: str
    categories_enabled: List[str]
    is_active: bool
    
    def to_dict(self) -> Dict[str, Any]: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Driver': ...


@dataclass
class Location:
    """Localização com POI."""
    lat: float
    lon: float
    name: str
    poi_type: str  # AEROPORTO, SHOPPING, HOSPITAL, etc.


@dataclass
class Ride:
    """Corrida de app de mobilidade."""
    ride_id: str
    timestamp: datetime
    app: str  # UBER, 99, CABIFY, INDRIVER
    category: str  # UberX, Pop, Black, etc.
    driver_id: str
    passenger_id: str  # customer_id existente
    
    # Localizações
    pickup_location: Location
    dropoff_location: Location
    
    # Timestamps da corrida
    request_datetime: datetime
    accept_datetime: Optional[datetime]
    pickup_datetime: Optional[datetime]
    dropoff_datetime: Optional[datetime]
    
    # Métricas da corrida
    distance_km: float
    duration_minutes: int
    wait_time_minutes: int
    
    # Valores
    base_fare: float
    surge_multiplier: float
    final_fare: float
    driver_pay: float
    platform_fee: float
    tip: float
    payment_method: str
    
    # Status e avaliações
    status: str
    driver_rating: Optional[int]  # 1-5
    passenger_rating: Optional[int]  # 1-5
    cancellation_reason: Optional[str]
    
    # Contexto
    weather: str
    is_fraud: bool
    fraud_type: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ride': ...


class DriverIndex(NamedTuple):
    """Referência leve para Driver."""
    driver_id: str
    operating_state: str
    operating_city: str
    active_apps: tuple  # tuple para ser hashable


class RideIndex(NamedTuple):
    """Referência leve para Ride."""
    ride_id: str
    driver_id: str
    passenger_id: str
    app: str
    city: str
```

#### 2.2 Atualizar `models/__init__.py`

```python
from .ride import Driver, Ride, Location, DriverIndex, RideIndex
```

---

### **ETAPA 3: Geradores**
**Duração Estimada:** 6-8 horas  
**Dependências:** Etapas 1 e 2  
**Arquivos Criados:**
- `src/fraud_generator/generators/driver.py`
- `src/fraud_generator/generators/ride.py`

#### 3.1 Criar `generators/driver.py`

**Seguindo padrão de `CustomerGenerator`:**

```python
class DriverGenerator:
    """Gerador de motoristas de apps de mobilidade."""
    
    def __init__(self, seed: Optional[int] = None):
        self.faker = Faker('pt_BR')
        if seed:
            self.faker.seed_instance(seed)
            random.seed(seed)
    
    def generate(self, driver_id: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Gera um motorista."""
        # CPF válido usando validador existente
        # CNH com número de 11 dígitos, categoria B/AB/C/D
        # Placa Mercosul (ABC1D23) ou antiga (ABC-1234)
        # Veículo do config baseado em categorias habilitadas
        # Rating ~ normal(4.7, 0.2) clamp [4.0, 5.0]
        # trips_completed ~ 50-5000+
        
    def generate_batch(self, count: int, start_id: int = 1) -> List[Dict[str, Any]]:
        """Gera múltiplos motoristas."""
        
    def generate_index(self, driver_dict: Dict[str, Any]) -> DriverIndex:
        """Cria índice leve do motorista."""
```

**Funções auxiliares necessárias:**
- `generate_cnh()` → Número 11 dígitos, categoria, validade
- `generate_vehicle_plate()` → Mercosul ou formato antigo
- `select_vehicle_for_categories()` → Escolhe veículo compatível

#### 3.2 Criar `generators/ride.py`

**Seguindo padrão de `TransactionGenerator`:**

```python
class RideGenerator:
    """Gerador de corridas de apps de mobilidade."""
    
    def __init__(
        self,
        fraud_rate: float = 0.02,
        use_profiles: bool = True,
        seed: Optional[int] = None
    ):
        self.fraud_rate = fraud_rate
        self.use_profiles = use_profiles
        # ...
    
    def generate(
        self,
        ride_id: str,
        driver_id: str,
        passenger_id: str,
        timestamp: datetime,
        passenger_state: str,
        passenger_profile: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Gera uma corrida."""
        # Seleção de POI origem/destino (mesma cidade, categorias diferentes)
        # Distância Haversine * fator urbano (1.3-1.5)
        # Duração = distância / velocidade_média (25-35 km/h)
        # Preço = base + km*taxa + min*taxa
        # Surge por horário * clima
        # Distribuição status (85% FINALIZADA, 10% CANCELADA, 5% outras)
        # Fraude 2% default
```

**Funções auxiliares necessárias:**
- `haversine_distance()` → Cálculo de distância
- `calculate_surge()` → Baseado em horário + clima
- `calculate_fare()` → Preço final com taxas
- `select_pois()` → Origem/destino realistas

#### 3.3 Atualizar `generators/__init__.py`

```python
from .driver import DriverGenerator
from .ride import RideGenerator
```

---

### **ETAPA 4: Perfis Comportamentais de Corridas**
**Duração Estimada:** 2-3 horas  
**Dependências:** Etapa 3  
**Arquivos Criados:**
- `src/fraud_generator/profiles/ride_behavioral.py`

#### 4.1 Criar `profiles/ride_behavioral.py`

**6 perfis de uso de rideshare:**

```python
class RideProfileType(Enum):
    DAILY_COMMUTER = "daily_commuter"      # 2x/dia útil, casa-trabalho
    OCCASIONAL_USER = "occasional_user"     # 2-4x/semana, shoppings/lazer
    FREQUENT_TRAVELER = "frequent_traveler" # Aeroportos, hotéis, corporativo
    NIGHTLIFE = "nightlife"                 # Sex-Dom 22h-04h
    BUSINESS = "business"                   # Horário comercial, premium
    ECONOMY_FOCUSED = "economy_focused"     # Sempre Pop/UberX


@dataclass
class RideBehavioralProfile:
    name: str
    description: str
    preferred_apps: Dict[str, int]      # Pesos por app
    preferred_categories: Dict[str, int] # Pesos por categoria
    preferred_hours: List[int]          # Horários típicos
    monthly_rides: Tuple[int, int]      # Range de corridas/mês
    preferred_poi_types: List[str]      # Tipos de destino
    weekend_multiplier: float           # Atividade fim de semana
    tip_probability: float              # Probabilidade de gorjeta
    tip_range: Tuple[float, float]      # Range de gorjeta (% do valor)
```

**Mapeamento com perfis existentes:**
- `young_digital` → `nightlife` + `economy_focused`
- `high_spender` → `business` + `frequent_traveler`
- `business_owner` → `business`
- `traditional_senior` → `occasional_user`
- `family_provider` → `daily_commuter`

#### 4.2 Atualizar `profiles/__init__.py`

Adicionar exports dos novos perfis.

---

### **ETAPA 5: Integração com Utils e Streaming**
**Duração Estimada:** 2-3 horas  
**Dependências:** Etapas 2, 3, 4  
**Arquivos Modificados:**
- `src/fraud_generator/utils/streaming.py`
- `src/fraud_generator/utils/__init__.py`
- `src/fraud_generator/__init__.py`

#### 5.1 Atualizar `utils/streaming.py`

Adicionar:
- `create_driver_index()` → Helper para criar DriverIndex
- `create_ride_index()` → Helper para criar RideIndex
- Atualizar `BatchGenerator` para suportar drivers e rides

#### 5.2 Atualizar exports

Garantir que todos os novos componentes estão acessíveis via imports principais.

---

### **ETAPA 6: CLI - Batch Mode (generate.py)**
**Duração Estimada:** 4-5 horas  
**Dependências:** Etapas 1-5  
**Arquivos Modificados:**
- `generate.py`

#### 6.1 Modificações no generate.py

**Novo argumento:**
```bash
--type {transactions,rides,all}  # Default: transactions
```

**Novo fluxo para rides:**
```
Phase 1: Generate customers (reutiliza existente)
Phase 2: Generate devices (reutiliza existente)
Phase 3: Generate drivers (NOVO)
Phase 4: Generate rides (NOVO)
```

**Output para rides:**
```
output/
├── customers.jsonl       # Reutilizado como passageiros
├── devices.jsonl         # Reutilizado
├── drivers.jsonl         # NOVO - Motoristas
└── rides_*.jsonl         # NOVO - Corridas (~128MB cada)
```

#### 6.2 Atualizar versão

```python
__version__ = "3.2.0"
```

---

### **ETAPA 7: CLI - Streaming Mode (stream.py)**
**Duração Estimada:** 3-4 horas  
**Dependências:** Etapa 6  
**Arquivos Modificados:**
- `stream.py`

#### 7.1 Modificações no stream.py

**Novo argumento:**
```bash
--type {transactions,rides}  # Default: transactions
```

**Novo fluxo:**
- Gerar base de customers + devices (existente)
- Gerar base de drivers (NOVO para rides)
- Streaming de rides em tempo real

---

### **ETAPA 8: Testes e Validação**
**Duração Estimada:** 3-4 horas  
**Dependências:** Etapas 6, 7

#### 8.1 Testes de Batch

```bash
# Testar geração de rides
python3 generate.py --size 100MB --type rides --output ./test_rides

# Validar output
ls -la ./test_rides/
head -n 5 ./test_rides/drivers.jsonl
head -n 5 ./test_rides/rides_0000.jsonl
```

#### 8.2 Testes de Streaming

```bash
# Testar streaming de rides
python3 stream.py --target stdout --type rides --rate 5 --max-events 10 --pretty
```

#### 8.3 Validações

- [ ] Formato JSON válido
- [ ] CPFs válidos (motoristas e passageiros)
- [ ] CNHs com formato correto
- [ ] Placas formato Mercosul ou antigo
- [ ] Correlação `customer_id` ↔ `passenger_id`
- [ ] Correlação `driver_id` em rides
- [ ] POIs existentes para cidade do estado
- [ ] Valores de corrida coerentes (distância × tarifa)
- [ ] Surge realista por horário
- [ ] Distribuição de status (~85% FINALIZADA)
- [ ] Taxa de fraude conforme configurado

---

### **ETAPA 9: Documentação**
**Duração Estimada:** 2-3 horas  
**Dependências:** Etapa 8

#### 9.1 Atualizar README.md

Adicionar seção:
- **🚗 Ride-Share Mode** (novo)
  - Descrição do módulo
  - Apps suportados
  - Categorias por app
  - Exemplo de uso batch
  - Exemplo de uso streaming
  - Schema dos dados gerados (Driver, Ride)
  - Tipos de fraude específicos

#### 9.2 Atualizar README.pt-BR.md

Mesmo conteúdo em português.

#### 9.3 Criar exemplos

- `examples/rides/` com scripts de exemplo

---

## 📅 Cronograma Sugerido

| Etapa | Descrição | Horas | Acumulado |
|-------|-----------|-------|-----------|
| 1 | Configurações Base | 4-6h | 4-6h |
| 2 | Modelos de Dados | 3-4h | 7-10h |
| 3 | Geradores | 6-8h | 13-18h |
| 4 | Perfis Comportamentais | 2-3h | 15-21h |
| 5 | Utils e Streaming | 2-3h | 17-24h |
| 6 | CLI Batch | 4-5h | 21-29h |
| 7 | CLI Streaming | 3-4h | 24-33h |
| 8 | Testes e Validação | 3-4h | 27-37h |
| 9 | Documentação | 2-3h | 29-40h |

**Total Estimado:** 29-40 horas de desenvolvimento

---

## 🔮 Extensibilidade Futura

A arquitetura proposta facilita a adição futura de:

### Delivery (iFood, Rappi, Uber Eats)
- Reutiliza `Driver` (adicionar tipo: MOTO/BIKE/CAR)
- Nova entidade `Delivery` similar a `Ride`
- Novos POIs: restaurantes, mercados
- Config: `delivery.py` com restaurantes, tempos preparo

### Outros módulos potenciais
- **Patinetes/Bikes compartilhados** (Lime, Yellow, Grin)
- **Táxi tradicional** (rádio táxi, cooperativas)
- **Fretado/Corporativo** (BlaBlaCar, Buser)

---

## ✅ Checklist de Implementação

- [ ] **Etapa 1:** Config rideshare.py e weather.py
- [ ] **Etapa 2:** Models ride.py (Driver, Ride, Location, Indexes)
- [ ] **Etapa 3:** Generators driver.py e ride.py
- [ ] **Etapa 4:** Profiles ride_behavioral.py
- [ ] **Etapa 5:** Utils e streaming integração
- [ ] **Etapa 6:** CLI generate.py com --type rides
- [ ] **Etapa 7:** CLI stream.py com --type rides
- [ ] **Etapa 8:** Testes e validação completa
- [ ] **Etapa 9:** Documentação README

---

*Documento criado em Dezembro 2025*  
*Brazilian Fraud Data Generator v3.2.0*
