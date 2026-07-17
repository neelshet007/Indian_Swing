// Mock F&O Execution Router
export const executionService = {
  executeOrder: (symbol, structure) => {
    if (!structure) return null

    // Simulate order slippage and fills
    const slippagePct = 0.002 // 0.2% slippage on entry
    
    // Estimate credit received based on VIX and vehicle
    // Higher VIX = more credit
    const premiumBase = structure.vehicle === 'Iron Fly' ? 450 : 120
    const credit = premiumBase * (1 + (Math.random() - 0.5) * 0.1)
    const netCredit = credit * (1 - slippagePct)

    return {
      symbol,
      vehicle: structure.vehicle,
      legs: [
        { leg: 'Long Put', strike: structure.longPut, action: 'BUY' },
        { leg: 'Short Put', strike: structure.shortPut, action: 'SELL' },
        { leg: 'Short Call', strike: structure.shortCall, action: 'SELL' },
        { leg: 'Long Call', strike: structure.longCall, action: 'BUY' }
      ],
      netCreditReceived: netCredit,
      targetProfit: netCredit * 0.55, // 55% target
      stopLossLimit: netCredit * 1.75, // 1.75x stop loss limit
      fillTime: new Date().toLocaleTimeString(),
      status: 'FILLED'
    }
  }
}
