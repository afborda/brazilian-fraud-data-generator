"""
Configuration module for Brazilian bank data.
Contains bank codes, names, types and market share weights.
"""

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
    '623': {'nome': 'Banco Pan', 'tipo': 'privado', 'peso': 2},
    '121': {'nome': 'Agibank', 'tipo': 'digital', 'peso': 1},
    '707': {'nome': 'Daycoval', 'tipo': 'privado', 'peso': 1},
    '318': {'nome': 'BMG', 'tipo': 'privado', 'peso': 1},
}

# Pre-computed lists for weighted random selection
BANK_CODES = list(BANKS.keys())
BANK_WEIGHTS = [BANKS[code]['peso'] for code in BANK_CODES]


def get_bank_info(code: str) -> dict:
    """Get bank information by code."""
    return BANKS.get(code, {'nome': 'Banco Desconhecido', 'tipo': 'outro', 'peso': 1})


def get_bank_name(code: str) -> str:
    """Get bank name by code."""
    return BANKS.get(code, {}).get('nome', 'Banco Desconhecido')


def get_bank_type(code: str) -> str:
    """Get bank type by code."""
    return BANKS.get(code, {}).get('tipo', 'outro')
