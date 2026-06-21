"""Funções reutilizáveis de construção de gráficos Plotly."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.style import CATEGORICAL, GRAVIDADE_CORES, PALETTE, PLOTLY_TEMPLATE

# Centróides aproximados das capitais por UF — usados nos mapas de bolha por
# estado, evitando dependência de geojson externo / acesso à internet em runtime.
UF_CENTROIDS = {
    "AC": (-9.97, -67.81), "AL": (-9.66, -35.73), "AP": (0.03, -51.07),
    "AM": (-3.12, -60.02), "BA": (-12.97, -38.51), "CE": (-3.72, -38.54),
    "DF": (-15.78, -47.93), "ES": (-20.32, -40.34), "GO": (-16.68, -49.25),
    "MA": (-2.53, -44.30), "MT": (-15.60, -56.10), "MS": (-20.44, -54.65),
    "MG": (-19.92, -43.94), "PA": (-1.46, -48.50), "PB": (-7.12, -34.86),
    "PR": (-25.43, -49.27), "PE": (-8.05, -34.88), "PI": (-5.09, -42.80),
    "RJ": (-22.91, -43.17), "RN": (-5.79, -35.21), "RS": (-30.03, -51.23),
    "RO": (-8.76, -63.90), "RR": (2.82, -60.67), "SC": (-27.60, -48.55),
    "SP": (-23.55, -46.63), "SE": (-10.91, -37.07), "TO": (-10.18, -48.33),
}


def _fmt(fig, title=None, height=380):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(color=PALETTE["texto"]),
        legend_title_text="",
    )
    return fig


def bar_ranking(df, group_col, title, n=10, orientation="h", color=None):
    agg = df.groupby(group_col).size().reset_index(name="acidentes")
    agg = agg.sort_values("acidentes", ascending=False).head(n)
    if orientation == "h":
        agg = agg.sort_values("acidentes")
        fig = px.bar(agg, x="acidentes", y=group_col, orientation="h",
                     color_discrete_sequence=[color or PALETTE["azul"]], text="acidentes")
    else:
        fig = px.bar(agg, x=group_col, y="acidentes",
                     color_discrete_sequence=[color or PALETTE["azul"]], text="acidentes")
    fig.update_traces(textposition="outside")
    return _fmt(fig, title)


def line_trend(df, time_col, title, value_col=None, agg="count"):
    if agg == "count":
        serie = df.groupby(time_col).size().reset_index(name="valor")
    else:
        serie = df.groupby(time_col)[value_col].sum().reset_index(name="valor")
    serie = serie.sort_values(time_col)
    fig = px.line(serie, x=time_col, y="valor", markers=True,
                  color_discrete_sequence=[PALETTE["azul_escuro"]])
    fig.update_traces(line_width=3)
    return _fmt(fig, title)


def grouped_bar_by_gravidade(df, group_col, title, n=8):
    top_cats = df[group_col].value_counts().head(n).index
    sub = df[df[group_col].isin(top_cats)]
    agg = sub.groupby([group_col, "gravidade"]).size().reset_index(name="acidentes")
    fig = px.bar(agg, x=group_col, y="acidentes", color="gravidade", barmode="stack",
                 color_discrete_map=GRAVIDADE_CORES)
    fig.update_xaxes(categoryorder="total descending")
    return _fmt(fig, title)


def donut(df, group_col, title, n=6):
    agg = df.groupby(group_col).size().reset_index(name="acidentes")
    agg = agg.sort_values("acidentes", ascending=False)
    if len(agg) > n:
        topo = agg.head(n)
        outros = pd.DataFrame({group_col: ["Outros"], "acidentes": [agg["acidentes"].iloc[n:].sum()]})
        agg = pd.concat([topo, outros], ignore_index=True)
    fig = px.pie(agg, names=group_col, values="acidentes", hole=0.55,
                 color_discrete_sequence=CATEGORICAL)
    return _fmt(fig, title)


def heatmap_dia_hora(df, title):
    agg = df.groupby(["dia_semana_num", "hora"]).size().reset_index(name="acidentes")
    dias = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}
    agg["dia"] = agg["dia_semana_num"].map(dias)
    pivot = agg.pivot(index="dia", columns="hora", values="acidentes").reindex(list(dias.values()))
    fig = px.imshow(pivot, color_continuous_scale=[PALETTE["branco"], PALETTE["azul"], PALETTE["roxo_escuro"]],
                     aspect="auto", labels=dict(x="Hora do dia", y="Dia da semana", color="Acidentes"))
    return _fmt(fig, title, height=420)


def density_map(df, title):
    sub = df.dropna(subset=["latitude", "longitude"])
    fig = px.density_map(sub, lat="latitude", lon="longitude", radius=6, zoom=3,
                          center=dict(lat=-15, lon=-54), map_style="open-street-map",
                          color_continuous_scale=[PALETTE["azul"], PALETTE["roxo_escuro"], PALETTE["alerta_escuro"]])
    return _fmt(fig, title, height=520)


def bubble_map_by_uf(df, dim_uf, title):
    agg = df.groupby("uf").agg(acidentes=("id", "count"), mortos=("mortos", "sum")).reset_index()
    agg["lat"] = agg["uf"].map(lambda u: UF_CENTROIDS.get(u, (None, None))[0])
    agg["lon"] = agg["uf"].map(lambda u: UF_CENTROIDS.get(u, (None, None))[1])
    agg = agg.merge(dim_uf, on="uf", how="left")
    fig = px.scatter_map(agg, lat="lat", lon="lon", size="acidentes", color="mortos",
                          hover_name="uf_nome", size_max=45, zoom=3,
                          center=dict(lat=-15, lon=-54), map_style="open-street-map",
                          color_continuous_scale=[PALETTE["verde"], PALETTE["alerta"], PALETTE["alerta_escuro"]],
                          hover_data={"acidentes": True, "mortos": True, "lat": False, "lon": False})
    return _fmt(fig, title, height=520)


def cluster_map(df, n_clusters, title):
    from sklearn.cluster import KMeans

    sub = df.dropna(subset=["latitude", "longitude"]).copy()
    if len(sub) < n_clusters:
        n_clusters = max(1, len(sub))
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    sub["cluster"] = km.fit_predict(sub[["latitude", "longitude"]]).astype(str)
    fig = px.scatter_map(sub.sample(min(len(sub), 20000), random_state=42), lat="latitude", lon="longitude",
                          color="cluster", zoom=3, center=dict(lat=-15, lon=-54),
                          map_style="open-street-map", color_discrete_sequence=CATEGORICAL,
                          opacity=0.6)
    return _fmt(fig, title, height=520)


def choropleth_bar_uf(df, dim_uf, title, metric="acidentes"):
    agg = df.groupby("uf").agg(acidentes=("id", "count"), mortos=("mortos", "sum")).reset_index()
    agg = agg.merge(dim_uf, on="uf", how="left").sort_values(metric, ascending=False)
    fig = px.bar(agg, x="uf", y=metric, color=metric, text=metric,
                 color_continuous_scale=[PALETTE["azul"], PALETTE["roxo_escuro"]],
                 hover_data={"uf_nome": True})
    fig.update_traces(textposition="outside")
    return _fmt(fig, title)
