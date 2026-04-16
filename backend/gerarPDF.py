#!/usr/bin/env python3
"""
gerarPDF.py
Recebe JSON de um informe e gera o PDF via wkhtmltopdf.
Uso: python3 gerarPDF.py <dados.json> <saida.pdf>
"""

import sys
import json
import os
import pdfkit

RESPONSAVEL_NOME = "NELSON FERNANDES DE SOUZA JUNIOR"
RESPONSAVEL_DATA = "28.02.2026"

def fmt_brl(val):
    if val is None or val == "":
        return "R$ 0,00"
    s = str(val).strip().replace("R$", "").strip()
    # Normaliza para float
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        f = float(s)
        # Formata em pt-BR
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

def gerar_html(dados):
    fp = dados.get("fontePagadora", {})
    bn = dados.get("beneficiario", {})
    rd = dados.get("rendimentos", {})
    ano = dados.get("anoCalendario", "")
    resp = dados.get("responsavel", {})

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<style>
  @page {{ size: A4; margin: 1.2cm 1.4cm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; font-size: 9pt; color: #1a1a1a; }}

  .cabecalho {{
    background: #1F3864;
    color: white;
    text-align: center;
    padding: 10px;
    margin-bottom: 10px;
  }}
  .cabecalho h1 {{ font-size: 12pt; font-weight: bold; letter-spacing: 0.5px; }}
  .cabecalho p  {{ font-size: 9pt; margin-top: 3px; opacity: 0.9; }}

  table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
  th, td {{ border: 1px solid #aaa; padding: 4px 7px; }}

  .sec-title td {{
    background: #2563A8;
    color: white;
    font-weight: bold;
    font-size: 8.5pt;
    padding: 5px 7px;
    letter-spacing: 0.3px;
  }}
  .col-header {{
    background: #D9E1F2;
    font-weight: bold;
    font-size: 7.5pt;
    text-align: center;
    color: #1F3864;
  }}
  .val {{ font-size: 9.5pt; font-weight: bold; }}
  .val-right {{ text-align: right; }}
  .val-center {{ text-align: center; }}

  .rodape {{
    margin-top: 12px;
    border-top: 1px solid #ccc;
    padding-top: 6px;
    font-size: 7.5pt;
    color: #555;
    font-style: italic;
    text-align: justify;
  }}
  .assinatura {{
    margin-top: 20px;
    border-top: 1px solid #333;
    padding-top: 4px;
    text-align: center;
    font-size: 8pt;
  }}
</style>
</head>
<body>

<div class="cabecalho">
  <h1>COMPROVANTE ANUAL DE RENDIMENTOS PAGOS OU CREDITADOS</h1>
  <p>ANO-CALENDÁRIO: {ano}</p>
</div>

<!-- 1. Fonte Pagadora -->
<table>
  <tr class="sec-title"><td colspan="2">1. FONTE PAGADORA</td></tr>
  <tr>
    <th class="col-header" style="width:65%">RAZÃO SOCIAL / NOME EMPRESARIAL</th>
    <th class="col-header" style="width:35%">CNPJ</th>
  </tr>
  <tr>
    <td class="val">{fp.get('razaoSocial','')}</td>
    <td class="val val-center">{fmt_cnpj(fp.get('cnpj',''))}</td>
  </tr>
</table>

<!-- 2. Beneficiário -->
<table>
  <tr class="sec-title"><td colspan="2">2. BENEFICIÁRIO</td></tr>
  <tr>
    <th class="col-header" style="width:65%">NOME COMPLETO</th>
    <th class="col-header" style="width:35%">CPF</th>
  </tr>
  <tr>
    <td class="val">{bn.get('nome','')}</td>
    <td class="val val-center">{fmt_cpf(bn.get('cpf',''))}</td>
  </tr>
</table>

<!-- 3. Rendimentos Tributáveis -->
<table>
  <tr class="sec-title"><td colspan="4">3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO SOBRE A RENDA RETIDO NA FONTE</td></tr>
  <tr>
    <th class="col-header">RENDIMENTOS TRIBUTÁVEIS (R$)</th>
    <th class="col-header">CONTRIBUIÇÃO PREVIDENCIÁRIA INSS (R$)</th>
    <th class="col-header">OUTRAS DEDUÇÕES (R$)</th>
    <th class="col-header">IMPOSTO RETIDO NA FONTE (R$)</th>
  </tr>
  <tr>
    <td class="val val-right">{fmt_brl(rd.get('tributaveis'))}</td>
    <td class="val val-right">{fmt_brl(rd.get('inss'))}</td>
    <td class="val val-right">{fmt_brl(rd.get('outrasDeducoes'))}</td>
    <td class="val val-right">{fmt_brl(rd.get('irrf'))}</td>
  </tr>
</table>

<!-- 4. Rendimentos Isentos -->
<table>
  <tr class="sec-title"><td colspan="2">4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS</td></tr>
  <tr>
    <th class="col-header" style="width:50%">LUCROS E DIVIDENDOS DISTRIBUÍDOS (R$)</th>
    <th class="col-header" style="width:50%">OUTROS RENDIMENTOS ISENTOS (R$)</th>
  </tr>
  <tr>
    <td class="val val-right">{fmt_brl(rd.get('lucrosDividendos'))}</td>
    <td class="val val-right">{fmt_brl(rd.get('outrosIsentos'))}</td>
  </tr>
</table>

<!-- 5. Plano de Saúde -->
<table>
  <tr class="sec-title"><td colspan="2">5. PLANO DE SAÚDE COLETIVO EMPRESARIAL</td></tr>
  <tr>
    <th class="col-header" style="width:50%">VALORES PAGOS PELO BENEFICIÁRIO (R$)</th>
    <th class="col-header" style="width:50%">VALORES PAGOS PELA FONTE PAGADORA (R$)</th>
  </tr>
  <tr>
    <td class="val val-right">{fmt_brl(rd.get('planoBeneficiario'))}</td>
    <td class="val val-right">{fmt_brl(rd.get('planoFontePagadora'))}</td>
  </tr>
</table>

<!-- 6. 13° Salário -->
<table>
  <tr class="sec-title"><td colspan="3">6. DÉCIMO TERCEIRO SALÁRIO</td></tr>
  <tr>
    <th class="col-header">RENDIMENTOS TRIBUTÁVEIS (R$)</th>
    <th class="col-header">CONTRIBUIÇÃO PREVIDENCIÁRIA INSS (R$)</th>
    <th class="col-header">IMPOSTO RETIDO NA FONTE (R$)</th>
  </tr>
  <tr>
    <td class="val val-right">{fmt_brl(rd.get('trezeRendimentos'))}</td>
    <td class="val val-right">{fmt_brl(rd.get('trezeInss'))}</td>
    <td class="val val-right">{fmt_brl(rd.get('trezeIrrf'))}</td>
  </tr>
</table>

<!-- 7. Responsável -->
<table>
  <tr class="sec-title"><td colspan="2">7. RESPONSÁVEL PELAS INFORMAÇÕES</td></tr>
  <tr>
    <th class="col-header" style="width:70%">NOME COMPLETO</th>
    <th class="col-header" style="width:30%">DATA</th>
  </tr>
  <tr>
    <td class="val">{resp.get('nome', RESPONSAVEL_NOME)}</td>
    <td class="val val-center">{resp.get('data', RESPONSAVEL_DATA)}</td>
  </tr>
</table>

<div class="rodape">
  Este comprovante é válido como documento para a Declaração de Ajuste Anual do Imposto sobre a Renda
  da Pessoa Física — DIRPF, conforme art. 16 da Instrução Normativa RFB nº 1.215, de 15 de dezembro de 2011.
</div>

</body>
</html>"""

def gerar(dados, output_path):
    html = gerar_html(dados)
    options = {
        "quiet": "",
        "page-size": "A4",
        "margin-top":    "0mm",
        "margin-right":  "0mm",
        "margin-bottom": "0mm",
        "margin-left":   "0mm",
        "encoding": "UTF-8",
        "enable-local-file-access": "",
    }
    pdfkit.from_string(html, output_path, options=options)
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 gerarPDF.py <dados.json> <saida.pdf>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        dados = json.load(f)
    gerar(dados, sys.argv[2])
    print(f"✅ PDF gerado: {sys.argv[2]}")
