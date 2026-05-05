'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import '@/app/globals.css'

const FEEDBACK_PASSWORD = 'mio2026'

interface FeedbackRecord {
  id: string
  alias_name: string
  canonical_name: string
  similarity: number | null
  category: string | null
  label: string | null
}

export default function FeedbackReviewPage() {
  const [authenticated, setAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [records, setRecords] = useState<FeedbackRecord[]>([])
  const [displayed, setDisplayed] = useState<FeedbackRecord[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [stats, setStats] = useState({ correct: 0, wrong: 0, total: 0 })

  async function loadFeedback() {
    setLoading(true)
    
    // Load all feedback records
    const { data: allFeedback } = await supabase
      .from('dedup_feedback')
      .select('*')
      .order('updated_at', { ascending: false })
    
    if (allFeedback) {
      // Shuffle for variety
      const shuffled = [...allFeedback].sort(() => Math.random() - 0.5)
      
      // Get first 30
      const first30 = shuffled.slice(0, 30)
      setRecords(allFeedback as FeedbackRecord[])
      setDisplayed(first30 as FeedbackRecord[])
      setCurrentIndex(0)
      
      // Stats
      const correct = allFeedback.filter((r: any) => r.label === 'CORRECT').length
      const wrong = allFeedback.filter((r: any) => r.label === 'WRONG').length
      setStats({ correct, wrong, total: allFeedback.length })
    }
    
    setLoading(false)
  }

  function handleLogin() {
    if (password === FEEDBACK_PASSWORD) {
      setAuthenticated(true)
      loadFeedback()
    } else {
      setError('Password errata')
    }
  }

  async function handleMark(isCorrect: boolean) {
    if (saving || currentIndex >= displayed.length) return
    
    setSaving(true)
    const current = displayed[currentIndex]
    
    // Update in DB
    const { error } = await supabase
      .from('dedup_feedback')
      .update({ label: isCorrect ? 'CORRECT' : 'WRONG' })
      .eq('id', current.id)
    
    if (!error) {
      // Update local state
      const updated = [...displayed]
      updated[currentIndex] = { ...current, label: isCorrect ? 'CORRECT' : 'WRONG' }
      setDisplayed(updated)
      
      // Update stats
      setStats(s => ({
        ...s,
        correct: isCorrect ? s.correct + 1 : s.correct,
        wrong: isCorrect ? s.wrong : s.wrong + 1
      }))
      
      // Move to next
      if (currentIndex < displayed.length - 1) {
        setCurrentIndex(i => i + 1)
      } else {
        // Load next 30
        const remaining = records.filter(r => !displayed.some(d => d.id === r.id))
        const next30 = remaining.slice(0, 30)
        if (next30.length > 0) {
          setDisplayed([...displayed.slice(currentIndex + 1), ...next30])
        } else {
          // Refresh from DB
          loadFeedback()
        }
      }
    }
    
    setSaving(false)
  }

  async function handleSkip() {
    if (currentIndex < displayed.length - 1) {
      setCurrentIndex(i => i + 1)
    }
  }

  async function loadNextBatch() {
    const shownIds = new Set(displayed.map(d => d.id))
    const remaining = records.filter(r => !shownIds.has(r.id))
    const next30 = remaining.slice(0, 30)
    
    if (next30.length > 0) {
      setDisplayed(next30 as FeedbackRecord[])
      setCurrentIndex(0)
    } else {
      // All reviewed, reload
      loadFeedback()
    }
  }

  const current = displayed[currentIndex]

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold text-center text-orange-500 mb-8">Revisione Feedback</h1>
          
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
          <div className="text-2xl mb-4">Caricamento...</div>
        </div>
      </div>
    )
  }

  if (!current || displayed.length === 0) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-3xl mb-4">Nessun record da revisionare</div>
          <button 
            onClick={loadFeedback}
            className="mt-6 px-6 py-3 bg-orange-600 rounded-lg text-lg hover:bg-orange-700"
          >
            Ricarica
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white p-4">
      <div className="max-w-3xl mx-auto">
        {/* Stats */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-orange-500 mb-2">Revisione Feedback</h1>
          <div className="flex justify-center gap-8 text-gray-400">
            <span>✅ CORRECT: <span className="text-green-400 font-bold">{stats.correct}</span></span>
            <span>❌ WRONG: <span className="text-red-400 font-bold">{stats.wrong}</span></span>
            <span>📊 Totale: <span className="font-bold">{stats.total}</span></span>
          </div>
        </div>

        {/* Progress */}
        <div className="bg-gray-800 rounded-lg p-3 text-center mb-6">
          Record {currentIndex + 1} di {displayed.length}
        </div>

        {/* Current Record */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* ALIAS */}
          <div className="bg-gray-900 rounded-xl p-5">
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm text-gray-500">ALIAS</div>
              {current.label && (
                <div className={`text-xs px-2 py-1 rounded ${current.label === 'CORRECT' ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'}`}>
                  {current.label}
                </div>
              )}
            </div>
            <div className="text-lg text-red-400 font-medium">{current.alias_name}</div>
            {current.similarity && (
              <div className="text-gray-500 text-sm mt-2">
                Similarity: {(current.similarity * 100).toFixed(1)}%
              </div>
            )}
            {current.category && (
              <div className="text-gray-500 text-sm">
                Category: {current.category}
              </div>
            )}
          </div>

          {/* CANONICAL */}
          <div className="bg-gray-900 rounded-xl p-5">
            <div className="text-sm text-gray-500 mb-2">CANONICAL</div>
            <div className="text-lg text-green-400 font-medium">{current.canonical_name}</div>
          </div>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={() => handleMark(false)}
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
            onClick={() => handleMark(true)}
            disabled={saving}
            className="px-6 py-4 bg-green-700 hover:bg-green-600 rounded-lg text-lg font-bold disabled:opacity-50"
          >
            ✅ Corretto
          </button>
        </div>

        {/* Load more */}
        <div className="mt-6 text-center">
          <button 
            onClick={loadNextBatch}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg"
          >
            Carica altri 30
          </button>
        </div>
      </div>
    </div>
  )
}
