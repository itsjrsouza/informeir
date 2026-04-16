#!/usr/bin/env python3
"""
parseExcel.py
Lê planilha de importação e retorna JSON com os dados de cada sócio.
Suporta .xlsx, .xls, .csv (qualquer formato que o pandas leia).
Uso: python3 parseExcel.py <arquivo>
"""

import sys
import json
import re
import os
import pandas as pd

# Mapeamento: nome da coluna no Excel → (chave interna, seção)
COL_MAP = {
    "ANO_CALENDARIO":      ("anoCalendario",      "meta"),
    "CNPJ_EMPRESA":        ("cnpj",               "fontePagadora"),
    "RAZAO_SOCIAL":        ("razaoSocial",         "fontePagadora"),
    "NOME_SOCIO":          ("nome",                "beneficiario"),
    "CPF_SOCIO":           ("cpf",                 "beneficiario"),
    "TRIBUTAVEIS":         ("tributaveis",         "rendimentos"),
    "INSS":                ("inss",                "rendimentos"),
    "OUTRAS_DEDUCOES":     ("outrasDeducoes",      "rendimentos"),
    "IRRF":                ("irrf",                "rendimentos"),
    "LUCROS_DIVIDENDOS":   ("lucrosDividendos",    "rendimentos"),
    "OUTROS_ISENTOS":      ("outrosIsentos",       "rendimentos"),
    "PLANO_BENEFICIARIO":  ("planoBeneficiario",   "rendimentos"),
    "PLANO_FONTE":         ("planoFontePagadora",  "rendimentos"),
    "TREZE_RENDIMENTOS":   ("trezeRendimentos",    "rendimentos"),
    "TREZE_INSS":          ("trezeInss",           "rendimentos"),
    "TREZE_IRRF":          ("trezeIrrf",           "rendimentos"),
}

def limpar_numero(val):
    """Converte valor monetário brasileiro para string formatada sem R$"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "0,00"
    
    s = str(val).strip()
    
    # Remove R$, espaços, e outros símbolos
    s = re.sub(r'[R$\s]', '', s)
    
    # Se for apenas vírgula ou vazio
    if s in ('', ',', '.', '-', '0'):
        return "0,00"
    
    # Caso comum: "170110,21000" -> remover zeros extras após 2 casas decimais
    # Primeiro, substitui vírgula por ponto para conversão
    if ',' in s:
        # Se tem ponto e vírgula (ex: 1.234,56)
        if '.' in s:
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '.')
    
    try:
        f = float(s)
        # Arredonda para 2 casas decimais
        f = round(f, 2)
        # Formata com separadores brasileiros
        inteiro, decimal = f"{f:.2f}".split('.')
        # Adiciona pontos a cada 3 dígitos
        inteiro_fmt = ""
        for i, d in enumerate(reversed(inteiro)):
            if i > 0 and i % 3 == 0:
                inteiro_fmt = "." + inteiro_fmt
            inteiro_fmt = d + inteiro_fmt
        return f"{inteiro_fmt},{decimal}"
    except (ValueError, TypeError):
        return "0,00"

def limpar_cnpj(val):
    return re.sub(r'\D', '', str(val or ""))

def limpar_cpf(val):
    return re.sub(r'\D', '', str(val or ""))

def parse(caminho):
    if not os.path.exists(caminho):
        return {"erro": f"Arquivo não encontrado: {caminho}"}
    
    tamanho = os.path.getsize(caminho)
    if tamanho == 0:
        return {"erro": "Arquivo vazio"}

    try:
        # Tenta ler com pandas (suporta .xlsx, .xls, .csv, etc.)
        df = pd.read_excel(caminho, dtype=str, header=None)
    except Exception as e:
        return {"erro": f"Erro ao ler arquivo: {str(e)}. Verifique se é um Excel válido."}

    # Encontra a linha que contém "ANO_CALENDARIO"
    header_row = None
    for idx, row in df.iterrows():
        if 'ANO_CALENDARIO' in row.values:
            header_row = idx
            break

    if header_row is None:
        return {"erro": "Coluna ANO_CALENDARIO não encontrada. Use o modelo correto."}

    # Define a linha de cabeçalho como nomes das colunas
    df.columns = df.iloc[header_row]
    df = df.iloc[header_row+1:].reset_index(drop=True)
    
    # Remove linhas totalmente vazias
    df = df.dropna(how='all')
    
    socios = []
    erros = []

    for idx, row in df.iterrows():
        socio = {"fontePagadora": {}, "beneficiario": {}, "rendimentos": {}}
        erros_linha = []
        
        for col_nome, (chave, secao) in COL_MAP.items():
            if col_nome not in df.columns:
                continue
            val = row[col_nome]
            
            if pd.isna(val):
                val = ""
            else:
                val = str(val).strip()
            
            if secao == "meta":
                try:
                    socio["anoCalendario"] = int(float(val)) if val else None
                except:
                    socio["anoCalendario"] = None
            elif secao == "fontePagadora":
                if col_nome == "CNPJ_EMPRESA":
                    socio["fontePagadora"][chave] = limpar_cnpj(val)
                else:
                    socio["fontePagadora"][chave] = val.upper()
            elif secao == "beneficiario":
                if col_nome == "CPF_SOCIO":
                    socio["beneficiario"][chave] = limpar_cpf(val)
                else:
                    socio["beneficiario"][chave] = val.upper()
            elif secao == "rendimentos":
                socio["rendimentos"][chave] = limpar_numero(val)
        
        # Validações obrigatórias
        if not socio["fontePagadora"].get("cnpj"):
            erros_linha.append("CNPJ_EMPRESA vazio")
        if not socio["fontePagadora"].get("razaoSocial"):
            erros_linha.append("RAZAO_SOCIAL vazia")
        if not socio["beneficiario"].get("nome"):
            erros_linha.append("NOME_SOCIO vazio")
        if not socio["beneficiario"].get("cpf"):
            erros_linha.append("CPF_SOCIO vazio")
        if not socio.get("anoCalendario"):
            erros_linha.append("ANO_CALENDARIO inválido")
        
        if erros_linha:
            erros.append({
                "linha": idx + header_row + 2,
                "erros": erros_linha,
                "nome": socio["beneficiario"].get("nome", "?")
            })
            continue
        
        socio["responsavel"] = {
            "nome": "NELSON FERNANDES DE SOUZA JUNIOR",
            "data": "28.02.2026"
        }
        socios.append(socio)
    
    return {
        "total": len(socios),
        "registros": socios,
        "validos": len(socios),
        "invalidos": len(erros),
        "erros": erros,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"erro": "Informe o caminho do arquivo Excel"}))
        sys.exit(1)
    result = parse(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))