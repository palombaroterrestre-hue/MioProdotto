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

export async function searchProdotti(query: string): Promise<Prodotto[]> {
  const upperQuery = query.toUpperCase()
  
  // Step 1: Find canonical names from aliases
  let canonicalNames = new Set<string>([upperQuery])
  
  const { data: aliasData } = await supabase
    .from('product_aliases')
    .select('canonical_name, alias_name')
    .or(`alias_name.ilike.%${upperQuery}%,canonical_name.ilike.%${upperQuery}%`)
    .limit(20)
  
  if (aliasData && aliasData.length > 0) {
    aliasData.forEach((a: { canonical_name: string; alias_name: string }) => {
      canonicalNames.add(a.canonical_name.toUpperCase())
      canonicalNames.add(a.alias_name.toUpperCase())
    })
  }
  
  // Step 2: Search rilevazioni_v2 for all matching names
  const orConditions = Array.from(canonicalNames).map(n => `nome.ilike.%${n}%`).join(',')
  
  const { data: products, error } = await supabase
    .from('rilevazioni_v2')
    .select('*')
    .or(orConditions)
    .order('fine_validita', { ascending: false })
    .limit(50)
  
  if (error) {
    console.error('Search error:', error)
    return []
  }
  
  if (!products || products.length === 0) {
    return []
  }

  function stripAccents(s: string): string {
    return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim()
  }

  // Build a fast lookup map: normalized alias -> canonical
  const aliasMap = new Map<string, string>()
  for (const a of aliasData || []) {
    aliasMap.set(stripAccents(a.alias_name), stripAccents(a.canonical_name))
  }

  // Step 3: Deduplicate - group by canonical name, keep best offer per group
  const canonicalMap = new Map<string, Prodotto>()

  for (const p of products) {
    const normalizedNome = stripAccents(p.nome)

    // Look up canonical: check if this product is a known alias
    const canonical = aliasMap.get(normalizedNome) ?? normalizedNome

    // Keep the product with the highest discount for each canonical
    const existing = canonicalMap.get(canonical)
    if (!existing) {
      canonicalMap.set(canonical, p)
    } else {
      const newDiscount = Math.abs(p.percentuale_sconto ?? 0)
      const oldDiscount = Math.abs(existing.percentuale_sconto ?? 0)
      if (newDiscount > oldDiscount) {
        canonicalMap.set(canonical, p)
      }
    }
  }

  return Array.from(canonicalMap.values())
}

export async function getLatestOffer(prodottoNome: string): Promise<Prodotto | null> {
  const upperQuery = prodottoNome.toUpperCase()
  
  let searchNames = [upperQuery]
  
  const { data: aliasData } = await supabase
    .from('product_aliases')
    .select('canonical_name, alias_name')
    .or(`alias_name.ilike.%${upperQuery}%,canonical_name.ilike.%${upperQuery}%`)
    .limit(10)
  
  if (aliasData && aliasData.length > 0) {
    aliasData.forEach((a: { canonical_name: string; alias_name: string }) => {
      searchNames.push(a.canonical_name.toUpperCase())
      searchNames.push(a.alias_name.toUpperCase())
    })
    searchNames = [...new Set(searchNames)]
  }
  
  const orConditions = searchNames.map(n => `nome.ilike.%${n}%`).join(',')
  
  const { data, error } = await supabase
    .from('rilevazioni_v2')
    .select('*')
    .or(orConditions)
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