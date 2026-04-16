# 📋 Informe de Rendimentos — Gerador Automático

Sistema completo para geração de **Comprovantes Anuais de Rendimentos Pagos** no padrão da Receita Federal do Brasil.

---

## 🗂️ Estrutura do Projeto

```
informe-rendimentos/
├── backend/
│   ├── server.js          ← Servidor Express (API REST)
│   ├── gerarInforme.js    ← Motor de geração do .docx
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── App.jsx        ← Interface React completa
│   │   └── main.jsx       ← Entrypoint
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

---

## ⚙️ Pré-requisitos

- **Node.js** v18 ou superior
- **npm** v9 ou superior

---

## 🚀 Como rodar

### 1. Backend

```bash
cd backend
npm install
npm start
```

O servidor sobe em **http://localhost:3001**

Para desenvolvimento com auto-reload:
```bash
npm run dev
```

---

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

A interface abre em **http://localhost:5173**

---

## 🔗 API

### `POST /api/informe/gerar`

Gera e retorna o arquivo `.docx` para download.

**Content-Type:** `application/json`

**Body:**
```json
{
  "anoCalendario": 2025,
  "fontePagadora": {
    "razaoSocial": "EMPRESA EXEMPLO LTDA",
    "cnpj": "12.345.678/0001-95"
  },
  "beneficiario": {
    "nome": "JOÃO DA SILVA SOUZA",
    "cpf": "123.456.789-01"
  },
  "rendimentos": {
    "tributaveis":        "84000,00",
    "inss":               "7786,00",
    "outrasDeducoes":     "0,00",
    "irrf":               "4200,00",
    "lucrosDividendos":   "120000,00",
    "outrosIsentos":      "0,00",
    "planoBeneficiario":  "0,00",
    "planoFontePagadora": "3600,00",
    "trezeRendimentos":   "7000,00",
    "trezeInss":          "648,83",
    "trezeIrrf":          "0,00"
  }
}
```

**Resposta:** Arquivo `.docx` (download direto)

> O campo `responsavel` é preenchido automaticamente:
> - **Nome:** NELSON FERNANDES DE SOUZA JUNIOR
> - **Data:** 28.02.2026

---

### `GET /api/health`

Verifica se o servidor está no ar.

```json
{ "status": "ok", "timestamp": "2026-02-28T..." }
```

---

## 📄 Seções do Informe Gerado

| # | Seção |
|---|-------|
| 1 | Fonte Pagadora (Razão Social + CNPJ) |
| 2 | Beneficiário (Nome + CPF) |
| 3 | Rendimentos Tributáveis, Deduções e IRRF |
| 4 | Rendimentos Isentos e Não Tributáveis |
| 5 | Plano de Saúde Coletivo Empresarial |
| 6 | Décimo Terceiro Salário |
| 7 | Responsável pelas Informações *(fixo)* |

---

## 🔄 Fluxo da Aplicação

```
[Formulário React]
      │
      │  POST /api/informe/gerar
      ▼
[Express Server]
      │
      │  gerarInforme(dados, path)
      ▼
[gerarInforme.js]  ←── biblioteca: docx (npm)
      │
      │  Packer.toBuffer(doc)
      ▼
[Arquivo .docx]
      │
      │  res.download(file)
      ▼
[Download automático no navegador]
```

---

## 🧪 Teste rápido (sem frontend)

Execute direto o gerador para produzir um arquivo de exemplo:

```bash
cd backend
node gerarInforme.js
# Gera: teste_informe.docx
```

Ou via curl:
```bash
curl -X POST http://localhost:3001/api/informe/gerar \
  -H "Content-Type: application/json" \
  -d '{
    "anoCalendario": 2025,
    "fontePagadora": { "razaoSocial": "EMPRESA EXEMPLO LTDA", "cnpj": "12345678000195" },
    "beneficiario": { "nome": "JOÃO DA SILVA", "cpf": "12345678901" },
    "rendimentos": { "tributaveis": "84000,00", "lucrosDividendos": "120000,00" }
  }' \
  --output informe.docx
```

---

## 📦 Dependências

| Pacote | Uso |
|--------|-----|
| `express` | Servidor HTTP |
| `cors` | Permitir requisições do frontend |
| `docx` | Geração do arquivo Word (.docx) |
| `react` | Interface web |
| `vite` | Bundler do frontend |

---

## 🔒 Responsável fixo

Por determinação do projeto, o campo **Responsável pelas Informações** é sempre:

- **Nome:** NELSON FERNANDES DE SOUZA JUNIOR
- **Data:** 28.02.2026

Para alterar, edite o objeto `responsavel` em `backend/server.js`:
```js
dados.responsavel = {
  nome: 'NELSON FERNANDES DE SOUZA JUNIOR',
  data: '28.02.2026'
};
```

---

## 📌 Próximos passos sugeridos

- [ ] Banco de dados para salvar histórico de informes gerados
- [ ] Autenticação por usuário/empresa
- [ ] Importação em lote via planilha Excel (múltiplos sócios)
- [ ] Geração em PDF além de .docx
- [ ] Validação de CNPJ e CPF com dígito verificador
- [ ] Envio por e-mail automático
