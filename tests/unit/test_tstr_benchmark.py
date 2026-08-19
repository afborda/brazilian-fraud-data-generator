"""Tests for the TSTR benchmark.

The tool's whole reason to exist is measuring whether a model trained on our
synthetic data works on real traffic. Its previous version ran cross-validation
over a single synthetic file and called that TSTR, which cannot detect transfer
failure by construction. These tests pin the properties that stop it from
drifting back:

* it refuses to run without a real dataset instead of silently substituting one;
* label-derived fields never reach the feature space;
* the verdict fails at BOTH ends — a gap too large means it does not transfer,
  a gap near zero over few features means the number is not credible.
"""

import csv
import json
import random

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from tstr_benchmark import (  # noqa: E402
    LABEL_DERIVED,
    MAX_GAP,
    MIN_GAP,
    _find_label,
    _numeric_columns,
    _verdict,
    main,
    run,
)


def _rows(n, seed, fraud_rate=0.02, shift=0.0):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        fraud = rng.random() < fraud_rate
        out.append({
            "is_fraud": int(fraud),
            "amount": round(rng.lognormvariate(4.0 + shift + (0.8 if fraud else 0), 1.2), 2),
            "velocity_transactions_24h": max(1, int(rng.lognormvariate(0.5 + (0.9 if fraud else 0), 0.7))),
            "device_age_days": int(abs(rng.gauss(400 - (240 if fraud else 0), 300))),
            "hours_inactive": int(abs(rng.gauss(20 + (40 if fraud else 0), 40))),
            "unusual_time": int(rng.random() < (0.25 if fraud else 0.09)),
            "new_beneficiary": int(rng.random() < (0.55 if fraud else 0.13)),
            "accumulated_amount_24h": round(rng.lognormvariate(5.0 + (1.0 if fraud else 0), 1.3), 2),
            # Deve ser ignorado pelo seletor de features.
            "fraud_score": 95 if fraud else 10,
            "transaction_id": f"TX{rng.random()}",
        })
    return out


class TestFeatureSelection:
    def test_label_derived_fields_are_never_features(self):
        rows = _rows(500, seed=1)
        cols = _numeric_columns(rows, "is_fraud")
        for bad in LABEL_DERIVED:
            assert bad not in cols, f"{bad} entrou no espaço de features"

    def test_ids_are_not_features(self):
        rows = _rows(500, seed=1)
        assert "transaction_id" not in _numeric_columns(rows, "is_fraud")

    def test_label_column_is_discovered(self):
        assert _find_label(_rows(10, seed=1)) == "is_fraud"

    def test_missing_label_says_what_was_available(self):
        with pytest.raises(ValueError, match="nenhuma coluna de rótulo"):
            _find_label([{"amount": 1.0, "channel": "PIX"}])


class TestVerdict:
    def test_large_gap_fails(self):
        v = _verdict(MAX_GAP + 0.1, n_features=12)
        assert not v["passed"]
        assert "não transfere" in v["reason"]

    def test_gap_in_band_passes(self):
        assert _verdict((MIN_GAP + MAX_GAP) / 2, n_features=12)["passed"]

    def test_near_zero_gap_with_few_features_fails(self):
        """O critério contra-intuitivo: bom demais também reprova."""
        v = _verdict(MIN_GAP / 4, n_features=2)
        assert not v["passed"]
        assert "bom demais" in v["reason"]

    def test_near_zero_gap_with_many_features_passes(self):
        assert _verdict(MIN_GAP / 4, n_features=20)["passed"]

    def test_missing_gap_fails_rather_than_passing_by_default(self):
        assert not _verdict(None, n_features=12)["passed"]


class TestRun:
    def test_reports_the_three_measurements_and_a_gap(self):
        res = run(_rows(4000, seed=2), _rows(2000, seed=3, shift=0.6))
        assert res["n_shared_features"] >= 6
        for model in res["per_model"].values():
            assert model["trtr"] is not None
            assert model["tstr"] is not None
            assert model["tsts"] is not None
            assert model["gap"] == pytest.approx(model["trtr"] - model["tstr"], abs=1e-4)

    def test_disjoint_schemas_raise_instead_of_returning_a_number(self):
        real = [{"is_fraud": 0, "v1": 1.0, "v2": 2.0} for _ in range(200)]
        real[0]["is_fraud"] = 1
        with pytest.raises(ValueError, match="nenhuma coluna numérica em comum"):
            run(_rows(500, seed=4), real)


class TestCli:
    def test_refuses_without_real_dataset(self, tmp_path, capsys):
        synth = tmp_path / "s.jsonl"
        synth.write_text(
            "\n".join(json.dumps(r) for r in _rows(200, seed=5)), encoding="utf-8"
        )
        code = main(["--synthetic", str(synth)])
        assert code == 2
        err = capsys.readouterr().err
        assert "--real" in err
        assert "cross-validation" in err

    def test_gate_returns_one_when_verdict_fails(self, tmp_path):
        synth = tmp_path / "s.jsonl"
        synth.write_text(
            "\n".join(json.dumps(r) for r in _rows(3000, seed=6)), encoding="utf-8"
        )
        # Real com relação invertida entre features e rótulo: o modelo treinado
        # no sintético deve falhar nele, produzindo gap grande.
        real_rows = _rows(1500, seed=7)
        for r in real_rows:
            r["is_fraud"] = 1 - r["is_fraud"]
        real = tmp_path / "r.csv"
        with real.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(real_rows[0]))
            w.writeheader()
            w.writerows(real_rows)
        assert main(["--synthetic", str(synth), "--real", str(real), "--gate", "--json"]) == 1
