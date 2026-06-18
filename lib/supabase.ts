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
  categoria: string
  tipo_meccanica: string
  inizio_promozione: string
  fine_promozione: string
  link_volantino: string
  pagina_num: number
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

export const CATEGORIA_TO_EMOJI: Record<string, string> = {
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

export async function getCategorie(): Promise<{ categoria: string; emoji: string }[]> {
  try {
    const { data, error } = await supabase
      .from('rilevazioni_v4')
      .select('categoria')
      .not('categoria', 'is', null)
    if (error || !data) return []
    const seen = new Set<string>()
    const result: { categoria: string; emoji: string }[] = []
    for (const r of data) {
      const cat = r.categoria
      if (cat && !seen.has(cat)) {
        seen.add(cat)
        result.push({ categoria: cat, emoji: CATEGORIA_TO_EMOJI[cat] || '\u{1F6D2}' })
      }
    }
    result.sort((a, b) => a.categoria.localeCompare(b.categoria))
    return result
  } catch {
    return []
  }
}

export async function searchProdotti(query: string, categoria?: string): Promise<Prodotto[]> {
  const upperQuery = query.toUpperCase()
  const noAccent = upperQuery.normalize('NFD').replace(/[\u0300-\u036f]/g, '')

  const searchPattern = `nome_prodotto.ilike.%${noAccent}%,nome_prodotto.ilike.%${upperQuery}%,alias.ilike.%${noAccent}%,alias.ilike.%${upperQuery}%`

  let queryBuilder = supabase
    .from('rilevazioni_v4')
    .select('*')
    .or(searchPattern)

  if (categoria) {
    queryBuilder = queryBuilder.eq('categoria', categoria)
  }

  const { data: products, error } = await queryBuilder
    .order('fine_promozione', { ascending: false })
    .limit(50)

  if (error || !products) return []

  const mapped = products.map(mapCategoria)

  const aliasMap = new Map<string, Prodotto>()
  for (const p of mapped) {
    const groupKey = p.alias ? stripAccents(p.alias) : stripAccents(p.nome_prodotto)
    const existing = aliasMap.get(groupKey)
    if (!existing || p.fine_promozione > existing.fine_promozione) {
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
  return mapCategoria(data)
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
