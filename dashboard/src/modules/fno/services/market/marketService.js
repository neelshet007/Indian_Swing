// Mock F&O Live Market Data Service
export const marketService = {
  getLatestMarketData: (selectedIndex) => {
    // Return dummy data dynamically based on the selected index context
    const timestamp = new Date().toLocaleTimeString();
    
    const indexConfigs = {
      NIFTY: { basePrice: 24350.0, vix: 14.12, expiry: '23-JUL-2026' },
      BANKNIFTY: { basePrice: 52420.0, vix: 15.60, expiry: '23-JUL-2026' },
      SENSEX: { basePrice: 79890.0, vix: 12.80, expiry: '24-JUL-2026' },
      FINNIFTY: { basePrice: 23680.0, vix: 13.90, expiry: '21-JUL-2026' },
      MIDCPNIFTY: { basePrice: 12340.0, vix: 16.20, expiry: '20-JUL-2026' }
    };

    const config = indexConfigs[selectedIndex] || indexConfigs.NIFTY;
    
    // Add small random fluctuation to simulate ticks
    const tickChange = (Math.random() - 0.5) * 5;
    const spotPrice = config.basePrice + tickChange;
    const changePct = ((tickChange / config.basePrice) * 100) + (selectedIndex === 'BANKNIFTY' ? -0.22 : 0.45);

    return {
      symbol: selectedIndex,
      spotPrice,
      changePct,
      indiaVix: config.vix + (Math.random() - 0.5) * 0.1,
      marketStatus: 'OPEN',
      expiry: config.expiry,
      tradingSession: 'REGULAR',
      timestamp
    };
  }
};
