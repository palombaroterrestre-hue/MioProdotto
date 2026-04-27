'use client'
import { useState } from 'react'
import { searchProdotti, addToWatchlist, getWatchlist, getLatestOffer, Prodotto, WatchlistItem } from '../lib/supabase'

export default function Home() {
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<Prodotto[]>([])
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [loading, setLoading] = useState(false)
  const [utenteId] = useState('user-' + Math.random().toString(36).substr(2, 9))

  const handleSearch = async () => {
    if (!search.trim()) return
    setLoading(true)
    try {
      const prodotti = await searchProdotti(search)
      setResults(prodotti)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const handleAddToWatchlist = async (nome: string) => {
    try {
      await addToWatchlist(nome, utenteId)
      loadWatchlist()
    } catch (e) {
      console.error(e)
    }
  }

  const loadWatchlist = async () => {
    const items = await getWatchlist(utenteId)
    setWatchlist(items)
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-emerald-600 text-white p-4">
        <h1 className="text-2xl font-bold">MioProdotto</h1>
        <p className="text-emerald-100">Trova le migliori offerte nei volantini Ekom</p>
      </header>

      {/* Search */}
      <div className="p-4 bg-white shadow">
        <div className="flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Cerca un prodotto... (es: UOVA, LATTE, PANE)"
            className="flex-1 p-3 border rounded-lg"
          />
          <button 
            onClick={handleSearch}
            disabled={loading}
            className="bg-emerald-600 text-white px-6 py-3 rounded-lg disabled:opacity-50"
          >
            {loading ? '...' : 'CERCA'}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-3">Risultati</h2>
        {results.length === 0 ? (
          <p className="text-gray-500">Cerca un prodotto per vedere le offerte</p>
        ) : (
          <div className="space-y-3">
            {results.map((p) => (
              <div key={p.id} className="bg-white p-4 rounded-lg shadow flex justify-between items-center">
                <div>
                  <p className="font-bold text-lg">{p.emoji} {p.nome}</p>
                  <p className="text-2xl font-bold text-emerald-600">€{p.prezzo.toFixed(2)}</p>
                  <p className="text-sm text-gray-600">
                    {p.quantita_singola} • {p.percentuale_sconto > 0 ? `-${p.percentuale_sconto}%` : 'OFFERTA'}
                  </p>
                  {p.fonte_volantino_link && (
                    <a 
                      href={p.fonte_volantino_link} 
                      target="_blank"
                      className="text-blue-600 text-sm hover:underline"
                    >
                      📄 Vedi volantino
                    </a>
                  )}
                </div>
                <button 
                  onClick={() => handleAddToWatchlist(p.nome)}
                  className="bg-gray-100 px-4 py-2 rounded hover:bg-gray-200"
                >
                  + Watchlist
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Watchlist */}
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-3">La tua Watchlist</h2>
        {watchlist.length === 0 ? (
          <p className="text-gray-500">Nessun prodotto nella watchlist</p>
        ) : (
          <div className="space-y-2">
            {watchlist.map((item) => (
              <div key={item.id} className="bg-white p-3 rounded shadow flex items-center gap-2">
                <span className="text-xl">🔔</span>
                <span className="font-medium">{item.nome_prodotto}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}