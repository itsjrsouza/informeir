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
    exercicio = dados.get('exercicio', 2026)
    ano = dados.get('anoCalendario', exercicio - 1)
    fp = dados.get('fontePagadora', {})
    bn = dados.get('beneficiario', {})
    rd = dados.get('rendimentos', {})
    resp = dados.get('responsavel', {})
    info = dados.get('informacoesComplementares', '')

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           leftMargin=15*mm, rightMargin=15*mm,
                           topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    styles['Normal'].fontName = FONT_NAME
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 12

    styles.add(ParagraphStyle(name='Left', parent=styles['Normal'], alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='Right', parent=styles['Normal'], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER))

    story = []

    def add_section(title, data, col_widths, align_right=False):
        story.append(Table([[title]], colWidths=[sum(col_widths)], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))

        t = Table(data, colWidths=col_widths)

        style = [
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]

        if align_right:
            style.append(('ALIGN', (1,0), (1,-1), 'RIGHT'))

        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 2*mm))

    # Seção 3
    add_section('3. RENDIMENTOS TRIBUTÁVEIS',
        [['01 - Total', fmt_brl(rd.get('tributaveis'))],
         ['02 - INSS', fmt_brl(rd.get('inss'))]],
        [130*mm, 40*mm],
        align_right=True
    )

    # Seção 4
    add_section('4. ISENTOS',
        [['01 - Lucros', fmt_brl(rd.get('lucrosDividendos'))]],
        [130*mm, 40*mm],
        align_right=True
    )

    # Seção 5
    add_section('5. EXCLUSIVOS',
        [['01 - 13º', fmt_brl(rd.get('trezeRendimentos'))]],
        [130*mm, 40*mm],
        align_right=True
    )

    doc.build(story)

if __name__ == '__main__':
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        dados = json.load(f)
    gerar_pdf(dados, sys.argv[2])