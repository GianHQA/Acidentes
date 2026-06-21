"""Carregamento (cacheado) do modelo de dados em Parquet."""
import pathlib

import pandas as pd
import streamlit as st

DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "data_model"


@st.cache_data(show_spinner="Carregando base de acidentes...")
def load_data():
    fact_acidentes = pd.read_parquet(DATA_DIR / "fact_acidentes.parquet")
    fact_pessoas = pd.read_parquet(DATA_DIR / "fact_pessoas.parquet")
    dim_uf = pd.read_parquet(DATA_DIR / "dim_uf.parquet")

    # Denormaliza colunas de filtro (br, gravidade) para a fact de pessoas,
    # garantindo os mesmos filtros globais em todas as páginas.
    fact_pessoas = fact_pessoas.merge(
        fact_acidentes[["id", "br", "gravidade"]], on="id", how="left"
    )
    return fact_acidentes, fact_pessoas, dim_uf
