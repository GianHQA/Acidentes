"""Visão Operacional — análise detalhada, tabela dinâmica, drill-down e drill-through."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from utils.charts import donut, grouped_bar_by_gravidade
from utils.data_loader import load_data
from utils.filters import apply_filters, render_sidebar_filters
from utils.style import inject_css

st.set_page_config(page_title="Visão Operacional", page_icon="🛠️", layout="wide")
inject_css()

fact_acidentes, fact_pessoas, dim_uf = load_data()
selections = render_sidebar_filters(fact_acidentes, dim_uf)
df = apply_filters(fact_acidentes, selections)
dfp = apply_filters(fact_pessoas, selections)

st.title("🛠️ Visão Operacional")
st.caption("Análise detalhada por tipo, causa, clima, pista e segmentações cruzadas.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

DIMENSOES = {
    "Tipo de Acidente": "tipo_acidente", "Causa do Acidente": "causa_acidente",
    "Condição Climática": "condicao_metereologica", "Tipo de Pista": "tipo_pista",
    "Sentido da Via": "sentido_via", "Fase do Dia": "fase_dia",
    "Dia da Semana": "dia_semana", "Município": "municipio", "Estado (UF)": "uf",
}

col1, col2 = st.columns(2)
with col1:
    dim1_label = st.selectbox("Dimensão principal", list(DIMENSOES.keys()), index=0)
with col2:
    dim2_label = st.selectbox("Segmentar cruzando com (gravidade)", ["Gravidade"], index=0, disabled=True)

dim1 = DIMENSOES[dim1_label]

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(grouped_bar_by_gravidade(df, dim1, f"{dim1_label} x Gravidade (Top 8)"),
                     use_container_width=True)
with c2:
    st.plotly_chart(donut(df, dim1, f"Distribuição por {dim1_label}"), use_container_width=True)

st.divider()
st.markdown("### 📋 Tabela Dinâmica")
st.caption("Selecione as dimensões para agrupar e veja as métricas agregadas — clique nas colunas para ordenar.")

dims_sel = st.multiselect("Agrupar por", list(DIMENSOES.keys()), default=[dim1_label])
group_cols = [DIMENSOES[d] for d in dims_sel] or [dim1]

pivot = (
    df.groupby(group_cols)
    .agg(acidentes=("id", "count"), mortos=("mortos", "sum"), feridos_graves=("feridos_graves", "sum"),
         feridos_leves=("feridos_leves", "sum"))
    .reset_index()
    .sort_values("acidentes", ascending=False)
)
st.dataframe(pivot, use_container_width=True, hide_index=True, height=320)

st.divider()
st.markdown("### 🔎 Drill-down / Drill-through")
st.caption("Escolha um valor da dimensão principal para ver o detalhe — até o nível de pessoas/veículos envolvidos.")

valores = df[dim1].dropna().value_counts().index.tolist()
valor_sel = st.selectbox(f"Selecione um valor de '{dim1_label}' para detalhar", valores)

sub_acidentes = df[df[dim1] == valor_sel]
sub_pessoas = dfp[dfp[dim1] == valor_sel] if dim1 in dfp.columns else pd.DataFrame()

m1, m2, m3 = st.columns(3)
m1.metric("Acidentes neste recorte", len(sub_acidentes))
m2.metric("Óbitos", int(sub_acidentes["mortos"].sum()))
m3.metric("Pessoas envolvidas (drill-through)", len(sub_pessoas))

tab1, tab2 = st.tabs(["Acidentes (grão = ocorrência)", "Pessoas / Veículos (grão = envolvido)"])
with tab1:
    st.dataframe(
        sub_acidentes[["id", "data_inversa", "uf", "municipio", "causa_acidente", "tipo_acidente",
                       "classificacao_acidente", "gravidade", "mortos", "feridos_graves"]]
        .sort_values("data_inversa", ascending=False),
        use_container_width=True, hide_index=True, height=300,
    )
with tab2:
    if not sub_pessoas.empty:
        st.dataframe(
            sub_pessoas[["id", "pesid", "tipo_veiculo", "marca", "tipo_envolvido", "estado_fisico",
                        "idade", "faixa_etaria", "sexo"]],
            use_container_width=True, hide_index=True, height=300,
        )
    else:
        st.info("Dimensão não disponível na granularidade de pessoas para drill-through direto.")
