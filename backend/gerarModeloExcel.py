#!/usr/bin/env python3
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sys

COLUNAS = [
    ("EXERCICIO",           "Exercício (ano de entrega)",           12),
    ("ANO_CALENDARIO",      "Ano-Calendário",                       12),
    ("CNPJ_EMPRESA",        "CNPJ da Empresa",                      20),
    ("RAZAO_SOCIAL",        "Razão Social / Nome Empresarial",       35),
    ("NOME_SOCIO",          "Nome Completo do Beneficiário",         35),
    ("CPF_SOCIO",           "CPF do Beneficiário",                  16),
    ("TRIBUTAVEIS",         "Rendimentos Tributáveis (R$)",          22),
    ("INSS",                "Contribuição INSS (R$)",                20),
    ("OUTRAS_DEDUCOES",     "Pensão Alimentícia/Outras Deduções (R$)",20),
    ("IRRF",                "IRRF (R$)",                             16),
    ("LUCROS_DIVIDENDOS",   "Lucros e Dividendos (R$)",              22),
    ("OUTROS_ISENTOS",      "Outros Rendimentos Isentos (R$)",       26),
    ("TREZE_RENDIMENTOS",   "13º Salário (R$)",                      20),
    ("TREZE_IRRF",          "IRRF sobre 13º (R$)",                   20),
]

EXEMPLOS = [
    [2026, 2025, "12.345.678/0001-95", "EMPRESA ALPHA LTDA", "JOÃO DA SILVA SOUZA", "123.456.789-01", 84000.00, 7786.00, 0.00, 4200.00, 120000.00, 0.00, 7000.00, 0.00],
    [2026, 2025, "98.765.432/0001-10", "BETA CONSULTORIA S/A", "MARIA OLIVEIRA SANTOS", "987.654.321-00", 60000.00, 6600.00, 0.00, 1800.00, 80000.00, 0.00, 5000.00, 0.00],
]

AZUL_ESCURO, AZUL_HEADER, AZUL_CLARO, VERDE_EX, BRANCO, CINZA = "1F3864", "2563A8", "D9E1F2", "E2EFDA", "FFFFFF", "F5F5F5"
def borda(cor="CCCCCC"): s=Side(style="thin", color=cor); return Border(left=s, right=s, top=s, bottom=s)

def gerar(output_path):
    wb = Workbook()
    ws = wb.active; ws.title = "MODELO"
    ws.merge_cells("A1:N1"); ws["A1"].value = "IMPORTAÇÃO EM LOTE — INFORME DE RENDIMENTOS"; ws["A1"].font = Font(bold=True, size=14, color=BRANCO); ws["A1"].fill = PatternFill("solid", fgColor=AZUL_ESCURO); ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30
    ws.merge_cells("A2:N2"); ws["A2"].value = "Preencha uma linha por sócio. Não altere os nomes das colunas. Responsável deve ser informado no momento da geração."
    ws["A2"].font = Font(italic=True, size=10, color="444444"); ws["A2"].fill = PatternFill("solid", fgColor=AZUL_CLARO); ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18

    for col_idx, (campo, label, largura) in enumerate(COLUNAS, start=1):
        col_letra = get_column_letter(col_idx)
        c = ws.cell(row=3, column=col_idx, value=campo); c.font = Font(bold=True, size=10, color=BRANCO); c.fill = PatternFill("solid", fgColor=AZUL_HEADER); c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = borda("1F3864")
        ws.column_dimensions[col_letra].width = largura
        l = ws.cell(row=4, column=col_idx, value=label); l.font = Font(italic=True, size=9, color="1F3864"); l.fill = PatternFill("solid", fgColor=AZUL_CLARO); l.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); l.border = borda()
    ws.row_dimensions[3].height = 22; ws.row_dimensions[4].height = 36

    for row_idx, exemplo in enumerate(EXEMPLOS, start=5):
        for col_idx, valor in enumerate(exemplo, start=1):
            c = ws.cell(row=row_idx, column=col_idx, value=valor); c.font = Font(size=10, color="1a5276"); c.fill = PatternFill("solid", fgColor=VERDE_EX); c.border = borda(); c.alignment = Alignment(horizontal="center", vertical="center")
            if col_idx >= 7: c.number_format = '#.##0,00'
        ws.row_dimensions[row_idx].height = 18

    for row_idx in range(7, 107):
        for col_idx in range(1, len(COLUNAS)+1):
            c = ws.cell(row=row_idx, column=col_idx); c.border = borda(); c.fill = PatternFill("solid", fgColor=BRANCO if row_idx % 2 == 0 else CINZA); c.alignment = Alignment(horizontal="center", vertical="center")
            if col_idx >= 7: c.number_format = '#.##0,00'
        ws.row_dimensions[row_idx].height = 18

    ws.freeze_panes = "A5"
    wb.save(output_path)
    print(f"✅ Modelo Excel gerado: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "modelo.xlsx"
    gerar(out)