"""
Configuration module for Brazilian geographic data.
Contains states, coordinates, and population weights.
"""

# Brazilian states with coordinates (centro aproximado) and population weight
ESTADOS_BR = {
    'SP': {'name': 'São Paulo', 'lat': -23.55, 'lon': -46.64, 'weight': 22},
    'RJ': {'name': 'Rio de Janeiro', 'lat': -22.91, 'lon': -43.17, 'weight': 8},
    'MG': {'name': 'Minas Gerais', 'lat': -19.92, 'lon': -43.94, 'weight': 10},
    'BA': {'name': 'Bahia', 'lat': -12.97, 'lon': -38.51, 'weight': 7},
    'RS': {'name': 'Rio Grande do Sul', 'lat': -30.03, 'lon': -51.23, 'weight': 6},
    'PR': {'name': 'Paraná', 'lat': -25.43, 'lon': -49.27, 'weight': 6},
    'PE': {'name': 'Pernambuco', 'lat': -8.05, 'lon': -34.88, 'weight': 5},
    'CE': {'name': 'Ceará', 'lat': -3.72, 'lon': -38.54, 'weight': 4},
    'PA': {'name': 'Pará', 'lat': -1.46, 'lon': -48.50, 'weight': 4},
    'SC': {'name': 'Santa Catarina', 'lat': -27.60, 'lon': -48.55, 'weight': 4},
    'GO': {'name': 'Goiás', 'lat': -16.68, 'lon': -49.25, 'weight': 4},
    'MA': {'name': 'Maranhão', 'lat': -2.53, 'lon': -44.27, 'weight': 3},
    'PB': {'name': 'Paraíba', 'lat': -7.12, 'lon': -34.86, 'weight': 2},
    'ES': {'name': 'Espírito Santo', 'lat': -20.32, 'lon': -40.34, 'weight': 2},
    'AM': {'name': 'Amazonas', 'lat': -3.10, 'lon': -60.02, 'weight': 2},
    'RN': {'name': 'Rio Grande do Norte', 'lat': -5.79, 'lon': -35.21, 'weight': 2},
    'PI': {'name': 'Piauí', 'lat': -5.09, 'lon': -42.80, 'weight': 2},
    'AL': {'name': 'Alagoas', 'lat': -9.67, 'lon': -35.74, 'weight': 2},
    'MT': {'name': 'Mato Grosso', 'lat': -15.60, 'lon': -56.10, 'weight': 2},
    'MS': {'name': 'Mato Grosso do Sul', 'lat': -20.44, 'lon': -54.65, 'weight': 1},
    'DF': {'name': 'Distrito Federal', 'lat': -15.78, 'lon': -47.93, 'weight': 2},
    'SE': {'name': 'Sergipe', 'lat': -10.91, 'lon': -37.07, 'weight': 1},
    'RO': {'name': 'Rondônia', 'lat': -8.76, 'lon': -63.90, 'weight': 1},
    'TO': {'name': 'Tocantins', 'lat': -10.18, 'lon': -48.33, 'weight': 1},
    'AC': {'name': 'Acre', 'lat': -9.97, 'lon': -67.81, 'weight': 0.5},
    'AP': {'name': 'Amapá', 'lat': 0.03, 'lon': -51.05, 'weight': 0.5},
    'RR': {'name': 'Roraima', 'lat': 2.82, 'lon': -60.67, 'weight': 0.5},
}

ESTADOS_LIST = list(ESTADOS_BR.keys())
ESTADOS_WEIGHTS = [ESTADOS_BR[e]['weight'] for e in ESTADOS_LIST]

# Major cities by state with approximate coordinates
CIDADES_POR_ESTADO = {
    'SP': ['São Paulo', 'Campinas', 'Santos', 'Ribeirão Preto', 'São José dos Campos', 'Sorocaba', 'Osasco', 'Santo André'],
    'RJ': ['Rio de Janeiro', 'Niterói', 'Petrópolis', 'Nova Iguaçu', 'Duque de Caxias', 'São Gonçalo', 'Campos dos Goytacazes'],
    'MG': ['Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora', 'Betim', 'Montes Claros', 'Uberaba'],
    'BA': ['Salvador', 'Feira de Santana', 'Vitória da Conquista', 'Camaçari', 'Itabuna', 'Juazeiro', 'Lauro de Freitas'],
    'RS': ['Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas', 'Santa Maria', 'Gravataí', 'Novo Hamburgo'],
    'PR': ['Curitiba', 'Londrina', 'Maringá', 'Ponta Grossa', 'Cascavel', 'São José dos Pinhais', 'Foz do Iguaçu'],
    'PE': ['Recife', 'Jaboatão dos Guararapes', 'Olinda', 'Caruaru', 'Petrolina', 'Paulista', 'Cabo de Santo Agostinho'],
    'CE': ['Fortaleza', 'Caucaia', 'Juazeiro do Norte', 'Maracanaú', 'Sobral', 'Crato', 'Itapipoca'],
    'PA': ['Belém', 'Ananindeua', 'Santarém', 'Marabá', 'Parauapebas', 'Castanhal', 'Abaetetuba'],
    'SC': ['Florianópolis', 'Joinville', 'Blumenau', 'São José', 'Chapecó', 'Criciúma', 'Itajaí'],
    'GO': ['Goiânia', 'Aparecida de Goiânia', 'Anápolis', 'Rio Verde', 'Luziânia', 'Águas Lindas de Goiás', 'Valparaíso de Goiás'],
    'MA': ['São Luís', 'Imperatriz', 'São José de Ribamar', 'Timon', 'Caxias', 'Codó', 'Paço do Lumiar'],
    'PB': ['João Pessoa', 'Campina Grande', 'Santa Rita', 'Patos', 'Bayeux', 'Sousa', 'Cabedelo'],
    'ES': ['Vitória', 'Vila Velha', 'Serra', 'Cariacica', 'Cachoeiro de Itapemirim', 'Linhares', 'Colatina'],
    'AM': ['Manaus', 'Parintins', 'Itacoatiara', 'Manacapuru', 'Coari', 'Tefé', 'Tabatinga'],
    'RN': ['Natal', 'Mossoró', 'Parnamirim', 'São Gonçalo do Amarante', 'Macaíba', 'Ceará-Mirim', 'Caicó'],
    'PI': ['Teresina', 'Parnaíba', 'Picos', 'Piripiri', 'Floriano', 'Campo Maior', 'Barras'],
    'AL': ['Maceió', 'Arapiraca', 'Rio Largo', 'Palmeira dos Índios', 'União dos Palmares', 'Penedo', 'São Miguel dos Campos'],
    'MT': ['Cuiabá', 'Várzea Grande', 'Rondonópolis', 'Sinop', 'Tangará da Serra', 'Cáceres', 'Sorriso'],
    'MS': ['Campo Grande', 'Dourados', 'Três Lagoas', 'Corumbá', 'Ponta Porã', 'Naviraí', 'Nova Andradina'],
    'DF': ['Brasília', 'Taguatinga', 'Ceilândia', 'Samambaia', 'Planaltina', 'Águas Claras', 'Gama'],
    'SE': ['Aracaju', 'Nossa Senhora do Socorro', 'Lagarto', 'Itabaiana', 'São Cristóvão', 'Estância', 'Tobias Barreto'],
    'RO': ['Porto Velho', 'Ji-Paraná', 'Ariquemes', 'Vilhena', 'Cacoal', 'Rolim de Moura', 'Guajará-Mirim'],
    'TO': ['Palmas', 'Araguaína', 'Gurupi', 'Porto Nacional', 'Paraíso do Tocantins', 'Colinas do Tocantins', 'Guaraí'],
    'AC': ['Rio Branco', 'Cruzeiro do Sul', 'Sena Madureira', 'Tarauacá', 'Feijó', 'Brasileia', 'Senador Guiomard'],
    'AP': ['Macapá', 'Santana', 'Laranjal do Jari', 'Oiapoque', 'Porto Grande', 'Mazagão', 'Tartarugalzinho'],
    'RR': ['Boa Vista', 'Rorainópolis', 'Caracaraí', 'Alto Alegre', 'Mucajaí', 'Cantá', 'Pacaraima'],
}

# Brazilian IP ranges by major ISPs
BRAZILIAN_IP_PREFIXES = [
    '177.', '187.', '189.', '191.', '200.', '201.',  # Common
    '179.', '186.', '188.', '190.', '170.',          # Also common
    '138.', '143.', '152.', '168.',                  # Corporate/ISP
]


def get_state_info(state_code: str) -> dict:
    """Get state information by code."""
    return ESTADOS_BR.get(state_code, {'name': 'Unknown', 'lat': -15.78, 'lon': -47.93, 'weight': 1})


def get_state_coordinates(state_code: str) -> tuple:
    """Get approximate center coordinates for a state."""
    info = ESTADOS_BR.get(state_code, {'lat': -15.78, 'lon': -47.93})
    return info['lat'], info['lon']


def get_cities_for_state(state_code: str) -> list:
    """Get list of major cities for a given state."""
    return CIDADES_POR_ESTADO.get(state_code, ['City'])


def get_state_name(state_code: str) -> str:
    """Get full state name by code."""
    return ESTADOS_BR.get(state_code, {}).get('name', 'Unknown')
