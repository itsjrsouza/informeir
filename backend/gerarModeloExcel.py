#!/usr/bin/env python3
"""
gerarModeloExcel.py
Gera o arquivo modelo.xlsx que o usuário vai preencher com os sócios.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sys

COLUNAS = [
    ("ANO_CALENDARIO",      "Ano-Calendário",                          10),
    ("CNPJ_EMPRESA",        "CNPJ da Empresa",                         20),
    ("RAZAO_SOCIAL",        "Razão Social / Nome Empresarial",          35),
    ("NOME_SOCIO",          "Nome Completo do Sócio/Beneficiário",      35),
    ("CPF_SOCIO",           "CPF do Sócio",                            16),
    ("TRIBUTAVEIS",         "Rendimentos Tributáveis (R$)",             22),
    ("INSS",                "Contribuição INSS (R$)",                   20),
    ("OUTRAS_DEDUCOES",     "Outras Deduções (R$)",                     20),
    ("IRRF",                "IRRF (R$)",                                16),
    ("LUCROS_DIVIDENDOS",   "Lucros e Dividendos (R$)",                 22),
    ("OUTROS_ISENTOS",      "Outros Rendimentos Isentos (R$)",          26),
    ("PLANO_BENEFICIARIO",  "Plano Saúde - Beneficiário (R$)",          26),
    ("PLANO_FONTE",         "Plano Saúde - Empresa (R$)",               24),
    ("TREZE_RENDIMENTOS",   "13° Salário - Tributáveis (R$)",           26),
    ("TREZE_INSS",          "13° Salário - INSS (R$)",                  22),
    ("TREZE_IRRF",          "13° Salário - IRRF (R$)",                  22),
]

EXEMPLOS = [
    [2025, "12.345.678/0001-95", "EMPRESA ALPHA LTDA",
     "JOÃO DA SILVA SOUZA", "123.456.789-01",
     84000.00, 7786.00, 0.00, 4200.00, 120000.00, 0.00, 0.00, 3600.00, 7000.00, 648.83, 0.00],
    [2025, "98.765.432/0001-10", "BETA CONSULTORIA S/A",
     "MARIA OLIVEIRA SANTOS", "987.654.321-00",
     60000.00, 6600.00, 0.00, 1800.00, 80000.00, 0.00, 1200.00, 0.00, 5000.00, 550.00, 0.00],
]

AZUL_ESCURO  = "1F3864"
AZUL_HEADER  = "2563A8"
AZUL_CLARO   = "D9E1F2"
VERDE_EX     = "E2EFDA"
BRANCO       = "FFFFFF"
CINZA        = "F5F5F5"

def borda(cor="CCCCCC"):
    s = Side(style="thin", color=cor)
    return Border(left=s, right=s, top=s, bottom=s)

def gerar(output_path):
    wb = Workbook()

    # ── Aba MODELO ────────────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "MODELO"

    # Título principal
    ws.merge_cells("A1:P1")
    t = ws["A1"]
    t.value = "IMPORTAÇÃO EM LOTE — INFORME DE RENDIMENTOS"
    t.font = Font(name="Arial", bold=True, size=14, color=BRANCO)
    t.fill = PatternFill("solid", fgColor=AZUL_ESCURO)
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # Subtítulo
    ws.merge_cells("A2:P2")
    s = ws["A2"]
    s.value = (
        "Preencha uma linha por sócio. "
        "Não altere os nomes das colunas. "
        "Responsável fixo: NELSON FERNANDES DE SOUZA JUNIOR — 28.02.2026"
    )
    s.font = Font(name="Arial", italic=True, size=10, color="444444")
    s.fill = PatternFill("solid", fgColor=AZUL_CLARO)
    s.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18

    # Cabeçalhos (linha 3)
    for col_idx, (campo, label, largura) in enumerate(COLUNAS, start=1):
        col_letra = get_column_letter(col_idx)
        c = ws.cell(row=3, column=col_idx)
        c.value = campo
        c.font = Font(name="Arial", bold=True, size=10, color=BRANCO)
        c.fill = PatternFill("solid", fgColor=AZUL_HEADER)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = borda("1F3864")
        ws.column_dimensions[col_letra].width = largura

        # Linha 4: label amigável
        l = ws.cell(row=4, column=col_idx)
        l.value = label
        l.font = Font(name="Arial", italic=True, size=9, color="1F3864")
        l.fill = PatternFill("solid", fgColor=AZUL_CLARO)
        l.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        l.border = borda()

    ws.row_dimensions[3].height = 22
    ws.row_dimensions[4].height = 36

    # Exemplos (linhas 5 e 6)
    for row_idx, exemplo in enumerate(EXEMPLOS, start=5):
        for col_idx, valor in enumerate(exemplo, start=1):
            c = ws.cell(row=row_idx, column=col_idx)
            c.value = valor
            c.font = Font(name="Arial", size=10, color="1a5276")
            c.fill = PatternFill("solid", fgColor=VERDE_EX)
            c.border = borda()
            c.alignment = Alignment(horizontal="center", vertical="center")
            # Formatar números monetários
            if col_idx >= 6:
                c.number_format = '#.##0,00'
        ws.row_dimensions[row_idx].height = 18

    # Linhas em branco para preenchimento (7 a 106 — até 100 sócios)
    for row_idx in range(7, 107):
        for col_idx in range(1, len(COLUNAS) + 1):
            c = ws.cell(row=row_idx, column=col_idx)
            c.border = borda()
            c.fill = PatternFill("solid", fgColor=BRANCO if row_idx % 2 == 0 else CINZA)
            c.alignment = Alignment(horizontal="center", vertical="center")
            if col_idx >= 6:
                c.number_format = '#.##0,00'
        ws.row_dimensions[row_idx].height = 18

    # Congela cabeçalho
    ws.freeze_panes = "A5"

    # ── Aba INSTRUÇÕES ────────────────────────────────────────────────────────
    wi = wb.create_sheet("INSTRUÇÕES")
    instrucoes = [
        ("INSTRUÇÕES DE PREENCHIMENTO", True, 14, AZUL_ESCURO, BRANCO),
        ("", False, 10, BRANCO, "000000"),
        ("CAMPO",              True,  11, AZUL_HEADER, BRANCO),
        ("ANO_CALENDARIO",     False, 10, AZUL_CLARO,  "000000"),
        ("CNPJ_EMPRESA",       False, 10, BRANCO,      "000000"),
        ("RAZAO_SOCIAL",       False, 10, AZUL_CLARO,  "000000"),
        ("NOME_SOCIO",         False, 10, BRANCO,      "000000"),
        ("CPF_SOCIO",          False, 10, AZUL_CLARO,  "000000"),
        ("TRIBUTAVEIS",        False, 10, BRANCO,      "000000"),
        ("INSS",               False, 10, AZUL_CLARO,  "000000"),
        ("OUTRAS_DEDUCOES",    False, 10, BRANCO,      "000000"),
        ("IRRF",               False, 10, AZUL_CLARO,  "000000"),
        ("LUCROS_DIVIDENDOS",  False, 10, BRANCO,      "000000"),
        ("OUTROS_ISENTOS",     False, 10, AZUL_CLARO,  "000000"),
        ("PLANO_BENEFICIARIO", False, 10, BRANCO,      "000000"),
        ("PLANO_FONTE",        False, 10, AZUL_CLARO,  "000000"),
        ("TREZE_RENDIMENTOS",  False, 10, BRANCO,      "000000"),
        ("TREZE_INSS",         False, 10, AZUL_CLARO,  "000000"),
        ("TREZE_IRRF",         False, 10, BRANCO,      "000000"),
    ]

    descricoes = {
        "CAMPO":              "DESCRIÇÃO / EXEMPLO",
        "ANO_CALENDARIO":     "Ano de referência. Ex: 2025",
        "CNPJ_EMPRESA":       "CNPJ com ou sem máscara. Ex: 12.345.678/0001-95 ou 12345678000195",
        "RAZAO_SOCIAL":       "Nome completo da empresa. Ex: EMPRESA ALPHA LTDA",
        "NOME_SOCIO":         "Nome completo do sócio/beneficiário em maiúsculas",
        "CPF_SOCIO":          "CPF com ou sem máscara. Ex: 123.456.789-01 ou 12345678901",
        "TRIBUTAVEIS":        "Rendimentos tributáveis (pró-labore, salário). Use ponto ou vírgula decimal. Ex: 84000,00",
        "INSS":               "Contribuição Previdenciária descontada. Ex: 7786,00",
        "OUTRAS_DEDUCOES":    "Outras deduções legais. Deixe 0 se não houver.",
        "IRRF":               "Imposto de Renda Retido na Fonte. Ex: 4200,00",
        "LUCROS_DIVIDENDOS":  "Lucros e dividendos distribuídos (rendimento isento). Ex: 120000,00",
        "OUTROS_ISENTOS":     "Outros rendimentos isentos não tributáveis. Deixe 0 se não houver.",
        "PLANO_BENEFICIARIO": "Valor do plano de saúde pago pelo sócio. Deixe 0 se não houver.",
        "PLANO_FONTE":        "Valor do plano de saúde custeado pela empresa. Deixe 0 se não houver.",
        "TREZE_RENDIMENTOS":  "Rendimentos tributáveis do 13° salário. Deixe 0 se não aplicável.",
        "TREZE_INSS":         "INSS descontado sobre o 13° salário.",
        "TREZE_IRRF":         "IRRF sobre o 13° salário.",
    }

    wi.column_dimensions["A"].width = 22
    wi.column_dimensions["B"].width = 60

    for row_idx, (campo, bold, size, bg, fg) in enumerate(instrucoes, start=1):
        ca = wi.cell(row=row_idx, column=1, value=campo)
        cb = wi.cell(row=row_idx, column=2, value=descricoes.get(campo, ""))
        for c in (ca, cb):
            c.font = Font(name="Arial", bold=bold, size=size, color=fg)
            c.fill = PatternFill("solid", fgColor=bg)
            c.border = borda()
            c.alignment = Alignment(vertical="center", wrap_text=True)
        wi.row_dimensions[row_idx].height = 22 if bold else 18

    wb.save(output_path)
    print(f"✅ Modelo Excel gerado: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/informe-rendimentos/modelo_importacao.xlsx"
    gerar(out)
