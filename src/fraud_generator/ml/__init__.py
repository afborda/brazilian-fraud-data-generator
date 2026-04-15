"""
fraud_generator.ml — Adversarial quality validation for synthetic fraud datasets.

Public API:
    extract_features(records)          -> pd.DataFrame
    train_binary_model(records, ...)   -> dict (metrics)
    train_multilabel_models(records, ...) -> dict (per-type metrics)
    evaluate_batch(records, model_registry) -> dict (quality report)
    load_models(model_dir, version)    -> dict (model registry)
"""

from .features import extract_features, FEATURE_NAMES
from .trainer import train_binary_model, train_multilabel_models, HAS_LGBM
from .evaluator import evaluate_batch, load_models

__all__ = [
    "extract_features",
    "FEATURE_NAMES",
    "train_binary_model",
    "train_multilabel_models",
    "evaluate_batch",
    "load_models",
    "HAS_LGBM",
]
