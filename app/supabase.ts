import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

export interface Prodotto {
  id: number
  nome: string
  prezzo: number
  quantita_singola: string
  percentuale_sconto: number
  emoji: string
  tipo_meccanica: string
  inizio_validita: string
  fine_validita: string
  fonte_volantino_link: string
  pagina_num: number
  file_pagina_intera: string
}

export interface WatchlistItem {
  id: number
  nome_prodotto: string
  utente_id: string
  created_at: string
}

const BRANDS = ['CALVE', 'BARILLA', 'BIFFI', 'GALBANI', 'MUTTI', 'CARREFOUR', 'ESELUNGA', 
            'PRONTO', 'SIMPLY', 'HEINZ', 'KRAFT', 'MAGGI', 'KNORR', 'STAR', 'DANONE',
            'NESTLE', 'PERUGINA', 'FERRERO', 'MILKA', 'KINDER', 'MARS']

function normalize(s: string): string {
  return s.toLowerCase().trim()
}

function similarity(a: string, b: string): number {
  const words1 = normalize(a).split(/\s+/)
  const words2 = normalize(b).split(/\s+/)
  
  if (words1.length === 0 || words2.length === 0) return 0
  if (a.toLowerCase() === b.toLowerCase()) return 1
  
  const set1 = new Set(words1)
  const set2 = new Set(words2)
  
  let matches = 0
  for (const w of set1) {
    if (set2.has(w)) matches++
  }
  
  const maxLen = Math.max(words1.length, words2.length)
  return matches / maxLen
}

function hasBrand(name: string): boolean {
  const nameUp = name.toUpperCase()
  return BRANDS.some(b => nameUp.includes(b))
}

function pickCanonical(group: string[]): string {
  const withBrand = group.filter(p => hasBrand(p))
  
  if (withBrand.length > 0) {
    withBrand.sort((a, b) => a.length - b.length)
    return withBrand[0]
  }
  
  const sorted = [...group].sort((a, b) => a.length - b.length)
  return sorted[0]
}

function isSameProductType(a: string, b: string): boolean {
  const types = ['maionese', 'ketchup', 'yogurt', 'pasta', 'riso', 'pomodoro', 'passata',
                'olio', 'latte', 'formaggio', 'prosciutto', 'carne', 'pesce', 'uovo']
  return types.some(t => a.toLowerCase().includes(t) && b.toLowerCase().includes(t))
}

function dedupeResults(products: Prodotto[]): Prodotto[] {
  if (products.length <= 1) return products
  
  const names = products.map(p => p.nome)
  const uniqueNames = [...new Set(names)]
  
  if (uniqueNames.length <= 1) return products
  
  const threshold = 0.75
  const groups: string[][] = []
  const processed = new Set<string>()
  
  for (const name1 of uniqueNames) {
    if (processed.has(name1)) continue
    
    const group: string[] = [name1]
    processed.add(name1)
    
    for (const name2 of uniqueNames) {
      if (processed.has(name2)) continue
      
      const sim = similarity(name1, name2)
      if (sim >= threshold && isSameProductType(name1, name2)) {
        group.push(name2)
        processed.add(name2)
      }
    }
    
    if (group.length > 1) {
      groups.push(group)
    }
  }
  
  if (groups.length === 0) return products
  
  const canonicalName = pickCanonical(groups[0])
  
  return products.filter(p => p.nome === canonicalName)
}

export async function searchProdotti(query: string): Promise<Prodotto[]> {
  const upperQuery = query.toUpperCase()
  
  const { data, error } = await supabase
    .from('rilevazioni_v2')
    .select('*')
    .ilike('nome', `%${upperQuery}%`)
    .order('fine_validita', { ascending: false })
    .limit(20)
  
  if (error) {
    console.error('Search error:', error)
    return []
  }
  
  const results = data || []
  
  if (results.length > 1) {
    return dedupeResults(results)
  }
  
  return results
}

export async function getLatestOffer(prodottoNome: string): Promise<Prodotto | null> {
  const upperQuery = prodottoNome.toUpperCase()
  
  const { data, error } = await supabase
    .from('rilevazioni_v2')
    .select('*')
    .ilike('nome', `%${upperQuery}%`)
    .order('fine_validita', { ascending: false })
    .limit(1)
    .single()
  
  if (error) return null
  return data
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