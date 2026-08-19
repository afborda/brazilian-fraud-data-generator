"""
Configuration module for transaction types, fraud types, and payment methods.
"""

from typing import Dict

# Transaction types — calibrated against BCB payment statistics 2024
# PIX: 65% of all digital transactions (BCB Nota Imprensa Q4 2024)
# Cards: ~22% combined (Relatório de Sistemas de Pagamento BCB 2024)
# TED: ~7% (declining but still significant for high-value B2B)
# Boleto: ~5% (declining with PIX growth)
TRANSACTION_TYPES = {
    'PIX': 65,            # 65% - Dominant channel (BCB 2024: 4B+ tx/month)
    'CREDIT_CARD': 14,    # 14% - Reduced: cards losing share to PIX
    'DEBIT_CARD': 8,      # 8%  - Reduced: contactless PIX replacing debit
    'BOLETO': 5,          # 5%  - BCB 2024: declining with PIX growth
    'TED': 5,             # 5%  - BCB 2024: ~7% (high-value B2B transfers)
    'AUTO_DEBIT': 1,      # 1%  - Recurring bills
    'WITHDRAWAL': 1,      # 1%  - ATM cash (sharply declining)
    'MOBILE_TOPUP': 1,    # 1%  - Mobile phone recharge
    # DOC removed — BCB discontinued in 2024
}

TX_TYPES_LIST = list(TRANSACTION_TYPES.keys())
TX_TYPES_WEIGHTS = list(TRANSACTION_TYPES.values())

# Channels with realistic weights
CHANNELS = {
    'MOBILE_APP': 60,    # 60% - Mobile dominates
    'WEB_BANKING': 25,   # 25% - Desktop banking
    'ATM': 8,            # 8%  - ATM (decreasing)
    'BRANCH': 5,         # 5%  - Branch (rare)
    'WHATSAPP_PAY': 2,   # 2%  - WhatsApp payments
}

CHANNELS_LIST = list(CHANNELS.keys())
CHANNELS_WEIGHTS = list(CHANNELS.values())

# Channel weights CONDITIONED on transaction type.
#
# `type` and `channel` used to be drawn independently (one weighted choice
# from TX_TYPES, one unrelated weighted choice from CHANNELS), which builds
# combinations the real product cannot produce: WITHDRAWAL is cash out of a
# physical terminal — there is no "WITHDRAWAL via WEB_BANKING" — yet with
# independent sampling ~35% of generated withdrawals landed on MOBILE_APP or
# WEB_BANKING. PIX at ATM/BRANCH also came out far more often than the
# minor real channel (Pix Saque/Troco terminals) justifies. Cramér's V
# between the independently-sampled columns measured 0.082 on a 268k batch —
# essentially unrelated, when the two are causally linked in reality.
#
# Each entry restricts and re-weights CHANNELS for one instrument, built from
# how that instrument is actually accessed in a Brazilian bank/PSP app.
# WHATSAPP_PAY is omitted for instruments the product does not support there
# (BOLETO, TED, WITHDRAWAL, AUTO_DEBIT, MOBILE_TOPUP-only-app). Types absent
# from this table (none today) fall back to the unconditional CHANNELS table.
CHANNEL_WEIGHTS_BY_TYPE = {
    'WITHDRAWAL':   {'ATM': 88, 'BRANCH': 12},
    'PIX':          {'MOBILE_APP': 78, 'WEB_BANKING': 15, 'WHATSAPP_PAY': 5, 'ATM': 1.5, 'BRANCH': 0.5},
    'CREDIT_CARD':  {'MOBILE_APP': 55, 'WEB_BANKING': 30, 'ATM': 8, 'BRANCH': 7},
    'DEBIT_CARD':   {'MOBILE_APP': 55, 'WEB_BANKING': 25, 'ATM': 15, 'BRANCH': 5},
    'BOLETO':       {'MOBILE_APP': 45, 'WEB_BANKING': 30, 'ATM': 15, 'BRANCH': 10},
    'TED':          {'MOBILE_APP': 40, 'WEB_BANKING': 40, 'BRANCH': 15, 'ATM': 5},
    'AUTO_DEBIT':   {'WEB_BANKING': 50, 'MOBILE_APP': 35, 'BRANCH': 15},
    'MOBILE_TOPUP': {'MOBILE_APP': 70, 'WEB_BANKING': 20, 'WHATSAPP_PAY': 10},
}


def get_channel_weights_for_type(tx_type: str) -> Dict[str, float]:
    """Return {channel: weight} valid for *tx_type*.

    Falls back to the unconditional CHANNELS table for any type not covered
    above, so a new transaction type added later degrades to the old
    (independent) behaviour instead of raising.
    """
    return CHANNEL_WEIGHTS_BY_TYPE.get(tx_type) or dict(CHANNELS)

# Fraud types with realistic distribution
# DEPRECATED: Use fraud_patterns.py for contextualized fraud patterns
# Kept for backward compatibility only
FRAUD_TYPES_LEGACY = {
    'ENGENHARIA_SOCIAL': 20,    # Social engineering - most common
    'CONTA_TOMADA': 15,         # Account takeover
    'CARTAO_CLONADO': 14,       # Cloned card
    'IDENTIDADE_FALSA': 10,     # Identity fraud
    'AUTOFRAUDE': 8,            # First-party fraud
    'FRAUDE_AMIGAVEL': 5,       # Friendly fraud
    'LAVAGEM_DINHEIRO': 4,      # Money laundering
    'TRIANGULACAO': 3,          # Triangulation fraud
    'GOLPE_WHATSAPP': 8,        # WhatsApp scams (fake support, fake relatives)
    'PHISHING': 6,              # Fake emails/sites to steal credentials
    'SIM_SWAP': 3,              # SIM card swap fraud
    'BOLETO_FALSO': 2,          # Fake bank slips
    'QR_CODE_FALSO': 2,         # Fake PIX QR codes
}

# NEW: Import from fraud_patterns (OTIMIZAÇÃO 2: Fraud Contextualization)
try:
    from .fraud_patterns import FRAUD_PATTERNS, FRAUD_TYPES_LIST as FP_LIST, FRAUD_TYPES_WEIGHTS as FP_WEIGHTS
    FRAUD_TYPES_LIST = FP_LIST
    FRAUD_TYPES_WEIGHTS = FP_WEIGHTS
    # Create FRAUD_TYPES dict for backward compatibility
    FRAUD_TYPES = {k: int(v * 100) for k, v in zip(FP_LIST, FP_WEIGHTS)}
except ImportError:
    # Fallback to legacy if fraud_patterns not available
    FRAUD_TYPES = FRAUD_TYPES_LEGACY
    FRAUD_TYPES_LIST = list(FRAUD_TYPES_LEGACY.keys())
    FRAUD_TYPES_WEIGHTS = list(FRAUD_TYPES_LEGACY.values())

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

# Transaction status codes
TRANSACTION_STATUS = {
    'APPROVED': 'Transaction approved',
    'DECLINED': 'Transaction declined',
    'PENDING': 'Transaction pending',
    'BLOCKED': 'Transaction blocked',
    'CANCELLED': 'Transaction cancelled',
    'REVERSED': 'Transaction reversed',
}

# Refusal reasons
REFUSAL_REASONS = [
    'INSUFFICIENT_BALANCE',
    'FRAUD_SUSPECT',
    'LIMIT_EXCEEDED',
    'CARD_BLOCKED',
    'CVV_ERROR',
    'CARD_EXPIRED',
    'INVALID_PIN',
    'ACCOUNT_BLOCKED',
]

# Card entry methods
CARD_ENTRY_METHODS = {
    'CHIP': 40,
    'CONTACTLESS': 35,
    'MANUAL': 20,
    'MAGNETIC': 5,
}

CARD_ENTRY_LIST = list(CARD_ENTRY_METHODS.keys())
CARD_ENTRY_WEIGHTS = list(CARD_ENTRY_METHODS.values())

# Installment options with weights
INSTALLMENT_OPTIONS = {
    1: 50,
    2: 10,
    3: 10,
    4: 5,
    5: 5,
    6: 10,
    10: 5,
    12: 5,
}

INSTALLMENT_LIST = list(INSTALLMENT_OPTIONS.keys())
INSTALLMENT_WEIGHTS = list(INSTALLMENT_OPTIONS.values())


# ─── Multiplicador de valor por tipo de transação ────────────────────────────
# O valor base sai da faixa do MCC, que descreve o *estabelecimento*, não o
# meio de pagamento. Sem este ajuste, TED e PIX saíam com a mesma mediana:
# medido antes da correção, TED tinha mediana de R$ 244,96 — um TED de R$ 245
# não existe na prática desde 2021, porque o TED cobra tarifa e sobreviveu ao
# PIX justamente por carregar o alto valor (B2B, imóveis, veículos).
#
# Aplicado como fator sobre o valor amostrado. Ordens de grandeza derivadas do
# ticket médio relativo por instrumento (BCB/Febraban 2024).
#
# ATENÇÃO: são fatores de ordem de grandeza, não calibração fina. Substituir por
# distribuição própria por instrumento quando houver dado real de referência.
TYPE_VALUE_MULTIPLIER: dict[str, float] = {
    'TED':           15.0,   # canal de alto valor
    'BOLETO':         3.0,   # contas, mensalidades, fornecedores
    'AUTO_DEBIT':     1.2,   # contas de consumo e assinaturas
    'WITHDRAWAL':     1.5,   # saque em espécie
    'PIX':            1.0,   # referência
    'CREDIT_CARD':    1.0,
    'DEBIT_CARD':     0.9,
    'MOBILE_TOPUP':   0.15,  # recarga de celular
}

DEFAULT_TYPE_VALUE_MULTIPLIER: float = 1.0


def get_value_multiplier_for_type(tx_type: str | None) -> float:
    """Return the value multiplier for a transaction type (1.0 when unknown)."""
    if not tx_type:
        return DEFAULT_TYPE_VALUE_MULTIPLIER
    return TYPE_VALUE_MULTIPLIER.get(tx_type, DEFAULT_TYPE_VALUE_MULTIPLIER)
