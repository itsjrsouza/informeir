#!/usr/bin/env python3
import sys, json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

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

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Left', parent=styles['Normal'], alignment=TA_LEFT, fontSize=10))
    styles.add(ParagraphStyle(name='Right', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=10))
    styles.add(ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10))
    styles.add(ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=8))

    story = []

    story.append(Paragraph('<b>MINISTÉRIO DA FAZENDA</b>', styles['Center']))
    story.append(Paragraph('<b>SECRETARIA DA RECEITA FEDERAL DO BRASIL</b>', styles['Center']))
    story.append(Paragraph('<b>IMPOSTO SOBRE A RENDA DA PESSOA FÍSICA</b>', styles['Center']))
    story.append(Spacer(1, 5*mm))

    data_periodo = [[
        Paragraph(f'<b>Exercício de {exercicio}</b>', styles['Left']),
        Paragraph(f'<b>Ano-Calendário {ano}</b>', styles['Right'])
    ]]
    t_periodo = Table(data_periodo, colWidths=[85*mm, 85*mm])
    t_periodo.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_periodo)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('<b>Comprovante de Rendimentos Pagos e de Imposto sobre a Renda Retido na Fonte</b>', styles['Center']))
    story.append(Spacer(1, 5*mm))

    def add_section(title, data, col_widths, header_style=None):
        story.append(Table([[title]], colWidths=[sum(col_widths)], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        t = Table(data, colWidths=col_widths)
        style = [
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]
        if header_style:
            style.extend(header_style)
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 4*mm))

    # Seção 1
    add_section('1. FONTE PAGADORA PESSOA JURÍDICA OU PESSOA FÍSICA',
                [['Nome Empresarial/Nome Completo', 'CNPJ/CPF'],
                 [fp.get('razaoSocial',''), fmt_cnpj(fp.get('cnpj',''))]],
                [120*mm, 50*mm],
                [('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE'))])

    # Seção 2
    add_section('2. PESSOA FÍSICA BENEFICIÁRIA DOS RENDIMENTOS',
                [['CPF', 'Nome Completo'],
                 [fmt_cpf(bn.get('cpf','')), bn.get('nome','')]],
                [50*mm, 120*mm],
                [('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE'))])
    nat_table = Table([['Natureza do Rendimento: Assalariado']], colWidths=[170*mm])
    nat_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(nat_table)
    story.append(Spacer(1, 4*mm))

    # Seção 3
    add_section('3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO RETIDO NA FONTE',
                [['01 - Total dos Rendimentos (inclusive Férias)', fmt_brl(rd.get('tributaveis'))],
                 ['02 - Contribuição Previdenciária Oficial', fmt_brl(rd.get('inss'))],
                 ['03 - Contrib. Previd. Complementar / FAPI', fmt_brl(rd.get('prevComplementar'))],
                 ['04 - Pensão Alimentícia', fmt_brl(rd.get('pensaoAlimenticia'))],
                 ['05 - Imposto sobre a renda retido na fonte', fmt_brl(rd.get('irrf'))]],
                [130*mm, 40*mm])

    # Seção 4
    add_section('4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS',
                [['01 - Parcela Isenta 65 anos ou mais', fmt_brl(rd.get('parcelaIsenta65'))],
                 ['02 - Diárias e Ajudas de Custo', fmt_brl(rd.get('diariasAjudas'))],
                 ['03 - Pensão/Aposent. Moléstia Grave ou Acidente', fmt_brl(rd.get('molestiaGrave'))],
                 ['04 - Lucros e Dividendos', fmt_brl(rd.get('lucrosDividendos'))],
                 ['05 - Pro-labore isento ME/EPP', fmt_brl(rd.get('prolaboreIsento'))],
                 ['06 - Indenizações por Rescisão/PDV', fmt_brl(rd.get('indenizacoes'))],
                 ['07 - Outros', fmt_brl(rd.get('outrosIsentos'))]],
                [130*mm, 40*mm])

    # Seção 5
    add_section('5. RENDIMENTOS SUJEITOS À TRIBUTAÇÃO EXCLUSIVA',
                [['01 - 13º Salário', fmt_brl(rd.get('trezeRendimentos'))],
                 ['02 - IRRF sobre 13º Salário', fmt_brl(rd.get('trezeIrrf'))],
                 ['03 - Outros', fmt_brl(rd.get('outrosTribExclusiva'))]],
                [130*mm, 40*mm])

    # Seção 6 - RRA
    add_section('6. RENDIMENTOS RECEBIDOS ACUMULADAMENTE (RRA)',
                [['Número do Processo', rd.get('rraNumProcesso','')],
                 ['Quantidade de Meses', rd.get('rraMeses','')],
                 ['Total Rendimentos Tributáveis', fmt_brl(rd.get('rraTributaveis'))],
                 ['Despesas com Ação Judicial', fmt_brl(rd.get('rraDespesasJudiciais'))],
                 ['Contribuição Previdenciária', fmt_brl(rd.get('rraInss'))],
                 ['Pensão Alimentícia', fmt_brl(rd.get('rraPensao'))],
                 ['IRRF', fmt_brl(rd.get('rraIrrf'))],
                 ['Rendimentos Isentos (Moléstia/Acidente)', fmt_brl(rd.get('rraIsentos'))]],
                [60*mm, 110*mm])

    # Seção 7
    story.append(Table([['7. INFORMAÇÕES COMPLEMENTARES']], colWidths=[170*mm], style=[
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    info_table = Table([[Paragraph(info or 'Nada a declarar', styles['Normal'])]], colWidths=[170*mm])
    info_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 4*mm))

    # Seção 8
    add_section('8. RESPONSÁVEL PELAS INFORMAÇÕES',
                [['Nome', 'Data', 'Assinatura'],
                 [resp.get('nome', 'Não informado'), resp.get('data', '  /  /    '), Paragraph(resp.get('assinatura', 'Isento conforme IN RFB 1215/2011'), styles['Small'])]],
                [70*mm, 40*mm, 60*mm])

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph('<i>Aprovado pela Instrução Normativa RFB nº 2.060, de 13 de dezembro de 2021.</i>', styles['Normal']))
    doc.build(story)

if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(1)
    with open(sys.argv[1]) as f: dados = json.load(f)
    gerar_pdf(dados, sys.argv[2])
    print(f"✅ PDF gerado: {sys.argv[2]}")