import { useState, useRef, useEffect } from "react";
import "./App.css";

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
  // Seção 3
  {key:"tributaveis", label:"01 - Total dos Rendimentos (inclusive Férias)", sec:3},
  {key:"inss", label:"02 - Contribuição Previdenciária Oficial", sec:3},
  {key:"prevComplementar", label:"03 - Contrib. Previd. Complementar / FAPI", sec:3},
  {key:"pensaoAlimenticia", label:"04 - Pensão Alimentícia", sec:3},
  {key:"irrf", label:"05 - Imposto sobre a renda retido na fonte", sec:3},
  // Seção 4
  {key:"parcelaIsenta65", label:"01 - Parcela Isenta 65 anos ou mais", sec:4},
  {key:"diariasAjudas", label:"02 - Diárias e Ajudas de Custo", sec:4},
  {key:"molestiaGrave", label:"03 - Pensão/Aposent. Moléstia Grave ou Acidente", sec:4},
  {key:"lucrosDividendos", label:"04 - Lucros e Dividendos", sec:4},
  {key:"prolaboreIsento", label:"05 - Pro-labore isento ME/EPP", sec:4},
  {key:"indenizacoes", label:"06 - Indenizações por Rescisão/PDV", sec:4},
  {key:"outrosIsentos", label:"07 - Outros Rendimentos Isentos", sec:4},
  // Seção 5
  {key:"trezeRendimentos", label:"01 - 13º Salário", sec:5},
  {key:"trezeIrrf", label:"02 - IRRF sobre 13º Salário", sec:5},
  {key:"outrosTribExclusiva", label:"03 - Outros (Trib. Exclusiva)", sec:5},
  // Seção 6 ...
];

const INIT_REND = Object.fromEntries(REND_FIELDS.map(f=>[f.key,""]));

function AbaIndividual(){
  const [exercicio, setExercicio] = useState(new Date().getFullYear() + 1);
  const [ano, setAno] = useState(exercicio - 1);
  const [fonte, setFonte] = useState({razaoSocial:"", cnpj:""});
  const [benef, setBenef] = useState({nome:"", cpf:""});
  const [rend, setRend] = useState(INIT_REND);
  const [responsavel, setResponsavel] = useState({nome:"", data:"", assinatura:""});
  const [infoComplementar, setInfoComplementar] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);
  const [ok, setOk] = useState(false);

  useEffect(() => { setAno(exercicio - 1); }, [exercicio]);

  const setF = k => v => setFonte(p => ({...p, [k]: v}));
  const setB = k => v => setBenef(p => ({...p, [k]: v}));
  const setR = k => v => setRend(p => ({...p, [k]: v}));
  const setResp = k => v => setResponsavel(p => ({...p, [k]: v}));

  async function handleSubmit(){
    setErro(null); setOk(false); setLoading(true);
    try{
      const payload = {
        exercicio,
        anoCalendario: ano,
        fontePagadora: fonte,
        beneficiario: benef,
        rendimentos: rend,
        responsavel: {
          nome: responsavel.nome || "Não informado",
          data: responsavel.data || new Date().toLocaleDateString('pt-BR'),
          assinatura: responsavel.assinatura || "Isento conforme IN RFB 1215/2011"
        },
        informacoesComplementares: infoComplementar
      };
      const res = await fetch(API_URL + "/api/informe/gerar-pdf", {
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
      a.download = `Informe_${benef.nome}_${ano}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
      setOk(true);
    } catch(e) {
      setErro(e.message);
    } finally {
      setLoading(false);
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
        {n:3, t:"3. Rendimentos Tributáveis, Deduções e Imposto Retido na Fonte"},
        {n:4, t:"4. Rendimentos Isentos e Não Tributáveis"},
        {n:5, t:"5. Rendimentos Sujeitos à Tributação Exclusiva"}
      ].map(({n,t}) => (
        <div className="card" key={n}>
          <SectionTitle number={n} title={t}/>
          <div className="g2">
            {sec(n).map(f => (
              f.tipo === "texto" ? (
                <Field key={f.key} label={f.label}>
                  <input value={rend[f.key]} onChange={e=>setR(f.key)(e.target.value)} />
                </Field>
              ) : f.tipo === "numero" ? (
                <Field key={f.key} label={f.label}>
                  <input type="number" value={rend[f.key]} onChange={e=>setR(f.key)(e.target.value)} />
                </Field>
              ) : (
                <CurrencyField key={f.key} label={f.label} value={rend[f.key]} onChange={setR(f.key)}/>
              )
            ))}
          </div>
        </div>
      ))}

      <div className="card">
        <SectionTitle number="6" title="Rendimentos Recebidos Acumuladamente (RRA)"/>
        <div className="g3">
          {sec(6).map(f => (
            f.tipo === "texto" ? (
              <Field key={f.key} label={f.label}>
                <input value={rend[f.key]} onChange={e=>setR(f.key)(e.target.value)} />
              </Field>
            ) : f.tipo === "numero" ? (
              <Field key={f.key} label={f.label}>
                <input type="number" value={rend[f.key]} onChange={e=>setR(f.key)(e.target.value)} />
              </Field>
            ) : (
              <CurrencyField key={f.key} label={f.label} value={rend[f.key]} onChange={setR(f.key)}/>
            )
          ))}
        </div>
      </div>

      <div className="card">
        <SectionTitle number="7" title="Informações Complementares"/>
        <Field label="Descreva informações adicionais se necessário">
          <textarea rows="3" value={infoComplementar} onChange={e=>setInfoComplementar(e.target.value)} />
        </Field>
      </div>

      <div className="card">
        <SectionTitle number="8" title="Responsável pelas Informações"/>
        <div className="g3">
          <Field label="Nome Completo">
            <input value={responsavel.nome} onChange={e=>setResp("nome")(e.target.value)} placeholder="Nome do responsável" />
          </Field>
          <Field label="Data">
            <input type="text" value={responsavel.data} onChange={e=>setResp("data")(e.target.value)} placeholder="DD/MM/AAAA" />
          </Field>
          <Field label="Assinatura">
            <input value={responsavel.assinatura} onChange={e=>setResp("assinatura")(e.target.value)} placeholder="Ex: Isento conforme IN..." />
          </Field>
        </div>
      </div>

      {erro && <div className="alert err">⚠️ {erro}</div>}
      {ok && <div className="alert suc">✅ PDF gerado com sucesso!</div>}
      <div className="actions">
        <button className="btn-sec" onClick={()=>{
          setFonte({razaoSocial:"",cnpj:""});
          setBenef({nome:"",cpf:""});
          setRend(INIT_REND);
          setResponsavel({nome:"",data:"",assinatura:""});
          setInfoComplementar("");
          setErro(null); setOk(false);
        }}>Limpar</button>
        <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
          {loading ? <><Spin/> Gerando PDF...</> : "⬇ Baixar PDF"}
        </button>
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
    if (!file.name.match(/\.xlsx$/i)) { setMsgErro('O arquivo deve ter extensão .xlsx'); return; }
    if (file.size < 1000) { setMsgErro(`Arquivo muito pequeno (${file.size} bytes).`); return; }
    setLP(true); setMsgErro(null);
    const form = new FormData(); form.append("arquivo", file, file.name);
    try{
      const res = await fetch(`${API_URL}/api/lote/preview`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.erro || data.detalhes);
      setSocios(data.registros || []); setErros(data.erros || []); setFase("preview");
    } catch(e) {
      setMsgErro(e.message);
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
        <div><h3>Faça o upload do Excel preenchido</h3><p className="step-sub">Prévia será gerada para conferência.</p></div>
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
          <div><h3>Prévia dos dados</h3><p className="step-sub"><strong>{socios.length}</strong> sócio(s) válido(s) · {erros.length} erro(s)</p></div>
        </div>
        {erros.length>0&&(<div className="erros-box"><strong>⚠️ Linhas com erro:</strong>{erros.map((e,i)=><div key={i} className="erro-linha">Linha {e.linha} — {e.nome}: {e.erros.join(", ")}</div>)}</div>)}
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
          <div><h3>Gerar PDFs em lote</h3><p className="step-sub">Será gerado um ZIP com <strong>{socios.length}</strong> PDF(s).</p></div>
        </div>
        {fase==="pronto"?(
          <div className="alert suc">✅ ZIP gerado! Cada PDF está nomeado com o número e nome do sócio.</div>
        ):(
          <div className="actions" style={{marginTop:16}}>
            <button className="btn-sec" onClick={()=>{setFase("upload");setSocios([]);setErros([])}}>Voltar</button>
            <button className="btn-primary" onClick={gerarLote} disabled={loadGerar}>{loadGerar?<><Spin/> Gerando...</>:`⬇ Gerar ${socios.length} PDF(s) em ZIP`}</button>
          </div>
        )}
      </div>
    )}
  </div>);
}

export default function App(){
  const [aba,setAba]=useState("individual");
  return (
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
  );
}