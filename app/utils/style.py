"""Paleta de cores e estilo visual (pastel, profissional) do dashboard."""
import streamlit as st

PALETTE = {
    "azul": "#8EC5E8",
    "azul_escuro": "#5B9BD5",
    "verde": "#9ED9B8",
    "verde_escuro": "#5FB888",
    "roxo": "#C3B1E1",
    "roxo_escuro": "#9B7FC7",
    "cinza_claro": "#EDEFF2",
    "cinza_medio": "#B0B6C0",
    "branco": "#FFFFFF",
    "texto": "#3A3F4B",
    "alerta": "#F3B6A1",
    "alerta_escuro": "#E08E72",
}

# Paleta categórica (ordem usada nos gráficos com múltiplas categorias)
CATEGORICAL = [PALETTE["azul"], PALETTE["verde"], PALETTE["roxo"], PALETTE["alerta"],
               PALETTE["azul_escuro"], PALETTE["verde_escuro"], PALETTE["roxo_escuro"],
               PALETTE["cinza_medio"], PALETTE["alerta_escuro"]]

GRAVIDADE_CORES = {
    "Fatal": PALETTE["alerta_escuro"],
    "Grave": PALETTE["alerta"],
    "Leve": PALETTE["azul"],
    "Sem Vítimas": PALETTE["verde"],
}

PLOTLY_TEMPLATE = "plotly_white"


def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: {PALETTE['branco']}; }}
        section[data-testid="stSidebar"] {{ background-color: {PALETTE['cinza_claro']}; }}
        h1, h2, h3 {{ color: {PALETTE['texto']}; font-family: 'Segoe UI', sans-serif; }}
        div[data-testid="stMetric"] {{
            background-color: {PALETTE['cinza_claro']};
            border: 1px solid #E2E5EA;
            border-radius: 12px;
            padding: 14px 16px 8px 16px;
        }}
        div[data-testid="stMetricLabel"] {{ color: {PALETTE['texto']}; font-weight: 600; }}
        .insight-card {{
            background-color: {PALETTE['cinza_claro']};
            border-left: 5px solid {PALETTE['azul_escuro']};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
            color: {PALETTE['texto']};
            font-size: 0.95rem;
        }}
        .insight-card.alerta {{ border-left-color: {PALETTE['alerta_escuro']}; }}
        .insight-card.positivo {{ border-left-color: {PALETTE['verde_escuro']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
