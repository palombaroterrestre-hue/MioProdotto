import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

export interface Prodotto {
  id: number
  nome_prodotto: string
  alias: string | null
  prezzo: number
  quantita: string
  sconto: number
  emoji: string
  tipo_meccanica: string
  inizio_promozione: string
  fine_promozione: string
  link_volantino: string
  pagina_num: number
  file_pagina_intera: string
  image_url: string | null
}

export interface WatchlistItem {
  id: number
  nome_prodotto: string
  utente_id: string
  created_at: string
}

const CATEGORIA_TO_EMOJI: Record<string, string> = {
  'LATTICINI': '\u{1F95B}', 'FORMAGGI': '\u{1F9C0}', 'CARNE': '\u{1F356}',
  'PESCE': '\u{1F41F}', 'ORTOFRUTTA': '\u{1F34E}', 'PANE': '\u{1F35E}',
  'PASTA': '\u{1F35D}', 'CAFFE': '\u2615', 'DOLCI': '\u{1F36A}',
  'BEVANDE': '\u{1F964}', 'SURGELATI': '\u{1F9CA}', 'CONSERVE': '\u{1F96B}',
  'IGIENE': '\u{1F9FB}', 'ANIMALI': '\u{1F436}',
}

function stripAccents(s: string): string {
  return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim()
}

function mapCategoria(r: any): Prodotto {
  return { ...r, emoji: CATEGORIA_TO_EMOJI[r.categoria] || '\u{1F6D2}' }
}

export async function searchProdotti(query: string): Promise<Prodotto[]> {
  const upperQuery = query.toUpperCase()
  const noAccent = upperQuery.normalize('NFD').replace(/[\u0300-\u036f]/g, '')

  const searchPattern = `nome_prodotto.ilike.%${noAccent}%,nome_prodotto.ilike.%${upperQuery}%,alias.ilike.%${noAccent}%,alias.ilike.%${upperQuery}%`

  const { data: products, error } = await supabase
    .from('rilevazioni_v4')
    .select('*')
    .or(searchPattern)
    .order('fine_promozione', { ascending: false })
    .limit(50)

  if (error || !products) return []

  const pages = [...new Set(products.map(p => p.file_pagina_intera).filter(Boolean))]
  const { data: volantinoPages } = await supabase
    .from('volantino_pagine')
    .select('nome_file, image_url')
    .in('nome_file', pages)

  const imageMap = new Map<string, string>()
  if (volantinoPages) {
    for (const vp of volantinoPages) {
      if (vp.image_url) imageMap.set(vp.nome_file, vp.image_url)
    }
  }

  const mapped = products.map(p => ({ ...mapCategoria(p), image_url: imageMap.get(p.file_pagina_intera) || null }))

  const aliasMap = new Map<string, Prodotto>()
  for (const p of mapped) {
    const groupKey = p.alias ? stripAccents(p.alias) : stripAccents(p.nome_prodotto)
    const existing = aliasMap.get(groupKey)
    if (!existing || (p.sconto ?? 0) > (existing.sconto ?? 0)) {
      aliasMap.set(groupKey, p)
    }
  }

  return Array.from(aliasMap.values())
}

export async function getLatestOffer(prodottoNome: string): Promise<Prodotto | null> {
  const upperQuery = stripAccents(prodottoNome)

  const { data, error } = await supabase
    .from('rilevazioni_v4')
    .select('*')
    .or(`nome_prodotto.ilike.%${upperQuery}%,alias.ilike.%${upperQuery}%`)
    .order('fine_promozione', { ascending: false })
    .limit(1)
    .single()

  if (error || !data) return null
  const prodotto = mapCategoria(data)
  if (prodotto.file_pagina_intera) {
    const { data: vp } = await supabase
      .from('volantino_pagine')
      .select('image_url')
      .eq('nome_file', prodotto.file_pagina_intera)
      .limit(1)
      .single()
    prodotto.image_url = vp?.image_url || null
  }
  return prodotto
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
