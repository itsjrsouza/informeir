#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    pdfmetrics.registerFont(TTFont('Tahoma', 'Tahoma.ttf'))
    FONT_NAME = 'Tahoma'
except:
    FONT_NAME = 'Helvetica'

def fmt_brl(val):
    if val is None or str(val).strip() == "":
        return "0,00"
    s = str(val).strip().replace("R$", "").strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        f = float(s)
        inteiro, decimal = f"{f:.2f}".split('.')
        inteiro_fmt = ""
        for i, d in enumerate(reversed(inteiro)):
            if i > 0 and i % 3 == 0:
                inteiro_fmt = "." + inteiro_fmt
            inteiro_fmt = d + inteiro_fmt
        return f"{inteiro_fmt},{decimal}"
    except:
        return "0,00"

def fmt_cnpj(v):
    d = ''.join(c for c in str(v or '') if c.isdigit())
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}" if len(d) == 14 else v

def fmt_cpf(v):
    d = ''.join(c for c in str(v or '') if c.isdigit())
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else v

def gerar_pdf(dados, output_path):

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT, fontName=FONT_NAME, fontSize=10))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontName=FONT_NAME, fontSize=10))
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName=FONT_NAME, fontSize=10))
    styles.add(ParagraphStyle(name='Small', alignment=TA_LEFT, fontName=FONT_NAME, fontSize=8))

    def P(text, style='Left'):
        return Paragraph(text or " ", styles[style])

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=10*mm, bottomMargin=10*mm)

    story = []

    exercicio = dados.get('exercicio', 2026)
    ano = dados.get('anoCalendario', exercicio - 1)
    fp = dados.get('fontePagadora', {})
    bn = dados.get('beneficiario', {})
    rd = dados.get('rendimentos', {})
    resp = dados.get('responsavel', {})
    info = dados.get('informacoesComplementares', '')

    # Cabeçalho
    story.append(P('<b>MINISTÉRIO DA FAZENDA</b>', 'Center'))
    story.append(P('<b>SECRETARIA DA RECEITA FEDERAL DO BRASIL</b>', 'Center'))
    story.append(P('<b>IMPOSTO SOBRE A RENDA DA PESSOA FÍSICA</b>', 'Center'))

    story.append(Spacer(1, 5))

    story.append(Table([[
        P(f'<b>Exercício de {exercicio}</b>', 'Left'),
        P(f'<b>Ano-Calendário {ano}</b>', 'Right')
    ]], colWidths=[85*mm, 85*mm]))

    story.append(Spacer(1, 5))
    story.append(P('<b>Comprovante de Rendimentos Pagos e de Imposto sobre a Renda Retido na Fonte</b>', 'Center'))

    def add_section(title, rows, widths):
        story.append(Table([[P(title)]], colWidths=[sum(widths)], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))

        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 5))

    # Seção 1
    add_section(
        '<b>1. FONTE PAGADORA</b>',
        [
            [P('<b>Nome</b>'), P('<b>CNPJ</b>')],
            [P(fp.get('razaoSocial')), P(fmt_cnpj(fp.get('cnpj')))]
        ],
        [120*mm, 50*mm]
    )

    # Seção 2
    add_section(
        '<b>2. BENEFICIÁRIO</b>',
        [
            [P('<b>CPF</b>'), P('<b>Nome</b>')],
            [P(fmt_cpf(bn.get('cpf'))), P(bn.get('nome'))]
        ],
        [50*mm, 120*mm]
    )

    # Seção 3
    add_section(
        '<b>3. RENDIMENTOS TRIBUTÁVEIS</b>',
        [
            [P('01 - Rendimentos'), P(fmt_brl(rd.get('tributaveis')), 'Right')],
            [P('02 - INSS'), P(fmt_brl(rd.get('inss')), 'Right')],
            [P('03 - IRRF'), P(fmt_brl(rd.get('irrf')), 'Right')],
        ],
        [130*mm, 40*mm]
    )

    # Seção 6 (mantida padrão)
    add_section(
        '<b>6. RRA</b>',
        [
            [P('<b>Natureza</b>'), P('<b>Valor</b>', 'Right')],
            [P('Rendimentos'), P(fmt_brl(rd.get('rraTributaveis')), 'Right')],
        ],
        [130*mm, 40*mm]
    )

    # Seção 7
    add_section(
        '<b>7. INFORMAÇÕES COMPLEMENTARES</b>',
        [[P(info or 'Nada a declarar')]],
        [170*mm]
    )

    # Seção 8
    add_section(
        '<b>8. RESPONSÁVEL</b>',
        [
            [P('<b>Nome</b>'), P('<b>Data</b>'), P('<b>Assinatura</b>')],
            [
                P(resp.get('nome')),
                P(resp.get('data')),
                P(resp.get('assinatura'), 'Small')
            ]
        ],
        [70*mm, 40*mm, 60*mm]
    )

    doc.build(story)

if __name__ == '__main__':
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        dados = json.load(f)
    gerar_pdf(dados, sys.argv[2])