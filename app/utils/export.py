"""Geração de exportações (Excel / PDF) a partir dos dados filtrados."""
import io

import pandas as pd


def to_excel_bytes(df: pd.DataFrame, sheet_name="Acidentes") -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()


def kpis_to_pdf_bytes(titulo, kpis: dict, insights: list) -> bytes:
    """Gera um PDF resumido com KPIs e insights (relatório executivo rápido)."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, titulo, ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "Relatorio gerado pelo Dashboard de Acidentes de Transito (PRF)", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Indicadores-chave", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for label, valor in kpis.items():
        texto = f"{label}: {valor}"
        pdf.cell(0, 8, texto.encode("latin-1", "replace").decode("latin-1"), ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Insights Automaticos", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for item in insights:
        texto = item["texto"].replace("**", "")
        texto = texto.encode("latin-1", "replace").decode("latin-1")
        pdf.set_x(pdf.l_margin)  # multi_cell(w=0) deixa o cursor na margem direita; reposiciona antes da próxima linha
        pdf.multi_cell(0, 7, f"- {texto}")
    return bytes(pdf.output(dest="S"))
