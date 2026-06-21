"""Visão Executiva — KPIs estratégicos, tendências e ranking de regiões críticas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from utils.charts import bar_ranking, choropleth_bar_uf, line_trend
from utils.data_loader import load_data
from utils.filters import apply_filters, render_sidebar_filters
from utils.style import PALETTE, inject_css

st.set_page_config(page_title="Visão Executiva", page_icon="📊", layout="wide")
inject_css()

fact_acidentes, fact_pessoas, dim_uf = load_data()
selections = render_sidebar_filters(fact_acidentes, dim_uf)
df = apply_filters(fact_acidentes, selections)

st.title("📊 Visão Executiva")
st.caption("KPIs estratégicos para tomada de decisão rápida.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------------------------------
# KPIs estratégicos
# ---------------------------------------------------------------------------
total_acidentes = len(df)
total_vitimas = int(df["feridos_leves"].sum() + df["feridos_graves"].sum() + df["mortos"].sum())
total_obitos = int(df["mortos"].sum())
total_pessoas = int(df["pessoas"].sum())
taxa_mortalidade = round(100 * total_obitos / total_pessoas, 2) if total_pessoas else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de Acidentes", f"{total_acidentes:,}".replace(",", "."))
c2.metric("Total de Vítimas", f"{total_vitimas:,}".replace(",", "."))
c3.metric("Total de Óbitos", f"{total_obitos:,}".replace(",", "."))
c4.metric("Taxa de Mortalidade", f"{taxa_mortalidade}%")
c5.metric("Veículos Envolvidos", f"{int(df['veiculos'].sum()):,}".replace(",", "."))

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(choropleth_bar_uf(df, dim_uf, "Acidentes por Estado (UF)"), use_container_width=True)
with col2:
    st.plotly_chart(bar_ranking(df, "municipio", "Top 10 Municípios em Nº de Acidentes",
                                 n=10, color=PALETTE["roxo"]), use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(line_trend(df, "ano", "Evolução Anual de Acidentes"), use_container_width=True)
with col4:
    st.plotly_chart(line_trend(df, "ano_mes", "Evolução Mensal de Acidentes"), use_container_width=True)

st.divider()
st.markdown("### 🏆 Ranking de Regiões mais Críticas")
ranking = (
    df.groupby("regiao")
    .agg(acidentes=("id", "count"), mortos=("mortos", "sum"), feridos_graves=("feridos_graves", "sum"))
    .reset_index()
    .sort_values("mortos", ascending=False)
)
ranking["taxa_mortalidade_%"] = (100 * ranking["mortos"] / ranking["acidentes"]).round(2)
st.dataframe(
    ranking.rename(columns={"regiao": "Região", "acidentes": "Acidentes", "mortos": "Óbitos",
                             "feridos_graves": "Feridos Graves", "taxa_mortalidade_%": "Mortes / 100 Acid."}),
    use_container_width=True, hide_index=True,
)
