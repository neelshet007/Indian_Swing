import { useState, useEffect, useRef, useCallback } from 'react'
import { marketService } from '../services/market/marketService'
import { optionChainService } from '../services/option-chain/optionChainService'

// A7 — Resilient polling engine
// Consecutive failure thresholds before degraded state
const MAX_CONSECUTIVE_FAILURES = 3
const BASE_INTERVAL_MS         = 3000
const DEGRADED_INTERVAL_MS     = 10000   // slow down polling when degraded

export default function useFnoEngine() {
  const [monitoringMode, setMonitoringMode]   = useState('single')
  const [selectedIndices, setSelectedIndices] = useState(['NIFTY'])
  const [isMonitoring, setIsMonitoring]       = useState(false)
  const [sessions, setSessions]               = useState({})

  const intervalRef       = useRef(null)
  const failureCountRef   = useRef({})   // { NIFTY: 0, BANKNIFTY: 0, ... }

  // ── Core tick function ───────────────────────────────────────────────────
  const tick = useCallback(async () => {
    if (!isMonitoring || selectedIndices.length === 0) return

    const updatedSessions = {}

    await Promise.allSettled(
      selectedIndices.map(async (symbol) => {
        const start = performance.now()
        try {
          const marketData = await marketService.getLatestMarketData(symbol)
          const optionChain = await optionChainService.getOptionChain(symbol)
          const end = performance.now()

          // Reset failure counter on success
          failureCountRef.current[symbol] = 0

          updatedSessions[symbol] = {
            marketData,
            optionChain,
            indicators:       marketData.indicators,
            regimeResults:    marketData.regimeResults,
            selectedStrikes:  marketData.selectedStrikes,
            structure:        marketData.structure,
            recommendation_uuid: marketData.recommendation_uuid,
            connectionStatus: 'Connected',
            status:           'Running',
            lastUpdate:       new Date().toLocaleTimeString(),
            latency:          Math.round(end - start),
            consecutiveErrors: 0,
          }
        } catch (e) {
          const prevCount = (failureCountRef.current[symbol] || 0) + 1
          failureCountRef.current[symbol] = prevCount
          const isDegraded = prevCount >= MAX_CONSECUTIVE_FAILURES

          console.warn(`[useFnoEngine] ${symbol} tick failed (${prevCount}/${MAX_CONSECUTIVE_FAILURES}):`, e?.message)

          // Preserve last valid session data if available; only wipe if fully degraded
          updatedSessions[symbol] = {
            ...(sessions[symbol] || {}),          // keep previous data visible
            connectionStatus: isDegraded ? 'Error' : 'Retrying',
            status:           isDegraded ? 'Degraded' : 'Running',
            lastError:        e?.message || 'Unknown error',
            consecutiveErrors: prevCount,
            lastUpdate:       new Date().toLocaleTimeString(),
          }
        }
      })
    )

    setSessions(prev => ({ ...prev, ...updatedSessions }))

    // Adaptive polling: if any symbol is degraded, slow down to DEGRADED_INTERVAL_MS
    const anyDegraded = Object.values(failureCountRef.current).some(c => c >= MAX_CONSECUTIVE_FAILURES)
    const targetInterval = anyDegraded ? DEGRADED_INTERVAL_MS : BASE_INTERVAL_MS
    if (intervalRef.current?._delay !== targetInterval) {
      // Restart interval at new rate if needed
      if (intervalRef.current) clearInterval(intervalRef.current)
      intervalRef.current = setInterval(tick, targetInterval)
      intervalRef.current._delay = targetInterval
    }
  }, [isMonitoring, selectedIndices, sessions])

  // ── Start / Stop ─────────────────────────────────────────────────────────
  const startMonitoring = () => {
    failureCountRef.current = {}
    setIsMonitoring(true)
  }

  const stopMonitoring = () => {
    setIsMonitoring(false)
    setSessions(prev => {
      const stopped = { ...prev }
      selectedIndices.forEach(symbol => {
        if (stopped[symbol]) stopped[symbol] = { ...stopped[symbol], status: 'Stopped' }
      })
      return stopped
    })
  }

  const changeMode = (mode) => {
    stopMonitoring()
    setMonitoringMode(mode)
    setSessions({})
    setSelectedIndices(['NIFTY'])
  }

  const selectSingleIndex = (symbol) => {
    setSelectedIndices([symbol])
    setSessions({})
  }

  const toggleMultiIndex = (symbol) => {
    setSelectedIndices(prev => {
      if (prev.includes(symbol)) {
        if (prev.length === 1) return prev
        const filtered = prev.filter(s => s !== symbol)
        setSessions(sPrev => {
          const copy = { ...sPrev }
          delete copy[symbol]
          return copy
        })
        return filtered
      }
      return [...prev, symbol]
    })
  }

  // ── Polling lifecycle ─────────────────────────────────────────────────────
  useEffect(() => {
    if (isMonitoring) {
      tick()
      intervalRef.current = setInterval(tick, BASE_INTERVAL_MS)
      intervalRef.current._delay = BASE_INTERVAL_MS
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isMonitoring, tick])

  return {
    monitoringMode,
    selectedIndices,
    isMonitoring,
    sessions,
    startMonitoring,
    stopMonitoring,
    changeMode,
    selectSingleIndex,
    toggleMultiIndex,
  }
}
