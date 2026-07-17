// F&O VRP Risk Manager
export const riskService = {
  checkRiskLimits: (params) => {
    const {
      tradeRiskPct = 0.0075, // 0.75%
      portfolioExposurePct = 0.035, // 3.5%
      dailyLossPct = 0.0,
      weeklyLossPct = 0.0,
      monthlyDrawdownPct = 0.0
    } = params

    // Limits config
    const LIMITS = {
      maxTradeRisk: 0.01,       // 1% max per trade
      maxPortfolioRisk: 0.06,   // 6% max portfolio exposure
      dailyLossLimit: 0.02,     // 2% daily loss limit
      weeklyLossLimit: 0.04,    // 4% weekly loss limit
      monthlyDrawdownLimit: 0.08 // 8% monthly drawdown limit
    }

    const tradeRiskPass = tradeRiskPct <= LIMITS.maxTradeRisk
    const portfolioPass = portfolioExposurePct <= LIMITS.maxPortfolioRisk
    const dailyPass = dailyLossPct < LIMITS.dailyLossLimit
    const weeklyPass = weeklyLossPct < LIMITS.weeklyLossLimit
    const monthlyPass = monthlyDrawdownPct < LIMITS.monthlyDrawdownLimit

    const isRiskCleared = tradeRiskPass && portfolioPass && dailyPass && weeklyPass && monthlyPass

    return {
      isRiskCleared,
      limits: {
        tradeRisk: { val: `${(tradeRiskPct * 100).toFixed(2)}%`, pass: tradeRiskPass, limit: 'Max 1.0%' },
        portfolioExposure: { val: `${(portfolioExposurePct * 100).toFixed(2)}%`, pass: portfolioPass, limit: 'Max 6.0%' },
        dailyLoss: { val: `${(dailyLossPct * 100).toFixed(2)}%`, pass: dailyPass, limit: 'Max 2.0%' },
        weeklyLoss: { val: `${(weeklyLossPct * 100).toFixed(2)}%`, pass: weeklyPass, limit: 'Max 4.0%' },
        monthlyDrawdown: { val: `${(monthlyDrawdownPct * 100).toFixed(2)}%`, pass: monthlyPass, limit: 'Max 8.0%' }
      }
    }
  }
}
