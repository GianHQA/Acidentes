"""Filtros globais sincronizados entre todas as páginas do dashboard.

Os widgets usam chaves fixas em `st.session_state`, o que faz o Streamlit
preservar a seleção do usuário ao navegar entre páginas dentro da mesma sessão.
"""
import streamlit as st

PERIODOS = ["Madrugada (00-05h)", "Manhã (06-11h)", "Tarde (12-17h)", "Noite (18-23h)"]
GRAVIDADES = ["Fatal", "Grave", "Leve", "Sem Vítimas"]


def render_sidebar_filters(fact_acidentes, dim_uf):
    st.sidebar.header("🔎 Filtros Globais")
    st.sidebar.caption("Aplicados a todas as páginas do dashboard.")

    anos = sorted(fact_acidentes["ano"].dropna().unique().tolist())
    sel_anos = st.sidebar.multiselect("Ano", anos, default=[], key="f_anos")

    meses = (
        fact_acidentes[["mes", "mes_nome"]].drop_duplicates().sort_values("mes")
    )
    sel_meses = st.sidebar.multiselect(
        "Mês", meses["mes_nome"].tolist(), default=[], key="f_meses"
    )

    ufs = sorted(fact_acidentes["uf"].dropna().unique().tolist())
    sel_ufs = st.sidebar.multiselect("Estado (UF)", ufs, default=[], key="f_ufs")

    # Cascata: município depende do(s) estado(s) selecionado(s)
    base_mun = fact_acidentes if not sel_ufs else fact_acidentes[fact_acidentes["uf"].isin(sel_ufs)]
    municipios = sorted(base_mun["municipio"].dropna().unique().tolist())
    sel_municipios = st.sidebar.multiselect("Município", municipios, default=[], key="f_municipios")

    brs = sorted(fact_acidentes["br"].dropna().unique().tolist())
    sel_brs = st.sidebar.multiselect("BR", brs, default=[], key="f_brs")

    tipos = sorted(fact_acidentes["tipo_acidente"].dropna().unique().tolist())
    sel_tipos = st.sidebar.multiselect("Tipo de Acidente", tipos, default=[], key="f_tipos")

    sel_gravidade = st.sidebar.multiselect("Gravidade", GRAVIDADES, default=[], key="f_gravidade")

    sel_periodo = st.sidebar.multiselect("Período do Dia", PERIODOS, default=[], key="f_periodo")

    if st.sidebar.button("🧹 Limpar filtros"):
        for k in ["f_anos", "f_meses", "f_ufs", "f_municipios", "f_brs", "f_tipos",
                  "f_gravidade", "f_periodo"]:
            st.session_state[k] = []
        st.rerun()

    return {
        "anos": sel_anos,
        "meses": sel_meses,
        "ufs": sel_ufs,
        "municipios": sel_municipios,
        "brs": sel_brs,
        "tipos": sel_tipos,
        "gravidade": sel_gravidade,
        "periodo": sel_periodo,
    }


def apply_filters(df, selections):
    """Aplica o dicionário de seleções a qualquer fact table compatível."""
    mask = None

    def _and(cond):
        nonlocal mask
        mask = cond if mask is None else (mask & cond)

    if selections["anos"]:
        _and(df["ano"].isin(selections["anos"]))
    if selections["meses"]:
        _and(df["mes_nome"].isin(selections["meses"]))
    if selections["ufs"]:
        _and(df["uf"].isin(selections["ufs"]))
    if selections["municipios"]:
        _and(df["municipio"].isin(selections["municipios"]))
    if selections["brs"]:
        _and(df["br"].isin(selections["brs"]))
    if selections["tipos"]:
        _and(df["tipo_acidente"].isin(selections["tipos"]))
    if selections["gravidade"]:
        _and(df["gravidade"].isin(selections["gravidade"]))
    if selections["periodo"]:
        _and(df["periodo_dia"].isin(selections["periodo"]))

    return df if mask is None else df[mask]
