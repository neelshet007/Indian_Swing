// VRP Harvester Indicator Engine
export const indicatorEngine = {
  computeIndicators: (symbol, marketData, optionChain) => {
    if (!marketData || !optionChain) return null

    // 1. IV Percentile (60D) - simulated relative to historical range
    // Under normal conditions it lies between 35 and 75. 
    // We can simulate an IV percentile relative to the index's current VIX.
    const ivPercentile = Math.min(
      95,
      Math.max(5, 30 + ((marketData.indiaVix - 12) * 8) + (Math.random() - 0.5) * 5)
    )

    // 2. Realized Volatility (RV20) - 20-day historical realized volatility
    // Standard realized volatility is slightly lower than VIX (implied volatility)
    const rv20 = Math.max(8.0, marketData.indiaVix * 0.85 + (Math.random() - 0.5) * 1.5)

    // 3. IV vs RV Spread
    const ivRvSpread = marketData.indiaVix - rv20

    // 4. Dealer Gamma Exposure (GEX)
    // Positive Net Dealer Gamma > 0 represents a supportive regime.
    // Simulate GEX based on spot price positioning.
    const spot = marketData.spotPrice
    const gexSign = Math.sin(spot / 500) > -0.1 ? 1 : -1
    const dealerGex = gexSign * (250000 + Math.round(Math.random() * 500000))

    // 5. Term Structure: Front IV vs Back IV
    // Front IV represents weekly, Back IV represents monthly.
    // In normal contango, Front IV > Back IV is typical during trade opportunities.
    const frontIv = marketData.indiaVix
    const backIv = marketData.indiaVix * 0.95 + (Math.random() - 0.5) * 0.5
    const termStructurePos = frontIv > backIv

    return {
      ivPercentile,
      rv20,
      ivRvSpread,
      dealerGex,
      frontIv,
      backIv,
      termStructurePos,
      timestamp: new Date().toLocaleTimeString()
    }
  }
}
