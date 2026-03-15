"""
PIX enricher — fills in BACEN pacs.008 fields for PIX transactions.

Extracted from TransactionGenerator._add_type_specific_fields (PIX branch) and
_apply_fraud_pattern (channel_preference upgrade to PIX).

For non-PIX transactions all PIX fields are set to None.
For PIX transactions the 7 BACEN core fields + TPRD3 Fase-2 fields are filled.
"""

import hashlib
from typing import Any, Dict

from .base import EnricherProtocol, GeneratorBag
from ..config.pix import (
    MODALIDADE_INICIACAO_LIST, MODALIDADE_INICIACAO_WEIGHTS,
    TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS,
    HOLDER_TYPE_LIST, HOLDER_TYPE_WEIGHTS,
    generate_end_to_end_id,
    MOTIVO_DEVOLUCAO_LIST, MOTIVO_DEVOLUCAO_WEIGHTS,
)
from ..validators.cpf import generate_valid_cpf


class PIXEnricher:
    """
    Enriches PIX transactions with BACEN pacs.008 fields.

    Picks up any transaction whose type is 'PIX' (whether set by the base
    builder or by FraudEnricher's channel override) and fills the mandatory
    PIX/BACEN columns.

    Also handles TPRD3: MED devolution injection for confirmed fraud PIX txns.
    """

    def enrich(self, tx: Dict[str, Any], bag: GeneratorBag) -> None:
        tx_type = tx.get("type")

        if tx_type != "PIX":
            # Ensure all PIX columns are present to keep a stable schema
            _pix_nulls = {
                "end_to_end_id": None,
                "ispb_pagador": None,
                "ispb_recebedor": None,
                "tipo_conta_pagador": None,
                "tipo_conta_recebedor": None,
                "holder_type_recebedor": None,
                "modalidade_iniciacao": None,
                "cpf_hash_pagador": None,
                "cpf_hash_recebedor": None,
                "pacs_status": None,
                "is_devolucao": None,
                "motivo_devolucao_med": None,
            }
            for k, v in _pix_nulls.items():
                tx.setdefault(k, v)
            return

        buf = bag.buf

        # Only fill if not already populated (FraudEnricher may have set some)
        if not tx.get("end_to_end_id"):
            ispb_pag = buf.next_choice(bag.ispb_list)
            ispb_rec = buf.next_choice(bag.ispb_list)
            ts_str = str(tx.get("timestamp", ""))[:14].replace("-", "").replace("T", "").replace(":", "")
            seq = buf.next_hash16()[:10]
            e2e_id = generate_end_to_end_id(ispb_pag, ts_str, seq)
            customer_id = tx.get("customer_id", "")
            customer_cpf = tx.get("_customer_cpf")  # internal key, stripped later

            tx.update({
                "end_to_end_id": e2e_id,
                "ispb_pagador": ispb_pag,
                "ispb_recebedor": ispb_rec,
                "tipo_conta_pagador": buf.next_weighted("tipo_conta", TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS),
                "tipo_conta_recebedor": buf.next_weighted("tipo_conta", TIPO_CONTA_LIST, TIPO_CONTA_WEIGHTS),
                "holder_type_recebedor": buf.next_weighted("holder", HOLDER_TYPE_LIST, HOLDER_TYPE_WEIGHTS),
                "modalidade_iniciacao": buf.next_weighted("modalidade", MODALIDADE_INICIACAO_LIST, MODALIDADE_INICIACAO_WEIGHTS),
                "cpf_hash_pagador": hashlib.sha256((customer_cpf or customer_id).encode()).hexdigest(),
                "cpf_hash_recebedor": hashlib.sha256(generate_valid_cpf().encode()).hexdigest(),
                "pacs_status": buf.next_weighted("pacs_status", ["ACSC", "RJCT", "PDNG"], [92, 6, 2]),
                "is_devolucao": False,
                "motivo_devolucao_med": None,
            })

        # TPRD3: MED devolution — 30% of fraud PIX transactions
        if (
            bag.is_fraud
            and tx.get("is_devolucao") is False
            and buf.next_float() < 0.30
        ):
            tx["is_devolucao"] = True
            tx["motivo_devolucao_med"] = buf.next_weighted(
                "motivo_devolucao", MOTIVO_DEVOLUCAO_LIST, MOTIVO_DEVOLUCAO_WEIGHTS
            )
