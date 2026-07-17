import axios from 'axios'

// Live F&O Market Data Service calling Upstox backend
export const marketService = {
  getLatestMarketData: async (selectedIndex) => {
    const { data } = await axios.get(`/api/fno/market-data?symbol=${selectedIndex}`)
    return data
  }
}
