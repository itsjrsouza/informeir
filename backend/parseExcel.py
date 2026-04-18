#!/usr/bin/env python3
import sys, json, re, os, pandas as pd

COL_MAP = {
    "EXERCICIO": ("exercicio", "meta"),
    "ANO_CALENDARIO": ("anoCalendario", "meta"),
    "CNPJ_EMPRESA": ("cnpj", "fontePagadora"),
    "RAZAO_SOCIAL": ("razaoSocial", "fontePagadora"),
    "NOME_BENEFICIARIO": ("nome", "beneficiario"),
    "CPF_BENEFICIARIO": ("cpf", "beneficiario"),
    "TRIBUTAVEIS": ("tributaveis", "rendimentos"),
    "INSS": ("inss", "rendimentos"),
    "PREV_COMPLEMENTAR": ("prevComplementar", "rendimentos"),
    "PENSAO_ALIMENTICIA": ("pensaoAlimenticia", "rendimentos"),
    "IRRF": ("irrf", "rendimentos"),
    "PARCELA_ISENTA65": ("parcelaIsenta65", "rendimentos"),
    "DIARIAS_AJUDAS": ("diariasAjudas", "rendimentos"),
    "MOLESTIA_GRAVE": ("molestiaGrave", "rendimentos"),
    "LUCROS_DIVIDENDOS": ("lucrosDividendos", "rendimentos"),
    "PROLABORE_ISENTO": ("prolaboreIsento", "rendimentos"),
    "INDENIZACOES": ("indenizacoes", "rendimentos"),
    "OUTROS_ISENTOS": ("outrosIsentos", "rendimentos"),
    "TREZE_RENDIMENTOS": ("trezeRendimentos", "rendimentos"),
    "TREZE_IRRF": ("trezeIrrf", "rendimentos"),
    "OUTROS_TRIB_EXCL": ("outrosTribExclusiva", "rendimentos"),
    "RRA_NUM_PROCESSO": ("rraNumProcesso", "rendimentos"),
    "RRA_MESES": ("rraMeses", "rendimentos"),
    "RRA_TRIBUTAVEIS": ("rraTributaveis", "rendimentos"),
    "RRA_DESP_JUDICIAIS": ("rraDespesasJudiciais", "rendimentos"),
    "RRA_INSS": ("rraInss", "rendimentos"),
    "RRA_PENSAO": ("rraPensao", "rendimentos"),
    "RRA_IRRF": ("rraIrrf", "rendimentos"),
    "RRA_ISENTOS": ("rraIsentos", "rendimentos"),
    "INFO_COMPLEMENTARES": ("informacoesComplementares", "info"),
    "RESP_NOME": ("responsavelNome", "responsavel"),
    "RESP_DATA": ("responsavelData", "responsavel"),
    "RESP_ASSINATURA": ("responsavelAssinatura", "responsavel"),
}

PALAVRAS_ROTULO = {'ano-calendário', 'ano calendário', 'ano', 'exercício', 'nome completo', 'cnpj', 'cpf', 'razão social'}

def limpar_numero(val):
    if val is None or (isinstance(val, float) and pd.isna(val)): return "0,00"
    s = re.sub(r'[R$\s]', '', str(val).strip())
    if s in ('', ',', '.', '-', '0'): return "0,00"
    if ',' in s: s = s.replace('.', '').replace(',', '.') if '.' in s else s.replace(',', '.')
    try:
        f = round(float(s), 2)
        inteiro, decimal = f"{f:.2f}".split('.')
        inteiro_fmt = ""
        for i, d in enumerate(reversed(inteiro)):
            if i > 0 and i % 3 == 0: inteiro_fmt = "." + inteiro_fmt
            inteiro_fmt = d + inteiro_fmt
        return f"{inteiro_fmt},{decimal}"
    except: return "0,00"

def limpar_cnpj(v): return re.sub(r'\D', '', str(v or ""))
def limpar_cpf(v): return re.sub(r'\D', '', str(v or ""))

def linha_ignoravel(row):
    if all(pd.isna(v) or str(v).strip() == '' for v in row): return True
    primeira_col = None
    if 'ANO_CALENDARIO' in row.index: primeira_col = str(row['ANO_CALENDARIO']).strip().lower()
    elif 'EXERCICIO' in row.index: primeira_col = str(row['EXERCICIO']).strip().lower()
    if primeira_col and any(p in primeira_col for p in PALAVRAS_ROTULO): return True
    if 'CPF_BENEFICIARIO' in row.index:
        cpf_val = str(row['CPF_BENEFICIARIO']).strip()
        if cpf_val and not re.search(r'\d', cpf_val): return True
    return False

def parse(caminho):
    if not os.path.exists(caminho): return {"erro": "Arquivo não encontrado"}
    if os.path.getsize(caminho) == 0: return {"erro": "Arquivo vazio"}
    try: df = pd.read_excel(caminho, dtype=str, header=None)
    except Exception as e: return {"erro": f"Erro ao ler arquivo: {e}"}
    header_row = None
    for idx, row in df.iterrows():
        if 'ANO_CALENDARIO' in row.values: header_row = idx; break
    if header_row is None: return {"erro": "Coluna ANO_CALENDARIO não encontrada"}
    df.columns = df.iloc[header_row]
    df = df.iloc[header_row+1:].reset_index(drop=True).dropna(how='all')
    BENEFICIARIOs, erros = [], []
    for idx, row in df.iterrows():
        if linha_ignoravel(row): continue
        BENEFICIARIO = {"fontePagadora": {}, "beneficiario": {}, "rendimentos": {}, "responsavel": {}}
        info = ""
        erros_linha = []
        for col_nome, (chave, secao) in COL_MAP.items():
            if col_nome not in df.columns: continue
            val = str(row[col_nome]).strip() if not pd.isna(row[col_nome]) else ""
            if secao == "meta":
                try: BENEFICIARIO[chave] = int(float(val)) if val else None
                except: BENEFICIARIO[chave] = None
            elif secao == "fontePagadora":
                BENEFICIARIO["fontePagadora"][chave] = limpar_cnpj(val) if col_nome == "CNPJ_EMPRESA" else val.upper()
            elif secao == "beneficiario":
                BENEFICIARIO["beneficiario"][chave] = limpar_cpf(val) if col_nome == "CPF_BENEFICIARIO" else val.upper()
            elif secao == "rendimentos":
                if chave.startswith('rra') and chave not in ['rraTributaveis','rraDespesasJudiciais','rraInss','rraPensao','rraIrrf','rraIsentos']:
                    BENEFICIARIO["rendimentos"][chave] = val
                else:
                    BENEFICIARIO["rendimentos"][chave] = limpar_numero(val)
            elif secao == "info":
                info = val
            elif secao == "responsavel":
                BENEFICIARIO["responsavel"][chave.replace('responsavel','').lower()] = val

        BENEFICIARIO["informacoesComplementares"] = info
        if not BENEFICIARIO.get("exercicio") and BENEFICIARIO.get("anoCalendario"): BENEFICIARIO["exercicio"] = BENEFICIARIO["anoCalendario"] + 1
        if not BENEFICIARIO["fontePagadora"].get("cnpj"): erros_linha.append("CNPJ_EMPRESA vazio")
        if not BENEFICIARIO["fontePagadora"].get("razaoSocial"): erros_linha.append("RAZAO_SOCIAL vazia")
        if not BENEFICIARIO["beneficiario"].get("nome"): erros_linha.append("NOME_BENEFICIARIO vazio")
        if not BENEFICIARIO["beneficiario"].get("cpf"): erros_linha.append("CPF_BENEFICIARIO vazio")
        if not BENEFICIARIO.get("anoCalendario"): erros_linha.append("ANO_CALENDARIO inválido")
        if erros_linha:
            erros.append({"linha": idx + header_row + 2, "erros": erros_linha, "nome": BENEFICIARIO["beneficiario"].get("nome", "?")})
            continue
        BENEFICIARIOs.append(BENEFICIARIO)
    return {"total": len(BENEFICIARIOs), "registros": BENEFICIARIOs, "validos": len(BENEFICIARIOs), "invalidos": len(erros), "erros": erros}

if __name__ == "__main__":
    if len(sys.argv) < 2: print(json.dumps({"erro": "Informe o caminho"})); sys.exit(1)
    print(json.dumps(parse(sys.argv[1]), ensure_ascii=False, indent=2))