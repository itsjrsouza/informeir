const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, BorderStyle, WidthType, ShadingType, VerticalAlign,
  HeadingLevel
} = require('docx');
const fs = require('fs');

/**
 * Formata valor numérico para moeda brasileira: R$ 1.234,56
 */
function formatBRL(value) {
  if (value === null || value === undefined || value === '') return 'R$ 0,00';
  const num = parseFloat(String(value).replace(/\./g, '').replace(',', '.'));
  if (isNaN(num)) return 'R$ 0,00';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

/**
 * Formata CNPJ: XX.XXX.XXX/XXXX-XX
 */
function formatCNPJ(cnpj) {
  const digits = String(cnpj).replace(/\D/g, '');
  return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
}

/**
 * Formata CPF: XXX.XXX.XXX-XX
 */
function formatCPF(cpf) {
  const digits = String(cpf).replace(/\D/g, '');
  return digits.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
}

const BORDER_NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const BORDER_THIN = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const BORDER_THICK = { style: BorderStyle.SINGLE, size: 8, color: '000000' };
const NO_BORDERS = { top: BORDER_NONE, bottom: BORDER_NONE, left: BORDER_NONE, right: BORDER_NONE };
const ALL_BORDERS = { top: BORDER_THIN, bottom: BORDER_THIN, left: BORDER_THIN, right: BORDER_THIN };

function cell(text, opts = {}) {
  const {
    bold = false, size = 16, italic = false, underline = false,
    align = AlignmentType.LEFT, shading = null, colSpan = 1,
    width = null, borders = ALL_BORDERS, verticalAlign = VerticalAlign.CENTER,
    color = '000000', smallCaps = false
  } = opts;

  const runs = Array.isArray(text)
    ? text
    : [new TextRun({
        text: String(text ?? ''),
        bold, size, italic, underline: underline ? {} : undefined,
        color, smallCaps
      })];

  const cellProps = {
    borders,
    verticalAlign,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    columnSpan: colSpan,
    children: [new Paragraph({ alignment: align, children: runs })]
  };

  if (width) cellProps.width = { size: width, type: WidthType.DXA };
  if (shading) cellProps.shading = { fill: shading, type: ShadingType.CLEAR };

  return new TableCell(cellProps);
}

function row(...cells) {
  return new TableRow({ children: cells });
}

function labelValue(label, value, opts = {}) {
  return [
    cell(label, { bold: true, size: 14, borders: NO_BORDERS, ...opts }),
    cell(value, { size: 16, borders: NO_BORDERS, ...opts }),
  ];
}

/**
 * Gera o .docx do Informe de Rendimentos
 * @param {object} dados - Dados do informe
 * @param {string} outputPath - Caminho de saída do arquivo
 */
async function gerarInforme(dados, outputPath) {
  const {
    anoCalendario = new Date().getFullYear() - 1,
    fontePagadora = {},
    beneficiario = {},
    rendimentos = {},
    responsavel = {
      nome: 'NELSON FERNANDES DE SOUZA JUNIOR',
      data: '28.02.2026'
    }
  } = dados;

  const PAGE_W = 11906; // A4 em DXA
  const MARGIN = 567;   // ~1cm
  const CONTENT_W = PAGE_W - MARGIN * 2;

  // Cabeçalho azul escuro
  const headerTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell(
        [
          new TextRun({ text: 'COMPROVANTE ANUAL DE RENDIMENTOS PAGOS OU CREDITADOS', bold: true, size: 22, color: 'FFFFFF' }),
          new TextRun({ text: '\n', break: 1 }),
          new TextRun({ text: `ANO-CALENDÁRIO: ${anoCalendario}`, bold: true, size: 18, color: 'FFFFFF' }),
        ],
        {
          shading: '1F3864', width: CONTENT_W, borders: NO_BORDERS,
          align: AlignmentType.CENTER,
        }
      ))
    ]
  });

  // Seção 1 - Fonte Pagadora
  const secaoFontePagadora = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell('1. FONTE PAGADORA', {
        bold: true, size: 17, shading: 'D9E1F2', width: CONTENT_W,
        borders: { top: BORDER_THIN, bottom: BORDER_THIN, left: BORDER_THIN, right: BORDER_THIN }
      })),
    ]
  });

  const halfW = Math.floor(CONTENT_W / 2);
  const col3 = Math.floor(CONTENT_W / 3);

  const fontePagadoraTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [col3 * 2, col3],
    rows: [
      new TableRow({
        children: [
          cell('RAZÃO SOCIAL / NOME EMPRESARIAL', { bold: true, size: 14, shading: 'EEF2F9', width: col3 * 2 }),
          cell('CNPJ / CPF', { bold: true, size: 14, shading: 'EEF2F9', width: col3 }),
        ]
      }),
      new TableRow({
        children: [
          cell(fontePagadora.razaoSocial || '', { size: 17, bold: true, width: col3 * 2 }),
          cell(formatCNPJ(fontePagadora.cnpj || ''), { size: 17, width: col3 }),
        ]
      }),
    ]
  });

  // Seção 2 - Beneficiário
  const secaoBeneficiario = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell('2. BENEFICIÁRIO', {
        bold: true, size: 17, shading: 'D9E1F2', width: CONTENT_W,
      })),
    ]
  });

  const beneficiarioTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [col3 * 2, col3],
    rows: [
      new TableRow({
        children: [
          cell('NOME COMPLETO', { bold: true, size: 14, shading: 'EEF2F9', width: col3 * 2 }),
          cell('CPF', { bold: true, size: 14, shading: 'EEF2F9', width: col3 }),
        ]
      }),
      new TableRow({
        children: [
          cell(beneficiario.nome || '', { size: 17, bold: true, width: col3 * 2 }),
          cell(formatCPF(beneficiario.cpf || ''), { size: 17, width: col3 }),
        ]
      }),
    ]
  });

  // Seção 3 - Rendimentos Tributáveis
  const secao3 = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell('3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO SOBRE A RENDA RETIDO NA FONTE', {
        bold: true, size: 17, shading: 'D9E1F2', width: CONTENT_W,
      })),
    ]
  });

  const col4 = Math.floor(CONTENT_W / 4);
  const col4r = CONTENT_W - col4 * 3;

  const rendTributaveisTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [col4, col4, col4, col4r],
    rows: [
      new TableRow({
        children: [
          cell('RENDIMENTOS TRIBUTÁVEIS\n(R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col4, align: AlignmentType.CENTER }),
          cell('CONTRIBUIÇÃO\nPREVIDENCIÁRIA (INSS)\n(R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col4, align: AlignmentType.CENTER }),
          cell('OUTRAS DEDUÇÕES\n(R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col4, align: AlignmentType.CENTER }),
          cell('IMPOSTO RETIDO\nNA FONTE (R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col4r, align: AlignmentType.CENTER }),
        ]
      }),
      new TableRow({
        children: [
          cell(formatBRL(rendimentos.tributaveis), { size: 17, width: col4, align: AlignmentType.RIGHT }),
          cell(formatBRL(rendimentos.inss), { size: 17, width: col4, align: AlignmentType.RIGHT }),
          cell(formatBRL(rendimentos.outrasDeducoes), { size: 17, width: col4, align: AlignmentType.RIGHT }),
          cell(formatBRL(rendimentos.irrf), { size: 17, width: col4r, align: AlignmentType.RIGHT }),
        ]
      }),
    ]
  });

  // Seção 4 - Rendimentos Isentos
  const secao4 = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell('4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS', {
        bold: true, size: 17, shading: 'D9E1F2', width: CONTENT_W,
      })),
    ]
  });

  const col2 = Math.floor(CONTENT_W / 2);
  const rendIsentosTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [col2, CONTENT_W - col2],
    rows: [
      new TableRow({
        children: [
          cell('LUCROS E DIVIDENDOS\nDISTRIBUÍDOS (R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col2, align: AlignmentType.CENTER }),
          cell('OUTROS RENDIMENTOS\nISENTOS (R$)', { bold: true, size: 14, shading: 'EEF2F9', width: CONTENT_W - col2, align: AlignmentType.CENTER }),
        ]
      }),
      new TableRow({
        children: [
          cell(formatBRL(rendimentos.lucrosDividendos), { size: 17, width: col2, align: AlignmentType.RIGHT }),
          cell(formatBRL(rendimentos.outrosIsentos), { size: 17, width: CONTENT_W - col2, align: AlignmentType.RIGHT }),
        ]
      }),
    ]
  });

  // Seção 5 - Plano de Saúde
  const secao5 = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell('5. PLANO DE SAÚDE COLETIVO EMPRESARIAL', {
        bold: true, size: 17, shading: 'D9E1F2', width: CONTENT_W,
      })),
    ]
  });

  const planoSaudeTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [col2, CONTENT_W - col2],
    rows: [
      new TableRow({
        children: [
          cell('VALORES PAGOS PELO\nBENEFICIÁRIO (R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col2, align: AlignmentType.CENTER }),
          cell('VALORES PAGOS PELA\nFONTE PAGADORA (R$)', { bold: true, size: 14, shading: 'EEF2F9', width: CONTENT_W - col2, align: AlignmentType.CENTER }),
        ]
      }),
      new TableRow({
        children: [
          cell(formatBRL(rendimentos.planoBeneficiario), { size: 17, width: col2, align: AlignmentType.RIGHT }),
          cell(formatBRL(rendimentos.planoFontePagadora), { size: 17, width: CONTENT_W - col2, align: AlignmentType.RIGHT }),
        ]
      }),
    ]
  });

  // Seção 6 - 13° Salário
  const secao6 = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell('6. DÉCIMO TERCEIRO SALÁRIO', {
        bold: true, size: 17, shading: 'D9E1F2', width: CONTENT_W,
      })),
    ]
  });

  const col3a = Math.floor(CONTENT_W / 3);
  const treceTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [col3a, col3a, CONTENT_W - col3a * 2],
    rows: [
      new TableRow({
        children: [
          cell('RENDIMENTOS TRIBUTÁVEIS\n(R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col3a, align: AlignmentType.CENTER }),
          cell('CONTRIBUIÇÃO PREVIDENCIÁRIA\n(INSS) (R$)', { bold: true, size: 14, shading: 'EEF2F9', width: col3a, align: AlignmentType.CENTER }),
          cell('IMPOSTO RETIDO NA\nFONTE (R$)', { bold: true, size: 14, shading: 'EEF2F9', width: CONTENT_W - col3a * 2, align: AlignmentType.CENTER }),
        ]
      }),
      new TableRow({
        children: [
          cell(formatBRL(rendimentos.trezeRendimentos), { size: 17, width: col3a, align: AlignmentType.RIGHT }),
          cell(formatBRL(rendimentos.trezeInss), { size: 17, width: col3a, align: AlignmentType.RIGHT }),
          cell(formatBRL(rendimentos.trezeIrrf), { size: 17, width: CONTENT_W - col3a * 2, align: AlignmentType.RIGHT }),
        ]
      }),
    ]
  });

  // Seção 7 - Responsável
  const secao7 = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell('7. RESPONSÁVEL PELAS INFORMAÇÕES', {
        bold: true, size: 17, shading: 'D9E1F2', width: CONTENT_W,
      })),
    ]
  });

  const responsavelTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [col2, CONTENT_W - col2],
    rows: [
      new TableRow({
        children: [
          cell('NOME COMPLETO', { bold: true, size: 14, shading: 'EEF2F9', width: col2 }),
          cell('DATA', { bold: true, size: 14, shading: 'EEF2F9', width: CONTENT_W - col2 }),
        ]
      }),
      new TableRow({
        children: [
          cell(responsavel.nome, { size: 17, bold: true, width: col2 }),
          cell(responsavel.data, { size: 17, width: CONTENT_W - col2 }),
        ]
      }),
    ]
  });

  // Rodapé com nota
  const rodape = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [
      row(cell(
        [new TextRun({
          text: 'Este comprovante é válido como documento para a Declaração de Ajuste Anual do Imposto sobre a Renda da Pessoa Física - DIRPF, conforme art. 16 da Instrução Normativa RFB nº 1.215, de 15 de dezembro de 2011.',
          size: 14, italic: true, color: '444444'
        })],
        { shading: 'F5F5F5', width: CONTENT_W, borders: { top: BORDER_THIN, bottom: BORDER_NONE, left: BORDER_NONE, right: BORDER_NONE } }
      ))
    ]
  });

  const p = (spacing = 80) => new Paragraph({ spacing: { before: spacing, after: 0 } });

  const doc = new Document({
    sections: [{
      properties: {
        page: {
          size: { width: PAGE_W, height: 16838 },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }
        }
      },
      children: [
        headerTable,
        p(100),
        secaoFontePagadora,
        fontePagadoraTable,
        p(120),
        secaoBeneficiario,
        beneficiarioTable,
        p(120),
        secao3,
        rendTributaveisTable,
        p(120),
        secao4,
        rendIsentosTable,
        p(120),
        secao5,
        planoSaudeTable,
        p(120),
        secao6,
        treceTable,
        p(120),
        secao7,
        responsavelTable,
        p(160),
        rodape,
      ]
    }]
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`✅ Informe gerado: ${outputPath}`);
}

module.exports = { gerarInforme };

// Execução direta para teste
if (require.main === module) {
  const dadosTeste = {
    anoCalendario: 2025,
    fontePagadora: {
      razaoSocial: 'EMPRESA EXEMPLO LTDA',
      cnpj: '12345678000195',
    },
    beneficiario: {
      nome: 'JOÃO DA SILVA SOUZA',
      cpf: '12345678901',
    },
    rendimentos: {
      tributaveis: '84000,00',
      inss: '7786,00',
      outrasDeducoes: '0,00',
      irrf: '4200,00',
      lucrosDividendos: '120000,00',
      outrosIsentos: '0,00',
      planoBeneficiario: '0,00',
      planoFontePagadora: '3600,00',
      trezeRendimentos: '7000,00',
      trezeInss: '648,83',
      trezeIrrf: '0,00',
    },
    responsavel: {
      nome: 'NELSON FERNANDES DE SOUZA JUNIOR',
      data: '28.02.2026'
    }
  };

  gerarInforme(dadosTeste, '/home/claude/informe-rendimentos/teste_informe.docx')
    .catch(console.error);
}
