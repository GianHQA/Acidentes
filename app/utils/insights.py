"""Geração automática de insights em linguagem natural a partir dos dados filtrados.

Cada insight é uma frase curta, calculada dinamicamente sobre o recorte de
dados atualmente selecionado pelos filtros globais — por isso a narrativa
muda conforme o usuário explora o dashboard.
"""


def _pct(n, total):
    return 0 if total == 0 else round(100 * n / total, 1)


def generate_insights(df, dim_uf):
    """df = fact_acidentes já filtrada. Retorna lista de dicts {texto, tipo}."""
    insights = []
    total = len(df)
    if total == 0:
        return [{"texto": "Nenhum acidente encontrado para os filtros selecionados.", "tipo": "info"}]

    # 1. Concentração geográfica
    top_uf = df["uf"].value_counts()
    if not top_uf.empty:
        uf, n = top_uf.index[0], top_uf.iloc[0]
        nome = dim_uf.set_index("uf")["uf_nome"].get(uf, uf)
        insights.append({
            "texto": f"O estado de **{nome} ({uf})** concentrou **{_pct(n, total)}%** dos acidentes "
                     f"do período analisado ({n:,} ocorrências).".replace(",", "."),
            "tipo": "alerta" if _pct(n, total) > 15 else "info",
        })

    # 2. Horário crítico
    por_hora = df.groupby("hora").size()
    if not por_hora.empty:
        media_geral = por_hora.mean()
        pico = por_hora.idxmax()
        variacao = _pct(por_hora.max() - media_geral, media_geral) if media_geral else 0
        insights.append({
            "texto": f"O horário das **{int(pico):02d}h às {int(pico)+1:02d}h** concentra o maior volume de "
                     f"acidentes, **{variacao}%** acima da média horária do período.",
            "tipo": "alerta" if variacao > 30 else "info",
        })

    # 3. Dia da semana mais crítico (graves/fatais)
    graves = df[df["gravidade"].isin(["Fatal", "Grave"])]
    if not graves.empty:
        dia_top = graves["dia_semana"].value_counts().idxmax()
        insights.append({
            "texto": f"**{dia_top}** é o dia da semana com maior concentração de acidentes "
                     f"graves ou fatais.",
            "tipo": "alerta",
        })

    # 4. Tendência temporal (primeiro vs último ano disponível no recorte)
    anos = sorted(df["ano"].dropna().unique())
    if len(anos) >= 2:
        primeiro, ultimo = anos[0], anos[-1]
        n_primeiro = (df["ano"] == primeiro).sum()
        n_ultimo = (df["ano"] == ultimo).sum()
        if n_primeiro > 0:
            var = round(100 * (n_ultimo - n_primeiro) / n_primeiro, 1)
            direcao = "aumento" if var > 0 else "redução"
            insights.append({
                "texto": f"Houve **{direcao} de {abs(var)}%** no número de acidentes entre "
                         f"{int(primeiro)} e {int(ultimo)}.",
                "tipo": "alerta" if var > 0 else "positivo",
            })

    # 5. Principal causa de acidentes fatais
    fatais = df[df["gravidade"] == "Fatal"]
    if not fatais.empty:
        causa_top = fatais["causa_acidente"].value_counts()
        causa, n_causa = causa_top.index[0], causa_top.iloc[0]
        insights.append({
            "texto": f"**\"{causa}\"** é a principal causa entre os acidentes fatais, "
                     f"responsável por **{_pct(n_causa, len(fatais))}%** deles.",
            "tipo": "alerta",
        })

    # 6. Condição climática associada a maior letalidade
    if "condicao_metereologica" in df.columns:
        por_clima = df.groupby("condicao_metereologica")["mortos"].sum()
        contagem_clima = df.groupby("condicao_metereologica").size()
        taxa_clima = (por_clima / contagem_clima).dropna()
        taxa_clima = taxa_clima[contagem_clima >= max(30, total * 0.01)]
        if not taxa_clima.empty:
            clima_top = taxa_clima.idxmax()
            insights.append({
                "texto": f"Acidentes em condição **\"{clima_top}\"** apresentam a maior taxa de "
                         f"mortes por ocorrência entre as condições climáticas analisadas.",
                "tipo": "info",
            })

    # 7. Taxa de mortalidade geral
    total_pessoas = df["pessoas"].sum()
    total_mortos = df["mortos"].sum()
    if total_pessoas > 0:
        taxa = round(100 * total_mortos / total_pessoas, 2)
        insights.append({
            "texto": f"A taxa de mortalidade do período é de **{taxa}%** "
                     f"({int(total_mortos):,} óbitos em {int(total_pessoas):,} pessoas envolvidas).".replace(",", "."),
            "tipo": "alerta" if taxa > 3 else "info",
        })

    # 8. Padrão oculto: tipo de pista x gravidade
    if "tipo_pista" in df.columns:
        por_pista = df.groupby("tipo_pista")["gravidade"].apply(lambda s: (s == "Fatal").mean())
        cnt_pista = df.groupby("tipo_pista").size()
        por_pista = por_pista[cnt_pista >= max(30, total * 0.01)]
        if not por_pista.empty:
            pista_top = por_pista.idxmax()
            insights.append({
                "texto": f"Pistas do tipo **\"{pista_top}\"** apresentam a maior proporção de "
                         f"acidentes fatais — um padrão relevante para ações de engenharia viária.",
                "tipo": "info",
            })

    return insights
