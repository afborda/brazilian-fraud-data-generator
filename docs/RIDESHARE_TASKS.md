# 📋 Tarefas de Implementação - Ride-Share Module

**Versão:** 3.2.0  
**Status:** Em andamento

---

## Como Usar Este Documento

Copie cada prompt abaixo e cole no chat para executar em partes.
Marque [x] quando completar cada tarefa.

---

## ETAPA 1: Configurações Base

### Tarefa 1.1 - Criar config/rideshare.py
```
Seguindo o plano em docs/RIDESHARE_IMPLEMENTATION_PLAN.md, crie o arquivo src/fraud_generator/config/rideshare.py com:

1. RIDESHARE_APPS - Dict com apps (UBER, 99, CABIFY, INDRIVER) com categorias e pesos
2. POIS_POR_CAPITAL - POIs para todas as 27 capitais brasileiras (15-20 POIs cada com nome, tipo, lat, lon). Tipos: AEROPORTO, SHOPPING, RODOVIARIA, HOSPITAL, UNIVERSIDADE, ESTADIO, CENTRO_EMPRESARIAL, TERMINAL_ONIBUS, PARQUE, PRAIA, CENTRO_HISTORICO, HOTEL, FEIRA, MERCADO
3. VEICULOS_POPULARES - Lista de veículos brasileiros (HB20, Onix, Argo, Mobi, Kwid, Gol, Corolla, Civic, etc.) com marca, modelo, anos 2015-2025, cores, categoria_min
4. TAXAS_POR_CATEGORIA - Taxas base, por km, por minuto para cada categoria
5. SURGE_POR_HORARIO - Multiplicadores por faixa horária
6. RIDE_STATUS - Lista de status possíveis
7. CANCELLATION_REASONS - Motivos de cancelamento
8. RIDESHARE_FRAUD_TYPES - 6 tipos de fraude com pesos
9. PAYMENT_METHODS - Métodos de pagamento com pesos
10. CORES_VEICULOS - Lista de cores comuns
11. Helpers: get_app_categories(), get_pois_for_city(), get_random_vehicle()
```
- [ ] Concluído

### Tarefa 1.2 - Criar config/weather.py
```
Crie o arquivo src/fraud_generator/config/weather.py com:

1. REGIOES - Dict mapeando região para lista de estados (NORTE, NORDESTE, CENTRO_OESTE, SUDESTE, SUL)
2. WEATHER_CONDITIONS - Condições climáticas (CLEAR, CLOUDY, LIGHT_RAIN, RAIN, HEAVY_RAIN, STORM) com surge_impact (1.0 a 2.5)
3. TEMP_POR_REGIAO - Temperaturas médias por região e estação (verão/inverno)
4. PROB_CHUVA_POR_MES - Probabilidade de chuva por mês e região
5. Helper: get_region_for_state(state) - retorna região do estado
6. Helper: get_season(month) - retorna estação do ano
7. Helper: generate_weather(state, datetime) - retorna dict com condition, temperature, surge_impact
```
- [ ] Concluído

### Tarefa 1.3 - Atualizar config/__init__.py
```
Atualize src/fraud_generator/config/__init__.py para exportar os novos módulos rideshare e weather.
```
- [ ] Concluído

---

## ETAPA 2: Modelos de Dados

### Tarefa 2.1 - Criar models/ride.py
```
Crie o arquivo src/fraud_generator/models/ride.py seguindo o padrão de models/customer.py com:

1. @dataclass Location - lat, lon, name, poi_type, city, state. Métodos: to_dict()

2. @dataclass Driver - driver_id, nome, cpf, cnh_numero, cnh_categoria (B/AB/C/D/E), cnh_validade, telefone, email, vehicle_plate, vehicle_brand, vehicle_model, vehicle_year, vehicle_color, rating (float), trips_completed (int), registration_date, active_apps (List[str]), operating_city, operating_state, categories_enabled (List[str]), is_active (bool). Métodos: to_dict(), to_json(), from_dict()

3. @dataclass Ride - ride_id, timestamp, app, category, driver_id, passenger_id, pickup_location (Location), dropoff_location (Location), request_datetime, accept_datetime, pickup_datetime, dropoff_datetime, distance_km, duration_minutes, wait_time_minutes, base_fare, surge_multiplier, final_fare, driver_pay, platform_fee, tip, payment_method, status, driver_rating, passenger_rating, cancellation_reason, weather_condition, temperature, is_fraud, fraud_type. Métodos: to_dict(), to_json(), from_dict()

4. class DriverIndex(NamedTuple) - driver_id, operating_state, operating_city, active_apps (tuple)

5. class RideIndex(NamedTuple) - ride_id, driver_id, passenger_id, app, city

6. Helpers: create_driver_index(driver_dict), create_ride_index(ride_dict)
```
- [ ] Concluído

### Tarefa 2.2 - Atualizar models/__init__.py
```
Atualize src/fraud_generator/models/__init__.py para exportar Driver, Ride, Location, DriverIndex, RideIndex e os helpers.
```
- [ ] Concluído

---

## ETAPA 3: Geradores

### Tarefa 3.1 - Criar generators/driver.py
```
Crie o arquivo src/fraud_generator/generators/driver.py seguindo o padrão de generators/customer.py com:

1. class DriverGenerator:
   - __init__(self, seed=None) - inicializa Faker pt_BR
   - generate(self, driver_id, state=None) -> Dict - gera um motorista completo
   - generate_batch(self, count, start_id=1) -> List[Dict]
   - generate_index(self, driver_dict) -> DriverIndex

2. Funções auxiliares:
   - generate_cnh() - número 11 dígitos, categoria B/AB/C/D/E, validade 1-5 anos
   - generate_vehicle_plate(use_mercosul=None) - 70% Mercosul (ABC1D23), 30% antiga (ABC-1234)
   - select_vehicle_for_categories(categories) - escolhe veículo compatível do config

3. Lógica de geração:
   - CPF válido usando generate_valid_cpf() existente
   - Rating: random.gauss(4.7, 0.2) clamp entre 4.0 e 5.0
   - trips_completed: distribuição realista (maioria 100-1000, alguns 1000-5000)
   - active_apps: 1-3 apps aleatórios
   - categories_enabled: baseado no veículo
```
- [ ] Concluído

### Tarefa 3.2 - Criar generators/ride.py
```
Crie o arquivo src/fraud_generator/generators/ride.py seguindo o padrão de generators/transaction.py com:

1. class RideGenerator:
   - __init__(self, fraud_rate=0.02, use_profiles=True, seed=None)
   - generate(self, ride_id, driver_id, passenger_id, timestamp, passenger_state, passenger_profile=None) -> Dict
   - generate_batch(self, count, drivers, passengers, start_id=1) -> List[Dict]

2. Funções auxiliares:
   - haversine_distance(lat1, lon1, lat2, lon2) -> float km
   - calculate_surge(hour, weather_condition) -> float multiplicador
   - calculate_fare(distance_km, duration_min, category, surge) -> dict com base_fare, final_fare, driver_pay, platform_fee
   - select_pois(state, city) -> tuple(pickup_poi, dropoff_poi) diferentes

3. Lógica de geração:
   - POI origem/destino da mesma cidade, tipos diferentes
   - Distância real Haversine * fator urbano (1.3-1.5)
   - Duração = distância / velocidade_média (25-35 km/h conforme hora)
   - Surge por horário (pico manhã/tarde/noite) * clima
   - Status: 85% FINALIZADA, 10% CANCELADA, 5% outras
   - Fraude: fraud_rate default, tipos do config
   - Integração com weather.generate_weather()
```
- [ ] Concluído

### Tarefa 3.3 - Atualizar generators/__init__.py
```
Atualize src/fraud_generator/generators/__init__.py para exportar DriverGenerator e RideGenerator.
```
- [ ] Concluído

---

## ETAPA 4: Perfis Comportamentais

### Tarefa 4.1 - Criar profiles/ride_behavioral.py
```
Crie o arquivo src/fraud_generator/profiles/ride_behavioral.py seguindo o padrão de profiles/behavioral.py com:

1. class RideProfileType(Enum) - 6 tipos + RANDOM

2. @dataclass RideBehavioralProfile com campos para preferências de corrida

3. RIDE_PROFILES dict com 6 perfis:
   - DAILY_COMMUTER: 2x/dia útil, horários fixos (7-9h, 17-19h), POIs residencial↔empresarial
   - OCCASIONAL_USER: 2-4x/semana, shoppings/lazer/parques, horários variados
   - FREQUENT_TRAVELER: aeroportos, hotéis, corporativo, categorias comfort+
   - NIGHTLIFE: sex-dom 22h-04h, bares/baladas/restaurantes, surge alto aceito
   - BUSINESS: horário comercial, categorias premium (Black, Comfort), gorjeta alta
   - ECONOMY_FOCUSED: sempre Pop/UberX/99Pop, sensível a preço, sem gorjeta

4. CUSTOMER_TO_RIDE_PROFILE - mapeamento de perfis existentes:
   - young_digital → [nightlife, economy_focused]
   - high_spender → [business, frequent_traveler]
   - business_owner → [business, frequent_traveler]
   - traditional_senior → [occasional_user]
   - family_provider → [daily_commuter, occasional_user]
   - subscription_heavy → [daily_commuter, economy_focused]

5. Helper: get_ride_profile_for_customer(customer_profile) -> RideProfileType
```
- [ ] Concluído

### Tarefa 4.2 - Atualizar profiles/__init__.py
```
Atualize src/fraud_generator/profiles/__init__.py para exportar RideProfileType, RideBehavioralProfile, RIDE_PROFILES, get_ride_profile_for_customer.
```
- [ ] Concluído

---

## ETAPA 5: Utils e Streaming

### Tarefa 5.1 - Atualizar utils/streaming.py
```
Atualize src/fraud_generator/utils/streaming.py para adicionar:

1. Importar DriverIndex, RideIndex de models.ride
2. Função create_driver_index(driver_dict) -> DriverIndex
3. Função create_ride_index(ride_dict) -> RideIndex
4. Atualizar BatchGenerator para ter:
   - driver_index: List[DriverIndex]
   - add_driver_index(index)
   - get_random_driver(state=None, city=None)
```
- [ ] Concluído

### Tarefa 5.2 - Atualizar utils/__init__.py
```
Atualize src/fraud_generator/utils/__init__.py para exportar DriverIndex, RideIndex e os novos helpers.
```
- [ ] Concluído

### Tarefa 5.3 - Atualizar __init__.py principal
```
Atualize src/fraud_generator/__init__.py para:
1. Importar DriverGenerator, RideGenerator
2. Atualizar __version__ para "3.2.0"
3. Atualizar __all__ com os novos exports
```
- [ ] Concluído

---

## ETAPA 6: CLI Batch Mode

### Tarefa 6.1 - Atualizar generate.py - Argumentos
```
Atualize generate.py para adicionar:

1. Novo argumento --type com choices=['transactions', 'rides', 'all'], default='transactions'
2. Atualizar __version__ para "3.2.0"
3. Atualizar docstring com exemplos de --type rides
```
- [ ] Concluído

### Tarefa 6.2 - Atualizar generate.py - Geração de Drivers
```
Atualize generate.py para adicionar Phase 3 (se --type rides ou all):

1. Importar DriverGenerator, RideGenerator
2. Calcular num_drivers baseado no tamanho (ex: 1 driver para cada 50 rides)
3. Gerar drivers com DriverGenerator
4. Salvar drivers.jsonl
5. Criar driver_indexes para referência
```
- [ ] Concluído

### Tarefa 6.3 - Atualizar generate.py - Geração de Rides
```
Atualize generate.py para adicionar Phase 4 (se --type rides ou all):

1. Usar worker similar ao de transactions
2. Gerar rides referenciando customers existentes como passageiros
3. Gerar rides referenciando drivers existentes
4. Salvar rides_XXXX.jsonl (múltiplos arquivos ~128MB)
5. Atualizar estatísticas finais
```
- [ ] Concluído

---

## ETAPA 7: CLI Streaming Mode

### Tarefa 7.1 - Atualizar stream.py
```
Atualize stream.py para adicionar:

1. Novo argumento --type com choices=['transactions', 'rides'], default='transactions'
2. Atualizar __version__ para "3.2.0"
3. Importar DriverGenerator, RideGenerator
4. Se --type rides:
   - Gerar base de drivers além de customers/devices
   - Usar RideGenerator no loop de streaming
   - Ajustar output para formato de ride
```
- [ ] Concluído

---

## ETAPA 8: Testes

### Tarefa 8.1 - Testar Batch Mode
```
Execute os seguintes comandos para testar o batch mode:

1. python3 generate.py --size 50MB --type rides --output ./test_rides
2. Verificar se criou: customers.jsonl, devices.jsonl, drivers.jsonl, rides_*.jsonl
3. Validar JSON: head -n 3 ./test_rides/drivers.jsonl | python3 -m json.tool
4. Validar JSON: head -n 3 ./test_rides/rides_0000.jsonl | python3 -m json.tool
5. Contar registros: wc -l ./test_rides/*.jsonl
```
- [ ] Concluído

### Tarefa 8.2 - Testar Streaming Mode
```
Execute os seguintes comandos para testar o streaming mode:

1. python3 stream.py --target stdout --type rides --rate 5 --max-events 10 --pretty
2. Verificar se os campos estão corretos
3. Verificar correlação driver_id e passenger_id
```
- [ ] Concluído

### Tarefa 8.3 - Validações de Dados
```
Verifique as seguintes validações nos dados gerados:

1. CPFs de motoristas são válidos (11 dígitos, dígitos verificadores corretos)
2. CNHs têm formato correto (11 dígitos numéricos)
3. Placas são Mercosul (ABC1D23) ou antiga (ABC-1234)
4. POIs existem para a cidade/estado
5. Distância × tarifa são coerentes
6. Ratings entre 1.0 e 5.0
7. Status tem distribuição aproximada (85% FINALIZADA)
```
- [ ] Concluído

---

## ETAPA 9: Documentação (Opcional)

### Tarefa 9.1 - Atualizar README.md
```
Adicione uma seção "🚗 Ride-Share Mode" no README.md com:

1. Descrição do módulo
2. Apps suportados (Uber, 99, Cabify, InDriver)
3. Exemplos de uso batch e streaming
4. Schema dos dados (Driver, Ride)
5. Tipos de fraude específicos
```
- [ ] Concluído

---

## Progresso Geral

| Etapa | Descrição | Status |
|-------|-----------|--------|
| 1 | Configurações Base | ⬜ Pendente |
| 2 | Modelos de Dados | ⬜ Pendente |
| 3 | Geradores | ⬜ Pendente |
| 4 | Perfis Comportamentais | ⬜ Pendente |
| 5 | Utils e Streaming | ⬜ Pendente |
| 6 | CLI Batch | ⬜ Pendente |
| 7 | CLI Streaming | ⬜ Pendente |
| 8 | Testes | ⬜ Pendente |
| 9 | Documentação | ⬜ Opcional |

---

*Última atualização: Dezembro 2025*
