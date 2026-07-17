import axios from 'axios'

// Live F&O Option Chain Service calling Upstox backend
export const optionChainService = {
  getOptionChain: async (selectedIndex) => {
    const { data } = await axios.get(`/api/fno/option-chain?symbol=${selectedIndex}`)
    return data
  }
}
