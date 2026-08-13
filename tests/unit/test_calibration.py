"""Tests for the calibration registry.

The registry exists so the numbers that decide how hard the data is are visible
in one place, with their provenance attached. These tests guard the two
properties that make it worth having: every consumer reads from it (no literal
drifts back into a module), and an operator who supplies real figures either
gets them applied or gets an error — never a silent no-op.
"""

import json

import pytest

from src.fraud_generator.config import calibration
from src.fraud_generator.config.calibration import CALIBRATED, ESTIMATE, rate, report


class TestRegistryContents:
    def test_every_rate_is_a_probability(self):
        for key, entry in calibration._RATES.items():
            assert 0.0 <= entry.value <= 1.0, f"{key} fora de [0, 1]: {entry.value}"

    def test_every_rate_documents_its_reasoning(self):
        for key, entry in calibration._RATES.items():
            assert entry.note.strip(), f"{key} sem justificativa"
            assert entry.provenance in (ESTIMATE, CALIBRATED)

    def test_unknown_key_raises(self):
        with pytest.raises(KeyError):
            rate("nao.existe")

    def test_report_states_how_many_are_calibrated(self):
        text = report()
        assert "calibradas contra referência real" in text


class TestConsumersReadFromRegistry:
    """A literal drifting back into a module silently removes it from the
    calibration surface, so each consumer is pinned to its registry value."""

    def test_fraud_enricher_shares(self):
        from src.fraud_generator.enrichers import fraud

        assert fraud._LOW_AND_SLOW_SHARE == rate("fraud.low_and_slow_share")
        assert fraud._DECOY_SHARE == rate("fraud.decoy_share")

    def test_transaction_new_beneficiary_prob(self):
        from src.fraud_generator.generators import transaction

        assert transaction._FRAUD_NEW_BENEFICIARY_PROB == rate(
            "fraud.new_beneficiary_prob"
        )

    def test_counterparty_one_off_share(self):
        from src.fraud_generator.config import pix

        assert pix._ONE_OFF_SHARE == rate("counterparty.one_off_share_legit")


class TestOverrides:
    def test_override_applies_and_marks_provenance(self, tmp_path, monkeypatch):
        path = tmp_path / "calibration.json"
        path.write_text(
            json.dumps(
                {
                    "device_age.fraud_contamination": 0.44,
                    "_sources": {"device_age.fraud_contamination": "parceiro X"},
                }
            ),
            encoding="utf-8",
        )
        original = calibration._RATES["device_age.fraud_contamination"]
        monkeypatch.setenv(calibration._OVERRIDE_ENV, str(path))
        try:
            calibration._load_overrides()
            entry = calibration._RATES["device_age.fraud_contamination"]
            assert entry.value == 0.44
            assert entry.provenance == CALIBRATED
            assert entry.source == "parceiro X"
            # A justificativa original sobrevive ao override.
            assert entry.note == original.note
        finally:
            calibration._RATES["device_age.fraud_contamination"] = original

    def test_unknown_key_in_override_raises_instead_of_being_ignored(
        self, tmp_path, monkeypatch
    ):
        path = tmp_path / "calibration.json"
        path.write_text(json.dumps({"device_age.typo": 0.5}), encoding="utf-8")
        monkeypatch.setenv(calibration._OVERRIDE_ENV, str(path))
        with pytest.raises(KeyError, match="chave desconhecida"):
            calibration._load_overrides()

    def test_out_of_range_value_raises(self, tmp_path, monkeypatch):
        path = tmp_path / "calibration.json"
        path.write_text(
            json.dumps({"device_age.fraud_contamination": 1.7}), encoding="utf-8"
        )
        monkeypatch.setenv(calibration._OVERRIDE_ENV, str(path))
        with pytest.raises(ValueError):
            calibration._load_overrides()

    def test_no_env_var_is_a_no_op(self, monkeypatch):
        monkeypatch.delenv(calibration._OVERRIDE_ENV, raising=False)
        before = dict(calibration._RATES)
        calibration._load_overrides()
        assert calibration._RATES == before
