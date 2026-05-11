"""
Config validation tests — ensures all config modules follow the
*_LIST + *_WEIGHTS + get_*() convention and data integrity invariants.

Checks:
  1. All *_WEIGHTS sum to approximately 1.0 (or are positive proportional weights)
  2. All *_LIST and *_WEIGHTS pairs have matching lengths
  3. All get_*() lookup functions return valid values (no KeyError)
  4. All weights are non-negative
"""

import importlib
import inspect
from datetime import date

import pytest


CONFIG_MODULES = [
    "src.fraud_generator.config.banks",
    "src.fraud_generator.config.devices",
    "src.fraud_generator.config.distributions",
    "src.fraud_generator.config.fraud_patterns",
    "src.fraud_generator.config.geography",
    "src.fraud_generator.config.merchants",
    "src.fraud_generator.config.pix",
    "src.fraud_generator.config.rideshare",
    "src.fraud_generator.config.seasonality",
    "src.fraud_generator.config.transactions",
    "src.fraud_generator.config.weather",
]


def _get_list_weight_pairs(module):
    """Find all (*_LIST, *_WEIGHTS) pairs in a module."""
    attrs = dir(module)
    pairs = []
    for name in attrs:
        if name.endswith("_LIST") and not name.startswith("_"):
            weight_name = name.replace("_LIST", "_WEIGHTS")
            if weight_name in attrs:
                pairs.append((name, weight_name))
    return pairs


def _load_all_modules():
    modules = []
    for mod_path in CONFIG_MODULES:
        try:
            modules.append((mod_path, importlib.import_module(mod_path)))
        except ImportError:
            pass
    return modules


ALL_MODULES = _load_all_modules()


# ── 1. LIST/WEIGHTS length match ────────────────────────────────────────────

class TestListWeightsLengthMatch:
    @pytest.mark.parametrize("mod_path,mod", ALL_MODULES, ids=[m[0].split(".")[-1] for m in ALL_MODULES])
    def test_list_weights_same_length(self, mod_path, mod):
        pairs = _get_list_weight_pairs(mod)
        for list_name, weight_name in pairs:
            lst = getattr(mod, list_name)
            wts = getattr(mod, weight_name)
            assert len(lst) == len(wts), (
                f"{mod_path}.{list_name} has {len(lst)} items but "
                f"{weight_name} has {len(wts)} weights"
            )


# ── 2. Weights are non-negative ─────────────────────────────────────────────

class TestWeightsNonNegative:
    @pytest.mark.parametrize("mod_path,mod", ALL_MODULES, ids=[m[0].split(".")[-1] for m in ALL_MODULES])
    def test_all_weights_non_negative(self, mod_path, mod):
        for name in dir(mod):
            if name.endswith("_WEIGHTS") and not name.startswith("_"):
                weights = getattr(mod, name)
                if isinstance(weights, (list, tuple)):
                    for i, w in enumerate(weights):
                        assert w >= 0, (
                            f"{mod_path}.{name}[{i}] is negative: {w}"
                        )


# ── 3. Weights sum > 0 (proportional weights are valid) ─────────────────────

class TestWeightsSumPositive:
    @pytest.mark.parametrize("mod_path,mod", ALL_MODULES, ids=[m[0].split(".")[-1] for m in ALL_MODULES])
    def test_weights_sum_positive(self, mod_path, mod):
        for name in dir(mod):
            if name.endswith("_WEIGHTS") and not name.startswith("_"):
                weights = getattr(mod, name)
                if isinstance(weights, (list, tuple)) and len(weights) > 0:
                    total = sum(weights)
                    assert total > 0, (
                        f"{mod_path}.{name} sums to {total} (must be > 0)"
                    )


# ── 4. get_*() functions don't raise on valid inputs ────────────────────────

class TestGetFunctions:
    def test_get_bank_info(self):
        from src.fraud_generator.config.banks import get_bank_info, BANK_CODES
        for code in BANK_CODES:
            info = get_bank_info(code)
            assert isinstance(info, dict)
            assert "name" in info

    def test_get_bank_name(self):
        from src.fraud_generator.config.banks import get_bank_name, BANK_CODES
        for code in BANK_CODES:
            name = get_bank_name(code)
            assert isinstance(name, str)
            assert len(name) > 0

    def test_get_state_info(self):
        from src.fraud_generator.config.geography import get_state_info, ESTADOS_LIST
        for code in ESTADOS_LIST:
            info = get_state_info(code)
            assert "name" in info
            assert "lat" in info
            assert "lon" in info

    def test_get_state_coordinates(self):
        from src.fraud_generator.config.geography import get_state_coordinates, ESTADOS_LIST
        for code in ESTADOS_LIST:
            lat, lon = get_state_coordinates(code)
            assert -34 < lat < 6, f"{code} lat={lat} out of Brazil bounds"
            assert -74 < lon < -34, f"{code} lon={lon} out of Brazil bounds"

    def test_get_cities_for_state(self):
        from src.fraud_generator.config.geography import get_cities_for_state, ESTADOS_LIST
        for code in ESTADOS_LIST:
            cities = get_cities_for_state(code)
            assert len(cities) > 0, f"No cities for {code}"

    def test_get_fraud_concentration(self):
        from src.fraud_generator.config.geography import get_fraud_concentration, ESTADOS_LIST
        for code in ESTADOS_LIST:
            fc = get_fraud_concentration(code)
            assert 0 < fc < 5, f"{code} fraud_concentration={fc} seems wrong"

    def test_get_mcc_info(self):
        from src.fraud_generator.config.merchants import get_mcc_info, MCC_LIST
        for mcc in MCC_LIST:
            info = get_mcc_info(mcc)
            assert isinstance(info, dict)

    def test_get_merchants_for_mcc(self):
        from src.fraud_generator.config.merchants import get_merchants_for_mcc, MCC_LIST
        for mcc in MCC_LIST:
            merchants = get_merchants_for_mcc(mcc)
            assert isinstance(merchants, list)
            assert len(merchants) > 0

    def test_get_device_category(self):
        from src.fraud_generator.config.devices import (
            get_device_category, DEVICE_TYPES_LIST,
        )
        for dt in DEVICE_TYPES_LIST:
            cat = get_device_category(dt)
            assert isinstance(cat, str) and len(cat) > 0, (
                f"Empty category for device type '{dt}'"
            )

    def test_get_surge_multiplier(self):
        from src.fraud_generator.config.rideshare import get_surge_multiplier
        for hour in range(24):
            mult = get_surge_multiplier(hour)
            assert 0.5 <= mult <= 5.0, f"Surge at {hour}h = {mult}"

    def test_get_app_categories(self):
        from src.fraud_generator.config.rideshare import get_app_categories, APPS_LIST
        for app in APPS_LIST:
            cats = get_app_categories(app)
            assert len(cats) > 0

    def test_get_pois_for_state(self):
        from src.fraud_generator.config.rideshare import get_pois_for_state
        for state in ["SP", "RJ", "MG", "BA", "DF"]:
            pois = get_pois_for_state(state)
            assert len(pois) > 0
            for poi in pois:
                assert "name" in poi
                assert "type" in poi

    def test_get_monthly_multiplier(self):
        from src.fraud_generator.config.seasonality import get_monthly_multiplier
        for month in range(1, 13):
            mult = get_monthly_multiplier(month)
            assert 0.5 <= mult <= 2.0, f"Month {month} multiplier={mult}"

    def test_get_day_multiplier(self):
        from src.fraud_generator.config.seasonality import get_day_multiplier
        d = date(2025, 1, 15)
        mult = get_day_multiplier(d)
        assert 0.3 <= mult <= 4.0

    def test_get_day_multiplier_black_friday(self):
        from src.fraud_generator.config.seasonality import get_day_multiplier
        bf = date(2025, 11, 28)
        mult = get_day_multiplier(bf)
        assert mult >= 2.0, "Black Friday should have high multiplier"

    def test_get_hour_weights_for_fraud(self):
        from src.fraud_generator.config.seasonality import get_hour_weights_for_fraud
        for fraud_type in ["CONTA_TOMADA", "ENGENHARIA_SOCIAL", "FRAUDE_DELIVERY_APP", "UNKNOWN"]:
            weights = get_hour_weights_for_fraud(fraud_type)
            assert len(weights) == 24
            assert all(w >= 0 for w in weights)

    def test_get_seasonal_fraud_boost(self):
        from src.fraud_generator.config.seasonality import get_seasonal_fraud_boost
        boost = get_seasonal_fraud_boost(11, "PHISHING_BANCARIO")
        assert boost > 1.0, "November phishing should be boosted"
        neutral = get_seasonal_fraud_boost(6, "NONEXISTENT_TYPE")
        assert neutral == 1.0

    def test_get_region_for_state(self):
        from src.fraud_generator.config.weather import get_region_for_state
        regions = {"NORTE", "NORDESTE", "CENTRO_OESTE", "SUDESTE", "SUL"}
        for state in ["SP", "AM", "BA", "GO", "RS"]:
            region = get_region_for_state(state)
            assert region in regions, f"Unknown region '{region}' for {state}"

    def test_get_season(self):
        from src.fraud_generator.config.weather import get_season
        expected = {1: "verao", 4: "outono", 7: "inverno", 10: "primavera"}
        for month, season in expected.items():
            assert get_season(month) == season


# ── 5. Rideshare random selectors return valid values ────────────────────────

class TestRandomSelectors:
    def test_get_random_app(self):
        from src.fraud_generator.config.rideshare import get_random_app, APPS_LIST
        for _ in range(100):
            assert get_random_app() in APPS_LIST

    def test_get_random_payment_method(self):
        from src.fraud_generator.config.rideshare import get_random_payment_method, PAYMENT_METHODS_LIST
        for _ in range(100):
            assert get_random_payment_method() in PAYMENT_METHODS_LIST

    def test_get_random_fraud_type(self):
        from src.fraud_generator.config.rideshare import get_random_fraud_type, FRAUD_TYPES_LIST
        for _ in range(100):
            assert get_random_fraud_type() in FRAUD_TYPES_LIST

    def test_get_random_final_status(self):
        from src.fraud_generator.config.rideshare import get_random_final_status, FINAL_STATUS_LIST
        for _ in range(100):
            assert get_random_final_status() in FINAL_STATUS_LIST

    def test_pick_hour(self):
        from src.fraud_generator.config.seasonality import pick_hour
        for _ in range(100):
            h = pick_hour()
            assert 0 <= h <= 23

    def test_pick_weighted_date(self):
        from src.fraud_generator.config.seasonality import pick_weighted_date
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        for _ in range(50):
            d = pick_weighted_date(start, end)
            assert start <= d <= end
