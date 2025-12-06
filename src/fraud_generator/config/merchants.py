"""
Configuration module for MCC codes and merchant data.
"""

# MCC codes with categories, risk levels and typical value ranges
MCC_CODES = {
    # Food (very common)
    '5411': {'category': 'Supermarkets', 'risk': 'low', 'min_value': 15, 'max_value': 800, 'weight': 20},
    '5812': {'category': 'Restaurants', 'risk': 'low', 'min_value': 20, 'max_value': 300, 'weight': 15},
    '5814': {'category': 'Fast Food', 'risk': 'low', 'min_value': 15, 'max_value': 100, 'weight': 12},
    '5499': {'category': 'Convenience/Grocery', 'risk': 'low', 'min_value': 5, 'max_value': 150, 'weight': 8},
    # Fuel and transportation
    '5541': {'category': 'Gas Stations', 'risk': 'low', 'min_value': 50, 'max_value': 500, 'weight': 10},
    '4121': {'category': 'Uber/99/Taxi', 'risk': 'low', 'min_value': 8, 'max_value': 150, 'weight': 8},
    '4131': {'category': 'Public Transit', 'risk': 'low', 'min_value': 4, 'max_value': 20, 'weight': 5},
    # Health
    '5912': {'category': 'Pharmacies', 'risk': 'low', 'min_value': 10, 'max_value': 500, 'weight': 6},
    '8011': {'category': 'Doctors/Clinics', 'risk': 'low', 'min_value': 100, 'max_value': 1500, 'weight': 2},
    # Retail
    '5311': {'category': 'Department Stores', 'risk': 'medium', 'min_value': 30, 'max_value': 2000, 'weight': 4},
    '5651': {'category': 'Clothing', 'risk': 'medium', 'min_value': 50, 'max_value': 1000, 'weight': 4},
    '5732': {'category': 'Electronics', 'risk': 'high', 'min_value': 100, 'max_value': 8000, 'weight': 2},
    '5944': {'category': 'Jewelry', 'risk': 'high', 'min_value': 200, 'max_value': 15000, 'weight': 1},
    # Services
    '4900': {'category': 'Utilities (Water/Power/Gas)', 'risk': 'low', 'min_value': 50, 'max_value': 800, 'weight': 5},
    '4814': {'category': 'Telecommunications', 'risk': 'low', 'min_value': 50, 'max_value': 300, 'weight': 4},
    '5977': {'category': 'Cosmetics/Perfumery', 'risk': 'medium', 'min_value': 30, 'max_value': 500, 'weight': 2},
    # High risk
    '7995': {'category': 'Gambling/Games', 'risk': 'high', 'min_value': 20, 'max_value': 5000, 'weight': 1},
    '6011': {'category': 'Cash/ATM', 'risk': 'medium', 'min_value': 20, 'max_value': 3000, 'weight': 3},
    # Travel
    '7011': {'category': 'Hotels', 'risk': 'medium', 'min_value': 150, 'max_value': 2000, 'weight': 1},
    '4511': {'category': 'Airlines', 'risk': 'medium', 'min_value': 200, 'max_value': 5000, 'weight': 1},
    # Streaming/Digital
    '5815': {'category': 'Digital Services', 'risk': 'low', 'min_value': 10, 'max_value': 100, 'weight': 3},
    # New categories
    '8299': {'category': 'Education/Courses', 'risk': 'low', 'min_value': 50, 'max_value': 3000, 'weight': 3},
    '5995': {'category': 'Pet Shop', 'risk': 'low', 'min_value': 20, 'max_value': 800, 'weight': 3},
    '7941': {'category': 'Gyms/Fitness', 'risk': 'low', 'min_value': 50, 'max_value': 300, 'weight': 4},
    '5812_delivery': {'category': 'Delivery/Food Apps', 'risk': 'low', 'min_value': 15, 'max_value': 200, 'weight': 8},
}

MCC_LIST = list(MCC_CODES.keys())
MCC_WEIGHTS = [MCC_CODES[mcc]['weight'] for mcc in MCC_LIST]

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
        'category': 'Other',
        'risk': 'medium',
        'min_value': 10,
        'max_value': 1000,
        'weight': 1
    })


def get_merchants_for_mcc(mcc_code: str) -> list:
    """Get list of merchants for a given MCC code."""
    return MERCHANTS_BY_MCC.get(mcc_code, ['Local Merchant'])


def get_risk_level(mcc_code: str) -> str:
    """Get risk level for a given MCC code."""
    return MCC_CODES.get(mcc_code, {}).get('risk', 'medium')
