#!/usr/bin/env python3
import sys, json, re, os, pandas as pd

COL_MAP = {
    "EXERCICIO": ("exercicio", "meta"),
    "ANO_CALENDARIO": ("anoCalendario", "meta"),
    "CNPJ_EMPRESA": ("cnpj", "fontePagadora"),
    "RAZAO_SOCIAL": ("razaoSocial", "fontePagadora"),
    "NOME_SOCIO": ("nome", "beneficiario"),
    "CPF_SOCIO": ("cpf", "beneficiario"),
    "TRIBUTAVEIS": ("tributaveis", "rendimentos"),
    "INSS": ("inss", "rendimentos"),
    "OUTRAS_DEDUCOES": ("outrasDeducoes", "rendimentos"),
    "IRRF": ("irrf", "rendimentos"),
    "LUCROS_DIVIDENDOS": ("lucrosDividendos", "rendimentos"),
    "OUTROS_ISENTOS": ("outrosIsentos", "rendimentos"),
    "TREZE_RENDIMENTOS": ("trezeRendimentos", "rendimentos"),
    "TREZE_IRRF": ("trezeIrrf", "rendimentos"),
}

# Palavras-chave que indicam que a linha é um cabeçalho descritivo (não dados)
PALAVRAS_ROTULO = {'ano-calendário', 'ano calendário', 'ano', 'exercício', 'nome completo', 'cnpj', 'cpf', 'razão social'}

def limpar_numero(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "0,00"
    s = re.sub(r'[R$\s]', '', str(val).strip())
    if s in ('', ',', '.', '-', '0'):
        return "0,00"
    if ',' in s:
        s = s.replace('.', '').replace(',', '.') if '.' in s else s.replace(',', '.')
    try:
        f = round(float(s), 2)
        inteiro, decimal = f"{f:.2f}".split('.')
        inteiro_fmt = ""
        for i, d in enumerate(reversed(inteiro)):
            if i > 0 and i % 3 == 0:
                inteiro_fmt = "." + inteiro_fmt
            inteiro_fmt = d + inteiro_fmt
        return f"{inteiro_fmt},{decimal}"
    except:
        return "0,00"

def limpar_cnpj(v):
    return re.sub(r'\D', '', str(v or ""))

def limpar_cpf(v):
    return re.sub(r'\D', '', str(v or ""))

def linha_ignoravel(row, col_indices):
    """Verifica se a linha deve ser ignorada (ex: cabeçalho descritivo ou totalmente vazia)."""
    # Se todas as células são vazias ou NaN
    if all(pd.isna(cell) or str(cell).strip() == '' for cell in row):
        return True

    # Se a primeira coluna (geralmente ano ou exercício) contém texto descritivo
    if col_indices.get('ANO_CALENDARIO') is not None:
        idx = col_indices['ANO_CALENDARIO']
        val = str(row[idx]).strip().lower() if not pd.isna(row[idx]) else ''
        if any(p in val for p in PALAVRAS_ROTULO):
            return True
    elif col_indices.get('EXERCICIO') is not None:
        idx = col_indices['EXERCICIO']
        val = str(row[idx]).strip().lower() if not pd.isna(row[idx]) else ''
        if any(p in val for p in PALAVRAS_ROTULO):
            return True

    # Se o CPF não tem nenhum dígito, provavelmente é texto
    if col_indices.get('CPF_SOCIO') is not None:
        idx = col_indices['CPF_SOCIO']
        val = str(row[idx]).strip() if not pd.isna(row[idx]) else ''
        if val and not re.search(r'\d', val):
            return True

    return False

def parse(caminho):
    if not os.path.exists(caminho):
        return {"erro": "Arquivo não encontrado"}
    if os.path.getsize(caminho) == 0:
        return {"erro": "Arquivo vazio"}

    try:
        df = pd.read_excel(caminho, dtype=str, header=None)
    except Exception as e:
        return {"erro": f"Erro ao ler arquivo: {e}"}

    # Encontra a linha que contém "ANO_CALENDARIO"
    header_row = None
    for idx, row in df.iterrows():
        if 'ANO_CALENDARIO' in row.values:
            header_row = idx
            break

    if header_row is None:
        return {"erro": "Coluna ANO_CALENDARIO não encontrada"}

    # Mapeia nome da coluna -> índice na linha
    col_indices = {}
    for i, cell in enumerate(df.iloc[header_row]):
        if cell and str(cell).strip():
            col_indices[str(cell).strip()] = i

    # Define colunas e descarta linhas anteriores
    df.columns = df.iloc[header_row]
    df = df.iloc[header_row+1:].reset_index(drop=True)

    socios, erros = [], []
    for idx, row in df.iterrows():
        if linha_ignoravel(row, col_indices):
            continue

        socio = {"fontePagadora": {}, "beneficiario": {}, "rendimentos": {}}
        erros_linha = []

        for col_nome, (chave, secao) in COL_MAP.items():
            if col_nome not in col_indices:
                continue
            cell_idx = col_indices[col_nome]
            val = str(row.iloc[cell_idx]).strip() if not pd.isna(row.iloc[cell_idx]) else ""

            if secao == "meta":
                try:
                    socio[chave] = int(float(val)) if val else None
                except:
                    socio[chave] = None
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

        # Se não veio EXERCICIO, calcula a partir do ANO_CALENDARIO
        if not socio.get("exercicio") and socio.get("anoCalendario"):
            socio["exercicio"] = socio["anoCalendario"] + 1

        # Validações
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
        print(json.dumps({"erro": "Informe o caminho"}))
        sys.exit(1)
    resultado = parse(sys.argv[1])
    print(json.dumps(resultado, ensure_ascii=False, indent=2))