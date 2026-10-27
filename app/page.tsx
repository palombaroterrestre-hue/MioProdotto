'use client'
import { useEffect, useMemo, useState } from 'react'
import { products, Product, Saved, same, readSaved, STORAGE_KEY } from '../lib/catalog'
type Screen={view:'catalog'|'list'}|{view:'detail';productId:string;returnTo:'catalog'|'list'}
function normalized(s:string){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('it')}
function Photo({src,alt,className=''}:{src:string;alt:string;className?:string}){
 const [failed,setFailed]=useState(false)
 useEffect(()=>setFailed(false),[src])
 return src&&!failed?<img className={className} src={src} alt={alt} loading="lazy" onError={()=>setFailed(true)}/>:<div className={`no-photo ${className}`} role="img" aria-label="Foto non disponibile">Foto non disponibile</div>
}
export default function Home(){
 const [screen,setScreen]=useState<Screen>({view:'catalog'}),[query,setQuery]=useState(''),[saved,setSaved]=useState<Saved[]>([]),[ready,setReady]=useState(false),[warning,setWarning]=useState(''),[selected,setSelected]=useState(''),[notice,setNotice]=useState(''),[limit,setLimit]=useState(40)
 useEffect(()=>{try{setSaved(readSaved(localStorage.getItem(STORAGE_KEY)))}catch{setWarning('Non riesco a leggere la lista salvata. Puoi usarla in questa sessione, ma il salvataggio precedente non è disponibile.')}setReady(true)},[])
 function changeSaved(next:Saved[]){setSaved(next);try{localStorage.setItem(STORAGE_KEY,JSON.stringify(next));setWarning('')}catch{setWarning('Il browser non permette il salvataggio. La lista resterà disponibile solo finché questa pagina è aperta.')}}
 function go(next:Screen){setScreen(next);setNotice('');window.scrollTo({top:0})}
 function open(p:Product,returnTo:'catalog'|'list',formatId?:string){setSelected(formatId||(p.formats.length===1?p.formats[0].id:''));go({view:'detail',productId:p.id,returnTo})}
 const product=screen.view==='detail'?products.find(p=>p.id===screen.productId):undefined
 const format=product?.formats.find(f=>f.id===selected)
 const target=product&&format?{productId:product.id,formatId:format.id}:undefined
 const isSaved=!!target&&saved.some(x=>same(x,target))
 const filtered=useMemo(()=>{const terms=normalized(query).trim().split(/\s+/).filter(Boolean);return products.filter(p=>{const text=normalized([p.name,p.brand,p.summary,...p.formats.map(f=>f.label)].join(' '));return terms.every(t=>text.includes(t))})},[query])
 const shownOffers=product?product.offers.filter(o=>!format||format.offerIds.includes(o.id)):[]
 return <main className="app">
  <header className="brand"><span>1 / MIOPRODOTTO</span><p>Catalogo da fonti verificate · offerte storiche</p></header>
  {warning&&<p className="warning" role="alert">{warning}</p>}
  {screen.view==='catalog'&&<section aria-labelledby="catalog-title">
   <h1 id="catalog-title">Riconosci. Scegli. Segui.</h1>
   <label className="sr-only" htmlFor="search">Cerca un prodotto</label><input id="search" type="search" value={query} onChange={e=>{setQuery(e.target.value);setLimit(40)}} placeholder="Cerca prodotto, marca o formato"/>
   <h2>Prodotti</h2><p className="muted results-count" role="status">{filtered.length.toLocaleString('it')} schede{query?' trovate':''}</p>
   <div className="grid">{filtered.slice(0,limit).map(p=><button className="product-card" key={p.id} onClick={()=>open(p,'catalog')} aria-label={`Vedi dettagli: ${p.name}`}><Photo src={p.image} alt={`Ritaglio dell'offerta: ${p.name}`}/><strong>{p.name}</strong>{p.summary&&<span>{p.summary}</span>}{p.assortment&&<span>Varianti dell'offerta</span>}<span className="card-link">{p.offers.length} {p.offers.length===1?'offerta storica':'offerte storiche'} · Vedi dettagli</span></button>)}</div>
   {!filtered.length&&<p className="empty">Nessun prodotto trovato. Prova un nome, una marca o un formato diverso.</p>}
   {filtered.length>limit&&<button className="primary more" onClick={()=>setLimit(limit+40)}>Mostra altri 40 prodotti</button>}
   <p className="muted after-grid">Dati selezionati dalle fonti. Le informazioni contraddittorie o non verificabili sono escluse. Le foto sono ritagli dei volantini; possono raffigurare un assortimento.</p>
  </section>}
  {product&&screen.view==='detail'&&<section aria-labelledby="detail-title">
   <button className="back" onClick={()=>go({view:screen.returnTo})}>‹ {screen.returnTo==='list'?'La mia lista':'Catalogo'}</button>
   <Photo className="hero" src={product.image} alt={`Ritaglio dell'offerta: ${product.name}`}/><p className="muted photo-note">{product.imageNote}</p>
   <h1 id="detail-title">{product.name}</h1>{product.brand&&<p className="intro">{product.brand}</p>}
   {product.facts.length>0&&<ul className="facts">{product.facts.map((f,i)=><li key={i}>{f}</li>)}</ul>}
   {product.formats.length>1&&<fieldset><legend>Scegli la variante da salvare</legend><div className="formats">{product.formats.map(f=><label className={`format ${selected===f.id?'chosen':''}`} key={f.id}><input type="radio" name="format" value={f.id} checked={selected===f.id} onChange={()=>{setSelected(f.id);setNotice('')}}/><span>{f.label}</span></label>)}</div><p className="muted photo-note">Le alternative restano distinte nella lista. Un prezzo dell'assortimento non prova che tutte le confezioni siano identiche.</p></fieldset>}
   <button className="primary" disabled={!ready||!target||isSaved} onClick={()=>{if(target&&!isSaved){changeSaved([...saved,target]);setNotice('Prodotto aggiunto alla tua lista.')}}}>{isSaved?'Aggiunto alla mia lista ✓':!selected?'Scegli una variante per seguire':'+ Aggiungi alla mia lista'}</button><p className="status" role="status">{notice}</p>
   <h2>Storico delle offerte</h2><p className="muted">Le offerte sono raggruppate secondo le prove disponibili. Formati o varianti diversi restano distinti.</p><p className="muted">Prezzi storici, non offerte attuali. Le date non verificate non sono mostrate: consulta il volantino originale.</p>
   {shownOffers.map(o=><article className="offer" key={o.id}><p className="eyebrow">OFFERTA STORICA · VOLANTINO {o.flyer} · PAGINA {o.page}</p><strong className="price">{o.starting?'da ':''}{o.price.toLocaleString('it-IT',{style:'currency',currency:'EUR'})} {o.priceUnit}</strong><p className="offer-caption">{o.caption}</p>{o.promo&&<p className="muted">{o.promo}</p>}<a href={o.source} target="_blank" rel="noopener noreferrer">Vedi il volantino originale ↗</a></article>)}
  </section>}
  {screen.view==='list'&&<section aria-labelledby="list-title"><h1 id="list-title">La mia lista</h1><p className="intro">I prodotti che vuoi seguire.</p>
   {!ready?<p>Caricamento lista…</p>:!saved.length?<div className="empty"><p>La tua lista è ancora vuota.</p><button className="text-button" onClick={()=>go({view:'catalog'})}>Scegli un prodotto dal catalogo</button></div>:<div className="saved-list">{saved.map(item=>{const p=products.find(p=>p.id===item.productId)!,f=p.formats.find(f=>f.id===item.formatId)!;return <article className="saved-card" key={`${p.id}/${f.id}`}><Photo src={p.image} alt={`Ritaglio dell'offerta: ${p.name}`}/><div><h2>{p.name}</h2><p className="muted">{f.label}</p><p className="muted photo-note">{p.imageNote}</p><button className="text-button" onClick={()=>open(p,'list',f.id)}>Apri storico offerte</button><button className="remove" aria-label={`Rimuovi ${p.name} ${f.label} dalla lista`} onClick={()=>{changeSaved(saved.filter(x=>!same(x,item)));setNotice('Prodotto rimosso dalla lista.')}}>Rimuovi dalla lista</button></div></article>})}</div>}
   <aside className="local-note"><strong>{warning?'Salvataggio non disponibile':'Salvata in questo browser'}</strong><p>{warning?'Puoi usare la lista in questa pagina. Non fare affidamento sul salvataggio dopo la chiusura.':'La ritrovi sullo stesso telefono e browser. Nessun account, sincronizzazione o avviso automatico sui prezzi. Se cancelli i dati del browser, la lista si perde.'}</p></aside><p className="status" role="status">{notice}</p>
  </section>}
  <nav aria-label="Navigazione principale"><button aria-current={screen.view==='catalog'?'page':undefined} onClick={()=>go({view:'catalog'})}>Catalogo</button><button aria-current={screen.view==='list'?'page':undefined} onClick={()=>go({view:'list'})}>La mia lista{ready&&saved.length?` (${saved.length})`:''}</button></nav>
 </main>
}
