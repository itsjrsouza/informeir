#!/usr/bin/env python3
import sys, json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

def fmt_brl(val):
    if val is None or val == "": return "0,00"
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

    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    story = []

    story.append(Paragraph('<b>MINISTÉRIO DA FAZENDA</b>', styles['Center']))
    story.append(Paragraph('<b>SECRETARIA DA RECEITA FEDERAL DO BRASIL</b>', styles['Center']))
    story.append(Paragraph('<b>IMPOSTO SOBRE A RENDA DA PESSOA FÍSICA</b>', styles['Center']))
    story.append(Spacer(1, 5*mm))

    data_periodo = [[Paragraph(f'<b>Exercício de {exercicio}</b>', styles['Left']), Paragraph(f'<b>Ano-Calendário {ano}</b>', styles['Right'])]]
    t_periodo = Table(data_periodo, colWidths=[85*mm, 85*mm])
    t_periodo.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_periodo)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('<b>Comprovante de Rendimentos Pagos e de Imposto sobre a Renda Retido na Fonte</b>', styles['Center']))
    story.append(Spacer(1, 5*mm))

    def add_section(title, data, col_widths):
        story.append(Table([[title]], colWidths=[sum(col_widths)], style=[('BACKGROUND', (0,0), (-1,-1), colors.lightgrey), ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3), ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
        t = Table(data, colWidths=col_widths)
        style = [('FONTSIZE', (0,0), (-1,-1), 9), ('GRID', (0,0), (-1,-1), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEEEEE'))]
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 4*mm))

    add_section('1. FONTE PAGADORA PESSOA JURÍDICA OU PESSOA FÍSICA', [['Nome Empresarial/Nome Completo', 'CNPJ/CPF'], [fp.get('razaoSocial',''), fmt_cnpj(fp.get('cnpj',''))]], [120*mm, 50*mm])
    add_section('2. PESSOA FÍSICA BENEFICIÁRIA DOS RENDIMENTOS', [['CPF', 'Nome Completo'], [fmt_cpf(bn.get('cpf','')), bn.get('nome','')], ['Natureza do Rendimento: Assalariado', '']], [50*mm, 120*mm])
    add_section('3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO RETIDO NA FONTE', [['01 - Total dos Rendimentos (inclusive Férias)', fmt_brl(rd.get('tributaveis'))], ['02 - Contribuição Previdenciária Oficial', fmt_brl(rd.get('inss'))], ['03 - Contrib. previd. complementar / FAPI', '0,00'], ['04 - Pensão Alimentícia', fmt_brl(rd.get('outrasDeducoes'))], ['05 - Imposto sobre a renda retido na fonte', fmt_brl(rd.get('irrf'))]], [130*mm, 40*mm])
    add_section('4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS', [['04 - Lucros e Dividendos pagos por PJ', fmt_brl(rd.get('lucrosDividendos'))], ['07 - Outros', fmt_brl(rd.get('outrosIsentos'))]], [130*mm, 40*mm])
    add_section('5. RENDIMENTOS SUJEITOS À TRIBUTAÇÃO EXCLUSIVA', [['01 - 13º (décimo terceiro) salário', fmt_brl(rd.get('trezeRendimentos'))], ['02 - IRRF sobre 13º salário', fmt_brl(rd.get('trezeIrrf'))]], [130*mm, 40*mm])
    add_section('8. RESPONSÁVEL PELAS INFORMAÇÕES', [['Nome', 'Data', 'Assinatura'], [resp.get('nome', 'Não informado'), resp.get('data', '  /  /    '), 'Isento conforme IN RFB 1215/2011']], [80*mm, 40*mm, 50*mm])

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph('<i>Aprovado pela Instrução Normativa RFB nº 2.060, de 13 de dezembro de 2021.</i>', styles['Left']))
    doc.build(story)

if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(1)
    with open(sys.argv[1]) as f: dados = json.load(f)
    gerar_pdf(dados, sys.argv[2])
    print(f"✅ PDF gerado: {sys.argv[2]}")