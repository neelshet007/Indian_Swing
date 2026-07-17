import { indicatorEngine } from './indicatorEngine'
import { regimeFilter } from './regimeFilter'
import { strikeSelection } from './strikeSelection'
import { positionBuilder } from './positionBuilder'

export const strategyService = {
  evaluate: (symbol, marketData, optionChain, scheduledEvents = []) => {
    if (!marketData || !optionChain) return null

    // 1. Compute VRP Indicators
    const indicators = indicatorEngine.computeIndicators(symbol, marketData, optionChain)

    // 2. Evaluate 6 Regime Filters
    const regimeResults = regimeFilter.checkFilters(marketData, indicators, scheduledEvents)

    // 3. Select Short & Long Strikes by delta
    const selectedStrikes = strikeSelection.selectStrikes(symbol, marketData, optionChain)

    // 4. Construct iron spreads (Iron Condor vs Iron Fly)
    const structure = positionBuilder.buildStructure(symbol, marketData, selectedStrikes, indicators)

    return {
      indicators,
      regimeResults,
      selectedStrikes,
      structure,
      timestamp: new Date().toLocaleTimeString()
    }
  }
}
