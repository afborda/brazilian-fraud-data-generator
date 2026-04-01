"""
FraudGen Data Validation Dashboard
====================================
Dashboard interativo para validar que os dados gerados são realistas
e que os campos estão correlacionados corretamente.

Uso:
    pip install streamlit pandas plotly scipy
    streamlit run validate/dashboard.py

    # com arquivo específico:
    streamlit run validate/dashboard.py -- --file output/transactions_00000.jsonl
"""

import sys
import os
import json
import math
import argparse
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="FraudGen — Data Validator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Benchmarks reais (FEBRABAN / BACEN 2023-2024) ───────────────────────────

FEBRABAN_FRAUD_TYPES = {
    "PIX_GOLPE":           0.28,
    "ENGENHARIA_SOCIAL":   0.18,
    "CONTA_TOMADA":        0.13,
    "CARTAO_CLONADO":      0.12,
    "FRAUDE_APLICATIVO":   0.10,
    "COMPRA_TESTE":        0.07,
    "BOLETO_FALSO":        0.07,
    "MULA_FINANCEIRA":     0.05,
}

EXPECTED_FRAUD_NIGHT_RATE = 0.35   # fraudes noturnas (22h-6h): ~35% do total
EXPECTED_FRAUD_RATE_RANGE = (0.01, 0.15)
EXPECTED_AVG_FRAUD_SCORE  = 65     # fraudes devem ter score médio > 65
EXPECTED_AVG_LEGIT_SCORE  = 12     # legítimas devem ter score médio < 20

# ─── Loaders ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Carregando dados...")
def load_file(path: str, max_records: int = 300_000) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jsonl", ".ndjson"):
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
                    if len(records) >= max_records:
                        break
        return pd.DataFrame(records)
    elif ext == ".csv":
        return pd.read_csv(path, nrows=max_records)
    elif ext in (".parquet", ".pq"):
        return pd.read_parquet(path)
    else:
        st.error(f"Formato não suportado: {ext}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Carregando dados enviados...")
def load_uploaded(file_bytes: bytes, ext: str, max_records: int = 300_000) -> pd.DataFrame:
    import io
    if ext in (".jsonl", ".ndjson"):
        text = file_bytes.decode("utf-8")
        records = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
                if len(records) >= max_records:
                    break
        return pd.DataFrame(records)
    elif ext == ".csv":
        return pd.read_csv(io.BytesIO(file_bytes), nrows=max_records)
    elif ext in (".parquet", ".pq"):
        return pd.read_parquet(io.BytesIO(file_bytes))
    return pd.DataFrame()

# ─── Helpers ─────────────────────────────────────────────────────────────────

_STATE_CENTROIDS = {
    "SP": (-23.55, -46.64), "RJ": (-22.91, -43.17), "MG": (-19.92, -43.94),
    "BA": (-12.97, -38.51), "RS": (-30.03, -51.23), "PR": (-25.43, -49.27),
    "PE": (-8.05,  -34.88), "CE": (-3.72,  -38.54), "SC": (-27.60, -48.55),
    "GO": (-16.68, -49.25), "PA": (-1.46,  -48.50), "AM": (-3.10,  -60.02),
    "DF": (-15.78, -47.93), "ES": (-20.32, -40.34), "MT": (-15.60, -56.10),
    "MS": (-20.44, -54.65), "RN": (-5.79,  -35.21), "MA": (-2.53,  -44.27),
}

def infer_state(lat: float, lon: float) -> str:
    best, best_d = "SP", float("inf")
    for state, (clat, clon) in _STATE_CENTROIDS.items():
        d = (lat - clat) ** 2 + (lon - clon) ** 2
        if d < best_d:
            best_d = d
            best = state
    return best

def pct(n: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{n/total*100:.1f}%"

def null_rate(series: pd.Series) -> float:
    return series.isna().mean() * 100

def metric_card(label: str, value: str, delta: Optional[str] = None, ok: bool = True):
    color = "#22c55e" if ok else "#ef4444"
    st.markdown(
        f"""
        <div style="background:#1e293b;border-radius:8px;padding:12px 16px;border-left:4px solid {color}">
            <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px">{label}</div>
            <div style="font-size:22px;font-weight:700;color:#f1f5f9;margin-top:4px">{value}</div>
            {f'<div style="font-size:12px;color:{color};margin-top:2px">{delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://img.shields.io/badge/FraudGen-Data%20Validator-blue?style=for-the-badge",
        use_container_width=True,
    )
    st.markdown("### Carregar dados")

    uploaded = st.file_uploader(
        "Arraste um arquivo (.jsonl, .csv, .parquet)",
        type=["jsonl", "ndjson", "csv", "parquet", "pq"],
    )

    manual_path = st.text_input(
        "Ou insira um caminho local:",
        placeholder="/caminho/para/transactions_00000.jsonl",
    )

    max_rows = st.slider("Máximo de linhas", 10_000, 300_000, 100_000, step=10_000)

    st.markdown("---")
    st.markdown("### Filtros")
    filter_fraud_only = st.checkbox("Mostrar apenas transações fraudulentas")

    st.markdown("---")
    st.markdown(
        "**FraudGen** · [GitHub](https://github.com/afborda/synthfin-core) · "
        "[Docs](https://synthfin.com.br/docs)",
        unsafe_allow_html=True,
    )

# ─── Load data ────────────────────────────────────────────────────────────────

df = pd.DataFrame()

if uploaded is not None:
    ext = os.path.splitext(uploaded.name)[1].lower()
    df = load_uploaded(uploaded.read(), ext, max_rows)
elif manual_path and os.path.exists(manual_path):
    df = load_file(manual_path, max_rows)
else:
    # Try auto-detect common paths
    candidates = [
        "baseline_seed42/transactions_00000.jsonl",
        "output_test/transactions_00000.jsonl",
        "output/transactions_00000.jsonl",
    ]
    for c in candidates:
        full = os.path.join(os.path.dirname(os.path.dirname(__file__)), c)
        if os.path.exists(full):
            df = load_file(full, max_rows)
            st.sidebar.success(f"Auto-carregado: {c}")
            break

if df.empty:
    st.title("🔍 FraudGen — Validador de Dados")
    st.info(
        "Carregue um arquivo de transações gerado pelo FraudGen para ver o dashboard completo.\n\n"
        "**Formatos suportados:** `.jsonl`, `.csv`, `.parquet`\n\n"
        "**Gerar dados de exemplo:**\n"
        "```bash\n"
        "python generate.py --count 50000 --fraud-rate 0.05 --output output/\n"
        "```"
    )
    st.stop()

# ─── Pre-process ──────────────────────────────────────────────────────────────

if filter_fraud_only:
    df = df[df.get("is_fraud", df.get("fraud", False)) == True]

# Normalize is_fraud column
if "is_fraud" in df.columns:
    df["is_fraud"] = df["is_fraud"].astype(bool)
else:
    df["is_fraud"] = False

# Parse timestamp
if "timestamp" in df.columns:
    df["_ts"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["_hour"] = df["_ts"].dt.hour
    df["_dow"]  = df["_ts"].dt.dayofweek
    df["_date"] = df["_ts"].dt.date

total = len(df)
n_fraud = df["is_fraud"].sum()
n_legit = total - n_fraud
fraud_rate = n_fraud / total if total > 0 else 0

# ─── Header ───────────────────────────────────────────────────────────────────

st.title("🔍 FraudGen — Validador de Dados")
st.markdown(f"**{total:,} transações carregadas** · {n_fraud:,} fraudulentas ({fraud_rate*100:.2f}%) · {n_legit:,} legítimas")

tabs = st.tabs([
    "📊 Visão Geral",
    "🦹 Padrões de Fraude",
    "⚡ Sinais de Risco",
    "🕐 Padrões Temporais",
    "📍 Geografia",
    "🤖 Bot & Automação",
    "🔬 Qualidade dos Dados",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════

with tabs[0]:
    st.subheader("Métricas Principais")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        ok = EXPECTED_FRAUD_RATE_RANGE[0] <= fraud_rate <= EXPECTED_FRAUD_RATE_RANGE[1]
        metric_card(
            "Taxa de Fraude",
            f"{fraud_rate*100:.2f}%",
            f"Esperado: {EXPECTED_FRAUD_RATE_RANGE[0]*100:.0f}–{EXPECTED_FRAUD_RATE_RANGE[1]*100:.0f}%",
            ok=ok,
        )
    with c2:
        n_customers = df["customer_id"].nunique() if "customer_id" in df.columns else 0
        metric_card("Clientes únicos", f"{n_customers:,}")
    with c3:
        n_devices = df["device_id"].nunique() if "device_id" in df.columns else 0
        metric_card("Devices únicos", f"{n_devices:,}")
    with c4:
        if "amount" in df.columns:
            avg_fraud = df[df["is_fraud"]]["amount"].mean() if n_fraud > 0 else 0
            avg_legit = df[~df["is_fraud"]]["amount"].mean() if n_legit > 0 else 0
            ratio = avg_fraud / avg_legit if avg_legit > 0 else 0
            ok = ratio >= 3.0
            metric_card(
                "Valor fraude / legítimo",
                f"{ratio:.1f}×",
                f"Fraude: R${avg_fraud:,.0f} · Legítimo: R${avg_legit:,.0f}",
                ok=ok,
            )
        else:
            metric_card("Valor fraude / legítimo", "N/A")
    with c5:
        if "fraud_risk_score" in df.columns:
            avg_score_fraud = df[df["is_fraud"]]["fraud_risk_score"].mean() if n_fraud > 0 else 0
            avg_score_legit = df[~df["is_fraud"]]["fraud_risk_score"].mean() if n_legit > 0 else 0
            ok = avg_score_fraud >= EXPECTED_AVG_FRAUD_SCORE and avg_score_legit <= EXPECTED_AVG_LEGIT_SCORE
            metric_card(
                "Risk Score médio",
                f"Fraude: {avg_score_fraud:.0f} · Legít: {avg_score_legit:.0f}",
                f"Esperado: >{EXPECTED_AVG_FRAUD_SCORE} / <{EXPECTED_AVG_LEGIT_SCORE}",
                ok=ok,
            )

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribuição de Valores (log scale)")
        if "amount" in df.columns:
            fig = px.histogram(
                df[df["amount"] > 0].assign(label=df["is_fraud"].map({True: "Fraude", False: "Legítimo"})),
                x="amount",
                color="label",
                nbins=80,
                log_x=True,
                barmode="overlay",
                opacity=0.7,
                color_discrete_map={"Fraude": "#ef4444", "Legítimo": "#22c55e"},
                labels={"amount": "Valor (R$, log)", "label": "Tipo"},
            )
            fig.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("fraud_risk_score por classe")
        if "fraud_risk_score" in df.columns:
            fig = px.box(
                df.assign(label=df["is_fraud"].map({True: "Fraude", False: "Legítimo"})),
                x="label",
                y="fraud_risk_score",
                color="label",
                color_discrete_map={"Fraude": "#ef4444", "Legítimo": "#22c55e"},
                labels={"label": "", "fraud_risk_score": "Risk Score (0-100)"},
            )
            fig.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Campo `fraud_risk_score` não encontrado no dataset.")

    st.subheader("Completude de Campos por Tier")
    pro_fields = [
        "velocity_transactions_1h", "velocity_transactions_6h",
        "velocity_transactions_7d", "velocity_transactions_30d",
        "accumulated_amount_1h", "accumulated_amount_6h",
        "distance_from_home_km", "is_known_location", "location_cluster_id",
        "fraud_labels", "bot_confidence_score", "automation_signature",
        "is_impossible_travel",
    ]
    team_fields = ["mule_tier", "mule_forward_ratio", "mule_network_size"]
    base_fields = [
        "transaction_id", "customer_id", "amount", "is_fraud", "fraud_type",
        "fraud_risk_score", "fraud_signals", "velocity_transactions_24h",
        "device_id", "geolocation_lat", "geolocation_lon", "status",
    ]

    rows = []
    for f in base_fields + pro_fields + team_fields:
        if f in df.columns:
            nr = null_rate(df[f])
            tier = "Base" if f in base_fields else ("Pro+" if f in pro_fields else "Team+")
            rows.append({"Campo": f, "Tier": tier, "Preenchido (%)": round(100 - nr, 1), "Nulo (%)": round(nr, 1)})

    if rows:
        comp_df = pd.DataFrame(rows)
        tier_colors = {"Base": "#22c55e", "Pro+": "#3b82f6", "Team+": "#f59e0b"}
        fig = px.bar(
            comp_df.sort_values("Tier"),
            x="Campo", y="Preenchido (%)", color="Tier",
            color_discrete_map=tier_colors,
            labels={"Preenchido (%)": "% Preenchido"},
        )
        fig.update_layout(template="plotly_dark", height=340, margin=dict(t=10, b=10),
                          xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PADRÕES DE FRAUDE
# ══════════════════════════════════════════════════════════════════════════════

with tabs[1]:
    st.subheader("Tipos de Fraude: Gerado vs Benchmark FEBRABAN")

    if "fraud_type" in df.columns and n_fraud > 0:
        fraud_df = df[df["is_fraud"] & df["fraud_type"].notna()]
        counts = fraud_df["fraud_type"].value_counts(normalize=True)

        compare_rows = []
        all_types = set(counts.index) | set(FEBRABAN_FRAUD_TYPES.keys())
        for ft in sorted(all_types):
            generated = counts.get(ft, 0.0)
            benchmark = FEBRABAN_FRAUD_TYPES.get(ft, None)
            compare_rows.append({
                "Tipo": ft,
                "Gerado (%)": round(generated * 100, 2),
                "FEBRABAN (%)": round(benchmark * 100, 2) if benchmark else None,
            })
        cdf = pd.DataFrame(compare_rows)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Gerado",
            x=cdf["Tipo"],
            y=cdf["Gerado (%)"],
            marker_color="#3b82f6",
        ))
        benchmarks = cdf["FEBRABAN (%)"].fillna(0)
        if benchmarks.sum() > 0:
            fig.add_trace(go.Bar(
                name="FEBRABAN (benchmark)",
                x=cdf["Tipo"],
                y=benchmarks,
                marker_color="#f59e0b",
                opacity=0.7,
            ))
        fig.update_layout(
            template="plotly_dark", barmode="group", height=380,
            xaxis_tickangle=-40, margin=dict(t=10, b=10),
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Risk Score por Tipo de Fraude")
            if "fraud_risk_score" in df.columns:
                fig = px.box(
                    fraud_df.dropna(subset=["fraud_risk_score"]),
                    x="fraud_type", y="fraud_risk_score",
                    color="fraud_type",
                    labels={"fraud_type": "Tipo", "fraud_risk_score": "Risk Score"},
                )
                fig.update_layout(template="plotly_dark", height=350, showlegend=False,
                                  xaxis_tickangle=-40, margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Valor Médio por Tipo de Fraude")
            if "amount" in df.columns:
                avg_by_type = fraud_df.groupby("fraud_type")["amount"].mean().sort_values(ascending=False)
                fig = px.bar(
                    x=avg_by_type.index, y=avg_by_type.values,
                    labels={"x": "Tipo", "y": "Valor Médio (R$)"},
                    color=avg_by_type.values,
                    color_continuous_scale="Reds",
                )
                fig.update_layout(template="plotly_dark", height=350, showlegend=False,
                                  xaxis_tickangle=-40, margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Multi-label Taxonomy (fraud_labels — Pro+)")
        if "fraud_labels" in df.columns:
            labels_data = df[df["fraud_labels"].notna()]["fraud_labels"]
            if len(labels_data) > 0:
                all_labels: Counter = Counter()
                for row in labels_data:
                    if isinstance(row, list):
                        all_labels.update(row)
                    elif isinstance(row, str):
                        try:
                            parsed = json.loads(row)
                            all_labels.update(parsed)
                        except Exception:
                            all_labels[row] += 1
                if all_labels:
                    ldf = pd.DataFrame(all_labels.most_common(20), columns=["Label", "Count"])
                    fig = px.bar(ldf, x="Label", y="Count", color="Count", color_continuous_scale="Blues")
                    fig.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum fraud_label encontrado.")
            else:
                st.info("Campo `fraud_labels` está null — requer plano Pro+.")
        else:
            st.info("Campo `fraud_labels` não presente — requer plano Pro+.")
    else:
        st.info("Nenhuma transação fraudulenta encontrada ou coluna `fraud_type` ausente.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SINAIS DE RISCO
# ══════════════════════════════════════════════════════════════════════════════

with tabs[2]:
    st.subheader("Sinais de Fraude Mais Frequentes")

    if "fraud_signals" in df.columns:
        fraud_rows = df[df["is_fraud"] & df["fraud_signals"].notna()]
        all_signals: Counter = Counter()
        for row in fraud_rows["fraud_signals"]:
            if isinstance(row, list):
                all_signals.update(row)
            elif isinstance(row, str):
                try:
                    parsed = json.loads(row)
                    all_signals.update(parsed)
                except Exception:
                    pass

        if all_signals:
            sig_df = pd.DataFrame(all_signals.most_common(17), columns=["Sinal", "Ocorrências"])
            fig = px.bar(
                sig_df, x="Ocorrências", y="Sinal", orientation="h",
                color="Ocorrências", color_continuous_scale="Reds",
                labels={"Ocorrências": "Transações fraudulentas com este sinal"},
            )
            fig.update_layout(template="plotly_dark", height=450, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum sinal encontrado nas transações fraudulentas.")
    else:
        st.info("Campo `fraud_signals` não encontrado.")

    st.markdown("---")
    st.subheader("Correlação entre Sinais Numéricos e is_fraud")

    numeric_candidates = [
        "fraud_risk_score", "velocity_transactions_24h", "accumulated_amount_24h",
        "velocity_transactions_1h", "distance_from_home_km", "hours_inactive",
        "bot_confidence_score", "customer_velocity_z_score", "amount",
        "velocity_transactions_6h", "velocity_transactions_7d",
    ]
    available_num = [c for c in numeric_candidates if c in df.columns]

    if len(available_num) >= 3:
        corr_df = df[[*available_num, "is_fraud"]].copy()
        corr_df["is_fraud"] = corr_df["is_fraud"].astype(int)
        corr_matrix = corr_df.dropna().corr()

        fig = px.imshow(
            corr_matrix,
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            text_auto=".2f",
            aspect="auto",
            title="Matriz de Correlação (incluindo is_fraud)",
        )
        fig.update_layout(template="plotly_dark", height=500, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Correlação de cada campo com is_fraud")
        corr_fraud = corr_matrix["is_fraud"].drop("is_fraud").sort_values(key=abs, ascending=False)
        colors = ["#ef4444" if v > 0 else "#3b82f6" for v in corr_fraud.values]
        fig2 = go.Figure(go.Bar(
            x=corr_fraud.index, y=corr_fraud.values,
            marker_color=colors,
            text=[f"{v:.3f}" for v in corr_fraud.values],
            textposition="outside",
        ))
        fig2.update_layout(
            template="plotly_dark", height=350,
            yaxis_title="Correlação com is_fraud",
            margin=dict(t=10, b=10),
            xaxis_tickangle=-40,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info(f"Campos numéricos encontrados: {available_num}. Necessário pelo menos 3.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PADRÕES TEMPORAIS
# ══════════════════════════════════════════════════════════════════════════════

with tabs[3]:
    if "_hour" in df.columns:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Transações por Hora do Dia")
            hour_all   = df.groupby("_hour").size().reset_index(name="Total")
            hour_fraud = df[df["is_fraud"]].groupby("_hour").size().reset_index(name="Fraude")
            hour_merge = hour_all.merge(hour_fraud, on="_hour", how="left").fillna(0)
            hour_merge["Fraude (%)"] = hour_merge["Fraude"] / hour_merge["Total"] * 100

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(
                x=hour_merge["_hour"], y=hour_merge["Total"],
                name="Total", marker_color="#334155", opacity=0.7,
            ), secondary_y=False)
            fig.add_trace(go.Scatter(
                x=hour_merge["_hour"], y=hour_merge["Fraude (%)"],
                name="% Fraude", mode="lines+markers",
                line=dict(color="#ef4444", width=2),
                marker=dict(size=6),
            ), secondary_y=True)
            fig.add_vrect(x0=22, x1=23.9, fillcolor="#ef4444", opacity=0.05, line_width=0)
            fig.add_vrect(x0=0, x1=6, fillcolor="#ef4444", opacity=0.05, line_width=0)
            fig.update_layout(
                template="plotly_dark", height=380, margin=dict(t=10, b=10),
                xaxis_title="Hora do dia",
                legend=dict(orientation="h", y=1.08),
                annotations=[dict(
                    x=2, y=max(hour_merge["Fraude (%)"]) * 0.9,
                    text="⚠ Zona de risco (22h–6h)",
                    showarrow=False, font=dict(color="#f87171", size=11),
                )]
            )
            fig.update_yaxes(title_text="Nº de transações", secondary_y=False)
            fig.update_yaxes(title_text="% fraudulentas", secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)

            # Validate night fraud concentration
            night_fraud = df[df["is_fraud"] & df["_hour"].isin(list(range(22, 24)) + list(range(0, 6)))].shape[0]
            night_pct = night_fraud / n_fraud if n_fraud > 0 else 0
            ok = night_pct >= 0.20
            st.markdown(f"**Fraudes noturnas (22h–6h):** {night_fraud:,} ({night_pct*100:.1f}%) "
                        f"{'✅' if ok else '⚠️ esperado > 20%'}")

        with col2:
            st.subheader("Fraudes por Dia da Semana")
            dow_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            if "_dow" in df.columns:
                dow_fraud = df[df["is_fraud"]].groupby("_dow").size()
                dow_all   = df.groupby("_dow").size()
                dow_pct   = (dow_fraud / dow_all * 100).fillna(0).reindex(range(7), fill_value=0)
                fig = px.bar(
                    x=[dow_names[i] for i in range(7)],
                    y=dow_pct.values,
                    color=dow_pct.values,
                    color_continuous_scale="Reds",
                    labels={"x": "Dia", "y": "% Fraudulentas"},
                )
                fig.update_layout(template="plotly_dark", height=380, showlegend=False,
                                  margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

        if "_date" in df.columns:
            st.subheader("Volume ao Longo do Tempo")
            daily = df.groupby(["_date", df["is_fraud"].map({True: "Fraude", False: "Legítimo"})]).size().reset_index()
            daily.columns = ["Data", "Tipo", "Transações"]
            fig = px.line(
                daily, x="Data", y="Transações", color="Tipo",
                color_discrete_map={"Fraude": "#ef4444", "Legítimo": "#22c55e"},
            )
            fig.update_layout(template="plotly_dark", height=280, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Campo `timestamp` não encontrado ou não parsável.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — GEOGRAFIA
# ══════════════════════════════════════════════════════════════════════════════

with tabs[4]:
    if "geolocation_lat" in df.columns and "geolocation_lon" in df.columns:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Mapa de Calor — Transações Fraudulentas")
            fraud_geo = df[df["is_fraud"] & df["geolocation_lat"].notna()][
                ["geolocation_lat", "geolocation_lon"]
            ].sample(min(5000, n_fraud)).rename(
                columns={"geolocation_lat": "lat", "geolocation_lon": "lon"}
            )
            if not fraud_geo.empty:
                st.map(fraud_geo, color="#ef4444")

        with col2:
            st.subheader("Distribuição por Estado Inferido")
            sample = df[df["geolocation_lat"].notna() & df["geolocation_lon"].notna()].sample(
                min(10000, len(df))
            )
            sample["_state"] = sample.apply(
                lambda r: infer_state(r["geolocation_lat"], r["geolocation_lon"]), axis=1
            )
            state_dist = sample.groupby(["_state", sample["is_fraud"].map({True: "Fraude", False: "Legítimo"})]).size().reset_index()
            state_dist.columns = ["Estado", "Tipo", "Transações"]
            fig = px.bar(
                state_dist, x="Estado", y="Transações", color="Tipo",
                barmode="stack",
                color_discrete_map={"Fraude": "#ef4444", "Legítimo": "#22c55e"},
            )
            fig.update_layout(template="plotly_dark", height=400, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Impossible Travel (Pro+)")
        imp_col = next((c for c in ["is_impossible_travel", "is_impossible_travel"] if c in df.columns), None)
        if imp_col:
            n_imp = df[imp_col].sum()
            st.metric("Eventos de Impossible Travel detectados", f"{n_imp:,}")
            imp_df = df[df[imp_col] == True]
            if not imp_df.empty and "min_travel_time_required_hours" in df.columns:
                fig = px.scatter(
                    imp_df.dropna(subset=["min_travel_time_required_hours", "actual_gap_hours"]),
                    x="actual_gap_hours", y="min_travel_time_required_hours",
                    color="fraud_type" if "fraud_type" in df.columns else None,
                    labels={
                        "actual_gap_hours": "Tempo real entre transações (h)",
                        "min_travel_time_required_hours": "Tempo mínimo de viagem necessário (h)",
                    },
                    title="Impossible Travel: tempo real vs mínimo necessário",
                )
                fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=10,
                              line=dict(color="red", dash="dash"))
                fig.update_layout(template="plotly_dark", height=350, margin=dict(t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Campo `is_impossible_travel` não encontrado — requer plano Pro+.")

        st.subheader("Geo Clustering (Pro+)")
        if "location_cluster_id" in df.columns:
            cluster_counts = df["location_cluster_id"].value_counts().reset_index()
            cluster_counts.columns = ["Cluster", "Transações"]
            fig = px.pie(cluster_counts, names="Cluster", values="Transações",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(template="plotly_dark", height=320, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Campo `location_cluster_id` não encontrado — requer plano Pro+.")
    else:
        st.info("Campos de geolocalização não encontrados.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — BOT & AUTOMAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

with tabs[5]:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("automation_signature por Tipo de Fraude (Pro+)")
        if "automation_signature" in df.columns and "fraud_type" in df.columns:
            sig_df = df[df["is_fraud"] & df["automation_signature"].notna()]
            if not sig_df.empty:
                cross = pd.crosstab(sig_df["fraud_type"], sig_df["automation_signature"])
                cross_pct = cross.div(cross.sum(axis=1), axis=0) * 100
                fig = px.imshow(
                    cross_pct,
                    color_continuous_scale="Blues",
                    text_auto=".0f",
                    aspect="auto",
                    labels={"color": "% do tipo"},
                    title="% por assinatura de automação",
                )
                fig.update_layout(template="plotly_dark", height=420, margin=dict(t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum dado de automation_signature disponível.")
        else:
            st.info("Campos `automation_signature` / `fraud_type` não encontrados — requer plano Pro+.")

    with col2:
        st.subheader("bot_confidence_score (Pro+)")
        if "bot_confidence_score" in df.columns:
            valid_bot = df[df["bot_confidence_score"].notna()]
            if not valid_bot.empty:
                fig = px.histogram(
                    valid_bot.assign(label=valid_bot["is_fraud"].map({True: "Fraude", False: "Legítimo"})),
                    x="bot_confidence_score",
                    color="label",
                    nbins=40,
                    barmode="overlay",
                    opacity=0.75,
                    color_discrete_map={"Fraude": "#ef4444", "Legítimo": "#22c55e"},
                    labels={"bot_confidence_score": "Bot Confidence Score (0-1)", "label": "Tipo"},
                )
                fig.update_layout(template="plotly_dark", height=380, margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

                avg_bot_fraud = valid_bot[valid_bot["is_fraud"]]["bot_confidence_score"].mean()
                avg_bot_legit = valid_bot[~valid_bot["is_fraud"]]["bot_confidence_score"].mean()
                ok_separation = (avg_bot_fraud - avg_bot_legit) > 0.3
                st.markdown(
                    f"**Fraude:** {avg_bot_fraud:.3f} · **Legítimo:** {avg_bot_legit:.3f} "
                    f"{'✅ boa separação' if ok_separation else '⚠️ separação baixa'}"
                )
            else:
                st.info("Campo `bot_confidence_score` presente mas todos nulos — requer plano Pro+.")
        else:
            st.info("Campo `bot_confidence_score` não encontrado — requer plano Pro+.")

    st.markdown("---")
    st.subheader("Velocity Windows (Pro+)")
    vel_cols = [c for c in ["velocity_transactions_1h", "velocity_transactions_6h",
                             "velocity_transactions_24h", "velocity_transactions_7d",
                             "velocity_transactions_30d"] if c in df.columns]
    if len(vel_cols) >= 2:
        vel_data = df[["is_fraud", *vel_cols]].dropna(subset=[vel_cols[0]])
        vel_melt = vel_data.melt(id_vars=["is_fraud"], value_vars=vel_cols,
                                  var_name="Janela", value_name="Transações")
        vel_melt["Tipo"] = vel_melt["is_fraud"].map({True: "Fraude", False: "Legítimo"})
        fig = px.box(
            vel_melt, x="Janela", y="Transações", color="Tipo",
            color_discrete_map={"Fraude": "#ef4444", "Legítimo": "#22c55e"},
            labels={"Janela": "Janela de Velocidade"},
        )
        fig.update_layout(template="plotly_dark", height=380, margin=dict(t=10, b=10),
                          xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Velocity windows não encontradas — requer plano Pro+. "
                "Apenas `velocity_transactions_24h` disponível no plano Free/Starter.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — QUALIDADE DOS DADOS
# ══════════════════════════════════════════════════════════════════════════════

with tabs[6]:
    st.subheader("Checklist de Validação Estatística")

    checks = []

    # Check 1: fraud rate
    fr_ok = EXPECTED_FRAUD_RATE_RANGE[0] <= fraud_rate <= EXPECTED_FRAUD_RATE_RANGE[1]
    checks.append(("Taxa de fraude no intervalo esperado (1–15%)", fr_ok,
                   f"{fraud_rate*100:.2f}%"))

    # Check 2: risk score separation
    if "fraud_risk_score" in df.columns:
        s_fraud = df[df["is_fraud"]]["fraud_risk_score"].median()
        s_legit = df[~df["is_fraud"]]["fraud_risk_score"].median()
        sep_ok = (s_fraud - s_legit) >= 30
        checks.append(("Risk score: mediana fraude – mediana legítimo ≥ 30pts", sep_ok,
                       f"Fraude: {s_fraud:.0f} · Legítimo: {s_legit:.0f} · Delta: {s_fraud-s_legit:.0f}"))

    # Check 3: fraud type diversity
    if "fraud_type" in df.columns and n_fraud > 0:
        n_types = df[df["is_fraud"]]["fraud_type"].nunique()
        div_ok = n_types >= 5
        checks.append((f"Diversidade de tipos de fraude (≥ 5 tipos)", div_ok,
                       f"{n_types} tipos distintos"))

    # Check 4: new_beneficiary higher for fraud
    if "new_beneficiary" in df.columns:
        nb_fraud = df[df["is_fraud"]]["new_beneficiary"].mean()
        nb_legit = df[~df["is_fraud"]]["new_beneficiary"].mean()
        nb_ok = nb_fraud > nb_legit * 2
        checks.append(("new_beneficiary: fraude >> legítimo (esperado: ≥2×)", nb_ok,
                       f"Fraude: {nb_fraud*100:.1f}% · Legítimo: {nb_legit*100:.1f}%"))

    # Check 5: fraud higher at night
    if "_hour" in df.columns and n_fraud > 0:
        night_hours = list(range(22, 24)) + list(range(0, 6))
        night_pct = df[df["is_fraud"] & df["_hour"].isin(night_hours)].shape[0] / n_fraud
        night_ok = night_pct >= 0.20
        checks.append(("Fraudes concentradas à noite (22h–6h ≥ 20%)", night_ok,
                       f"{night_pct*100:.1f}% das fraudes"))

    # Check 6: amount higher for fraud
    if "amount" in df.columns and n_fraud > 0 and n_legit > 0:
        amt_fraud = df[df["is_fraud"]]["amount"].median()
        amt_legit = df[~df["is_fraud"]]["amount"].median()
        amt_ok = amt_fraud > amt_legit
        checks.append(("Valor mediano: fraude > legítimo", amt_ok,
                       f"Fraude: R${amt_fraud:,.0f} · Legítimo: R${amt_legit:,.0f}"))

    # Check 7: velocity higher for fraud
    if "velocity_transactions_24h" in df.columns:
        v_fraud = df[df["is_fraud"]]["velocity_transactions_24h"].median()
        v_legit = df[~df["is_fraud"]]["velocity_transactions_24h"].median()
        vel_ok = v_fraud > v_legit
        checks.append(("Velocidade 24h: fraude > legítimo", vel_ok,
                       f"Fraude: {v_fraud:.0f} · Legítimo: {v_legit:.0f} txns/dia"))

    # Check 8: status APPROVED higher for legit
    if "status" in df.columns:
        legit_approved = (df[~df["is_fraud"]]["status"] == "APPROVED").mean()
        status_ok = legit_approved >= 0.90
        checks.append(("Transações legítimas: ≥ 90% APPROVED", status_ok,
                       f"{legit_approved*100:.1f}%"))

    # Check 9: sim_swap correlates with SIM_SWAP fraud type
    if "sim_swap_recent" in df.columns and "fraud_type" in df.columns:
        sim_swap_rate = df[df["fraud_type"] == "SIM_SWAP"]["sim_swap_recent"].mean() if "SIM_SWAP" in df["fraud_type"].values else None
        if sim_swap_rate is not None:
            ss_ok = sim_swap_rate >= 0.5
            checks.append(("SIM_SWAP: sim_swap_recent ≥ 50% das ocorrências", ss_ok,
                           f"{sim_swap_rate*100:.1f}%"))

    # Render checks
    passed = sum(1 for _, ok, _ in checks if ok)
    total_checks = len(checks)
    score = int(passed / total_checks * 10) if total_checks > 0 else 0

    st.markdown(
        f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px">
            <div style="font-size:48px;font-weight:700;color:{'#22c55e' if score >= 7 else '#f59e0b' if score >= 5 else '#ef4444'}">{score}/10</div>
            <div style="font-size:16px;color:#94a3b8">Score de Realismo · {passed}/{total_checks} checks passaram</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for label, ok, detail in checks:
        icon = "✅" if ok else "❌"
        color = "#22c55e" if ok else "#ef4444"
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 16px;
                        border-radius:8px;background:#1e293b;margin-bottom:6px;
                        border-left:3px solid {color}">
                <span style="font-size:18px">{icon}</span>
                <div>
                    <div style="color:#f1f5f9;font-size:14px">{label}</div>
                    <div style="color:#64748b;font-size:12px">{detail}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Taxa de Nulos por Campo Crítico")
        critical = [
            "transaction_id", "customer_id", "amount", "timestamp",
            "is_fraud", "fraud_type", "fraud_risk_score", "status",
            "geolocation_lat", "geolocation_lon",
        ]
        null_rows = []
        for f in critical:
            if f in df.columns:
                nr = null_rate(df[f])
                null_rows.append({"Campo": f, "Nulo (%)": round(nr, 2)})
        if null_rows:
            null_df = pd.DataFrame(null_rows)
            fig = px.bar(
                null_df.sort_values("Nulo (%)", ascending=False),
                x="Campo", y="Nulo (%)",
                color="Nulo (%)",
                color_continuous_scale="RdYlGn_r",
                range_color=[0, 20],
            )
            fig.update_layout(template="plotly_dark", height=320, margin=dict(t=10, b=10),
                              xaxis_tickangle=-40)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Estatísticas de Campos Numéricos")
        num_fields = [c for c in ["amount", "fraud_risk_score", "velocity_transactions_24h",
                                   "hours_inactive", "bot_confidence_score"] if c in df.columns]
        if num_fields:
            stats = df[num_fields].describe().T[["mean", "std", "min", "50%", "max"]]
            stats.columns = ["Média", "DP", "Min", "Mediana", "Max"]
            st.dataframe(stats.round(2), use_container_width=True)

    st.subheader("Amostra de Transações")
    sample_n = st.slider("Número de linhas", 5, 100, 20)
    show_fraud = st.checkbox("Mostrar apenas fraudes", value=True)
    sample_df = df[df["is_fraud"] == show_fraud].head(sample_n) if show_fraud else df.head(sample_n)
    key_cols = [c for c in [
        "transaction_id", "customer_id", "is_fraud", "fraud_type", "amount",
        "status", "fraud_risk_score", "fraud_signals", "automation_signature",
        "bot_confidence_score", "velocity_transactions_1h", "location_cluster_id",
    ] if c in df.columns]
    st.dataframe(sample_df[key_cols], use_container_width=True)
