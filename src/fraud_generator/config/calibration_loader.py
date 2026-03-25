"""
Calibration loader — applies RAG-calibrated overrides from
fraud_pattern_overrides.json onto FRAUD_PATTERNS at import time.

Override fields supported per pattern key:
  - prevalence        (float)  : replaces pattern['prevalence']
  - amount_multiplier (float)  : replaces pattern['characteristics']['amount_multiplier']
                                 as a symmetric (v, v) tuple

Override file path resolution (first match wins):
  1. $CALIBRATION_OVERRIDES_PATH  env var
  2. <fraudflow_root>/data/rules/fraud_pattern_overrides.json
     (resolved relative to this file: ../../../../data/rules/…)
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Relative to this file: config/ → fraud_generator/ → src/ → synthfin-core/ → fraudflow/
_DEFAULT_OVERRIDES_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "rules" / "fraud_pattern_overrides.json"
)


def _find_overrides_file() -> Optional[Path]:
    env_path = os.environ.get("CALIBRATION_OVERRIDES_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        logger.warning(
            "CALIBRATION_OVERRIDES_PATH is set but file not found: %s", env_path
        )

    if _DEFAULT_OVERRIDES_PATH.is_file():
        return _DEFAULT_OVERRIDES_PATH

    return None


def apply_calibration_overrides(fraud_patterns: Dict[str, Any]) -> Dict[str, Any]:
    """Mutate *fraud_patterns* in-place with RAG-calibrated values.

    Returns the same dict (mutated), so callers can use it as a pass-through.
    Safe to call multiple times; later calls overwrite earlier ones.

    Supported override fields per fraud type:
      ``prevalence``        → ``pattern['prevalence']``
      ``amount_multiplier`` → ``pattern['characteristics']['amount_multiplier']``
                              stored as a symmetric ``(v, v)`` tuple so the
                              existing sampling code (which expects a 2-tuple)
                              keeps working unchanged.
    """
    override_file = _find_overrides_file()
    if override_file is None:
        logger.debug(
            "No calibration overrides file found — using default fraud patterns."
        )
        return fraud_patterns

    try:
        with override_file.open(encoding="utf-8") as fh:
            overrides: Dict[str, Any] = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "Failed to load calibration overrides from %s: %s", override_file, exc
        )
        return fraud_patterns

    applied = skipped = 0
    for fraud_type, fields in overrides.items():
        if fraud_type not in fraud_patterns:
            logger.debug(
                "Override for unknown fraud type %r — ignored.", fraud_type
            )
            skipped += 1
            continue

        pattern = fraud_patterns[fraud_type]

        if "prevalence" in fields and fields["prevalence"] is not None:
            pattern["prevalence"] = float(fields["prevalence"])

        if "amount_multiplier" in fields and fields["amount_multiplier"] is not None:
            raw = fields["amount_multiplier"]
            if isinstance(raw, (list, tuple)) and len(raw) == 2:
                pattern["characteristics"]["amount_multiplier"] = (
                    float(raw[0]),
                    float(raw[1]),
                )
            else:
                mult = float(raw)
                # Store as a symmetric tuple so downstream sampling code is unchanged
                pattern["characteristics"]["amount_multiplier"] = (mult, mult)

        # ── Extended override fields (added for RAG pipeline feedback) ──

        if "fraud_score_base" in fields and fields["fraud_score_base"] is not None:
            pattern["fraud_score_base"] = float(fields["fraud_score_base"])

        if "type_preference" in fields and fields["type_preference"] is not None:
            pattern["characteristics"]["type_preference"] = list(
                fields["type_preference"]
            )

        if "channel_preference" in fields and fields["channel_preference"] is not None:
            pattern["characteristics"]["channel_preference"] = list(
                fields["channel_preference"]
            )

        if (
            "new_beneficiary_prob" in fields
            and fields["new_beneficiary_prob"] is not None
        ):
            pattern["characteristics"]["new_beneficiary_prob"] = float(
                fields["new_beneficiary_prob"]
            )

        applied += 1

    logger.info(
        "Calibration overrides applied: %d patterns updated, %d unknown skipped "
        "(source: %s)",
        applied,
        skipped,
        override_file,
    )
    return fraud_patterns
