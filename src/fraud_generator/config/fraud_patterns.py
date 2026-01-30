"""
Fraud Pattern Definitions for Brazilian Fraud Data Generator.

Each fraud type has specific characteristics that make it detectável by ML models.
Based on real-world fraud patterns observed in Brazilian financial institutions.
"""

from typing import Dict, List, Any, Literal

# Anomaly levels
AnomalyLevel = Literal['NONE', 'LOW', 'MEDIUM', 'HIGH']

# Fraud pattern characteristics
FraudPattern = Dict[str, Any]

FRAUD_PATTERNS: Dict[str, FraudPattern] = {
    'ENGENHARIA_SOCIAL': {
        'name': 'Engenharia Social',
        'description': 'Vítima é enganada e faz transação legítima para fraudador',
        'characteristics': {
            'value_anomaly': 'LOW',              # Valor parece normal
            'new_beneficiary': True,              # Sempre novo destino
            'velocity': 'LOW',                    # Velocidade normal
            'time_anomaly': 'LOW',                # Horário normal
            'location_anomaly': 'NONE',           # Mesma localização
            'device_anomaly': 'NONE',             # Mesmo device
            'channel_preference': ['PIX', 'TED'], # Transferências
            'amount_multiplier': (1.0, 2.5),      # 1x-2.5x valor típico
        },
        'prevalence': 0.20,  # 20% das fraudes
        'fraud_score_base': 0.35,
    },
    
    'CONTA_TOMADA': {
        'name': 'Conta Tomada (Account Takeover)',
        'description': 'Fraudador obtém acesso à conta da vítima',
        'characteristics': {
            'value_anomaly': 'HIGH',              # Valores muito altos
            'new_beneficiary': True,              # Novos destinos suspeitos
            'velocity': 'HIGH',                   # Múltiplas transações rápidas
            'time_anomaly': 'HIGH',               # Madrugada (22h-5h)
            'location_anomaly': 'HIGH',           # IP/geo diferente
            'device_anomaly': 'HIGH',             # Device completamente novo
            'channel_preference': ['PIX', 'TED', 'ONLINE'],
            'amount_multiplier': (3.0, 10.0),     # 3x-10x valor típico
            'transaction_burst': (5, 15),         # 5-15 transações em sequência
        },
        'prevalence': 0.15,
        'fraud_score_base': 0.75,
    },
    
    'CARTAO_CLONADO': {
        'name': 'Cartão Clonado',
        'description': 'Dados do cartão foram copiados e usados em transações não autorizadas',
        'characteristics': {
            'value_anomaly': 'MEDIUM',            # Escalação: baixo depois alto
            'new_beneficiary': False,             # Merchants comuns (posto, loja)
            'velocity': 'HIGH',                   # Série rápida de compras
            'time_anomaly': 'MEDIUM',             # Pode ser qualquer hora
            'location_anomaly': 'HIGH',           # Geograficamente distante
            'device_anomaly': 'HIGH',             # POS/terminal diferente
            'channel_preference': ['POS', 'ECOMMERCE'],
            'amount_multiplier': (1.5, 4.0),      # 1.5x-4x valor típico
            'mcc_preference': ['5541', '5542', '5912', '5411'],  # Posto, farmácia, supermercado
        },
        'prevalence': 0.14,
        'fraud_score_base': 0.65,
    },
    
    'PIX_GOLPE': {
        'name': 'Golpe via PIX',
        'description': 'Fraude específica de PIX (QR code falso, falso sequestro, etc)',
        'characteristics': {
            'value_anomaly': 'MEDIUM',            # Valores altos mas não absurdos
            'new_beneficiary': True,              # Sempre chave PIX desconhecida
            'velocity': 'MEDIUM',                 # 2-5 transações rápidas
            'time_anomaly': 'MEDIUM',             # Urgência: qualquer hora
            'location_anomaly': 'LOW',            # Pode ser mesma localização
            'device_anomaly': 'LOW',              # Mesmo device (vítima opera)
            'channel_preference': ['PIX'],        # Exclusivamente PIX
            'amount_multiplier': (2.0, 6.0),      # 2x-6x valor típico
            'pix_key_type': ['CPF', 'PHONE', 'RANDOM'],  # Tipos de chave suspeitos
        },
        'prevalence': 0.25,  # PIX é muito comum no Brasil
        'fraud_score_base': 0.55,
    },
    
    'FRAUDE_APLICATIVO': {
        'name': 'Fraude de Aplicativo',
        'description': 'App malicioso ou app legítimo comprometido',
        'characteristics': {
            'value_anomaly': 'MEDIUM',
            'new_beneficiary': True,
            'velocity': 'HIGH',
            'time_anomaly': 'LOW',
            'location_anomaly': 'MEDIUM',         # IP pode ser proxy/VPN
            'device_anomaly': 'HIGH',             # Device ID suspeito
            'channel_preference': ['MOBILE_APP', 'PIX'],
            'amount_multiplier': (1.5, 5.0),
        },
        'prevalence': 0.12,
        'fraud_score_base': 0.60,
    },
    
    'COMPRA_TESTE': {
        'name': 'Compra Teste (Card Testing)',
        'description': 'Testes com cartões roubados para validar',
        'characteristics': {
            'value_anomaly': 'NONE',              # Valores MUITO baixos (R$1-10)
            'new_beneficiary': False,
            'velocity': 'HIGH',                   # Múltiplas tentativas
            'time_anomaly': 'LOW',
            'location_anomaly': 'HIGH',           # Pode ser internacional
            'device_anomaly': 'HIGH',
            'channel_preference': ['ECOMMERCE', 'POS'],
            'amount_multiplier': (0.01, 0.1),     # 1%-10% do valor típico
            'amount_override': (1.0, 30.0),       # Force very low amounts (R$1-30)
            'transaction_burst': (10, 50),        # Muitas tentativas
        },
        'prevalence': 0.08,
        'fraud_score_base': 0.50,
    },
    
    'MULA_FINANCEIRA': {
        'name': 'Mula Financeira (Money Mule)',
        'description': 'Conta usada para receber/transferir dinheiro de fraudes',
        'characteristics': {
            'value_anomaly': 'HIGH',              # Valores altos
            'new_beneficiary': True,              # Sempre novos destinos
            'velocity': 'MEDIUM',                 # Distribuição ao longo do dia
            'time_anomaly': 'LOW',
            'location_anomaly': 'LOW',
            'device_anomaly': 'LOW',
            'channel_preference': ['PIX', 'TED', 'DOC'],
            'amount_multiplier': (3.0, 8.0),
            'transaction_pattern': 'PASSTHROUGH',  # Recebe e transfere rápido
        },
        'prevalence': 0.06,
        'fraud_score_base': 0.70,
    },
}

# List of fraud types for random selection
FRAUD_TYPES_LIST = list(FRAUD_PATTERNS.keys())

# Weights based on prevalence
FRAUD_TYPES_WEIGHTS = [pattern['prevalence'] for pattern in FRAUD_PATTERNS.values()]

# Normalize weights to sum to 1.0
total_weight = sum(FRAUD_TYPES_WEIGHTS)
FRAUD_TYPES_WEIGHTS = [w / total_weight for w in FRAUD_TYPES_WEIGHTS]


def get_fraud_pattern(fraud_type: str) -> FraudPattern:
    """
    Get fraud pattern configuration for a specific type.
    
    Args:
        fraud_type: Fraud type key (e.g., 'CONTA_TOMADA')
        
    Returns:
        Fraud pattern configuration dict
        
    Raises:
        KeyError: If fraud type not found
    """
    if fraud_type not in FRAUD_PATTERNS:
        raise KeyError(f"Unknown fraud type: {fraud_type}. Available: {FRAUD_TYPES_LIST}")
    
    return FRAUD_PATTERNS[fraud_type]


def get_anomaly_multiplier(anomaly_level: AnomalyLevel) -> float:
    """
    Get intensity multiplier for anomaly level.
    
    Args:
        anomaly_level: NONE, LOW, MEDIUM, or HIGH
        
    Returns:
        Multiplier value (0.0 = no change, 1.0 = maximum change)
    """
    multipliers = {
        'NONE': 0.0,
        'LOW': 0.3,
        'MEDIUM': 0.6,
        'HIGH': 1.0,
    }
    return multipliers.get(anomaly_level, 0.0)


# Time windows for time anomaly
TIME_ANOMALY_WINDOWS = {
    'NONE': list(range(6, 22)),      # Normal: 6h-22h
    'LOW': list(range(22, 24)) + list(range(0, 2)),  # Slightly late: 22h-2h
    'MEDIUM': list(range(20, 24)) + list(range(0, 4)),  # Late: 20h-4h
    'HIGH': list(range(22, 24)) + list(range(0, 5)),    # Very late: 22h-5h (madrugada)
}


# MCC codes commonly used in fraud
FRAUD_MCC_CODES = {
    'CARTAO_CLONADO': ['5541', '5542', '5912', '5411', '5732'],  # Posto, farmácia, eletrônicos
    'COMPRA_TESTE': ['5999', '5732', '5411'],  # Lojas genéricas
}


def get_time_window_for_anomaly(anomaly_level: AnomalyLevel) -> List[int]:
    """Get valid hours for time anomaly level."""
    return TIME_ANOMALY_WINDOWS.get(anomaly_level, list(range(0, 24)))
