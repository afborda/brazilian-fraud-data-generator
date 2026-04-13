"""
CLI tool for offline LightGBM model training.

Usage:
    python tools/train_ml.py \
        --input ./data/ml_training/*.jsonl \
        --model-dir ./models \
        --version v1

    python tools/train_ml.py \
        --input ./data/ml_training/transactions_00000.jsonl \
        --model-dir ./models \
        --version v1 \
        --skip-multilabel

Output:
    models/fraud_detector_v1.pkl          (binary classifier)
    models/fraud_type_CONTA_TOMADA_v1.pkl (one per fraud type)
    models/train_metrics_v1.json          (metrics report)

Note:
    Training is intentionally offline (batch CLI), not online per-request.
    This keeps inference latency low and gives humans a chance to review
    quality flags before deploying a new model version.
"""

import argparse
import glob
import json
import sys
import time
from pathlib import Path

# Allow running from repo root without installing the package
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

import ijson  # type: ignore[import-untyped]
from fraud_generator.ml.trainer import train_binary_model, train_multilabel_models, HAS_LGBM


def load_jsonl(paths: list[str], max_records: int | None = None) -> list[dict]:
    records = []
    for path in paths:
        with open(path, "rb") as f:
            for record in ijson.items(f, "", multiple_values=True):
                records.append(record)
                if max_records and len(records) >= max_records:
                    return records
    return records


def load_jsonl_fallback(paths: list[str], max_records: int | None = None) -> list[dict]:
    """Fallback for files that are one-JSON-per-line (standard JSONL)."""
    records = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if max_records and len(records) >= max_records:
                    return records
    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train LightGBM fraud quality models offline."
    )
    parser.add_argument(
        "--input", nargs="+", required=True,
        help="Input JSONL file(s) or glob pattern (e.g. ./data/*.jsonl)"
    )
    parser.add_argument(
        "--model-dir", default="./models",
        help="Directory to save trained models (default: ./models)"
    )
    parser.add_argument(
        "--version", default="v1",
        help="Model version string used in filenames (default: v1)"
    )
    parser.add_argument(
        "--skip-multilabel", action="store_true",
        help="Skip per-type OvR models (faster, less diagnostic value)"
    )
    parser.add_argument(
        "--max-records", type=int, default=None,
        help="Cap number of records loaded (useful for quick tests)"
    )
    parser.add_argument(
        "--min-examples-per-class", type=int, default=50,
        help="Minimum fraud examples per type to train a per-type model (default: 50)"
    )
    args = parser.parse_args()

    if not HAS_LGBM:
        print("ERROR: lightgbm is not installed.")
        print("  pip install lightgbm>=4.3.0 joblib>=1.3.0")
        sys.exit(1)

    # Expand glob patterns
    input_paths: list[str] = []
    for pattern in args.input:
        expanded = glob.glob(pattern)
        if expanded:
            input_paths.extend(expanded)
        elif Path(pattern).exists():
            input_paths.append(pattern)

    if not input_paths:
        print(f"ERROR: No files found matching: {args.input}")
        sys.exit(1)

    print(f"Loading records from {len(input_paths)} file(s)...")
    t0 = time.time()
    try:
        records = load_jsonl(input_paths, args.max_records)
    except Exception:
        records = load_jsonl_fallback(input_paths, args.max_records)

    n_fraud = sum(1 for r in records if r.get("is_fraud"))
    print(f"  {len(records):,} records loaded ({n_fraud:,} fraud, {len(records)-n_fraud:,} legit) "
          f"in {time.time()-t0:.1f}s")

    all_metrics: dict = {}

    print(f"\nTraining binary model (version={args.version})...")
    t0 = time.time()
    binary_metrics = train_binary_model(
        records,
        model_dir=args.model_dir,
        model_version=args.version,
    )
    print(f"  AUC-ROC: {binary_metrics['auc_roc']:.4f}  "
          f"AUC-PR: {binary_metrics['auc_pr']:.4f}  "
          f"({time.time()-t0:.1f}s)")
    print(f"  Saved: {binary_metrics['model_path']}")
    print("  Top-5 feature importance:")
    for feat, imp in list(binary_metrics["feature_importance"].items())[:5]:
        bar = "█" * int(imp * 40)
        print(f"    {feat:<35} {imp:.3f} {bar}")
    all_metrics["binary"] = binary_metrics

    if not args.skip_multilabel:
        print(f"\nTraining per-type models (min_examples={args.min_examples_per_class})...")
        t0 = time.time()
        ml_metrics = train_multilabel_models(
            records,
            model_dir=args.model_dir,
            model_version=args.version,
            min_examples_per_class=args.min_examples_per_class,
        )
        print(f"  Trained: {ml_metrics['trained_count']}  "
              f"Skipped: {ml_metrics['skipped_count']}  "
              f"({time.time()-t0:.1f}s)")

        # Quality flags
        print("\n  Per-type AUC-ROC:")
        for ft, info in sorted(ml_metrics["per_type"].items(),
                                key=lambda x: x[1].get("auc_roc") or 0, reverse=True):
            if info.get("skipped"):
                print(f"    {ft:<40} SKIPPED (n={info['n_examples']})")
            else:
                auc = info["auc_roc"]
                flag = ""
                if auc > 0.99:
                    flag = "⚠ TOO EASY"
                elif auc < 0.70:
                    flag = "⚠ TOO HARD"
                bar = "█" * int(auc * 20)
                print(f"    {ft:<40} {auc:.4f} {bar} {flag}")

        all_metrics["multilabel"] = ml_metrics

    # Save combined metrics report
    metrics_path = Path(args.model_dir) / f"train_metrics_{args.version}.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)
    print(f"\nMetrics saved: {metrics_path}")


if __name__ == "__main__":
    main()
