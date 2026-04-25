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
  
  // Get canonical name from aliases
  const { data: aliasData } = await supabase
    .from('product_aliases')
    .select('canonical_name')
    .or(`alias_name.ilike.%${upperQuery}%,canonical_name.ilike.%${upperQuery}%`)
    .limit(1)
  
  // Build search conditions: query + any alias matches
  let searchQuery = supabase
    .from('rilevazioni_v2')
    .select('*')
    .or(`nome.ilike.%${upperQuery}%`, { foreignTable: 'product_aliases' })

  if (aliasData && aliasData.length > 0) {
    const aliasNames = aliasData.map((a: { canonical_name: string }) => a.canonical_name)
    const uniqueNames = [...new Set([upperQuery, ...aliasNames])]
    const orConditions = uniqueNames.map(n => `nome.ilike.%${n}%`).join(',')
    
    const { data, error } = await supabase
      .from('rilevazioni_v2')
      .select('*')
      .or(orConditions)
      .order('fine_validita', { ascending: false })
      .limit(20)
    
    if (error) throw error
    return data || []
  }

  const { data, error } = await supabase
    .from('rilevazioni_v2')
    .select('*')
    .ilike('nome', `%${upperQuery}%`)
    .order('fine_validita', { ascending: false })
    .limit(20)
  
  if (error) throw error
  return data || []
}

export async function getLatestOffer(prodottoNome: string): Promise<Prodotto | null> {
  const upperQuery = prodottoNome.toUpperCase()
  
  const { data: aliasData } = await supabase
    .from('product_aliases')
    .select('canonical_name')
    .or(`alias_name.ilike.%${upperQuery}%,canonical_name.ilike.%${upperQuery}%`)
    .limit(5)
  
  if (aliasData && aliasData.length > 0) {
    const aliasNames = aliasData.map((a: { canonical_name: string }) => a.canonical_name)
    const uniqueNames = [...new Set([upperQuery, ...aliasNames])]
    const orConditions = uniqueNames.map(n => `nome.ilike.%${n}%`).join(',')
    
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

  const { data, error } = await supabase
    .from('rilevazioni_v2')
    .select('*')
    .ilike('nome', `%${prodottoNome}%`)
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