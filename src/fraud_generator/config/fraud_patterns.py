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
            'new_beneficiary_prob': 0.55,        # Nem sempre novo destino (vítima pode pagar "conta atrasada")
            'velocity': 'LOW',                    # Velocidade normal
            'time_anomaly': 'LOW',                # Horário normal
            'location_anomaly': 'NONE',           # Mesma localização
            'device_anomaly': 'NONE',             # Mesmo device
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED'],    # Transferências
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
            'new_beneficiary_prob': 0.60,        # Fraudador pode usar destinos recorrentes
            'velocity': 'HIGH',                   # Múltiplas transações rápidas
            'time_anomaly': 'HIGH',               # Madrugada (22h-5h)
            'location_anomaly': 'HIGH',           # IP/geo diferente
            'device_anomaly': 'HIGH',             # Device completamente novo
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED'],
            'amount_multiplier': (1.5, 5.0),      # 1.5x-5x valor típico
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
            'new_beneficiary_prob': 0.25,        # Merchants comuns (posto, loja)
            'velocity': 'HIGH',                   # Série rápida de compras
            'time_anomaly': 'MEDIUM',             # Pode ser qualquer hora
            'location_anomaly': 'HIGH',           # Geograficamente distante
            'device_anomaly': 'HIGH',             # Terminal diferente
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['CREDIT_CARD', 'DEBIT_CARD'],
            'amount_multiplier': (1.2, 3.0),      # 1.2x-3x valor típico
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
            'new_beneficiary_prob': 0.65,        # Chave PIX frequentemente nova mas não sempre
            'velocity': 'MEDIUM',                 # 2-5 transações rápidas
            'time_anomaly': 'MEDIUM',             # Urgência: qualquer hora
            'location_anomaly': 'LOW',            # Pode ser mesma localização
            'device_anomaly': 'LOW',              # Mesmo device (vítima opera)
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX'],           # Exclusivamente PIX
            'amount_multiplier': (1.5, 4.0),      # 1.5x-4x valor típico
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
            'new_beneficiary_prob': 0.50,
            'velocity': 'HIGH',
            'time_anomaly': 'LOW',
            'location_anomaly': 'MEDIUM',         # IP pode ser proxy/VPN
            'device_anomaly': 'HIGH',             # Device ID suspeito
            'channel_preference': ['MOBILE_APP'],
            'type_preference': ['PIX', 'CREDIT_CARD'],
            'amount_multiplier': (1.2, 3.0),
        },
        'prevalence': 0.12,
        'fraud_score_base': 0.60,
    },

    'COMPRA_TESTE': {
        'name': 'Compra Teste (Card Testing)',
        'description': 'Testes com cartões roubados para validar',
        'characteristics': {
            'value_anomaly': 'NONE',              # Valores MUITO baixos (R$1-10)
            'new_beneficiary_prob': 0.15,        # Merchants comuns
            'velocity': 'HIGH',                   # Múltiplas tentativas
            'time_anomaly': 'LOW',
            'location_anomaly': 'HIGH',           # Pode ser internacional
            'device_anomaly': 'HIGH',
            'channel_preference': ['WEB_BANKING', 'MOBILE_APP'],
            'type_preference': ['CREDIT_CARD', 'DEBIT_CARD'],
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
            'new_beneficiary_prob': 0.40,        # Mulas têm destinos recorrentes
            'velocity': 'MEDIUM',                 # Distribuição ao longo do dia
            'time_anomaly': 'LOW',
            'location_anomaly': 'LOW',
            'device_anomaly': 'LOW',
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED'],
            'amount_multiplier': (1.5, 3.0),
            'transaction_pattern': 'PASSTHROUGH',  # Recebe e transfere rápido
        },
        'prevalence': 0.06,
        'fraud_score_base': 0.70,
    },

    # ------------------------------------------------------------------ #
    #  T3 — Novos Padrões de Alta Prioridade                              #
    # ------------------------------------------------------------------ #

    'CARD_TESTING': {
        'name': 'Teste de Cartão (Card Testing)',
        'description': (
            'Validação de cartões roubados em 3 fases: micro-compras → silêncio '
            '→ compras grandes. Sinal de ML muito forte: escalada de valor + '
            'burst de pequenas transações.'
        ),
        'characteristics': {
            'value_anomaly': 'MEDIUM',            # Varia por fase (baixo→alto)
            'new_beneficiary_prob': 0.15,        # Merchants comuns
            'velocity': 'HIGH',                   # Burst na fase 1
            'time_anomaly': 'LOW',
            'location_anomaly': 'HIGH',           # International / VPN
            'device_anomaly': 'HIGH',             # Device nunca visto
            'channel_preference': ['WEB_BANKING', 'MOBILE_APP'],
            'type_preference': ['CREDIT_CARD', 'DEBIT_CARD'],
            'transaction_burst': (3, 8),          # Fase-1: 3-8 micro-transações
            # Fase 1 (65% prob): micro-amounts
            'card_test_phase_1_amount': (0.01, 1.00),
            # Fase 3 (35% prob): valores médios-altos
            'card_test_phase_3_amount': (500.0, 3000.0),
            'mcc_preference': ['5999', '5732', '5411', '5912'],
        },
        'prevalence': 0.07,
        'fraud_score_base': 0.75,
    },

    'MICRO_BURST_VELOCITY': {
        'name': 'Rajada de Velocidade (Micro-Burst)',
        'description': (
            '10–50 transações em janela de 5–15 minutos, com valores variados. '
            'Tipicamente de device novo ou IP nunca visto. Indica automação / '
            'ataque de força bruta.'
        ),
        'characteristics': {
            'value_anomaly': 'MEDIUM',
            'new_beneficiary_prob': 0.75,
            'velocity': 'HIGH',
            'time_anomaly': 'MEDIUM',
            'location_anomaly': 'MEDIUM',
            'device_anomaly': 'HIGH',             # Device novo ou IP suspeito
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'CREDIT_CARD', 'DEBIT_CARD'],
            'amount_multiplier': (0.5, 3.0),
            'transaction_burst': (10, 50),        # 10-50 txns em 5-15 min
            'burst_window_minutes': (5, 15),      # Janela de tempo em minutos
        },
        'prevalence': 0.05,
        'fraud_score_base': 0.80,
    },

    'DISTRIBUTED_VELOCITY': {
        'name': 'Velocidade Distribuída (Evasão de Velocity Check)',
        'description': (
            'Mesmo ataque com rotação de devices/IPs para iludir velocity checks. '
            '2–3 transações por device, depois troca. Alta correlação com rings '
            'de fraude quando agrupadas por `distributed_attack_group`.'
        ),
        'characteristics': {
            'value_anomaly': 'MEDIUM',
            'new_beneficiary_prob': 0.70,
            'velocity': 'MEDIUM',                 # Baixo por device — alto no grupo
            'time_anomaly': 'MEDIUM',
            'location_anomaly': 'HIGH',           # IPs/cidades diferentes
            'device_anomaly': 'HIGH',             # Rotação de devices
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'CREDIT_CARD'],
            'amount_multiplier': (1.0, 4.0),
            'transactions_per_device': (2, 3),    # Antes de trocar device/IP
        },
        'prevalence': 0.04,
        'fraud_score_base': 0.78,
    },

    'BOLETO_FALSO': {
        'name': 'Boleto Falso',
        'description': (
            'Boleto forjado ou interceptado: vítima paga boleto legítimo mas '
            'linha digitável foi substituída. Chargeback 2–5 dias após. '
            'Real: 8% das fraudes bancárias BR (FEBRABAN 2024).'
        ),
        'characteristics': {
            'value_anomaly': 'LOW',               # Valor parece legítimo
            'new_beneficiary_prob': 0.90,        # Novo ISPB/banco destino
            'velocity': 'LOW',                    # Pagamento único
            'time_anomaly': 'LOW',                # Horário comercial
            'location_anomaly': 'NONE',           # Mesma localização da vítima
            'device_anomaly': 'NONE',             # Mesmo device
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['BOLETO'],
            'amount_multiplier': (0.8, 1.5),      # Próximo ao valor esperado
        },
        'prevalence': 0.08,
        'fraud_score_base': 0.40,
    },

    # ------------------------------------------------------------------ #
    #  Novos Padrões — Produto Pago Pro+ (pesquisa 2024-2025)             #
    # ------------------------------------------------------------------ #

    'MAO_FANTASMA': {
        'name': 'Mão Fantasma (RAT Fraud)',
        'description': (
            'Criminoso opera o dispositivo legítimo da vítima remotamente via RAT '
            '(Remote Access Tool). Device e localização são legítimos — o sinal '
            'está nos padrões comportamentais (velocidade de digitação zero, sem '
            'pressão de toque, sessão anormalmente curta). Exclusivo produto pago: '
            'nenhum dataset público tem dados calibrados para esse padrão no Brasil.'
        ),
        'characteristics': {
            'value_anomaly': 'HIGH',
            'new_beneficiary_prob': 0.65,
            'velocity': 'HIGH',
            'time_anomaly': 'HIGH',               # Madrugada — vítima dormindo
            'location_anomaly': 'NONE',           # Device legítimo = localização correta
            'device_anomaly': 'NONE',             # Mesmo device da vítima
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED'],
            'amount_multiplier': (2.0, 8.0),
            'transaction_burst': (3, 10),
            'pix_key_type': ['CPF', 'PHONE', 'RANDOM'],
        },
        'prevalence': 0.04,
        'fraud_score_base': 0.85,
        'detection_delay_days': (1, 3),
        'credential_breach_days_before': (0, 1),  # Acesso imediato via RAT
    },

    'WHATSAPP_CLONE': {
        'name': 'Clone de WhatsApp',
        'description': (
            'Criminoso clona número da vítima e se passa por familiar/amigo pedindo '
            'PIX urgente. Vítima opera seu próprio device normalmente — sinal único '
            'é "novo destinatário + valor atípico para o relacionamento". '
            'Muito comum no Brasil: R$150M+ em 2024 (Febraban).'
        ),
        'characteristics': {
            'value_anomaly': 'LOW',               # Parece pedido normal de familiar
            'new_beneficiary_prob': 0.70,        # Alta mas não determinística
            'velocity': 'LOW',
            'time_anomaly': 'NONE',               # Horário normal
            'location_anomaly': 'NONE',           # Vítima em casa
            'device_anomaly': 'NONE',             # Device legítimo
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX'],
            'amount_multiplier': (0.5, 2.5),
            'pix_key_type': ['CPF', 'PHONE'],
        },
        'prevalence': 0.05,
        'fraud_score_base': 0.25,                 # Muito difícil de detectar
        'detection_delay_days': (1, 7),
    },

    'SIM_SWAP': {
        'name': 'SIM Swap',
        'description': (
            'Portabilidade fraudulenta do número de telefone seguida de ATO. '
            'Cadeia: clona SIM → reseta senha (SMS token) → acessa conta → '
            'drena em sequência. Sinal mais forte: sim_swap_recent=True + '
            'novo device + madrugada.'
        ),
        'characteristics': {
            'value_anomaly': 'HIGH',
            'new_beneficiary_prob': 0.65,
            'velocity': 'HIGH',
            'time_anomaly': 'MEDIUM',
            'location_anomaly': 'HIGH',
            'device_anomaly': 'HIGH',             # Novo device logo após SIM swap
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED'],
            'amount_multiplier': (3.0, 10.0),
            'transaction_burst': (3, 8),
            'pix_key_type': ['CPF', 'PHONE', 'RANDOM'],
        },
        'prevalence': 0.03,
        'fraud_score_base': 0.80,
        'detection_delay_days': (1, 5),
        'credential_breach_days_before': (0, 0),  # Acesso no mesmo dia do SIM swap
    },

    'CREDENTIAL_STUFFING': {
        'name': 'Credential Stuffing',
        'description': (
            'Ataque automatizado: bot testa lista de credenciais vazadas de outros '
            'serviços até encontrar reuso de senha. Sinal biométrico: intervalo de '
            'digitação = 0ms, zero variância, navegação sem padrão humano. '
            'velocity_transactions_1h explode quando bot encontra credencial válida.'
        ),
        'characteristics': {
            'value_anomaly': 'LOW',               # Transferência não muito grande
            'new_beneficiary_prob': 0.30,        # Bots testam destinos comuns
            'velocity': 'HIGH',
            'time_anomaly': 'NONE',               # Bots rodam 24/7
            'location_anomaly': 'HIGH',           # IP de datacenter / TOR
            'device_anomaly': 'HIGH',             # Device nunca visto
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED', 'CREDIT_CARD'],
            'amount_multiplier': (1.0, 3.0),
            'transaction_burst': (20, 100),       # Bot é rápido
        },
        'prevalence': 0.03,
        'fraud_score_base': 0.90,
        'detection_delay_days': (0, 2),
        'credential_breach_days_before': (30, 365),  # Credenciais antigas de leak
    },

    'SYNTHETIC_IDENTITY': {
        'name': 'Identidade Sintética',
        'description': (
            'CPF válido (às vezes real, às vezes gerado artificialmente) usado para '
            'abrir conta que parece legítima por meses. Comportamento "perfeito" '
            'até o momento de ativação (saque grande). Fraud detection precisa de '
            'dados históricos + multi-label para treinar.'
        ),
        'characteristics': {
            'value_anomaly': 'NONE',              # Comportamento normal até ativação
            'new_beneficiary_prob': 0.70,
            'velocity': 'LOW',
            'time_anomaly': 'NONE',
            'location_anomaly': 'NONE',
            'device_anomaly': 'NONE',             # Parece humano normal
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED', 'CREDIT_CARD'],
            'amount_multiplier': (2.0, 6.0),     # Ativação: saque grande
        },
        'prevalence': 0.02,
        'fraud_score_base': 0.20,                 # Muito difícil de detectar
        'detection_delay_days': (30, 180),        # Descoberto tarde
        'credential_breach_days_before': (90, 365),
    },

    'SEQUESTRO_RELAMPAGO': {
        'name': 'Sequestro Relâmpago',
        'description': (
            'Vítima forçada sob coerção física a transferir dinheiro em tempo real. '
            'Padrão: device legítimo, localização estranha (rua, veículo), '
            'múltiplas transferências grandes em sequência curta, active_call=True, '
            'touch_pressure alta (coerção). Sinal FALSA_CENTRAL overlap forte.'
        ),
        'characteristics': {
            'value_anomaly': 'HIGH',
            'new_beneficiary_prob': 0.70,
            'velocity': 'MEDIUM',
            'time_anomaly': 'HIGH',               # Noite / madrugada
            'location_anomaly': 'LOW',            # Vítima está "em algum lugar" — pode ser distante
            'device_anomaly': 'NONE',             # Dispositivo legítimo
            'channel_preference': ['MOBILE_APP', 'WEB_BANKING'],
            'type_preference': ['PIX', 'TED'],
            'amount_multiplier': (2.0, 8.0),
            'transaction_burst': (2, 6),          # Múltiplas transferências
            'pix_key_type': ['CPF', 'PHONE', 'RANDOM'],
        },
        'prevalence': 0.02,
        'fraud_score_base': 0.60,                 # Operado pela vítima = difícil detectar
        'detection_delay_days': (1, 3),
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
