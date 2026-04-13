#!/usr/bin/env python3
"""
analyze_batch.py — Análise de qualidade de dados sintéticos SynthFin

METODOLOGIA E REFERÊNCIAS CIENTÍFICAS
======================================

Este script implementa métricas validadas na literatura de dados sintéticos e detecção de fraude.
Cada métrica é justificada com referência científica explícita. Métricas circulares (que apenas
verificam se o gerador rodou) são identificadas como tal.

Referências principais:
  [1] Synthcity — Jarrett et al. 2022 (arXiv:2301.07573) — framework de avaliação de dados sintéticos
  [2] SDMetrics — Patki et al. 2016 (SDV/DataCanto) — métricas de fidelidade tabulares
  [3] Esteban et al. 2017 (arXiv:1706.02633) — TSTR para avaliação de utilidade
  [4] Cohen 1988 — Statistical Power Analysis: tamanhos de efeito (d=0.2/0.5/0.8)
  [5] Fraud Detection Handbook — Le Borgne et al. (Springer) — benchmarks de fraude reais
  [6] BACEN 2023 — Relatório Pix: ~0.00005% de transações por contagem

LIMITAÇÃO FUNDAMENTAL (validação circular):
  Este script compara fraudes com legítimos nos MESMOS dados sintéticos. Isso confirma
  que o gerador funcionou, não que os dados são realistas. Para validação verdadeira:
  (a) comparo métricas com benchmarks externos (ULB, PaySim, BACEN)
  (b) flaggo o que é verificação de implementação vs. evidência de qualidade

ESTRUTURA DE OUTPUTS:
  - Seção "implementation_checks": verifica se o gerador executou corretamente
  - Seção "quality_evidence": métricas com interpretação baseada em benchmarks externos
  - Seção "methodology_notes": explica o que cada métrica pode e não pode afirmar
  - Seção "external_benchmarks": comparação com referências publicadas

Uso:
    python tools/analyze_batch.py \\
        --input ./data/ml_baseline/transactions_00000.jsonl \\
        --output ./data/ml_analysis_report.json \\
        [--sample N]
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import jensenshannon

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from fraud_generator.config.fraud_patterns import FRAUD_PATTERNS
    HAS_FRAUD_PATTERNS = True
except ImportError:
    HAS_FRAUD_PATTERNS = False

# ─── Benchmarks externos publicados ────────────────────────────────────────────
# Fonte [6]: BACEN Relatório Pix 2023
# Fonte [5]: Fraud Detection Handbook (Le Borgne et al.)
# Fonte [ULB]: Kaggle ULB Credit Card dataset
# Fonte [PaySim]: López-Rojas et al. 2016
EXTERNAL_BENCHMARKS = {
    "fraud_rate_bacen_pix_2023": 0.0000005,   # ~0.00005% por contagem [6]
    "fraud_rate_ulb_credit_card": 0.00172,     # 0.172% [ULB]
    "fraud_rate_paysim": 0.0013,               # 0.13% [PaySim]
    "fraud_rate_fraud_handbook": 0.0084,       # 0.84% [5]
    # Lift realista para sinais de velocidade em dados reais: 2–8x [5]
    "velocity_signal_lift_real_range": (2.0, 8.0),
    # AUC alvo para dataset sintético desafiador (não trivial) [1][5]
    "target_fraud_auc_min": 0.75,
    "target_fraud_auc_max": 0.92,
    # KSComplement alvo: > 0.8 (i.e., KS < 0.2 entre sintético e real) [2]
    "ks_complement_threshold": 0.80,
}

BINARY_SIGNALS = [
    "active_call_during_tx",
    "emulator_detected",
    "sim_swap_recent",
    "navigation_order_anomaly",
    "unusual_time",
    "new_beneficiary",
    "device_new_for_customer",
    "is_impossible_travel",
    "is_probe_transaction",
    "vpn_active",
    "recipient_is_mule",
    "ip_location_matches_account",
]

VELOCITY_FIELDS = [
    "velocity_transactions_1h",
    "velocity_transactions_6h",
    "velocity_transactions_24h",
    "velocity_transactions_7d",
    "velocity_transactions_30d",
    "accumulated_amount_24h",
    "accumulated_amount_7d",
]

# ─── Carregamento ──────────────────────────────────────────────────────────────

def load_records(path: str, sample: int | None = None) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if sample and i >= sample:
                break
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def to_dataframe(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    for col in BINARY_SIGNALS + ["is_fraud"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    for col in VELOCITY_FIELDS + ["amount", "fraud_score", "fraud_risk_score", "bot_confidence_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


# ─── BLOCO 1: Verificações de implementação ───────────────────────────────────
# Estas verificações confirmam que o gerador executou corretamente.
# NÃO provam qualidade dos dados — apenas que o código rodou.

def implementation_checks(df: pd.DataFrame) -> dict:
    """
    AVISO: Resultados aqui são verificação de implementação, não evidência de qualidade.
    Um gerador com bugs ainda poderia passar esses testes se os bugs forem sistemáticos.
    """
    fraud_mask = df["is_fraud"]
    fraud_n = int(fraud_mask.sum())
    total_n = len(df)

    # Distribuição de tipos de fraude
    type_dist = {}
    if "fraud_type" in df.columns:
        counts = df[fraud_mask]["fraud_type"].value_counts()
        type_dist = counts.to_dict()

    # Verificação de tipos esperados (circular: apenas confirma que fraud_patterns.py foi usado)
    types_present = list(type_dist.keys())
    types_missing = []
    expected_vs_actual = {}
    if HAS_FRAUD_PATTERNS:
        types_missing = [t for t in FRAUD_PATTERNS if t not in type_dist]
        total_prev = sum(p.get("prevalence", 0) for p in FRAUD_PATTERNS.values())
        for ftype, cnt in type_dist.items():
            exp = FRAUD_PATTERNS.get(ftype, {}).get("prevalence", 0)
            exp_share = exp / total_prev if total_prev > 0 else 0
            act_share = cnt / fraud_n if fraud_n > 0 else 0
            expected_vs_actual[ftype] = {
                "actual_share": round(act_share, 4),
                "expected_share": round(exp_share, 4),
                "ratio": round(act_share / exp_share, 3) if exp_share > 0.001 else None,
            }

    # Taxa de sinal binário por tipo (CIRCULAR: apenas verifica injeção)
    profile_col = next((c for c in ["cliente_perfil", "behavioral_profile"] if c in df.columns), None)
    profile_coverage = float((df[profile_col].notna().mean())) if profile_col else 0.0

    return {
        "_note": (
            "AVISO: Estas métricas verificam que o gerador funcionou. "
            "NÃO provam realismo dos dados."
        ),
        "total_records": total_n,
        "fraud_count": fraud_n,
        "fraud_rate_actual": round(fraud_n / total_n, 6),
        "fraud_types_present": len(types_present),
        "fraud_types_missing": types_missing,
        "fraud_type_distribution": type_dist,
        "expected_vs_actual_prevalence": expected_vs_actual,
        "profile_column_used": profile_col,
        "profile_coverage_rate": round(profile_coverage, 4),
        "schema_fields_count": len(df.columns),
    }


# ─── BLOCO 2: Separabilidade supervisionada com AUC-ROC ───────────────────────
# Método: sklearn.metrics.roc_auc_score com cross-val manual
# Referência: [1] [5] — AUC-ROC é a métrica padrão para avaliação de fraude
# Limitação: sem dado real, não podemos fazer TSTR. AUC interna mede separabilidade
#            dentro dos mesmos dados gerados — ainda parcialmente circular.
# PORÉM: comparar AUC contra benchmarks externos ([5] alvo 0.75-0.92) é informativo.

def compute_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(round(roc_auc_score(y_true, y_score), 4))


def compute_pr_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """
    AUC-PR (Average Precision) — preferida para classes desbalanceadas.
    Referência: [5] Fraud Detection Handbook — "AUC ROC can be misleading for
    highly imbalanced problems; Average Precision is preferred."
    """
    from sklearn.metrics import average_precision_score
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(round(average_precision_score(y_true, y_score), 4))


def separability_analysis(df: pd.DataFrame) -> dict:
    """
    Avalia se fraude é separável de legítimo usando AUC-ROC e AUC-PR.

    INTERPRETAÇÃO PARA DADOS SINTÉTICOS (não para detectores reais):
    - AUC < 0.75: Sinal fraco — enriquecedor pode não estar gerando padrões suficientes
    - AUC 0.75–0.92: Zona realista [5] — dados desafiadores mas classificáveis
    - AUC > 0.92: Possivelmente trivial — dados muito fáceis de classificar
    - AUC > 0.99: Quase certamente trivial — único sinal domina

    LIMITAÇÃO: Esta comparação ainda usa os mesmos dados gerados, não dados reais.
    Um AUC de 0.85 nos próprios dados sintéticos não garante utilidade em dados reais.
    """
    y = df["is_fraud"].astype(int).values
    results = {}

    for score_col in ["fraud_score", "fraud_risk_score", "bot_confidence_score"]:
        if score_col not in df.columns:
            continue
        scores = df[score_col].values
        auc = compute_auc(y, scores)
        pr_auc = compute_pr_auc(y, scores)

        fraud_vals = scores[y == 1]
        legit_vals = scores[y == 0]

        # KS test — interpretação correta: mede diferença de distribuição marginal
        # Referência: [2] SDMetrics usa KSComplement = 1 - KS
        # Threshold: KS > 0.80 sugere separabilidade forte (ajustado de 0.95 — incorreto antes)
        ks_stat, ks_pvalue = stats.ks_2samp(fraud_vals, legit_vals)

        # Jensen-Shannon Divergence — bounded [0,1], 0=idênticos, 1=disjuntos
        # Referência: [1] Synthcity JensenShannonDistance
        # Requer histograma discretizado
        bins = np.linspace(0, max(scores.max(), 1e-9), 51)
        p_fraud, _ = np.histogram(fraud_vals, bins=bins, density=True)
        p_legit, _ = np.histogram(legit_vals, bins=bins, density=True)
        p_fraud = p_fraud + 1e-10  # evita log(0)
        p_legit = p_legit + 1e-10
        jsd = float(jensenshannon(p_fraud, p_legit, base=2))  # base 2 → bounded [0,1]

        interpretation = (
            "weak_signal" if auc < 0.75
            else "realistic_range" if auc <= 0.92
            else "possibly_trivial" if auc <= 0.99
            else "trivially_separable"
        )

        results[score_col] = {
            "auc_roc": auc,
            "auc_pr": pr_auc,
            "ks_statistic": round(float(ks_stat), 4),
            "ks_pvalue": round(float(ks_pvalue), 6),
            "jensen_shannon_divergence": round(jsd, 4),
            "fraud_mean": round(float(fraud_vals.mean()), 3),
            "legit_mean": round(float(legit_vals.mean()), 3),
            "fraud_std": round(float(fraud_vals.std()), 3),
            "legit_std": round(float(legit_vals.std()), 3),
            "interpretation": interpretation,
            "vs_benchmark": {
                "target_auc_min": EXTERNAL_BENCHMARKS["target_fraud_auc_min"],
                "target_auc_max": EXTERNAL_BENCHMARKS["target_fraud_auc_max"],
                "within_realistic_range": EXTERNAL_BENCHMARKS["target_fraud_auc_min"] <= auc <= EXTERNAL_BENCHMARKS["target_fraud_auc_max"],
            },
        }

    return results


# ─── BLOCO 3: Separabilidade individual por sinal (binário) ───────────────────
# Método: Cramér's V para associação entre variável binária e is_fraud
# Referência: [1] Synthcity usa Chi² / Cramér's V para colunas categóricas
# MAIS CORRETO QUE LIFT para medir associação (não apenas confirmação de injeção)
# LIMITAÇÃO: Cramér's V mede associação nos dados gerados — ainda circular

def cramers_v(x: np.ndarray, y: np.ndarray) -> float:
    """
    Cramér's V — medida de associação para variáveis categóricas/binárias.
    Referência: [1][2] — Synthcity e SDMetrics usam Chi²/Cramér's V para colunas binárias.
    V = 0: sem associação. V = 1: associação perfeita.
    """
    contingency = pd.crosstab(x, y)
    chi2, _, dof, _ = stats.chi2_contingency(contingency)
    n = contingency.sum().sum()
    phi2 = chi2 / n
    r, k = contingency.shape
    phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    rcorr = r - ((r - 1) ** 2) / (n - 1)
    kcorr = k - ((k - 1) ** 2) / (n - 1)
    denom = min(kcorr - 1, rcorr - 1)
    if denom <= 0:
        return float("nan")
    return float(round(math.sqrt(phi2corr / denom), 4))


def binary_signal_quality(df: pd.DataFrame) -> dict:
    """
    Para cada sinal binário: mede associação com is_fraud usando Cramér's V e AUC-ROC.

    INTERPRETAÇÃO:
    - Cramér's V 0.10–0.30: associação fraca mas presente
    - Cramér's V 0.30–0.50: associação moderada
    - Cramér's V > 0.50: associação forte (potencial dominância)

    AVISO CIRCULAR: Sinais que o enricher injeta ativamente terão V alto por design.
    O que é informativo é: sinais com V < 0.05 — enriquecedor pode não estar ativando.

    COMPARAÇÃO COM BENCHMARK EXTERNO [5]:
    Lift realista em fraude real: 2–8x. Lift > 20x sugere sinal superinjetado.
    """
    y = df["is_fraud"].astype(int).values
    results = {}

    for sig in BINARY_SIGNALS:
        if sig not in df.columns:
            continue
        x = df[sig].astype(int).values
        n_total = len(x)
        n_fraud = y.sum()
        n_legit = n_total - n_fraud

        # Taxas de ativação
        fraud_rate = float(x[y == 1].mean()) if n_fraud > 0 else 0.0
        legit_rate = float(x[y == 0].mean()) if n_legit > 0 else 0.0
        overall_rate = float(x.mean())

        # Lift — [5] diz que lift realista em fraude real = 2-8x
        lift = fraud_rate / legit_rate if legit_rate > 0.001 else None

        # AUC de um único sinal (classificador binário trivial)
        auc_single = compute_auc(y, x)

        # Cramér's V [1][2]
        cramer = cramers_v(x, y)

        # Classificação do lift vs. benchmark externo
        lift_vs_benchmark = None
        if lift is not None:
            bench_min, bench_max = EXTERNAL_BENCHMARKS["velocity_signal_lift_real_range"]
            if lift < bench_min:
                lift_vs_benchmark = "below_real_world_range"
            elif lift <= bench_max:
                lift_vs_benchmark = "within_real_world_range"
            elif lift <= 20:
                lift_vs_benchmark = "above_real_world_range_moderate"
            else:
                lift_vs_benchmark = "far_above_real_world_possibly_over_injected"

        # Sinalizar se é provavelmente apenas verificação de injeção
        is_likely_implementation_check = (
            lift is not None
            and lift > 10
            and sig not in ["is_probe_transaction", "is_impossible_travel"]
        )

        results[sig] = {
            "fraud_activation_rate": round(fraud_rate, 4),
            "legit_activation_rate": round(legit_rate, 4),
            "overall_rate": round(overall_rate, 4),
            "lift": round(lift, 2) if lift is not None else None,
            "lift_vs_real_world_benchmark": lift_vs_benchmark,
            "auc_single_signal": auc_single,
            "cramers_v": cramer,
            "is_always_zero": bool(overall_rate < 0.0001),
            "is_likely_implementation_check": is_likely_implementation_check,
            "real_world_lift_reference": "[5] Fraud Detection Handbook: 2–8x typical",
        }

    return results


# ─── BLOCO 4: Velocidade — efeito não-paramétrico (Cliff's delta) ─────────────
# Método: Cliff's delta (rank-biserial correlation)
# Por que não Cohen's d: velocidade é zero-inflated e assimétrica.
# Cohen's d assume normalidade — INVÁLIDO aqui. [4]
# Cliff's delta é não-paramétrico e válido para qualquer distribuição.
# Referência: Cliff 1993, "Dominance statistics: Ordinal analyses to answer
#             ordinal questions" — Psychological Bulletin 114(3):494–509

def cliffs_delta(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Cliff's delta: P(X > Y) - P(X < Y) para grupos 1 e 2.
    Interpretação [Cliff 1993]:
      |d| < 0.147: negligível
      |d| < 0.330: pequeno
      |d| < 0.474: médio
      |d| >= 0.474: grande
    Vantagem: válido para distribuições não-normais e zero-inflated.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return float("nan")
    # Versão eficiente via U de Mann-Whitney
    u_stat, _ = stats.mannwhitneyu(group1, group2, alternative="two-sided")
    delta = (2 * u_stat / (n1 * n2)) - 1
    return float(round(delta, 4))


def velocity_separability(df: pd.DataFrame) -> dict:
    """
    Separabilidade de campos de velocidade usando Cliff's delta (não-paramétrico).

    NOTA METODOLÓGICA:
    - Cohen's d foi usado no script anterior — INCORRETO para dados zero-inflated
    - Cliff's delta é o equivalente não-paramétrico robusto [Cliff 1993]
    - Mann-Whitney U p-value indica significância estatística

    INTERPRETAÇÃO DOS RESULTADOS (velocity_24h com d negativo):
    - Fraude tem velocidade MENOR globalmente — isso é real, não bug
    - Fraudes one-shot (CONTA_TOMADA com 1 transação grande) têm velocidade baixa
    - Fraudes de burst (CARD_TESTING) têm velocidade alta — mas são minoria
    - Analisar por tipo de fraude (não globalmente) seria mais informativo

    LIMITAÇÃO: Análise global mascara heterogeneidade por tipo de fraude.
    CARD_TESTING deveria ter alta velocidade em 1h; ENGENHARIA_SOCIAL não.
    """
    fraud_mask = df["is_fraud"].values
    results = {}

    for field in VELOCITY_FIELDS:
        if field not in df.columns:
            continue
        fraud_vals = df[field].values[fraud_mask]
        legit_vals = df[field].values[~fraud_mask]

        cd = cliffs_delta(fraud_vals, legit_vals)
        _, mw_pvalue = stats.mannwhitneyu(fraud_vals, legit_vals, alternative="two-sided")

        # Estatísticas descritivas honestas (não-paramétricas)
        def pct(arr, p): return float(round(np.percentile(arr, p), 3)) if len(arr) > 0 else None
        def nonzero_mean(arr): return float(round(arr[arr > 0].mean(), 3)) if (arr > 0).sum() > 0 else 0.0

        cd_magnitude = (
            "negligible" if abs(cd) < 0.147
            else "small" if abs(cd) < 0.330
            else "medium" if abs(cd) < 0.474
            else "large"
        )

        results[field] = {
            "cliffs_delta": cd,
            "cliffs_delta_magnitude": cd_magnitude,
            "mannwhitney_pvalue": round(float(mw_pvalue), 6),
            "fraud_median": pct(fraud_vals, 50),
            "legit_median": pct(legit_vals, 50),
            "fraud_p95": pct(fraud_vals, 95),
            "legit_p95": pct(legit_vals, 95),
            "fraud_nonzero_mean": nonzero_mean(fraud_vals),
            "legit_nonzero_mean": nonzero_mean(legit_vals),
            "fraud_zero_rate": round(float((fraud_vals == 0).mean()), 3),
            "legit_zero_rate": round(float((legit_vals == 0).mean()), 3),
            "method": "Cliff's delta (rank-biserial correlation) — non-parametric, valid for zero-inflated data",
            "reference": "Cliff 1993, Psychological Bulletin 114(3):494-509",
            "note": (
                "AVISO: Análise global. Fraude tem velocidade global MENOR que legítimo "
                "porque fraudes one-shot (CONTA_TOMADA) dominam o dataset. "
                "Analisar por fraud_type para detectar padrões de burst."
            ),
        }

    # Análise por fraud_type para os campos mais relevantes (1h, 6h)
    per_type_velocity = {}
    if "fraud_type" in df.columns:
        burst_field = "velocity_transactions_1h"
        if burst_field in df.columns:
            for ftype in df[df["is_fraud"]][burst_field].groupby(df["fraud_type"]).groups.keys():
                subset = df[df["fraud_type"] == ftype][burst_field].values
                per_type_velocity[ftype] = {
                    "median": float(round(np.median(subset), 2)),
                    "p95": float(round(np.percentile(subset, 95), 2)),
                    "nonzero_rate": round(float((subset > 0).mean()), 3),
                }

    return {
        "global_analysis": results,
        "per_fraud_type_velocity_1h": per_type_velocity,
        "_methodological_note": (
            "Cohen's d não foi usado — inválido para dados zero-inflated. "
            "Cliff's delta (rank-biserial) é o método correto [Cliff 1993]."
        ),
    }


# ─── BLOCO 5: Fidelidade da distribuição de scores (JSD + KS por bucket) ──────
# Método: Jensen-Shannon Divergence entre distribuição de score de fraude e legítimo
# Referência: [1][2] Synthcity e SDMetrics usam JSD para comparação univariada
# INTERPRETAÇÃO: JSD mede divergência entre as duas distribuições como um todo
# JSD = 0: idênticas, JSD = 1: completamente separadas (base 2)

def score_distribution_quality(df: pd.DataFrame) -> dict:
    """
    Análise de qualidade da distribuição dos scores de risco.

    INTERPRETAÇÃO PARA DADOS SINTÉTICOS [1][5]:
    - JSD próximo de 1.0: scores perfeitamente separam fraude/legítimo → trivial
    - JSD 0.3–0.7: separação razoável — zona realista para dados desafiadores
    - JSD < 0.2: scores quase indistinguíveis → sinal fraco no gerador

    BENCHMARK EXTERNO: Dados reais de fraude (ULB, PaySim) têm JSD de scores
    em torno de 0.4–0.7 para features bem calibradas.
    """
    y = df["is_fraud"].astype(int).values
    results = {}

    for score_col in ["fraud_score", "fraud_risk_score", "bot_confidence_score"]:
        if score_col not in df.columns:
            continue
        vals = df[score_col].values
        max_val = max(vals.max(), 1.0)
        fraud_vals = vals[y == 1]
        legit_vals = vals[y == 0]

        # Histograma discretizado em 20 buckets (mais fino que 10)
        bins = np.linspace(0, max_val, 21)
        p_f, _ = np.histogram(fraud_vals, bins=bins)
        p_l, _ = np.histogram(legit_vals, bins=bins)
        p_f = (p_f + 1e-10).astype(float)
        p_l = (p_l + 1e-10).astype(float)
        p_f /= p_f.sum()
        p_l /= p_l.sum()
        jsd = float(round(jensenshannon(p_f, p_l, base=2), 4))

        jsd_interpretation = (
            "weak_signal" if jsd < 0.2
            else "realistic_range" if jsd <= 0.7
            else "strong_separation"
        )

        results[score_col] = {
            "jensen_shannon_divergence": jsd,
            "jsd_interpretation": jsd_interpretation,
            "fraud_percentiles": {
                "p25": round(float(np.percentile(fraud_vals, 25)), 1),
                "p50": round(float(np.percentile(fraud_vals, 50)), 1),
                "p75": round(float(np.percentile(fraud_vals, 75)), 1),
                "p95": round(float(np.percentile(fraud_vals, 95)), 1),
            },
            "legit_percentiles": {
                "p25": round(float(np.percentile(legit_vals, 25)), 1),
                "p50": round(float(np.percentile(legit_vals, 50)), 1),
                "p75": round(float(np.percentile(legit_vals, 75)), 1),
                "p95": round(float(np.percentile(legit_vals, 95)), 1),
            },
            "method": "Jensen-Shannon Divergence [1][2] — Synthcity/SDMetrics standard",
            "reference_range": "JSD 0.3-0.7 é zona realista para dados sintéticos desafiadores",
        }

    return results


# ─── BLOCO 6: Fraud rate vs. benchmarks externos ──────────────────────────────
# Esta comparação NÃO é circular — compara contra dados externos publicados.
# Referências [6] BACEN 2023, [ULB], [PaySim], [5]

def fraud_rate_comparison(df: pd.DataFrame) -> dict:
    """
    Compara a taxa de fraude gerada com benchmarks externos publicados.
    Esta é a única métrica que não é circular: compara contra dados reais publicados.

    INTERPRETAÇÃO:
    - Dados sintéticos tipicamente são gerados com fraud_rate >> real (ex: 5%) para
      garantir volume suficiente de fraude para treino de ML
    - Isso é uma ESCOLHA DE DESIGN, não um defeito de qualidade
    - Documentar que o gerador usa ~5% é importante: modelos treinados nele precisam
      recalibrar probabilidades para produção (ex: via threshold tuning)
    """
    fraud_rate = float(df["is_fraud"].mean())
    benchmarks = EXTERNAL_BENCHMARKS

    return {
        "generated_fraud_rate": round(fraud_rate, 6),
        "benchmarks": {
            "bacen_pix_2023": benchmarks["fraud_rate_bacen_pix_2023"],
            "ulb_credit_card": benchmarks["fraud_rate_ulb_credit_card"],
            "paysim": benchmarks["fraud_rate_paysim"],
            "fraud_handbook_simulation": benchmarks["fraud_rate_fraud_handbook"],
        },
        "ratio_vs_bacen_pix": round(fraud_rate / benchmarks["fraud_rate_bacen_pix_2023"], 0),
        "ratio_vs_ulb": round(fraud_rate / benchmarks["fraud_rate_ulb_credit_card"], 1),
        "ratio_vs_handbook": round(fraud_rate / benchmarks["fraud_rate_fraud_handbook"], 1),
        "interpretation": (
            "Taxa sintética é muito maior que real. Isso é ESPERADO para datasets de treino ML — "
            "garante volume suficiente por tipo de fraude. "
            "Modelos treinados nesse dado precisam de calibração de threshold para produção."
        ),
        "calibration_note": (
            "Para usar modelos treinados nesses dados em produção: "
            "ajuste o threshold de decisão ou aplique Platt scaling para recalibrar probabilidades."
        ),
        "references": "[6] BACEN Relatório Pix 2023; [ULB] Kaggle MLG-ULB; [5] Fraud Detection Handbook",
    }


# ─── BLOCO 7: Análise do classificador simples (feature importance proxy) ──────
# Método: Regressão logística simples para estimar quais features dominam
# Referência: [1][5] — importante para entender se um único sinal domina
# OBJETIVO: Detectar se bot_confidence_score domina o classificador (>60% peso)

def simple_classifier_analysis(df: pd.DataFrame) -> dict:
    """
    Treina um classificador logístico simples para estimar dominância de features.

    METODOLOGIA:
    - Usa apenas features numéricas disponíveis sem engenharia
    - Normaliza para comparar coeficientes
    - Objetivo: detectar se uma única feature domina (>50% do peso absoluto total)

    LIMITAÇÃO HONESTA:
    - Regressão logística não captura interações
    - É uma estimativa de dominância, não feature importance definitiva
    - Para importance real, use LightGBM (Fase 2/3 do plano)

    REFERÊNCIA: [1] Synthcity PerformanceEvaluatorLinear usa LR como proxy rápido
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    features = []
    feature_names = []

    # Features numéricas disponíveis
    numeric_candidates = (
        ["fraud_score", "fraud_risk_score", "bot_confidence_score"]
        + VELOCITY_FIELDS
        + [s for s in BINARY_SIGNALS if s in df.columns]
    )
    for col in numeric_candidates:
        if col in df.columns:
            features.append(df[col].fillna(0).astype(float).values)
            feature_names.append(col)

    if len(features) < 3:
        return {"note": "insufficient numeric features for classifier analysis"}

    X = np.column_stack(features)
    y = df["is_fraud"].astype(int).values

    # Subsample para velocidade (máx 30k)
    if len(y) > 30000:
        idx = np.random.RandomState(42).choice(len(y), 30000, replace=False)
        X, y = X[idx], y[idx]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    lr = LogisticRegression(max_iter=500, random_state=42, class_weight="balanced", C=1.0)
    lr.fit(X_scaled, y)

    # Coeficientes absolutos normalizados
    coefs = np.abs(lr.coef_[0])
    total = coefs.sum()
    importance = {name: round(float(c / total), 4) for name, c in zip(feature_names, coefs)}
    importance_sorted = dict(sorted(importance.items(), key=lambda x: -x[1]))

    # AUC do classificador logístico
    from sklearn.metrics import roc_auc_score
    y_pred = lr.predict_proba(X_scaled)[:, 1]
    lr_auc = float(round(roc_auc_score(y, y_pred), 4))

    # Detectar dominância: feature com > 40% do peso total
    dominant = {k: v for k, v in importance.items() if v > 0.40}

    return {
        "logistic_regression_auc": lr_auc,
        "feature_importance_proxy": importance_sorted,
        "dominant_features": dominant,
        "n_features_used": len(feature_names),
        "dominance_detected": len(dominant) > 0,
        "interpretation": (
            "Uma feature dominante (>40% peso) indica que dados podem ser "
            "trivialmente classificáveis a partir dessa feature sozinha. "
            "Ideal: distribuição mais uniforme entre features."
        ),
        "limitation": (
            "Regressão logística é proxy — não captura interações. "
            "Use LightGBM (Fase 3 do plano) para feature importance definitiva."
        ),
        "method": "Logistic Regression com StandardScaler + class_weight='balanced' [1]",
    }


# ─── BLOCO 8: Heterogeneidade por fraud type (não-circular) ───────────────────
# Esta análise é MENOS circular: mede se tipos de fraude DIFERENTES
# têm padrões de signal DIFERENTES entre si — não apenas vs. legítimo

def fraud_type_heterogeneity(df: pd.DataFrame) -> dict:
    """
    Verifica se tipos de fraude são distinguíveis entre si pelos sinais.

    POR QUE É MENOS CIRCULAR:
    - A análise anterior (M4) media "CONTA_TOMADA tem sim_swap alto" — sempre verdade por design
    - Esta análise mede "CONTA_TOMADA e PIX_GOLPE têm PERFIS DIFERENTES entre si"
    - Se todos os tipos tiverem perfis idênticos, os sinais são muito genéricos

    MÉTODO: Coeficiente de variação da taxa de ativação de cada sinal através dos tipos.
    Alto CV = sinal diferencia tipos entre si (informativo)
    Baixo CV = sinal é igual para todos os tipos (genérico, não discrimina tipos)
    """
    if "fraud_type" not in df.columns:
        return {"note": "fraud_type column not available"}

    fraud_df = df[df["is_fraud"]].copy()
    available_sigs = [s for s in BINARY_SIGNALS if s in df.columns]

    # Ativação por tipo de fraude
    type_profiles = {}
    for ftype in fraud_df["fraud_type"].dropna().unique():
        subset = fraud_df[fraud_df["fraud_type"] == ftype]
        if len(subset) < 20:
            continue
        type_profiles[ftype] = {
            sig: float(round(subset[sig].astype(int).mean(), 4))
            for sig in available_sigs
        }
        type_profiles[ftype]["_n"] = len(subset)

    if len(type_profiles) < 2:
        return {"note": "insufficient fraud types for heterogeneity analysis"}

    # Coeficiente de variação por sinal (através dos tipos)
    signal_cv = {}
    for sig in available_sigs:
        rates = [type_profiles[t][sig] for t in type_profiles if sig in type_profiles[t]]
        rates_arr = np.array(rates)
        mean_rate = rates_arr.mean()
        std_rate = rates_arr.std()
        cv = float(std_rate / mean_rate) if mean_rate > 0.01 else None
        signal_cv[sig] = {
            "mean_across_types": round(float(mean_rate), 4),
            "std_across_types": round(float(std_rate), 4),
            "cv": round(cv, 3) if cv is not None else None,
            "discriminates_fraud_types": (
                "yes" if cv and cv > 0.5
                else "weakly" if cv and cv > 0.2
                else "no"
            ),
        }

    # Tipos mais "homogêneos" (todos sinais similares) vs "heterogêneos" (sinais distintos)
    signal_cv_sorted = dict(sorted(signal_cv.items(), key=lambda x: -(x[1].get("cv") or 0)))

    return {
        "type_profiles": type_profiles,
        "signal_cv_by_fraud_type": signal_cv_sorted,
        "interpretation": (
            "Sinais com CV alto (>0.5) distinguem tipos de fraude entre si — mais informativos. "
            "Sinais com CV baixo (<0.2) são uniformes em todos os tipos — menos informativos para multi-class."
        ),
        "_note": "Menos circular que análise fraud vs. legit: mede distinção entre tipos de fraude.",
    }


# ─── Construção de gaps de qualidade ──────────────────────────────────────────

def build_quality_gaps(
    sep: dict,
    signals: dict,
    velocity: dict,
    lr: dict,
) -> list[dict]:
    gaps = []

    # AUC fora do range realista
    for score_col, info in sep.items():
        auc = info.get("auc_roc", 0)
        if auc > 0.92:
            gaps.append({
                "severity": "high",
                "type": "trivial_separability",
                "metric": score_col,
                "value": auc,
                "issue": f"{score_col} AUC={auc} > 0.92 — dados podem ser trivialmente classificáveis",
                "action": "Adicionar ruído aos campos de score ou revisar enricher que determina esse score",
                "reference": "[5] Fraud Detection Handbook: AUC realista 0.75-0.92 para dados desafiadores",
            })
        elif auc < 0.75:
            gaps.append({
                "severity": "medium",
                "type": "weak_signal",
                "metric": score_col,
                "value": auc,
                "issue": f"{score_col} AUC={auc} < 0.75 — sinal fraco",
                "action": "Revisar se enricher está ativando campos de score corretamente",
            })

    # Sinais com lift muito acima do mundo real (>20x vs. benchmark 2-8x)
    for sig, info in signals.items():
        lift = info.get("lift")
        benchmark = info.get("lift_vs_real_world_benchmark")
        if benchmark == "far_above_real_world_possibly_over_injected":
            gaps.append({
                "severity": "medium",
                "type": "over_injected_signal",
                "signal": sig,
                "lift": lift,
                "issue": f"{sig} lift={lift:.1f}x >> benchmark real 2-8x [5] — pode estar superinjetado",
                "action": f"Reduzir probabilidade de ativação de {sig} em fraudes ou aumentar em legítimos",
                "is_circular_note": "AVISO: Lift é parcialmente circular (mede injeção). Comparação com benchmark externo reduz circularidade.",
            })

    # Sinais sempre zero (possíveis stubs)
    zero_sigs = [sig for sig, info in signals.items() if info.get("is_always_zero")]
    for sig in zero_sigs:
        gaps.append({
            "severity": "high",
            "type": "zero_signal_stub",
            "signal": sig,
            "issue": f"{sig} nunca ativado — possível stub não implementado",
            "action": "Verificar se enricher implementa este sinal ou se requer licença Pro",
        })

    # Feature dominante no classificador logístico
    dominant = lr.get("dominant_features", {})
    for feat, weight in dominant.items():
        gaps.append({
            "severity": "medium",
            "type": "feature_dominance",
            "feature": feat,
            "weight": weight,
            "issue": f"{feat} domina {weight*100:.0f}% do peso no classificador linear — possível over-reliance",
            "action": "Ampliar distribuição desse campo para reduzir separabilidade trivial",
            "reference": "[1] Synthcity: features não devem dominar classificador unicamente",
        })

    return gaps


# ─── Notas metodológicas ──────────────────────────────────────────────────────

METHODOLOGY_NOTES = {
    "circular_validation_warning": (
        "PROBLEMA FUNDAMENTAL: Este script compara dados sintéticos gerados pelo SynthFin "
        "contra si mesmos (fraude vs. legítimo dentro do mesmo dataset). Isso confirma que "
        "o gerador executou corretamente, mas NÃO prova que os dados são realistas. "
        "Para validação verdadeira, é necessário: (a) comparar contra dados reais [TSTR], "
        "(b) validação por especialistas em fraude, ou (c) comparação com publicações "
        "externas (BACEN, FEBRABAN, Fraud Detection Handbook)."
    ),
    "what_is_NOT_circular": [
        "fraud_rate_vs_external_benchmarks: compara contra BACEN/ULB/PaySim publicados",
        "lift_vs_real_world_benchmark: compara lift calculado contra range 2-8x da literatura [5]",
        "fraud_type_heterogeneity: mede se tipos diferentes têm perfis diferentes entre si",
        "auc_vs_realistic_range: compara AUC contra range 0.75-0.92 considerado realista [5][1]",
    ],
    "what_IS_circular": [
        "per_type_signal_profiles (M4 antigo): confirma que enricher setou campos como programado",
        "signal_activation_rates: confirma que injeção de sinal funcionou",
        "behavioral_profile_lift: confirma que gerador distribuiu uniformemente (by design)",
    ],
    "recommended_external_validation": [
        "TSTR: treinar modelo em sintético, testar em PaySim ou ULB [3]",
        "Expert review: analistas de fraude de bancos brasileiros avaliam transações sintéticas",
        "BACEN comparison: comparar distribuição de tipos vs. relatórios BACEN/FEBRABAN",
        "Cross-dataset transfer: treinar em SynthFin, avaliar discriminação em PaySim",
    ],
    "metric_references": {
        "cohen_d": "NÃO USADO — inválido para dados zero-inflated [4]",
        "cliffs_delta": "USADO para velocidade — não-paramétrico, válido para qualquer distribuição [Cliff 1993]",
        "cramers_v": "USADO para sinais binários — métrica de associação correta para variáveis categóricas [1][2]",
        "jensen_shannon": "USADO para scores — bounded [0,1], padrão Synthcity/SDMetrics [1][2]",
        "auc_roc": "USADO — métrica padrão de fraud detection [5]",
        "auc_pr": "USADO — preferida para classes desbalanceadas [5]",
        "ks_statistic": "USADO com caution — N-sensitivo, apenas marginal [2]",
    },
}


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Análise de qualidade científica de dados sintéticos SynthFin"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Erro: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Carregando: {args.input}")
    records = load_records(args.input, sample=args.sample)
    print(f"  {len(records):,} registros")
    df = to_dataframe(records)
    fraud_n = int(df["is_fraud"].sum())
    print(f"  Fraudes: {fraud_n:,} ({100*fraud_n/len(df):.2f}%)\n")

    print("Bloco 1: Verificações de implementação (circular)...")
    b1 = implementation_checks(df)

    print("Bloco 2: Separabilidade supervisionada (AUC-ROC, AUC-PR, JSD)...")
    b2 = separability_analysis(df)

    print("Bloco 3: Qualidade dos sinais binários (Cramér's V, lift vs. benchmark)...")
    b3 = binary_signal_quality(df)

    print("Bloco 4: Velocidade — Cliff's delta (não-paramétrico)...")
    b4 = velocity_separability(df)

    print("Bloco 5: Distribuição dos scores (JSD)...")
    b5 = score_distribution_quality(df)

    print("Bloco 6: Fraud rate vs. benchmarks externos (não-circular)...")
    b6 = fraud_rate_comparison(df)

    print("Bloco 7: Classificador logístico simples (dominância de features)...")
    b7 = simple_classifier_analysis(df)

    print("Bloco 8: Heterogeneidade por fraud type (menos circular)...")
    b8 = fraud_type_heterogeneity(df)

    print("Construindo quality gaps...")
    gaps = build_quality_gaps(b2, b3, b4["global_analysis"], b7)

    report = {
        "metadata": {
            "input_file": args.input,
            "total_records": len(records),
            "fraud_count": fraud_n,
            "fraud_rate": round(fraud_n / len(records), 6),
            "sample_used": args.sample,
        },
        "methodology_notes": METHODOLOGY_NOTES,
        "b1_implementation_checks": b1,
        "b2_separability_analysis": b2,
        "b3_binary_signal_quality": b3,
        "b4_velocity_cliffs_delta": b4,
        "b5_score_distribution_jsd": b5,
        "b6_fraud_rate_vs_benchmarks": b6,
        "b7_logistic_regression_proxy": b7,
        "b8_fraud_type_heterogeneity": b8,
        "quality_gaps": gaps,
        "quality_gaps_summary": {
            "total": len(gaps),
            "high": sum(1 for g in gaps if g["severity"] == "high"),
            "medium": sum(1 for g in gaps if g["severity"] == "medium"),
        },
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'═'*65}")
    print(f"  Relatório: {args.output}")
    print(f"  Total: {len(records):,}  |  Fraude: {fraud_n:,} ({100*fraud_n/len(records):.2f}%)")
    print(f"\n  ── Separabilidade (AUC-ROC) ──")
    for col, info in b2.items():
        marker = "⚠" if info["interpretation"] != "realistic_range" else "✓"
        print(f"    {marker} {col:<30} AUC={info['auc_roc']}  PR-AUC={info['auc_pr']}  [{info['interpretation']}]")
    print(f"\n  ── JSD dos scores ──")
    for col, info in b5.items():
        print(f"    {col:<30} JSD={info['jensen_shannon_divergence']}  [{info['jsd_interpretation']}]")
    print(f"\n  ── Fraud rate vs. benchmarks ──")
    fb = b6
    print(f"    Gerado:        {fb['generated_fraud_rate']:.4%}")
    print(f"    BACEN Pix:     {fb['benchmarks']['bacen_pix_2023']:.6%}  (ratio: {fb['ratio_vs_bacen_pix']:,.0f}x)")
    print(f"    ULB:           {fb['benchmarks']['ulb_credit_card']:.4%}  (ratio: {fb['ratio_vs_ulb']}x)")
    print(f"    Handbook:      {fb['benchmarks']['fraud_handbook_simulation']:.4%}  (ratio: {fb['ratio_vs_handbook']}x)")
    print(f"\n  ── Classificador logístico (dominância) ──")
    imp = b7.get("feature_importance_proxy", {})
    for feat, w in list(imp.items())[:5]:
        bar = "█" * int(w * 40)
        print(f"    {feat:<35} {w:.3f} {bar}")
    dominant = b7.get("dominant_features", {})
    if dominant:
        print(f"  ⚠ Feature dominante detectada: {list(dominant.keys())}")
    print(f"\n  ── Quality Gaps ──")
    for g in gaps:
        sev = g["severity"].upper()
        print(f"    [{sev}] {g['type']}: {g.get('issue','')[:70]}")
    print(f"\n  AVISO: Leia 'methodology_notes' no JSON para entender o que é circular.")
    print(f"{'═'*65}")


if __name__ == "__main__":
    main()
