const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, AlignmentType, BorderStyle, WidthType, ShadingType, VerticalAlign } = require('docx');
const fs = require('fs');

function formatBRL(value) {
  if (value === null || value === undefined || value === '') return '0,00';
  const num = parseFloat(String(value).replace(/\./g, '').replace(',', '.'));
  if (isNaN(num)) return '0,00';
  return num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatCNPJ(cnpj) {
  const digits = String(cnpj).replace(/\D/g, '');
  return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
}

function formatCPF(cpf) {
  const digits = String(cpf).replace(/\D/g, '');
  return digits.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
}

const BORDER_NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const BORDER_THIN = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const NO_BORDERS = { top: BORDER_NONE, bottom: BORDER_NONE, left: BORDER_NONE, right: BORDER_NONE };
const ALL_BORDERS = { top: BORDER_THIN, bottom: BORDER_THIN, left: BORDER_THIN, right: BORDER_THIN };

function cell(text, opts = {}) {
  const { bold = false, size = 16, align = AlignmentType.LEFT, shading = null, colSpan = 1, borders = ALL_BORDERS, verticalAlign = VerticalAlign.CENTER, color = '000000' } = opts;
  const runs = Array.isArray(text) ? text : [new TextRun({ text: String(text ?? ''), bold, size, color })];
  return new TableCell({
    borders, verticalAlign, margins: { top: 40, bottom: 40, left: 80, right: 80 }, columnSpan: colSpan,
    shading: shading ? { fill: shading, type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ alignment: align, children: runs })]
  });
}

function row(...cells) { return new TableRow({ children: cells }); }

async function gerarInforme(dados, outputPath) {
  const {
    exercicio = new Date().getFullYear() + 1,
    anoCalendario = exercicio - 1,
    fontePagadora = {},
    beneficiario = {},
    rendimentos = {},
    responsavel = {}
  } = dados;

  const PAGE_W = 11906; const MARGIN = 567; const CONTENT_W = PAGE_W - MARGIN * 2;
  const half = Math.floor(CONTENT_W / 2);

  // Cabeçalho Ministério da Fazenda
  const headerTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
    rows: [
      row(cell([new TextRun({ text: 'MINISTÉRIO DA FAZENDA', bold: true, size: 24 })], { borders: NO_BORDERS, align: AlignmentType.CENTER })),
      row(cell([new TextRun({ text: 'SECRETARIA DA RECEITA FEDERAL DO BRASIL', bold: true, size: 20 })], { borders: NO_BORDERS, align: AlignmentType.CENTER })),
      row(cell([new TextRun({ text: 'IMPOSTO SOBRE A RENDA DA PESSOA FÍSICA', bold: true, size: 20 })], { borders: NO_BORDERS, align: AlignmentType.CENTER }))
    ]
  });

  // Linha Exercício / Ano-Calendário
  const periodoTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [half, half],
    rows: [new TableRow({
      children: [
        cell([new TextRun({ text: `Exercício de ${exercicio}`, bold: true, size: 20 })], { borders: NO_BORDERS, align: AlignmentType.LEFT }),
        cell([new TextRun({ text: `Ano-Calendário ${anoCalendario}`, bold: true, size: 20 })], { borders: NO_BORDERS, align: AlignmentType.RIGHT })
      ]
    })]
  });

  const tituloTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
    rows: [row(cell([new TextRun({ text: 'Comprovante de Rendimentos Pagos e de Imposto sobre a Renda Retido na Fonte', bold: true, size: 22 })], { borders: NO_BORDERS, align: AlignmentType.CENTER }))]
  });

  // Seção 1
  const secao1Title = new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [row(cell('1. FONTE PAGADORA PESSOA JURÍDICA OU PESSOA FÍSICA', { bold: true, size: 18, shading: 'D9D9D9' }))] });
  const fonteTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [Math.floor(CONTENT_W * 0.7), Math.floor(CONTENT_W * 0.3)],
    rows: [
      new TableRow({ children: [cell('Nome Empresarial/Nome Completo', { bold: true, size: 16, shading: 'EEEEEE' }), cell('CNPJ/CPF', { bold: true, size: 16, shading: 'EEEEEE' })] }),
      new TableRow({ children: [cell(fontePagadora.razaoSocial || '', { size: 18 }), cell(formatCNPJ(fontePagadora.cnpj || ''), { size: 18 })] })
    ]
  });

  // Seção 2
  const secao2Title = new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [row(cell('2. PESSOA FÍSICA BENEFICIÁRIA DOS RENDIMENTOS', { bold: true, size: 18, shading: 'D9D9D9' }))] });
  const benefTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [Math.floor(CONTENT_W * 0.3), Math.floor(CONTENT_W * 0.7)],
    rows: [
      new TableRow({ children: [cell('CPF', { bold: true, size: 16, shading: 'EEEEEE' }), cell('Nome Completo', { bold: true, size: 16, shading: 'EEEEEE' })] }),
      new TableRow({ children: [cell(formatCPF(beneficiario.cpf || ''), { size: 18 }), cell(beneficiario.nome || '', { size: 18 })] }),
      row(cell('Natureza do Rendimento: Assalariado', { colSpan: 2, size: 16 }))
    ]
  });

  // Seção 3
  const secao3Title = new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [row(cell('3. RENDIMENTOS TRIBUTÁVEIS, DEDUÇÕES E IMPOSTO RETIDO NA FONTE', { bold: true, size: 18, shading: 'D9D9D9' }))] });
  const rendTribTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W - 1000, 1000],
    rows: [
      new TableRow({ children: [cell('01 - Total dos Rendimentos (inclusive Férias)', { size: 16 }), cell(formatBRL(rendimentos.tributaveis), { align: AlignmentType.RIGHT, size: 18 })] }),
      new TableRow({ children: [cell('02 - Contribuição Previdenciária Oficial', { size: 16 }), cell(formatBRL(rendimentos.inss), { align: AlignmentType.RIGHT, size: 18 })] }),
      new TableRow({ children: [cell('03 - Contribuição a entidades de previdência complementar / FAPI', { size: 16 }), cell('0,00', { align: AlignmentType.RIGHT, size: 18 })] }),
      new TableRow({ children: [cell('04 - Pensão Alimentícia', { size: 16 }), cell(formatBRL(rendimentos.outrasDeducoes), { align: AlignmentType.RIGHT, size: 18 })] }),
      new TableRow({ children: [cell('05 - Imposto sobre a renda retido na fonte', { size: 16 }), cell(formatBRL(rendimentos.irrf), { align: AlignmentType.RIGHT, size: 18 })] })
    ]
  });

  // Seção 4
  const secao4Title = new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [row(cell('4. RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS', { bold: true, size: 18, shading: 'D9D9D9' }))] });
  const rendIsentosTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W - 1000, 1000],
    rows: [
      new TableRow({ children: [cell('04 - Lucros e Dividendos pagos por PJ', { size: 16 }), cell(formatBRL(rendimentos.lucrosDividendos), { align: AlignmentType.RIGHT, size: 18 })] }),
      new TableRow({ children: [cell('07 - Outros (especifique)', { size: 16 }), cell(formatBRL(rendimentos.outrosIsentos), { align: AlignmentType.RIGHT, size: 18 })] })
    ]
  });

  // Seção 5
  const secao5Title = new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [row(cell('5. RENDIMENTOS SUJEITOS À TRIBUTAÇÃO EXCLUSIVA (RENDIMENTO LÍQUIDO)', { bold: true, size: 18, shading: 'D9D9D9' }))] });
  const trezeTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W - 1000, 1000],
    rows: [
      new TableRow({ children: [cell('01 - 13º (décimo terceiro) salário', { size: 16 }), cell(formatBRL(rendimentos.trezeRendimentos), { align: AlignmentType.RIGHT, size: 18 })] }),
      new TableRow({ children: [cell('02 - Imposto sobre a renda retido na fonte sobre 13º', { size: 16 }), cell(formatBRL(rendimentos.trezeIrrf), { align: AlignmentType.RIGHT, size: 18 })] })
    ]
  });

  // Seção 8
  const secao8Title = new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [row(cell('8. RESPONSÁVEL PELAS INFORMAÇÕES', { bold: true, size: 18, shading: 'D9D9D9' }))] });
  const respTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [Math.floor(CONTENT_W * 0.5), Math.floor(CONTENT_W * 0.25), Math.floor(CONTENT_W * 0.25)],
    rows: [
      new TableRow({ children: [cell('Nome', { bold: true, size: 16, shading: 'EEEEEE' }), cell('Data', { bold: true, size: 16, shading: 'EEEEEE' }), cell('Assinatura', { bold: true, size: 16, shading: 'EEEEEE' })] }),
      new TableRow({ children: [cell(responsavel.nome || 'Não informado', { size: 16 }), cell(responsavel.data || '  /  /    ', { size: 16 }), cell('Isento conforme IN RFB 1215/2011', { size: 14 })] })
    ]
  });

  const doc = new Document({
    sections: [{
      properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
      children: [
        headerTable, new Paragraph({ spacing: { before: 200, after: 100 } }), periodoTable, new Paragraph({ spacing: { after: 150 } }), tituloTable, new Paragraph({ spacing: { after: 200 } }),
        secao1Title, fonteTable, new Paragraph({ spacing: { after: 200 } }),
        secao2Title, benefTable, new Paragraph({ spacing: { after: 200 } }),
        secao3Title, rendTribTable, new Paragraph({ spacing: { after: 200 } }),
        secao4Title, rendIsentosTable, new Paragraph({ spacing: { after: 200 } }),
        secao5Title, trezeTable, new Paragraph({ spacing: { after: 200 } }),
        secao8Title, respTable,
        new Paragraph({ spacing: { before: 300 }, children: [new TextRun({ text: 'Aprovado pela Instrução Normativa RFB nº 2.060, de 13 de dezembro de 2021.', size: 14, italics: true })] })
      ]
    }]
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`✅ Informe DOCX gerado: ${outputPath}`);
}

module.exports = { gerarInforme };