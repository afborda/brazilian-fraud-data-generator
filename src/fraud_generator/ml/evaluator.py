"""
Model evaluator for synthetic fraud quality validation.

Two public functions:
  load_models(model_dir, model_version) -> dict (model registry)
  evaluate_batch(records, model_registry) -> dict (quality report)

Quality flag thresholds (based on realistic AUC ranges from literature):
  AUC > 0.99  → too_easy   (enricher is deterministic, adding too many signals)
  0.85–0.99   → healthy_high_signal (expected for bot/ATO types)
  0.70–0.85   → healthy_low_signal (expected for social engineering)
  < 0.70      → too_hard   (enricher not injecting sufficient signals)

References:
  - Synthcity [arXiv:2301.07573]: ML efficacy evaluation framework
  - Fraud Detection Handbook (Bahnsen 2022): realistic AUC ranges 0.75–0.92
  - Esteban et al. TSTR [arXiv:1706.02633]: Train on Synthetic, Test on Real
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    joblib = None  # type: ignore[assignment]
    HAS_JOBLIB = False

from sklearn.metrics import roc_auc_score, average_precision_score

from .features import extract_features

_AUC_TOO_EASY  = 0.99
_AUC_TOO_HARD  = 0.70


def load_models(model_dir: str | Path, model_version: str) -> dict[str, Any]:
    """
    Load all models for a given version from model_dir.

    Returns a registry dict:
    {
        "binary": <LGBMClassifier>,                 # fraud_detector_{version}.pkl
        "per_type": {
            "CONTA_TOMADA": <LGBMClassifier>, ...   # fraud_type_{TYPE}_{version}.pkl
        },
        "model_version": "v1",
        "model_dir": "/data/models",
    }
    """
    if not HAS_JOBLIB:
        raise ImportError("joblib is required. Install with: pip install joblib>=1.3.0")

    model_dir = Path(model_dir)
    registry: dict[str, Any] = {
        "binary": None,
        "per_type": {},
        "model_version": model_version,
        "model_dir": str(model_dir),
    }

    binary_path = model_dir / f"fraud_detector_{model_version}.pkl"
    if binary_path.exists():
        registry["binary"] = joblib.load(binary_path)

    for p in model_dir.glob(f"fraud_type_*_{model_version}.pkl"):
        # extract fraud_type name: fraud_type_{TYPE}_{version}.pkl
        stem = p.stem  # e.g. fraud_type_CONTA_TOMADA_v1
        prefix = "fraud_type_"
        suffix = f"_{model_version}"
        if stem.startswith(prefix) and stem.endswith(suffix):
            ft = stem[len(prefix):-len(suffix)]
            registry["per_type"][ft] = joblib.load(p)

    return registry


def evaluate_batch(
    records: Sequence[dict[str, Any]],
    model_registry: dict[str, Any],
) -> dict[str, Any]:
    """
    Run inference on a batch of records and produce a quality report.

    Returns:
    {
        "overall": {
            "auc_roc": 0.91, "auc_pr": 0.78,
            "n_total": 100000, "n_fraud": 4821, "fraud_rate": 0.0482
        },
        "per_type": {
            "CONTA_TOMADA": {"auc_roc": 0.96, "n_examples": 785, "flag": "healthy_high_signal"},
            "ENGENHARIA_SOCIAL": {"auc_roc": 0.72, "n_examples": 412, "flag": "healthy_low_signal"},
        },
        "feature_importance": {"velocity_transactions_24h": 0.295, ...},
        "quality_flags": [
            {"fraud_type": "CREDENTIAL_STUFFING", "auc_roc": 0.9997, "flag": "too_easy",
             "recommendation": "Reduce deterministic signals in enricher"},
            {"fraud_type": "ENGENHARIA_SOCIAL", "auc_roc": 0.58, "flag": "too_hard",
             "recommendation": "Check if new_beneficiary_prob is being applied"},
        ],
        "per_record_scores": [
            {"transaction_id": "TX_...", "predicted_fraud_prob": 0.87}, ...
        ],
        "model_version": "v1",
    }
    """
    binary_model = model_registry.get("binary")
    per_type_models = model_registry.get("per_type", {})

    if binary_model is None:
        raise ValueError("No binary model loaded. Run train_binary_model first.")

    X = extract_features(records)
    labels = np.array([int(r.get("is_fraud", 0)) for r in records])
    n_fraud = int(labels.sum())
    n_legit = len(labels) - n_fraud

    y_prob = binary_model.predict_proba(X)[:, 1]
    auc_roc_overall = float(roc_auc_score(labels, y_prob))
    auc_pr_overall = float(average_precision_score(labels, y_prob))

    importance_raw = binary_model.feature_importances_
    importance_total = importance_raw.sum()
    feature_importance = {
        name: round(float(val) / importance_total, 4)
        for name, val in zip(X.columns, importance_raw)
    }
    feature_importance = dict(
        sorted(feature_importance.items(), key=lambda x: -x[1])
    )

    per_record_scores = []
    for rec, prob in zip(records, y_prob):
        per_record_scores.append({
            "transaction_id": rec.get("transaction_id") or rec.get("id"),
            "predicted_fraud_prob": round(float(prob), 4),
        })

    # Per-type evaluation
    fraud_records_by_type: dict[str, list[int]] = {}
    for i, rec in enumerate(records):
        if rec.get("is_fraud"):
            ft = rec.get("fraud_type") or "UNKNOWN"
            fraud_records_by_type.setdefault(ft, []).append(i)

    legit_indices = [i for i, r in enumerate(records) if not r.get("is_fraud")]

    per_type: dict[str, Any] = {}
    quality_flags: list[dict[str, Any]] = []

    for fraud_type, fraud_indices in sorted(fraud_records_by_type.items()):
        n_pos = len(fraud_indices)
        type_model = per_type_models.get(fraud_type)

        if type_model is None or n_pos < 10:
            per_type[fraud_type] = {
                "n_examples": n_pos,
                "auc_roc": None,
                "flag": "no_model",
            }
            continue

        indices = fraud_indices + legit_indices
        X_sub = X.iloc[indices]
        y_sub = np.array(
            [1] * len(fraud_indices) + [0] * len(legit_indices), dtype=np.int8
        )
        y_prob_sub = type_model.predict_proba(X_sub)[:, 1]
        auc = float(roc_auc_score(y_sub, y_prob_sub))

        flag = _classify_auc(auc)
        per_type[fraud_type] = {
            "n_examples": n_pos,
            "auc_roc": round(auc, 4),
            "flag": flag,
        }

        if flag in ("too_easy", "too_hard"):
            quality_flags.append({
                "fraud_type": fraud_type,
                "auc_roc": round(auc, 4),
                "flag": flag,
                "recommendation": _recommendation(flag, fraud_type),
            })

    return {
        "overall": {
            "auc_roc": round(auc_roc_overall, 4),
            "auc_pr": round(auc_pr_overall, 4),
            "n_total": len(records),
            "n_fraud": n_fraud,
            "n_legit": n_legit,
            "fraud_rate": round(n_fraud / max(len(records), 1), 4),
        },
        "per_type": per_type,
        "feature_importance": feature_importance,
        "quality_flags": quality_flags,
        "per_record_scores": per_record_scores,
        "model_version": model_registry.get("model_version", "unknown"),
    }


def _classify_auc(auc: float) -> str:
    if auc > _AUC_TOO_EASY:
        return "too_easy"
    if auc >= 0.85:
        return "healthy_high_signal"
    if auc >= _AUC_TOO_HARD:
        return "healthy_low_signal"
    return "too_hard"


def _recommendation(flag: str, fraud_type: str) -> str:
    if flag == "too_easy":
        return (
            f"{fraud_type}: AUC > 0.99 — enricher adds overly deterministic signals. "
            "Add Gaussian noise to velocity fields or widen bot_confidence range."
        )
    return (
        f"{fraud_type}: AUC < 0.70 — classifier cannot separate from legit. "
        "Check that fraud pattern characteristics are applied in the enricher "
        "(new_beneficiary_prob, velocity, time_anomaly)."
    )
