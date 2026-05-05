import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

export interface Prodotto {
  id: number
  nome: string
  alias: string | null           // NUOVO: colonna alias nella tabella product
  prezzo: number
  quantita_singola: string
  sconto_percentuale: number      // FIX 3: era percentuale_sconto
  percentuale_sconto: number      // FIX 3: tenuto per compatibilità
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

function stripAccents(s: string): string {
  return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim()
}

export async function searchProdotti(query: string): Promise<Prodotto[]> {
  // Simple approach: just search with the query as-is (uppercase)
  const upperQuery = query.toUpperCase()
  
  console.log('=== SEARCH ===')
  console.log('Query:', query, '->', upperQuery)
  
  // Search both with and without accent marks
  // è → e, É → E, etc. in uppercase
  const noAccent = upperQuery.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  
  // Try search with multiple variations
  const searchPattern = `nome.ilike.%${noAccent}%,nome.ilike.%${upperQuery}%,alias.ilike.%${noAccent}%,alias.ilike.%${upperQuery}%`
  console.log('Pattern:', searchPattern)
  
  const { data: products, error } = await supabase
    .from('product')
    .select('*')
    .or(searchPattern)
    .order('fine_validita', { ascending: false })
    .limit(50)

  if (error) {
    console.error('Search error:', error)
    return []
  }

  console.log('Results count:', products?.length || 0)
  
  if (!products || products.length === 0) {
    console.log('No results!')
    return []
  }

  // Deduplicate - group by alias (canonical), keep best offer per group
  const aliasMap = new Map<string, Prodotto>()
  
  console.log('=== DEDUP ===')
  console.log('Total products before dedup:', products.length)

  for (const p of products) {
    // Use alias if available, otherwise use nome
    const groupKey = p.alias ? stripAccents(p.alias) : stripAccents(p.nome)
    console.log('Product:', p.nome, '-> groupKey:', groupKey, '-> sconto:', p.sconto_percentuale)

    const existing = aliasMap.get(groupKey)
    if (!existing) {
      aliasMap.set(groupKey, p)
    } else {
      const newDiscount = Math.abs(p.sconto_percentuale ?? p.percentuale_sconto ?? 0)
      const oldDiscount = Math.abs(existing.sconto_percentuale ?? existing.percentuale_sconto ?? 0)
      console.log('  Existing:', existing.nome, 'sconto:', oldDiscount)
      if (newDiscount > oldDiscount) {
        aliasMap.set(groupKey, p)
        console.log('  -> REPLACED')
      }
    }
  }
  
  console.log('After dedup:', aliasMap.size)

  return Array.from(aliasMap.values())
}

export async function getLatestOffer(prodottoNome: string): Promise<Prodotto | null> {
  const upperQuery = stripAccents(prodottoNome)

  // Search on nome or alias column
  const { data, error } = await supabase
    .from('product')
    .select('*')
    .or(`nome.ilike.%${upperQuery}%,alias.ilike.%${upperQuery}%`)
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
