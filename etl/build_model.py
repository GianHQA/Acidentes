"""
ETL - Acidentes de Transito PRF (Datatran + Acidentes)
=======================================================
Le os CSVs brutos das pastas `datatran/` e `acidentes/` (2022-2025), aplica
limpeza/tratamento de qualidade de dados e grava um modelo otimizado em
Parquet dentro de `data_model/`, consumido pelo dashboard Streamlit.

Modelo gerado (estrela simplificada):
  - fact_acidentes.parquet : grao = 1 acidente  (fonte: datatran)
  - fact_pessoas.parquet   : grao = 1 pessoa/veiculo envolvido (fonte: acidentes)
  - dim_uf.parquet         : UF -> Regiao / nome completo

Executar: python etl/build_model.py
"""
import glob
import os

import numpy as np
import pandas as pd

RAW_DATATRAN = "datatran"
RAW_ACIDENTES = "acidentes"
OUT_DIR = "data_model"

# ---------------------------------------------------------------------------
# Dimensao auxiliar: UF -> Regiao / nome
# ---------------------------------------------------------------------------
UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte",
    "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

DIA_SEMANA_ORDEM = {
    "segunda-feira": 0, "terça-feira": 1, "quarta-feira": 2, "quinta-feira": 3,
    "sexta-feira": 4, "sábado": 5, "domingo": 6,
}
DIA_SEMANA_PT = {v: k.capitalize() for k, v in DIA_SEMANA_ORDEM.items()}


def _read_raw(folder, pattern):
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em {folder}/{pattern}")
    frames = []
    for f in files:
        df = pd.read_csv(f, sep=";", encoding="latin1", dtype=str, low_memory=False)
        df["arquivo_origem"] = os.path.basename(f)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _to_float_br(series):
    """Converte string numerica com decimal em virgula (pt-BR) para float."""
    return pd.to_numeric(
        series.astype(str).str.strip().str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def _clean_common(df):
    """Limpezas compartilhadas entre datatran e acidentes."""
    # Normaliza textos categoricos (strip espacos, evita variações de capitalização)
    text_cols = df.select_dtypes(include="object").columns
    for c in text_cols:
        if c == "arquivo_origem":
            continue
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"nan": np.nan, "NA": np.nan, "(null)": np.nan, "": np.nan})

    # Datas e derivacoes temporais
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce", format="%Y-%m-%d")
    df["ano"] = df["data_inversa"].dt.year
    df["mes"] = df["data_inversa"].dt.month
    df["dia"] = df["data_inversa"].dt.day
    df["mes_nome"] = df["data_inversa"].dt.month_name(locale="pt_BR.UTF-8") if False else df["data_inversa"].dt.strftime("%m")
    MESES_PT = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
    df["mes_nome"] = df["mes"].map(MESES_PT)
    df["ano_mes"] = df["data_inversa"].dt.to_period("M").astype(str)

    df["dia_semana"] = df["dia_semana"].str.lower()
    df["dia_semana_num"] = df["dia_semana"].map(DIA_SEMANA_ORDEM)
    df["dia_semana"] = df["dia_semana"].str.capitalize()

    hora = pd.to_datetime(df["horario"], errors="coerce", format="%H:%M:%S")
    df["hora"] = hora.dt.hour
    df["periodo_dia"] = pd.cut(
        df["hora"], bins=[-1, 5, 11, 17, 23],
        labels=["Madrugada (00-05h)", "Manhã (06-11h)", "Tarde (12-17h)", "Noite (18-23h)"],
    ).astype(str)

    # Geografia
    df["uf"] = df["uf"].str.upper()
    df["regiao"] = df["uf"].map(UF_REGIAO)
    df["municipio"] = df["municipio"].str.title()
    df["br"] = pd.to_numeric(df["br"], errors="coerce").astype("Int64")
    df["km"] = _to_float_br(df["km"])
    df["latitude"] = _to_float_br(df["latitude"])
    df["longitude"] = _to_float_br(df["longitude"])
    # Coordenadas fora do território brasileiro são inválidas/erro de digitação
    bad_geo = ~df["latitude"].between(-35, 6) | ~df["longitude"].between(-75, -28)
    df.loc[bad_geo, ["latitude", "longitude"]] = np.nan

    # Classificação textual ausente: preenchida depois (gravidade) com base nas vítimas
    df["classificacao_acidente"] = df["classificacao_acidente"].fillna("Não informado")

    return df


def build_fact_acidentes():
    print("Lendo arquivos datatran/*.csv ...")
    df = _read_raw(RAW_DATATRAN, "*.csv")
    df = df.drop_duplicates()  # remove linhas 100% idênticas
    df = df.drop_duplicates(subset="id", keep="first")  # garante grão único por acidente
    df = _clean_common(df)

    num_cols = ["pessoas", "mortos", "feridos_leves", "feridos_graves", "ilesos",
                "ignorados", "feridos", "veiculos"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # Gravidade derivada (mais granular e sem nulos, usada nas análises de risco)
    cond = [df["mortos"] > 0, df["feridos_graves"] > 0, df["feridos_leves"] > 0]
    escolhas = ["Fatal", "Grave", "Leve"]
    df["gravidade"] = np.select(cond, escolhas, default="Sem Vítimas") if hasattr(np, "select") else np.select(cond, escolhas, default="Sem Vítimas")
    df["taxa_mortalidade_acidente"] = np.where(df["pessoas"] > 0, df["mortos"] / df["pessoas"], 0)

    df["id"] = df["id"].astype(str)

    cols = ["id", "data_inversa", "ano", "mes", "mes_nome", "ano_mes", "dia",
            "dia_semana", "dia_semana_num", "horario", "hora", "periodo_dia",
            "fase_dia", "uf", "regiao", "br", "km", "municipio",
            "causa_acidente", "tipo_acidente", "classificacao_acidente", "gravidade",
            "sentido_via", "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
            "pessoas", "mortos", "feridos_leves", "feridos_graves", "ilesos", "ignorados",
            "feridos", "veiculos", "taxa_mortalidade_acidente",
            "latitude", "longitude", "regional", "delegacia", "uop", "arquivo_origem"]
    df = df[cols]
    print(f"fact_acidentes: {len(df):,} linhas, {df['id'].nunique():,} ids únicos")
    return df


def build_fact_pessoas(dim_acidentes):
    print("Lendo arquivos acidentes/*.csv ...")
    df = _read_raw(RAW_ACIDENTES, "*.csv")
    df = df.drop_duplicates()
    df = _clean_common(df)

    df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
    df.loc[~df["idade"].between(0, 120), "idade"] = np.nan
    faixas = [-1, 17, 24, 34, 44, 59, 200]
    labels = ["0-17", "18-24", "25-34", "35-44", "45-59", "60+"]
    df["faixa_etaria"] = pd.cut(df["idade"], bins=faixas, labels=labels).astype(str).replace("nan", "Não informado")

    df["sexo"] = df["sexo"].fillna("Não informado").replace({"Inválido": "Não informado"})
    df["tipo_envolvido"] = df["tipo_envolvido"].fillna("Veículo sem ocupante")
    df["estado_fisico"] = df["estado_fisico"].fillna("Não informado")
    df["tipo_veiculo"] = df["tipo_veiculo"].fillna("Não informado")
    df["marca"] = df["marca"].fillna("Não informado")

    for c in ["ilesos", "feridos_leves", "feridos_graves", "mortos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["id"] = df["id"].astype(str)
    # Mantém apenas pessoas/veículos cujo acidente existe no fato principal (integridade referencial)
    df = df[df["id"].isin(dim_acidentes["id"])]

    cols = ["id", "pesid", "id_veiculo", "data_inversa", "ano", "mes_nome", "ano_mes",
            "dia_semana", "hora", "periodo_dia", "uf", "regiao", "municipio",
            "causa_acidente", "tipo_acidente", "classificacao_acidente",
            "tipo_veiculo", "marca", "ano_fabricacao_veiculo", "tipo_envolvido",
            "estado_fisico", "idade", "faixa_etaria", "sexo",
            "ilesos", "feridos_leves", "feridos_graves", "mortos"]
    df = df[cols]
    print(f"fact_pessoas: {len(df):,} linhas")
    return df


def build_dim_uf():
    nomes = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
        "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
        "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
        "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
        "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
        "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
        "SE": "Sergipe", "TO": "Tocantins",
    }
    return pd.DataFrame({"uf": list(nomes.keys()), "uf_nome": list(nomes.values()),
                          "regiao": [UF_REGIAO[u] for u in nomes]})


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    fact_acidentes = build_fact_acidentes()
    fact_pessoas = build_fact_pessoas(fact_acidentes)
    dim_uf = build_dim_uf()

    fact_acidentes.to_parquet(os.path.join(OUT_DIR, "fact_acidentes.parquet"), index=False)
    fact_pessoas.to_parquet(os.path.join(OUT_DIR, "fact_pessoas.parquet"), index=False)
    dim_uf.to_parquet(os.path.join(OUT_DIR, "dim_uf.parquet"), index=False)

    print("\nModelo de dados gerado em:", os.path.abspath(OUT_DIR))
    print(" - fact_acidentes.parquet:", fact_acidentes.shape)
    print(" - fact_pessoas.parquet  :", fact_pessoas.shape)
    print(" - dim_uf.parquet        :", dim_uf.shape)


if __name__ == "__main__":
    main()
