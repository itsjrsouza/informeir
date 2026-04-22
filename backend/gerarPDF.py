#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerarPDF.py v4
Recebe JSON de um informe e gera o PDF via reportlab.
Uso: python3 gerarPDF.py <dados.json> <saida.pdf>
"""

import sys, json
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

# ---------- CONFIGURAÇÕES DE LAYOUT (Figma) ----------
LARGURA_UTIL = 197.5*mm
LARGURA_VALORES = LARGURA_UTIL * (103 / (452+103))
LARGURA_DESCRICAO = LARGURA_UTIL - LARGURA_VALORES
LARGURA_NOME_EMPRESARIAL = LARGURA_UTIL * (556 / (556+428))
LARGURA_CNPJ_CPF = LARGURA_UTIL - LARGURA_NOME_EMPRESARIAL
LARGURA_PROCESSO = LARGURA_UTIL * (298 / (298+90+54))
LARGURA_MESES = LARGURA_UTIL * (90 / (298+90+54))
LARGURA_ZERO = LARGURA_UTIL - LARGURA_PROCESSO - LARGURA_MESES
LARGURA_NOME_RESP = LARGURA_UTIL * (230 / (230+96+231))
LARGURA_DATA = LARGURA_UTIL * (96 / (230+96+231))
LARGURA_ASSINATURA = LARGURA_UTIL - LARGURA_NOME_RESP - LARGURA_DATA
RECUO_ESQUERDO_TEXTO = 2*mm

def fmt_brl(val):
    if val is None or str(val).strip() == "": return "0,00"
    s = str(val).strip().replace("R$", "").strip()
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try:
        f = float(s)
        inteiro, decimal = f"{f:.2f}".split('.')
        inteiro_fmt = ""
        for i, d in enumerate(reversed(inteiro)):
            if i > 0 and i % 3 == 0: inteiro_fmt = "." + inteiro_fmt
            inteiro_fmt = d + inteiro_fmt
        return f"{inteiro_fmt},{decimal}"
    except: return "0,00"

def fmt_cnpj(v):
    d = ''.join(c for c in str(v or '') if c.isdigit())
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}" if len(d)==14 else v
def fmt_cpf(v):
    d = ''.join(c for c in str(v or '') if c.isdigit())
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d)==11 else v

def gerar_pdf(dados, output_path):
    exercicio = dados.get('exercicio', 2026)
    ano = dados.get('anoCalendario', exercicio - 1)
    fp = dados.get('fontePagadora', {})
    bn = dados.get('beneficiario', {})
    rd = dados.get('rendimentos', {})
    resp = dados.get('responsavel', {})
    info = dados.get('informacoesComplementares', '')
    natureza = dados.get('naturezaRendimento', 'Assalariado')
    natureza_rra = dados.get('naturezaRendimentoRRA', '')

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           leftMargin=5.0*mm, rightMargin=7.5*mm,
                           topMargin=0*mm, bottomMargin=4.9*mm)

    styles = getSampleStyleSheet()
    styles['Normal'].fontName = FONT_NAME
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 12
    styles.add(ParagraphStyle(name='Left', parent=styles['Normal'], alignment=TA_LEFT,
                              leftIndent=RECUO_ESQUERDO_TEXTO, rightIndent=RECUO_ESQUERDO_TEXTO))
    styles.add(ParagraphStyle(name='Right', parent=styles['Normal'], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Bold', parent=styles['Normal'], fontName=FONT_NAME, bold=True))
    styles.add(ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=8))

    story = []
    story.append(Paragraph('<b>MINISTÉRIO DA FAZENDA</b>', styles['Center']))
    story.append(Paragraph('<b>SECRETARIA DA RECEITA FEDERAL DO BRASIL</b>', styles['Center']))
    story.append(Paragraph('<b>IMPOSTO SOBRE A RENDA DA PESSOA FÍSICA</b>', styles['Center']))
    story.append(Spacer(1, 3*mm))
    data_periodo = [[Paragraph(f'<b>Exercício de {exercicio}</b>', styles['Left']),
                     Paragraph(f'<b>Ano-Calendário {ano}</b>', styles['Right'])]]
    t_periodo = Table(data_periodo, colWidths=[LARGURA_UTIL/2, LARGURA_UTIL/2])
    t_periodo.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_periodo)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('<b>Comprovante de Rendimentos Pagos e de Imposto sobre a Renda Retido na Fonte</b>', styles['Center']))
    story.append(Spacer(1, 3*mm))

    def add_section(title, data, col_widths, header_style=None):
        story.append(Table([[title]], colWidths=[sum(col_widths)], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey), ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
        t = Table(data, colWidths=col_widths)
        style = [('FONTNAME', (0,0), (-1,-1), FONT_NAME), ('FONTSIZE', (0,0), (-1,-1), 10),
                 ('GRID', (0,0), (-1,-1), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                 ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
                 ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3)]
        if header_style: style.extend(header_style)
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 2*mm))

    # Seção 1
    add_section(Paragraph('<b>1. FONTE PAGADORA PESSOA JURÍDICA OU PESSOA FÍSICA</b>', styles['Normal']),
                [[Paragraph('<b>Nome Empresarial/Nome Completo</b>', styles['Normal']), Paragraph('<b>CNPJ/CPF</b>', styles['Normal'])],
                 [fp.get('razaoSocial','') or ' ', fmt_cnpj(fp.get('cnpj','')) or ' ']],
                [LARGURA_NOME_EMPRESARIAL, LARGURA_CNPJ_CPF],
                [('FONTNAME', (0,0), (-1,0), FONT_NAME), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE'))])
    # Seção 2
    add_section(Paragraph('<b>2. PESSOA FÍSICA BENEFICIÁRIA DOS RENDIMENTOS</b>', styles['Normal']),
                [[Paragraph('<b>CPF</b>', styles['Normal']), Paragraph('<b>Nome Completo</b>', styles['Normal'])],
                 [fmt_cpf(bn.get('cpf','')) or ' ', bn.get('nome','') or ' ']],
                [LARGURA_CNPJ_CPF, LARGURA_NOME_EMPRESARIAL],
                [('FONTNAME', (0,0), (-1,0), FONT_NAME), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE'))])
    nat_table = Table([[f'Natureza do Rendimento: {natureza}']], colWidths=[LARGURA_UTIL])
    nat_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black),
                                   ('FONTNAME', (0,0), (-1,-1), FONT_NAME), ('FONTSIZE', (0,0), (-1,-1), 10)]))
    story.append(nat_table)
    story.append(Spacer(1, 2*mm))

    # Seção 3
    add_section(Paragraph('<b>3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO RETIDO NA FONTE</b>', styles['Normal']),
                [[Paragraph('01 - Total dos Rendimentos (inclusive Férias)', styles['Left']), Paragraph(fmt_brl(rd.get('tributaveis')), styles['Right'])],
                 [Paragraph('02 - Contribuição Previdenciária Oficial', styles['Left']), Paragraph(fmt_brl(rd.get('inss')), styles['Right'])],
                 [Paragraph('03 - Contrib. Previd. Complementar / FAPI', styles['Left']), Paragraph(fmt_brl(rd.get('prevComplementar')), styles['Right'])],
                 [Paragraph('04 - Pensão Alimentícia', styles['Left']), Paragraph(fmt_brl(rd.get('pensaoAlimenticia')), styles['Right'])],
                 [Paragraph('05 - Imposto sobre a renda retido na fonte', styles['Left']), Paragraph(fmt_brl(rd.get('irrf')), styles['Right'])]],
                [LARGURA_DESCRICAO, LARGURA_VALORES])

    # Seção 4
    add_section(Paragraph('<b>4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS</b>', styles['Normal']),
                [[Paragraph('01 - Parcela Isenta dos Proventos de Aposentadoria, Reserva Remunerada, Reforma e Pensão (65 anos ou mais)', styles['Left']), Paragraph(fmt_brl(rd.get('parcelaIsenta65')), styles['Right'])],
                 [Paragraph('02 - Parcela Isenta do 13º de Aposentadoria, Reserva Remunerada, Reforma e Pensão (65 anos ou mais)', styles['Left']), Paragraph(fmt_brl(rd.get('parcelaIsenta13')), styles['Right'])],
                 [Paragraph('03 - Diárias e Ajudas de Custo', styles['Left']), Paragraph(fmt_brl(rd.get('diariasAjudas')), styles['Right'])],
                 [Paragraph('04 - Pensão, Prov.de Aposentadoria ou Reforma por Moléstia Grave e aposentadoria ou Reforma por Acidente em Serviço', styles['Left']), Paragraph(fmt_brl(rd.get('molestiaGrave')), styles['Right'])],
                 [Paragraph('05 - Lucro e Dividendo Apurado a partir de 1996 pago por PJ (Lucro Real, Presumido ou Arbitrado)', styles['Left']), Paragraph(fmt_brl(rd.get('lucrosDividendos')), styles['Right'])],
                 [Paragraph('06 - Vlr. Pago ao Titular ou Sócio da Microempresa ou Empr.de Pequeno Porte, exceto Pro-labore, aluguéis ou Serv.Prest.', styles['Left']), Paragraph(fmt_brl(rd.get('prolaboreIsento')), styles['Right'])],
                 [Paragraph('07 - Indenizações por Rescisão de Contrato de Trabalho, inclusive a título de PDV e por Acidente de Trabalho', styles['Left']), Paragraph(fmt_brl(rd.get('indenizacoes')), styles['Right'])],
                 [Paragraph('08 - Outros', styles['Left']), Paragraph(fmt_brl(rd.get('outrosIsentos')), styles['Right'])]],
                [LARGURA_DESCRICAO, LARGURA_VALORES])

    # Seção 5
    add_section(Paragraph('<b>5. RENDIMENTOS SUJEITOS À TRIBUTAÇÃO EXCLUSIVA</b>', styles['Normal']),
                [[Paragraph('01 - 13º Salário', styles['Left']), Paragraph(fmt_brl(rd.get('trezeRendimentos')), styles['Right'])],
                 [Paragraph('02 - IRRF sobre 13º Salário', styles['Left']), Paragraph(fmt_brl(rd.get('trezeIrrf')), styles['Right'])],
                 [Paragraph('03 - Outros', styles['Left']), Paragraph(fmt_brl(rd.get('outrosTribExclusiva')), styles['Right'])]],
                [LARGURA_DESCRICAO, LARGURA_VALORES])

    # Seção 6
    titulo_secao6 = Table([[Paragraph('<b>6. RENDIMENTOS RECEBIDOS ACUMULADAMENTE ART. 12-A DA LEI No. 7.713, DE 1988 (Sujeito à Tributação Exclusiva)</b>', styles['Normal'])]], colWidths=[LARGURA_UTIL])
    titulo_secao6.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.lightgrey), ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                                       ('FONTNAME', (0,0), (-1,-1), FONT_NAME), ('FONTSIZE', (0,0), (-1,-1), 10),
                                       ('LEFTPADDING', (0,0), (-1,-1), 3), ('TOPPADDING', (0,0), (-1,-1), 2),
                                       ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    story.append(titulo_secao6)

    linha_61 = Table([[
        Paragraph('<b>6.1 - Número do Processo:</b>', styles['Left']),
        Paragraph(f'<b>Quantidade de meses:</b> {rd.get("rraMeses","")}', styles['Left']),
        '0'
    ]], colWidths=[LARGURA_PROCESSO, LARGURA_MESES, LARGURA_ZERO])
    linha_61.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                                  ('FONTSIZE', (0,0), (-1,-1), 10), ('ALIGN', (2,0), (2,0), 'CENTER'),
                                  ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 4),
                                  ('RIGHTPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 3),
                                  ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
    story.append(linha_61)

    linha_natureza = Table([[
        Paragraph(f'<b>Natureza do Rendimento:</b> {natureza_rra}', styles['Left']),
        Paragraph('<b>Valores em Reais</b>', styles['Right'])
    ]], colWidths=[LARGURA_DESCRICAO, LARGURA_VALORES])
    linha_natureza.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                                        ('FONTSIZE', (0,0), (-1,-1), 10), ('ALIGN', (1,0), (1,0), 'RIGHT'),
                                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 4),
                                        ('RIGHTPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 3),
                                        ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
    story.append(linha_natureza)

    itens_rra = [
        [Paragraph('01 - Total dos Rendimentos Tributáveis (inclusive Férias e Décimo Terceiro Salário)', styles['Left']), Paragraph(fmt_brl(rd.get('rraTributaveis')), styles['Right'])],
        [Paragraph('02 - Exclusão: Despesas com a Ação Judicial', styles['Left']), Paragraph(fmt_brl(rd.get('rraDespesasJudiciais')), styles['Right'])],
        [Paragraph('03 - Dedução: Contribuição Previdenciária Oficial', styles['Left']), Paragraph(fmt_brl(rd.get('rraInss')), styles['Right'])],
        [Paragraph('04 - Dedução Pensão Alimentícia', styles['Left']), Paragraph(fmt_brl(rd.get('rraPensao')), styles['Right'])],
        [Paragraph('05 - Imposto sobre a Renda Retido na Fonte', styles['Left']), Paragraph(fmt_brl(rd.get('rraIrrf')), styles['Right'])],
        [Paragraph('06 - Rendimentos Isentos de Pensão, Proventos de Aposentadoria ou Reforma por Moléstia Grave ou Aposentadoria ou Reforma por Acidente em Serviço', styles['Left']), Paragraph(fmt_brl(rd.get('rraIsentos')), styles['Right'])]
    ]
    tabela_itens = Table(itens_rra, colWidths=[LARGURA_DESCRICAO, LARGURA_VALORES])
    tabela_itens.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                                      ('FONTSIZE', (0,0), (-1,-1), 10), ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                                      ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 4),
                                      ('RIGHTPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 3),
                                      ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
    story.append(tabela_itens)
    story.append(Spacer(1, 2*mm))

    # Seção 7
    story.append(Table([[Paragraph('<b>7. INFORMAÇÕES COMPLEMENTARES</b>', styles['Normal'])]], colWidths=[LARGURA_UTIL], style=[
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey), ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    info_table = Table([[Paragraph(info or 'Nada a declarar', styles['Normal'])]], colWidths=[LARGURA_UTIL])
    info_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                                    ('FONTSIZE', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 4),
                                    ('RIGHTPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 3),
                                    ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
    story.append(info_table)
    story.append(Spacer(1, 2*mm))

    # Seção 8
    add_section(Paragraph('<b>8. RESPONSÁVEL PELAS INFORMAÇÕES</b>', styles['Normal']),
                [[Paragraph('<b>Nome</b>', styles['Normal']),
                  Paragraph('<b>Data</b>', styles['Normal']),
                  Paragraph('<b>Assinatura</b>', styles['Normal'])],
                 [resp.get('nome', 'Não informado'),
                  resp.get('data', '  /  /    '),
                  Paragraph(resp.get('assinatura', 'Isento conforme IN RFB 1.215/2011'), styles['Small'])]],
                [LARGURA_NOME_RESP, LARGURA_DATA, LARGURA_ASSINATURA])

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