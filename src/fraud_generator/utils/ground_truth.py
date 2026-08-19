"""Split investigation-only fields off the transaction record.

`fraud_labels`, `fraud_chain_id`, `fraud_chain_role`, `fraud_reported_days_after`,
`credential_breach_days_before`, `card_test_phase` and `distributed_attack_group`
are not observable at the moment a transaction is scored — they are the
*output* of an investigation that happens after the fact (a multiclass
taxonomy assigned once a case is worked, a chain/cluster id assigned by an
analyst, how many days it took to report, which phase of a known card-testing
campaign this belongs to). A real bank's antifraud model never sees them at
inference time, and the generator itself never fills them for a class other
than the one they were invented to describe — so leaving them in the same
record as every ordinary feature makes a naive user's holdout evaluation look
artificially good even though the official ML feature set (`ml/features.py`)
never included them.

They still have value as forensic reference data, so instead of deleting them
this module moves them into a companion file, `fraud_ground_truth_NNNNN.jsonl`,
joined to the transaction record by `transaction_id`. `is_fraud` and
`fraud_type` — the base supervised-learning label the product exists to
provide — are duplicated into that file too (for a self-contained join) but
are NOT removed from the transaction record itself: unlike the fields above,
they are already excluded from the ML feature set, and stripping the label
out of a "labeled dataset" product would defeat the product's purpose for
every consumer (tests, `tools/analyze_batch.py`, `ml/`, benchmarks) rather
than fix a leakage risk that the ML pipeline doesn't have.

Usage::

    from ..utils.ground_truth import split_ground_truth

    tx["is_fraud"] = bag.is_fraud
    tx["fraud_type"] = bag.fraud_type
    ground_truth = split_ground_truth(tx)   # pops the 7 fields off tx
"""

from __future__ import annotations

from typing import Any, Dict

# Investigation-consequence fields — see module docstring.
GROUND_TRUTH_FIELDS = (
    "fraud_labels",
    "fraud_chain_id",
    "fraud_chain_role",
    "fraud_reported_days_after",
    "credential_breach_days_before",
    "card_test_phase",
    "distributed_attack_group",
)


def split_ground_truth(tx: Dict[str, Any]) -> Dict[str, Any]:
    """Pop `GROUND_TRUTH_FIELDS` off *tx* and return them as a companion record.

    Mutates *tx* in place (removes the 7 keys). The returned dict always
    carries `transaction_id`, `is_fraud`, and `fraud_type` so the companion
    file is self-contained for a join.
    """
    record = {
        "transaction_id": tx.get("transaction_id"),
        "is_fraud": tx.get("is_fraud"),
        "fraud_type": tx.get("fraud_type"),
    }
    for field in GROUND_TRUTH_FIELDS:
        record[field] = tx.pop(field, None)
    return record


def ground_truth_path(output_path: str) -> str:
    """Derive the companion ground-truth file path from a transactions output path.

    Always `.jsonl` regardless of the primary export format (CSV/Parquet
    readers don't need to handle this side file, and the ground-truth records
    are small enough that format parity isn't worth the complexity). Batch
    numbering mirrors the transactions file so multi-file batches join cleanly:
    `transactions_00003.parquet` -> `fraud_ground_truth_00003.jsonl`.
    """
    import os

    directory, filename = os.path.split(output_path)
    stem = filename.split(".", 1)[0]  # transactions_00003
    if stem.startswith("transactions_"):
        suffix = stem[len("transactions_"):]
    else:
        suffix = stem
    return os.path.join(directory, f"fraud_ground_truth_{suffix}.jsonl")
