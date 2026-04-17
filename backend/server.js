/**
 * server.js — Informe de Rendimentos
 */

const express  = require('express');
const cors     = require('cors');
const multer   = require('multer');
const path     = require('path');
const fs       = require('fs');
const { execFile } = require('child_process');
const AdmZip   = require('adm-zip');

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
    if (!ok) console.log('❌ Arquivo rejeitado pelo filtro:', file.originalname);
    cb(ok ? null : new Error('Apenas arquivos .xlsx são aceitos'), !!ok);
  },
  limits: { fileSize: 10 * 1024 * 1024 },
});

function runPython(script, args) {
  return new Promise((resolve, reject) => {
    console.log(`🐍 Executando Python: ${script} ${args.join(' ')}`);
    execFile('python3', [path.join(__dirname, script), ...args], { timeout: 120000 }, (err, stdout, stderr) => {
      if (err) {
        console.error(`❌ Erro Python (${script}):`, stderr || err.message);
        return reject(new Error(stderr || err.message));
      }
      console.log(`✅ Python OK (${script})`);
      resolve(stdout);
    });
  });
}

function slugify(str) {
  return (str || 'arquivo').toUpperCase().replace(/[^A-Z0-9]/g, '_').replace(/_+/g, '_').slice(0, 40);
}

function cleanup(...files) {
  for (const f of files) {
    try { if (f && fs.existsSync(f)) { fs.unlinkSync(f); console.log(`🧹 Limpo: ${f}`); } } catch (_) {}
  }
}

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/modelo-excel', async (req, res) => {
  const outPath = path.join(TEMP, `modelo_${Date.now()}.xlsx`);
  console.log(`📥 Gerando modelo Excel: ${outPath}`);
  try {
    await runPython('gerarModeloExcel.py', [outPath]);
    const stats = fs.statSync(outPath);
    console.log(`📊 Modelo gerado: ${stats.size} bytes`);
    if (stats.size < 1000) throw new Error('Arquivo modelo gerado está vazio ou corrompido');
    res.download(outPath, 'Modelo_Importacao_Informes.xlsx', (err) => {
      if (err) console.error('❌ Erro no download:', err);
      cleanup(outPath);
    });
  } catch (err) {
    console.error('❌ Erro ao gerar modelo:', err);
    cleanup(outPath);
    res.status(500).json({ erro: 'Erro ao gerar modelo Excel', detalhes: err.message });
  }
});

app.post('/api/informe/gerar-pdf', async (req, res) => {
  const dados = req.body;
  if (!dados.fontePagadora?.cnpj || !dados.beneficiario?.nome) {
    return res.status(400).json({ erro: 'Dados incompletos' });
  }
  const ts = Date.now();
  const jsonPath = path.join(TEMP, `dados_${ts}.json`);
  const pdfPath  = path.join(TEMP, `informe_${ts}.pdf`);
  try {
    fs.writeFileSync(jsonPath, JSON.stringify(dados));
    await runPython('gerarPDF.py', [jsonPath, pdfPath]);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="Informe_${slugify(dados.beneficiario.nome)}_${dados.anoCalendario || ''}.pdf"`);
    res.download(pdfPath, `Informe_${slugify(dados.beneficiario.nome)}_${dados.anoCalendario || ''}.pdf`, (err) => {
      if (err) console.error('❌ Erro no download:', err);
      cleanup(jsonPath, pdfPath);
    });
  } catch (err) {
    console.error('❌ Erro ao gerar PDF:', err);
    cleanup(jsonPath, pdfPath);
    res.status(500).json({ erro: 'Erro ao gerar PDF', detalhes: err.message });
  }
});

app.post('/api/lote/preview', upload.single('arquivo'), async (req, res) => {
  console.log('\n📤 === UPLOAD RECEBIDO ===');
  if (!req.file) {
    console.log('❌ Nenhum arquivo recebido');
    return res.status(400).json({ erro: 'Arquivo não enviado' });
  }
  const xlsxPath = req.file.path;
  console.log('📋 Informações do arquivo:');
  console.log('  - Nome original:', req.file.originalname);
  console.log('  - Caminho salvo:', xlsxPath);
  console.log('  - Tamanho reportado:', req.file.size, 'bytes');
  try {
    if (!fs.existsSync(xlsxPath)) throw new Error(`Arquivo não encontrado no disco: ${xlsxPath}`);
    const stats = fs.statSync(xlsxPath);
    console.log('  - Tamanho no disco:', stats.size, 'bytes');
    if (stats.size === 0) throw new Error('Arquivo está vazio (0 bytes)');
    const buffer = fs.readFileSync(xlsxPath);
    const header = buffer.slice(0, 4).toString('hex');
    console.log('  - Header do arquivo (hex):', header);
    const isValidXlsx = header === '504b0304';
    console.log('  - É .xlsx válido?', isValidXlsx ? '✅ SIM' : '❌ NÃO');
    if (!isValidXlsx) {
      const preview = buffer.slice(0, 100).toString('utf-8').replace(/[^\x20-\x7E]/g, '.');
      console.log('  - Preview do conteúdo:', preview);
      throw new Error(`Arquivo não é um .xlsx válido (header: ${header})`);
    }
    console.log('🐍 Chamando parseExcel.py...');
    const stdout = await runPython('parseExcel.py', [xlsxPath]);
    const resultado = JSON.parse(stdout);
    console.log(`✅ Preview processado: ${resultado.total || 0} registros encontrados`);
    console.log('='.repeat(50) + '\n');
    res.json(resultado);
  } catch (err) {
    console.error('❌ ERRO NO PROCESSAMENTO:', err.message);
    console.log('='.repeat(50) + '\n');
    res.status(500).json({ 
      erro: 'Erro ao processar Excel', 
      detalhes: err.message,
      debug: {
        nomeOriginal: req.file.originalname,
        tamanhoReportado: req.file.size,
        caminho: xlsxPath
      }
    });
  } finally {
    cleanup(xlsxPath);
  }
});

app.post('/api/lote/gerar', async (req, res) => {
  const { socios } = req.body;
  if (!Array.isArray(socios) || socios.length === 0) return res.status(400).json({ erro: 'Nenhum sócio informado' });
  
  console.log(`\n📦 Gerando lote com ${socios.length} sócios...`);
  
  const ts = Date.now();
  const dirLote = path.join(TEMP, `lote_${ts}`);
  const zipPath = path.join(TEMP, `informes_${ts}.zip`);
  fs.mkdirSync(dirLote);
  const erros = [];
  
  try {
    for (let i = 0; i < socios.length; i++) {
      const s = socios[i];
      const jsonPath = path.join(dirLote, `dados_${i}.json`);
      const nomeSocio = slugify(s.beneficiario?.nome || `socio_${i+1}`);
      const pdfPath = path.join(dirLote, `${String(i+1).padStart(3,'0')}_${nomeSocio}.pdf`);
      
      try {
        fs.writeFileSync(jsonPath, JSON.stringify(s));
        await runPython('gerarPDF.py', [jsonPath, pdfPath]);
        console.log(`  ✅ [${i+1}/${socios.length}] PDF gerado: ${nomeSocio}`);
        cleanup(jsonPath);
      } catch (err) {
        console.error(`  ❌ [${i+1}/${socios.length}] Erro: ${s.beneficiario?.nome} - ${err.message}`);
        erros.push({ socio: s.beneficiario?.nome || `#${i+1}`, erro: err.message });
        cleanup(jsonPath);
      }
    }
    
    if (erros.length > 0) {
      fs.writeFileSync(path.join(dirLote, 'ERROS.txt'), erros.map(e => `${e.socio}: ${e.erro}`).join('\n'));
      console.log(`⚠️ ${erros.length} erro(s) registrados`);
    }
    
    console.log(`🗜️ Compactando ZIP com adm-zip...`);
    const zip = new AdmZip();
    zip.addLocalFolder(dirLote);
    zip.writeZip(zipPath);
    
    console.log(`✅ Lote concluído: ${zipPath} (${fs.statSync(zipPath).size} bytes)`);
    
    res.download(zipPath, `Informes_Lote_${new Date().toISOString().slice(0,10)}.zip`, (err) => {
      if (err) console.error('❌ Erro no download:', err);
      cleanup(zipPath);
      fs.rmSync(dirLote, { recursive: true, force: true });
    });
  } catch (err) {
    console.error('❌ Erro ao gerar lote:', err);
    fs.rmSync(dirLote, { recursive: true, force: true });
    cleanup(zipPath);
    res.status(500).json({ erro: 'Erro ao gerar lote', detalhes: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`\n🚀 Servidor rodando na porta ${PORT}`);
  console.log('📋 Endpoints disponíveis:');
  console.log('  GET  /api/health');
  console.log('  GET  /api/modelo-excel');
  console.log('  POST /api/informe/gerar-pdf');
  console.log('  POST /api/lote/preview');
  console.log('  POST /api/lote/gerar\n');
});