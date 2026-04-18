#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerarPDF.py
Recebe JSON de um informe e gera o PDF via reportlab.
Uso: python3 gerarPDF.py <dados.json> <saida.pdf>
"""

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

# Tentar registrar Tahoma (fallback para Helvetica se não existir)
try:
    pdfmetrics.registerFont(TTFont('Tahoma', 'Tahoma.ttf'))
    FONT_NAME = 'Tahoma'
except:
    FONT_NAME = 'Helvetica'

def fmt_brl(val):
    """Formata valor monetário brasileiro, retornando string com 2 casas decimais."""
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
    except Exception:
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
    styles.add(ParagraphStyle(name='Bold', parent=styles['Normal'], fontName=FONT_NAME, bold=True))
    styles.add(ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=8))

    story = []

    # Cabeçalho
    story.append(Paragraph('<b>MINISTÉRIO DA FAZENDA</b>', styles['Center']))
    story.append(Paragraph('<b>SECRETARIA DA RECEITA FEDERAL DO BRASIL</b>', styles['Center']))
    story.append(Paragraph('<b>IMPOSTO SOBRE A RENDA DA PESSOA FÍSICA</b>', styles['Center']))
    story.append(Spacer(1, 3*mm))

    data_periodo = [[
        Paragraph(f'<b>Exercício de {exercicio}</b>', styles['Left']),
        Paragraph(f'<b>Ano-Calendário {ano}</b>', styles['Right'])
    ]]
    t_periodo = Table(data_periodo, colWidths=[85*mm, 85*mm])
    t_periodo.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_periodo)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('<b>Comprovante de Rendimentos Pagos e de Imposto sobre a Renda Retido na Fonte</b>', styles['Center']))
    story.append(Spacer(1, 3*mm))

    def add_section(title, data, col_widths, header_style=None):
        story.append(Table([[title]], colWidths=[sum(col_widths)], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        t = Table(data, colWidths=col_widths)
        style = [
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]
        if header_style:
            style.extend(header_style)
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 2*mm))

    # Seção 1
    add_section(Paragraph('<b>1. FONTE PAGADORA PESSOA JURÍDICA OU PESSOA FÍSICA</b>', styles['Normal']),
                [[Paragraph('<b>Nome Empresarial/Nome Completo</b>', styles['Normal']), Paragraph('<b>CNPJ/CPF</b>', styles['Normal'])],
                 [fp.get('razaoSocial','') or ' ', fmt_cnpj(fp.get('cnpj','')) or ' ']],
                [120*mm, 50*mm],
                [('FONTNAME', (0,0), (-1,0), FONT_NAME), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE'))])

    # Seção 2
    add_section(Paragraph('<b>2. PESSOA FÍSICA BENEFICIÁRIA DOS RENDIMENTOS</b>', styles['Normal']),
                [[Paragraph('<b>CPF</b>', styles['Normal']), Paragraph('<b>Nome Completo</b>', styles['Normal'])],
                 [fmt_cpf(bn.get('cpf','')) or ' ', bn.get('nome','') or ' ']],
                [50*mm, 120*mm],
                [('FONTNAME', (0,0), (-1,0), FONT_NAME), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE'))])
    nat_table = Table([['Natureza do Rendimento: Assalariado']], colWidths=[170*mm])
    nat_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black),
                                   ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                                   ('FONTSIZE', (0,0), (-1,-1), 10)]))
    story.append(nat_table)
    story.append(Spacer(1, 2*mm))

    # Seção 3
    add_section(Paragraph('<b>3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO RETIDO NA FONTE</b>', styles['Normal']),
                [['01 - Total dos Rendimentos (inclusive Férias)', fmt_brl(rd.get('tributaveis'))],
                 ['02 - Contribuição Previdenciária Oficial', fmt_brl(rd.get('inss'))],
                 ['03 - Contrib. Previd. Complementar / FAPI', fmt_brl(rd.get('prevComplementar'))],
                 ['04 - Pensão Alimentícia', fmt_brl(rd.get('pensaoAlimenticia'))],
                 ['05 - Imposto sobre a renda retido na fonte', fmt_brl(rd.get('irrf'))]],
                [130*mm, 40*mm])

    # Seção 4
    add_section(Paragraph('<b>4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS</b>', styles['Normal']),
                [['01 - Parcela Isenta 65 anos ou mais', fmt_brl(rd.get('parcelaIsenta65'))],
                 ['02 - Diárias e Ajudas de Custo', fmt_brl(rd.get('diariasAjudas'))],
                 ['03 - Pensão/Aposent. Moléstia Grave ou Acidente', fmt_brl(rd.get('molestiaGrave'))],
                 ['04 - Lucros e Dividendos', fmt_brl(rd.get('lucrosDividendos'))],
                 ['05 - Pro-labore isento ME/EPP', fmt_brl(rd.get('prolaboreIsento'))],
                 ['06 - Indenizações por Rescisão/PDV', fmt_brl(rd.get('indenizacoes'))],
                 ['07 - Outros', fmt_brl(rd.get('outrosIsentos'))]],
                [130*mm, 40*mm])

    # Seção 5
    add_section(Paragraph('<b>5. RENDIMENTOS SUJEITOS À TRIBUTAÇÃO EXCLUSIVA</b>', styles['Normal']),
                [['01 - 13º Salário', fmt_brl(rd.get('trezeRendimentos'))],
                 ['02 - IRRF sobre 13º Salário', fmt_brl(rd.get('trezeIrrf'))],
                 ['03 - Outros', fmt_brl(rd.get('outrosTribExclusiva'))]],
                [130*mm, 40*mm])

    # Seção 6 - RRA (Rendimentos Recebidos Acumuladamente)
    # 1) Cabeçalho único ocupando 100% da largura
    titulo_secao6 = Table(
        [[Paragraph('<b>6. RENDIMENTOS RECEBIDOS ACUMULADAMENTE ART. 12-A DA LEI No. 7.713, DE 1988 (Sujeito à Tributação Exclusiva)</b>', styles['Normal'])]],
        colWidths=[170*mm]
    )
    titulo_secao6.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(titulo_secao6)

    # 2) Linha 6.1 com 3 colunas: "6.1 - Número do Processo:" | "Quantidade de meses" | "0"
    proc_val = rd.get('rraNumProcesso', '')
    meses_val = rd.get('rraMeses', '')
    linha_61 = Table(
        [[
            Paragraph('<b>6.1 - Número do Processo:</b>', styles['Left']),
            Paragraph(f'<b>Quantidade de meses:</b> {meses_val}', styles['Left']),
            '0'
        ]],
        colWidths=[70*mm, 60*mm, 40*mm]
    )
    linha_61.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(linha_61)

    # 3) Linha "Natureza do Rendimento:" (esquerda) | "Valores em Reais" (direita)
    linha_natureza = Table(
        [[
            Paragraph('<b>Natureza do Rendimento:</b>', styles['Left']),
            Paragraph('<b>Valores em Reais</b>', styles['Right'])
        ]],
        colWidths=[130*mm, 40*mm]
    )
    linha_natureza.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(linha_natureza)

    # 4) Tabela de itens com 2 colunas fixas (descrição à esquerda, valor à direita)
    itens_rra = [
        [
            Paragraph('01 - Total dos Rendimentos Tributáveis (inclusive Férias e Décimo Terceiro Salário)', styles['Left']),
            Paragraph(fmt_brl(rd.get('rraTributaveis')), styles['Right'])
        ],
        [
            Paragraph('02 - Exclusão: Despesas com a Ação Judicial', styles['Left']),
            Paragraph(fmt_brl(rd.get('rraDespesasJudiciais')), styles['Right'])
        ],
        [
            Paragraph('03 - Dedução: Contribuição Previdenciária Oficial', styles['Left']),
            Paragraph(fmt_brl(rd.get('rraInss')), styles['Right'])
        ],
        [
            Paragraph('04 - Dedução Pensão Alimentícia', styles['Left']),
            Paragraph(fmt_brl(rd.get('rraPensao')), styles['Right'])
        ],
        [
            Paragraph('05 - Imposto sobre a Renda Retido na Fonte', styles['Left']),
            Paragraph(fmt_brl(rd.get('rraIrrf')), styles['Right'])
        ],
        [
            Paragraph('06 - Rendimentos Isentos de Pensão, Proventos de Aposentadoria ou Reforma por Moléstia Grave ou Aposentadoria ou Reforma por Acidente em Serviço', styles['Left']),
            Paragraph(fmt_brl(rd.get('rraIsentos')), styles['Right'])
        ]
    ]
    tabela_itens = Table(itens_rra, colWidths=[130*mm, 40*mm])
    tabela_itens.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(tabela_itens)
    story.append(Spacer(1, 2*mm))

    # Seção 7
    story.append(Table([[Paragraph('<b>7. INFORMAÇÕES COMPLEMENTARES</b>', styles['Normal'])]], colWidths=[170*mm], style=[
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    info_table = Table([[Paragraph(info or 'Nada a declarar', styles['Normal'])]], colWidths=[170*mm])
    info_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 2*mm))

    # Seção 8
    add_section(Paragraph('<b>8. RESPONSÁVEL PELAS INFORMAÇÕES</b>', styles['Normal']),
                [Paragraph(['<b>Nome</b>', '<b>Data</b>', '<b>Assinatura</b>'], styles['Normal']),
                 [resp.get('nome', 'Não informado'),
                  resp.get('data', '  /  /    '),
                  Paragraph(resp.get('assinatura', 'Isento conforme IN RFB 1215/2011'), styles['Small'])]],
                [70*mm, 40*mm, 60*mm])

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('<i>Aprovado pela Instrução Normativa RFB nº 2.060, de 13 de dezembro de 2021.</i>', styles['Normal']))
    doc.build(story)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python3 gerarPDF.py <dados.json> <saida.pdf>")
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        dados = json.load(f)
    gerar_pdf(dados, sys.argv[2])
    print(f"✅ PDF gerado: {sys.argv[2]}")