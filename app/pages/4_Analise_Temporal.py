"""Análise Temporal — série temporal, tendência, sazonalidade e comparação entre períodos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from utils.data_loader import load_data
from utils.filters import apply_filters, render_sidebar_filters
from utils.style import PALETTE, PLOTLY_TEMPLATE, inject_css

st.set_page_config(page_title="Análise Temporal", page_icon="📈", layout="wide")
inject_css()

fact_acidentes, fact_pessoas, dim_uf = load_data()
selections = render_sidebar_filters(fact_acidentes, dim_uf)
df = apply_filters(fact_acidentes, selections)

st.title("📈 Análise Temporal")
st.caption("Série temporal, sazonalidade e comparação entre períodos selecionados.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------------------------------
# Série temporal + linha de tendência (média móvel)
# ---------------------------------------------------------------------------
serie = df.groupby("ano_mes").size().reset_index(name="acidentes").sort_values("ano_mes")
serie["tendencia_3m"] = serie["acidentes"].rolling(3, min_periods=1).mean()

fig = px.line(serie, x="ano_mes", y=["acidentes", "tendencia_3m"], template=PLOTLY_TEMPLATE,
              color_discrete_sequence=[PALETTE["azul"], PALETTE["alerta_escuro"]],
              labels={"value": "Acidentes", "ano_mes": "Mês"})
fig.update_layout(title="Série Temporal Mensal + Tendência (média móvel 3 meses)", height=420,
                   legend_title_text="", font=dict(color=PALETTE["texto"]))
st.plotly_chart(fig, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    sazonal = df.groupby("mes_nome").size().reindex(
        ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    ).reset_index(name="acidentes")
    fig_s = px.bar(sazonal, x="mes_nome", y="acidentes", color_discrete_sequence=[PALETTE["verde"]],
                    template=PLOTLY_TEMPLATE, title="Sazonalidade — Acidentes por Mês (todos os anos)")
    fig_s.update_layout(height=380, font=dict(color=PALETTE["texto"]))
    st.plotly_chart(fig_s, use_container_width=True)
with col2:
    dias_ordem = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
                  "Sexta-feira", "Sábado", "Domingo"]
    por_dia = df.groupby("dia_semana").size().reindex(dias_ordem).reset_index(name="acidentes")
    fig_d = px.bar(por_dia, x="dia_semana", y="acidentes", color_discrete_sequence=[PALETTE["roxo"]],
                    template=PLOTLY_TEMPLATE, title="Acidentes por Dia da Semana")
    fig_d.update_layout(height=380, font=dict(color=PALETTE["texto"]))
    st.plotly_chart(fig_d, use_container_width=True)

st.divider()
st.markdown("### ⚖️ Comparação entre Períodos")
anos_disp = sorted(df["ano"].dropna().unique().tolist())
if len(anos_disp) >= 2:
    c1, c2 = st.columns(2)
    ano_a = c1.selectbox("Período A (ano)", anos_disp, index=0)
    ano_b = c2.selectbox("Período B (ano)", anos_disp, index=len(anos_disp) - 1)

    df_a, df_b = df[df["ano"] == ano_a], df[df["ano"] == ano_b]

    def _kpis(d):
        return len(d), int(d["mortos"].sum()), round(100 * d["mortos"].sum() / d["pessoas"].sum(), 2) if d["pessoas"].sum() else 0

    a_acid, a_mortos, a_taxa = _kpis(df_a)
    b_acid, b_mortos, b_taxa = _kpis(df_b)

    m1, m2, m3 = st.columns(3)
    m1.metric(f"Acidentes ({ano_b})", b_acid, delta=b_acid - a_acid)
    m2.metric(f"Óbitos ({ano_b})", b_mortos, delta=b_mortos - a_mortos)
    m3.metric(f"Taxa de Mortalidade ({ano_b})", f"{b_taxa}%", delta=round(b_taxa - a_taxa, 2))
else:
    st.info("Selecione (ou mantenha sem filtro) ao menos 2 anos no recorte para habilitar a comparação.")
