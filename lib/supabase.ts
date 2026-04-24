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
  const { data, error } = await supabase
    .from('rilevazioni_v2')
    .select('*')
    .ilike('nome', `%${query}%`)
    .order('fine_validita', { ascending: false })
    .limit(20)
  
  if (error) throw error
  return data || []
}

export async function getLatestOffer(prodottoNome: string): Promise<Prodotto | null> {
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