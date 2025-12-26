"""
Configuration module for transaction types, fraud types, and payment methods.
"""

# Transaction types (PIX weighted higher - realistic for Brazil 2024)
TRANSACTION_TYPES = {
    'PIX': 42,            # 42% - PIX dominates Brazil
    'CREDIT_CARD': 22,    # 22% - Credit card
    'DEBIT_CARD': 13,     # 13% - Debit card
    'BOLETO': 7,          # 7%  - Bank slip (Brazilian term)
    'TED': 3,             # 3%  - Wire transfer (Brazilian term)
    'WITHDRAWAL': 3,      # 3%  - Cash withdrawal (decreasing)
    'DOC': 1,             # 1%  - DOC transfer (Brazilian term, being phased out)
    'AUTO_DEBIT': 5,      # 5%  - Automatic debit (bills, subscriptions)
    'MOBILE_TOPUP': 4,    # 4%  - Mobile phone top-up
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
