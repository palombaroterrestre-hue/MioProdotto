'use client'
import {useEffect,useState} from 'react'
import {Saved,products} from '../lib/catalog'
import type {Extraction,ExtractedOffer} from '../lib/live-extraction'
const EMAIL_KEY='mioprodotto.demo.email.v1'
const money=(n:number)=>n.toLocaleString('it-IT',{style:'currency',currency:'EUR'})
type Run={email:string;watchlist:Saved[];extraction:Extraction;offers:ExtractedOffer[]}
export default function DemoFlow({saved,ready,onChoose,onProduct}:{saved:Saved[];ready:boolean;onChoose:()=>void;onProduct:(id:string)=>void}){
 const[email,setEmail]=useState(''),[run,setRun]=useState<Run|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[showData,setShowData]=useState(false)
 useEffect(()=>{try{setEmail(localStorage.getItem(EMAIL_KEY)||'')}catch{setError('Il browser non permette di recuperare l’email di prova.')}},[])
 const changed=!!run&&(run.email!==email.trim()||JSON.stringify(run.watchlist)!==JSON.stringify(saved))
 async function simulate(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();if(!saved.length||busy)return;const address=email.trim();if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address))return
  setRun(null);setError('');setBusy(true)
  try{
   const response=await fetch('/api/extract-latest',{method:'POST',cache:'no-store',signal:AbortSignal.timeout(65000)})
   if(!response.headers.get('content-type')?.includes('application/json'))throw Error('Servizio di estrazione non disponibile. Riprova più tardi.');const result=await response.json();if(!response.ok)throw Error(result.error||'Estrazione fallita.')
   const extraction=result as Extraction;if(!extraction.source||!Array.isArray(extraction.offers))throw Error('Risultato dell’estrazione non valido.')
   const offers=extraction.offers.filter(o=>o.status==='matched'&&saved.some(s=>s.productId===o.productId&&(s.formatId==='linea'||o.formatIds.includes(s.formatId))))
   setRun({email:address,watchlist:saved.map(x=>({...x})),extraction,offers});try{localStorage.setItem(EMAIL_KEY,address)}catch{}
  }catch(e){setError((e instanceof Error?e.message:'Estrazione fallita.')+' Nessun avviso generato e nessun dato preparato usato al suo posto.')}finally{setBusy(false)}
 }
 function reset(){setRun(null);setEmail('');setError('');try{localStorage.removeItem(EMAIL_KEY);localStorage.removeItem('mioprodotto.demo.run.v1')}catch{}}
 const meta=run?.extraction
 return <div className="demo-flow">
  <section className="demo-panel" aria-labelledby="demo-title"><span className="step-label">2 / ESTRAZIONE REALE</span><h2 id="demo-title">Leggiamo il volantino adesso.</h2>
   <p>Il pulsante cerca l'ultimo PDF Ekom Liguria/Piemonte, lo scarica e ne estrae testo e prezzi dal testo digitale. Poi confronta i risultati con la tua watchlist.</p>
   <form onSubmit={simulate}><label htmlFor="demo-email">Email per la prova</label><input id="demo-email" type="email" autoComplete="off" placeholder="prova@example.com" value={email} onChange={e=>setEmail(e.target.value)} required disabled={busy}/><p className="muted privacy">Email e watchlist restano in questo browser. Il server riceve solo il comando di leggere il volantino, non il tuo indirizzo.</p><button className="primary" type="submit" disabled={!ready||!saved.length||busy}>{busy?'Recupero PDF ed estrazione in corso…':'Estrai ultimo volantino e simula l’avviso'}</button></form>
   {!saved.length&&<button className="text-button" onClick={onChoose}>Prima scegli un prodotto dal catalogo</button>}
   {busy&&<p className="status" role="status">1. Controllo elenco Ekom · 2. Download PDF · 3. Estrazione e confronto. Può richiedere alcuni secondi. Non vengono usati risultati precedenti.</p>}
   {error&&<p role="alert" className="warning">{error}</p>}
   <p className="muted demo-source">Solo il giorno dopo e la ricezione dell'email sono simulati. Nessun invio reale, account o controllo programmato. Se il PDF non è leggibile o il formato non è supportato, la prova si ferma.</p>
  </section>
  {run&&meta&&<>
   <section className="extraction-receipt"><span className="step-label">ESTRAZIONE ESEGUITA</span><h2>{meta.title}</h2><p>{meta.region} · {meta.validFrom} / {meta.validTo}</p><p className="muted">Controllo completato: {new Date(meta.checkedAt).toLocaleString('it-IT',{timeZone:'Europe/Rome'})} (ora italiana).</p><p>{meta.pages} pagine lette · {meta.textItems} elementi di testo · {meta.offers.length} offerte candidate · {meta.offers.filter(o=>o.status==='matched').length} collegamenti verificati al catalogo.</p><a href={meta.source} target="_blank" rel="noopener noreferrer">PDF effettivamente scaricato ↗</a><details><summary>Impronta del PDF e limiti</summary><p className="hash">SHA-256: {meta.sha256}</p><p>Estrazione automatica dal testo digitale e dalla posizione dei prezzi. Non è OCR di immagini. Le righe candidate possono contenere testo di contorno e non sono tutte validate: solo i collegamenti verificati possono generare un avviso. Marca, variante e formato devono essere verificabili nel testo: se sono solo nella foto, la riga non genera avvisi. Le promozioni solo percentuali non sono incluse.</p>{meta.warnings.map((w,i)=><p className="muted" key={i}>{w}</p>)}</details><button className="text-button" onClick={()=>setShowData(!showData)}>{showData?'Nascondi righe estratte':'Mostra le righe estratte dal PDF'}</button></section>
   <section className="mailbox" aria-labelledby="mail-title"><span className="step-label">3 / GIORNO DOPO · SIMULAZIONE</span><h2 id="mail-title">La tua casella di prova</h2>
   {changed&&<p role="status" className="warning">Watchlist o email cambiate. Ripeti l'estrazione per un nuovo risultato.</p>}
   {run.offers.length?<article className="demo-mail"><div className="mail-meta"><span>EMAIL SIMULATA · NON INVIATA</span><p><strong>A:</strong> {run.email}</p><p><strong>Oggetto:</strong> {run.offers.length} {run.offers.length===1?'offerta per un prodotto che segui':'offerte per i prodotti che segui'}</p></div><div className="mail-body"><p>Ciao! Abbiamo letto il volantino {meta.title}, valido dal {meta.validFrom} al {meta.validTo}. Queste offerte corrispondono alle tue scelte.</p>{run.offers.map(o=><div className="notification-offer" key={o.id}><h3>{products.find(p=>p.id===o.productId)?.name}</h3><p className="notification-price">{money(o.price)}</p>{o.condition&&<p className="condition">{o.condition}</p>}<p className="source-excerpt">Testo estratto: {o.rawText}</p><a href={meta.source+`#page=${o.page}`} target="_blank" rel="noopener noreferrer">Controlla la pagina {o.page} del PDF ↗</a></div>)}<p className="muted">Le unità di vendita e le condizioni sono nel testo fonte. Verifica disponibilità e condizioni del punto vendita.</p></div></article>:<div className="no-mail"><h3>Nessuna email generata</h3><p>Nessuna corrispondenza verificata in questa estrazione. Non significa che i prodotti non siano in offerta: i collegamenti al catalogo sono ancora parziali.</p></div>}
   <p className="muted safety-note">Nessun messaggio è stato spedito. Se premi di nuovo, il sistema ripete ricerca del PDF, download ed estrazione; non ripresenta un dataset statico.</p><button className="text-button" onClick={reset}>Azzera email e risultato della prova</button></section>
   {showData&&<section className="flyer-panel"><h2>Righe lette durante questa prova</h2>{meta.offers.map(o=><div key={o.id} className="flyer-row"><strong>{o.name}</strong><p>{money(o.price)} · pagina {o.page} · {o.status==='matched'?'Collegamento verificato':'Candidata, non usata per gli avvisi'}</p><p className="source-excerpt">{o.rawText}</p>{o.productId&&<button className="text-button" onClick={()=>onProduct(o.productId)}>Apri il prodotto collegato</button>}</div>)}</section>}
  </>}
 </div>
}
