/**
 * server.js — Informe de Rendimentos
 *
 * Instalar:
 *   npm install express cors multer
 *
 * Rodar:
 *   node server.js
 */

const express  = require('express');
const cors     = require('cors');
const multer   = require('multer');
const path     = require('path');
const fs       = require('fs');
const { execFile, exec } = require('child_process');
const { gerarInforme }   = require('./gerarInforme');

const app    = express();
const PORT   = process.env.PORT || 3001;
const TEMP   = path.join(__dirname, 'temp');

if (!fs.existsSync(TEMP)) fs.mkdirSync(TEMP);

app.use(cors());
app.use(express.json({ limit: '10mb' }));

const upload = multer({
  dest: TEMP,
  fileFilter: (req, file, cb) => {
    const ok = file.originalname.match(/\.(xlsx|xls)$/i);
    cb(ok ? null : new Error('Apenas arquivos .xlsx são aceitos'), !!ok);
  },
  limits: { fileSize: 10 * 1024 * 1024 },
});

function runPython(script, args) {
  return new Promise((resolve, reject) => {
    execFile('python3', [path.join(__dirname, script), ...args], { timeout: 120000 }, (err, stdout, stderr) => {
      if (err) return reject(new Error(stderr || err.message));
      resolve(stdout);
    });
  });
}

function slugify(str) {
  return (str || 'arquivo').toUpperCase().replace(/[^A-Z0-9]/g, '_').replace(/_+/g, '_').slice(0, 40);
}

function cleanup(...files) {
  for (const f of files) {
    try { if (f && fs.existsSync(f)) fs.unlinkSync(f); } catch (_) {}
  }
}

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/modelo-excel', async (req, res) => {
  const outPath = path.join(TEMP, `modelo_${Date.now()}.xlsx`);
  try {
    await runPython('gerarModeloExcel.py', [outPath]);
    res.download(outPath, 'Modelo_Importacao_Informes.xlsx', () => cleanup(outPath));
  } catch (err) {
    cleanup(outPath);
    res.status(500).json({ erro: 'Erro ao gerar modelo Excel', detalhes: err.message });
  }
});

app.post('/api/informe/gerar', async (req, res) => {
  const dados = req.body;
  dados.responsavel = { nome: 'NELSON FERNANDES DE SOUZA JUNIOR', data: '28.02.2026' };
  if (!dados.fontePagadora?.cnpj) return res.status(400).json({ erro: 'CNPJ obrigatório' });
  if (!dados.fontePagadora?.razaoSocial) return res.status(400).json({ erro: 'Razão Social obrigatória' });
  if (!dados.beneficiario?.nome) return res.status(400).json({ erro: 'Nome do beneficiário obrigatório' });
  if (!dados.beneficiario?.cpf) return res.status(400).json({ erro: 'CPF obrigatório' });
  const docxPath = path.join(TEMP, `informe_${Date.now()}.docx`);
  try {
    await gerarInforme(dados, docxPath);
    res.download(docxPath, `Informe_${slugify(dados.beneficiario.nome)}_${dados.anoCalendario || ''}.docx`, () => cleanup(docxPath));
  } catch (err) {
    cleanup(docxPath);
    res.status(500).json({ erro: 'Erro ao gerar informe', detalhes: err.message });
  }
});

app.post('/api/informe/gerar-pdf', async (req, res) => {
  const dados = req.body;
  dados.responsavel = { nome: 'NELSON FERNANDES DE SOUZA JUNIOR', data: '28.02.2026' };
  if (!dados.fontePagadora?.cnpj || !dados.beneficiario?.nome) return res.status(400).json({ erro: 'Dados incompletos' });
  const ts = Date.now();
  const jsonPath = path.join(TEMP, `dados_${ts}.json`);
  const pdfPath  = path.join(TEMP, `informe_${ts}.pdf`);
  try {
    fs.writeFileSync(jsonPath, JSON.stringify(dados));
    await runPython('gerarPDF.py', [jsonPath, pdfPath]);
    res.download(pdfPath, `Informe_${slugify(dados.beneficiario.nome)}_${dados.anoCalendario || ''}.pdf`, () => cleanup(jsonPath, pdfPath));
  } catch (err) {
    cleanup(jsonPath, pdfPath);
    res.status(500).json({ erro: 'Erro ao gerar PDF', detalhes: err.message });
  }
});

app.post('/api/lote/preview', upload.single('arquivo'), async (req, res) => {
  if (!req.file) return res.status(400).json({ erro: 'Arquivo não enviado' });
  const xlsxPath = req.file.path;
  try {
    const stdout = await runPython('parseExcel.py', [xlsxPath]);
    res.json(JSON.parse(stdout));
  } catch (err) {
    res.status(500).json({ erro: 'Erro ao processar Excel', detalhes: err.message });
  } finally {
    cleanup(xlsxPath);
  }
});

app.post('/api/lote/gerar', async (req, res) => {
  const { socios } = req.body;
  if (!Array.isArray(socios) || socios.length === 0) return res.status(400).json({ erro: 'Nenhum sócio informado' });
  const ts      = Date.now();
  const dirLote = path.join(TEMP, `lote_${ts}`);
  const zipPath = path.join(TEMP, `informes_${ts}.zip`);
  fs.mkdirSync(dirLote);
  const erros = [];
  try {
    for (let i = 0; i < socios.length; i++) {
      const s = socios[i];
      s.responsavel = { nome: 'NELSON FERNANDES DE SOUZA JUNIOR', data: '28.02.2026' };
      const jsonPath = path.join(dirLote, `dados_${i}.json`);
      const nomeSocio = slugify(s.beneficiario?.nome || `socio_${i+1}`);
      const pdfPath   = path.join(dirLote, `${String(i+1).padStart(3,'0')}_${nomeSocio}.pdf`);
      try {
        fs.writeFileSync(jsonPath, JSON.stringify(s));
        await runPython('gerarPDF.py', [jsonPath, pdfPath]);
        cleanup(jsonPath);
      } catch (err) {
        erros.push({ socio: s.beneficiario?.nome || `#${i+1}`, erro: err.message });
        cleanup(jsonPath);
      }
    }
    if (erros.length > 0) {
      fs.writeFileSync(path.join(dirLote, 'ERROS.txt'), erros.map(e => `${e.socio}: ${e.erro}`).join('\n'));
    }
    await new Promise((resolve, reject) => {
      exec(`cd "${dirLote}" && zip -r "${zipPath}" .`, err => err ? reject(err) : resolve());
    });
    res.download(zipPath, `Informes_Lote_${new Date().toISOString().slice(0,10)}.zip`, () => {
      cleanup(zipPath);
      fs.rmSync(dirLote, { recursive: true, force: true });
    });
  } catch (err) {
    fs.rmSync(dirLote, { recursive: true, force: true });
    cleanup(zipPath);
    res.status(500).json({ erro: 'Erro ao gerar lote', detalhes: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`\n Servidor: http://localhost:${PORT}`);
  console.log('  GET  /api/health');
  console.log('  GET  /api/modelo-excel');
  console.log('  POST /api/informe/gerar');
  console.log('  POST /api/informe/gerar-pdf');
  console.log('  POST /api/lote/preview');
  console.log('  POST /api/lote/gerar\n');
});
