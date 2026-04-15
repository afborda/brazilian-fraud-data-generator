#!/usr/bin/env python3
"""
data_quality_benchmark.py — Benchmark completo de qualidade dos dados gerados.

Executa baterias de testes de qualidade em datasets gerados pelo synthfin-data:
  1. Completude: campos nulos, vazios, ausentes
  2. Consistência: tipos de dados, ranges válidos, relações
  3. Unicidade: duplicatas em IDs, distribuição de valores
  4. Validade: CPFs, timestamps, coordenadas, IPs
  5. Distribuições estatísticas: entropia, KS-test, chi-squared
  6. Realismo de fraude: taxa, tipos, separabilidade (AUC)
  7. Correlações e anti-padrões

Uso:
  python3 benchmarks/data_quality_benchmark.py --input benchmark_quality_output/transactions_00000.jsonl
  python3 benchmarks/data_quality_benchmark.py --input benchmark_quality_output/transactions_00000.jsonl --save benchmarks/quality_results.json
"""

import json
import math
import sys
import os
import re
import argparse
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Optional imports
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score, average_precision_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Add project root to path for CPF validator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from src.fraud_generator.validators.cpf import validate_cpf
    HAS_CPF_VALIDATOR = True
except ImportError:
    HAS_CPF_VALIDATOR = False


# ─── Constants ────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    'transaction_id', 'customer_id', 'device_id', 'timestamp', 'type',
    'amount', 'currency', 'channel', 'is_fraud', 'fraud_score',
    'geolocation_lat', 'geolocation_lon', 'merchant_id', 'merchant_name',
    'ip_address', 'status',
]

VALID_TYPES = {'PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'TED', 'DOC', 'BOLETO', 'AUTO_DEBIT', 'WITHDRAWAL', 'CASH_WITHDRAWAL'}
VALID_CHANNELS = {'MOBILE_APP', 'WEB', 'WEB_BANKING', 'ATM', 'BRANCH', 'POS', 'PHONE', 'WHATSAPP', 'WHATSAPP_PAY', 'OPEN_BANKING'}
VALID_STATUSES = {'APPROVED', 'DECLINED', 'PENDING', 'REVERSED', 'CANCELLED', 'TIMEOUT', 'ERROR', 'BLOCKED'}
VALID_IP_TYPES = {'RESIDENTIAL', 'MOBILE', 'CORPORATE', 'DATACENTER', 'VPN', 'TOR', 'PROXY'}
VALID_CARD_BRANDS = {'VISA', 'MASTERCARD', 'ELO', 'AMEX', 'HIPERCARD', 'DINERS'}
VALID_NETWORK_TYPES = {'WIFI', '4G', '5G', '3G', 'WIRED', 'ETHERNET'}
VALID_PROFILES = {
    'young_digital', 'conservative_senior', 'business_owner',
    'rural_basic', 'urban_professional', 'student_budget', 'high_income_investor',
    'subscription_heavy', 'family_provider', 'micro_empreendedor',
    'traditional_senior', 'high_spender',
}

BRAZIL_LAT_RANGE = (-33.75, 5.27)
BRAZIL_LON_RANGE = (-73.99, -32.39)  # extended to cover Fernando de Noronha & coast

# Expected distribution targets (BCB / FEBRABAN references)
EXPECTED_TYPE_DIST = {
    'PIX': (0.30, 0.55),         # PIX dominates (~40%)
    'CREDIT_CARD': (0.15, 0.30),
    'DEBIT_CARD': (0.08, 0.20),
}
EXPECTED_FRAUD_RATE = (0.005, 0.05)  # 0.5% to 5%


# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_jsonl(paths: List[str], max_records: int = 200_000) -> List[Dict]:
    records = []
    for path in paths:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if len(records) >= max_records:
                    return records
    return records


# ─── Utility ──────────────────────────────────────────────────────────────────

def shannon_entropy(counts: Dict, normalize: bool = True) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    n = len(counts)
    entropy = 0.0
    for v in counts.values():
        if v > 0:
            p = v / total
            entropy -= p * math.log2(p)
    max_entropy = math.log2(n) if n > 1 else 1.0
    if normalize and max_entropy > 0:
        return entropy / max_entropy
    return entropy


def score_range(value: float, bad: float, good: float) -> float:
    """Map value to 0-10 score. bad=0, good=10."""
    if good > bad:
        return max(0.0, min(10.0, (value - bad) / (good - bad) * 10))
    else:
        return max(0.0, min(10.0, (bad - value) / (bad - good) * 10))


def pct(n: int, total: int) -> float:
    return round(n / total * 100, 2) if total > 0 else 0.0


# ─── Test Batteries ───────────────────────────────────────────────────────────

# Fields that are conditional (only present for specific transaction types)
CONDITIONAL_FIELDS = {
    'auth_3ds', 'card_brand', 'card_entry', 'card_number_hash', 'card_type',
    'cvv_validated', 'installments',  # card-only
    'beneficiary_cpf_hash', 'cpf_hash_pagador', 'cpf_hash_recebedor',
    'destination_bank', 'end_to_end_id', 'holder_type_recebedor',
    'is_devolucao', 'ispb_pagador', 'ispb_recebedor', 'modalidade_iniciacao',
    'pacs_status', 'pix_key_destination', 'pix_key_type',
    'tipo_conta_pagador', 'tipo_conta_recebedor',  # PIX-only
    'fraud_type', 'fraud_signals',  # fraud-only
    'refusal_reason',  # declined-only
    'automation_signature', 'classe_social', 'codigo_ibge_municipio',
    'municipio_nome', 'distance_from_last_txn_km', 'time_since_last_txn_min',
    'velocity_burst_id',  # optional enrichment
    'card_test_phase', 'distributed_attack_group', 'fraud_ring_id',
    'motivo_devolucao_med', 'probe_original_amount', 'ring_role',  # fraud enrichment
}


def test_completeness(records: List[Dict]) -> Dict:
    """Test 1: Completeness — null, empty, missing fields.

    Distinguishes required fields (must always be present) from conditional
    fields (present only for specific transaction types like card or PIX).
    """
    n = len(records)
    field_counts = Counter()
    null_counts = Counter()
    empty_counts = Counter()

    all_fields = set()
    for r in records:
        all_fields.update(r.keys())

    # Only count non-conditional fields for completeness scoring
    core_fields = all_fields - CONDITIONAL_FIELDS

    for r in records:
        for f in all_fields:
            if f not in r:
                field_counts[f] += 1
            elif r[f] is None:
                null_counts[f] += 1
            elif isinstance(r[f], str) and r[f].strip() == '':
                empty_counts[f] += 1

    missing_required = []
    for f in REQUIRED_FIELDS:
        missing_pct = pct(field_counts.get(f, 0), n)
        null_pct = pct(null_counts.get(f, 0), n)
        if missing_pct > 0 or null_pct > 0:
            missing_required.append({
                'field': f, 'missing_pct': missing_pct, 'null_pct': null_pct,
            })

    # Completeness based on core (non-conditional) fields only
    core_missing = sum(field_counts.get(f, 0) for f in core_fields)
    core_null = sum(null_counts.get(f, 0) for f in core_fields)
    core_cells = n * len(core_fields)

    completeness_pct = round((1 - (core_missing + core_null) / core_cells) * 100, 4) if core_cells else 0

    # Score: 10 = 100% complete, 0 = <90% complete
    score = score_range(completeness_pct, 90.0, 100.0)

    return {
        'test': 'completeness',
        'score': round(score, 1),
        'total_records': n,
        'total_fields': len(all_fields),
        'core_fields': len(core_fields),
        'conditional_fields': len(all_fields - core_fields),
        'completeness_pct': completeness_pct,
        'missing_required_fields': missing_required,
        'fields_with_nulls': {k: pct(v, n) for k, v in null_counts.most_common(10) if k in core_fields},
        'fields_with_empty': {k: pct(v, n) for k, v in empty_counts.most_common(10) if k in core_fields},
        'passed': len(missing_required) == 0 and completeness_pct >= 99.0,
    }


def test_uniqueness(records: List[Dict]) -> Dict:
    """Test 2: Uniqueness — duplicate IDs, cardinality."""
    n = len(records)

    tx_ids = [r.get('transaction_id', '') for r in records]
    session_ids = [r.get('session_id', '') for r in records]
    customer_ids = [r.get('customer_id', '') for r in records]
    device_ids = [r.get('device_id', '') for r in records]

    tx_dupes = n - len(set(tx_ids))
    session_dupes = n - len(set(session_ids))

    unique_customers = len(set(customer_ids))
    unique_devices = len(set(device_ids))
    unique_merchants = len(set(r.get('merchant_id', '') for r in records))
    unique_ips = len(set(r.get('ip_address', '') for r in records))

    # transaction_id must be 100% unique
    tx_unique_pct = pct(len(set(tx_ids)), n)
    score = 10.0 if tx_dupes == 0 else score_range(tx_unique_pct, 95.0, 100.0)

    return {
        'test': 'uniqueness',
        'score': round(score, 1),
        'transaction_id_duplicates': tx_dupes,
        'session_id_duplicates': session_dupes,
        'unique_customers': unique_customers,
        'unique_devices': unique_devices,
        'unique_merchants': unique_merchants,
        'unique_ips': unique_ips,
        'tx_per_customer_avg': round(n / unique_customers, 1) if unique_customers else 0,
        'devices_per_customer_avg': round(unique_devices / unique_customers, 2) if unique_customers else 0,
        'passed': tx_dupes == 0,
    }


def test_validity(records: List[Dict]) -> Dict:
    """Test 3: Validity — field values within valid ranges/sets."""
    n = len(records)
    issues = defaultdict(int)

    valid_timestamp = 0
    valid_amount = 0
    valid_lat = 0
    valid_lon = 0
    valid_type = 0
    valid_channel = 0
    valid_status = 0
    valid_ip = 0
    valid_fraud_score = 0
    valid_cpf = 0
    cpf_checked = 0

    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

    for r in records:
        # Timestamp
        ts = r.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(ts)
            if 2020 <= dt.year <= 2030:
                valid_timestamp += 1
            else:
                issues['timestamp_out_of_range'] += 1
        except (ValueError, TypeError):
            issues['timestamp_invalid_format'] += 1

        # Amount
        amt = r.get('amount')
        if isinstance(amt, (int, float)) and 0 < amt < 1_000_000:
            valid_amount += 1
        else:
            issues['amount_invalid'] += 1

        # Geolocation
        lat = r.get('geolocation_lat')
        lon = r.get('geolocation_lon')
        if isinstance(lat, (int, float)) and BRAZIL_LAT_RANGE[0] <= lat <= BRAZIL_LAT_RANGE[1]:
            valid_lat += 1
        else:
            issues['lat_out_of_brazil'] += 1
        if isinstance(lon, (int, float)) and BRAZIL_LON_RANGE[0] <= lon <= BRAZIL_LON_RANGE[1]:
            valid_lon += 1
        else:
            issues['lon_out_of_brazil'] += 1

        # Categorical fields
        if r.get('type') in VALID_TYPES:
            valid_type += 1
        else:
            issues['invalid_type'] += 1

        if r.get('channel') in VALID_CHANNELS:
            valid_channel += 1
        else:
            issues['invalid_channel'] += 1

        if r.get('status') in VALID_STATUSES:
            valid_status += 1
        else:
            issues['invalid_status'] += 1

        # IP
        ip = r.get('ip_address', '')
        if isinstance(ip, str) and ip_pattern.match(ip):
            octets = ip.split('.')
            if all(0 <= int(o) <= 255 for o in octets):
                valid_ip += 1
            else:
                issues['ip_octet_out_of_range'] += 1
        else:
            issues['ip_invalid_format'] += 1

        # Fraud score
        fs = r.get('fraud_score')
        if isinstance(fs, (int, float)) and 0 <= fs <= 100:
            valid_fraud_score += 1
        else:
            issues['fraud_score_out_of_range'] += 1

    # CPF validation (sample)
    if HAS_CPF_VALIDATOR:
        customers_file = None
        for r in records[:1]:
            base_dir = os.path.dirname(args.input[0]) if args else '.'
            cpf_path = os.path.join(base_dir, 'customers.jsonl')
            if os.path.exists(cpf_path):
                customers_file = cpf_path
                break

        if customers_file:
            cpf_sample = []
            with open(customers_file) as f:
                for i, line in enumerate(f):
                    if i >= 1000:
                        break
                    try:
                        c = json.loads(line.strip())
                        cpf = c.get('cpf', '')
                        if cpf:
                            cpf_sample.append(cpf)
                    except json.JSONDecodeError:
                        pass

            cpf_checked = len(cpf_sample)
            valid_cpf = sum(1 for cpf in cpf_sample if validate_cpf(cpf))

    checks = {
        'timestamp': pct(valid_timestamp, n),
        'amount': pct(valid_amount, n),
        'geolocation_lat': pct(valid_lat, n),
        'geolocation_lon': pct(valid_lon, n),
        'type': pct(valid_type, n),
        'channel': pct(valid_channel, n),
        'status': pct(valid_status, n),
        'ip_address': pct(valid_ip, n),
        'fraud_score': pct(valid_fraud_score, n),
    }
    if cpf_checked > 0:
        checks['cpf_valid'] = pct(valid_cpf, cpf_checked)

    avg_valid = sum(checks.values()) / len(checks)
    score = score_range(avg_valid, 90.0, 100.0)

    all_passed = all(v >= 99.0 for k, v in checks.items())

    return {
        'test': 'validity',
        'score': round(score, 1),
        'field_validity_pct': checks,
        'issues': dict(issues),
        'passed': all_passed,
    }


def test_consistency(records: List[Dict]) -> Dict:
    """Test 4: Consistency — logical relationships between fields."""
    n = len(records)
    issues = defaultdict(int)

    for r in records:
        # Fraud consistency: is_fraud=True should have fraud_score > 50 usually
        is_fraud = r.get('is_fraud', False)
        fraud_score = r.get('fraud_score', 0)

        if is_fraud and fraud_score < 20:
            issues['fraud_low_score'] += 1
        if not is_fraud and fraud_score > 90:
            issues['legit_high_score'] += 1

        # Card fields should exist for card transactions
        tx_type = r.get('type', '')
        if tx_type in ('CREDIT_CARD', 'DEBIT_CARD'):
            if not r.get('card_brand'):
                issues['card_missing_brand'] += 1
            if not r.get('card_number_hash'):
                issues['card_missing_hash'] += 1

        # Velocity consistency
        vel_24h = r.get('velocity_transactions_24h', 0)
        acc_24h = r.get('accumulated_amount_24h', 0)
        amount = r.get('amount', 0)
        if isinstance(vel_24h, (int, float)) and vel_24h >= 1:
            if isinstance(acc_24h, (int, float)) and isinstance(amount, (int, float)):
                if acc_24h < amount * 0.99:  # accumulated should be >= current amount
                    issues['accumulated_less_than_amount'] += 1

        # Currency should always be BRL
        if r.get('currency') != 'BRL':
            issues['non_brl_currency'] += 1

        # Profile should be in valid set
        profile = r.get('cliente_perfil', '')
        if profile and profile not in VALID_PROFILES:
            issues['invalid_profile'] += 1

    total_issues = sum(issues.values())
    consistency_pct = pct(n * 5 - total_issues, n * 5)  # 5 checks per record
    score = score_range(consistency_pct, 90.0, 100.0)

    return {
        'test': 'consistency',
        'score': round(score, 1),
        'consistency_pct': consistency_pct,
        'issues': dict(issues),
        'issue_rate_pct': pct(total_issues, n),
        'passed': consistency_pct >= 98.0,
    }


def test_distributions(records: List[Dict]) -> Dict:
    """Test 5: Statistical distributions — entropy, KS-test, chi-squared."""
    n = len(records)

    # Transaction type distribution
    type_counts = Counter(r.get('type', 'UNKNOWN') for r in records)
    type_entropy = shannon_entropy(type_counts)

    # Channel distribution
    channel_counts = Counter(r.get('channel', 'UNKNOWN') for r in records)
    channel_entropy = shannon_entropy(channel_counts)

    # Hour distribution
    hour_counts = Counter()
    for r in records:
        try:
            dt = datetime.fromisoformat(r.get('timestamp', ''))
            hour_counts[dt.hour] += 1
        except (ValueError, TypeError):
            pass
    hour_entropy = shannon_entropy(hour_counts)

    # Day of week distribution
    dow_counts = Counter()
    for r in records:
        try:
            dt = datetime.fromisoformat(r.get('timestamp', ''))
            dow_counts[dt.weekday()] += 1
        except (ValueError, TypeError):
            pass
    dow_entropy = shannon_entropy(dow_counts)

    # Profile distribution
    profile_counts = Counter(r.get('cliente_perfil', 'unknown') for r in records)
    profile_entropy = shannon_entropy(profile_counts)

    # Amount distribution statistics
    amounts = [r.get('amount', 0) for r in records if isinstance(r.get('amount'), (int, float))]
    amount_stats = {}
    if amounts:
        arr = np.array(amounts)
        amount_stats = {
            'mean': round(float(np.mean(arr)), 2),
            'median': round(float(np.median(arr)), 2),
            'std': round(float(np.std(arr)), 2),
            'p5': round(float(np.percentile(arr, 5)), 2),
            'p25': round(float(np.percentile(arr, 25)), 2),
            'p75': round(float(np.percentile(arr, 75)), 2),
            'p95': round(float(np.percentile(arr, 95)), 2),
            'p99': round(float(np.percentile(arr, 99)), 2),
            'skewness': round(float(pd.Series(arr).skew()), 4),
            'kurtosis': round(float(pd.Series(arr).kurtosis()), 4),
        }

    # Type distribution check against expected ranges
    type_dist_pct = {k: round(v / n * 100, 2) for k, v in type_counts.items()}
    type_in_range = {}
    for t, (lo, hi) in EXPECTED_TYPE_DIST.items():
        actual = type_counts.get(t, 0) / n
        type_in_range[t] = {
            'actual_pct': round(actual * 100, 2),
            'expected_range': f'{lo*100:.0f}%-{hi*100:.0f}%',
            'in_range': lo <= actual <= hi,
        }

    # KS-test: amount distribution vs lognormal (realistic for financial data)
    ks_result = None
    if HAS_SCIPY and amounts:
        log_amounts = np.log1p(arr[arr > 0])
        if len(log_amounts) > 100:
            mu, sigma = np.mean(log_amounts), np.std(log_amounts)
            stat, p_value = scipy_stats.kstest(log_amounts, 'norm', args=(mu, sigma))
            ks_result = {
                'statistic': round(float(stat), 6),
                'p_value': round(float(p_value), 6),
                'log_amounts_normal': p_value > 0.01,
            }

    # Chi-squared: hour distribution vs expected (not perfectly uniform)
    chi2_hour = None
    if HAS_SCIPY and len(hour_counts) == 24:
        observed = np.array([hour_counts.get(h, 0) for h in range(24)])
        # Expected: business hours more active (simplified model)
        expected_weights = np.array([
            0.7, 0.4, 0.3, 0.3, 0.3, 0.6, 1.4, 2.5, 4.0, 5.0,
            7.5, 7.0, 4.0, 4.5, 7.0, 7.0, 5.0, 5.5, 6.5, 8.5,
            7.5, 5.5, 3.5, 2.2,
        ])
        expected = expected_weights / expected_weights.sum() * n
        stat, p_value = scipy_stats.chisquare(observed, f_exp=expected)
        chi2_hour = {
            'statistic': round(float(stat), 2),
            'p_value': round(float(p_value), 6),
            'matches_expected_pattern': p_value > 0.001,
        }

    # Score: combine entropies (higher = more realistic diversity)
    entropy_avg = np.mean([type_entropy, channel_entropy, hour_entropy, profile_entropy])
    type_range_ok = all(v['in_range'] for v in type_in_range.values())
    score = score_range(entropy_avg, 0.5, 0.95) * 0.6
    if type_range_ok:
        score += 4.0
    else:
        score += 2.0

    return {
        'test': 'distributions',
        'score': round(min(score, 10.0), 1),
        'entropies': {
            'transaction_type': round(type_entropy, 4),
            'channel': round(channel_entropy, 4),
            'hour_of_day': round(hour_entropy, 4),
            'day_of_week': round(dow_entropy, 4),
            'behavioral_profile': round(profile_entropy, 4),
        },
        'type_distribution_pct': type_dist_pct,
        'type_vs_expected': type_in_range,
        'amount_statistics': amount_stats,
        'ks_test_lognormal': ks_result,
        'chi2_hour_pattern': chi2_hour,
        'passed': entropy_avg > 0.7 and type_range_ok,
    }


def test_fraud_quality(records: List[Dict]) -> Dict:
    """Test 6: Fraud realism — rate, types, separability."""
    n = len(records)

    frauds = [r for r in records if r.get('is_fraud')]
    legits = [r for r in records if not r.get('is_fraud')]
    fraud_rate = len(frauds) / n if n > 0 else 0

    # Fraud type diversity
    fraud_types = Counter(r.get('fraud_type', 'UNKNOWN') for r in frauds if r.get('fraud_type'))
    fraud_type_entropy = shannon_entropy(fraud_types)

    # Fraud score separation
    fraud_scores = [r.get('fraud_score', 0) for r in frauds if isinstance(r.get('fraud_score'), (int, float))]
    legit_scores = [r.get('fraud_score', 0) for r in legits if isinstance(r.get('fraud_score'), (int, float))]

    score_separation = {}
    if fraud_scores and legit_scores:
        score_separation = {
            'fraud_mean_score': round(np.mean(fraud_scores), 2),
            'legit_mean_score': round(np.mean(legit_scores), 2),
            'separation_gap': round(np.mean(fraud_scores) - np.mean(legit_scores), 2),
        }
        if HAS_SCIPY:
            ks_stat, ks_p = scipy_stats.ks_2samp(fraud_scores, legit_scores)
            score_separation['ks_test'] = {
                'statistic': round(float(ks_stat), 4),
                'p_value': float(ks_p),
                'distributions_different': ks_p < 0.05,
            }

    # Amount separation
    fraud_amounts = [r.get('amount', 0) for r in frauds if isinstance(r.get('amount'), (int, float))]
    legit_amounts = [r.get('amount', 0) for r in legits if isinstance(r.get('amount'), (int, float))]
    amount_separation = {}
    if fraud_amounts and legit_amounts:
        amount_separation = {
            'fraud_mean_amount': round(np.mean(fraud_amounts), 2),
            'legit_mean_amount': round(np.mean(legit_amounts), 2),
            'ratio': round(np.mean(fraud_amounts) / np.mean(legit_amounts), 2) if np.mean(legit_amounts) > 0 else 0,
        }

    # AUC via GradientBoosting
    auc_result = None
    if HAS_SKLEARN and len(frauds) >= 20:
        auc_result = _compute_auc(records)

    # Fraud rate in expected range
    rate_ok = EXPECTED_FRAUD_RATE[0] <= fraud_rate <= EXPECTED_FRAUD_RATE[1]

    # Score
    score = 0.0
    if rate_ok:
        score += 3.0
    else:
        score += 1.0
    if len(fraud_types) >= 10:
        score += 2.0
    elif len(fraud_types) >= 5:
        score += 1.0
    if fraud_type_entropy > 0.8:
        score += 2.0
    elif fraud_type_entropy > 0.6:
        score += 1.0
    if auc_result and auc_result.get('auc_roc', 0) > 0.8:
        score += 3.0
    elif auc_result and auc_result.get('auc_roc', 0) > 0.65:
        score += 2.0
    elif not auc_result:
        score += 1.5  # partial credit if can't compute

    return {
        'test': 'fraud_quality',
        'score': round(min(score, 10.0), 1),
        'fraud_rate_pct': round(fraud_rate * 100, 4),
        'fraud_rate_in_range': rate_ok,
        'expected_range': f'{EXPECTED_FRAUD_RATE[0]*100:.1f}%-{EXPECTED_FRAUD_RATE[1]*100:.1f}%',
        'total_frauds': len(frauds),
        'total_legit': len(legits),
        'fraud_types': len(fraud_types),
        'fraud_type_entropy': round(fraud_type_entropy, 4),
        'fraud_type_distribution': {k: round(v / len(frauds) * 100, 2) for k, v in fraud_types.most_common(15)} if frauds else {},
        'score_separation': score_separation,
        'amount_separation': amount_separation,
        'ml_separability': auc_result,
        'passed': rate_ok and len(fraud_types) >= 5,
    }


def _compute_auc(records: List[Dict]) -> Optional[Dict]:
    """Compute AUC-ROC using basic features."""
    features = []
    labels = []

    for r in records:
        try:
            feat = [
                float(r.get('amount', 0)),
                float(r.get('fraud_score', 0)),
                float(r.get('fraud_risk_score', 0)),
                float(r.get('velocity_transactions_24h', 0)),
                float(r.get('accumulated_amount_24h', 0)),
                float(r.get('customer_velocity_z_score', 0)),
                float(r.get('device_age_days', 0)),
                float(r.get('bot_confidence_score', 0)),
                float(r.get('distance_from_last_km', 0)),
                float(r.get('hours_inactive', 0)),
                1.0 if r.get('unusual_time') else 0.0,
                1.0 if r.get('new_beneficiary') else 0.0,
                1.0 if r.get('vpn_active') else 0.0,
                1.0 if r.get('emulator_detected') else 0.0,
                1.0 if r.get('is_impossible_travel') else 0.0,
                1.0 if r.get('sim_swap_recent') else 0.0,
                1.0 if r.get('active_call_during_tx') else 0.0,
                1.0 if r.get('recipient_is_mule') else 0.0,
            ]
            features.append(feat)
            labels.append(1 if r.get('is_fraud') else 0)
        except (TypeError, ValueError):
            continue

    if len(features) < 100 or sum(labels) < 10:
        return None

    X = np.array(features)
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    clf = GradientBoostingClassifier(
        n_estimators=100, max_depth=4, random_state=42, subsample=0.8,
    )
    clf.fit(X_train, y_train)

    y_prob = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)
    ap = average_precision_score(y_test, y_prob)

    feature_names = [
        'amount', 'fraud_score', 'fraud_risk_score', 'velocity_24h',
        'accumulated_24h', 'velocity_z_score', 'device_age_days',
        'bot_confidence', 'distance_last_km', 'hours_inactive',
        'unusual_time', 'new_beneficiary', 'vpn_active', 'emulator',
        'impossible_travel', 'sim_swap', 'active_call', 'recipient_mule',
    ]
    importances = clf.feature_importances_
    top_features = sorted(
        zip(feature_names, importances), key=lambda x: -x[1]
    )[:10]

    return {
        'auc_roc': round(float(auc), 4),
        'average_precision': round(float(ap), 4),
        'test_size': len(y_test),
        'test_fraud_count': int(y_test.sum()),
        'top_features': {name: round(float(imp), 4) for name, imp in top_features},
    }


def test_temporal_patterns(records: List[Dict]) -> Dict:
    """Test 7: Temporal realism — business hours, weekday patterns."""
    n = len(records)

    hours = []
    weekdays = []
    dates = []
    for r in records:
        try:
            dt = datetime.fromisoformat(r.get('timestamp', ''))
            hours.append(dt.hour)
            weekdays.append(dt.weekday())
            dates.append(dt.date())
        except (ValueError, TypeError):
            pass

    if not hours:
        return {'test': 'temporal_patterns', 'score': 0, 'error': 'no valid timestamps', 'passed': False}

    hour_counts = Counter(hours)
    dow_counts = Counter(weekdays)

    # Business hours (8-20) should have more transactions than night (0-6)
    business_pct = sum(hour_counts.get(h, 0) for h in range(8, 21)) / len(hours) * 100
    night_pct = sum(hour_counts.get(h, 0) for h in range(0, 7)) / len(hours) * 100

    # Weekday (Mon-Fri) should have more than weekend
    weekday_pct = sum(dow_counts.get(d, 0) for d in range(5)) / len(weekdays) * 100
    weekend_pct = sum(dow_counts.get(d, 0) for d in range(5, 7)) / len(weekdays) * 100

    # Date range
    unique_dates = len(set(dates))
    date_range_days = (max(dates) - min(dates)).days if len(set(dates)) > 1 else 0

    # Peak hours (common in Brazilian banking)
    peak_morning = sum(hour_counts.get(h, 0) for h in [10, 11]) / len(hours)
    peak_afternoon = sum(hour_counts.get(h, 0) for h in [14, 15]) / len(hours)
    peak_evening = sum(hour_counts.get(h, 0) for h in [19, 20]) / len(hours)
    has_realistic_peaks = peak_morning > 0.08 and peak_afternoon > 0.08 and peak_evening > 0.08

    # Score
    score = 0.0
    if business_pct > 75:
        score += 3.0
    elif business_pct > 60:
        score += 2.0
    if weekday_pct > 60:
        score += 2.0
    if has_realistic_peaks:
        score += 3.0
    elif peak_morning > 0.05 or peak_evening > 0.05:
        score += 1.5
    if date_range_days >= 30:
        score += 2.0
    elif date_range_days >= 7:
        score += 1.0

    return {
        'test': 'temporal_patterns',
        'score': round(min(score, 10.0), 1),
        'business_hours_pct': round(business_pct, 2),
        'night_hours_pct': round(night_pct, 2),
        'weekday_pct': round(weekday_pct, 2),
        'weekend_pct': round(weekend_pct, 2),
        'has_realistic_peaks': has_realistic_peaks,
        'peak_morning_pct': round(peak_morning * 100, 2),
        'peak_afternoon_pct': round(peak_afternoon * 100, 2),
        'peak_evening_pct': round(peak_evening * 100, 2),
        'unique_dates': unique_dates,
        'date_range_days': date_range_days,
        'passed': business_pct > 70 and has_realistic_peaks,
    }


# ─── Main Benchmark Runner ───────────────────────────────────────────────────

def run_benchmark(records: List[Dict]) -> Dict:
    """Run all quality benchmarks and produce final report."""
    start = time.time()

    results = {}
    tests = [
        ('completeness', test_completeness),
        ('uniqueness', test_uniqueness),
        ('validity', test_validity),
        ('consistency', test_consistency),
        ('distributions', test_distributions),
        ('fraud_quality', test_fraud_quality),
        ('temporal_patterns', test_temporal_patterns),
    ]

    for name, fn in tests:
        t0 = time.time()
        results[name] = fn(records)
        results[name]['duration_sec'] = round(time.time() - t0, 3)

    # Compute overall score
    scores = [results[name]['score'] for name in results]
    passed = [results[name].get('passed', False) for name in results]

    overall = {
        'overall_score': round(np.mean(scores), 2),
        'max_possible': 10.0,
        'tests_passed': sum(passed),
        'tests_total': len(tests),
        'all_passed': all(passed),
        'grade': _grade(np.mean(scores)),
        'scores_by_test': {name: results[name]['score'] for name in results},
        'total_duration_sec': round(time.time() - start, 2),
        'records_analyzed': len(records),
        'timestamp': datetime.now().isoformat(),
    }

    return {'summary': overall, 'tests': results}


def _grade(score: float) -> str:
    if score >= 9.0:
        return 'A+'
    elif score >= 8.0:
        return 'A'
    elif score >= 7.0:
        return 'B'
    elif score >= 6.0:
        return 'C'
    elif score >= 5.0:
        return 'D'
    return 'F'


def print_report(report: Dict) -> None:
    """Pretty-print the benchmark report."""
    s = report['summary']

    print()
    print('=' * 70)
    print('  DATA QUALITY BENCHMARK REPORT')
    print('=' * 70)
    print(f'  Records analisados  : {s["records_analyzed"]:>10,}')
    print(f'  Tempo total         : {s["total_duration_sec"]:>10.2f}s')
    print(f'  Testes executados   : {s["tests_total"]:>10}')
    print(f'  Testes aprovados    : {s["tests_passed"]:>10} / {s["tests_total"]}')
    print(f'  Score GERAL         : {s["overall_score"]:>10.2f} / {s["max_possible"]:.1f}')
    print(f'  Grade               : {s["grade"]:>10}')
    print('=' * 70)
    print()

    # Individual test scores
    print('  SCORES POR TESTE:')
    print('  ' + '-' * 50)

    test_labels = {
        'completeness': 'Completude',
        'uniqueness': 'Unicidade',
        'validity': 'Validade',
        'consistency': 'Consistência',
        'distributions': 'Distribuições',
        'fraud_quality': 'Qualidade Fraude',
        'temporal_patterns': 'Padrões Temporais',
    }

    for name, label in test_labels.items():
        t = report['tests'].get(name, {})
        score = t.get('score', 0)
        passed = t.get('passed', False)
        duration = t.get('duration_sec', 0)
        status = 'PASS' if passed else 'FAIL'
        bar = '█' * int(score) + '░' * (10 - int(score))
        print(f'  {label:<22} {bar} {score:>5.1f}/10  [{status}]  ({duration:.3f}s)')

    print()

    # Key highlights
    tests = report['tests']

    # Completeness
    c = tests.get('completeness', {})
    print(f'  Completude: {c.get("completeness_pct", 0):.2f}%')
    if c.get('missing_required_fields'):
        for mf in c['missing_required_fields']:
            print(f'    ⚠  {mf["field"]}: {mf["missing_pct"]}% ausente, {mf["null_pct"]}% nulo')

    # Uniqueness
    u = tests.get('uniqueness', {})
    print(f'  IDs duplicados: {u.get("transaction_id_duplicates", 0)}')
    print(f'  Clientes únicos: {u.get("unique_customers", 0):,}  |  Tx/cliente: {u.get("tx_per_customer_avg", 0):.1f}')

    # Fraud quality
    fq = tests.get('fraud_quality', {})
    print(f'  Taxa de fraude: {fq.get("fraud_rate_pct", 0):.2f}%  (esperado: {fq.get("expected_range", "")})')
    print(f'  Tipos de fraude: {fq.get("fraud_types", 0)}')
    ml = fq.get('ml_separability')
    if ml:
        print(f'  AUC-ROC: {ml["auc_roc"]:.4f}  |  Avg Precision: {ml["average_precision"]:.4f}')
        if ml.get('top_features'):
            top3 = list(ml['top_features'].items())[:3]
            feats = ', '.join(f'{k}({v:.3f})' for k, v in top3)
            print(f'  Top features: {feats}')

    # Temporal
    tp = tests.get('temporal_patterns', {})
    print(f'  Horário comercial: {tp.get("business_hours_pct", 0):.1f}%  |  Picos realistas: {"Sim" if tp.get("has_realistic_peaks") else "Não"}')
    print(f'  Range temporal: {tp.get("date_range_days", 0)} dias  |  Dias únicos: {tp.get("unique_dates", 0)}')

    # Distributions
    d = tests.get('distributions', {})
    if d.get('type_vs_expected'):
        print('  Distribuição tipos vs esperado:')
        for t_name, info in d['type_vs_expected'].items():
            status = '✓' if info['in_range'] else '✗'
            print(f'    {status} {t_name}: {info["actual_pct"]:.1f}% (esperado: {info["expected_range"]})')

    print()
    print('=' * 70)
    if s['all_passed']:
        print('  ✅ TODOS OS TESTES APROVADOS')
    else:
        failed = [name for name in test_labels if not tests.get(name, {}).get('passed', False)]
        print(f'  ⚠  Testes reprovados: {", ".join(failed)}')
    print('=' * 70)
    print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    global args
    parser = argparse.ArgumentParser(description='Benchmark de qualidade de dados do synthfin-data')
    parser.add_argument('--input', required=True, nargs='+', help='Arquivo(s) JSONL de transações')
    parser.add_argument('--save', help='Salvar resultado em JSON')
    parser.add_argument('--max-records', type=int, default=100_000, help='Máximo de registros (default: 100000)')
    args = parser.parse_args()

    # Expand globs
    import glob
    paths = []
    for p in args.input:
        expanded = glob.glob(p)
        paths.extend(expanded if expanded else [p])

    print(f'📂 Carregando {len(paths)} arquivo(s)...')
    records = load_jsonl(paths, args.max_records)
    print(f'✅ {len(records):,} registros carregados')
    print()

    print('🔬 Executando benchmark de qualidade...')
    report = run_benchmark(records)

    print_report(report)

    if args.save:
        # Convert numpy types for JSON serialization
        def convert(obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            raise TypeError(f'Object of type {type(obj)} is not JSON serializable')

        with open(args.save, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=convert)
        print(f'  💾 Resultado salvo em: {args.save}')
        print()


if __name__ == '__main__':
    args = None
    main()
