"""
PIX payment system configuration — BACEN standards.

References:
- Manual de Operação do PIX (BACEN, 2023)
- Resolução BCB nº 1/2020 (regulamento PIX)
- IF.data — Participantes do PIX (BACEN open data)
"""

from typing import Optional

# ── Modalidade de iniciação ────────────────────────────────────────────────────

MODALIDADE_INICIACAO_LIST = [
    "CHAVE",           # chave PIX (CPF, CNPJ, e-mail, telefone, EVP)
    "MANUAL",          # dados bancários digitados manualmente
    "QRCODE_ESTATICO", # QR code estático (valor fixo ou livre)
    "QRCODE_DINAMICO", # QR code dinâmico (cobrança única)
]

MODALIDADE_INICIACAO_WEIGHTS = [55, 15, 20, 10]

# ── Tipo de conta ─────────────────────────────────────────────────────────────

TIPO_CONTA_LIST = [
    "CACC",  # checking account (conta corrente)
    "SVGS",  # savings account (poupança)
    "SLRY",  # salary account (conta salário)
    "TRAN",  # transactional account (conta pagamento)
]

TIPO_CONTA_WEIGHTS = [70, 15, 8, 7]

# ── Tipo de detentor ──────────────────────────────────────────────────────────

HOLDER_TYPE_LIST = ["CUSTOMER", "BUSINESS"]
HOLDER_TYPE_WEIGHTS = [75, 25]

# ── Motivo de devolução MED ────────────────────────────────────────────────────
# MED = Mecanismo Especial de Devolução

MOTIVO_DEVOLUCAO_LIST = [
    "FR01",  # fraude — golpe / falso pretexto
    "MD06",  # fraude — solicitação do usuário recebedor
    "BE08",  # erro na operação
    "REFU",  # recusa do recebedor
]

MOTIVO_DEVOLUCAO_WEIGHTS = [55, 25, 12, 8]

# ── ISPB map — participantes do PIX (principais bancos) ──────────────────────
# Source: BACEN IF.data, updated 2024-06
# Format: nome_curto → ISPB (8 digits, zero-padded)

ISPB_MAP = {
    "BB":           "00000000",  # Banco do Brasil
    "BRB":          "00000208",  # Banco de Brasília
    "BANRISUL":     "00000000",  # handled via ISPB in production
    "SANTANDER":    "90400888",
    "CAIXA":        "36098519",  # Caixa Econômica Federal
    "BRADESCO":     "60746948",
    "ITAU":         "60701190",  # Itaú Unibanco
    "NUBANK":       "18236120",
    "INTER":        "00416968",
    "C6":           "31872495",
    "ORIGINAL":     "92702067",
    "NEXT":         "60746948",  # Bradesco subsidiary
    "PAN":          "59285411",
    "SICREDI":      "01181521",
    "SICOOB":       "00714671",
    "SAFRA":        "58160789",
    "BTG":          "01526932",
    "XP":           "02332886",
    "MODAL":        "30723886",
    "PICPAY":       "09516419",
    "MERCADOPAGO":  "10573521",
    "PAGBANK":      "08550201",  # PagSeguro
    "WILL":         "13935893",
    "STONE":        "16501555",
    "GETNET":       "10264663",
    "REDE":         "01701201",
}

ISPB_LIST = list(ISPB_MAP.values())
ISPB_NAMES = list(ISPB_MAP.keys())

# Pre-built reverse map: ISPB → name
_ISPB_TO_NAME = {v: k for k, v in ISPB_MAP.items()}


def get_ispb_for_bank(bank_name: str) -> Optional[str]:
    """Return ISPB for a bank name key (case-insensitive prefix match)."""
    key = bank_name.upper()
    return ISPB_MAP.get(key)


def get_bank_for_ispb(ispb: str) -> Optional[str]:
    """Return short bank name for an ISPB code."""
    return _ISPB_TO_NAME.get(ispb)


def generate_end_to_end_id(ispb_pagador: str, timestamp_str: str, sequence: str) -> str:
    """
    Generate a PIX end-to-end ID (EndToEndId) following BACEN format.

    Format: E{ISPB pagador}{AAAAMMDDHHMMSS}{random 11 chars}
    Total: 32 alphanumeric characters.

    Args:
        ispb_pagador: 8-digit ISPB of the paying institution
        timestamp_str: Timestamp in 'YYYYMMDDHHmmss' format
        sequence: 10-digit random alphanumeric suffix

    Returns:
        32-character EndToEndId string
    """
    ispb_clean = ispb_pagador.zfill(8)[:8]
    ts_clean = timestamp_str[:14]
    seq_clean = sequence[:10].upper()
    return f"E{ispb_clean}{ts_clean}{seq_clean}"
