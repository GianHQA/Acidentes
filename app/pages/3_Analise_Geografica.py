"""Análise Geográfica — mapa de calor, clusterização e distribuição por estado/município."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from utils.charts import bar_ranking, bubble_map_by_uf, cluster_map, density_map
from utils.data_loader import load_data
from utils.filters import apply_filters, render_sidebar_filters
from utils.style import PALETTE, inject_css

st.set_page_config(page_title="Análise Geográfica", page_icon="🗺️", layout="wide")
inject_css()

fact_acidentes, fact_pessoas, dim_uf = load_data()
selections = render_sidebar_filters(fact_acidentes, dim_uf)
df = apply_filters(fact_acidentes, selections)

st.title("🗺️ Análise Geográfica")
st.caption("Distribuição espacial dos acidentes — mapa de calor, clusters e ranking por estado/município.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

com_geo = df.dropna(subset=["latitude", "longitude"])
pct_geo = round(100 * len(com_geo) / len(df), 1)
st.info(f"📍 {len(com_geo):,} de {len(df):,} acidentes possuem coordenadas geográficas válidas "
        f"({pct_geo}%). Os mapas abaixo consideram apenas esses registros.".replace(",", "."))

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(density_map(df, "Mapa de Calor de Acidentes"), use_container_width=True)
with col2:
    st.plotly_chart(bubble_map_by_uf(df, dim_uf, "Distribuição por Estado (tamanho=acidentes, cor=óbitos)"),
                     use_container_width=True)

st.divider()
n_clusters = st.slider("Número de clusters geográficos (K-Means)", 3, 15, 8)
st.plotly_chart(cluster_map(df, n_clusters, "Clusterização Geográfica de Acidentes"), use_container_width=True)

st.divider()
col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(bar_ranking(df, "uf", "Acidentes por Estado", n=27, color=PALETTE["azul"]),
                     use_container_width=True)
with col4:
    st.plotly_chart(bar_ranking(df, "municipio", "Top 15 Municípios", n=15, color=PALETTE["roxo"]),
                     use_container_width=True)
