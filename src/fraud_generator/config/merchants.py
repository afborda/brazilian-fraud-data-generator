"""
Configuration module for MCC codes and merchant data.
"""

# MCC codes with categories, risk levels and typical value ranges
MCC_CODES = {
    # Alimentação (muito comum)
    '5411': {'categoria': 'Supermercados', 'risco': 'low', 'valor_min': 15, 'valor_max': 800, 'peso': 20},
    '5812': {'categoria': 'Restaurantes', 'risco': 'low', 'valor_min': 20, 'valor_max': 300, 'peso': 15},
    '5814': {'categoria': 'Fast Food', 'risco': 'low', 'valor_min': 15, 'valor_max': 100, 'peso': 12},
    '5499': {'categoria': 'Conveniência/Mercado', 'risco': 'low', 'valor_min': 5, 'valor_max': 150, 'peso': 8},
    # Combustível e transporte
    '5541': {'categoria': 'Postos de Combustível', 'risco': 'low', 'valor_min': 50, 'valor_max': 500, 'peso': 10},
    '4121': {'categoria': 'Uber/99/Táxi', 'risco': 'low', 'valor_min': 8, 'valor_max': 150, 'peso': 8},
    '4131': {'categoria': 'Transporte Público', 'risco': 'low', 'valor_min': 4, 'valor_max': 20, 'peso': 5},
    # Saúde
    '5912': {'categoria': 'Farmácias', 'risco': 'low', 'valor_min': 10, 'valor_max': 500, 'peso': 6},
    '8011': {'categoria': 'Médicos/Clínicas', 'risco': 'low', 'valor_min': 100, 'valor_max': 1500, 'peso': 2},
    # Varejo
    '5311': {'categoria': 'Lojas de Departamento', 'risco': 'medium', 'valor_min': 30, 'valor_max': 2000, 'peso': 4},
    '5651': {'categoria': 'Vestuário', 'risco': 'medium', 'valor_min': 50, 'valor_max': 1000, 'peso': 4},
    '5732': {'categoria': 'Eletrônicos', 'risco': 'high', 'valor_min': 100, 'valor_max': 8000, 'peso': 2},
    '5944': {'categoria': 'Joalherias', 'risco': 'high', 'valor_min': 200, 'valor_max': 15000, 'peso': 1},
    # Serviços
    '4900': {'categoria': 'Utilidades (Água/Luz/Gás)', 'risco': 'low', 'valor_min': 50, 'valor_max': 800, 'peso': 5},
    '4814': {'categoria': 'Telecomunicações', 'risco': 'low', 'valor_min': 50, 'valor_max': 300, 'peso': 4},
    '5977': {'categoria': 'Cosméticos/Perfumaria', 'risco': 'medium', 'valor_min': 30, 'valor_max': 500, 'peso': 2},
    # Alto risco
    '7995': {'categoria': 'Apostas/Jogos', 'risco': 'high', 'valor_min': 20, 'valor_max': 5000, 'peso': 1},
    '6011': {'categoria': 'Saque/ATM', 'risco': 'medium', 'valor_min': 20, 'valor_max': 3000, 'peso': 3},
    # Viagem
    '7011': {'categoria': 'Hotéis', 'risco': 'medium', 'valor_min': 150, 'valor_max': 2000, 'peso': 1},
    '4511': {'categoria': 'Companhias Aéreas', 'risco': 'medium', 'valor_min': 200, 'valor_max': 5000, 'peso': 1},
    # Streaming/Digital
    '5815': {'categoria': 'Serviços Digitais', 'risco': 'low', 'valor_min': 10, 'valor_max': 100, 'peso': 3},
    # Novas categorias
    '8299': {'categoria': 'Educação/Cursos', 'risco': 'low', 'valor_min': 50, 'valor_max': 3000, 'peso': 3},
    '5995': {'categoria': 'Pet Shop', 'risco': 'low', 'valor_min': 20, 'valor_max': 800, 'peso': 3},
    '7941': {'categoria': 'Academias/Fitness', 'risco': 'low', 'valor_min': 50, 'valor_max': 300, 'peso': 4},
    '5812_delivery': {'categoria': 'Delivery/Apps de Comida', 'risco': 'low', 'valor_min': 15, 'valor_max': 200, 'peso': 8},
}

MCC_LIST = list(MCC_CODES.keys())
MCC_WEIGHTS = [MCC_CODES[mcc]['peso'] for mcc in MCC_LIST]

# Brazilian merchants with MCC mapping
MERCHANTS_BY_MCC = {
    '5411': [
        'Carrefour', 'Pão de Açúcar', 'Extra', 'Assaí', 'Atacadão', 'Big', 'Zaffari',
        'Savegnago', 'Dia', 'Guanabara', 'Sams Club', 'Costco', 'Makro', 'Mart Minas',
        'Supernosso'
    ],
    '5812': [
        'Outback', 'Coco Bambu', 'Madero', 'Applebees', 'Fogo de Chão', 'Paris 6',
        'Cosi', 'Lanchonete Local', 'Bar do Zé', 'Restaurante Familiar', 'iFood',
        'Rappi', 'Uber Eats', '99 Food', 'Zé Delivery'
    ],
    '5814': [
        'McDonalds', 'Burger King', 'Subway', 'Bobs', 'Habibs', 'Giraffas', 'Spoleto',
        'China in Box', 'Pizza Hut', 'KFC', 'Popeyes', 'Starbucks', 'Jeronimo',
        'Ragazzo', 'Vivenda do Camarão'
    ],
    '5499': [
        'Am Pm', 'BR Mania', 'Select', 'Oxxo', 'Minuto Pão de Açúcar',
        'Carrefour Express', 'Hortifruti', 'Quitanda Local', 'Mercearia', 'Empório',
        'Zona Sul', 'St Marche', 'Hirota', 'Natural da Terra'
    ],
    '5541': [
        'Shell', 'Ipiranga', 'BR Petrobras', 'Ale', 'Total', 'Repsol', 'Esso',
        'Cosan', 'Posto Cidade', 'Auto Posto', 'Vibra Energia', 'Raízen', 'YPF'
    ],
    '4121': [
        'Uber', '99', 'Cabify', 'InDriver', '99 Pop', 'Uber Black', 'Lady Driver',
        'Taxi Comum', 'Garupa', 'Buser', 'Fretadão', 'ClickBus', 'Blablacar'
    ],
    '4131': [
        'SPTrans', 'RioCard', 'BHTrans', 'Urbs Curitiba', 'MetroSP', 'MetroRio',
        'CPTM', 'ViaQuatro', 'CCR Metrô', 'Linha 4', 'Bilhete Único', 'TOP', 'BOM'
    ],
    '5912': [
        'Drogasil', 'Droga Raia', 'Pacheco', 'Pague Menos', 'Drogaria São Paulo',
        'Panvel', 'Venancio', 'Ultrafarma', 'Araújo', 'Nissei', 'Drogal', 'Onofre',
        'Drogarias Tamoio'
    ],
    '8011': [
        'Fleury', 'Dasa', 'Hermes Pardini', 'Einstein', 'Sírio-Libanês',
        'Clínica Popular', 'Dr. Consulta', 'Labi Exames', 'Lavoisier', 'CDB',
        'Hapvida', 'NotreDame', 'Unimed'
    ],
    '5311': [
        'Renner', 'C&A', 'Riachuelo', 'Magazine Luiza', 'Casas Bahia', 'Americanas',
        'Shoptime', 'Pernambucanas', 'Havan', 'Besni', 'Shopee', 'Shein',
        'AliExpress', 'Temu', 'Lojas Marisa'
    ],
    '5651': [
        'Zara', 'Forever 21', 'Marisa', 'Centauro', 'Netshoes', 'Dafiti', 'Arezzo',
        'Vivara', 'Farm', 'Animale', 'Track&Field', 'Osklen', 'Reserva', 'Richards',
        'Hering'
    ],
    '5732': [
        'Magazine Luiza', 'Casas Bahia', 'Fast Shop', 'Ponto Frio', 'Amazon',
        'Mercado Livre', 'Kabum', 'Terabyte', 'Girafa', 'Saraiva', 'Pichau',
        'Submarino', 'Extra.com', 'Zoom', 'Buscapé'
    ],
    '5944': [
        'Vivara', 'Pandora', 'Monte Carlo', 'HStern', 'Swarovski', 'Natan',
        'Tiffany', 'Cartier', 'Joalheria Local', 'Ourives', 'Dryzun', 'Sara Joias',
        'Rosana Chinche'
    ],
    '4900': [
        'Enel', 'Light', 'CPFL', 'Copel', 'Celesc', 'Sabesp', 'Cedae', 'Comgás',
        'Naturgy', 'Elektro', 'Equatorial', 'Energisa', 'Neoenergia', 'EDP', 'CEMIG'
    ],
    '4814': [
        'Vivo', 'Claro', 'Tim', 'Oi', 'NET', 'Sky', 'Nextel', 'Algar', 'Sercomtel',
        'Brisanet', 'Desktop', 'Sumicity', 'Unifique', 'Ligga', 'Americanet'
    ],
    '5977': [
        'O Boticário', 'Natura', 'Sephora', 'MAC', 'Quem Disse Berenice', 'Avon',
        'Eudora', 'LOccitane', 'The Body Shop', 'Época Cosméticos', 'Beleza na Web',
        'Dermage', 'Granado', 'Phebo'
    ],
    '7995': [
        'Bet365', 'Betano', 'Sportingbet', 'Betfair', 'Pixbet', 'Stake', 'Blaze',
        'Galera Bet', 'EstrelaBet', 'Novibet', 'Betsson', 'KTO', 'Betnacional',
        'Parimatch', 'F12 Bet'
    ],
    '6011': [
        'Banco 24 Horas', 'ATM Bradesco', 'ATM Itaú', 'ATM Santander', 'ATM Caixa',
        'ATM BB', 'Saque Nubank', 'Saque Inter', 'Saque PicPay', 'ATM Sicredi',
        'ATM C6', 'Saque Mercado Pago'
    ],
    '7011': [
        'Ibis', 'Mercure', 'Novotel', 'Quality', 'Comfort', 'Holiday Inn', 'Hilton',
        'Grand Hyatt', 'Blue Tree', 'Slaviero', 'Booking.com', 'Airbnb', 'Hoteis.com',
        'Decolar', 'Hurb'
    ],
    '4511': [
        'LATAM', 'GOL', 'Azul', 'Avianca', 'TAP', 'American Airlines', 'Emirates',
        'Copa Airlines', 'Air France', 'KLM', 'ITA Airways', 'Voepass',
        'Map Linhas Aéreas'
    ],
    '5815': [
        'Netflix', 'Spotify', 'Amazon Prime', 'Disney+', 'HBO Max', 'Globoplay',
        'Deezer', 'Apple Music', 'YouTube Premium', 'Paramount+', 'Star+',
        'Apple TV+', 'Crunchyroll', 'Telecine', 'Twitch'
    ],
    '8299': [
        'Alura', 'Rocketseat', 'Udemy', 'Coursera', 'Descomplica', 'Hotmart',
        'Domestika', 'Skillshare', 'LinkedIn Learning', 'Escola Conquer', 'FIAP',
        'Impacta', 'Digital House'
    ],
    '5995': [
        'Petz', 'Cobasi', 'Pet Love', 'DogHero', 'Petlove', 'PetShop Local',
        'Animale Pet', 'Mundo Animal', 'Casa dos Bichos', 'PetCenter', 'Zee.Dog',
        'Bicho Mania'
    ],
    '7941': [
        'Smart Fit', 'Bluefit', 'Bio Ritmo', 'Bodytech', 'Selfit', 'Academia Local',
        'Crossfit Box', 'Total Pass', 'Gympass', 'Queima Diária', 'Les Mills',
        'Velocity'
    ],
    '5812_delivery': [
        'iFood', 'Rappi', 'Uber Eats', '99 Food', 'Zé Delivery', 'James Delivery',
        'Delivery Center', 'Aiqfome', 'Get Ninjas', 'Delivery Much', 'Anota Aí'
    ],
}


def get_mcc_info(mcc_code: str) -> dict:
    """Get MCC information by code."""
    return MCC_CODES.get(mcc_code, {
        'categoria': 'Outros',
        'risco': 'medium',
        'valor_min': 10,
        'valor_max': 1000,
        'peso': 1
    })


def get_merchants_for_mcc(mcc_code: str) -> list:
    """Get list of merchants for a given MCC code."""
    return MERCHANTS_BY_MCC.get(mcc_code, ['Estabelecimento Local'])


def get_risk_level(mcc_code: str) -> str:
    """Get risk level for a given MCC code."""
    return MCC_CODES.get(mcc_code, {}).get('risco', 'medium')
