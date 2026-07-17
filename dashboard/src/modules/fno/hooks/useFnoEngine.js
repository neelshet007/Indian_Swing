import { useState, useEffect, useRef, useCallback } from 'react'
import { marketService } from '../services/market/marketService'
import { optionChainService } from '../services/option-chain/optionChainService'

export default function useFnoEngine() {
  const [monitoringMode, setMonitoringMode] = useState('single') // 'single' | 'multi'
  const [selectedIndices, setSelectedIndices] = useState(['NIFTY'])
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [sessions, setSessions] = useState({})

  const intervalRef = useRef(null)

  // Fetch updates for all active indices
  const tick = useCallback(() => {
    if (!isMonitoring || selectedIndices.length === 0) return

    setSessions(prev => {
      const updated = { ...prev }
      selectedIndices.forEach(symbol => {
        const start = performance.now()
        try {
          const marketData = marketService.getLatestMarketData(symbol)
          const optionChain = optionChainService.getOptionChain(symbol)
          const end = performance.now()

          updated[symbol] = {
            marketData,
            optionChain,
            connectionStatus: 'Connected',
            status: 'Running',
            lastUpdate: new Date().toLocaleTimeString(),
            latency: Math.round(end - start + 25)
          }
        } catch (e) {
          updated[symbol] = {
            ...(prev[symbol] || {}),
            connectionStatus: 'Error',
            status: 'Stopped'
          }
        }
      })
      return updated
    })
  }, [isMonitoring, selectedIndices])

  const startMonitoring = () => {
    setIsMonitoring(true)
  }

  const stopMonitoring = () => {
    setIsMonitoring(false)
    setSessions(prev => {
      const stopped = { ...prev }
      selectedIndices.forEach(symbol => {
        if (stopped[symbol]) {
          stopped[symbol] = {
            ...stopped[symbol],
            status: 'Stopped'
          }
        }
      })
      return stopped
    })
  }

  const changeMode = (mode) => {
    stopMonitoring()
    setMonitoringMode(mode)
    setSessions({})
    setSelectedIndices(mode === 'single' ? ['NIFTY'] : ['NIFTY'])
  }

  const selectSingleIndex = (symbol) => {
    setSelectedIndices([symbol])
    setSessions({})
  }

  const toggleMultiIndex = (symbol) => {
    setSelectedIndices(prev => {
      if (prev.includes(symbol)) {
        // Keep at least one index selected
        if (prev.length === 1) return prev
        const filtered = prev.filter(s => s !== symbol)
        // Clean session for removed index
        setSessions(sPrev => {
          const copy = { ...sPrev }
          delete copy[symbol]
          return copy
        })
        return filtered
      } else {
        return [...prev, symbol]
      }
    })
  }

  // Manage background loop (starts only when isMonitoring is true, cleans up on stop/unmount)
  useEffect(() => {
    if (isMonitoring) {
      // Run immediately
      tick()
      intervalRef.current = setInterval(tick, 3000)
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
    toggleMultiIndex
  }
}
