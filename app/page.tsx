'use client'

import { useEffect, useState } from 'react'
import { products, Product, Saved, same, readSaved, STORAGE_KEY } from '../lib/catalog'

type Screen = { view: 'catalog' | 'list' } | { view: 'detail'; productId: string; returnTo: 'catalog' | 'list' }
export default function Home() {
  const [screen, setScreen] = useState<Screen>({ view: 'catalog' })
  const [query, setQuery] = useState('')
  const [saved, setSaved] = useState<Saved[]>([])
  const [ready, setReady] = useState(false)
  const [warning, setWarning] = useState('')
  const [selected, setSelected] = useState('')
  const [notice, setNotice] = useState('')
  useEffect(() => {
    try { setSaved(readSaved(localStorage.getItem(STORAGE_KEY))) }
    catch { setWarning('Non riesco a leggere la lista salvata. Puoi usarla in questa sessione, ma il salvataggio precedente non è disponibile.') }
    setReady(true)
  }, [])
  function changeSaved(next: Saved[]) {
    setSaved(next)
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); setWarning('') }
    catch { setWarning('Il browser non permette il salvataggio. La lista resterà disponibile solo finché questa pagina è aperta.') }
  }
  function go(next: Screen) { setScreen(next); setNotice(''); window.scrollTo({ top: 0 }) }
  function open(product: Product, returnTo: 'catalog' | 'list', formatId?: string) {
    setSelected(formatId || (product.formats.length === 1 ? product.formats[0].id : ''))
    go({ view: 'detail', productId: product.id, returnTo })
  }
  const product = screen.view === 'detail' ? products.find(p => p.id === screen.productId) : undefined
  const target = product && selected ? { productId: product.id, formatId: selected } : undefined
  const isSaved = !!target && saved.some(x => same(x, target))
  const filter = query.toLocaleLowerCase('it').trim()
  const filtered = products.filter(p => [p.name, p.brand, p.summary, ...p.formats.map(f => f.label)].join(' ').toLocaleLowerCase('it').includes(filter))
  return <main className="app">
    <header className="brand"><span>1 / MIOPRODOTTO</span><p>Versione di prova · 2 prodotti verificati</p></header>
    {warning && <p className="warning" role="alert">{warning}</p>}
    {screen.view === 'catalog' && <section aria-labelledby="catalog-title">
      <h1 id="catalog-title">Riconosci. Scegli. Segui.</h1>
      <label className="sr-only" htmlFor="search">Cerca un prodotto</label>
      <input id="search" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Cerca un prodotto" />
      <h2>Prodotti</h2>
      <div className="grid">{filtered.map(p => <button className="product-card" key={p.id} onClick={() => open(p, 'catalog')} aria-label={`Vedi dettagli: ${p.name}`}>
        <img src={p.image} alt={`${p.brand} ${p.name}${p.imageNote ? ', confezione media da 20 pezzi' : ', 400 g'}`} />
        <strong>{p.id.startsWith('pan-') ? 'Pan Bauletto' : p.name}</strong><span>{p.brand} · {p.summary}</span><span className="card-link">Vedi dettagli</span>
      </button>)}</div>
      {filtered.length === 0 && <p className="empty">Nessun prodotto trovato in questo primo insieme. Prova "Pan Bauletto" o "Domo Pak".</p>}
      <p className="muted after-grid">Foto e formati prima di aggiungere alla lista.</p>
    </section>}
    {product && screen.view === 'detail' && <section aria-labelledby="detail-title">
      <button className="back" onClick={() => go({ view: screen.returnTo })}>‹ {screen.returnTo === 'list' ? 'La mia lista' : 'Catalogo'}</button>
      <img className={`hero ${product.formats.length > 1 ? 'short' : ''}`} src={product.image} alt={`${product.brand} ${product.name}`} />
      <h1 id="detail-title">{product.name}</h1>
      <p className="intro">{product.brand}{product.formats.length === 1 ? ` · ${product.formats[0].label}` : ''}</p>
      {product.formats.length > 1 && <fieldset><legend>Formati nella stessa offerta</legend><div className="formats">{product.formats.map(f => <label className={`format ${selected === f.id ? 'chosen' : ''}`} key={f.id}><input type="radio" name="format" value={f.id} checked={selected === f.id} onChange={() => { setSelected(f.id); setNotice('') }} /><span>{f.label}</span></label>)}</div><p className="muted photo-note">{product.imageNote}</p></fieldset>}
      <div className="offer"><p className="eyebrow">OFFERTA STORICA</p><strong className="price">{product.price}</strong><p className="muted">Volantino {product.period} · non attuale</p><a href={product.source} target="_blank" rel="noopener noreferrer">Vedi il volantino originale ↗</a></div>
      <button className="primary" disabled={!ready || !target || isSaved} onClick={() => { if (target && !isSaved) { changeSaved([...saved, target]); setNotice('Prodotto aggiunto alla tua lista.') } }}>{isSaved ? 'Aggiunto alla mia lista ✓' : !selected ? 'Scegli un formato per seguire' : '+ Aggiungi alla mia lista'}</button>
      <p className="status" role="status">{notice}</p>
    </section>}
    {screen.view === 'list' && <section aria-labelledby="list-title">
      <h1 id="list-title">La mia lista</h1><p className="intro">I prodotti che vuoi seguire.</p>
      {!ready ? <p>Caricamento lista…</p> : saved.length === 0 ? <div className="empty"><p>La tua lista è ancora vuota.</p><button className="text-button" onClick={() => go({ view: 'catalog' })}>Scegli un prodotto dal catalogo</button></div> : <div className="saved-list">{saved.map(item => {
        const p = products.find(p => p.id === item.productId)!
        const f = p.formats.find(f => f.id === item.formatId)!
        return <article className="saved-card" key={`${p.id}/${f.id}`}><img src={p.image} alt={`${p.brand} ${p.name}`} /><div><h2>{p.name}</h2><p className="muted">{p.brand} · {f.label}</p>{p.imageNote && <p className="muted photo-note">{p.imageNote}</p>}<button className="text-button" onClick={() => open(p, 'list', f.id)}>Apri storico offerte</button><button className="remove" aria-label={`Rimuovi ${p.name} ${f.label} dalla lista`} onClick={() => { changeSaved(saved.filter(x => !same(x, item))); setNotice('Prodotto rimosso dalla lista.') }}>Rimuovi dalla lista</button></div></article>
      })}</div>}
      <aside className="local-note"><strong>{warning ? 'Salvataggio non disponibile' : 'Salvata in questo browser'}</strong><p>{warning ? 'Per ora puoi usare la lista in questa pagina. Non fare affidamento sul salvataggio dopo la chiusura.' : 'La ritrovi quando riapri sullo stesso telefono e browser. Nessun account o sincronizzazione in questa prova. Se cancelli i dati del browser, la lista si perde.'}</p></aside><p className="status" role="status">{notice}</p>
    </section>}
    <nav aria-label="Navigazione principale"><button aria-current={screen.view === 'catalog' ? 'page' : undefined} onClick={() => go({ view: 'catalog' })}>Catalogo</button><button aria-current={screen.view === 'list' ? 'page' : undefined} onClick={() => go({ view: 'list' })}>La mia lista{ready && saved.length > 0 ? ` (${saved.length})` : ''}</button></nav>
  </main>
}
