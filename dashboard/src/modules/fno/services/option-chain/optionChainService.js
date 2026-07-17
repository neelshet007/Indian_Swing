// Mock Option Chain Data Service
export const optionChainService = {
  getOptionChain: (selectedIndex) => {
    // Generate dummy strikes around current price config
    const indexConfigs = {
      NIFTY: { basePrice: 24350, interval: 50 },
      BANKNIFTY: { basePrice: 52420, interval: 100 },
      SENSEX: { basePrice: 79890, interval: 100 },
      FINNIFTY: { basePrice: 23680, interval: 50 },
      MIDCPNIFTY: { basePrice: 12340, interval: 25 }
    };

    const config = indexConfigs[selectedIndex] || indexConfigs.NIFTY;
    const baseStrike = Math.round(config.basePrice / config.interval) * config.interval;
    
    const strikes = [];
    // Generate 5 OTM and 5 ITM strikes
    for (let i = -5; i <= 5; i++) {
      const strikePrice = baseStrike + (i * config.interval);
      strikes.push({
        strike: strikePrice,
        ce: {
          ltp: Math.max(2.0, (10 - i * 2) * (config.interval / 10) + Math.random()),
          change: (Math.random() - 0.4) * 10,
          oi: Math.round(100000 + Math.random() * 500000),
          iv: 12.0 + Math.random() * 4
        },
        pe: {
          ltp: Math.max(2.0, (10 + i * 2) * (config.interval / 10) + Math.random()),
          change: (Math.random() - 0.6) * 10,
          oi: Math.round(100000 + Math.random() * 500000),
          iv: 12.5 + Math.random() * 4
        }
      });
    }

    return {
      index: selectedIndex,
      strikes,
      timestamp: new Date().toLocaleTimeString()
    };
  }
};
