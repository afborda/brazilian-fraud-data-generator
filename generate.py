#!/usr/bin/env python3
"""
🇧🇷 BRAZILIAN FRAUD DATA GENERATOR v2.0
=======================================
Generate realistic Brazilian financial transaction data for testing,
development, and machine learning model training.

Features:
- 100% Brazilian data (CPF, banks, PIX, addresses)
- Configurable fraud patterns
- Parallel generation for high throughput
- JSON Lines output format
- Reproducible data with seed support

Usage:
    python3 generate.py --size 1GB --workers 4 --output ./output
    python3 generate.py --size 50GB --fraud-rate 0.01
    python3 generate.py --size 1GB --seed 42  # Reproducible
"""

__version__ = "2.1.0"

import json
import random
import hashlib
import uuid
import os
import sys
import time
import multiprocessing as mp
from datetime import datetime, timedelta
from faker import Faker
from functools import partial

# Configuration
TARGET_FILE_SIZE_MB = 128  # Each file will be ~128MB
BYTES_PER_TRANSACTION = 1050  # ~1KB per JSON transaction (measured)
TRANSACTIONS_PER_FILE = (TARGET_FILE_SIZE_MB * 1024 * 1024) // BYTES_PER_TRANSACTION

# Brazilian bank codes with names (Código COMPE/ISPB) - Top 25 banks by market share
BANKS = {
    '001': {'nome': 'Banco do Brasil', 'tipo': 'publico', 'peso': 15},
    '033': {'nome': 'Santander Brasil', 'tipo': 'privado', 'peso': 10},
    '104': {'nome': 'Caixa Econômica Federal', 'tipo': 'publico', 'peso': 14},
    '237': {'nome': 'Bradesco', 'tipo': 'privado', 'peso': 12},
    '341': {'nome': 'Itaú Unibanco', 'tipo': 'privado', 'peso': 15},
    '260': {'nome': 'Nubank', 'tipo': 'digital', 'peso': 10},
    '077': {'nome': 'Banco Inter', 'tipo': 'digital', 'peso': 5},
    '336': {'nome': 'C6 Bank', 'tipo': 'digital', 'peso': 4},
    '290': {'nome': 'PagBank', 'tipo': 'digital', 'peso': 3},
    '380': {'nome': 'PicPay', 'tipo': 'digital', 'peso': 2},
    '323': {'nome': 'Mercado Pago', 'tipo': 'digital', 'peso': 2},
    '403': {'nome': 'Cora', 'tipo': 'digital', 'peso': 1},
    '212': {'nome': 'Banco Original', 'tipo': 'digital', 'peso': 1},
    '756': {'nome': 'Sicoob', 'tipo': 'cooperativa', 'peso': 2},
    '748': {'nome': 'Sicredi', 'tipo': 'cooperativa', 'peso': 2},
    '422': {'nome': 'Safra', 'tipo': 'privado', 'peso': 1},
    '070': {'nome': 'BRB', 'tipo': 'publico', 'peso': 1},
    # Novos bancos adicionados
    '208': {'nome': 'BTG Pactual', 'tipo': 'privado', 'peso': 2},
    '655': {'nome': 'Neon', 'tipo': 'digital', 'peso': 2},
    '280': {'nome': 'Will Bank', 'tipo': 'digital', 'peso': 1},
    '237': {'nome': 'Next', 'tipo': 'digital', 'peso': 2},
    '623': {'nome': 'Banco Pan', 'tipo': 'privado', 'peso': 2},
    '121': {'nome': 'Agibank', 'tipo': 'digital', 'peso': 1},
    '707': {'nome': 'Daycoval', 'tipo': 'privado', 'peso': 1},
    '318': {'nome': 'BMG', 'tipo': 'privado', 'peso': 1},
}

BANK_CODES = list(BANKS.keys())
BANK_WEIGHTS = [BANKS[code]['peso'] for code in BANK_CODES]

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
    '5812': {'categoria': 'Delivery/Apps de Comida', 'risco': 'low', 'valor_min': 15, 'valor_max': 200, 'peso': 8},
}

MCC_LIST = list(MCC_CODES.keys())
MCC_WEIGHTS = [MCC_CODES[mcc]['peso'] for mcc in MCC_LIST]

# Brazilian merchants with MCC mapping
MERCHANTS_BY_MCC = {
    '5411': ['Carrefour', 'Pão de Açúcar', 'Extra', 'Assaí', 'Atacadão', 'Big', 'Zaffari', 'Savegnago', 'Dia', 'Guanabara', 'Sams Club', 'Costco', 'Makro', 'Mart Minas', 'Supernosso'],
    '5812': ['Outback', 'Coco Bambu', 'Madero', 'Applebees', 'Fogo de Chão', 'Paris 6', 'Cosi', 'Lanchonete Local', 'Bar do Zé', 'Restaurante Familiar', 'iFood', 'Rappi', 'Uber Eats', '99 Food', 'Zé Delivery'],
    '5814': ['McDonalds', 'Burger King', 'Subway', 'Bobs', 'Habibs', 'Giraffas', 'Spoleto', 'China in Box', 'Pizza Hut', 'KFC', 'Popeyes', 'Starbucks', 'Jeronimo', 'Ragazzo', 'Vivenda do Camarão'],
    '5499': ['Am Pm', 'BR Mania', 'Select', 'Oxxo', 'Minuto Pão de Açúcar', 'Carrefour Express', 'Hortifruti', 'Quitanda Local', 'Mercearia', 'Empório', 'Zona Sul', 'St Marche', 'Hirota', 'Natural da Terra'],
    '5541': ['Shell', 'Ipiranga', 'BR Petrobras', 'Ale', 'Total', 'Repsol', 'Esso', 'Cosan', 'Posto Cidade', 'Auto Posto', 'Vibra Energia', 'Raízen', 'YPF'],
    '4121': ['Uber', '99', 'Cabify', 'InDriver', '99 Pop', 'Uber Black', 'Lady Driver', 'Taxi Comum', 'Garupa', 'Buser', 'Fretadão', 'ClickBus', 'Blablacar'],
    '4131': ['SPTrans', 'RioCard', 'BHTrans', 'Urbs Curitiba', 'MetroSP', 'MetroRio', 'CPTM', 'ViaQuatro', 'CCR Metrô', 'Linha 4', 'Bilhete Único', 'TOP', 'BOM'],
    '5912': ['Drogasil', 'Droga Raia', 'Pacheco', 'Pague Menos', 'Drogaria São Paulo', 'Panvel', 'Venancio', 'Ultrafarma', 'Araújo', 'Nissei', 'Drogal', 'Onofre', 'Drogarias Tamoio'],
    '8011': ['Fleury', 'Dasa', 'Hermes Pardini', 'Einstein', 'Sírio-Libanês', 'Clínica Popular', 'Dr. Consulta', 'Labi Exames', 'Lavoisier', 'CDB', 'Hapvida', 'NotreDame', 'Unimed'],
    '5311': ['Renner', 'C&A', 'Riachuelo', 'Magazine Luiza', 'Casas Bahia', 'Americanas', 'Shoptime', 'Pernambucanas', 'Havan', 'Besni', 'Shopee', 'Shein', 'AliExpress', 'Temu', 'Lojas Marisa'],
    '5651': ['Zara', 'Forever 21', 'Marisa', 'Centauro', 'Netshoes', 'Dafiti', 'Arezzo', 'Vivara', 'Farm', 'Animale', 'Track&Field', 'Osklen', 'Reserva', 'Richards', 'Hering'],
    '5732': ['Magazine Luiza', 'Casas Bahia', 'Fast Shop', 'Ponto Frio', 'Amazon', 'Mercado Livre', 'Kabum', 'Terabyte', 'Girafa', 'Saraiva', 'Pichau', 'Submarino', 'Extra.com', 'Zoom', 'Buscapé'],
    '5944': ['Vivara', 'Pandora', 'Monte Carlo', 'HStern', 'Swarovski', 'Natan', 'Tiffany', 'Cartier', 'Joalheria Local', 'Ourives', 'Dryzun', 'Sara Joias', 'Rosana Chinche'],
    '4900': ['Enel', 'Light', 'CPFL', 'Copel', 'Celesc', 'Sabesp', 'Cedae', 'Comgás', 'Naturgy', 'Elektro', 'Equatorial', 'Energisa', 'Neoenergia', 'EDP', 'CEMIG'],
    '4814': ['Vivo', 'Claro', 'Tim', 'Oi', 'NET', 'Sky', 'Nextel', 'Algar', 'Sercomtel', 'Brisanet', 'Desktop', 'Sumicity', 'Unifique', 'Ligga', 'Americanet'],
    '5977': ['O Boticário', 'Natura', 'Sephora', 'MAC', 'Quem Disse Berenice', 'Avon', 'Eudora', 'LOccitane', 'The Body Shop', 'Época Cosméticos', 'Beleza na Web', 'Dermage', 'Granado', 'Phebo'],
    '7995': ['Bet365', 'Betano', 'Sportingbet', 'Betfair', 'Pixbet', 'Stake', 'Blaze', 'Galera Bet', 'EstrelaBet', 'Novibet', 'Betsson', 'KTO', 'Betnacional', 'Parimatch', 'F12 Bet'],
    '6011': ['Banco 24 Horas', 'ATM Bradesco', 'ATM Itaú', 'ATM Santander', 'ATM Caixa', 'ATM BB', 'Saque Nubank', 'Saque Inter', 'Saque PicPay', 'ATM Sicredi', 'ATM C6', 'Saque Mercado Pago'],
    '7011': ['Ibis', 'Mercure', 'Novotel', 'Quality', 'Comfort', 'Holiday Inn', 'Hilton', 'Grand Hyatt', 'Blue Tree', 'Slaviero', 'Booking.com', 'Airbnb', 'Hoteis.com', 'Decolar', 'Hurb'],
    '4511': ['LATAM', 'GOL', 'Azul', 'Avianca', 'TAP', 'American Airlines', 'Emirates', 'Copa Airlines', 'Air France', 'KLM', 'ITA Airways', 'Voepass', 'Map Linhas Aéreas'],
    '5815': ['Netflix', 'Spotify', 'Amazon Prime', 'Disney+', 'HBO Max', 'Globoplay', 'Deezer', 'Apple Music', 'YouTube Premium', 'Paramount+', 'Star+', 'Apple TV+', 'Crunchyroll', 'Telecine', 'Twitch'],
    # Novas categorias de merchants
    '8299': ['Alura', 'Rocketseat', 'Udemy', 'Coursera', 'Descomplica', 'Hotmart', 'Domestika', 'Skillshare', 'LinkedIn Learning', 'Escola Conquer', 'FIAP', 'Impacta', 'Digital House'],
    '5995': ['Petz', 'Cobasi', 'Pet Love', 'DogHero', 'Petlove', 'PetShop Local', 'Animale Pet', 'Mundo Animal', 'Casa dos Bichos', 'PetCenter', 'Zee.Dog', 'Bicho Mania'],
    '7941': ['Smart Fit', 'Bluefit', 'Bio Ritmo', 'Bodytech', 'Selfit', 'Academia Local', 'Crossfit Box', 'Total Pass', 'Gympass', 'Queima Diária', 'Les Mills', 'Velocity'],
}

# Transaction types (PIX weighted higher - realistic for Brazil 2024)
TRANSACTION_TYPES = {
    'PIX': 42,            # 42% - PIX dominates Brazil
    'CARTAO_CREDITO': 22, # 22% - Credit card
    'CARTAO_DEBITO': 13,  # 13% - Debit card
    'BOLETO': 7,          # 7%  - Bank slip
    'TED': 3,             # 3%  - Wire transfer
    'SAQUE': 3,           # 3%  - Cash withdrawal (decreasing)
    # Novos tipos de transação
    'DOC': 1,             # 1%  - DOC transfer (being phased out)
    'DEBITO_AUTOMATICO': 5, # 5% - Automatic debit (bills, subscriptions)
    'RECARGA_CELULAR': 4, # 4%  - Mobile phone top-up
}

TX_TYPES_LIST = list(TRANSACTION_TYPES.keys())
TX_TYPES_WEIGHTS = list(TRANSACTION_TYPES.values())

# Channels with realistic weights
CHANNELS = {
    'APP_MOBILE': 60,    # 60% - Mobile dominates
    'WEB_BANKING': 25,   # 25% - Desktop banking
    'ATM': 8,            # 8%  - ATM (decreasing)
    'AGENCIA': 5,        # 5%  - Branch (rare)
    'WHATSAPP_PAY': 2,   # 2%  - WhatsApp payments
}

CHANNELS_LIST = list(CHANNELS.keys())
CHANNELS_WEIGHTS = list(CHANNELS.values())

# Fraud types with realistic distribution
FRAUD_TYPES = {
    'ENGENHARIA_SOCIAL': 20,    # Social engineering - most common
    'CONTA_TOMADA': 15,         # Account takeover
    'CARTAO_CLONADO': 14,       # Cloned card
    'IDENTIDADE_FALSA': 10,     # Identity fraud
    'AUTOFRAUDE': 8,            # First-party fraud
    'FRAUDE_AMIGAVEL': 5,       # Friendly fraud
    'LAVAGEM_DINHEIRO': 4,      # Money laundering
    'TRIANGULACAO': 3,          # Triangulation fraud
    # Novos tipos de fraude
    'GOLPE_WHATSAPP': 8,        # WhatsApp scams (fake support, fake relatives)
    'PHISHING': 6,              # Fake emails/sites to steal credentials
    'SIM_SWAP': 3,              # SIM card swap fraud
    'BOLETO_FALSO': 2,          # Fake bank slips
    'QR_CODE_FALSO': 2,         # Fake PIX QR codes
}

FRAUD_TYPES_LIST = list(FRAUD_TYPES.keys())
FRAUD_TYPES_WEIGHTS = list(FRAUD_TYPES.values())

# PIX key types with realistic distribution
PIX_KEY_TYPES = {
    'CPF': 35,
    'TELEFONE': 30,
    'EMAIL': 20,
    'ALEATORIA': 10,
    'CNPJ': 5,
}

PIX_TYPES_LIST = list(PIX_KEY_TYPES.keys())
PIX_TYPES_WEIGHTS = list(PIX_KEY_TYPES.values())

# Card brands with market share in Brazil
CARD_BRANDS = {
    'VISA': 40,
    'MASTERCARD': 40,
    'ELO': 15,
    'HIPERCARD': 3,
    'AMEX': 2,
}

BRANDS_LIST = list(CARD_BRANDS.keys())
BRANDS_WEIGHTS = list(CARD_BRANDS.values())

# Brazilian states with coordinates (centro aproximado) and population weight
ESTADOS_BR = {
    'SP': {'lat': -23.55, 'lon': -46.64, 'peso': 22},
    'RJ': {'lat': -22.91, 'lon': -43.17, 'peso': 8},
    'MG': {'lat': -19.92, 'lon': -43.94, 'peso': 10},
    'BA': {'lat': -12.97, 'lon': -38.51, 'peso': 7},
    'RS': {'lat': -30.03, 'lon': -51.23, 'peso': 6},
    'PR': {'lat': -25.43, 'lon': -49.27, 'peso': 6},
    'PE': {'lat': -8.05, 'lon': -34.88, 'peso': 5},
    'CE': {'lat': -3.72, 'lon': -38.54, 'peso': 4},
    'PA': {'lat': -1.46, 'lon': -48.50, 'peso': 4},
    'SC': {'lat': -27.60, 'lon': -48.55, 'peso': 4},
    'GO': {'lat': -16.68, 'lon': -49.25, 'peso': 4},
    'MA': {'lat': -2.53, 'lon': -44.27, 'peso': 3},
    'PB': {'lat': -7.12, 'lon': -34.86, 'peso': 2},
    'ES': {'lat': -20.32, 'lon': -40.34, 'peso': 2},
    'AM': {'lat': -3.10, 'lon': -60.02, 'peso': 2},
    'RN': {'lat': -5.79, 'lon': -35.21, 'peso': 2},
    'PI': {'lat': -5.09, 'lon': -42.80, 'peso': 2},
    'AL': {'lat': -9.67, 'lon': -35.74, 'peso': 2},
    'MT': {'lat': -15.60, 'lon': -56.10, 'peso': 2},
    'MS': {'lat': -20.44, 'lon': -54.65, 'peso': 1},
    'DF': {'lat': -15.78, 'lon': -47.93, 'peso': 2},
    'SE': {'lat': -10.91, 'lon': -37.07, 'peso': 1},
    'RO': {'lat': -8.76, 'lon': -63.90, 'peso': 1},
    'TO': {'lat': -10.18, 'lon': -48.33, 'peso': 1},
    'AC': {'lat': -9.97, 'lon': -67.81, 'peso': 0.5},
    'AP': {'lat': 0.03, 'lon': -51.05, 'peso': 0.5},
    'RR': {'lat': 2.82, 'lon': -60.67, 'peso': 0.5},
}

ESTADOS_LIST = list(ESTADOS_BR.keys())
ESTADOS_WEIGHTS = [ESTADOS_BR[e]['peso'] for e in ESTADOS_LIST]

# Device types with realistic distribution
DEVICE_TYPES = {
    'SMARTPHONE_ANDROID': 55,
    'SMARTPHONE_IOS': 25,
    'DESKTOP_WINDOWS': 12,
    'DESKTOP_MAC': 4,
    'TABLET_ANDROID': 2,
    'TABLET_IOS': 2,
}

DEVICE_TYPES_LIST = list(DEVICE_TYPES.keys())
DEVICE_TYPES_WEIGHTS = list(DEVICE_TYPES.values())

# Device manufacturers
DEVICE_MANUFACTURERS = {
    'SMARTPHONE_ANDROID': ['Samsung', 'Motorola', 'Xiaomi', 'LG', 'ASUS', 'Realme', 'POCO', 'OnePlus', 'TCL', 'Nokia', 'Huawei', 'Honor', 'Google', 'Nothing', 'Sony'],
    'SMARTPHONE_IOS': ['Apple'],
    'DESKTOP_WINDOWS': ['Dell', 'HP', 'Lenovo', 'ASUS', 'Acer', 'Positivo', 'Samsung', 'MSI', 'Vaio', 'Avell', 'Multilaser'],
    'DESKTOP_MAC': ['Apple'],
    'TABLET_ANDROID': ['Samsung', 'Xiaomi', 'Lenovo', 'Multilaser', 'TCL', 'Nokia', 'Huawei', 'Positivo'],
    'TABLET_IOS': ['Apple'],
}


def generate_ip_brazil():
    """Generate Brazilian IP address from common ISP ranges"""
    # Brazilian IP ranges by major ISPs
    prefixes = [
        '177.', '187.', '189.', '191.', '200.', '201.',  # Common
        '179.', '186.', '188.', '190.', '170.',          # Also common
        '138.', '143.', '152.', '168.',                  # Corporate/ISP
    ]
    prefix = random.choice(prefixes)
    return prefix + '.'.join(str(random.randint(0, 255)) for _ in range(3))


def generate_realistic_timestamp(start_date, end_date):
    """Generate timestamp with realistic patterns (more activity during business hours)"""
    # Pick a random day
    days_between = (end_date - start_date).days
    random_day = start_date + timedelta(days=random.randint(0, days_between))
    
    # Hour distribution (weighted towards business/evening hours)
    hour_weights = {
        0: 2, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2,           # Late night (low)
        6: 4, 7: 6, 8: 10, 9: 12, 10: 14, 11: 14,     # Morning (rising)
        12: 15, 13: 14, 14: 13, 15: 12, 16: 12, 17: 13,  # Afternoon (peak)
        18: 14, 19: 15, 20: 14, 21: 12, 22: 8, 23: 4  # Evening (declining)
    }
    hours = list(hour_weights.keys())
    weights = list(hour_weights.values())
    hour = random.choices(hours, weights=weights)[0]
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    microsecond = random.randint(0, 999999)
    
    return random_day.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)


def generate_transaction(tx_id, customer_id, device_id, timestamp, is_fraud, fraud_type, customer_state=None):
    """Generate a single transaction with realistic Brazilian patterns"""
    
    # Select MCC based on weights
    mcc_code = random.choices(MCC_LIST, weights=MCC_WEIGHTS)[0]
    mcc_info = MCC_CODES[mcc_code]
    
    # Transaction type
    tx_type = random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)[0]
    
    # Value based on MCC category and fraud status
    if is_fraud:
        # Fraudsters tend to make higher value transactions
        if fraud_type in ['LAVAGEM_DINHEIRO', 'TRIANGULACAO']:
            valor = round(random.uniform(5000, 50000), 2)
        elif fraud_type in ['CARTAO_CLONADO', 'CONTA_TOMADA']:
            valor = round(random.uniform(500, 10000), 2)
        else:
            valor = round(random.uniform(200, 5000), 2)
    else:
        # Normal distribution based on MCC typical values
        valor_min = mcc_info['valor_min']
        valor_max = mcc_info['valor_max']
        # Use log-normal for more realistic distribution (more small, fewer large)
        mean = (valor_min + valor_max) / 3  # Skew towards lower values
        valor = round(min(max(random.gauss(mean, mean/2), valor_min), valor_max), 2)
    
    # Get appropriate merchant for MCC
    merchants_for_mcc = MERCHANTS_BY_MCC.get(mcc_code, ['Estabelecimento Local'])
    merchant_name = random.choice(merchants_for_mcc)
    
    # Geolocation based on customer state or random
    if customer_state and customer_state in ESTADOS_BR:
        estado_info = ESTADOS_BR[customer_state]
        base_lat, base_lon = estado_info['lat'], estado_info['lon']
        # Add small random offset (within ~50km)
        lat = round(base_lat + random.uniform(-0.5, 0.5), 6)
        lon = round(base_lon + random.uniform(-0.5, 0.5), 6)
    else:
        # Random state weighted by population
        estado = random.choices(ESTADOS_LIST, weights=ESTADOS_WEIGHTS)[0]
        estado_info = ESTADOS_BR[estado]
        lat = round(estado_info['lat'] + random.uniform(-1, 1), 6)
        lon = round(estado_info['lon'] + random.uniform(-1, 1), 6)
    
    # Channel selection
    canal = random.choices(CHANNELS_LIST, weights=CHANNELS_WEIGHTS)[0]
    
    # Bank selection for destination
    banco_destino = random.choices(BANK_CODES, weights=BANK_WEIGHTS)[0]
    
    tx = {
        'transaction_id': f'TXN_{tx_id:015d}',
        'customer_id': customer_id,
        'session_id': f'SESS_{tx_id:012d}',
        'device_id': device_id,
        'timestamp': timestamp.isoformat(),
        'tipo': tx_type,
        'valor': valor,
        'moeda': 'BRL',
        'canal': canal,
        'ip_address': generate_ip_brazil(),
        'geolocalizacao_lat': lat,
        'geolocalizacao_lon': lon,
        'merchant_id': f'MERCH_{random.randint(1, 100000):06d}',
        'merchant_name': merchant_name,
        'merchant_category': mcc_info['categoria'],
        'mcc_code': mcc_code,
        'mcc_risk_level': mcc_info['risco'],
    }
    
    # Type-specific fields
    if tx_type in ['CARTAO_CREDITO', 'CARTAO_DEBITO']:
        bandeira = random.choices(BRANDS_LIST, weights=BRANDS_WEIGHTS)[0]
        tx.update({
            'numero_cartao_hash': hashlib.sha256(str(random.random()).encode()).hexdigest()[:16],
            'bandeira': bandeira,
            'tipo_cartao': 'CREDITO' if tx_type == 'CARTAO_CREDITO' else 'DEBITO',
            'parcelas': random.choices([1, 2, 3, 4, 5, 6, 10, 12], weights=[50, 10, 10, 5, 5, 10, 5, 5])[0] if tx_type == 'CARTAO_CREDITO' else 1,
            'entrada_cartao': random.choices(['CHIP', 'CONTACTLESS', 'DIGITADO', 'MAGNETICO'], weights=[40, 35, 20, 5])[0],
            'cvv_validado': random.choices([True, False], weights=[95, 5])[0],
            'autenticacao_3ds': random.choices([True, False], weights=[70, 30])[0],
            'chave_pix_tipo': None,
            'chave_pix_destino': None,
            'banco_destino': None,
        })
    elif tx_type == 'PIX':
        pix_tipo = random.choices(PIX_TYPES_LIST, weights=PIX_TYPES_WEIGHTS)[0]
        tx.update({
            'numero_cartao_hash': None,
            'bandeira': None,
            'tipo_cartao': None,
            'parcelas': None,
            'entrada_cartao': None,
            'cvv_validado': None,
            'autenticacao_3ds': None,
            'chave_pix_tipo': pix_tipo,
            'chave_pix_destino': hashlib.sha256(str(random.random()).encode()).hexdigest()[:32],
            'banco_destino': banco_destino,
        })
    else:
        tx.update({
            'numero_cartao_hash': None,
            'bandeira': None,
            'tipo_cartao': None,
            'parcelas': None,
            'entrada_cartao': None,
            'cvv_validado': None,
            'autenticacao_3ds': None,
            'chave_pix_tipo': None,
            'chave_pix_destino': None,
            'banco_destino': banco_destino if tx_type in ['TED', 'BOLETO'] else None,
        })
    
    # Risk indicators
    hour = timestamp.hour
    horario_incomum = hour < 6 or hour > 23  # Unusual: before 6am or after 11pm
    
    # Fraud indicators affect transaction patterns
    if is_fraud:
        status = random.choices(
            ['APROVADA', 'RECUSADA', 'PENDENTE', 'BLOQUEADA'],
            weights=[60, 25, 10, 5]
        )[0]
        fraud_score = round(random.uniform(65, 100), 2)
        transacoes_24h = random.randint(5, 50)  # Fraudsters do many transactions
        valor_acumulado = round(random.uniform(2000, 50000), 2)
    else:
        status = random.choices(
            ['APROVADA', 'RECUSADA', 'PENDENTE'],
            weights=[96, 3, 1]
        )[0]
        fraud_score = round(random.uniform(0, 35), 2)
        transacoes_24h = random.randint(1, 15)
        valor_acumulado = round(random.uniform(50, 5000), 2)
    
    tx.update({
        'distancia_ultima_transacao_km': round(random.uniform(0, 100), 2) if random.random() > 0.5 else None,
        'tempo_desde_ultima_transacao_min': random.randint(1, 1440) if random.random() > 0.3 else None,
        'transacoes_ultimas_24h': transacoes_24h,
        'valor_acumulado_24h': valor_acumulado,
        'horario_incomum': horario_incomum,
        'novo_beneficiario': random.random() < (0.7 if is_fraud else 0.15),  # Frauds often go to new beneficiaries
        'status': status,
        'motivo_recusa': random.choice(['SALDO_INSUFICIENTE', 'SUSPEITA_FRAUDE', 'LIMITE_EXCEDIDO', 'CARTAO_BLOQUEADO', 'ERRO_CVV']) if status == 'RECUSADA' else None,
        'fraud_score': fraud_score,
        'is_fraud': is_fraud,
        'fraud_type': fraud_type,
    })
    
    return tx


def generate_device(device_id, customer_id, fake):
    """Generate a device with realistic data"""
    device_type = random.choices(DEVICE_TYPES_LIST, weights=DEVICE_TYPES_WEIGHTS)[0]
    manufacturers = DEVICE_MANUFACTURERS[device_type]
    manufacturer = random.choice(manufacturers)
    
    # Model names by manufacturer
    models = {
        'Samsung': ['Galaxy S24', 'Galaxy S24 Ultra', 'Galaxy S23', 'Galaxy A55', 'Galaxy A35', 'Galaxy M55', 'Galaxy Z Fold 5', 'Galaxy Z Flip 5', 'Galaxy Tab S9'],
        'Motorola': ['Edge 50', 'Edge 40', 'G84', 'G54', 'Razr 40', 'ThinkPhone', 'Moto G Stylus'],
        'Xiaomi': ['Xiaomi 14', 'Redmi Note 13', 'Redmi 13C', 'POCO X6', 'Mi 14', 'Redmi Note 12', 'Xiaomi Pad 6'],
        'Apple': ['iPhone 16', 'iPhone 16 Pro', 'iPhone 15', 'iPhone 15 Pro', 'iPhone SE', 'iPad Pro M4', 'iPad Air M2', 'MacBook Pro M3', 'MacBook Air M3', 'iMac M3'],
        'LG': ['K62', 'K52', 'K42', 'Velvet'],
        'Dell': ['Inspiron 16', 'XPS 15', 'XPS 13', 'Latitude 7440', 'Vostro 3520', 'Alienware m16'],
        'HP': ['Pavilion 15', 'Spectre x360', 'EliteBook 840', 'ProBook 450', 'Omen 16', 'Victus 15'],
        'Lenovo': ['IdeaPad Slim 5', 'ThinkPad X1 Carbon', 'Legion Pro 5', 'Yoga 9i', 'ThinkBook 14'],
        'ASUS': ['ZenBook 14', 'VivoBook 15', 'ROG Strix', 'TUF Gaming F15', 'ProArt Studiobook'],
        'Acer': ['Aspire 5', 'Swift Go 14', 'Nitro 5', 'Predator Helios'],
        'Positivo': ['Motion Q464C', 'Vision C14', 'Twist Tab'],
        'Multilaser': ['M10 4G', 'M8 4G', 'Ultra U10'],
        'Realme': ['12 Pro+', 'C67', 'GT5 Pro', 'Narzo 70'],
        'POCO': ['X6 Pro', 'M6 Pro', 'F6', 'C65'],
        'OnePlus': ['12', 'Nord 4', 'Open', '12R'],
        # Novos fabricantes
        'TCL': ['40 NxtPaper', '50 SE', 'Tab 10 Gen 2', '30 5G'],
        'Nokia': ['G42 5G', 'C32', 'XR21', 'T21 Tablet'],
        'Huawei': ['P60 Pro', 'Mate 60', 'Nova 12', 'MatePad Pro'],
        'Honor': ['Magic 6 Pro', '90', 'X9b', 'Pad 9'],
        'Google': ['Pixel 8', 'Pixel 8 Pro', 'Pixel 7a', 'Pixel Tablet'],
        'Nothing': ['Phone 2', 'Phone 2a', 'Phone 1'],
        'Sony': ['Xperia 1 V', 'Xperia 5 V', 'Xperia 10 V'],
        'MSI': ['Stealth 16', 'Raider GE78', 'Katana 15', 'Creator Z17'],
        'Vaio': ['FE 14', 'FE 15', 'SX14'],
        'Avell': ['A70', 'C65', 'Storm Two'],
    }
    
    model = random.choice(models.get(manufacturer, ['Generic']))
    
    # OS based on device type
    if 'ANDROID' in device_type:
        os_name = f"Android {random.choice(['11', '12', '13', '14'])}"
    elif 'IOS' in device_type or 'TABLET_IOS' in device_type:
        os_name = f"iOS {random.choice(['16', '17', '17.1', '17.2'])}"
    elif 'WINDOWS' in device_type:
        os_name = f"Windows {random.choice(['10', '11'])}"
    else:
        os_name = f"macOS {random.choice(['Sonoma', 'Ventura', 'Monterey'])}"
    
    return {
        'device_id': device_id,
        'customer_id': customer_id,
        'tipo': device_type.split('_')[0],
        'fabricante': manufacturer,
        'modelo': model,
        'sistema_operacional': os_name,
        'fingerprint': hashlib.sha256(f"{device_id}{random.random()}".encode()).hexdigest()[:32],
        'primeiro_uso': fake.date_between(start_date='-2y', end_date='today').isoformat(),
        'is_trusted': random.choices([True, False], weights=[85, 15])[0],
        'is_rooted_jailbroken': random.choices([False, True], weights=[97, 3])[0],
    }


def generate_customer(customer_id, fake):
    """Generate a single customer with realistic Brazilian data"""
    created_date = fake.date_time_between(start_date='-5y', end_date='-1m')
    
    # State selection weighted by population
    estado = random.choices(ESTADOS_LIST, weights=ESTADOS_WEIGHTS)[0]
    
    # Risk profile based on account age
    account_age_days = (datetime.now() - created_date).days
    if account_age_days < 30:
        risk_level = random.choices(['ALTO', 'MEDIO', 'BAIXO'], weights=[30, 50, 20])[0]
    elif account_age_days < 180:
        risk_level = random.choices(['ALTO', 'MEDIO', 'BAIXO'], weights=[10, 40, 50])[0]
    else:
        risk_level = random.choices(['ALTO', 'MEDIO', 'BAIXO'], weights=[5, 25, 70])[0]
    
    # Income distribution (realistic for Brazil)
    renda = round(random.choices(
        [random.uniform(1500, 3000), random.uniform(3000, 7000), random.uniform(7000, 15000), random.uniform(15000, 50000)],
        weights=[40, 35, 18, 7]
    )[0], 2)
    
    # Credit score correlates with income and account age
    base_score = 300 + (account_age_days / 30) * 5  # Older accounts have better scores
    if renda > 10000:
        base_score += 100
    elif renda > 5000:
        base_score += 50
    score = min(900, max(300, int(base_score + random.gauss(100, 50))))
    
    # Bank selection weighted
    banco = random.choices(BANK_CODES, weights=BANK_WEIGHTS)[0]
    
    return {
        'customer_id': customer_id,
        'nome': fake.name(),
        'cpf': fake.cpf(),
        'email': fake.email(),
        'telefone': fake.phone_number(),
        'data_nascimento': fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
        'endereco': {
            'logradouro': fake.street_address(),
            'bairro': fake.bairro(),
            'cidade': fake.city(),
            'estado': estado,
            'cep': fake.postcode(),
        },
        'renda_mensal': renda,
        'profissao': fake.job(),
        'conta_criada_em': created_date.isoformat(),
        'tipo_conta': random.choices(['CORRENTE', 'POUPANCA', 'DIGITAL'], weights=[40, 20, 40])[0],
        'status_conta': random.choices(['ATIVA', 'BLOQUEADA', 'INATIVA'], weights=[95, 3, 2])[0],
        'limite_credito': round(renda * random.uniform(2, 8), 2),
        'score_credito': score,
        'nivel_risco': risk_level,
        'banco_codigo': banco,
        'banco_nome': BANKS[banco]['nome'],
        'agencia': f'{random.randint(1, 9999):04d}',
        'numero_conta': f'{random.randint(10000, 999999)}-{random.randint(0, 9)}',
    }


def worker_generate_batch(args):
    """Worker that generates a 128MB file"""
    batch_id, num_transactions, customer_data, device_ids, start_date, end_date, fraud_rate, output_dir, seed = args
    
    # Deterministic seed per worker for reproducibility
    if seed is not None:
        worker_seed = seed + batch_id * 12345
    else:
        worker_seed = batch_id * 12345 + int(time.time() * 1000) % 10000
    
    random.seed(worker_seed)
    
    output_path = os.path.join(output_dir, f'transactions_{batch_id:05d}.json')
    
    start_time = time.time()
    tx_id_start = batch_id * num_transactions
    
    # Extract customer IDs and states
    customer_ids = [c['customer_id'] for c in customer_data]
    customer_states = {c['customer_id']: c.get('estado') for c in customer_data}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(num_transactions):
            tx_id = tx_id_start + i
            customer_id = random.choice(customer_ids)
            customer_state = customer_states.get(customer_id)
            device_id = random.choice(device_ids) if device_ids else None
            timestamp = generate_realistic_timestamp(start_date, end_date)
            is_fraud = random.random() < fraud_rate
            fraud_type = random.choices(FRAUD_TYPES_LIST, weights=FRAUD_TYPES_WEIGHTS)[0] if is_fraud else None
            
            tx = generate_transaction(tx_id, customer_id, device_id, timestamp, is_fraud, fraud_type, customer_state)
            f.write(json.dumps(tx, ensure_ascii=False) + '\n')
    
    elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    
    return batch_id, num_transactions, file_size_mb, elapsed


def generate_base_data(output_dir, num_customers=100000, num_devices=None, quiet=False, seed=None):
    """Generate base customer and device data"""
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)
    
    fake = Faker('pt_BR')
    
    # Default devices = 3x customers
    if num_devices is None:
        num_devices = num_customers * 3
    
    # Generate customers
    customers_path = os.path.join(output_dir, 'customers.json')
    if not quiet:
        print(f"\n👤 Generating {num_customers:,} customers...")
    
    customer_data = []
    with open(customers_path, 'w', encoding='utf-8') as f:
        for i in range(1, num_customers + 1):
            customer_id = f'CUST_{i:08d}'
            customer = generate_customer(customer_id, fake)
            customer_data.append({
                'customer_id': customer_id,
                'estado': customer['endereco']['estado']
            })
            f.write(json.dumps(customer, ensure_ascii=False) + '\n')
            
            if not quiet and i % 10000 == 0:
                print(f"   ✓ {i:,} / {num_customers:,}", end='\r')
    
    if not quiet:
        print(f"   ✓ {num_customers:,} customers saved to {customers_path}")
    
    # Generate devices and save to file
    devices_path = os.path.join(output_dir, 'devices.json')
    if not quiet:
        print(f"📱 Generating {num_devices:,} devices...")
    
    device_ids = []
    with open(devices_path, 'w', encoding='utf-8') as f:
        for i in range(1, num_devices + 1):
            device_id = f'DEV_{i:08d}'
            device_ids.append(device_id)
            # Associate device with a random customer
            customer_id = customer_data[random.randint(0, len(customer_data) - 1)]['customer_id']
            device = generate_device(device_id, customer_id, fake)
            f.write(json.dumps(device, ensure_ascii=False) + '\n')
            
            if not quiet and i % 50000 == 0:
                print(f"   ✓ {i:,} / {num_devices:,}", end='\r')
    
    if not quiet:
        print(f"   ✓ {num_devices:,} devices saved to {devices_path}")
    
    return customer_data, device_ids


def main():
    import argparse
    from datetime import date
    
    parser = argparse.ArgumentParser(
        description='🇧🇷 Brazilian Fraud Data Generator - Generate realistic financial transaction data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --size 1GB                    Generate 1GB of data
  %(prog)s --size 10GB --workers 8       Generate 10GB using 8 workers
  %(prog)s --size 50GB --fraud-rate 0.01 Generate 50GB with 1%% fraud
  %(prog)s --seed 42                     Reproducible generation
  %(prog)s --customers-only              Generate only customer base data
  %(prog)s --start-date 2024-01-01       Start from specific date

GitHub: https://github.com/afborda/brazilian-fraud-data-generator
        """
    )
    parser.add_argument('--size', type=str, default='1GB', 
                        help='Target data size (e.g., 1GB, 10GB, 50GB). Default: 1GB')
    parser.add_argument('--workers', type=int, default=mp.cpu_count(), 
                        help=f'Number of parallel workers. Default: {mp.cpu_count()} (CPU count)')
    parser.add_argument('--output', type=str, default='./output', 
                        help='Output directory. Default: ./output')
    parser.add_argument('--fraud-rate', type=float, default=0.007, 
                        help='Fraud rate (0.0-1.0). Default: 0.007 (0.7%%)')
    parser.add_argument('--customers', type=int, default=100000, 
                        help='Number of unique customers. Default: 100,000')
    parser.add_argument('--devices', type=int, default=None,
                        help='Number of devices. Default: 3x customers')
    parser.add_argument('--customers-only', action='store_true',
                        help='Generate only customer base data (no transactions)')
    parser.add_argument('--days', type=int, default=730,
                        help='Number of days of historical data. Default: 730 (2 years)')
    parser.add_argument('--start-date', type=str, default=None,
                        help='Start date (YYYY-MM-DD). Default: --days ago from today')
    parser.add_argument('--end-date', type=str, default=None,
                        help='End date (YYYY-MM-DD). Default: today')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode (minimal output)')
    
    args = parser.parse_args()
    
    # Set global seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)
    
    # Parse target size
    size_str = args.size.upper()
    if 'GB' in size_str:
        target_gb = float(size_str.replace('GB', ''))
    elif 'MB' in size_str:
        target_gb = float(size_str.replace('MB', '')) / 1024
    else:
        target_gb = float(size_str)
    
    # Calculate number of files
    target_mb = target_gb * 1024
    num_files = max(1, int(target_mb / TARGET_FILE_SIZE_MB))
    total_transactions = num_files * TRANSACTIONS_PER_FILE
    
    # Parse dates
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    else:
        start_date = end_date - timedelta(days=args.days)
    
    if not args.quiet:
        print("=" * 70)
        print("🇧🇷 BRAZILIAN FRAUD DATA GENERATOR")
        print("=" * 70)
        print(f"📊 Configuration:")
        print(f"   • Target size: {target_gb:.1f} GB")
        print(f"   • Files (128MB each): {num_files:,}")
        print(f"   • Transactions per file: {TRANSACTIONS_PER_FILE:,}")
        print(f"   • Total transactions: {total_transactions:,}")
        print(f"   • Parallel workers: {args.workers}")
        print(f"   • Fraud rate: {args.fraud_rate*100:.1f}%")
        print(f"   • Expected frauds: ~{int(total_transactions * args.fraud_rate):,}")
        print(f"   • Unique customers: {args.customers:,}")
        print(f"   • Devices: {args.devices if args.devices else args.customers * 3:,}")
        print(f"   • Date range: {start_date.date()} to {end_date.date()}")
        if args.seed is not None:
            print(f"   • Seed: {args.seed} (reproducible)")
        print(f"   • Output: {os.path.abspath(args.output)}")
        print("=" * 70)
    
    os.makedirs(args.output, exist_ok=True)
    
    # Generate or load base data
    customers_path = os.path.join(args.output, 'customers.json')
    devices_path = os.path.join(args.output, 'devices.json')
    
    if os.path.exists(customers_path) and os.path.exists(devices_path):
        if not args.quiet:
            print(f"\n📂 Loading existing data from {args.output}...")
        with open(customers_path, 'r') as f:
            customer_data = []
            for line in f:
                c = json.loads(line)
                customer_data.append({
                    'customer_id': c['customer_id'],
                    'estado': c['endereco']['estado']
                })
        if not args.quiet:
            print(f"   ✓ {len(customer_data):,} customers loaded")
        
        with open(devices_path, 'r') as f:
            device_ids = [json.loads(line)['device_id'] for line in f]
        if not args.quiet:
            print(f"   ✓ {len(device_ids):,} devices loaded")
    else:
        customer_data, device_ids = generate_base_data(
            args.output, args.customers, args.devices, args.quiet, args.seed
        )
    
    if args.customers_only:
        if not args.quiet:
            print(f"\n✅ Customer and device data generated successfully!")
        return
    
    # Check for existing transaction files
    existing_files = [f for f in os.listdir(args.output) if f.startswith('transactions_') and f.endswith('.json')]
    existing_count = len(existing_files)
    
    # Calculate current size
    current_size_mb = sum(
        os.path.getsize(os.path.join(args.output, f)) / (1024 * 1024) 
        for f in existing_files
    )
    current_size_gb = current_size_mb / 1024
    
    if current_size_gb >= target_gb * 0.99:
        if not args.quiet:
            print(f"\n✅ Already have {current_size_gb:.2f} GB generated ({existing_count} files)!")
            print(f"   Delete existing files to regenerate.")
        return
    
    # Calculate remaining files
    remaining_gb = target_gb - current_size_gb
    remaining_files = int((remaining_gb * 1024) / TARGET_FILE_SIZE_MB) + 1
    start_batch = existing_count
    
    if not args.quiet and existing_count > 0:
        print(f"\n🔄 Resuming: {current_size_gb:.2f} GB exists ({existing_count} files)")
        print(f"   Remaining: {remaining_gb:.2f} GB ({remaining_files} files)")
    
    # Prepare worker arguments
    batch_args = [
        (start_batch + i, TRANSACTIONS_PER_FILE, customer_data, device_ids, 
         start_date, end_date, args.fraud_rate, args.output, args.seed)
        for i in range(remaining_files)
    ]
    
    if not args.quiet:
        print(f"\n💳 Generating {remaining_files:,} files of ~128MB...")
        print(f"   🎯 Target: ~{remaining_files * TARGET_FILE_SIZE_MB / 1024:.1f} GB\n")
    
    # Execute in parallel
    start_time = time.time()
    completed = 0
    total_mb = 0
    
    with mp.Pool(args.workers) as pool:
        for batch_id, num_tx, file_mb, elapsed in pool.imap_unordered(worker_generate_batch, batch_args):
            completed += 1
            total_mb += file_mb
            
            if not args.quiet:
                # Progress bar
                pct = (completed / remaining_files) * 100
                elapsed_total = time.time() - start_time
                rate_mb_s = total_mb / elapsed_total if elapsed_total > 0 else 0
                remaining_mb = (remaining_files - completed) * TARGET_FILE_SIZE_MB
                eta_s = remaining_mb / rate_mb_s if rate_mb_s > 0 else 0
                
                bar_width = 40
                filled = int(bar_width * pct / 100)
                bar = '█' * filled + '░' * (bar_width - filled)
                
                print(f"\r  [{bar}] {pct:5.1f}% | {completed}/{remaining_files} | "
                      f"{total_mb/1024:.1f}GB | {rate_mb_s:.1f}MB/s | "
                      f"ETA: {int(eta_s//3600)}h{int((eta_s%3600)//60):02d}m", end='', flush=True)
    
    # Summary
    total_time = time.time() - start_time
    final_size_gb = current_size_gb + (total_mb / 1024)
    total_transactions_generated = remaining_files * TRANSACTIONS_PER_FILE
    
    if not args.quiet:
        print(f"\n\n{'=' * 70}")
        print("✅ GENERATION COMPLETE!")
        print("=" * 70)
        print(f"📁 Output directory: {os.path.abspath(args.output)}")
        print(f"📊 Files generated: {remaining_files:,} (total: {existing_count + remaining_files:,})")
        print(f"💳 Transactions: ~{total_transactions_generated:,}")
        print(f"💾 Total size: {final_size_gb:.2f} GB")
        print(f"⏱️  Time: {int(total_time//3600)}h {int((total_time%3600)//60)}m {int(total_time%60)}s")
        print(f"🚀 Speed: {total_mb/total_time:.1f} MB/s")
        print(f"\n📄 Files created:")
        print(f"   • customers.json ({len(customer_data):,} customers)")
        print(f"   • devices.json ({len(device_ids):,} devices)")
        print(f"   • transactions_XXXXX.json ({existing_count + remaining_files} files)")
    else:
        # Minimal output for quiet mode
        print(json.dumps({
            'status': 'complete',
            'output_dir': os.path.abspath(args.output),
            'files': existing_count + remaining_files,
            'transactions': total_transactions_generated,
            'size_gb': round(final_size_gb, 2),
            'time_seconds': round(total_time, 2)
        }))


if __name__ == '__main__':
    main()
