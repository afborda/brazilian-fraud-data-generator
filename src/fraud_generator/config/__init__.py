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

from .rideshare import (
    RIDESHARE_APPS,
    APPS_LIST,
    APPS_WEIGHTS,
    POIS_POR_CAPITAL,
    CAPITAL_POR_ESTADO,
    POI_TYPES,
    CORES_VEICULOS,
    VEICULOS_POPULARES,
    VEHICLE_YEARS,
    CATEGORY_LEVELS,
    CATEGORY_HIERARCHY,
    TAXAS_POR_CATEGORIA,
    SURGE_POR_HORARIO,
    PLATFORM_FEE_PERCENT,
    RIDE_STATUS,
    RIDE_STATUS_WEIGHTS,
    FINAL_STATUS_LIST,
    FINAL_STATUS_WEIGHTS,
    CANCELLATION_REASONS,
    RIDESHARE_FRAUD_TYPES,
    FRAUD_TYPES_LIST as RIDESHARE_FRAUD_TYPES_LIST,
    FRAUD_TYPES_WEIGHTS as RIDESHARE_FRAUD_TYPES_WEIGHTS,
    PAYMENT_METHODS as RIDESHARE_PAYMENT_METHODS,
    PAYMENT_METHODS_LIST as RIDESHARE_PAYMENT_METHODS_LIST,
    PAYMENT_METHODS_WEIGHTS as RIDESHARE_PAYMENT_METHODS_WEIGHTS,
    get_app_categories,
    get_pois_for_state,
    get_pois_for_city,
    get_random_vehicle,
    get_vehicle_for_category,
    get_surge_multiplier,
    calculate_base_fare,
    get_random_cancellation_reason,
    get_random_app,
    get_random_category_for_app,
    get_random_payment_method as get_random_rideshare_payment_method,
    get_random_fraud_type as get_random_rideshare_fraud_type,
    get_random_final_status,
    get_available_states,
)

from .weather import (
    REGIOES,
    STATE_TO_REGION,
    WEATHER_CONDITIONS,
    WEATHER_CONDITIONS_LIST,
    TEMP_POR_REGIAO,
    PROB_CHUVA_POR_MES,
    get_region_for_state,
    get_season,
    generate_weather,
    get_surge_impact,
    get_weather_description,
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
    # Rideshare
    'RIDESHARE_APPS', 'APPS_LIST', 'APPS_WEIGHTS',
    'POIS_POR_CAPITAL', 'CAPITAL_POR_ESTADO', 'POI_TYPES',
    'CORES_VEICULOS', 'VEICULOS_POPULARES', 'VEHICLE_YEARS',
    'CATEGORY_LEVELS', 'CATEGORY_HIERARCHY',
    'TAXAS_POR_CATEGORIA', 'SURGE_POR_HORARIO', 'PLATFORM_FEE_PERCENT',
    'RIDE_STATUS', 'RIDE_STATUS_WEIGHTS', 'FINAL_STATUS_LIST', 'FINAL_STATUS_WEIGHTS',
    'CANCELLATION_REASONS', 'RIDESHARE_FRAUD_TYPES',
    'RIDESHARE_FRAUD_TYPES_LIST', 'RIDESHARE_FRAUD_TYPES_WEIGHTS',
    'RIDESHARE_PAYMENT_METHODS', 'RIDESHARE_PAYMENT_METHODS_LIST', 'RIDESHARE_PAYMENT_METHODS_WEIGHTS',
    'get_app_categories', 'get_pois_for_state', 'get_pois_for_city',
    'get_random_vehicle', 'get_vehicle_for_category',
    'get_surge_multiplier', 'calculate_base_fare',
    'get_random_cancellation_reason', 'get_random_app', 'get_random_category_for_app',
    'get_random_rideshare_payment_method', 'get_random_rideshare_fraud_type',
    'get_random_final_status', 'get_available_states',
    # Weather
    'REGIOES', 'STATE_TO_REGION',
    'WEATHER_CONDITIONS', 'WEATHER_CONDITIONS_LIST',
    'TEMP_POR_REGIAO', 'PROB_CHUVA_POR_MES',
    'get_region_for_state', 'get_season', 'generate_weather',
    'get_surge_impact', 'get_weather_description',
]
