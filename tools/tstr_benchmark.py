"""TSTR — Train on Synthetic, Test on Real.

The point of synthetic fraud data is that a model trained on it works on real
traffic. TSTR is the only measurement that answers that, and it needs two
datasets: ours and a real one.

## O que este arquivo fazia antes

Ele se chamava "TSTR Benchmark — Train Synthetic, Test Real" e rodava
`StratifiedKFold` sobre um único CSV sintético — treinava em sintético e testava
em sintético, o que é TSTS. Não havia dado real em lugar nenhum do fluxo, então
era estruturalmente incapaz de detectar falha de transferência, que é a única
coisa que TSTR existe para medir. Aprovava com `if auc > 0.85`, e incluía
`fraud_score` entre as features — campo que o próprio gerador deriva do rótulo.

## O que ele faz agora

Três medições, e o que importa é a diferença entre elas:

* **TRTR** — treina no real, testa no real. É o teto: o que um modelo consegue
  com dados de verdade. Sem esta linha o TSTR não tem contra o que ser comparado.
* **TSTR** — treina no sintético, testa no real. É a pergunta do produto.
* **TSTS** — treina e testa no sintético. Serve só para diagnóstico: um TSTS
  muito acima do TSTR indica que o sintético tem estrutura que o real não tem.

**gap = AUC_TRTR − AUC_TSTR.** Quanto menor, melhor o sintético substitui o real.

## Veredito

Reprova nos dois extremos, e o segundo é contra-intuitivo:

* `gap > MAX_GAP` — o modelo não transfere. O sintético ensina padrões que não
  existem no real.
* `gap < MIN_GAP` com poucas features alinhadas — bom demais para ser verdade.
  O critério é do próprio `TSTR_FRAUD_ROADMAP.md` do projeto: *"Gap = 0% com 2
  features indica bug ou overfitting"*. Com duas ou três colunas em comum,
  igualar o desempenho do dado real significa quase sempre que a mesma
  informação vazou dos dois lados, não que o sintético é excelente.

## Uso

    python tools/tstr_benchmark.py --synthetic out/transactions_00000.jsonl \\
                                   --real referencia.csv

Sem `--real` o comando não roda TSTR — ele diz isso e sai, em vez de rodar
cross-validation e chamar o resultado de TSTR.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")


# Campos derivados do rótulo pelo gerador. Nunca entram: nenhum banco os tem
# antes de rodar o próprio modelo, e um deles sozinho já dava AUC 1.0.
LABEL_DERIVED = frozenset({
    "is_fraud", "fraud_type", "fraud_labels", "fraud_signals",
    "fraud_score", "fraud_risk_score", "fraud_chain_id", "fraud_chain_role",
    "fraud_reported_days_after", "credential_breach_days_before",
    "card_test_phase", "distributed_attack_group", "dict_fraud_marker",
})

# Identificadores: alta cardinalidade, não generalizam entre datasets.
ID_LIKE = frozenset({
    "transaction_id", "customer_id", "device_id", "merchant_id",
    "end_to_end_id", "ip_address", "cpf_hash_pagador", "cpf_hash_recebedor",
    "beneficiary_cpf_hash", "card_number_hash",
})

LABEL_COLUMN_CANDIDATES = ("is_fraud", "isFraud", "Class", "fraud", "label")

# Limiares do veredito.
MAX_GAP = 0.15          # acima disso o modelo não transfere
MIN_GAP = 0.02          # abaixo disso, com poucas features, é suspeito
MIN_FEATURES_FOR_TRUST = 6


# ─── Carregamento ────────────────────────────────────────────────────────────

def _load_any(path: str, max_rows: int = 300_000) -> List[Dict]:
    """Load a JSONL or CSV file into a list of dicts."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    rows: List[Dict] = []
    if p.suffix.lower() in (".jsonl", ".ndjson"):
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if len(rows) >= max_rows:
                    break
    else:
        with p.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                rows.append(row)
                if len(rows) >= max_rows:
                    break
    return rows


def _find_label(rows: List[Dict]) -> str:
    """Return the name of the label column, or raise with what was available."""
    if not rows:
        raise ValueError("dataset vazio")
    keys = set(rows[0])
    for cand in LABEL_COLUMN_CANDIDATES:
        if cand in keys:
            return cand
    raise ValueError(
        f"nenhuma coluna de rótulo encontrada. Procurei por "
        f"{', '.join(LABEL_COLUMN_CANDIDATES)}; o arquivo tem: "
        f"{', '.join(sorted(keys)[:20])}"
    )


def _numeric_columns(rows: List[Dict], label: str) -> List[str]:
    """Columns that parse as numeric in at least 80% of a sample."""
    sample = rows[:5000]
    usable: List[str] = []
    for col in sorted(rows[0]):
        if col == label or col in LABEL_DERIVED or col in ID_LIKE:
            continue
        ok = 0
        for r in sample:
            v = r.get(col)
            if isinstance(v, bool):
                ok += 1
            elif isinstance(v, (int, float)):
                ok += 1
            elif isinstance(v, str) and v.strip():
                try:
                    float(v)
                    ok += 1
                except ValueError:
                    pass
        if ok >= len(sample) * 0.8:
            usable.append(col)
    return usable


def _matrix(rows: List[Dict], columns: List[str], label: str) -> Tuple[np.ndarray, np.ndarray]:
    """Build (X, y) for the given columns."""
    X = np.zeros((len(rows), len(columns)), dtype=np.float64)
    y = np.zeros(len(rows), dtype=np.int8)
    for i, r in enumerate(rows):
        for j, col in enumerate(columns):
            v = r.get(col)
            if isinstance(v, bool):
                X[i, j] = 1.0 if v else 0.0
            elif isinstance(v, (int, float)):
                X[i, j] = float(v)
            elif isinstance(v, str) and v.strip():
                try:
                    X[i, j] = float(v)
                except ValueError:
                    X[i, j] = 0.0
        lv = r.get(label)
        if isinstance(lv, bool):
            y[i] = int(lv)
        elif isinstance(lv, (int, float)):
            y[i] = int(lv > 0)
        elif isinstance(lv, str):
            y[i] = int(lv.strip().lower() in ("1", "true", "yes", "sim", "t"))
    return X, y


# ─── Medição ─────────────────────────────────────────────────────────────────

def _models() -> Dict[str, object]:
    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=120, max_depth=10, random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100, max_depth=4, random_state=42, subsample=0.8
        ),
    }


def _auc(model, X_tr, y_tr, X_te, y_te) -> Optional[float]:
    if len(set(y_tr)) < 2 or len(set(y_te)) < 2:
        return None
    model.fit(X_tr, y_tr)
    return float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))


def run(synth_rows: List[Dict], real_rows: List[Dict]) -> Dict:
    """Run TRTR / TSTR / TSTS over the columns the two datasets share."""
    synth_label = _find_label(synth_rows)
    real_label = _find_label(real_rows)

    shared = sorted(
        set(_numeric_columns(synth_rows, synth_label))
        & set(_numeric_columns(real_rows, real_label))
    )
    if not shared:
        raise ValueError(
            "nenhuma coluna numérica em comum entre os dois datasets. "
            "TSTR exige um espaço de features compartilhado — alinhe os "
            "esquemas (renomeie colunas equivalentes) antes de medir."
        )

    Xs, ys = _matrix(synth_rows, shared, synth_label)
    Xr, yr = _matrix(real_rows, shared, real_label)

    # O real é dividido uma vez: a MESMA metade de teste avalia TRTR e TSTR,
    # senão a comparação não seria pareada.
    Xr_tr, Xr_te, yr_tr, yr_te = train_test_split(
        Xr, yr, test_size=0.5, random_state=42, stratify=yr
    )
    Xs_tr, Xs_te, ys_tr, ys_te = train_test_split(
        Xs, ys, test_size=0.3, random_state=42, stratify=ys
    )

    results: Dict[str, Dict] = {}
    for name, _ in _models().items():
        trtr = _auc(_models()[name], Xr_tr, yr_tr, Xr_te, yr_te)
        tstr = _auc(_models()[name], Xs_tr, ys_tr, Xr_te, yr_te)
        tsts = _auc(_models()[name], Xs_tr, ys_tr, Xs_te, ys_te)
        results[name] = {
            "trtr": None if trtr is None else round(trtr, 4),
            "tstr": None if tstr is None else round(tstr, 4),
            "tsts": None if tsts is None else round(tsts, 4),
            "gap": None if (trtr is None or tstr is None) else round(trtr - tstr, 4),
        }

    gaps = [r["gap"] for r in results.values() if r["gap"] is not None]
    mean_gap = round(sum(gaps) / len(gaps), 4) if gaps else None

    return {
        "shared_features": shared,
        "n_shared_features": len(shared),
        "n_synthetic": len(synth_rows),
        "n_real": len(real_rows),
        "synthetic_fraud_rate": round(float(ys.mean()), 4),
        "real_fraud_rate": round(float(yr.mean()), 4),
        "per_model": results,
        "mean_gap": mean_gap,
        "verdict": _verdict(mean_gap, len(shared)),
    }


def _verdict(mean_gap: Optional[float], n_features: int) -> Dict:
    """Pass/fail with the reason spelled out."""
    if mean_gap is None:
        return {"passed": False, "reason": "não foi possível computar o gap"}

    if mean_gap > MAX_GAP:
        return {
            "passed": False,
            "reason": (
                f"gap {mean_gap:.4f} acima de {MAX_GAP}: o modelo treinado no "
                f"sintético não transfere para o real"
            ),
        }
    if mean_gap < MIN_GAP and n_features < MIN_FEATURES_FOR_TRUST:
        return {
            "passed": False,
            "reason": (
                f"gap {mean_gap:.4f} abaixo de {MIN_GAP} com apenas "
                f"{n_features} features alinhadas: bom demais para ser "
                f"verdade. Critério do TSTR_FRAUD_ROADMAP.md — gap ~0 com "
                f"poucas features indica bug ou vazamento nos dois lados, não "
                f"qualidade."
            ),
        }
    return {
        "passed": True,
        "reason": f"gap {mean_gap:.4f} dentro de [{MIN_GAP}, {MAX_GAP}]",
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _print_report(res: Dict) -> None:
    print("=" * 68)
    print("  TSTR — Train on Synthetic, Test on Real")
    print("=" * 68)
    print(f"  sintético : {res['n_synthetic']:>9,} registros  "
          f"(fraude {res['synthetic_fraud_rate']*100:.2f}%)")
    print(f"  real      : {res['n_real']:>9,} registros  "
          f"(fraude {res['real_fraud_rate']*100:.2f}%)")
    print(f"  features compartilhadas: {res['n_shared_features']}")
    print()
    print(f"  {'modelo':<20}{'TRTR':>9}{'TSTR':>9}{'TSTS':>9}{'gap':>9}")
    print("  " + "-" * 56)
    for name, r in res["per_model"].items():
        def f(v):
            return "—" if v is None else f"{v:.4f}"
        print(f"  {name:<20}{f(r['trtr']):>9}{f(r['tstr']):>9}"
              f"{f(r['tsts']):>9}{f(r['gap']):>9}")
    print()
    print("  TRTR = teto (real→real) · TSTR = a pergunta (sintético→real)")
    print("  TSTS = diagnóstico (sintético→sintético) · gap = TRTR − TSTR")
    print()
    v = res["verdict"]
    print(f"  {'✓ APROVADO' if v['passed'] else '✗ REPROVADO'} — {v['reason']}")
    print("=" * 68)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="tstr_benchmark",
        description="Mede se um modelo treinado no dado sintético funciona no real.",
    )
    ap.add_argument("--synthetic", required=True, help="JSONL ou CSV gerado")
    ap.add_argument(
        "--real",
        help="JSONL ou CSV de referência real. Sem ele não existe TSTR.",
    )
    ap.add_argument("--json", action="store_true", help="saída em JSON")
    ap.add_argument(
        "--gate", action="store_true",
        help="sai com código 1 se o veredito reprovar",
    )
    args = ap.parse_args(argv)

    if not args.real:
        print(
            "TSTR precisa de um dataset real: passe --real.\n"
            "\n"
            "Este comando NÃO cai para cross-validation sobre o próprio arquivo\n"
            "sintético. Fazer isso e chamar o resultado de TSTR foi o defeito\n"
            "que esta ferramenta tinha: treinar e testar no mesmo dado não pode,\n"
            "por construção, detectar falha de transferência.\n"
            "\n"
            "Referências utilizáveis: Sparkov, PaySim, ULB Credit Card Fraud, ou\n"
            "agregados de um parceiro com o esquema alinhado.",
            file=sys.stderr,
        )
        return 2

    synth = _load_any(args.synthetic)
    real = _load_any(args.real)
    res = run(synth, real)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        _print_report(res)

    if args.gate and not res["verdict"]["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
