// F&O Position Builder
export const positionBuilder = {
  buildStructure: (symbol, marketData, selectedStrikes, indicators) => {
    if (!marketData || !selectedStrikes || !indicators) return null

    // Determine vehicle: Iron Fly or Iron Condor
    // Condition: IV Percentile > 60 AND RV20 is low (<13%) -> Compression Regime (Iron Fly)
    const isCompressionRegime = indicators.ivPercentile > 60 && indicators.rv20 < 13.0
    const vehicle = isCompressionRegime ? 'Iron Fly' : 'Iron Condor'

    let structure = {}

    if (vehicle === 'Iron Fly') {
      // Iron Fly short strikes are ATM (closest to spot)
      const atmStrike = Math.round(marketData.spotPrice / selectedStrikes.wingWidth) * selectedStrikes.wingWidth
      
      structure = {
        vehicle,
        longPut: atmStrike - selectedStrikes.wingWidth,
        shortPut: atmStrike,
        shortCall: atmStrike,
        longCall: atmStrike + selectedStrikes.wingWidth,
        wingWidth: selectedStrikes.wingWidth,
        notes: 'Compression Regime: Neutral ATM short legs placed.'
      }
    } else {
      // Iron Condor uses standard delta selected strikes
      structure = {
        vehicle,
        longPut: selectedStrikes.longPut,
        shortPut: selectedStrikes.shortPut,
        shortCall: selectedStrikes.shortCall,
        longCall: selectedStrikes.longCall,
        wingWidth: selectedStrikes.wingWidth,
        notes: 'VRP Harvesting regime active.'
      }
    }

    return structure
  }
}
