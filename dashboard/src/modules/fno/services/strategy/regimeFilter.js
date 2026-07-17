// F&O VRP Regime Filters
export const regimeFilter = {
  checkFilters: (marketData, indicators, scheduledEvents = []) => {
    if (!marketData || !indicators) {
      return { isAllowed: false, filters: {} }
    }

    // Filter 1: IV Percentile (35 <= IVP <= 75)
    const ivpPass = indicators.ivPercentile >= 35 && indicators.ivPercentile <= 75

    // Filter 2: Term Structure (Front IV > Back IV)
    const termPass = indicators.termStructurePos

    // Filter 3: Dealer Gamma (GEX > 0)
    const gexPass = indicators.dealerGex > 0

    // Filter 4: IV vs RV Spread (IV - RV > 0)
    const spreadPass = indicators.ivRvSpread > 0

    // Filter 5: Macro Event Filter (Avoid entry if scheduled major event exists)
    // Avoid RBI policy, Budget, Elections, Fed rate decisions
    const hasMacroEvent = scheduledEvents.some(event => {
      const eventDate = new Date(event.date)
      const today = new Date()
      const diffTime = Math.abs(eventDate - today)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return diffDays <= 5 // Within holding period (5 days DTE)
    })
    const eventPass = !hasMacroEvent

    // Filter 6: India VIX Spike Entry Filter (+15% limit)
    const vixSpikePass = marketData.changePct < 15.0 // Limit intraday change to +15%

    const isAllowed = ivpPass && termPass && gexPass && spreadPass && eventPass && vixSpikePass

    return {
      isAllowed,
      filters: {
        ivPercentile: { val: `${indicators.ivPercentile.toFixed(1)}%`, pass: ivpPass, desc: '35% to 75%' },
        termStructure: { val: `${indicators.frontIv.toFixed(1)} vs ${indicators.backIv.toFixed(1)}`, pass: termPass, desc: 'Front IV > Back IV' },
        dealerGamma: { val: indicators.dealerGex > 0 ? 'Positive' : 'Negative', pass: gexPass, desc: 'Net Gamma > 0' },
        spread: { val: `${indicators.ivRvSpread.toFixed(2)}%`, pass: spreadPass, desc: 'IV - RV > 0' },
        macroEvents: { val: hasMacroEvent ? 'Event Pending' : 'Clear Window', pass: eventPass, desc: 'No RBI/Budget' },
        vixSpike: { val: `${marketData.changePct.toFixed(2)}%`, pass: vixSpikePass, desc: '< 15% Spike' }
      }
    }
  }
}
