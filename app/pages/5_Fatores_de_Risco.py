"""Fatores de Risco — causas, condições e perfis associados a acidentes graves/fatais."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from utils.charts import heatmap_dia_hora
from utils.data_loader import load_data
from utils.filters import apply_filters, render_sidebar_filters
from utils.style import GRAVIDADE_CORES, PALETTE, PLOTLY_TEMPLATE, inject_css

st.set_page_config(page_title="Fatores de Risco", page_icon="⚠️", layout="wide")
inject_css()

fact_acidentes, fact_pessoas, dim_uf = load_data()
selections = render_sidebar_filters(fact_acidentes, dim_uf)
df = apply_filters(fact_acidentes, selections)
dfp = apply_filters(fact_pessoas, selections)

st.title("⚠️ Fatores de Risco")
st.caption("O que mais contribui para acidentes graves e fatais.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

st.plotly_chart(heatmap_dia_hora(df, "Mapa de Calor: Dia da Semana x Horário"), use_container_width=True)

st.divider()
col1, col2 = st.columns(2)
with col1:
    top_causas = df["causa_acidente"].value_counts().head(10).index
    sub = df[df["causa_acidente"].isin(top_causas)]
    taxa = sub.groupby("causa_acidente").apply(
        lambda s: round(100 * (s["gravidade"] == "Fatal").mean(), 1)
    ).reset_index(name="taxa_fatal_%").sort_values("taxa_fatal_%", ascending=True)
    fig = px.bar(taxa, x="taxa_fatal_%", y="causa_acidente", orientation="h",
                 color_discrete_sequence=[PALETTE["alerta_escuro"]], text="taxa_fatal_%",
                 template=PLOTLY_TEMPLATE, title="Top 10 Causas — % de Acidentes Fatais")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=420, font=dict(color=PALETTE["texto"]))
    st.plotly_chart(fig, use_container_width=True)
with col2:
    clima = df.groupby("condicao_metereologica").agg(
        acidentes=("id", "count"), mortos=("mortos", "sum")
    ).reset_index()
    clima["taxa_mortalidade"] = (100 * clima["mortos"] / clima["acidentes"]).round(2)
    clima = clima.sort_values("acidentes", ascending=False)
    fig2 = px.bar(clima, x="condicao_metereologica", y="acidentes", color="taxa_mortalidade",
                  color_continuous_scale=[PALETTE["verde"], PALETTE["alerta"], PALETTE["alerta_escuro"]],
                  template=PLOTLY_TEMPLATE, title="Condição Climática: Volume e Taxa de Mortalidade")
    fig2.update_layout(height=420, font=dict(color=PALETTE["texto"]))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
col3, col4 = st.columns(2)
with col3:
    pista = df.groupby(["tipo_pista", "gravidade"]).size().reset_index(name="acidentes")
    fig3 = px.bar(pista, x="tipo_pista", y="acidentes", color="gravidade", barmode="group",
                  color_discrete_map=GRAVIDADE_CORES, template=PLOTLY_TEMPLATE,
                  title="Tipo de Pista x Gravidade")
    fig3.update_layout(height=380, font=dict(color=PALETTE["texto"]))
    st.plotly_chart(fig3, use_container_width=True)
with col4:
    tracado = df["tracado_via"].value_counts().head(8).reset_index()
    tracado.columns = ["tracado_via", "acidentes"]
    fig4 = px.bar(tracado, x="acidentes", y="tracado_via", orientation="h",
                  color_discrete_sequence=[PALETTE["roxo"]], template=PLOTLY_TEMPLATE,
                  title="Top 8 Traçados de Via")
    fig4.update_layout(height=380, font=dict(color=PALETTE["texto"]))
    st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.markdown("### 👤 Perfil das Vítimas (granularidade de pessoas)")
if not dfp.empty:
    col5, col6 = st.columns(2)
    with col5:
        faixa = dfp[dfp["mortos"] > 0]["faixa_etaria"].value_counts().reset_index()
        faixa.columns = ["faixa_etaria", "obitos"]
        fig5 = px.bar(faixa, x="faixa_etaria", y="obitos", color_discrete_sequence=[PALETTE["alerta_escuro"]],
                      template=PLOTLY_TEMPLATE, title="Óbitos por Faixa Etária")
        fig5.update_layout(height=360, font=dict(color=PALETTE["texto"]))
        st.plotly_chart(fig5, use_container_width=True)
    with col6:
        sexo = dfp[dfp["mortos"] > 0]["sexo"].value_counts().reset_index()
        sexo.columns = ["sexo", "obitos"]
        fig6 = px.pie(sexo, names="sexo", values="obitos", hole=0.5,
                      color_discrete_sequence=[PALETTE["azul"], PALETTE["roxo"], PALETTE["cinza_medio"]],
                      template=PLOTLY_TEMPLATE, title="Óbitos por Sexo")
        fig6.update_layout(height=360, font=dict(color=PALETTE["texto"]))
        st.plotly_chart(fig6, use_container_width=True)
