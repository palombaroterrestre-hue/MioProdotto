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
  
  // Step 3: Deduplicate by canonical name - keep only latest per canonical
  const canonicalMap = new Map<string, Prodotto>()
  
  for (const p of products) {
    // Find best canonical match
    let bestCanonical = p.nome.toUpperCase()
    let minDistance = 999
    
    // Check if this product matches any known alias
    for (const a of aliasData || []) {
      const aliasUpper = a.alias_name.toUpperCase()
      const canonicalUpper = a.canonical_name.toUpperCase()
      
      if (p.nome.toUpperCase().includes(aliasUpper) || p.nome.toUpperCase() === aliasUpper) {
        // Calculate similarity to canonical
        const dist = levenshteinDistance(p.nome.toUpperCase(), canonicalUpper)
        if (dist < minDistance) {
          minDistance = dist
          bestCanonical = canonicalUpper
        }
      }
    }
    
    // Only keep first (latest) for each canonical
    if (!canonicalMap.has(bestCanonical)) {
      canonicalMap.set(bestCanonical, p)
    }
  }
  
  return Array.from(canonicalMap.values())
}

// Simple Levenshtein distance for fuzzy matching
function levenshteinDistance(a: string, b: string): number {
  if (a.length === 0) return b.length
  if (b.length === 0) return a.length
  
  const matrix = []
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i]
  }
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j
  }
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1]
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        )
      }
    }
  }
  return matrix[b.length][a.length]
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