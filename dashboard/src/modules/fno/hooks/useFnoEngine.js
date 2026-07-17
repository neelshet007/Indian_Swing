import { useState, useEffect, useRef, useCallback } from 'react'
import { marketService } from '../services/market/marketService'
import { optionChainService } from '../services/option-chain/optionChainService'
import { strategyService } from '../services/strategy/strategyService'

export default function useFnoEngine() {
  const [monitoringMode, setMonitoringMode] = useState('single') // 'single' | 'multi'
  const [selectedIndices, setSelectedIndices] = useState(['NIFTY'])
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [sessions, setSessions] = useState({})

  const intervalRef = useRef(null)

  // Fetch updates and run strategy engine for active indices asynchronously
  const tick = useCallback(async () => {
    if (!isMonitoring || selectedIndices.length === 0) return

    const updatedSessions = {}

    try {
      await Promise.all(
        selectedIndices.map(async (symbol) => {
          const start = performance.now()
          try {
            const marketData = await marketService.getLatestMarketData(symbol)
            const optionChain = await optionChainService.getOptionChain(symbol)
            const end = performance.now()

            updatedSessions[symbol] = {
              marketData,
              optionChain,
              indicators: marketData.indicators,
              regimeResults: marketData.regimeResults,
              selectedStrikes: marketData.selectedStrikes,
              structure: marketData.structure,
              recommendation_uuid: marketData.recommendation_uuid,
              connectionStatus: 'Connected',
              status: 'Running',
              lastUpdate: new Date().toLocaleTimeString(),
              latency: Math.round(end - start)
            }
          } catch (e) {
            updatedSessions[symbol] = {
              connectionStatus: 'Error',
              status: 'Stopped'
            }
          }
        })
      )
      
      setSessions(prev => ({ ...prev, ...updatedSessions }))
    } catch (e) {
      // Top level failure handling
    }
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
        if (prev.length === 1) return prev
        const filtered = prev.filter(s => s !== symbol)
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

  useEffect(() => {
    if (isMonitoring) {
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
