// F&O Strike Selection Engine
export const strikeSelection = {
  selectStrikes: (symbol, marketData, optionChain) => {
    if (!marketData || !optionChain) return null

    const strikes = optionChain.strikes
    const spot = marketData.spotPrice

    // Fixed wing width by index config
    const wingConfig = {
      NIFTY: 200,
      BANKNIFTY: 500,
      SENSEX: 600,
      FINNIFTY: 200,
      MIDCPNIFTY: 100
    }
    const wingWidth = wingConfig[symbol] || 200

    // Assign mock Delta to strikes based on distance from spot
    const mappedStrikes = strikes.map(s => {
      const distance = s.strike - spot
      // Delta ranges from 0 to 1 for Call, 0 to -1 for Put
      const ceDelta = 1 / (1 + Math.exp(distance / 150)) // Sigmoid delta approx
      const peDelta = ceDelta - 1
      return {
        ...s,
        ceDelta,
        peDelta
      }
    })

    // Find short Call (Delta ~0.18)
    const shortCallItem = mappedStrikes.reduce((prev, curr) => 
      Math.abs(curr.ceDelta - 0.18) < Math.abs(prev.ceDelta - 0.18) ? curr : prev
    )

    // Find short Put (Delta ~ -0.18)
    const shortPutItem = mappedStrikes.reduce((prev, curr) => 
      Math.abs(curr.peDelta - (-0.18)) < Math.abs(prev.peDelta - (-0.18)) ? curr : prev
    )

    const shortCall = shortCallItem.strike
    const shortPut = shortPutItem.strike

    // Wings distance
    const longCall = shortCall + wingWidth
    const longPut = shortPut - wingWidth

    return {
      longPut,
      shortPut,
      shortCall,
      longCall,
      shortCallDelta: shortCallItem.ceDelta,
      shortPutDelta: shortPutItem.peDelta,
      wingWidth
    }
  }
}
