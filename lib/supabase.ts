import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

// Catalogo pulito v7: i prodotti attivi stanno in v7_prodotti.
// Le offerte si raggiungono via v7_alias -> v6_prodotti_canonici -> v6_offerte,
// con le date di validita' in v6_pagine -> v6_volantini.

export interface Prodotto {
  id: number
  marca: string | null
  tipo: string
  variante: string | null
  quantita_valore: number | null
  quantita_unita: string | null
  n_offerte: number
  nome: string     // marca + tipo + variante, pronto per la UI
  quantita: string // es. "250 g"
}

export interface OffertaProdotto {
  id: number
  prezzo: number
  promo: string | null
  valido_dal: string | null
  valido_al: string | null
}

export interface OffertaCorrente {
  id: number
  title: string
  price: string
  pieces: string
  subtitle: string | null
  weight_price: string
  start_date: string
  end_date: string
  image_url: string | null
}

export interface WatchlistItem {
  id: number
  nome_prodotto: string
  utente_id: string
  created_at: string
}

function stripAccents(s: string): string {
  return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim()
}

function toProdotto(r: any): Prodotto {
  const nome = [r.marca, r.tipo, r.variante].filter(Boolean).join(' ')
  const quantita =
    r.quantita_valore != null
      ? `${r.quantita_valore} ${r.quantita_unita || ''}`.trim()
      : ''
  return { ...r, nome, quantita }
}

let catalogoCache: Prodotto[] | null = null

// Scarica tutto il catalogo attivo (poche migliaia di righe) una sola volta:
// la ricerca e' poi locale e insensibile agli accenti (CAFFE trova CAFFÈ).
export async function getCatalogo(): Promise<Prodotto[]> {
  if (catalogoCache) return catalogoCache
  const PAGE = 1000
  const righe: any[] = []
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await supabase
      .from('v7_prodotti')
      .select('id,marca,tipo,variante,quantita_valore,quantita_unita,n_offerte')
      .eq('attivo', true)
      .order('id')
      .range(from, from + PAGE - 1)
    if (error || !data) break
    righe.push(...data)
    if (data.length < PAGE) break
  }
  catalogoCache = righe.map(toProdotto)
  return catalogoCache
}

export async function searchProdotti(query: string): Promise<Prodotto[]> {
  const q = stripAccents(query)
  if (!q) return []
  const catalogo = await getCatalogo()
  const termini = q.split(/\s+/)
  const trovati = catalogo.filter((p) => {
    const testo = stripAccents(p.nome)
    return termini.every((t) => testo.includes(t))
  })
  trovati.sort((a, b) => b.n_offerte - a.n_offerte)
  return trovati.slice(0, 50)
}

// Per ogni prodotto v7, le sue offerte (max 3, dalla piu' recente).
export async function getOffertePerProdotti(
  prodottoIds: number[]
): Promise<Record<number, OffertaProdotto[]>> {
  const vuoto: Record<number, OffertaProdotto[]> = {}
  if (prodottoIds.length === 0) return vuoto

  const { data: aliasRows, error: errAlias } = await supabase
    .from('v7_alias')
    .select('prodotto_id,v6_prodotto_id')
    .in('prodotto_id', prodottoIds)
  if (errAlias || !aliasRows) return vuoto

  const v6ToV7 = new Map<number, number>()
  for (const r of aliasRows) v6ToV7.set(r.v6_prodotto_id, r.prodotto_id)
  const v6Ids = Array.from(v6ToV7.keys())
  if (v6Ids.length === 0) return vuoto

  const { data: offerte, error: errOfferte } = await supabase
    .from('v6_offerte')
    .select('id,prodotto_id,prezzo,promo,pagina_id')
    .in('prodotto_id', v6Ids)
  if (errOfferte || !offerte || offerte.length === 0) return vuoto

  const paginaIds = Array.from(new Set(offerte.map((o) => o.pagina_id)))
  const { data: pagine } = await supabase
    .from('v6_pagine')
    .select('id,volantino_id')
    .in('id', paginaIds)
  const paginaToVolantino = new Map<number, number>(
    (pagine || []).map((p) => [p.id, p.volantino_id])
  )

  const volantinoIds = Array.from(
    new Set((pagine || []).map((p) => p.volantino_id))
  )
  const { data: volantini } = await supabase
    .from('v6_volantini')
    .select('id,valido_dal,valido_al')
    .in('id', volantinoIds)
  const volantinoDate = new Map<number, { dal: string | null; al: string | null }>(
    (volantini || []).map((v) => [v.id, { dal: v.valido_dal, al: v.valido_al }])
  )

  const risultato: Record<number, OffertaProdotto[]> = {}
  for (const o of offerte) {
    const v7id = v6ToV7.get(o.prodotto_id)
    if (!v7id) continue
    const volId = paginaToVolantino.get(o.pagina_id)
    const date = volId ? volantinoDate.get(volId) : undefined
    ;(risultato[v7id] ||= []).push({
      id: o.id,
      prezzo: o.prezzo,
      promo: o.promo,
      valido_dal: date?.dal || null,
      valido_al: date?.al || null,
    })
  }
  for (const lista of Object.values(risultato)) {
    lista.sort((a, b) => (b.valido_al || '').localeCompare(a.valido_al || ''))
    lista.splice(3)
  }
  return risultato
}

export async function getCurrentOffers(): Promise<OffertaCorrente[]> {
  try {
    const resp = await fetch('/api/current-offers')
    if (!resp.ok) return []
    const data = await resp.json()
    return (data || []).map((o: any) => ({
      id: o.ID,
      title: o.TITLE,
      price: o.PRICE,
      pieces: o.PIECES,
      subtitle: o.SUBTITLE,
      weight_price: o.WEIGHT_PRICE,
      start_date: o.START_DATE,
      end_date: o.END_DATE,
      image_url: o.IMAGE?.location || null,
    }))
  } catch {
    return []
  }
}

export async function addToWatchlist(nomeProdotto: string, utenteId: string) {
  const { data, error } = await supabase
    .from('watchlist')
    .insert({ nome_prodotto: nomeProdotto.toUpperCase(), utente_id: utenteId })
    .select()

  if (error) throw error
  return data
}

export async function getWatchlist(utenteId: string): Promise<WatchlistItem[]> {
  const { data, error } = await supabase
    .from('watchlist')
    .select('*')
    .eq('utente_id', utenteId)
    .order('created_at', { ascending: false })

  if (error) throw error
  return data || []
}
