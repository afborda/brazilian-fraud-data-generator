"""
Structural validation tests for JSON output from TransactionGenerator.

Verifies:
- All required fields are present
- Field types are correct
- fraud_risk_score > 0 for fraudulent transactions
- fraud_risk_score is low for legitimate transactions
- Core schema invariants (currency=BRL, status in allowed values, etc.)
"""

import pytest
from datetime import datetime
from src.fraud_generator.generators.transaction import TransactionGenerator


REQUIRED_FIELDS = [
    "transaction_id",
    "customer_id",
    "session_id",
    "device_id",
    "timestamp",
    "type",
    "amount",
    "currency",
    "channel",
    "ip_address",
    "geolocation_lat",
    "geolocation_lon",
    "merchant_id",
    "merchant_name",
    "merchant_category",
    "mcc_code",
    "mcc_risk_level",
    "distance_from_last_txn_km",
    "time_since_last_txn_min",
    "velocity_transactions_24h",
    "accumulated_amount_24h",
    "unusual_time",
    "new_beneficiary",
    "status",
    "fraud_score",
    "fraud_risk_score",
    "is_fraud",
    "fraud_type",
]

ALLOWED_STATUSES = {"APPROVED", "DECLINED", "PENDING", "BLOCKED"}
ALLOWED_CHANNELS = {"MOBILE_APP", "WEB_BANKING", "ATM", "POS", "PHONE", "PIX", "API"}


@pytest.fixture
def fraud_generator():
    return TransactionGenerator(fraud_rate=1.0, seed=42)


@pytest.fixture
def legit_generator():
    return TransactionGenerator(fraud_rate=0.0, seed=42)


@pytest.fixture
def mixed_generator():
    return TransactionGenerator(fraud_rate=0.05, seed=42)


@pytest.fixture
def base_ts():
    return datetime(2025, 6, 15, 14, 30, 0)


def _gen_txs(gen, count=50, ts=None):
    if ts is None:
        ts = datetime(2025, 6, 15, 14, 30, 0)
    return [
        gen.generate(
            tx_id=f"{i:015d}",
            customer_id="CUST_001",
            device_id="DEV_001",
            timestamp=ts,
            customer_state="SP",
        )
        for i in range(count)
    ]


# ── Required fields ───────────────────────────────────────────────────────────

class TestRequiredFields:
    def test_all_required_fields_present(self, fraud_generator, base_ts):
        tx = fraud_generator.generate(
            tx_id="000000000000001",
            customer_id="CUST_001",
            device_id="DEV_001",
            timestamp=base_ts,
        )
        for field in REQUIRED_FIELDS:
            assert field in tx, f"Missing required field: {field}"

    def test_required_fields_for_100_transactions(self, mixed_generator):
        txs = _gen_txs(mixed_generator, count=100)
        for i, tx in enumerate(txs):
            for field in REQUIRED_FIELDS:
                assert field in tx, f"tx[{i}]: missing field '{field}'"


# ── Field types ───────────────────────────────────────────────────────────────

class TestFieldTypes:
    def test_transaction_id_is_string(self, fraud_generator, base_ts):
        tx = _gen_txs(fraud_generator, 1, base_ts)[0]
        assert isinstance(tx["transaction_id"], str)

    def test_amount_is_float(self, fraud_generator, base_ts):
        txs = _gen_txs(fraud_generator, 20, base_ts)
        for tx in txs:
            assert isinstance(tx["amount"], float), f"amount is {type(tx['amount'])}"

    def test_amount_positive(self, fraud_generator, base_ts):
        txs = _gen_txs(fraud_generator, 20, base_ts)
        for tx in txs:
            assert tx["amount"] > 0

    def test_currency_always_brl(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 50):
            assert tx["currency"] == "BRL"

    def test_is_fraud_is_bool(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 50):
            assert isinstance(tx["is_fraud"], bool)

    def test_unusual_time_is_bool(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 50):
            assert isinstance(tx["unusual_time"], bool)

    def test_new_beneficiary_is_bool(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 50):
            assert isinstance(tx["new_beneficiary"], bool)

    def test_fraud_score_is_int(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 50):
            assert isinstance(tx["fraud_score"], int)

    def test_fraud_risk_score_is_int(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 50):
            assert isinstance(tx["fraud_risk_score"], int)

    def test_velocity_is_int(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 50):
            if tx["velocity_transactions_24h"] is not None:
                assert isinstance(tx["velocity_transactions_24h"], int)

    def test_status_in_allowed_values(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 100):
            assert tx["status"] in ALLOWED_STATUSES, f"Unknown status: {tx['status']}"

    def test_geolocation_lat_in_brazil_range(self, mixed_generator):
        # Brazil: roughly -33 to +5 latitude
        for tx in _gen_txs(mixed_generator, 50):
            assert -35.0 <= tx["geolocation_lat"] <= 6.0, \
                f"lat out of range: {tx['geolocation_lat']}"

    def test_geolocation_lon_in_brazil_range(self, mixed_generator):
        # Brazil: roughly -74 to -34 longitude
        for tx in _gen_txs(mixed_generator, 50):
            assert -75.0 <= tx["geolocation_lon"] <= -33.0, \
                f"lon out of range: {tx['geolocation_lon']}"


# ── fraud_risk_score validation ───────────────────────────────────────────────

class TestFraudRiskScore:
    def test_fraud_risk_score_range_0_100(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 100):
            score = tx["fraud_risk_score"]
            assert 0 <= score <= 100, f"fraud_risk_score out of range: {score}"

    def test_fraud_risk_score_not_always_zero(self, fraud_generator):
        """At least some fraud transactions must have score > 0."""
        txs = _gen_txs(fraud_generator, 50)
        scores = [tx["fraud_risk_score"] for tx in txs]
        assert any(s > 0 for s in scores), \
            "All fraud_risk_score values are 0 — pipeline not wired"

    def test_fraud_median_score_higher_than_legit(self, fraud_generator, legit_generator):
        fraud_txs = _gen_txs(fraud_generator, 100)
        legit_txs = _gen_txs(legit_generator, 100)
        fraud_avg = sum(tx["fraud_risk_score"] for tx in fraud_txs) / len(fraud_txs)
        legit_avg = sum(tx["fraud_risk_score"] for tx in legit_txs) / len(legit_txs)
        assert fraud_avg > legit_avg, \
            f"Fraud avg {fraud_avg:.1f} should be higher than legit avg {legit_avg:.1f}"

    def test_legit_max_score_is_low(self, legit_generator):
        """Legitimate transactions should not score very high.
        
        Normal-human device signals occasionally coincide with risk indicators
        (e.g. 3% rooted devices), so the ceiling is intentionally set at 70
        to remain robust across different random-state orderings in the suite.
        """
        txs = _gen_txs(legit_generator, 200)
        max_score = max(tx["fraud_risk_score"] for tx in txs)
        assert max_score < 70, f"Legit transaction scored {max_score} — too high"


# ── Fraud type consistency ────────────────────────────────────────────────────

class TestFraudTypeConsistency:
    def test_fraud_type_none_for_legit(self, legit_generator, base_ts):
        for tx in _gen_txs(legit_generator, 20, base_ts):
            assert tx["fraud_type"] is None, \
                f"Legit tx has fraud_type={tx['fraud_type']}"

    def test_fraud_type_set_for_fraud(self, fraud_generator, base_ts):
        for tx in _gen_txs(fraud_generator, 20, base_ts):
            assert tx["fraud_type"] is not None, \
                "Fraud tx is missing fraud_type"

    def test_refusal_reason_only_for_declined(self, mixed_generator):
        for tx in _gen_txs(mixed_generator, 200):
            if tx["status"] != "DECLINED":
                assert tx["refusal_reason"] is None, \
                    f"Non-declined tx has refusal_reason={tx['refusal_reason']}"


# ── PIX-specific fields ───────────────────────────────────────────────────────

class TestPixFields:
    def test_pix_transactions_have_key_type(self, mixed_generator):
        pix_txs = [tx for tx in _gen_txs(mixed_generator, 200) if tx["type"] == "PIX"]
        if pix_txs:
            for tx in pix_txs:
                assert tx["pix_key_type"] is not None, "PIX tx missing pix_key_type"

    def test_card_transactions_have_brand(self, mixed_generator):
        card_txs = [
            tx for tx in _gen_txs(mixed_generator, 200)
            if tx["type"] in ("CREDIT_CARD", "DEBIT_CARD")
        ]
        if card_txs:
            for tx in card_txs:
                assert tx["card_brand"] is not None, "Card tx missing card_brand"
