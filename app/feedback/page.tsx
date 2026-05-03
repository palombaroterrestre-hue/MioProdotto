'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import '@/app/globals.css'

const FEEDBACK_PASSWORD = 'mio2026'

interface FeedbackPair {
  id: string
  alias_name: string
  canonical_name: string
  similarity_score: number
  user_feedback: boolean | null
}

export default function FeedbackPage() {
  const [authenticated, setAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [pairs, setPairs] = useState<FeedbackPair[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [submitted, setSubmitted] = useState(0)

  function handleLogin() {
    if (password === FEEDBACK_PASSWORD) {
      setAuthenticated(true)
      loadDubbie()
    } else {
      setError('Password errata')
    }
  }

  useEffect(() => {
    if (authenticated) {
      loadDubbie()
    }
  }, [authenticated])

  async function loadDubbie() {
    setLoading(true)
    
    const { data, error } = await supabase
      .from('product_aliases')
      .select('id, alias_name, canonical_name, similarity_score')
      .eq('source', 'string_match')
      .gte('similarity_score', 0.85)
      .lte('similarity_score', 0.99)
      .limit(30)
      .order('similarity_score', { ascending: true })

    if (!error && data) {
      setPairs(data as FeedbackPair[])
    }
    setLoading(false)
  }

  async function handleFeedback(isCorrect: boolean) {
    if (saving || currentIndex >= pairs.length) return
    
    setSaving(true)
    const current = pairs[currentIndex]
    
    const { error } = await supabase
      .from('product_aliases')
      .update({ 
        confidence: isCorrect ? 1 : 0,
        updated_at: new Date().toISOString()
      })
      .eq('id', current.id)

    if (!error) {
      setSubmitted(s => s + 1)
      setCurrentIndex(i => i + 1)
    }
    
    setSaving(false)
  }

  async function handleSkip() {
    setCurrentIndex(i => i + 1)
  }

  const current = pairs[currentIndex]

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold text-center text-orange-500 mb-8">Feedback Deduplicazione</h1>
          
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
            placeholder="Password"
            className="w-full px-6 py-4 bg-gray-900 border border-gray-700 rounded-lg text-lg mb-4 focus:border-orange-500 focus:outline-none"
          />
          
          <button
            onClick={handleLogin}
            className="w-full px-6 py-4 bg-orange-600 hover:bg-orange-700 rounded-lg text-lg font-bold"
          >
            Accedi
          </button>
          
          {error && <div className="mt-4 text-red-500 text-center">{error}</div>}
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl mb-4">Caricamento coppie...</div>
        </div>
      </div>
    )
  }

  if (!current || currentIndex >= pairs.length) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-3xl mb-4">Completato!</div>
          <div className="text-xl text-gray-400">Hai valutato {submitted} coppie</div>
          <button 
            onClick={() => { setCurrentIndex(0); loadDubbie(); setSubmitted(0); }}
            className="mt-6 px-6 py-3 bg-orange-600 rounded-lg text-lg hover:bg-orange-700"
          >
            Ricomincia
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white p-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-orange-500 mb-2">Feedback Deduplicazione</h1>
          <div className="text-gray-400">
            Coppia {currentIndex + 1} di {pairs.length} • Valutate: {submitted}
          </div>
        </div>

        <div className="bg-gray-900 rounded-xl p-6 mb-8">
          <div className="mb-6">
            <div className="text-sm text-gray-500 mb-2">ALIAS</div>
            <div className="text-xl text-red-400">{current.alias_name}</div>
          </div>
          
          <div className="mb-6">
            <div className="text-sm text-gray-500 mb-2">CANONICAL</div>
            <div className="text-xl text-green-400">{current.canonical_name}</div>
          </div>

          <div className="bg-gray-800 rounded-lg p-3">
            <div className="text-sm text-gray-500">Similarità</div>
            <div className="text-2xl font-bold">
              {(current.similarity_score * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={() => handleFeedback(false)}
            disabled={saving}
            className="px-6 py-4 bg-red-700 hover:bg-red-600 rounded-lg text-lg font-bold disabled:opacity-50"
          >
            ❌ Sbagliato
          </button>
          
          <button
            onClick={handleSkip}
            className="px-6 py-4 bg-gray-700 hover:bg-gray-600 rounded-lg text-lg"
          >
            ⏭️ Skip
          </button>
          
          <button
            onClick={() => handleFeedback(true)}
            disabled={saving}
            className="px-6 py-4 bg-green-700 hover:bg-green-600 rounded-lg text-lg font-bold disabled:opacity-50"
          >
            ✅ Corretto
          </button>
        </div>

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>I feedback miglioreranno il modello AI di deduplicazione</p>
        </div>
      </div>
    </div>
  )
}