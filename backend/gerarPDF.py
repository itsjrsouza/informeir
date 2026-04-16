#!/usr/bin/env python3
"""
gerarPDF.py
Recebe JSON de um informe e gera o PDF via reportlab.
Uso: python3 gerarPDF.py <dados.json> <saida.pdf>
"""

import sys
import json

# Verificar se reportlab está instalado
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    print(f"❌ Erro: reportlab não está instalado. Execute: pip install reportlab", file=sys.stderr)
    print(f"   Detalhes: {e}", file=sys.stderr)
    REPORTLAB_AVAILABLE = False
    sys.exit(1)

RESPONSAVEL_NOME = "NELSON FERNANDES DE SOUZA JUNIOR"
RESPONSAVEL_DATA = "28.02.2026"

def fmt_brl(val):
    if val is None or val == "":
        return "R$ 0,00"
    s = str(val).strip().replace("R$", "").strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        f = float(s)
        inteiro, decimal = f"{f:.2f}".split(".")
        inteiro_fmt = ""
        for i, d in enumerate(reversed(inteiro)):
            if i and i % 3 == 0:
                inteiro_fmt = "." + inteiro_fmt
            inteiro_fmt = d + inteiro_fmt
        return f"R$ {inteiro_fmt},{decimal}"
    except Exception:
        return "R$ 0,00"

def fmt_cnpj(v):
    d = "".join(c for c in str(v or "") if c.isdigit())
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return v

def fmt_cpf(v):
    d = "".join(c for c in str(v or "") if c.isdigit())
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return v

def gerar_pdf(dados, output_path):
    fp = dados.get("fontePagadora", {})
    bn = dados.get("beneficiario", {})
    rd = dados.get("rendimentos", {})
    ano = dados.get("anoCalendario", "")
    resp = dados.get("responsavel", {})

    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=15*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
    
    story = []
    
    # Cabeçalho
    header_data = [[Paragraph(f'<font color="white"><b>COMPROVANTE ANUAL DE RENDIMENTOS PAGOS OU CREDITADOS</b></font><br/><font color="white">ANO-CALENDÁRIO: {ano}</font>', styles['Center'])]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1F3864')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 5*mm))
    
    # Função para criar seção
    def add_section(title, data, col_widths):
        # Título da seção
        title_table = Table([[title]], colWidths=[sum(col_widths)])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#D9E1F2')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(title_table)
        
        # Dados
        data_table = Table(data, colWidths=col_widths)
        style = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        
        # Cabeçalho em negrito com fundo
        style.extend([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F9')),
        ])
        
        data_table.setStyle(TableStyle(style))
        story.append(data_table)
        story.append(Spacer(1, 4*mm))
    
    # Seção 1 - Fonte Pagadora
    add_section(
        '1. FONTE PAGADORA',
        [[
            Paragraph('<b>RAZÃO SOCIAL / NOME EMPRESARIAL</b>', styles['Left']),
            Paragraph('<b>CNPJ</b>', styles['Left'])
        ],
        [
            fp.get('razaoSocial', ''),
            fmt_cnpj(fp.get('cnpj', ''))
        ]],
        [120*mm, 50*mm]
    )
    
    # Seção 2 - Beneficiário
    add_section(
        '2. BENEFICIÁRIO',
        [[
            Paragraph('<b>NOME COMPLETO</b>', styles['Left']),
            Paragraph('<b>CPF</b>', styles['Left'])
        ],
        [
            bn.get('nome', ''),
            fmt_cpf(bn.get('cpf', ''))
        ]],
        [120*mm, 50*mm]
    )
    
    # Seção 3 - Rendimentos Tributáveis
    add_section(
        '3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO SOBRE A RENDA RETIDO NA FONTE',
        [[
            Paragraph('<b>RENDIMENTOS TRIBUTÁVEIS (R$)</b>', styles['Center']),
            Paragraph('<b>CONTRIBUIÇÃO PREVIDENCIÁRIA INSS (R$)</b>', styles['Center']),
            Paragraph('<b>OUTRAS DEDUÇÕES (R$)</b>', styles['Center']),
            Paragraph('<b>IMPOSTO RETIDO NA FONTE (R$)</b>', styles['Center'])
        ],
        [
            Paragraph(fmt_brl(rd.get('tributaveis')), styles['Right']),
            Paragraph(fmt_brl(rd.get('inss')), styles['Right']),
            Paragraph(fmt_brl(rd.get('outrasDeducoes')), styles['Right']),
            Paragraph(fmt_brl(rd.get('irrf')), styles['Right'])
        ]],
        [42*mm, 42*mm, 42*mm, 44*mm]
    )
    
    # Seção 4 - Rendimentos Isentos
    add_section(
        '4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS',
        [[
            Paragraph('<b>LUCROS E DIVIDENDOS DISTRIBUÍDOS (R$)</b>', styles['Center']),
            Paragraph('<b>OUTROS RENDIMENTOS ISENTOS (R$)</b>', styles['Center'])
        ],
        [
            Paragraph(fmt_brl(rd.get('lucrosDividendos')), styles['Right']),
            Paragraph(fmt_brl(rd.get('outrosIsentos')), styles['Right'])
        ]],
        [85*mm, 85*mm]
    )
    
    # Seção 5 - Plano de Saúde
    add_section(
        '5. PLANO DE SAÚDE COLETIVO EMPRESARIAL',
        [[
            Paragraph('<b>VALORES PAGOS PELO BENEFICIÁRIO (R$)</b>', styles['Center']),
            Paragraph('<b>VALORES PAGOS PELA FONTE PAGADORA (R$)</b>', styles['Center'])
        ],
        [
            Paragraph(fmt_brl(rd.get('planoBeneficiario')), styles['Right']),
            Paragraph(fmt_brl(rd.get('planoFontePagadora')), styles['Right'])
        ]],
        [85*mm, 85*mm]
    )
    
    # Seção 6 - 13° Salário
    add_section(
        '6. DÉCIMO TERCEIRO SALÁRIO',
        [[
            Paragraph('<b>RENDIMENTOS TRIBUTÁVEIS (R$)</b>', styles['Center']),
            Paragraph('<b>CONTRIBUIÇÃO PREVIDENCIÁRIA INSS (R$)</b>', styles['Center']),
            Paragraph('<b>IMPOSTO RETIDO NA FONTE (R$)</b>', styles['Center'])
        ],
        [
            Paragraph(fmt_brl(rd.get('trezeRendimentos')), styles['Right']),
            Paragraph(fmt_brl(rd.get('trezeInss')), styles['Right']),
            Paragraph(fmt_brl(rd.get('trezeIrrf')), styles['Right'])
        ]],
        [56*mm, 56*mm, 58*mm]
    )
    
    # Seção 7 - Responsável
    add_section(
        '7. RESPONSÁVEL PELAS INFORMAÇÕES',
        [[
            Paragraph('<b>NOME COMPLETO</b>', styles['Left']),
            Paragraph('<b>DATA</b>', styles['Left'])
        ],
        [
            resp.get('nome', RESPONSAVEL_NOME),
            resp.get('data', RESPONSAVEL_DATA)
        ]],
        [120*mm, 50*mm]
    )
    
    # Rodapé
    story.append(Spacer(1, 8*mm))
    footer_text = Paragraph(
        '<font color="#555555"><i>Este comprovante é válido como documento para a Declaração de Ajuste Anual do Imposto sobre a Renda da Pessoa Física — DIRPF, conforme art. 16 da Instrução Normativa RFB nº 1.215, de 15 de dezembro de 2011.</i></font>',
        styles['Left']
    )
    footer_table = Table([[footer_text]], colWidths=[170*mm])
    footer_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(footer_table)
    
    doc.build(story)
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 gerarPDF.py <dados.json> <saida.pdf>")
        sys.exit(1)
    
    if not REPORTLAB_AVAILABLE:
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        gerar_pdf(dados, sys.argv[2])
        print(f"✅ PDF gerado: {sys.argv[2]}")
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}", file=sys.stderr)
        sys.exit(1)