"""Single registry for every rate that shapes fraud/legit overlap.

These numbers decide how hard the generated data is. They were spread across
six modules as bare literals, which had two costs: nobody could see the whole
calibration at once, and there was no way to tell an estimate from a measured
value — so a plausible guess and a figure taken from BCB statistics looked
identical in the code.

Each entry here carries its **provenance**:

* ``ESTIMATE`` — reasoned from domain knowledge, not measured. Defensible, but
  it is a hypothesis. Most entries are this today.
* ``CALIBRATED`` — derived from a real reference (public statistics or a data
  partner's aggregates), with the source named.

That distinction is the point. The audit that produced this module found the
product publishing "AUC-ROC 0.9991" as a quality badge when the number measured
label leakage. Replacing one unjustified number with another — picking rates
until the AUC lands where we want it — would repeat that mistake. So the rule
is: **an entry only becomes CALIBRATED when there is a source to name.**

## Applying real data

Aggregates are enough; no record-level data is needed. A histogram of amount by
instrument, fraud rate per type, or the age distribution of destination
accounts each let one or more entries move from ESTIMATE to CALIBRATED.

Overrides load from a JSON file, so a partner's figures can be applied without
touching code::

    FRAUDGEN_CALIBRATION=/path/to/calibration.json python generate.py ...

    {
      "dest_account_age.fraud_contamination": 0.41,
      "_sources": {"dest_account_age.fraud_contamination": "PSP parceiro, agregado 2026-Q2"}
    }

`report()` prints the current table with provenance, which is what should go in
front of a buyer asking how the data was calibrated.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

ESTIMATE = "ESTIMATE"
CALIBRATED = "CALIBRATED"


@dataclass(frozen=True)
class Rate:
    """One calibration constant with its provenance."""

    value: float
    provenance: str
    note: str
    source: Optional[str] = None


# ─── Registry ────────────────────────────────────────────────────────────────
# Keys are dotted: <subject>.<parameter>. Keep them stable — an override file
# written by a partner references them by name.

_RATES: Dict[str, Rate] = {
    # ── Contaminação cruzada entre as duas populações ────────────────────
    "dest_account_age.legit_contamination": Rate(
        0.09, ESTIMATE,
        "Conta de destino aberta há poucos dias recebendo transferência legítima. "
        "O Brasil abre milhões de contas digitais por mês e receber um PIX no "
        "primeiro dia é rotina.",
    ),
    "dest_account_age.fraud_contamination": Rate(
        0.30, ESTIMATE,
        "Fraude que cai em conta antiga: laranja comprada ou aliciada meses antes. "
        "Sem isso, idade de conta vira limiar perfeito.",
    ),
    "company_age.legit_contamination": Rate(
        0.10, ESTIMATE,
        "PJ de destino com menos de 90 dias em pagamento legítimo — MEI recém-aberto.",
    ),
    "company_age.fraud_contamination": Rate(
        0.28, ESTIMATE,
        "Lavagem através de empresa estabelecida, não de fachada recém-criada.",
    ),
    "device_age.legit_contamination": Rate(
        0.10, ESTIMATE,
        "Cliente legítimo em aparelho novo — troca de celular.",
    ),
    "device_age.fraud_contamination": Rate(
        0.30, ESTIMATE,
        "Fraudador operando de aparelho antigo, não de device recém-registrado.",
    ),
    "bot_score.legit_contamination": Rate(
        0.05, ESTIMATE,
        "Sessão legítima que pontua alto no detector de automação: leitor de tela, "
        "gerenciador de senha, RPA corporativo, usuário apressado.",
    ),
    "bot_score.fraud_contamination": Rate(
        0.22, ESTIMATE,
        "Automação que imita cadência humana bem o bastante para pontuar baixo.",
    ),
    # ── Formas de fraude que quebram heurística trivial ──────────────────
    "fraud.low_and_slow_share": Rate(
        0.32, ESTIMATE,
        "Fraudes que não fazem rajada e mantêm a velocity da sessão. Mula paciente "
        "de uma transferência por dia derrota regra de velocidade de propósito.",
    ),
    "fraud.decoy_share": Rate(
        0.032, ESTIMATE,
        "Registros legítimos gerados como decoy — carregam 3 a 6 traços da silhueta "
        "de fraude ao mesmo tempo. Dimensionado para decoys superarem a fraude real "
        "em ~2:1, que é o regime de um time de antifraude: a maioria dos alertas é "
        "falso positivo.",
    ),
    "fraud.new_beneficiary_prob": Rate(
        0.82, ESTIMATE,
        "Probabilidade de a fraude pagar contraparte inédita, para os tipos marcados. "
        "Abaixo de 1.0 porque golpe de boleto e ATO reaproveitam contraparte que a "
        "vítima já paga — é o que os torna difíceis.",
    ),
    # ── Grafo de contrapartes ────────────────────────────────────────────
    "counterparty.one_off_share_legit": Rate(
        0.18, ESTIMATE,
        "Transferências legítimas para fora do conjunto habitual: compra avulsa, "
        "novo locador, vendedor de marketplace.",
    ),
    "counterparty.one_off_share_fraud": Rate(
        0.80, ESTIMATE,
        "Fraude quase sempre paga alguém novo — mas não sempre.",
    ),
    # ── Marcadores de destino ────────────────────────────────────────────
    "mule.p_fraud_cashout_types": Rate(
        0.14, ESTIMATE,
        "Fraude de cash-out cujo destino JÁ CONSTA em lista de mula no momento "
        "da transação. Não é a fração que usa laranja — essa é a maioria — mas a "
        "fração já conhecida. Lista de mula é indicador atrasado: a conta entra "
        "depois que a fraude é reportada. Valor anterior (0,62) dava lift de "
        "180x sobre o legítimo e fazia o campo virar a feature dominante: se um "
        "banco soubesse o destino em 62% dos casos no ato, a fraude estaria "
        "resolvida.",
    ),
    "mule.p_fraud_other_types": Rate(
        0.06, ESTIMATE,
        "Demais tipos de fraude com destino já listado como mula.",
    ),
    # ── Ride-share ───────────────────────────────────────────────────────
    # MEDIÇÃO PENDENTE: com estas taxas a AUC multivariada das corridas mede
    # ~0.69 num feature set ad-hoc, abaixo do piso de 0.75 da faixa alvo. Ou a
    # contaminação está agressiva demais, ou o domínio de corridas tem menos
    # sinal genuíno que o bancário. Não foram ajustadas para bater o número —
    # precisam de referência real ou de um feature set oficial de corridas.
    "ride.legit_refund_zero_share": Rate(
        0.93, ESTIMATE,
        "Passageiros sem nenhum reembolso no mês. Reembolso legítimo existe — "
        "motorista não apareceu, corrida cancelada, cobrança duplicada.",
    ),
    "ride.legit_dispute_prob": Rate(
        0.004, ESTIMATE,
        "Contestação de cartão em corrida legítima: cobrança não reconhecida "
        "pelo titular, disputa familiar sobre o cartão, erro de tarifa dinâmica.",
    ),
    "ride.legit_new_device_prob": Rate(
        0.03, ESTIMATE,
        "Primeira corrida num aparelho por troca de celular, formatação ou "
        "login em tablet.",
    ),
    "ride.legit_promo_group_share": Rate(
        0.06, ESTIMATE,
        "Corridas legítimas dentro de alguma campanha promocional. Um group_id "
        "não nulo indica participação em campanha, não abuso dela.",
    ),
    "ride.chargeback_dispute_prob": Rate(
        0.72, ESTIMATE,
        "Fraude de chargeback em que o titular efetivamente abre a contestação. "
        "Parte nunca é aberta, e parte só aparece na corrida seguinte.",
    ),
    "ride.ato_new_device_prob": Rate(
        0.75, ESTIMATE,
        "Tomada de conta que estreia aparelho novo. Parte dos ATO opera de "
        "sessão já ativa no aparelho da própria vítima.",
    ),
    "ride.ghost_no_rating_prob": Rate(
        0.80, ESTIMATE,
        "Corrida fantasma sem avaliação do motorista. Corrida legítima sem "
        "avaliação é comum — o passageiro simplesmente não avalia.",
    ),
    "mule.p_legit": Rate(
        0.009, ESTIMATE,
        "Transferência legítima cujo destino consta em lista de mula. Lista de mula "
        "tem falso positivo — conta alugada e depois vendida, conta compartilhada. "
        "Sem essa taxa o campo volta a ser rótulo.",
    ),
}


# ─── Overrides ───────────────────────────────────────────────────────────────

_OVERRIDE_ENV = "FRAUDGEN_CALIBRATION"


def _load_overrides() -> None:
    """Apply overrides from the JSON file named by $FRAUDGEN_CALIBRATION, if set.

    An unknown key raises rather than being ignored: a typo in a partner's file
    would otherwise silently leave the default in place, and the operator would
    believe they had calibrated something they had not.
    """
    path = os.environ.get(_OVERRIDE_ENV)
    if not path:
        return
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    sources = data.pop("_sources", {})
    for key, value in data.items():
        if key not in _RATES:
            raise KeyError(
                f"{_OVERRIDE_ENV}: chave desconhecida {key!r}. "
                f"Chaves válidas: {', '.join(sorted(_RATES))}"
            )
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{_OVERRIDE_ENV}: {key} = {value} fora de [0, 1]")
        current = _RATES[key]
        _RATES[key] = Rate(
            value=float(value),
            provenance=CALIBRATED,
            note=current.note,
            source=sources.get(key, f"override via {_OVERRIDE_ENV}"),
        )


def rate(key: str) -> float:
    """Return the current value for *key*."""
    try:
        return _RATES[key].value
    except KeyError:
        raise KeyError(
            f"taxa de calibração desconhecida: {key!r}. "
            f"Válidas: {', '.join(sorted(_RATES))}"
        ) from None


def report() -> str:
    """Render the calibration table with provenance, for docs or a buyer."""
    width = max(len(k) for k in _RATES)
    lines = [
        f"{'parâmetro'.ljust(width)}  {'valor':>7}  proveniência",
        f"{'-' * width}  {'-' * 7}  {'-' * 40}",
    ]
    for key in sorted(_RATES):
        r = _RATES[key]
        tag = r.provenance if r.source is None else f"{r.provenance} ({r.source})"
        lines.append(f"{key.ljust(width)}  {r.value:>7.4f}  {tag}")

    n_cal = sum(1 for r in _RATES.values() if r.provenance == CALIBRATED)
    lines.append("")
    lines.append(f"{n_cal}/{len(_RATES)} calibradas contra referência real.")
    if n_cal < len(_RATES):
        lines.append(
            "As demais são estimativas fundamentadas, não medições — trate os "
            "números derivados delas como hipótese."
        )
    return "\n".join(lines)


_load_overrides()
