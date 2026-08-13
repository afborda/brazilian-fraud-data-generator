"""
PIX payment system configuration — BACEN standards.

References:
- Manual de Operação do PIX (BACEN, 2023)
- Resolução BCB nº 1/2020 (regulamento PIX)
- IF.data — Participantes do PIX (BACEN open data)
"""

import hashlib
import random
from typing import Optional

from ..validators.cpf import generate_valid_cpf

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

# Devolução em PIX legítimo: BE08 (chave PIX errada, pagamento duplicado) e
# REFU (recebedor recusa um valor inesperado) acontecem sem qualquer fraude
# envolvida — só FR01/MD06 carregam a alegação de golpe, por isso ficam de
# fora daqui. É o mesmo campo `motivo_devolucao_med` que a fraude usa; a
# diferença é a taxa e o motivo, não a existência do campo.
MOTIVO_DEVOLUCAO_LEGIT_LIST = ["BE08", "REFU"]
MOTIVO_DEVOLUCAO_LEGIT_WEIGHTS = [65, 35]

# ── ISPB map — participantes do PIX (principais bancos) ──────────────────────
# Source: BACEN IF.data, updated 2024-06
# Format: nome_curto → ISPB (8 digits, zero-padded)

ISPB_MAP = {
    "BB":           "00000000",  # Banco do Brasil
    "BRB":          "00000208",  # Banco de Brasília
    "BANRISUL":     "92702067",  # Banco do Estado do RS (CNPJ 92.702.067)
    "SANTANDER":    "90400888",
    "CAIXA":        "36098519",  # Caixa Econômica Federal
    "BRADESCO":     "60746948",
    "ITAU":         "60701190",  # Itaú Unibanco
    "NUBANK":       "18236120",
    "INTER":        "00416968",
    "C6":           "31872495",
    "ORIGINAL":     "92894922",  # Banco Original (CNPJ 92.894.922)
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

# Deduplicated: NEXT shares Bradesco's ISPB (it was folded back into Bradesco in
# 2022). Keeping the duplicate here gave that ISPB double weight during sampling.
# NOTE (known gap): sampling over this list is still uniform, so Modal and Getnet
# are as likely as Nubank and Itaú. Real PIX endpoints concentrate in ~6
# institutions — needs an ISPB_WEIGHTS table proportional to PIX share.
ISPB_LIST = list(dict.fromkeys(ISPB_MAP.values()))
ISPB_NAMES = list(ISPB_MAP.keys())

# Pre-built reverse map: ISPB → name. First name wins, so a shared ISPB resolves
# to the parent institution (60746948 → BRADESCO, not NEXT).
_ISPB_TO_NAME: dict[str, str] = {}
for _name, _ispb in ISPB_MAP.items():
    _ISPB_TO_NAME.setdefault(_ispb, _name)


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


# ── Counterparty pool ────────────────────────────────────────────────────────
# Each PIX used to hash a freshly generated CPF, so 119,182 legitimate PIX
# produced 119,179 distinct recipients: the maximum frequency was 2, and that
# was a birthday collision. Two consequences:
#
#   * `new_beneficiary` sat at 97.4% of legitimate traffic, because the
#     counterparty was in fact always new; and
#   * every graph feature (degree, PageRank, community, recurrence) was
#     constant or noise, since the transaction graph had no repeated edge.
#
# Real P2P PIX concentrates on a small, stable set — family, rent, the school,
# the same corner shop — with a long tail beyond it. The pool is derived from
# the customer id, so it needs no extra state and stays stable across batches
# and workers.
_POOL_SIZE = 14

# Zipf-like weights: the top counterparty takes far more volume than the 14th.
_POOL_WEIGHTS = [1.0 / (i + 1) ** 1.1 for i in range(_POOL_SIZE)]

# Share of transfers that go outside the pool entirely (a one-off purchase, a
# new landlord, a marketplace seller).
from .calibration import rate as _rate

_ONE_OFF_SHARE = _rate("counterparty.one_off_share_legit")


def counterparty_hash(customer_id: str, is_fraud: bool) -> str:
    """Hash of the recipient CPF, drawn from this customer's counterparty pool.

    Fraud mostly pays someone the customer has never paid before, which is a
    genuine signal — but it must be a tendency, not a certainty: an invoice
    scam redirects a payment the victim makes every month, landing on a
    familiar counterparty.
    """
    one_off = _ONE_OFF_SHARE if not is_fraud else _rate("counterparty.one_off_share_fraud")
    if random.random() < one_off:
        return hashlib.sha256(generate_valid_cpf().encode()).hexdigest()
    idx = random.choices(range(_POOL_SIZE), weights=_POOL_WEIGHTS, k=1)[0]
    return hashlib.sha256(f"{customer_id}|counterparty|{idx}".encode()).hexdigest()
