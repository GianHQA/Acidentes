"""
Dashboard Executivo — Acidentes de Trânsito (PRF / Datatran)
==============================================================
Página inicial: contextualiza o dashboard, define os filtros globais
(compartilhados via st.session_state com todas as páginas) e apresenta
um resumo rápido de navegação.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from utils.data_loader import load_data
from utils.filters import render_sidebar_filters, apply_filters
from utils.style import inject_css, PALETTE

st.set_page_config(page_title="Acidentes de Trânsito | Dashboard Executivo",
                    page_icon="🚦", layout="wide")
inject_css()

fact_acidentes, fact_pessoas, dim_uf = load_data()
selections = render_sidebar_filters(fact_acidentes, dim_uf)
df = apply_filters(fact_acidentes, selections)

st.title("🚦 Dashboard de Acidentes de Trânsito Federais")
st.caption("Fonte: Polícia Rodoviária Federal (PRF) — bases *Datatran* (acidente) e *Acidentes* (pessoas/veículos), 2022–2025.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Acidentes no recorte", f"{len(df):,}".replace(",", "."))
c2.metric("Vítimas (mortos)", f"{int(df['mortos'].sum()):,}".replace(",", "."))
c3.metric("Estados (UF) cobertos", df["uf"].nunique())
c4.metric("Período", f"{int(df['ano'].min())}–{int(df['ano'].max())}" if len(df) else "—")

st.divider()
st.markdown("### 🧭 Como navegar")
st.markdown(
    """
Use o menu lateral **Pages** para explorar as visões do dashboard. Os filtros globais
(painel à esquerda) valem para **todas** as páginas e permanecem aplicados ao navegar.

- **Visão Executiva** — KPIs estratégicos, tendência anual/mensal e ranking de regiões críticas.
- **Visão Operacional** — análise detalhada por tipo, causa, clima, pista, com tabelas dinâmicas e drill-down.
- **Análise Geográfica** — mapa de calor, clusterização e distribuição por estado/município.
- **Análise Temporal** — série temporal, sazonalidade e comparação entre períodos.
- **Fatores de Risco** — causas, condições e perfis associados a acidentes graves/fatais.
- **Insights e Recomendações** — narrativa automática gerada a partir dos dados filtrados + exportações.
"""
)

with st.expander("ℹ️ Sobre o modelo de dados"):
    st.markdown(
        """
        - **fact_acidentes**: grão = 1 linha por acidente (fonte *Datatran*).
        - **fact_pessoas**: grão = 1 linha por pessoa/veículo envolvido (fonte *Acidentes*), ligada por `id`.
        - Cerca de **27%** dos acidentes não possuem coordenadas geográficas válidas na base oficial —
          os mapas consideram apenas os registros com latitude/longitude válidas dentro do território brasileiro.
        """
    )
