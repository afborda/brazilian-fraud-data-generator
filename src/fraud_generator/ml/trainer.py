"""
LightGBM trainer for synthetic fraud quality validation.

Two public functions:
  train_binary_model(records, model_dir, model_version, test_size=0.2) -> dict
  train_multilabel_models(records, model_dir, model_version, min_examples_per_class=50) -> dict

Both save models via joblib and return metric dicts that feed into the
quality report. LightGBM is a soft dependency — HAS_LGBM=False gracefully
degrades to a message rather than a crash.

Why LightGBM (not XGBoost, not neural nets):
  - Faster than XGBoost on CPU for tabular data of this size (100k–1M rows)
  - Native handling of mixed float/int feature types without preprocessing
  - Built-in feature importance (no SHAP overhead for aggregate reporting)
  - No GPU required, reproducible with fixed seed

Fixed hyperparameters (no AutoML / HPO):
  n_estimators=300, learning_rate=0.05, num_leaves=31, n_jobs=-1
  These are conservative defaults that work well on tabular fraud data.
  Reproducibility matters more than squeezing last 0.1% AUC here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np

try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    lgb = None  # type: ignore[assignment]
    HAS_LGBM = False

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    joblib = None  # type: ignore[assignment]
    HAS_JOBLIB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score

from .features import extract_features

_LGBM_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "n_jobs": -1,
    "random_state": 42,
    "verbosity": -1,
}


def _require_lgbm() -> None:
    if not HAS_LGBM:
        raise ImportError(
            "lightgbm is required for ML training. "
            "Install it with: pip install lightgbm>=4.3.0"
        )
    if not HAS_JOBLIB:
        raise ImportError(
            "joblib is required for model persistence. "
            "Install it with: pip install joblib>=1.3.0"
        )


def train_binary_model(
    records: Sequence[dict[str, Any]],
    model_dir: str | Path,
    model_version: str,
    test_size: float = 0.2,
) -> dict[str, Any]:
    """
    Train a binary fraud classifier (is_fraud = 0/1).

    Saves model to {model_dir}/fraud_detector_{model_version}.pkl.

    Returns a metrics dict:
    {
        "model_path": "...",
        "n_total": 100000,
        "n_fraud": 4821,
        "n_legit": 95179,
        "fraud_rate": 0.0482,
        "auc_roc": 0.9123,
        "auc_pr": 0.7845,
        "feature_importance": {"velocity_transactions_24h": 0.295, ...},
    }
    """
    _require_lgbm()
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    labels = np.array([int(r.get("is_fraud", 0)) for r in records])
    n_fraud = int(labels.sum())
    n_legit = len(labels) - n_fraud

    if n_fraud < 10:
        raise ValueError(f"Too few fraud records ({n_fraud}) to train a model.")

    X = extract_features(records)
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=test_size, random_state=42, stratify=labels
    )

    scale_pos_weight = n_legit / max(n_fraud, 1)
    model = lgb.LGBMClassifier(
        **_LGBM_PARAMS,
        scale_pos_weight=scale_pos_weight,
        class_weight=None,
    )
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    auc_roc = float(roc_auc_score(y_test, y_prob))
    auc_pr = float(average_precision_score(y_test, y_prob))

    importance_raw = model.feature_importances_
    importance_total = importance_raw.sum()
    feature_importance = {
        name: round(float(val) / importance_total, 4)
        for name, val in zip(X.columns, importance_raw)
    }
    feature_importance = dict(
        sorted(feature_importance.items(), key=lambda x: -x[1])
    )

    model_path = model_dir / f"fraud_detector_{model_version}.pkl"
    joblib.dump(model, model_path)

    return {
        "model_path": str(model_path),
        "n_total": len(labels),
        "n_fraud": n_fraud,
        "n_legit": n_legit,
        "fraud_rate": round(n_fraud / len(labels), 4),
        "auc_roc": round(auc_roc, 4),
        "auc_pr": round(auc_pr, 4),
        "feature_importance": feature_importance,
    }


def train_multilabel_models(
    records: Sequence[dict[str, Any]],
    model_dir: str | Path,
    model_version: str,
    min_examples_per_class: int = 50,
) -> dict[str, Any]:
    """
    Train one binary OvR classifier per fraud type.

    For each fraud_type T:
      positives = fraud records of type T
      negatives = all legitimate records
      target = 1 if fraud_type==T else 0

    Saves models to {model_dir}/fraud_type_{TYPE}_{model_version}.pkl.

    Returns:
    {
        "per_type": {
            "CONTA_TOMADA": {"auc_roc": 0.96, "n_examples": 785, "model_path": "..."},
            "ENGENHARIA_SOCIAL": {"auc_roc": 0.72, "n_examples": 412, ...},
            "SMALL_CLASS": {"skipped": true, "reason": "insufficient_data", "n_examples": 12},
        },
        "trained_count": 23,
        "skipped_count": 2,
    }
    """
    _require_lgbm()
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    fraud_records = [r for r in records if r.get("is_fraud")]
    legit_records = [r for r in records if not r.get("is_fraud")]

    fraud_types: dict[str, list] = {}
    for r in fraud_records:
        ft = r.get("fraud_type") or "UNKNOWN"
        fraud_types.setdefault(ft, []).append(r)

    X_legit = extract_features(legit_records)
    y_legit = np.zeros(len(legit_records), dtype=np.int8)

    per_type: dict[str, Any] = {}
    trained_count = 0
    skipped_count = 0

    for fraud_type, fraud_recs in sorted(fraud_types.items()):
        n_pos = len(fraud_recs)
        if n_pos < min_examples_per_class:
            per_type[fraud_type] = {
                "skipped": True,
                "reason": "insufficient_data",
                "n_examples": n_pos,
            }
            skipped_count += 1
            continue

        X_pos = extract_features(fraud_recs)
        y_pos = np.ones(n_pos, dtype=np.int8)

        import pandas as pd
        X_all = pd.concat([X_pos, X_legit], ignore_index=True)
        y_all = np.concatenate([y_pos, y_legit])

        scale_pos_weight = len(y_legit) / max(n_pos, 1)
        model = lgb.LGBMClassifier(
            **_LGBM_PARAMS,
            scale_pos_weight=scale_pos_weight,
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X_all, y_all, test_size=0.2, random_state=42, stratify=y_all
        )
        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:, 1]
        auc_roc = float(roc_auc_score(y_test, y_prob))

        safe_name = fraud_type.replace("/", "_")
        model_path = model_dir / f"fraud_type_{safe_name}_{model_version}.pkl"
        joblib.dump(model, model_path)

        per_type[fraud_type] = {
            "skipped": False,
            "n_examples": n_pos,
            "auc_roc": round(auc_roc, 4),
            "model_path": str(model_path),
        }
        trained_count += 1

    return {
        "per_type": per_type,
        "trained_count": trained_count,
        "skipped_count": skipped_count,
    }
