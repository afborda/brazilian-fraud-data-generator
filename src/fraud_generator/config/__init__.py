"""
Configuration package for Brazilian Fraud Data Generator.
Contains all static configuration data.
"""

from .banks import (
    BANKS,
    BANK_CODES,
    BANK_WEIGHTS,
    get_bank_info,
    get_bank_name,
    get_bank_type,
)

from .transactions import (
    TRANSACTION_TYPES,
    TX_TYPES_LIST,
    TX_TYPES_WEIGHTS,
    CHANNELS,
    CHANNELS_LIST,
    CHANNELS_WEIGHTS,
    FRAUD_TYPES,
    FRAUD_TYPES_LIST,
    FRAUD_TYPES_WEIGHTS,
    PIX_KEY_TYPES,
    PIX_TYPES_LIST,
    PIX_TYPES_WEIGHTS,
    CARD_BRANDS,
    BRANDS_LIST,
    BRANDS_WEIGHTS,
    TRANSACTION_STATUS,
    REFUSAL_REASONS,
    CARD_ENTRY_METHODS,
    CARD_ENTRY_LIST,
    CARD_ENTRY_WEIGHTS,
    INSTALLMENT_OPTIONS,
    INSTALLMENT_LIST,
    INSTALLMENT_WEIGHTS,
)

from .merchants import (
    MCC_CODES,
    MCC_LIST,
    MCC_WEIGHTS,
    MERCHANTS_BY_MCC,
    get_mcc_info,
    get_merchants_for_mcc,
    get_risk_level,
)

from .geography import (
    ESTADOS_BR,
    ESTADOS_LIST,
    ESTADOS_WEIGHTS,
    CIDADES_POR_ESTADO,
    BRAZILIAN_IP_PREFIXES,
    get_state_info,
    get_state_coordinates,
    get_cities_for_state,
    get_state_name,
)

from .devices import (
    DEVICE_TYPES,
    DEVICE_TYPES_LIST,
    DEVICE_TYPES_WEIGHTS,
    DEVICE_MANUFACTURERS,
    DEVICE_MODELS,
    OS_BY_DEVICE_TYPE,
    get_manufacturers_for_device_type,
    get_models_for_manufacturer,
    get_os_for_device_type,
    get_device_category,
)

__all__ = [
    # Banks
    'BANKS', 'BANK_CODES', 'BANK_WEIGHTS',
    'get_bank_info', 'get_bank_name', 'get_bank_type',
    # Transactions
    'TRANSACTION_TYPES', 'TX_TYPES_LIST', 'TX_TYPES_WEIGHTS',
    'CHANNELS', 'CHANNELS_LIST', 'CHANNELS_WEIGHTS',
    'FRAUD_TYPES', 'FRAUD_TYPES_LIST', 'FRAUD_TYPES_WEIGHTS',
    'PIX_KEY_TYPES', 'PIX_TYPES_LIST', 'PIX_TYPES_WEIGHTS',
    'CARD_BRANDS', 'BRANDS_LIST', 'BRANDS_WEIGHTS',
    'TRANSACTION_STATUS', 'REFUSAL_REASONS',
    'CARD_ENTRY_METHODS', 'CARD_ENTRY_LIST', 'CARD_ENTRY_WEIGHTS',
    'INSTALLMENT_OPTIONS', 'INSTALLMENT_LIST', 'INSTALLMENT_WEIGHTS',
    # Merchants
    'MCC_CODES', 'MCC_LIST', 'MCC_WEIGHTS', 'MERCHANTS_BY_MCC',
    'get_mcc_info', 'get_merchants_for_mcc', 'get_risk_level',
    # Geography
    'ESTADOS_BR', 'ESTADOS_LIST', 'ESTADOS_WEIGHTS',
    'CIDADES_POR_ESTADO', 'BRAZILIAN_IP_PREFIXES',
    'get_state_info', 'get_state_coordinates', 'get_cities_for_state', 'get_state_name',
    # Devices
    'DEVICE_TYPES', 'DEVICE_TYPES_LIST', 'DEVICE_TYPES_WEIGHTS',
    'DEVICE_MANUFACTURERS', 'DEVICE_MODELS', 'OS_BY_DEVICE_TYPE',
    'get_manufacturers_for_device_type', 'get_models_for_manufacturer',
    'get_os_for_device_type', 'get_device_category',
]
