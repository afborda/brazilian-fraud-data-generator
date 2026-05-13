"""
Distribution extractor — analyzes user-uploaded CSV/JSONL transaction samples
and produces a CalibrationProfile that the generator can use to match real-world
distributions (amounts, time patterns, transaction types, fraud rates).

Supports files up to 10MB with columns:
  Required: amount (float)
  Optional: timestamp/date, type/transaction_type, is_fraud/fraud (0/1),
            channel, hour, day_of_week
"""

from __future__ import annotations

import csv
import io
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

MAX_ROWS = 500_000
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass
class AmountDistribution:
    mean: float
    median: float
    std: float
    p10: float
    p25: float
    p75: float
    p90: float
    p99: float
    min_val: float
    max_val: float
    log_mean: float
    log_std: float


@dataclass
class TemporalDistribution:
    hour_weights: List[float] = field(default_factory=lambda: [1.0] * 24)
    day_of_week_weights: List[float] = field(default_factory=lambda: [1.0] * 7)


@dataclass
class CalibrationProfile:
    n_records: int
    fraud_rate: Optional[float]
    amount_distribution: AmountDistribution
    temporal_distribution: Optional[TemporalDistribution]
    transaction_type_weights: Optional[Dict[str, float]]
    channel_weights: Optional[Dict[str, float]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CalibrationProfile":
        return cls(
            n_records=d["n_records"],
            fraud_rate=d.get("fraud_rate"),
            amount_distribution=AmountDistribution(**d["amount_distribution"]),
            temporal_distribution=(
                TemporalDistribution(**d["temporal_distribution"])
                if d.get("temporal_distribution")
                else None
            ),
            transaction_type_weights=d.get("transaction_type_weights"),
            channel_weights=d.get("channel_weights"),
            metadata=d.get("metadata", {}),
        )


def _detect_column(headers: List[str], candidates: List[str]) -> Optional[str]:
    lower_headers = {h.lower().strip(): h for h in headers}
    for c in candidates:
        if c.lower() in lower_headers:
            return lower_headers[c.lower()]
    return None


def _parse_float(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        s = str(val).replace(",", ".").replace("R$", "").replace(" ", "")
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_hour(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        s = str(val).strip()
        if len(s) <= 2:
            h = int(s)
            return h if 0 <= h <= 23 else None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(s[:26], fmt).hour
            except ValueError:
                continue
        return None
    except (ValueError, TypeError):
        return None


def _parse_dow(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        s = str(val).strip()
        if s.isdigit():
            d = int(s)
            return d if 0 <= d <= 6 else None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(s[:26], fmt).weekday()
            except ValueError:
                continue
        return None
    except (ValueError, TypeError):
        return None


def _parse_bool(val: Any) -> Optional[bool]:
    if val is None or val == "":
        return None
    s = str(val).strip().lower()
    if s in ("1", "true", "yes", "sim"):
        return True
    if s in ("0", "false", "no", "nao", "não"):
        return False
    return None


def _compute_amount_distribution(amounts: List[float]) -> AmountDistribution:
    arr = np.array(amounts)
    log_vals = np.log1p(arr[arr > 0])
    return AmountDistribution(
        mean=float(np.mean(arr)),
        median=float(np.median(arr)),
        std=float(np.std(arr)),
        p10=float(np.percentile(arr, 10)),
        p25=float(np.percentile(arr, 25)),
        p75=float(np.percentile(arr, 75)),
        p90=float(np.percentile(arr, 90)),
        p99=float(np.percentile(arr, 99)),
        min_val=float(np.min(arr)),
        max_val=float(np.max(arr)),
        log_mean=float(np.mean(log_vals)) if len(log_vals) > 0 else 0.0,
        log_std=float(np.std(log_vals)) if len(log_vals) > 0 else 1.0,
    )


def _normalize_weights(counter: Counter) -> Dict[str, float]:
    total = sum(counter.values())
    if total == 0:
        return {}
    return {k: round(v / total, 6) for k, v in counter.most_common()}


def _normalize_list_weights(counts: List[int], n_bins: int) -> List[float]:
    total = sum(counts)
    if total == 0:
        return [1.0 / n_bins] * n_bins
    return [round(c / total, 6) for c in counts]


def _read_csv(content: bytes) -> List[Dict[str, str]]:
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for i, row in enumerate(reader):
        if i >= MAX_ROWS:
            break
        rows.append(row)
    return rows


def _read_jsonl(content: bytes) -> List[Dict[str, Any]]:
    rows = []
    for line in content.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(rows) >= MAX_ROWS:
            break
    return rows


def extract_distributions(
    content: bytes,
    filename: str,
) -> CalibrationProfile:
    """Extract statistical distributions from uploaded transaction data.

    Args:
        content: Raw file bytes (CSV or JSONL, max 10MB).
        filename: Original filename (used to detect format).

    Returns:
        CalibrationProfile with extracted distributions.

    Raises:
        ValueError: If file is too large, empty, or has no valid amount column.
    """
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE})")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("jsonl", "ndjson", "json"):
        rows = _read_jsonl(content)
    elif ext in ("csv", "tsv", "txt"):
        rows = _read_csv(content)
    else:
        try:
            rows = _read_csv(content)
        except Exception:
            rows = _read_jsonl(content)

    if not rows:
        raise ValueError("File is empty or could not be parsed")

    headers = list(rows[0].keys())

    amount_col = _detect_column(headers, [
        "amount", "valor", "value", "transaction_amount", "amt",
        "valor_transacao", "vl_transacao",
    ])
    if not amount_col:
        raise ValueError(
            f"No amount column found. Available columns: {headers}. "
            "Expected one of: amount, valor, value, transaction_amount"
        )

    timestamp_col = _detect_column(headers, [
        "timestamp", "date", "datetime", "created_at", "data",
        "data_transacao", "dt_transacao", "transaction_date",
    ])
    hour_col = _detect_column(headers, ["hour", "hora", "hr"])
    dow_col = _detect_column(headers, [
        "day_of_week", "dia_semana", "weekday", "dow",
    ])
    fraud_col = _detect_column(headers, [
        "is_fraud", "fraud", "fraude", "label", "is_fraude", "target",
    ])
    type_col = _detect_column(headers, [
        "type", "transaction_type", "tipo", "tipo_transacao", "tx_type",
    ])
    channel_col = _detect_column(headers, [
        "channel", "canal", "payment_method", "metodo_pagamento",
    ])

    amounts: List[float] = []
    hours: List[int] = []
    dows: List[int] = []
    fraud_flags: List[bool] = []
    type_counter: Counter = Counter()
    channel_counter: Counter = Counter()

    for row in rows:
        amt = _parse_float(row.get(amount_col))
        if amt is None or amt < 0:
            continue
        amounts.append(amt)

        if timestamp_col:
            h = _parse_hour(row.get(timestamp_col))
            if h is not None:
                hours.append(h)
            d = _parse_dow(row.get(timestamp_col))
            if d is not None:
                dows.append(d)
        elif hour_col:
            h = _parse_hour(row.get(hour_col))
            if h is not None:
                hours.append(h)

        if dow_col and not timestamp_col:
            d = _parse_dow(row.get(dow_col))
            if d is not None:
                dows.append(d)

        if fraud_col:
            f = _parse_bool(row.get(fraud_col))
            if f is not None:
                fraud_flags.append(f)

        if type_col:
            t = row.get(type_col)
            if t and str(t).strip():
                type_counter[str(t).strip().upper()] += 1

        if channel_col:
            c = row.get(channel_col)
            if c and str(c).strip():
                channel_counter[str(c).strip().upper()] += 1

    if len(amounts) < 10:
        raise ValueError(
            f"Too few valid amount records ({len(amounts)}). Need at least 10."
        )

    amount_dist = _compute_amount_distribution(amounts)

    temporal_dist = None
    if hours:
        hour_counts = [0] * 24
        for h in hours:
            hour_counts[h] += 1
        dow_counts = [0] * 7
        for d in dows:
            dow_counts[d] += 1
        temporal_dist = TemporalDistribution(
            hour_weights=_normalize_list_weights(hour_counts, 24),
            day_of_week_weights=_normalize_list_weights(dow_counts, 7),
        )

    fraud_rate = None
    if fraud_flags:
        fraud_rate = sum(fraud_flags) / len(fraud_flags)

    profile = CalibrationProfile(
        n_records=len(amounts),
        fraud_rate=fraud_rate,
        amount_distribution=amount_dist,
        temporal_distribution=temporal_dist,
        transaction_type_weights=_normalize_weights(type_counter) or None,
        channel_weights=_normalize_weights(channel_counter) or None,
        metadata={
            "source_filename": filename,
            "source_rows_total": len(rows),
            "source_rows_valid": len(amounts),
            "columns_detected": {
                "amount": amount_col,
                "timestamp": timestamp_col,
                "hour": hour_col,
                "day_of_week": dow_col,
                "fraud": fraud_col,
                "type": type_col,
                "channel": channel_col,
            },
        },
    )

    logger.info(
        "Calibration profile extracted: %d records, fraud_rate=%.4f, "
        "mean_amount=%.2f, median_amount=%.2f",
        profile.n_records,
        profile.fraud_rate or 0.0,
        amount_dist.mean,
        amount_dist.median,
    )

    return profile
