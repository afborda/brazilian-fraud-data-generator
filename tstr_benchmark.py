"""
TSTR Benchmark — Train Synthetic, Test Real (Melhoria 10)

Treina RF e XGBoost no dataset sintético V5 para estimar utilidade dos dados.
Compara com benchmarks da dissertação Pacheco (FGV 2019): ROC ~79-85%.

Uso:
    python tstr_benchmark.py [csv_path]
    python tstr_benchmark.py data/generated_v5/transactions_00000.csv
"""
import csv
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# Features to use (numeric + encodable categorical)
NUMERIC_FEATURES = [
    "amount",
    "fraud_score",
    "velocity_transactions_24h",
    "accumulated_amount_24h",
    "distance_from_home_km",
    "distance_from_last_km",
    "device_age_days",
    "customer_velocity_z_score",
    "time_since_last_txn_min",
    "distance_from_last_txn_km",
]

CATEGORICAL_FEATURES = [
    "channel",
    "card_brand",
    "card_type",
    "type",
]

TARGET = "is_fraud"


def load_data(path: str):
    """Load CSV and extract features + target."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    all_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X_raw = []
    y = []

    label_encoders = {}
    for feat in CATEGORICAL_FEATURES:
        vals = [r.get(feat, "unknown") or "unknown" for r in rows]
        le = LabelEncoder()
        le.fit(vals)
        label_encoders[feat] = le

    for row in rows:
        target = row.get(TARGET, "").strip().lower() in ("true", "1")
        features = []

        for feat in NUMERIC_FEATURES:
            val = row.get(feat, "")
            if val in ("", "None", None):
                features.append(0.0)
            else:
                try:
                    features.append(float(val))
                except ValueError:
                    features.append(0.0)

        for feat in CATEGORICAL_FEATURES:
            val = row.get(feat, "unknown") or "unknown"
            features.append(label_encoders[feat].transform([val])[0])

        X_raw.append(features)
        y.append(int(target))

    return np.array(X_raw), np.array(y)


def run_benchmark(X, y):
    """Run stratified 5-fold CV with RF and GBT."""
    # Sample down for speed if dataset is large
    max_samples = 50_000
    if len(y) > max_samples:
        rng = np.random.RandomState(42)
        idx = rng.choice(len(y), max_samples, replace=False)
        X, y = X[idx], y[idx]
        print(f"  Amostrado para {max_samples:,} registros (speed)")

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=100, max_depth=12, class_weight="balanced",
            random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=50, max_depth=4, learning_rate=0.1,
            random_state=42, subsample=0.8
        ),
    }

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results = {}

    for name, model in models.items():
        aucs = []
        f1s = []
        precs = []
        recs = []

        for train_idx, test_idx in skf.split(X, y):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            model.fit(X_train, y_train)

            y_prob = model.predict_proba(X_test)[:, 1]
            y_pred = model.predict(X_test)

            aucs.append(roc_auc_score(y_test, y_prob))
            f1s.append(f1_score(y_test, y_pred))
            precs.append(precision_score(y_test, y_pred))
            recs.append(recall_score(y_test, y_pred))

        results[name] = {
            "AUC": (np.mean(aucs), np.std(aucs)),
            "F1": (np.mean(f1s), np.std(f1s)),
            "Precision": (np.mean(precs), np.std(precs)),
            "Recall": (np.mean(recs), np.std(recs)),
        }

        # Feature importance
        if hasattr(model, "feature_importances_"):
            feat_names = NUMERIC_FEATURES + CATEGORICAL_FEATURES
            importances = model.feature_importances_
            top_idx = np.argsort(importances)[::-1][:10]
            results[name]["top_features"] = [
                (feat_names[i], round(importances[i], 4)) for i in top_idx
            ]

    return results


def main():
    default_path = "data/generated_v5/transactions_00000.csv"
    path = sys.argv[1] if len(sys.argv) > 1 else default_path

    if not Path(path).exists():
        print(f"Arquivo não encontrado: {path}")
        sys.exit(1)

    print("TSTR Benchmark — Train Synthetic, Test Real")
    print("=" * 60)
    print(f"Dataset: {path}")

    X, y = load_data(path)
    n_fraud = y.sum()
    n_legit = len(y) - n_fraud
    print(f"Transações: {len(y):,} (fraud: {n_fraud:,}, legit: {n_legit:,})")
    print(f"Fraud rate: {n_fraud / len(y) * 100:.2f}%")
    print(f"Features: {X.shape[1]} ({len(NUMERIC_FEATURES)} numeric + {len(CATEGORICAL_FEATURES)} categorical)")
    print(f"\nRodando 5-fold Stratified CV...")

    results = run_benchmark(X, y)

    # Pacheco benchmarks
    pacheco = {"RF ROC Fraude_concessão": 79.31, "RF ROC Conta_nunca_paga": 68.67, "RF ROC Ação_cível": 85.37}

    print(f"\n{'='*60}")
    print("RESULTADOS")
    print(f"{'='*60}")

    for name, metrics in results.items():
        print(f"\n  {name}:")
        for metric, val in metrics.items():
            if metric == "top_features":
                continue
            mean, std = val
            print(f"    {metric}: {mean:.4f} ± {std:.4f}")

        if "top_features" in metrics:
            print(f"    Top features:")
            for feat, imp in metrics["top_features"]:
                print(f"      {feat}: {imp:.4f}")

    # Compare with Pacheco
    print(f"\n{'='*60}")
    print("COMPARAÇÃO COM PACHECO (FGV 2019 — dados reais)")
    print(f"{'='*60}")

    our_auc = results.get("RandomForest", {}).get("AUC", (0, 0))
    print(f"\n  Nosso RF AUC: {our_auc[0]*100:.1f}%")
    for name, roc in pacheco.items():
        delta = our_auc[0] * 100 - roc
        status = "✅" if abs(delta) < 10 else "⚠️"
        print(f"  {status} {name}: {roc:.1f}% (Δ {delta:+.1f}%)")

    # Verdict
    print(f"\n{'='*60}")
    if our_auc[0] > 0.85:
        print("  ✅ APROVADO — Dados altamente treináveis (AUC > 85%)")
    elif our_auc[0] > 0.70:
        print("  ✅ APROVADO — Dados treináveis (AUC > 70%)")
    elif our_auc[0] > 0.60:
        print("  ⚠️ ACEITÁVEL — Dados razoáveis mas correlações fracas (AUC 60-70%)")
    else:
        print("  ❌ REPROVADO — Dados não treináveis (AUC < 60%)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
