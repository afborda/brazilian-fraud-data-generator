"""
Configuration module for Brazilian bank data.
Contains bank codes, names, types and market share weights.
"""

# Brazilian bank codes with names (Código COMPE/ISPB) - Top 25 banks by market share
BANKS = {
    '001': {'name': 'Banco do Brasil', 'type': 'public', 'weight': 15},
    '033': {'name': 'Santander Brasil', 'type': 'private', 'weight': 10},
    '104': {'name': 'Caixa Econômica Federal', 'type': 'public', 'weight': 14},
    '237': {'name': 'Bradesco', 'type': 'private', 'weight': 12},
    '341': {'name': 'Itaú Unibanco', 'type': 'private', 'weight': 15},
    '260': {'name': 'Nubank', 'type': 'digital', 'weight': 10},
    '077': {'name': 'Banco Inter', 'type': 'digital', 'weight': 5},
    '336': {'name': 'C6 Bank', 'type': 'digital', 'weight': 4},
    '290': {'name': 'PagBank', 'type': 'digital', 'weight': 3},
    '380': {'name': 'PicPay', 'type': 'digital', 'weight': 2},
    '323': {'name': 'Mercado Pago', 'type': 'digital', 'weight': 2},
    '403': {'name': 'Cora', 'type': 'digital', 'weight': 1},
    '212': {'name': 'Banco Original', 'type': 'digital', 'weight': 1},
    '756': {'name': 'Sicoob', 'type': 'cooperative', 'weight': 2},
    '748': {'name': 'Sicredi', 'type': 'cooperative', 'weight': 2},
    '422': {'name': 'Safra', 'type': 'private', 'weight': 1},
    '070': {'name': 'BRB', 'type': 'public', 'weight': 1},
    # Additional banks
    '208': {'name': 'BTG Pactual', 'type': 'private', 'weight': 2},
    '655': {'name': 'Neon', 'type': 'digital', 'weight': 2},
    '280': {'name': 'Will Bank', 'type': 'digital', 'weight': 1},
    '623': {'name': 'Banco Pan', 'type': 'private', 'weight': 2},
    '121': {'name': 'Agibank', 'type': 'digital', 'weight': 1},
    '707': {'name': 'Daycoval', 'type': 'private', 'weight': 1},
    '318': {'name': 'BMG', 'type': 'private', 'weight': 1},
}

# Pre-computed lists for weighted random selection
BANK_CODES = list(BANKS.keys())
BANK_WEIGHTS = [BANKS[code]['weight'] for code in BANK_CODES]


def get_bank_info(code: str) -> dict:
    """Get bank information by code."""
    return BANKS.get(code, {'name': 'Unknown Bank', 'type': 'other', 'weight': 1})


def get_bank_name(code: str) -> str:
    """Get bank name by code."""
    return BANKS.get(code, {}).get('name', 'Unknown Bank')


def get_bank_type(code: str) -> str:
    """Get bank type by code."""
    return BANKS.get(code, {}).get('type', 'other')
