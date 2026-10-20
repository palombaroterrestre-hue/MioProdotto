'use client'
import { useState, useEffect } from 'react'
import { searchProdotti, getOffertePerProdotti, addToWatchlist, getWatchlist, getCurrentOffers, Prodotto, OffertaProdotto, OffertaCorrente, WatchlistItem } from '../lib/supabase'

export default function Home() {
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<Prodotto[]>([])
  const [offerte, setOfferte] = useState<Record<number, OffertaProdotto[]>>({})
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [loading, setLoading] = useState(false)
  const [offers, setOffers] = useState<OffertaCorrente[]>([])
  const [utenteId] = useState('user-' + Math.random().toString(36).substr(2, 9))

  useEffect(() => {
    getCurrentOffers().then(setOffers)
  }, [])

  const handleSearch = async () => {
    if (!search.trim()) return
    setLoading(true)
    try {
      const prodotti = await searchProdotti(search)
      setResults(prodotti)
      const mappa = await getOffertePerProdotti(prodotti.map((p) => p.id))
      setOfferte(mappa)
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
    try {
      const items = await getWatchlist(utenteId)
      setWatchlist(items)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-emerald-600 text-white p-4">
        <h1 className="text-2xl font-bold">MioProdotto</h1>
        <p className="text-emerald-100">Trova le migliori offerte nei volantini Ekom</p>
      </header>

      {offers.length > 0 && (
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-3">Offerte correnti</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {offers.map((o) => (
              <div key={o.id} className="bg-white rounded-lg shadow overflow-hidden">
                {o.image_url && (
                  <img
                    src={o.image_url}
                    alt={o.title}
                    className="w-full h-40 object-contain bg-gray-100"
                  />
                )}
                <div className="p-3">
                  <p className="font-bold text-sm leading-tight">{o.title}</p>
                  <p className="text-xs text-gray-500">{o.pieces}</p>
                  <p className="text-xl font-bold text-emerald-600 mt-1">€{o.price}</p>
                  {o.subtitle && <p className="text-xs text-gray-400">{o.subtitle}</p>}
                  <p className="text-xs text-gray-400 mt-1">
                    {o.start_date} → {o.end_date}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 bg-white shadow">
        <div className="flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Cerca un prodotto... (es: caffè, tonno, lavazza)"
            className="flex-1 p-3 border rounded-lg"
          />
          <button
            onClick={() => handleSearch()}
            disabled={loading}
            className="bg-emerald-600 text-white px-6 py-3 rounded-lg disabled:opacity-50"
          >
            {loading ? '...' : 'CERCA'}
          </button>
        </div>
      </div>

      <div className="p-4">
        <h2 className="text-lg font-semibold mb-3">Risultati{results.length > 0 && ` (${results.length})`}</h2>
        {results.length === 0 ? (
          <p className="text-gray-500">Cerca un prodotto per vedere le offerte</p>
        ) : (
          <div className="space-y-3">
            {results.map((p) => (
              <div key={p.id} className="bg-white p-4 rounded-lg shadow">
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <p className="font-bold text-lg">{p.nome}</p>
                    <p className="text-sm text-gray-600">
                      {[p.quantita, `${p.n_offerte} offerte`].filter(Boolean).join(' • ')}
                    </p>
                  </div>
                  <button
                    onClick={() => handleAddToWatchlist(p.nome)}
                    className="bg-gray-100 px-4 py-2 rounded hover:bg-gray-200 shrink-0"
                  >
                    + Watchlist
                  </button>
                </div>
                {(offerte[p.id] || []).length > 0 && (
                  <div className="mt-2 space-y-1">
                    {offerte[p.id].map((o) => (
                      <div key={o.id} className="flex justify-between items-baseline text-sm border-t pt-1">
                        <span className="text-emerald-700 font-bold">
                          €{o.prezzo.toFixed(2)}{o.promo && o.promo !== 'N/D' ? ` (${o.promo})` : ''}
                        </span>
                        {o.valido_dal && (
                          <span className="text-gray-400 text-xs">
                            {o.valido_dal} → {o.valido_al}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

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
