#!/usr/bin/env python3
"""
🇧🇷 BRAZILIAN FRAUD DATA GENERATOR
===================================
Generate realistic Brazilian financial transaction data for testing,
development, and machine learning model training.

Features:
- 100% Brazilian data (CPF, banks, PIX, addresses)
- Configurable fraud patterns
- Parallel generation for high throughput
- JSON Lines output format

Usage:
    python3 generate.py --size 1GB --workers 4 --output ./output
    python3 generate.py --size 50GB --fraud-rate 0.01
"""

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

# Brazilian bank codes (Código COMPE)
BANK_CODES = [
    '001',  # Banco do Brasil
    '033',  # Santander
    '104',  # Caixa Econômica Federal
    '237',  # Bradesco
    '341',  # Itaú
    '260',  # Nubank
    '077',  # Inter
    '336',  # C6 Bank
    '290',  # PagBank
    '380',  # PicPay
    '323',  # Mercado Pago
    '403',  # Cora
    '212',  # Banco Original
]

# MCC codes with categories and risk levels
MCC_CODES = {
    '5411': ('Supermercados', 'low'),
    '5541': ('Postos de Combustível', 'low'),
    '5812': ('Restaurantes', 'low'),
    '5814': ('Fast Food', 'low'),
    '5912': ('Farmácias', 'low'),
    '5311': ('Lojas de Departamento', 'medium'),
    '5651': ('Vestuário', 'medium'),
    '5732': ('Eletrônicos', 'high'),
    '5944': ('Joalherias', 'high'),
    '5999': ('Diversos', 'medium'),
    '7011': ('Hotéis', 'medium'),
    '4111': ('Transporte', 'low'),
    '6011': ('Caixa Eletrônico', 'medium'),
    '7995': ('Apostas/Cassino', 'high'),
}

# Brazilian merchants
MERCHANTS = [
    # Supermarkets
    'Supermercado Extra', 'Carrefour', 'Pão de Açúcar', 'Assaí Atacadista',
    # Gas stations
    'Posto Shell', 'Posto Ipiranga', 'Posto BR',
    # Food delivery
    'iFood', 'Rappi', 'Uber Eats',
    # Fast food
    'McDonald\'s', 'Burger King', 'Subway', 'Bob\'s',
    # Pharmacies
    'Drogasil', 'Droga Raia', 'Pacheco',
    # Clothing
    'Renner', 'C&A', 'Riachuelo', 'Zara',
    # Electronics/Retail
    'Magazine Luiza', 'Casas Bahia', 'Amazon Brasil', 'Mercado Livre', 'Americanas',
    # Travel
    'Hotel Ibis', 'Booking.com', 'Airbnb',
    # Transport
    '99', 'Uber', 'Cabify',
]

# Transaction types (PIX weighted higher - realistic for Brazil)
TRANSACTION_TYPES = ['PIX', 'PIX', 'PIX', 'PIX', 'CARTAO_CREDITO', 'CARTAO_CREDITO', 
                     'CARTAO_DEBITO', 'TED', 'BOLETO', 'SAQUE']

# Channels
CHANNELS = ['APP_MOBILE', 'APP_MOBILE', 'APP_MOBILE', 'WEB_BANKING', 'ATM', 'AGENCIA']

# Fraud types
FRAUD_TYPES = [
    'CARTAO_CLONADO',       # Cloned card
    'CONTA_TOMADA',         # Account takeover
    'IDENTIDADE_FALSA',     # Identity fraud
    'ENGENHARIA_SOCIAL',    # Social engineering
    'LAVAGEM_DINHEIRO',     # Money laundering
    'AUTOFRAUDE',           # First-party fraud
    'FRAUDE_AMIGAVEL',      # Friendly fraud
    'TRIANGULACAO',         # Triangulation fraud
]

# PIX key types
PIX_KEY_TYPES = ['CPF', 'EMAIL', 'TELEFONE', 'ALEATORIA', 'CNPJ']

# Card brands
CARD_BRANDS = ['VISA', 'MASTERCARD', 'ELO', 'AMEX', 'HIPERCARD']


def generate_ip_brazil():
    """Generate Brazilian IP address"""
    # Common Brazilian IP prefixes
    prefix = random.choice(['177.', '187.', '189.', '191.', '200.', '201.'])
    return prefix + '.'.join(str(random.randint(0, 255)) for _ in range(3))


def generate_transaction(tx_id, customer_id, device_id, timestamp, is_fraud, fraud_type, fake):
    """Generate a single transaction"""
    tx_type = random.choice(TRANSACTION_TYPES)
    mcc_code = random.choice(list(MCC_CODES.keys()))
    mcc_cat, mcc_risk = MCC_CODES[mcc_code]
    
    # Value based on fraud status
    if is_fraud:
        # Fraudsters tend to make higher value transactions
        valor = round(random.uniform(500, 15000), 2)
    else:
        # Normal distribution for legitimate transactions
        valor = round(random.choices(
            [random.uniform(5, 100), random.uniform(100, 500), random.uniform(500, 2000), random.uniform(2000, 10000)],
            weights=[50, 30, 15, 5]
        )[0], 2)
    
    tx = {
        'transaction_id': f'TXN_{tx_id:015d}',
        'customer_id': customer_id,
        'session_id': f'SESS_{tx_id:012d}',
        'device_id': device_id,
        'timestamp': timestamp.isoformat(),
        'tipo': tx_type,
        'valor': valor,
        'moeda': 'BRL',
        'canal': random.choice(CHANNELS),
        'ip_address': generate_ip_brazil(),
        # Brazilian geographical coordinates
        'geolocalizacao_lat': round(random.uniform(-33.75, 5.27), 6),
        'geolocalizacao_lon': round(random.uniform(-73.99, -34.79), 6),
        'merchant_id': f'MERCH_{random.randint(1, 100000):06d}',
        'merchant_name': random.choice(MERCHANTS),
        'merchant_category': mcc_cat,
        'mcc_code': mcc_code,
        'mcc_risk_level': mcc_risk,
    }
    
    # Type-specific fields
    if tx_type in ['CARTAO_CREDITO', 'CARTAO_DEBITO']:
        tx.update({
            'numero_cartao_hash': hashlib.md5(str(random.random()).encode()).hexdigest()[:16],
            'bandeira': random.choice(CARD_BRANDS),
            'tipo_cartao': 'CREDITO' if tx_type == 'CARTAO_CREDITO' else 'DEBITO',
            'parcelas': random.choice([1, 1, 1, 2, 3, 6, 12]) if tx_type == 'CARTAO_CREDITO' else 1,
            'entrada_cartao': random.choice(['CHIP', 'CONTACTLESS', 'DIGITADO', 'MAGNETICO']),
            'cvv_validado': random.choice([True, True, True, False]),
            'autenticacao_3ds': random.choice([True, False]),
            'chave_pix_tipo': None,
            'chave_pix_destino': None,
            'banco_destino': None,
        })
    elif tx_type == 'PIX':
        tx.update({
            'numero_cartao_hash': None,
            'bandeira': None,
            'tipo_cartao': None,
            'parcelas': None,
            'entrada_cartao': None,
            'cvv_validado': None,
            'autenticacao_3ds': None,
            'chave_pix_tipo': random.choice(PIX_KEY_TYPES),
            'chave_pix_destino': fake.email() if random.random() > 0.5 else fake.cpf(),
            'banco_destino': random.choice(BANK_CODES),
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
            'banco_destino': random.choice(BANK_CODES) if tx_type in ['TED', 'DOC'] else None,
        })
    
    # Risk indicators
    tx.update({
        'distancia_ultima_transacao_km': round(random.uniform(0, 500), 2) if random.random() > 0.7 else None,
        'tempo_desde_ultima_transacao_min': random.randint(1, 1440) if random.random() > 0.5 else None,
        'transacoes_ultimas_24h': random.randint(1, 30),
        'valor_acumulado_24h': round(random.uniform(100, 10000), 2),
        'horario_incomum': random.random() < 0.1,
        'novo_beneficiario': random.random() < 0.2,
        'status': 'APROVADA' if not is_fraud or random.random() > 0.3 else random.choice(['RECUSADA', 'PENDENTE', 'BLOQUEADA']),
        'motivo_recusa': random.choice(['SALDO_INSUFICIENTE', 'SUSPEITA_FRAUDE', 'LIMITE_EXCEDIDO', 'ERRO_COMUNICACAO']) if random.random() < 0.05 else None,
        'fraud_score': round(random.uniform(70, 100), 2) if is_fraud else round(random.uniform(0, 30), 2),
        'is_fraud': is_fraud,
        'fraud_type': fraud_type,
    })
    
    return tx


def generate_customer(customer_id, fake):
    """Generate a single customer"""
    created_date = fake.date_time_between(start_date='-5y', end_date='-1m')
    
    # Risk profile based on account age
    account_age_days = (datetime.now() - created_date).days
    if account_age_days < 30:
        risk_level = random.choices(['ALTO', 'MEDIO', 'BAIXO'], weights=[30, 50, 20])[0]
    elif account_age_days < 180:
        risk_level = random.choices(['ALTO', 'MEDIO', 'BAIXO'], weights=[10, 40, 50])[0]
    else:
        risk_level = random.choices(['ALTO', 'MEDIO', 'BAIXO'], weights=[5, 25, 70])[0]
    
    return {
        'customer_id': customer_id,
        'nome': fake.name(),
        'cpf': fake.cpf(),
        'email': fake.email(),
        'telefone': fake.phone_number(),
        'data_nascimento': fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
        'endereco': {
            'logradouro': fake.street_address(),
            'cidade': fake.city(),
            'estado': fake.estado_sigla(),
            'cep': fake.postcode(),
        },
        'conta_criada_em': created_date.isoformat(),
        'tipo_conta': random.choice(['CORRENTE', 'POUPANCA', 'DIGITAL']),
        'status_conta': random.choices(['ATIVA', 'BLOQUEADA', 'INATIVA'], weights=[95, 3, 2])[0],
        'limite_credito': round(random.uniform(500, 50000), 2),
        'score_credito': random.randint(300, 900),
        'nivel_risco': risk_level,
        'banco_codigo': random.choice(BANK_CODES),
        'agencia': f'{random.randint(1, 9999):04d}',
        'numero_conta': f'{random.randint(10000, 999999)}-{random.randint(0, 9)}',
    }


def worker_generate_batch(args):
    """Worker that generates a 128MB file"""
    batch_id, num_transactions, customer_ids, device_ids, start_date, end_date, fraud_rate, output_dir = args
    
    # Unique seed per worker for different data
    seed = batch_id * 12345 + int(time.time() * 1000) % 10000
    random.seed(seed)
    fake = Faker('pt_BR')
    Faker.seed(seed)
    
    output_path = os.path.join(output_dir, f'transactions_{batch_id:05d}.json')
    
    start_time = time.time()
    tx_id_start = batch_id * num_transactions
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(num_transactions):
            tx_id = tx_id_start + i
            customer_id = random.choice(customer_ids)
            device_id = random.choice(device_ids) if device_ids else None
            timestamp = fake.date_time_between(start_date=start_date, end_date=end_date)
            is_fraud = random.random() < fraud_rate
            fraud_type = random.choice(FRAUD_TYPES) if is_fraud else None
            
            tx = generate_transaction(tx_id, customer_id, device_id, timestamp, is_fraud, fraud_type, fake)
            f.write(json.dumps(tx, ensure_ascii=False) + '\n')
    
    elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    
    return batch_id, num_transactions, file_size_mb, elapsed


def generate_base_data(output_dir, num_customers=100000, num_devices=300000):
    """Generate base customer and device data"""
    fake = Faker('pt_BR')
    
    # Generate customers
    customers_path = os.path.join(output_dir, 'customers.json')
    print(f"\n👤 Generating {num_customers:,} customers...")
    
    customer_ids = []
    with open(customers_path, 'w', encoding='utf-8') as f:
        for i in range(1, num_customers + 1):
            customer_id = f'CUST_{i:08d}'
            customer_ids.append(customer_id)
            customer = generate_customer(customer_id, fake)
            f.write(json.dumps(customer, ensure_ascii=False) + '\n')
            
            if i % 10000 == 0:
                print(f"   ✓ {i:,} / {num_customers:,}", end='\r')
    
    print(f"   ✓ {num_customers:,} customers saved to {customers_path}")
    
    # Generate device IDs
    device_ids = [f'DEV_{i:08d}' for i in range(1, num_devices + 1)]
    print(f"📱 Generated {num_devices:,} device IDs")
    
    return customer_ids, device_ids


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='🇧🇷 Brazilian Fraud Data Generator - Generate realistic financial transaction data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --size 1GB                    Generate 1GB of data
  %(prog)s --size 10GB --workers 8       Generate 10GB using 8 workers
  %(prog)s --size 50GB --fraud-rate 0.01 Generate 50GB with 1%% fraud
  %(prog)s --customers-only              Generate only customer base data

GitHub: https://github.com/your-username/brazilian-fraud-data-generator
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
    parser.add_argument('--customers-only', action='store_true',
                        help='Generate only customer base data (no transactions)')
    parser.add_argument('--days', type=int, default=730,
                        help='Number of days of historical data. Default: 730 (2 years)')
    
    args = parser.parse_args()
    
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
    print(f"   • Historical days: {args.days}")
    print(f"   • Output: {os.path.abspath(args.output)}")
    print("=" * 70)
    
    os.makedirs(args.output, exist_ok=True)
    
    # Generate or load base data
    customers_path = os.path.join(args.output, 'customers.json')
    if os.path.exists(customers_path):
        print(f"\n📂 Loading existing customers from {customers_path}...")
        with open(customers_path, 'r') as f:
            customer_ids = [json.loads(line)['customer_id'] for line in f]
        print(f"   ✓ {len(customer_ids):,} customers loaded")
        device_ids = [f'DEV_{i:08d}' for i in range(1, 300001)]
    else:
        customer_ids, device_ids = generate_base_data(args.output, args.customers)
    
    if args.customers_only:
        print(f"\n✅ Customer data generated successfully!")
        return
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
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
        print(f"\n✅ Already have {current_size_gb:.2f} GB generated ({existing_count} files)!")
        print(f"   Delete existing files to regenerate.")
        return
    
    # Calculate remaining files
    remaining_gb = target_gb - current_size_gb
    remaining_files = int((remaining_gb * 1024) / TARGET_FILE_SIZE_MB) + 1
    start_batch = existing_count
    
    if existing_count > 0:
        print(f"\n🔄 Resuming: {current_size_gb:.2f} GB exists ({existing_count} files)")
        print(f"   Remaining: {remaining_gb:.2f} GB ({remaining_files} files)")
    
    # Prepare worker arguments
    batch_args = [
        (start_batch + i, TRANSACTIONS_PER_FILE, customer_ids, device_ids, 
         start_date, end_date, args.fraud_rate, args.output)
        for i in range(remaining_files)
    ]
    
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
    print(f"   • customers.json ({args.customers:,} customers)")
    print(f"   • transactions_XXXXX.json ({remaining_files} files)")


if __name__ == '__main__':
    main()
