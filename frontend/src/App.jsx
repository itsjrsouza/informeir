import { useState, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || '';

function maskCNPJ(v){v=v.replace(/\D/g,"").slice(0,14);return v.replace(/^(\d{2})(\d)/,"$1.$2").replace(/^(\d{2})\.(\d{3})(\d)/,"$1.$2.$3").replace(/\.(\d{3})(\d)/,".$1/$2").replace(/(\d{4})(\d)/,"$1-$2")}
function maskCPF(v){v=v.replace(/\D/g,"").slice(0,11);return v.replace(/(\d{3})(\d)/,"$1.$2").replace(/(\d{3})\.(\d{3})(\d)/,"$1.$2.$3").replace(/\.(\d{3})(\d)/,".$1-$2")}
function maskBRL(v){const d=v.replace(/\D/g,"");if(!d)return"";return(parseInt(d,10)/100).toFixed(2).replace(".",",").replace(/\B(?=(\d{3})+(?!\d))/g,".")}
function fmtBRL(v){if(!v)return"R$ 0,00";const n=parseFloat(String(v).replace(/\./g,"").replace(",","."));if(isNaN(n))return"R$ 0,00";return"R$ "+n.toFixed(2).replace(".",",").replace(/\B(?=(\d{3})+(?!\d))/g,".")}
function fmtCNPJ(v){const d=String(v||"").replace(/\D/g,"");return d.length===14?`${d.slice(0,2)}.${d.slice(2,5)}.${d.slice(5,8)}/${d.slice(8,12)}-${d.slice(12)}`:v}
function fmtCPF(v){const d=String(v||"").replace(/\D/g,"");return d.length===11?`${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9)}`:v}

function SectionTitle({number,title}){return(<div className="sec-title"><span className="sec-num">{number}</span><h2>{title}</h2></div>)}
function Field({label,children}){return(<div className="field"><label>{label}</label>{children}</div>)}
function MaskedInput({mask,value,onChange,...rest}){return(<input value={value} onChange={e=>{let v=e.target.value;if(mask==="cnpj")v=maskCNPJ(v);else if(mask==="cpf")v=maskCPF(v);else if(mask==="brl")v=maskBRL(v);onChange(v)}} {...rest}/>)}
function CurrencyField({label,value,onChange}){return(<Field label={label}><div className="currency-wrap"><span className="currency-pre">R$</span><MaskedInput mask="brl" value={value} onChange={onChange} placeholder="0,00"/></div></Field>)}
function Spin({large}){return<span className={large?"spin-lg":"spin"}/>}

const REND_FIELDS = [
  {key:"tributaveis", label:"Total dos Rendimentos (inclusive férias)", sec:3},
  {key:"inss", label:"Contribuição Previdenciária Oficial", sec:3},
  {key:"outrasDeducoes", label:"Pensão Alimentícia / Outras Deduções", sec:3},
  {key:"irrf", label:"Imposto sobre a renda retido na fonte", sec:3},
  {key:"lucrosDividendos", label:"Lucros e Dividendos (item 04)", sec:4},
  {key:"outrosIsentos", label:"Outros Rendimentos Isentos", sec:4},
  {key:"trezeRendimentos", label:"13º Salário", sec:5},
  {key:"trezeIrrf", label:"IRRF sobre 13º Salário", sec:5},
];
const INIT_REND = Object.fromEntries(REND_FIELDS.map(f=>[f.key,""]));

function AbaIndividual(){
  const [exercicio, setExercicio] = useState(new Date().getFullYear() + 1);
  const [ano, setAno] = useState(exercicio - 1);
  const [fonte, setFonte] = useState({razaoSocial:"", cnpj:""});
  const [benef, setBenef] = useState({nome:"", cpf:""});
  const [rend, setRend] = useState(INIT_REND);
  const [responsavel, setResponsavel] = useState({nome:"", data:""});
  const [loading, setLoad] = useState(null);
  const [erro, setErro] = useState(null);
  const [ok, setOk] = useState(false);

  useEffect(() => { setAno(exercicio - 1); }, [exercicio]);

  const setF = k => v => setFonte(p => ({...p, [k]: v}));
  const setB = k => v => setBenef(p => ({...p, [k]: v}));
  const setR = k => v => setRend(p => ({...p, [k]: v}));
  const setResp = k => v => setResponsavel(p => ({...p, [k]: v}));

  async function submit(fmt){
    setErro(null); setOk(false); setLoad(fmt);
    try{
      const endpoint = fmt === "pdf" ? "/api/informe/gerar-pdf" : "/api/informe/gerar";
      const payload = {
        exercicio,
        anoCalendario: ano,
        fontePagadora: fonte,
        beneficiario: benef,
        rendimentos: rend,
        responsavel: {
          nome: responsavel.nome || "Não informado",
          data: responsavel.data || new Date().toLocaleDateString('pt-BR')
        }
      };
      const res = await fetch(API_URL + endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      if(!res.ok){
        const d = await res.json();
        throw new Error(d.erro || d.detalhes);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Informe_${benef.nome}_${ano}.${fmt === "pdf" ? "pdf" : "docx"}`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
      setOk(true);
    } catch(e) {
      setErro(e.message);
    } finally {
      setLoad(null);
    }
  }

  const sec = n => REND_FIELDS.filter(f => f.sec === n);
  return (
    <div>
      <div className="card">
        <SectionTitle number="●" title="Período de Referência"/>
        <div className="g2">
          <Field label="Exercício (ano de entrega)">
            <select value={exercicio} onChange={e => setExercicio(Number(e.target.value))}>
              {Array.from({length:5}, (_,i) => new Date().getFullYear() + i).map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </Field>
          <Field label="Ano-Calendário (automático)">
            <input type="text" value={ano} readOnly className="ro" />
          </Field>
        </div>
      </div>

      <div className="card">
        <SectionTitle number="1" title="Fonte Pagadora Pessoa Jurídica ou Física"/>
        <div className="g2">
          <Field label="Nome Empresarial / Nome Completo"><input value={fonte.razaoSocial} onChange={e=>setF("razaoSocial")(e.target.value)} placeholder="Nome da empresa" required/></Field>
          <Field label="CNPJ/CPF"><MaskedInput mask="cnpj" value={fonte.cnpj} onChange={setF("cnpj")} placeholder="00.000.000/0000-00" required/></Field>
        </div>
      </div>

      <div className="card">
        <SectionTitle number="2" title="Pessoa Física Beneficiária dos Rendimentos"/>
        <div className="g2">
          <Field label="Nome Completo"><input value={benef.nome} onChange={e=>setB("nome")(e.target.value)} placeholder="Nome do beneficiário" required/></Field>
          <Field label="CPF"><MaskedInput mask="cpf" value={benef.cpf} onChange={setB("cpf")} placeholder="000.000.000-00" required/></Field>
        </div>
      </div>

      {[
        {n:3, t:"Rendimentos Tributáveis, Deduções e Imposto Retido na Fonte"},
        {n:4, t:"Rendimentos Isentos e Não Tributáveis"},
        {n:5, t:"Rendimentos Sujeitos à Tributação Exclusiva (13° Salário)"}
      ].map(({n,t}) => (
        <div className="card" key={n}>
          <SectionTitle number={n} title={t}/>
          <div className={sec(n).length === 3 ? "g3" : "g2"}>
            {sec(n).map(f => <CurrencyField key={f.key} label={f.label} value={rend[f.key]} onChange={setR(f.key)}/>)}
          </div>
        </div>
      ))}

      <div className="card">
        <SectionTitle number="8" title="Responsável pelas Informações"/>
        <div className="g2">
          <Field label="Nome Completo">
            <input value={responsavel.nome} onChange={e=>setResp("nome")(e.target.value)} placeholder="Nome do responsável" />
          </Field>
          <Field label="Data">
            <input type="text" value={responsavel.data} onChange={e=>setResp("data")(e.target.value)} placeholder="DD/MM/AAAA" />
          </Field>
        </div>
      </div>

      {erro && <div className="alert err">⚠️ {erro}</div>}
      {ok && <div className="alert suc">✅ Download iniciado com sucesso!</div>}
      <div className="actions">
        <button className="btn-sec" onClick={()=>{
          setFonte({razaoSocial:"",cnpj:""});
          setBenef({nome:"",cpf:""});
          setRend(INIT_REND);
          setResponsavel({nome:"",data:""});
          setErro(null); setOk(false);
        }}>Limpar</button>
        <button className="btn-outline" onClick={()=>submit("pdf")} disabled={!!loading}>{loading==="pdf"?<><Spin/> Gerando PDF...</>:"⬇ Baixar PDF"}</button>
        <button className="btn-primary" onClick={()=>submit("docx")} disabled={!!loading}>{loading==="docx"?<><Spin/> Gerando...</>:"⬇ Baixar Word (.docx)"}</button>
      </div>
    </div>
  );
}

function AbaLote(){
  const [fase,setFase]=useState("upload");
  const [socios,setSocios]=useState([]);
  const [erros,setErros]=useState([]);
  const [loadPreview,setLP]=useState(false);
  const [loadGerar,setLG]=useState(false);
  const [msgErro,setMsgErro]=useState(null);
  const fileRef=useRef();

  async function baixarModelo(){
    const res=await fetch(API_URL+"/api/modelo-excel");
    const blob=await res.blob();
    const a=Object.assign(document.createElement("a"),{href:URL.createObjectURL(blob),download:"Modelo_Importacao_Informes.xlsx"});
    document.body.appendChild(a);a.click();a.remove();
  }

  async function handleUpload(e){
    const file = e.target.files?.[0];
    if(!file) return;
    console.log('📤 === UPLOAD INICIADO ===');
    console.log('📋 Arquivo selecionado:', { name: file.name, size: file.size, type: file.type });
    if (!file.name.match(/\.xlsx$/i)) { setMsgErro('O arquivo deve ter extensão .xlsx'); return; }
    if (file.size < 1000) { setMsgErro(`Arquivo muito pequeno (${file.size} bytes). Pode estar vazio ou corrompido.`); return; }
    setLP(true); setMsgErro(null);
    const form = new FormData(); form.append("arquivo", file, file.name);
    try{
      const res = await fetch(`${API_URL}/api/lote/preview`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.erro || data.detalhes || 'Erro ao processar arquivo');
      console.log('✅ Preview processado:', { total: data.total, validos: data.validos });
      setSocios(data.registros || []); setErros(data.erros || []); setFase("preview");
    } catch(e) {
      console.error('❌ Erro no upload:', e); setMsgErro(e.message);
    } finally {
      setLP(false); if(fileRef.current) fileRef.current.value = "";
    }
  }

  async function gerarLote(){
    setLG(true); setMsgErro(null); setFase("gerando");
    try{
      const res=await fetch(API_URL+"/api/lote/gerar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({socios})});
      if(!res.ok){ const d=await res.json(); throw new Error(d.erro); }
      const blob=await res.blob();
      const a=Object.assign(document.createElement("a"),{href:URL.createObjectURL(blob),download:`Informes_Lote_${new Date().toISOString().slice(0,10)}.zip`});
      document.body.appendChild(a);a.click();a.remove();
      setFase("pronto");
    }catch(e){ setMsgErro(e.message); setFase("preview"); }
    finally{ setLG(false); }
  }

  return(<div>
    <div className="card">
      <div className="step-header">
        <div className="step-badge">1</div>
        <div><h3>Baixe o modelo e preencha</h3><p className="step-sub">Uma linha por sócio. Cada linha pode ter empresa diferente.</p></div>
        <button className="btn-outline" onClick={baixarModelo}>⬇ Baixar Modelo Excel</button>
      </div>
    </div>
    <div className="card">
      <div className="step-header">
        <div className="step-badge">2</div>
        <div><h3>Faça o upload do Excel preenchido</h3><p className="step-sub">Prévia será gerada para você conferir antes de gerar os PDFs.</p></div>
      </div>
      <div className="upload-zone" onClick={()=>fileRef.current?.click()}>
        <input ref={fileRef} type="file" accept=".xlsx,.xls" onChange={handleUpload} style={{display:"none"}}/>
        {loadPreview?(<><Spin large/><p>Processando planilha...</p></>):(<><span className="upload-icon">📊</span><p><strong>Clique para selecionar</strong> ou arraste o .xlsx aqui</p><p className="upload-hint">Máx. 10 MB · somente .xlsx</p></>)}
      </div>
      {msgErro&&<div className="alert err" style={{marginTop:12}}>⚠️ {msgErro}</div>}
    </div>
    {(fase==="preview"||fase==="gerando"||fase==="pronto")&&(
      <div className="card">
        <div className="step-header">
          <div className="step-badge" style={{background:socios.length>0?"var(--success)":"var(--error)"}}>3</div>
          <div><h3>Prévia dos dados</h3><p className="step-sub"><strong>{socios.length}</strong> sócio(s) válido(s) · <span style={{color:erros.length?"var(--error)":"inherit"}}>{erros.length} erro(s)</span></p></div>
        </div>
        {erros.length>0&&(<div className="erros-box"><strong>⚠️ Linhas com erro (não serão geradas):</strong>{erros.map((e,i)=><div key={i} className="erro-linha">Linha {e.linha} — {e.nome}: {e.erros.join(", ")}</div>)}</div>)}
        {socios.length>0&&(
          <div className="preview-table-wrap">
            <table className="preview-table">
              <thead><tr><th>#</th><th>Exercício</th><th>Empresa</th><th>CNPJ</th><th>Sócio</th><th>CPF</th><th>Tributáveis</th><th>Lucros/Div.</th><th>IRRF</th><th></th></tr></thead>
              <tbody>{socios.map((s,i)=>(
                <tr key={i}>
                  <td>{i+1}</td>
                  <td>{s.exercicio || (s.anoCalendario ? s.anoCalendario+1 : '')}</td>
                  <td>{s.fontePagadora?.razaoSocial}</td>
                  <td className="mono">{fmtCNPJ(s.fontePagadora?.cnpj)}</td>
                  <td>{s.beneficiario?.nome}</td>
                  <td className="mono">{fmtCPF(s.beneficiario?.cpf)}</td>
                  <td className="num">{fmtBRL(s.rendimentos?.tributaveis)}</td>
                  <td className="num">{fmtBRL(s.rendimentos?.lucrosDividendos)}</td>
                  <td className="num">{fmtBRL(s.rendimentos?.irrf)}</td>
                  <td><button className="btn-rm" onClick={()=>setSocios(s=>s.filter((_,j)=>j!==i))}>✕</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    )}
    {(fase==="preview"||fase==="gerando"||fase==="pronto")&&socios.length>0&&(
      <div className="card">
        <div className="step-header">
          <div className="step-badge" style={{background:fase==="pronto"?"var(--success)":"var(--rf-blue)"}}>4</div>
          <div><h3>Gerar PDFs em lote</h3><p className="step-sub">Será gerado um ZIP com <strong>{socios.length}</strong> PDF(s), um por sócio.</p></div>
        </div>
        {fase==="pronto"?(
          <div className="alert suc">✅ ZIP gerado! Cada PDF está nomeado com o número e nome do sócio.</div>
        ):(
          <div className="actions" style={{marginTop:16}}>
            <button className="btn-sec" onClick={()=>{setFase("upload");setSocios([]);setErros([])}}>Voltar</button>
            <button className="btn-primary" onClick={gerarLote} disabled={loadGerar}>{loadGerar?<><Spin/> Gerando {socios.length} PDF(s)...</>:`⬇ Gerar ${socios.length} PDF(s) em ZIP`}</button>
          </div>
        )}
      </div>
    )}
  </div>);
}

export default function App(){
  const [aba,setAba]=useState("individual");
  return(<>
    <style>{CSS}</style>
    <div className="app">
      <header className="hdr">
        <div className="hdr-inner">
          <div className="hdr-badge">RF</div>
          <div><h1>Informe de Rendimentos</h1><p>Comprovante Anual · Receita Federal do Brasil</p></div>
        </div>
      </header>
      <div className="tabs-bar">
        <button className={`tab ${aba==="individual"?"tab-on":""}`} onClick={()=>setAba("individual")}>📄 Individual</button>
        <button className={`tab ${aba==="lote"?"tab-on":""}`} onClick={()=>setAba("lote")}>📊 Importação em Lote</button>
      </div>
      <main className="main">{aba==="individual"?<AbaIndividual/>:<AbaLote/>}</main>
      <footer className="ftr">Aprovado pela Instrução Normativa RFB nº 2.060, de 13 de dezembro de 2021.</footer>
    </div>
  </>);
}

const CSS=`
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--rf-blue:#1F3864;--rf-mid:#2563A8;--rf-acc:#f5a623;--bg:#f0f4fa;--card:#fff;--border:#d4dce8;--text:#1e293b;--muted:#64748b;--success:#16a34a;--error:#dc2626;--r:10px}
body{font-family:'Figtree',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.hdr{background:linear-gradient(135deg,var(--rf-blue),var(--rf-mid));color:#fff;padding:24px 32px;box-shadow:0 4px 20px rgba(26,60,110,.25)}
.hdr-inner{max-width:960px;margin:0 auto;display:flex;align-items:center;gap:18px}
.hdr-badge{width:50px;height:50px;background:var(--rf-acc);color:var(--rf-blue);font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center;border-radius:12px;flex-shrink:0}
.hdr-inner h1{font-size:20px;font-weight:700}.hdr-inner p{font-size:12px;opacity:.8;margin-top:2px}
.tabs-bar{max-width:960px;margin:0 auto;display:flex;gap:4px;padding:20px 16px 0}
.tab{padding:10px 22px;border:none;border-radius:8px 8px 0 0;font-family:'Figtree',sans-serif;font-size:14px;font-weight:600;cursor:pointer;background:#dce6f5;color:var(--muted);transition:all .15s}
.tab-on{background:var(--card);color:var(--rf-blue);box-shadow:0 -2px 0 var(--rf-mid) inset}.tab:hover:not(.tab-on){background:#cddaee}
.main{max-width:960px;margin:0 auto;padding:0 16px 80px;border-top:3px solid var(--rf-mid)}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:22px 26px;margin-top:18px;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.card-resp{background:#f8faff;border-color:#b8cce8}
.sec-title{display:flex;align-items:center;gap:12px;margin-bottom:18px;padding-bottom:12px;border-bottom:2px solid var(--bg)}
.sec-num{width:28px;height:28px;background:var(--rf-blue);color:#fff;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;border-radius:7px;flex-shrink:0}
.sec-title h2{font-size:13px;font-weight:600;color:var(--rf-blue);text-transform:uppercase;letter-spacing:.4px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
@media(max-width:640px){.g2,.g3{grid-template-columns:1fr}}
.field{display:flex;flex-direction:column;gap:5px}
.field label{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
input,select{font-family:'Figtree',sans-serif;font-size:14px;padding:9px 13px;border:1.5px solid var(--border);border-radius:8px;color:var(--text);background:#fff;width:100%;transition:border-color .15s,box-shadow .15s}
input:focus,select:focus{outline:none;border-color:var(--rf-mid);box-shadow:0 0 0 3px rgba(37,99,168,.12)}
.ro{background:#f1f5f9;color:var(--muted);cursor:default;font-family:'JetBrains Mono',monospace;font-size:12px}
.currency-wrap{display:flex;align-items:center;border:1.5px solid var(--border);border-radius:8px;overflow:hidden;transition:border-color .15s,box-shadow .15s}
.currency-wrap:focus-within{border-color:var(--rf-mid);box-shadow:0 0 0 3px rgba(37,99,168,.12)}
.currency-pre{padding:9px 10px;background:#f1f5f9;font-size:12px;font-weight:600;color:var(--muted);border-right:1.5px solid var(--border);flex-shrink:0;font-family:'JetBrains Mono',monospace}
.currency-wrap input{border:none;border-radius:0;text-align:right;font-family:'JetBrains Mono',monospace;font-size:13px}
.currency-wrap input:focus{box-shadow:none}
.alert{padding:12px 16px;border-radius:var(--r);font-size:13px;font-weight:500;margin-top:16px;display:flex;align-items:center;gap:8px}
.err{background:#fef2f2;color:var(--error);border:1px solid #fca5a5}.suc{background:#f0fdf4;color:var(--success);border:1px solid #86efac}
.actions{display:flex;justify-content:flex-end;gap:12px;margin-top:20px;flex-wrap:wrap}
.btn-primary,.btn-sec,.btn-outline{display:flex;align-items:center;gap:7px;padding:11px 24px;border-radius:9px;font-family:'Figtree',sans-serif;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:all .15s}
.btn-primary{background:var(--rf-blue);color:#fff;box-shadow:0 4px 12px rgba(26,60,110,.3)}.btn-primary:hover:not(:disabled){background:var(--rf-mid);transform:translateY(-1px)}.btn-primary:disabled{opacity:.6;cursor:not-allowed}
.btn-outline{background:#fff;color:var(--rf-mid);border:1.5px solid var(--rf-mid)}.btn-outline:hover{background:#eef4ff}
.btn-sec{background:#fff;color:var(--muted);border:1.5px solid var(--border)}.btn-sec:hover{background:var(--bg)}
.btn-rm{background:none;border:none;color:#ccc;cursor:pointer;font-size:13px;padding:2px 6px;border-radius:4px}.btn-rm:hover{color:var(--error);background:#fef2f2}
.step-header{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.step-badge{width:32px;height:32px;border-radius:50%;background:var(--rf-blue);color:#fff;font-weight:700;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.step-header h3{font-size:15px;font-weight:600}.step-sub{font-size:12px;color:var(--muted);margin-top:2px}
.step-header .btn-outline{margin-left:auto}
.upload-zone{border:2px dashed var(--border);border-radius:var(--r);padding:36px;text-align:center;cursor:pointer;transition:border-color .15s,background .15s;margin-top:16px;color:var(--muted)}
.upload-zone:hover{border-color:var(--rf-mid);background:#f0f7ff}
.upload-icon{font-size:32px;display:block;margin-bottom:8px}.upload-zone p{font-size:13px;margin-top:4px}.upload-hint{font-size:11px;margin-top:4px;opacity:.6}
.erros-box{background:#fef9ec;border:1px solid #fcd34d;border-radius:8px;padding:12px 16px;margin-bottom:14px;font-size:12px}
.erro-linha{margin-top:4px;color:#92400e}
.preview-table-wrap{overflow-x:auto;margin-top:12px}
.preview-table{width:100%;border-collapse:collapse;font-size:12px}
.preview-table th{background:#f1f5f9;font-weight:600;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:2px solid var(--border);white-space:nowrap}
.preview-table td{padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:middle}
.preview-table tr:hover td{background:#f8faff}
.mono{font-family:'JetBrains Mono',monospace;font-size:11px}.num{text-align:right;font-family:'JetBrains Mono',monospace}
.spin{width:14px;height:14px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;display:inline-block;animation:spin .7s linear infinite}
.spin-lg{width:28px;height:28px;border:3px solid rgba(37,99,168,.2);border-top-color:var(--rf-mid);border-radius:50%;display:inline-block;animation:spin .7s linear infinite;margin-bottom:10px}
@keyframes spin{to{transform:rotate(360deg)}}
.ftr{text-align:center;padding:20px;font-size:11px;color:var(--muted);border-top:1px solid var(--border);margin-top:30px}
`;