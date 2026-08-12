"""Guard tests for the ML feature set.

These exist because the quality pipeline once fed the classifier fields that the
generator itself derives from `is_fraud`. That made the binary AUC saturate near
1.0 and turned the A+ grade into a measure of leakage strength: 21 of 25
per-type models reported auc_roc exactly 1.0.

The tests are cheap and deliberately blunt — they fail loudly if a
label-derived field is put back into the feature set.
"""

import pytest

from src.fraud_generator.ml.features import (
    FEATURE_DTYPES,
    FEATURE_NAMES,
    _DEFAULTS,
)

# Fields the generator computes FROM the label, or that are the label. None of
# these exist in a real bank's feed before its own model has run.
LABEL_DERIVED_FIELDS = frozenset({
    "is_fraud",
    "fraud_type",
    "fraud_labels",
    "fraud_signals",
    "fraud_score",
    "fraud_risk_score",
    "fraud_chain_id",
    "fraud_chain_role",
    "dict_fraud_marker",
})


class TestFeatureSetExcludesLabelDerivedFields:
    @pytest.mark.parametrize("field", sorted(LABEL_DERIVED_FIELDS))
    def test_field_is_not_a_feature(self, field):
        assert field not in FEATURE_NAMES, (
            f"'{field}' is derived from the label by the generator. Feeding it "
            f"back to the classifier is circular and saturates AUC at ~1.0. "
            f"See the module docstring in ml/features.py."
        )

    def test_no_feature_name_looks_like_a_label(self):
        suspicious = [f for f in FEATURE_NAMES if f.startswith("fraud_")]
        assert not suspicious, (
            f"Features prefixed 'fraud_' are almost always generator-side "
            f"artefacts rather than observable signals: {suspicious}"
        )


class TestFeatureTablesStayInSync:
    """A field removed from one table and left in another silently breaks
    extraction, so the three tables are checked against each other."""

    def test_every_feature_has_a_dtype(self):
        missing = [f for f in FEATURE_NAMES if f not in FEATURE_DTYPES]
        assert not missing, f"features without dtype: {missing}"

    def test_every_feature_has_a_default(self):
        missing = [f for f in FEATURE_NAMES if f not in _DEFAULTS]
        assert not missing, f"features without default: {missing}"

    def test_no_orphan_dtype(self):
        orphans = [f for f in FEATURE_DTYPES if f not in FEATURE_NAMES]
        assert not orphans, f"dtypes for non-features: {orphans}"

    def test_no_orphan_default(self):
        orphans = [f for f in _DEFAULTS if f not in FEATURE_NAMES]
        assert not orphans, f"defaults for non-features: {orphans}"

    def test_feature_names_are_unique(self):
        assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES))
