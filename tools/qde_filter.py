"""
QDE — Quality Data Extractor (Melhoria 3)

Filtra transações inconsistentes do CSV gerado pelo synthfin-core.
Baseado no conceito QDE do artigo "Geração de Dados Sintéticos para ML" (2026).

Uso:
    python qde_filter.py data/generated_v5/transactions_00000.csv
    python qde_filter.py data/generated_v5/  # processa todos CSVs na pasta

Resultado:
    - CSV limpo (mesmo nome com sufixo _qde)
    - Relatório de remoções por regra
"""
import csv
import os
import sys
from pathlib import Path
from collections import Counter


def _safe_float(val, default=None):
    if val is None or val == "" or val == "None":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes")
    return bool(val) if val is not None else False


RULES = {
    "fraud_low_score": "is_fraud=True mas fraud_score < 0.1",
    "legit_high_score": "is_fraud=False mas fraud_score > 0.9",
    "fraud_no_type": "is_fraud=True mas fraud_type vazio",
    "legit_has_type": "is_fraud=False mas fraud_type preenchido",
    "amount_negative": "amount < 0",
    "velocity_1h_extreme": "velocity_transactions_1h > 100",
    "impossible_travel_short": "is_impossible_travel=True mas distance_from_last_km < 10",
}


def check_row(row: dict) -> str | None:
    """Return rule name if row should be removed, None if OK."""
    is_fraud = _safe_bool(row.get("is_fraud"))
    fraud_score = _safe_float(row.get("fraud_score"))
    fraud_type = row.get("fraud_type", "").strip()
    amount = _safe_float(row.get("amount"))
    velocity_1h = _safe_float(row.get("velocity_transactions_1h"))
    is_impossible = _safe_bool(row.get("is_impossible_travel"))
    dist_last = _safe_float(row.get("distance_from_last_km"))

    # R1: Fraud with very low score (undetectable = inconsistent)
    # fraud_score uses 0-100 scale in synthfin-core
    if is_fraud and fraud_score is not None and fraud_score < 10:
        return "fraud_low_score"

    # R2: Legit with extremely high fraud score
    if not is_fraud and fraud_score is not None and fraud_score > 95:
        return "legit_high_score"

    # R3: Fraud without type
    if is_fraud and (not fraud_type or fraud_type in ("None", "nan", "")):
        return "fraud_no_type"

    # R4: Legit with fraud type (should not happen)
    if not is_fraud and fraud_type and fraud_type not in ("None", "nan", "", "NONE"):
        return "legit_has_type"

    # R5: Negative amount
    if amount is not None and amount < 0:
        return "amount_negative"

    # R6: Humanly impossible velocity
    if velocity_1h is not None and velocity_1h > 100:
        return "velocity_1h_extreme"

    # R7: Impossible travel with short distance
    if is_impossible and dist_last is not None and dist_last < 10:
        return "impossible_travel_short"

    return None


def filter_csv(input_path: str) -> dict:
    """Filter a single CSV, return stats."""
    input_path = Path(input_path)
    output_path = input_path.with_stem(input_path.stem + "_qde")

    removed = Counter()
    total = 0
    kept = 0

    with open(input_path, "r", newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames

        with open(output_path, "w", newline="", encoding="utf-8") as fout:
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                total += 1
                violation = check_row(row)
                if violation:
                    removed[violation] += 1
                else:
                    writer.writerow(row)
                    kept += 1

    return {
        "input": str(input_path),
        "output": str(output_path),
        "total": total,
        "kept": kept,
        "removed_total": total - kept,
        "removed_pct": round((total - kept) / max(total, 1) * 100, 2),
        "by_rule": dict(removed),
    }


def main():
    if len(sys.argv) < 2:
        print("Uso: python qde_filter.py <csv_ou_pasta>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if target.is_dir():
        csvs = sorted(target.glob("transactions_*.csv"))
        csvs = [c for c in csvs if "_qde" not in c.name]
    elif target.is_file():
        csvs = [target]
    else:
        print(f"Não encontrado: {target}")
        sys.exit(1)

    print(f"QDE Filter — {len(csvs)} arquivo(s)")
    print("=" * 60)

    grand_total = 0
    grand_kept = 0
    grand_removed = Counter()

    for csv_path in csvs:
        stats = filter_csv(csv_path)
        grand_total += stats["total"]
        grand_kept += stats["kept"]
        grand_removed.update(stats["by_rule"])

        print(f"\n  {csv_path.name}")
        print(f"    Total: {stats['total']:,} → Kept: {stats['kept']:,} "
              f"({stats['removed_pct']}% removido)")
        for rule, count in sorted(stats["by_rule"].items(), key=lambda x: -x[1]):
            print(f"    {rule}: {count:,} ({RULES.get(rule, '')})")

    print(f"\n{'='*60}")
    print(f"TOTAL: {grand_total:,} → {grand_kept:,} "
          f"({round((grand_total - grand_kept) / max(grand_total, 1) * 100, 2)}% removido)")
    print(f"\nRemoções por regra:")
    for rule, count in sorted(grand_removed.items(), key=lambda x: -x[1]):
        print(f"  {rule}: {count:,}")


if __name__ == "__main__":
    main()
