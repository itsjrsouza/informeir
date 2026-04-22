import { useState, useRef } from "react";

const API_URL = import.meta.env.VITE_API_URL;

// ─── Estados do wizard ─────────────────────────────────────────────────────────
const STEPS = {
  UPLOAD:    "upload",
  PREVIEW:   "preview",
  GERANDO:   "gerando",
  CONCLUIDO: "concluido",
};

// ─── Helpers ───────────────────────────────────────────────────────────────────
function fmt(v) {
  if (!v || v === "0,00") return <span style={{ color: "#aaa" }}>—</span>;
  return `R$ ${v}`;
}

function fmtCNPJ(v = "") {
  const d = String(v).replace(/\D/g, "");
  return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5") || v;
}

function fmtCPF(v = "") {
  const d = String(v).replace(/\D/g, "");
  return d.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4") || v;
}

// ─── Componente principal ──────────────────────────────────────────────────────
export default function ImportacaoLote({ onVoltar }) {
  const [step, setStep]           = useState(STEPS.UPLOAD);
  const [arquivo, setArquivo]     = useState(null);
  const [resultado, setResultado] = useState(null);
  const [selecionados, setSel]    = useState([]);
  const [progresso, setProgresso] = useState(0);
  const [erro, setErro]           = useState(null);
  const [zipUrl, setZipUrl]       = useState(null);
  const inputRef                  = useRef();

  async function handleValidar() {
    if (!arquivo) return;
    setErro(null);
    console.log('📤 === VALIDANDO ARQUIVO ===');
    if (!arquivo.name.match(/\.xlsx$/i)) { setErro('O arquivo deve ter extensão .xlsx'); return; }
    if (arquivo.size < 1000) { setErro(`Arquivo muito pequeno (${arquivo.size} bytes).`); return; }

    const form = new FormData();
    form.append("arquivo", arquivo, arquivo.name);
    try {
      const res = await fetch(`${API_URL}/api/lote/preview`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.erro || data.detalhes);
      setResultado(data);
      setSel(data.registros.map((_, i) => i));
      setStep(STEPS.PREVIEW);
    } catch (e) {
      setErro(e.message);
    }
  }

  async function handleGerar() {
    const registrosSelecionados = selecionados.map(i => resultado.registros[i]);
    if (!registrosSelecionados.length) return;
    setStep(STEPS.GERANDO);
    setProgresso(0);
    setErro(null);
    try {
      const interval = setInterval(() => setProgresso(p => Math.min(p + 3, 90)), 300);
      const res = await fetch(`${API_URL}/api/lote/gerar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ socios: registrosSelecionados }),
      });
      clearInterval(interval);
      if (!res.ok) { const data = await res.json(); throw new Error(data.erro); }
      setProgresso(100);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      setZipUrl(url);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Informes_Lote_${new Date().toISOString().slice(0,10)}.zip`;
      document.body.appendChild(a); a.click(); a.remove();
      setStep(STEPS.CONCLUIDO);
    } catch (e) {
      setErro(e.message);
      setStep(STEPS.PREVIEW);
    }
  }

  function handleBaixarModelo() {
    window.open(`${API_URL}/api/modelo-excel`, "_blank");
  }

  function toggleSel(i) {
    setSel(prev => prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i]);
  }
  function toggleTodos() {
    setSel(prev => prev.length === resultado.registros.length ? [] : resultado.registros.map((_, i) => i));
  }

  function handleReset() {
    setStep(STEPS.UPLOAD);
    setArquivo(null);
    setResultado(null);
    setSel([]);
    setErro(null);
    setZipUrl(null);
    setProgresso(0);
  }

  function handleDrop(e) {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f && f.name.endsWith(".xlsx")) { setArquivo(f); setErro(null); }
    else setErro("Apenas arquivos .xlsx são aceitos.");
  }

  async function baixarPDFIndividual(beneficiario, nome) {
    try {
      const payload = { ...beneficiario };
      const res = await fetch(API_URL + "/api/informe/gerar-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Erro ao gerar PDF individual");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Informe_${nome}_${beneficiario.anoCalendario || ''}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Erro ao baixar PDF individual: " + e.message);
    }
  }

  return (
    <>
      <style>{LOTE_CSS}</style>
      <div className="lote-wrapper">
        <div className="lote-breadcrumb">
          <button className="btn-voltar" onClick={onVoltar}>← Formulário Individual</button>
          <span className="breadcrumb-sep">/</span>
          <strong>Importação em Lote</strong>
        </div>

        {step === STEPS.UPLOAD && (
          <div className="lote-card">
            <div className="lote-card-header">
              <span className="lote-icon">📥</span>
              <div><h2>Importação em Lote</h2><p>Suba uma planilha Excel com todos os beneficiários e gere um PDF por pessoa</p></div>
            </div>
            <div className={`drop-area ${arquivo ? "drop-area--ok" : ""}`} onDragOver={e => e.preventDefault()} onDrop={handleDrop} onClick={() => inputRef.current.click()}>
              <input ref={inputRef} type="file" accept=".xlsx" style={{ display: "none" }} onChange={e => { setArquivo(e.target.files[0]); setErro(null); }} />
              {arquivo ? ( <><div className="drop-icon">✅</div><p className="drop-fname">{arquivo.name}</p><p className="drop-hint">{(arquivo.size / 1024).toFixed(1)} KB · clique para trocar</p></> )
              : ( <><div className="drop-icon">📂</div><p className="drop-label">Arraste o arquivo .xlsx aqui</p><p className="drop-hint">ou clique para selecionar</p></> )}
            </div>
            {erro && <div className="lote-erro">⚠️ {erro}</div>}
            <div className="lote-actions">
              <button className="btn-outline" onClick={handleBaixarModelo}>⬇️ Baixar planilha modelo</button>
              <button className="btn-primary" disabled={!arquivo} onClick={handleValidar}>Validar planilha →</button>
            </div>
            <div className="lote-info-box">
              <strong>Colunas obrigatórias:</strong> ANO_CALENDARIO, CNPJ_EMPRESA, RAZAO_SOCIAL, NOME_BENEFICIARIO, CPF_BENEFICIARIO<br/>
              <strong>Colunas monetárias:</strong> TRIBUTAVEIS, INSS, IRRF, PREV_COMPLEMENTAR, PENSAO_ALIMENTICIA, PARCELA_ISENTA65, PARCELA_13, DIARIAS_AJUDAS, MOLESTIA_GRAVE, LUCROS_DIVIDENDOS, LUCROS_SIMPLES_NACIONAL, INDENIZACOES, OUTROS_ISENTOS, TREZE_RENDIMENTOS, TREZE_IRRF, OUTROS_TRIB_EXCL, RRA_TRIBUTAVEIS, RRA_DESP_JUDICIAIS, RRA_INSS, RRA_PENSAO, RRA_IRRF, RRA_ISENTOS
            </div>
          </div>
        )}

        {step === STEPS.PREVIEW && resultado && (
          <div className="lote-card">
            <div className="lote-card-header">
              <span className="lote-icon">🔍</span>
              <div><h2>Pré-visualização</h2><p><strong>{resultado.validos}</strong> registros válidos · {resultado.invalidos > 0 && <><span className="badge-erro">{resultado.invalidos} com erro</span> · </>}<strong>{selecionados.length}</strong> selecionados</p></div>
            </div>
            {resultado.erros.length > 0 && (
              <div className="erros-bloco"><strong>⚠️ Linhas com problemas:</strong><ul>{resultado.erros.map((e, i) => <li key={i}>Linha {e.linha}: {e.erros.join(", ")}</li>)}</ul></div>
            )}
            {erro && <div className="lote-erro">⚠️ {erro}</div>}
            <div className="table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    <th><input type="checkbox" checked={selecionados.length === resultado.registros.length} onChange={toggleTodos} /></th>
                    <th>#</th>
                    <th>Exercício</th>
                    <th>Empresa / CNPJ</th>
                    <th>Beneficiário / CPF</th>
                    <th>Natureza</th>
                    <th colSpan="2">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {resultado.registros.map((reg, i) => (
                    <tr key={i} className={selecionados.includes(i) ? "row-sel" : "row-unsel"}>
                      <td><input type="checkbox" checked={selecionados.includes(i)} onChange={() => toggleSel(i)} /></td>
                      <td className="td-num">{i + 1}</td>
                      <td>{reg.exercicio || (reg.anoCalendario ? reg.anoCalendario + 1 : '')}</td>
                      <td><div className="td-primary">{reg.fontePagadora?.razaoSocial}</div><div className="td-secondary">{fmtCNPJ(reg.fontePagadora?.cnpj)}</div></td>
                      <td><div className="td-primary">{reg.beneficiario?.nome}</div><div className="td-secondary">{fmtCPF(reg.beneficiario?.cpf)}</div></td>
                      <td>{reg.naturezaRendimento || "Assalariado"}</td>
                      <td className="td-action"><button className="btn-rm" onClick={() => baixarPDFIndividual(reg, reg.beneficiario?.nome)} title="Baixar PDF individual">📄</button></td>
                      <td className="td-action"><button className="btn-rm" onClick={() => setResultado(prev => ({ ...prev, registros: prev.registros.filter((_, j) => j !== i) }))}>✕</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="lote-actions">
              <button className="btn-outline" onClick={handleReset}>← Trocar arquivo</button>
              <button className="btn-primary" disabled={!selecionados.length} onClick={handleGerar}>📄 Gerar {selecionados.length} PDF{selecionados.length !== 1 ? "s" : ""} →</button>
            </div>
          </div>
        )}

        {step === STEPS.GERANDO && (
          <div className="lote-card lote-card--center">
            <div className="progress-icon">⚙️</div>
            <h2>Gerando PDFs...</h2>
            <p>Aguarde enquanto os informes são processados</p>
            <div className="progress-bar-wrap"><div className="progress-bar" style={{ width: `${progresso}%` }} /></div>
            <div className="progress-pct">{progresso}%</div>
          </div>
        )}

        {step === STEPS.CONCLUIDO && (
          <div className="lote-card lote-card--center">
            <div className="progress-icon">🎉</div>
            <h2>Lote gerado com sucesso!</h2>
            <p><strong>{selecionados.length}</strong> informes foram gerados.</p>
            <div className="lote-actions lote-actions--center">
              {zipUrl && <a className="btn-outline" href={zipUrl} download={`Informes_Lote_${new Date().toISOString().slice(0,10)}.zip`}>⬇️ Baixar novamente</a>}
              <button className="btn-primary" onClick={handleReset}>Nova importação</button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

const LOTE_CSS = `
  .lote-wrapper { max-width: 960px; margin: 0 auto; padding: 0 16px 80px; }
  .lote-breadcrumb { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; font-size: 14px; color: #64748b; }
  .breadcrumb-sep { color: #cbd5e1; }
  .btn-voltar { background: none; border: none; color: #2563a8; font-size: 14px; cursor: pointer; padding: 0; font-family: inherit; }
  .btn-voltar:hover { text-decoration: underline; }
  .lote-card { background: #fff; border: 1px solid #d4dce8; border-radius: 12px; padding: 28px 32px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
  .lote-card--center { text-align: center; padding: 48px 32px; }
  .lote-card--center h2 { font-size: 22px; margin: 12px 0 8px; color: #1a3c6e; }
  .lote-card--center p  { color: #64748b; }
  .lote-card-header { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #f0f4fa; }
  .lote-icon { font-size: 32px; line-height: 1; }
  .lote-card-header h2 { font-size: 18px; color: #1a3c6e; margin-bottom: 4px; }
  .lote-card-header p  { font-size: 13px; color: #64748b; }
  .drop-area { border: 2px dashed #b8cce8; border-radius: 10px; padding: 40px 24px; text-align: center; cursor: pointer; transition: all 0.15s; background: #f8faff; }
  .drop-area:hover { border-color: #2563a8; background: #eef4ff; }
  .drop-area--ok { border-color: #16a34a; background: #f0fdf4; border-style: solid; }
  .drop-icon { font-size: 40px; margin-bottom: 10px; }
  .drop-label { font-size: 16px; font-weight: 600; color: #1e293b; }
  .drop-fname { font-size: 15px; font-weight: 600; color: #16a34a; }
  .drop-hint { font-size: 12px; color: #94a3b8; margin-top: 4px; }
  .lote-erro { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; border-radius: 8px; padding: 12px 16px; font-size: 13px; margin: 16px 0; }
  .lote-info-box { background: #f8faff; border: 1px solid #d4dce8; border-left: 3px solid #2563a8; border-radius: 8px; padding: 12px 16px; font-size: 12px; color: #475569; line-height: 1.8; margin-top: 20px; }
  .lote-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
  .lote-actions--center { justify-content: center; }
  .btn-primary, .btn-outline { display: inline-flex; align-items: center; gap: 6px; padding: 11px 24px; border-radius: 9px; font-family: inherit; font-size: 14px; font-weight: 600; cursor: pointer; border: none; transition: all 0.15s; text-decoration: none; }
  .btn-primary { background: #1a3c6e; color: #fff; box-shadow: 0 3px 10px rgba(26,60,110,0.25); }
  .btn-primary:hover:not(:disabled) { background: #2563a8; transform: translateY(-1px); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-outline { background: #fff; color: #475569; border: 1.5px solid #d4dce8; }
  .btn-outline:hover { background: #f0f4fa; color: #1e293b; }
  .erros-bloco { background: #fff7ed; border: 1px solid #fdba74; border-radius: 8px; padding: 12px 16px; font-size: 12px; color: #c2410c; margin-bottom: 16px; }
  .erros-bloco ul { margin-top: 6px; padding-left: 20px; }
  .erros-bloco li { margin-bottom: 2px; }
  .badge-erro { background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 20px; font-size: 12px; font-weight: 600; }
  .table-wrapper { overflow-x: auto; margin: 0 -4px; }
  .preview-table { width: 100%; border-collapse: collapse; font-size: 12px; min-width: 900px; }
  .preview-table th { background: #1a3c6e; color: #fff; padding: 9px 10px; text-align: left; font-size: 11px; font-weight: 600; white-space: nowrap; }
  .preview-table th:first-child { border-radius: 6px 0 0 0; }
  .preview-table th:last-child  { border-radius: 0 6px 0 0; }
  .preview-table td { padding: 9px 10px; border-bottom: 1px solid #e8eef5; }
  .row-sel   { background: #fff; }
  .row-unsel { background: #fafafa; opacity: 0.55; }
  .row-sel:hover, .row-unsel:hover { background: #eef4ff; opacity: 1; }
  .td-num     { color: #94a3b8; text-align: center; }
  .td-primary { font-weight: 600; font-size: 12px; }
  .td-secondary { font-size: 11px; color: #94a3b8; margin-top: 1px; font-family: monospace; }
  .td-action { text-align: center; vertical-align: middle; }
  .progress-icon { font-size: 48px; margin-bottom: 16px; }
  .progress-bar-wrap { width: 320px; height: 10px; background: #e2e8f0; border-radius: 99px; margin: 24px auto 8px; overflow: hidden; }
  .progress-bar { height: 100%; background: linear-gradient(90deg, #1a3c6e, #2563a8); border-radius: 99px; transition: width 0.3s ease; }
  .progress-pct { font-size: 13px; color: #64748b; font-weight: 600; }
`;