"""
V6-M16 — Backtesting de regras de fraude.

Simula o impacto de alterações em fraud_pattern_overrides.json contra o dataset
V5 existente, ANTES de regenerar. Responde: "se eu mudar prevalência X, quantas
fraudes extras teremos?"

Uso:
  python backtest_rules.py                                       # compara current vs stored
  python backtest_rules.py --type PHISHING_BANCARIO --prev 0.15  # simula prevalência 0.15
  python backtest_rules.py --type DEEP_FAKE_BIOMETRIA --prev 0.08 --type MULA_FINANCEIRA --prev 0.06
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

csv.field_size_limit(10**7)

ROOT = Path(__file__).resolve().parent.parent
OVERRIDES_PATH = ROOT / "data" / "rules" / "fraud_pattern_overrides.json"
V5_PATH = ROOT / "data" / "generated_v5"


def load_overrides():
    with open(OVERRIDES_PATH) as f:
        return json.load(f)


def find_v5_csv():
    csvs = sorted(V5_PATH.glob("transactions*.csv"))
    if not csvs:
        print("ERRO: Nenhum CSV V5 encontrado em", V5_PATH)
        sys.exit(1)
    return csvs[0]


def analyze_v5(csv_path):
    """Count fraud type distribution in V5 data."""
    total = 0
    n_fraud = 0
    fraud_types = Counter()
    fraud_amounts = Counter()  # sum per type

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            is_fraud = row.get("is_fraud", "") in ("True", "true", "1")
            if is_fraud:
                n_fraud += 1
                ft = row.get("fraud_type", "?")
                fraud_types[ft] += 1
                try:
                    fraud_amounts[ft] += float(row.get("amount", 0))
                except (ValueError, TypeError):
                    pass

    return total, n_fraud, fraud_types, fraud_amounts


def simulate(current_overrides, changes, total, n_fraud, fraud_types, fraud_amounts):
    """Simulate impact of prevalence changes."""
    # Current prevalences (normalized)
    current_prevs = {k: v.get("prevalence", 0) for k, v in current_overrides.items()}
    total_prev = sum(current_prevs.values()) or 1.0

    # Apply changes
    new_prevs = dict(current_prevs)
    for fraud_type, new_prev in changes.items():
        old = new_prevs.get(fraud_type, 0)
        new_prevs[fraud_type] = new_prev
        print(f"  {fraud_type}: {old:.4f} → {new_prev:.4f} (Δ {new_prev - old:+.4f})")

    new_total_prev = sum(new_prevs.values()) or 1.0

    print(f"\n{'='*60}")
    print("RESULTADO DO BACKTEST")
    print(f"{'='*60}")

    print(f"\nDataset V5: {total:,} transações, {n_fraud:,} fraudes ({n_fraud/total*100:.2f}%)")
    print(f"Prevalência total: {total_prev:.4f} → {new_total_prev:.4f}")

    # Estimate new fraud distribution
    print(f"\n{'Tipo':<35} {'Atual':>6} {'Simulado':>8} {'Δ':>6} {'Volume R$':>12}")
    print("-" * 71)

    total_new_fraud = 0
    total_new_volume = 0.0

    for ft in sorted(set(list(current_prevs.keys()) + list(new_prevs.keys()))):
        old_frac = current_prevs.get(ft, 0) / total_prev if total_prev else 0
        new_frac = new_prevs.get(ft, 0) / new_total_prev if new_total_prev else 0

        old_count = fraud_types.get(ft, 0)
        # Estimate new count proportionally
        new_count = round(n_fraud * new_frac)
        delta = new_count - old_count

        avg_amount = fraud_amounts.get(ft, 0) / old_count if old_count > 0 else 0
        delta_volume = delta * avg_amount

        total_new_fraud += new_count
        total_new_volume += delta_volume

        if delta != 0:
            print(f"  {ft:<33} {old_count:>6} {new_count:>8} {delta:>+6} R${delta_volume:>10,.0f}")

    print(f"\n  TOTAL: {n_fraud:,} → {total_new_fraud:,} (Δ {total_new_fraud - n_fraud:+,})")
    print(f"  Volume estimado: R$ {total_new_volume:+,.0f}")

    # Safety check
    new_rate = total_new_fraud / total * 100
    if new_rate > 5.0:
        print(f"\n  ⚠️  ATENÇÃO: Taxa de fraude simulada ({new_rate:.2f}%) > 5% — pode ser excessiva")
    elif new_rate < 0.5:
        print(f"\n  ⚠️  ATENÇÃO: Taxa de fraude simulada ({new_rate:.2f}%) < 0.5% — pode ser baixa")
    else:
        print(f"\n  ✅ SAFE: Taxa de fraude {new_rate:.2f}% dentro do range aceitável (0.5-5%)")

    return total_new_fraud


def main():
    parser = argparse.ArgumentParser(description="Backtest rule changes against V5 data")
    parser.add_argument("--type", action="append", dest="types", help="Fraud type to change")
    parser.add_argument("--prev", action="append", dest="prevs", type=float, help="New prevalence")
    args = parser.parse_args()

    print("=" * 60)
    print("BACKTESTING DE REGRAS (V6-M16)")
    print("=" * 60)

    csv_path = find_v5_csv()
    print(f"\nAnalisando: {csv_path}")

    total, n_fraud, fraud_types, fraud_amounts = analyze_v5(csv_path)

    overrides = load_overrides()

    if args.types and args.prevs:
        if len(args.types) != len(args.prevs):
            print("ERRO: Número de --type deve igualar --prev")
            sys.exit(1)
        changes = dict(zip(args.types, args.prevs))
        print(f"\nSimulando {len(changes)} alterações:")
        simulate(overrides, changes, total, n_fraud, fraud_types, fraud_amounts)
    else:
        # Show current state
        print(f"\nEstado atual: {total:,} transações, {n_fraud:,} fraudes ({n_fraud/total*100:.2f}%)")
        print(f"\n{'Tipo':<35} {'Count':>6} {'%':>6} {'Override':>8}")
        print("-" * 59)
        for ft, count in fraud_types.most_common():
            pct = count / n_fraud * 100 if n_fraud else 0
            ov_prev = overrides.get(ft, {}).get("prevalence", "?")
            print(f"  {ft:<33} {count:>6} {pct:>5.1f}% {ov_prev:>8}")
        print(f"\nUso: python backtest_rules.py --type TIPO --prev 0.XX")


if __name__ == "__main__":
    main()
