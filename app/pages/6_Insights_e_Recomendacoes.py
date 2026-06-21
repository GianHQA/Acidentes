"""Insights e Recomendações — narrativa automática + exportação de relatórios."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from utils.data_loader import load_data
from utils.export import kpis_to_pdf_bytes, to_excel_bytes
from utils.filters import apply_filters, render_sidebar_filters
from utils.insights import generate_insights
from utils.style import inject_css

st.set_page_config(page_title="Insights e Recomendações", page_icon="💡", layout="wide")
inject_css()

fact_acidentes, fact_pessoas, dim_uf = load_data()
selections = render_sidebar_filters(fact_acidentes, dim_uf)
df = apply_filters(fact_acidentes, selections)

st.title("💡 Insights e Recomendações")
st.caption("Narrativa gerada automaticamente a partir do recorte de dados atualmente filtrado.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

st.markdown("### 🧠 Insights Automáticos")
insights = generate_insights(df, dim_uf)
for item in insights:
    st.markdown(f"<div class='insight-card {item['tipo']}'>📌 {item['texto']}</div>", unsafe_allow_html=True)

st.divider()
st.markdown("### ✅ Recomendações Acionáveis")
st.markdown(
    """
- **Fiscalização e blitz educativas** nos horários e dias da semana com maior concentração de acidentes
  graves (ver insight de horário/dia crítico acima) — reforço de policiamento e radares móveis.
- **Engenharia viária prioritária** nos trechos/BRs com maior taxa de fatalidade e nos traçados
  identificados como mais críticos (curvas, interseções) na página *Fatores de Risco*.
- **Campanhas direcionadas por causa raiz**: a principal causa de acidentes fatais no recorte deve
  orientar campanhas específicas (ex.: combate à embriaguez ao volante, fadiga, distância segura).
- **Atenção redobrada em condições climáticas adversas** com maior taxa de mortalidade observada
  (sinalização, limites de velocidade dinâmicos, alertas).
- **Monitoramento contínuo da tendência**: se a tendência apurada for de aumento, recomenda-se
  reavaliação trimestral das ações de segurança viária nas regiões mais críticas do ranking executivo.
- **Investimento proporcional ao risco**: priorizar UFs/municípios no topo do ranking de óbitos
  (Visão Executiva) para alocação de recursos de fiscalização e infraestrutura.
"""
)

st.divider()
st.markdown("### 📤 Exportar Relatório")
col1, col2 = st.columns(2)

with col1:
    st.download_button(
        "⬇️ Exportar dados filtrados (Excel)",
        data=to_excel_bytes(df.drop(columns=["arquivo_origem"], errors="ignore")),
        file_name="acidentes_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with col2:
    kpis = {
        "Total de Acidentes": f"{len(df):,}".replace(",", "."),
        "Total de Obitos": int(df["mortos"].sum()),
        "Taxa de Mortalidade": f"{round(100 * df['mortos'].sum() / df['pessoas'].sum(), 2) if df['pessoas'].sum() else 0}%",
        "Estados no recorte": df["uf"].nunique(),
        "Periodo": f"{int(df['ano'].min())}-{int(df['ano'].max())}",
    }
    st.download_button(
        "⬇️ Exportar relatório executivo (PDF)",
        data=kpis_to_pdf_bytes("Relatorio Executivo - Acidentes de Transito", kpis, insights),
        file_name="relatorio_executivo.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

st.caption("💡 Dica: para capturas de tela de gráficos individuais, use o ícone de câmera no canto "
           "superior direito de cada gráfico Plotly (gerado automaticamente em todas as páginas).")
