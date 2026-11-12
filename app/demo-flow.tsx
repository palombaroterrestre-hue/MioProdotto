'use client'
import {useEffect,useState} from 'react'
import {demoFlyer as flyer,matchingOffers} from '../lib/notifications'
export {demoFlyer} from '../lib/notifications'
import {Saved,products} from '../lib/catalog'
const EMAIL_KEY='mioprodotto.demo.email.v1'
const RUN_KEY='mioprodotto.demo.run.v1'
const money=(n:number)=>n.toLocaleString('it-IT',{style:'currency',currency:'EUR'})
type Run={email:string;watchlist:Saved[];offerIds:string[]}
export default function DemoFlow({saved,ready,onChoose,onProduct}:{saved:Saved[];ready:boolean;onChoose:()=>void;onProduct:(id:string)=>void}){
 const[email,setEmail]=useState(''),[run,setRun]=useState<Run|null>(null),[error,setError]=useState(''),[showFlyer,setShowFlyer]=useState(false)
 useEffect(()=>{try{setEmail(localStorage.getItem(EMAIL_KEY)||'');const raw=localStorage.getItem(RUN_KEY);if(raw){const r=JSON.parse(raw);if(typeof r.email==='string'&&Array.isArray(r.watchlist)&&Array.isArray(r.offerIds))setRun(r)}}catch{setError('Il browser non consente di recuperare la prova precedente. Puoi ripartire qui.')}},[])
 const changed=!!run&&(run.email!==email.trim()||JSON.stringify(run.watchlist)!==JSON.stringify(saved))
 const offers=run?flyer.offers.filter(o=>run.offerIds.includes(o.id)):[]
 const potential=matchingOffers(saved)
 function simulate(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();setError('')
  if(!saved.length){setError('Scegli almeno un prodotto per fare la prova.');return}
  const address=email.trim();if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address)){setError('Inserisci un indirizzo email valido, anche di prova.');return}
  const next={email:address,watchlist:saved.map(x=>({...x})),offerIds:potential.map(o=>o.id)};setRun(next)
  try{localStorage.setItem(EMAIL_KEY,address);localStorage.setItem(RUN_KEY,JSON.stringify(next))}catch{setError('Prova eseguita, ma il browser non permette di salvarla dopo la chiusura.')}
 }
 function reset(){setRun(null);setEmail('');setError('');try{localStorage.removeItem(EMAIL_KEY);localStorage.removeItem(RUN_KEY)}catch{setError('Non riesco a cancellare il salvataggio del browser.')}}
 return <div className="demo-flow">
  <section className="demo-panel" aria-labelledby="demo-title">
   <span className="step-label">2 / LA TUA EMAIL</span><h2 id="demo-title">Proviamo il giorno dopo.</h2>
   <p>Hai scelto i prodotti. Inserisci un'email e controlliamo il volantino Ekom reale, senza aspettare domani.</p>
   <form onSubmit={simulate}>
    <label htmlFor="demo-email">Email per la prova</label><input id="demo-email" type="email" autoComplete="off" placeholder="prova@example.com" value={email} onChange={e=>setEmail(e.target.value)} required/>
    <p className="muted privacy">L'indirizzo resta in questo browser. Nessuna registrazione e nessun invio: vedrai l'email soltanto qui.</p>
    <button className="primary" type="submit" disabled={!ready||!saved.length}>Simula il giorno dopo</button>
   </form>
   {!saved.length&&<button className="text-button" onClick={onChoose}>Prima scegli un prodotto dal catalogo</button>}
   {error&&<p role="alert" className="warning">{error}</p>}
   <p className="muted demo-source"><strong>Dati reali:</strong> {flyer.title}, {flyer.region}, 3-16 novembre 2026. Verificato il 12 novembre. Simuliamo il controllo e la ricezione dell'avviso, non i prezzi.</p>
   <button className="text-button" onClick={()=>setShowFlyer(!showFlyer)} aria-expanded={showFlyer}>{showFlyer?'Chiudi i dati del volantino':'Guarda il volantino usato per il test'}</button>
  </section>
  {run&&<section className="mailbox" aria-labelledby="mail-title">
   <span className="step-label">3 / GIORNO DOPO · SIMULAZIONE</span><h2 id="mail-title">La tua casella di prova</h2>
   {changed&&<p role="status" className="warning">Hai cambiato email o watchlist. Questo è il risultato precedente: premi di nuovo "Simula il giorno dopo" per aggiornarlo.</p>}
   {offers.length?<article className="demo-mail"><div className="mail-meta"><span>EMAIL SIMULATA · NON INVIATA</span><p><strong>A:</strong> {run.email}</p><p><strong>Oggetto:</strong> {offers.length===1?'Un prodotto della tua watchlist è nel volantino Ekom':`${offers.length} offerte per la tua watchlist nel volantino Ekom`}</p></div>
    <div className="mail-body"><p>Ciao! Nel volantino Ekom Black Week del 3-16 novembre abbiamo trovato queste offerte per i prodotti che segui.</p>
     {offers.map(o=><div className="notification-offer" key={o.id}><h3>{o.name}</h3><p>{o.format}</p><p className="notification-price">{o.price!==null?money(o.price):o.discount}</p>{o.condition&&<p className="condition">Solo possessori EKOM UP</p>}{(o.page===9||(o.page===8&&['prosciutto','gorgonzola','tomino'].some(t=>o.name.toLowerCase().includes(t))))&&<p className="condition">Solo reparti con vendita assistita.</p>}<a href={flyer.source+`#page=${o.page}`} target="_blank" rel="noopener noreferrer">Controlla il volantino · pagina {o.page} ↗</a></div>)}
     <p className="muted">Quantità e varianti sono quelle del volantino. Prezzi e disponibilità possono variare nel punto vendita.</p>
    </div></article>:<div className="no-mail"><h3>Nessuna email generata</h3><p>Non abbiamo trovato corrispondenze verificate per questa watchlist nel test. Non equivale a dire che i prodotti non siano in offerta: gli abbinamenti non certi restano esclusi.</p></div>}
   <p className="muted safety-note">Questa schermata non è una conferma di invio. Non c'è un servizio email collegato e non è stato programmato alcun controllo automatico.</p>
   <button className="text-button" onClick={reset}>Azzera email e risultato della prova</button>
  </section>}
  {showFlyer&&<section className="flyer-panel"><h2>Il volantino del test</h2><p>{flyer.title} · Liguria e Piemonte · 3-16 novembre 2026.</p><p className="muted">{flyer.offers.length} offerte e promozioni trascritte dal PDF. {flyer.offers.filter(o=>o.productId).length} collegate a prodotti e formati del catalogo con riscontro; gli altri collegamenti non sono confermati. Un nome simile o un formato diverso non bastano per mandare un avviso.</p><a href={flyer.source} target="_blank" rel="noopener noreferrer">Apri il PDF originale ↗</a>
   <h3>Prodotti pronti per la prova</h3><p className="muted">Puoi sceglierne uno qui, poi seguire il formato indicato oppure tutta la linea.</p>
   <div className="demo-picks">{flyer.offers.filter(o=>o.productId).map(o=><button key={o.id} onClick={()=>onProduct(o.productId)}>{products.find(p=>p.id===o.productId)?.name}<span>{o.format} · {o.price!==null?money(o.price):o.discount}</span></button>)}</div>
   <details><summary>Tutte le offerte trascritte ({flyer.offers.length})</summary>{flyer.offers.map(o=><div className="flyer-row" key={o.id}><strong>{o.name}</strong><p>{o.format} · {o.price!==null?money(o.price):o.discount}{o.condition?' · Solo EKOM UP':''}</p><p className="muted">Pagina {o.page} · {o.productId?'Collegamento verificato':'Collegamento al catalogo non confermato'}</p></div>)}</details>
  </section>}
 </div>
}
