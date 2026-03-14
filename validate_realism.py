#!/usr/bin/env python3
"""
validate_realism.py — Métricas de realismo do dataset gerado.

Uso:
  python3 validate_realism.py --input baseline_before/transactions_00000.jsonl
  python3 validate_realism.py --input output/*.jsonl --save baseline_before/REALISM_METRICS.json
  python3 validate_realism.py --input output/*.jsonl --auc   (requer scikit-learn)

Métricas produzidas:
  - temporal_entropy       : quão distribuído é o horário (0=uniforme ideal, 1=concentrado)
  - hour_distribution      : % por hora do dia (0-23)
  - dow_distribution       : % por dia da semana (0=Seg, 6=Dom)
  - geo_entropy            : diversidade geográfica (lat/lon → cluster de estado)
  - state_distribution     : % por estado inferido
  - fraud_rate             : % total de registros fraudulentos
  - fraud_type_distribution: % por tipo de fraude
  - amount_stats           : mean, median, p95, p99 por is_fraud
  - auc_simple (opcional)  : AUC de XGBoost simples em features básicas
  - score_realism          : pontuação 0-10 composta
"""

import json
import math
import sys
import os
import glob
import argparse
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Optional


# ─── Leitura de arquivos ──────────────────────────────────────────────────────

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


# ─── Entropia de Shannon normalizada ─────────────────────────────────────────

def shannon_entropy(counts: Dict, normalize: bool = True) -> float:
    """
    Retorna entropia de Shannon. normalize=True → 0..1 (1.0 = distribuição uniforme).
    """
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


# ─── Inferir estado por lat/lon ───────────────────────────────────────────────

# Centróides aproximados dos estados brasileiros
_STATE_CENTROIDS = {
    'SP': (-23.55, -46.64), 'RJ': (-22.91, -43.17), 'MG': (-19.92, -43.94),
    'BA': (-12.97, -38.51), 'RS': (-30.03, -51.23), 'PR': (-25.43, -49.27),
    'PE': (-8.05,  -34.88), 'CE': (-3.72,  -38.54), 'PA': (-1.46,  -48.50),
    'SC': (-27.60, -48.55), 'GO': (-16.68, -49.25), 'MA': (-2.53,  -44.27),
    'PB': (-7.12,  -34.86), 'ES': (-20.32, -40.34), 'AM': (-3.10,  -60.02),
    'RN': (-5.79,  -35.21), 'PI': (-5.09,  -42.80), 'AL': (-9.67,  -35.74),
    'MT': (-15.60, -56.10), 'MS': (-20.44, -54.65), 'DF': (-15.78, -47.93),
    'SE': (-10.91, -37.07), 'RO': (-8.76,  -63.90), 'TO': (-10.18, -48.33),
    'AC': (-9.97,  -67.81), 'AP': (0.03,   -51.05), 'RR': (2.82,   -60.67),
}

def _infer_state(lat: float, lon: float) -> str:
    best, best_d = 'SP', float('inf')
    for state, (clat, clon) in _STATE_CENTROIDS.items():
        d = (lat - clat) ** 2 + (lon - clon) ** 2
        if d < best_d:
            best_d = d
            best = state
    return best


# ─── Métricas ─────────────────────────────────────────────────────────────────

def compute_temporal_metrics(records: List[Dict]) -> Dict:
    hours = Counter()
    dows  = Counter()
    for r in records:
        ts_raw = r.get('timestamp')
        if not ts_raw:
            continue
        try:
            ts = datetime.fromisoformat(ts_raw)
            hours[ts.hour] += 1
            dows[ts.weekday()] += 1
        except ValueError:
            continue

    # Garantir todos os slots mesmo se zero
    hour_counts = {h: hours.get(h, 0) for h in range(24)}
    dow_counts  = {d: dows.get(d, 0)  for d in range(7)}
    total = sum(hour_counts.values())

    hour_pct = {h: round(v / total * 100, 2) if total else 0 for h, v in hour_counts.items()}
    dow_pct  = {d: round(v / sum(dow_counts.values()) * 100, 2) if total else 0
                for d, v in dow_counts.items()}

    entropy = shannon_entropy(hour_counts)

    # Detectar picos: hora com > 1.5× a média
    mean_per_hour = total / 24 if total else 0
    peaks = [h for h, v in hour_counts.items() if v > 1.5 * mean_per_hour]

    return {
        'temporal_entropy_normalized': round(entropy, 4),
        'temporal_realism_score': round(entropy * 10, 1),  # 0-10
        'hour_distribution_pct': hour_pct,
        'dow_distribution_pct': {dow_labels[k]: v for k, v in dow_pct.items()},
        'peak_hours_detected': sorted(peaks),
        'note': (
            'Entropy ~1.0 = uniforme (atual, ruim para ML). '
            'Target: ~0.85 com picos visíveis em 12h, 18h, 21h.'
        ),
    }

dow_labels = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sab', 6: 'Dom'}


def compute_geo_metrics(records: List[Dict]) -> Dict:
    state_counts: Counter = Counter()
    for r in records:
        lat = r.get('geolocation_lat')
        lon = r.get('geolocation_lon')
        if lat is None or lon is None:
            continue
        state_counts[_infer_state(lat, lon)] += 1

    total = sum(state_counts.values())
    state_pct = {s: round(v / total * 100, 2) for s, v in
                 sorted(state_counts.items(), key=lambda x: -x[1])}
    entropy = shannon_entropy(state_counts)

    return {
        'geo_entropy_normalized': round(entropy, 4),
        'geo_realism_score': round(entropy * 10, 1),  # 0-10
        'state_distribution_pct': state_pct,
        'unique_states': len(state_counts),
        'note': (
            'Geo uniforme por estado é esperado agora (random). '
            'Após T2, transações legítimas devem ser concentradas em 3-5 estados por cliente.'
        ),
    }


def compute_fraud_metrics(records: List[Dict]) -> Dict:
    total = len(records)
    fraud_count = sum(1 for r in records if r.get('is_fraud'))
    fraud_rate = fraud_count / total if total else 0

    type_counts: Counter = Counter()
    for r in records:
        if r.get('is_fraud'):
            ft = r.get('fraud_type') or 'UNKNOWN'
            type_counts[ft] += 1

    type_pct = {t: round(v / fraud_count * 100, 2) for t, v in
                sorted(type_counts.items(), key=lambda x: -x[1])} if fraud_count else {}

    return {
        'total_records': total,
        'fraud_count': fraud_count,
        'fraud_rate_pct': round(fraud_rate * 100, 3),
        'fraud_type_distribution_pct': type_pct,
    }


def compute_amount_stats(records: List[Dict]) -> Dict:
    def _stats(values: List[float]) -> Dict:
        if not values:
            return {}
        s = sorted(values)
        n = len(s)
        return {
            'count': n,
            'mean':   round(sum(s) / n, 2),
            'median': round(s[n // 2], 2),
            'p95':    round(s[int(n * 0.95)], 2),
            'p99':    round(s[int(n * 0.99)], 2),
            'max':    round(s[-1], 2),
        }

    legit  = [r['amount'] for r in records if not r.get('is_fraud') and r.get('amount')]
    frauds = [r['amount'] for r in records if r.get('is_fraud') and r.get('amount')]

    return {
        'legitimate_transactions': _stats(legit),
        'fraudulent_transactions': _stats(frauds),
    }


def compute_auc(records: List[Dict]) -> Optional[Dict]:
    """AUC de modelo simples (requer scikit-learn). Retorna None se não disponível."""
    try:
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import train_test_split
        import numpy as np
    except ImportError:
        return None

    features = []
    labels = []
    for r in records:
        try:
            ts = datetime.fromisoformat(r['timestamp'])
            features.append([
                r.get('amount', 0),
                ts.hour,
                ts.weekday(),
                r.get('transactions_last_24h', 0) or 0,
                r.get('accumulated_amount_24h', 0) or 0,
                1 if r.get('unusual_time') else 0,
                1 if r.get('new_beneficiary') else 0,
                r.get('fraud_score', 0) or 0,
            ])
            labels.append(1 if r.get('is_fraud') else 0)
        except Exception:
            continue

    if len(labels) < 100 or sum(labels) < 10:
        return {'error': 'Dados insuficientes para calcular AUC'}

    X = np.array(features)
    y = np.array(labels)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    clf = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
    clf.fit(X_train, y_train)
    y_prob = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)

    return {
        'auc': round(float(auc), 4),
        'model': 'GradientBoostingClassifier(n_estimators=50)',
        'features': ['amount', 'hour', 'dow', 'tx_last_24h', 'amount_24h',
                     'unusual_time', 'new_beneficiary', 'fraud_score'],
        'note': (
            'AUC > 0.90 com só essas features indica que o dataset atual é "fácil demais" '
            '(modelos ficam overconfident). Target após melhorias: 0.82-0.88.'
        ),
    }


def compute_score(temporal: Dict, geo: Dict, fraud: Dict) -> Dict:
    """
    Score composto 0-10 por dimensão.

    Temporal: recompensa distribui\u00e7\u00f5es peakedas nos hor\u00e1rios corretos, n\u00e3o uniformidade.
      - Distribui\u00e7\u00e3o uniforme (entropia \u2248 1.0) = ruim      → score baixo
      - Picos em 12h, 18h, 21h com valleys em 0h-5h = bom → score alto
    Geo: quanto mais concentrado em SP/RJ/MG (realidade BR), melhor.
    Fraud rate: target 1.5–5%.
    """
    peaks = temporal.get('peak_hours_detected', [])
    hour_pct = temporal.get('hour_distribution_pct', {})
    entropy = temporal.get('temporal_entropy_normalized', 1.0)

    # Recompensa picos nas janelas certas
    lunch_hits  = sum(1 for h in peaks if 11 <= h <= 13)   # pico almoço
    evening_hits = sum(1 for h in peaks if 17 <= h <= 20)  # pico saída
    night_hits  = sum(1 for h in peaks if 20 <= h <= 22)   # pico noturno

    # Valley noturno: horas 1-5 devem ter < 3% cada
    night_valley = sum(
        1 for h in range(1, 6)
        if float(hour_pct.get(h, 100)) < 3.0
    )

    # Penalidade por distribuição uniforme (entropia muito alta)
    uniformity_penalty = max(0.0, (entropy - 0.90) * 20)  # > 0.90 começa a penalizar

    t_score = (
        min(3.0, lunch_hits * 1.5) +
        min(3.0, evening_hits * 1.0) +
        min(2.0, night_hits * 1.0) +
        min(2.0, night_valley * 0.4) -
        uniformity_penalty
    )
    t_adjusted = round(max(0.0, min(10.0, t_score)), 1)

    # Geo score: SP+RJ+MG esperados ~40% do volume Brasil
    sp_rj_mg = sum(geo.get('state_distribution_pct', {}).get(s, 0) for s in ['SP', 'RJ', 'MG'])
    geo_concentration = min(10.0, sp_rj_mg / 4.0)  # 40% → score 10
    g_entropy = geo.get('geo_entropy_normalized', 0)
    g_adjusted = round(min(10.0, geo_concentration * 0.7 + (1.0 - g_entropy) * 30), 1)

    # Fraud rate
    fraud_rate = fraud.get('fraud_rate_pct', 0)
    fraud_score = 10.0 if 1.5 <= fraud_rate <= 5.0 else max(0.0, 10.0 - abs(fraud_rate - 2.5) * 2)

    overall = round((t_adjusted + g_adjusted + float(fraud_score)) / 3, 1)

    return {
        'temporal_score':    t_adjusted,
        'geo_score':         g_adjusted,
        'fraud_rate_score':  round(fraud_score, 1),
        'overall_score':     overall,
        'scale':             '0-10 (10 = perfeito realismo)',
        'targets_after_T1_T2': {
            'temporal_score':    '≥ 7.0',
            'geo_score':         '≥ 8.0',
            'fraud_rate_score':  '≥ 8.0',
            'overall_score':     '≥ 7.5',
        },
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Valida realismo de dataset de fraudes')
    parser.add_argument('--input',  required=True, nargs='+',
                        help='Arquivo(s) JSONL de transações (glob suportado)')
    parser.add_argument('--save',   default=None,
                        help='Salvar resultado em JSON (ex: baseline_before/REALISM_METRICS.json)')
    parser.add_argument('--auc',    action='store_true',
                        help='Calcular AUC (requer scikit-learn)')
    parser.add_argument('--max-records', type=int, default=100_000,
                        help='Máximo de registros a processar (default: 100000)')
    args = parser.parse_args()

    # Expandir globs
    paths = []
    for pattern in args.input:
        expanded = glob.glob(pattern)
        paths.extend(expanded if expanded else [pattern])

    if not paths:
        print(f'❌ Nenhum arquivo encontrado: {args.input}', file=sys.stderr)
        sys.exit(1)

    print(f'📂 Carregando {len(paths)} arquivo(s)...')
    records = load_jsonl(paths, max_records=args.max_records)
    print(f'✅ {len(records):,} registros carregados\n')

    print('⏱  Calculando métricas temporais...')
    temporal = compute_temporal_metrics(records)

    print('🗺  Calculando métricas geográficas...')
    geo = compute_geo_metrics(records)

    print('🎭 Calculando métricas de fraude...')
    fraud = compute_fraud_metrics(records)

    print('💰 Calculando estatísticas de valores...')
    amounts = compute_amount_stats(records)

    auc_result = None
    if args.auc:
        print('🤖 Calculando AUC (GradientBoosting)...')
        auc_result = compute_auc(records)
        if auc_result is None:
            print('   ⚠️  scikit-learn não disponível, AUC pulado')

    print('📊 Calculando score de realismo...')
    score = compute_score(temporal, geo, fraud)

    result = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'source_files': [os.path.basename(p) for p in paths],
        'records_analyzed': len(records),
        'score_realism': score,
        'temporal': temporal,
        'geo': geo,
        'fraud': fraud,
        'amounts': amounts,
    }
    if auc_result:
        result['auc_simple_model'] = auc_result

    # ── Imprimir resumo ────────────────────────────────────────────────────────
    print('\n' + '═' * 60)
    print('  REALISM SCORE REPORT')
    print('═' * 60)
    print(f"  Records analisados : {len(records):>10,}")
    print(f"  Fraud rate         : {fraud['fraud_rate_pct']:>9.2f}%")
    print(f"  Unique fraud types : {len(fraud['fraud_type_distribution_pct']):>10}")
    print()
    print(f"  Score Temporal     : {score['temporal_score']:>6.1f} / 10  (target T1: ≥ 7.0)")
    print(f"  Score Geo          : {score['geo_score']:>6.1f} / 10  (target T2: ≥ 8.0)")
    print(f"  Score Fraud Rate   : {score['fraud_rate_score']:>6.1f} / 10")
    print(f"  Score GERAL        : {score['overall_score']:>6.1f} / 10  (target: ≥ 7.5)")
    print()
    print(f"  Picos detectados   : {temporal['peak_hours_detected']}")
    print(f"  Entrop. temporal   : {temporal['temporal_entropy_normalized']:.4f}")
    print(f"  Entrop. geo        : {geo['geo_entropy_normalized']:.4f}")
    if auc_result and 'auc' in auc_result:
        print(f"  AUC (simples)      : {auc_result['auc']:.4f}  (target após melhorias: 0.82-0.88)")
    print()

    # Top 5 fraud types
    ftype_items = list(fraud['fraud_type_distribution_pct'].items())[:5]
    if ftype_items:
        print('  Top fraud types:')
        for ft, pct in ftype_items:
            print(f'    {ft:<30s} {pct:>6.2f}%')
    print('═' * 60)

    # ── Salvar ─────────────────────────────────────────────────────────────────
    save_path = args.save
    if save_path is None:
        # auto-detectar pasta
        if paths and 'baseline_before' in paths[0]:
            save_path = 'baseline_before/REALISM_METRICS.json'
        elif paths and 'baseline_after' in paths[0]:
            save_path = 'baseline_after/REALISM_METRICS.json'
        else:
            save_path = 'REALISM_METRICS.json'

    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
    with open(save_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f'\n  💾 Métricas salvas em: {save_path}')


if __name__ == '__main__':
    main()
